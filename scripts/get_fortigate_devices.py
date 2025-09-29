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
            
            # FortiCloud uses username/password OAuth with service-specific client_id
            payload = {
                "username": self.client_id,
                "password": self.client_secret,
                "client_id": "assetmanagement",
                "grant_type": "password"
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

    def get_devices(self, account_id: int, product_model_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve all devices from FortiCloud for a specific account.

        Args:
            account_id: Account ID to query
            product_model_filter: Filter by product model (e.g., 'FortiGate', 'FortiWiFi')

        Returns:
            List of device dictionaries
        """
        devices = []
        
        try:
            self._log(f"Fetching devices for account {account_id}...")
            
            # Build request payload - API v3 uses POST with JSON body
            # API requires either serialNumber or expireBefore, plus accountId for Org scope
            # Use 'F' as pattern to match FortiGate devices (FG*, FW*, etc.)
            payload = {
                'serialNumber': 'F',  # Match all Fortinet devices starting with F
                'status': 'Registered',
                'accountId': account_id
            }
            
            if product_model_filter:
                payload['productModel'] = product_model_filter
            
            endpoint = f"{self.api_base_url}/products/list"
            response = self.session.post(endpoint, json=payload, timeout=30)
                
            # Check for rate limiting
            if response.status_code == 429:
                print("WARNING: Rate limit reached")
                return devices
            
            response.raise_for_status()
            data = response.json()
            
            # API v3 returns status: 0 for success
            if data.get('status') == 0:
                assets = data.get('assets', [])
                if assets is None:
                    assets = []
                devices.extend(assets)
                self._log(f"Retrieved {len(devices)} devices")
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"ERROR: API returned error status: {error_msg}")
                return devices
                
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
    Flatten device data to include one row per entitlement (contract) per device.

    Args:
        devices: List of device dictionaries from the API

    Returns:
        List of flattened dictionaries suitable for CSV export
    """
    flattened = []
    
    for device in devices:
        serial_number = device.get('serialNumber', 'N/A')
        description = device.get('description', '')
        product_model = device.get('productModel', 'N/A')
        registration_date = device.get('registrationDate', 'N/A')
        folder_path = device.get('folderPath', 'N/A')
        
        # Entitlements are the support/contract coverage
        entitlements = device.get('entitlements', [])
        
        if not entitlements:
            # If no entitlements, still include the device
            flattened.append({
                'Serial Number': serial_number,
                'Product Model': product_model,
                'Description': description,
                'Registration Date': registration_date,
                'Folder Path': folder_path,
                'Support Level': 'No Coverage',
                'Support Type': 'N/A',
                'Start Date': 'N/A',
                'End Date': 'N/A',
                'Status': 'Expired/None'
            })
        else:
            # Create one row per entitlement (support contract)
            for entitlement in entitlements:
                start_date = entitlement.get('startDate', 'N/A')
                end_date = entitlement.get('endDate', 'N/A')
                
                # Determine status based on end date
                status = 'Active'
                if end_date != 'N/A':
                    try:
                        from dateutil import parser
                        end_dt = parser.parse(end_date)
                        if end_dt < datetime.now(end_dt.tzinfo):
                            status = 'Expired'
                    except:
                        status = 'Unknown'
                
                flattened.append({
                    'Serial Number': serial_number,
                    'Product Model': product_model,
                    'Description': description,
                    'Registration Date': registration_date,
                    'Folder Path': folder_path,
                    'Support Level': entitlement.get('levelDesc', 'N/A'),
                    'Support Type': entitlement.get('typeDesc', 'N/A'),
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Status': status
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
                'Serial Number',
                'Product Model',
                'Description',
                'Registration Date',
                'Folder Path',
                'Support Level',
                'Support Type',
                'Start Date',
                'End Date',
                'Status'
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
    account_ids_str = os.getenv('FORTICLOUD_ACCOUNT_IDS', '')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Validate required configuration
    if not all([client_id, client_secret, auth_url, api_base_url]):
        print("ERROR: Missing required environment variables.")
        print("Please ensure the following are set in your .env file:")
        print("  - FORTICLOUD_CLIENT_ID")
        print("  - FORTICLOUD_CLIENT_SECRET")
        print("  - FORTICLOUD_AUTH_URL")
        print("  - FORTICLOUD_API_BASE_URL")
        print("  - FORTICLOUD_ACCOUNT_IDS")
        print()
        print("See ACCOUNT_ID_HELP.md for help finding your Account ID(s).")
        sys.exit(1)
    
    # Parse account IDs
    if not account_ids_str.strip():
        print("ERROR: FORTICLOUD_ACCOUNT_IDS is required for Org-scope API users.")
        print()
        print("Please add your Account ID(s) to the .env file:")
        print("  FORTICLOUD_ACCOUNT_IDS=1234567")
        print()
        print("For multiple accounts (comma-separated):")
        print("  FORTICLOUD_ACCOUNT_IDS=1234567,2345678,3456789")
        print()
        print("See ACCOUNT_ID_HELP.md for instructions on finding your Account ID.")
        sys.exit(1)
    
    account_ids = [int(aid.strip()) for aid in account_ids_str.split(',') if aid.strip()]
    
    if not account_ids:
        print("ERROR: No valid Account IDs found in FORTICLOUD_ACCOUNT_IDS.")
        sys.exit(1)
    
    print(f"Configured for {len(account_ids)} account(s): {account_ids}")
    print()
    
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
        
        # Retrieve devices from all accounts
        print(f"Step 2: Retrieving devices from {len(account_ids)} account(s)...")
        all_devices = []
        for account_id in account_ids:
            devices = api.get_devices(account_id)
            all_devices.extend(devices)
            print(f"  Account {account_id}: {len(devices)} devices")
        print(f"Retrieved {len(all_devices)} total devices across all accounts")
        print()
        
        # Filter for FortiGate and FortiWiFi devices
        print("Step 3: Filtering FortiGate/FortiWiFi devices...")
        filtered_devices = [d for d in all_devices if 'FortiGate' in d.get('productModel', '') or 'FortiWiFi' in d.get('productModel', '')]
        print(f"Found {len(filtered_devices)} FortiGate/FortiWiFi devices")
        print()
        if not filtered_devices:
            print("WARNING: No FortiGate/FortiWiFi devices found.")
            if all_devices:
                print(f"However, {len(all_devices)} total devices were retrieved.")
                print("Product models found:")
                models = set(d.get('productModel', 'Unknown') for d in all_devices[:10])
                for model in list(models)[:10]:
                    print(f"  - {model}")
            sys.exit(0)
        
        # Flatten data for CSV export
        print("Step 4: Processing device data...")
        flattened_data = flatten_device_data(filtered_devices)
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
            print(f"Unique devices: {len(filtered_devices)}")
        else:
            print("ERROR: Export failed")
            sys.exit(1)
    
    finally:
        # Clean up
        api.close()


if __name__ == '__main__':
    main()
