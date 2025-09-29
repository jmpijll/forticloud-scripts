#!/usr/bin/env python3
"""
FortiCloud API Script - Get FortiGate/FortiWiFi Devices

This script retrieves all FortiGate and FortiWiFi devices from FortiCloud
and exports them to a CSV file with device details and contract information.

Author: FortiCloud API Project
Date: September 29, 2025
"""

import os
import sys
import csv
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv


class FortiCloudAPI:
    """
    FortiCloud API client for retrieving device and contract information.
    """

    def __init__(self, client_id: str, client_secret: str, auth_url: str, api_base_url: str, debug: bool = False):
        """
        Initialize the FortiCloud API client.

        Args:
            client_id: FortiCloud API Client ID
            client_secret: FortiCloud API Client Secret
            auth_url: Authentication endpoint URL
            api_base_url: Base URL for API endpoints
            debug: Enable debug logging
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.api_base_url = api_base_url.rstrip('/')
        self.debug = debug
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Create a session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FortiCloud-API-Script/1.0'
        })

    def _log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def authenticate(self) -> bool:
        """
        Authenticate with FortiCloud API and obtain OAuth access token.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            self._log("Authenticating with FortiCloud API...")
            
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            
            response = self.session.post(self.auth_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            if not self.access_token:
                print("ERROR: No access token received from authentication response")
                return False
            
            # Update session headers with the access token
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            self._log("Authentication successful")
            return True
            
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP error during authentication: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Network error during authentication: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error during authentication: {e}")
            return False

    def get_devices(self, product_type: Optional[str] = None, per_page: int = 100) -> List[Dict]:
        """
        Retrieve all devices from FortiCloud.

        Args:
            product_type: Filter by product type (e.g., 'fortigate', 'fortiwifi')
            per_page: Number of results per page (max 1000)

        Returns:
            List of device dictionaries
        """
        devices = []
        page = 1
        
        try:
            while True:
                self._log(f"Fetching devices page {page}...")
                
                # Build query parameters
                params = {
                    'page': page,
                    'per_page': per_page
                }
                
                if product_type:
                    params['product_type'] = product_type
                
                endpoint = f"{self.api_base_url}/registration/v2/products/list"
                response = self.session.get(endpoint, params=params, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 429:
                    print("WARNING: Rate limit reached. Waiting before retry...")
                    import time
                    time.sleep(60)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Handle different response structures
                if data.get('status') == 'success':
                    products = data.get('data', {}).get('products', [])
                    if not products:
                        break
                    devices.extend(products)
                    
                    total = data.get('data', {}).get('total', 0)
                    self._log(f"Retrieved {len(devices)} of {total} devices")
                    
                    # Check if there are more pages
                    if len(devices) >= total:
                        break
                else:
                    print(f"WARNING: Unexpected response status: {data.get('status')}")
                    break
                
                page += 1
                
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: HTTP error retrieving devices: {e}")
            if e.response is not None:
                print(f"Response: {e.response.text}")
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Network error retrieving devices: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected error retrieving devices: {e}")
        
        return devices

    def close(self) -> None:
        """Close the session."""
        self.session.close()


def flatten_device_data(devices: List[Dict]) -> List[Dict]:
    """
    Flatten device data to include one row per contract per device.

    Args:
        devices: List of device dictionaries from the API

    Returns:
        List of flattened dictionaries suitable for CSV export
    """
    flattened = []
    
    for device in devices:
        serial_number = device.get('serial_number', 'N/A')
        device_name = device.get('product_name', device.get('product_model', 'N/A'))
        product_model = device.get('product_model', 'N/A')
        product_type = device.get('product_type', 'N/A')
        
        contracts = device.get('contracts', [])
        
        if not contracts:
            # If no contracts, still include the device with empty contract fields
            flattened.append({
                'Device Name': device_name,
                'Serial Number': serial_number,
                'Product Model': product_model,
                'Product Type': product_type,
                'Contract Number': 'No Contract',
                'Contract Type': 'N/A',
                'Contract Start Date': 'N/A',
                'Contract Expiration Date': 'N/A',
                'Contract Status': 'N/A'
            })
        else:
            # Create one row per contract
            for contract in contracts:
                flattened.append({
                    'Device Name': device_name,
                    'Serial Number': serial_number,
                    'Product Model': product_model,
                    'Product Type': product_type,
                    'Contract Number': contract.get('contract_number', 'N/A'),
                    'Contract Type': contract.get('contract_type', 'N/A'),
                    'Contract Start Date': contract.get('start_date', 'N/A'),
                    'Contract Expiration Date': contract.get('end_date', 'N/A'),
                    'Contract Status': contract.get('status', 'N/A')
                })
    
    return flattened


def export_to_csv(data: List[Dict], filename: str) -> bool:
    """
    Export data to a CSV file.

    Args:
        data: List of dictionaries to export
        filename: Output CSV filename

    Returns:
        bool: True if successful, False otherwise
    """
    if not data:
        print("WARNING: No data to export")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Device Name',
                'Serial Number',
                'Product Model',
                'Product Type',
                'Contract Number',
                'Contract Type',
                'Contract Start Date',
                'Contract Expiration Date',
                'Contract Status'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"SUCCESS: Data exported to {filename}")
        return True
        
    except IOError as e:
        print(f"ERROR: Failed to write CSV file: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error exporting CSV: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 70)
    print("FortiCloud API - FortiGate/FortiWiFi Device Export")
    print("=" * 70)
    print()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment
    client_id = os.getenv('FORTICLOUD_CLIENT_ID')
    client_secret = os.getenv('FORTICLOUD_CLIENT_SECRET')
    auth_url = os.getenv('FORTICLOUD_AUTH_URL')
    api_base_url = os.getenv('FORTICLOUD_API_BASE_URL')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Validate required configuration
    if not all([client_id, client_secret, auth_url, api_base_url]):
        print("ERROR: Missing required environment variables.")
        print("Please ensure the following are set in your .env file:")
        print("  - FORTICLOUD_CLIENT_ID")
        print("  - FORTICLOUD_CLIENT_SECRET")
        print("  - FORTICLOUD_AUTH_URL")
        print("  - FORTICLOUD_API_BASE_URL")
        print()
        print("You can copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    
    # Initialize API client
    api = FortiCloudAPI(
        client_id=client_id,
        client_secret=client_secret,
        auth_url=auth_url,
        api_base_url=api_base_url,
        debug=debug
    )
    
    try:
        # Authenticate
        print("Step 1: Authenticating with FortiCloud...")
        if not api.authenticate():
            print("ERROR: Authentication failed. Please check your credentials.")
            sys.exit(1)
        print("SUCCESS: Authentication complete")
        print()
        
        # Retrieve FortiGate devices
        print("Step 2: Retrieving FortiGate devices...")
        fortigate_devices = api.get_devices(product_type='fortigate')
        print(f"Retrieved {len(fortigate_devices)} FortiGate devices")
        print()
        
        # Retrieve FortiWiFi devices
        print("Step 3: Retrieving FortiWiFi devices...")
        fortiwifi_devices = api.get_devices(product_type='fortiwifi')
        print(f"Retrieved {len(fortiwifi_devices)} FortiWiFi devices")
        print()
        
        # Combine all devices
        all_devices = fortigate_devices + fortiwifi_devices
        print(f"Total devices: {len(all_devices)}")
        print()
        
        if not all_devices:
            print("WARNING: No devices found. This could mean:")
            print("  - No devices are registered in your FortiCloud account")
            print("  - The API credentials don't have proper permissions")
            print("  - The API endpoints may have changed")
            sys.exit(0)
        
        # Flatten data for CSV export
        print("Step 4: Processing device data...")
        flattened_data = flatten_device_data(all_devices)
        print(f"Processed {len(flattened_data)} rows (including contracts)")
        print()
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'fortigate_devices_{timestamp}.csv'
        
        # Export to CSV
        print(f"Step 5: Exporting to CSV ({output_filename})...")
        if export_to_csv(flattened_data, output_filename):
            print()
            print("=" * 70)
            print("EXPORT COMPLETE!")
            print("=" * 70)
            print(f"Output file: {output_filename}")
            print(f"Total rows: {len(flattened_data)}")
            print(f"Unique devices: {len(all_devices)}")
        else:
            print("ERROR: Export failed")
            sys.exit(1)
    
    finally:
        # Clean up
        api.close()


if __name__ == '__main__':
    main()
