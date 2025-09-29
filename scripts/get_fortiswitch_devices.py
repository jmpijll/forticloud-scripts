#!/usr/bin/env python3
"""
FortiCloud API - Get FortiSwitch Devices

Idempotent script that:
1. Discovers all accessible accounts automatically
2. Tests API connectivity
3. Retrieves all FortiSwitch devices
4. Exports to CSV with entitlements/contracts

Author: FortiCloud API Project
Date: September 30, 2025
Version: 2.0 - Idempotent
"""

import os
import sys
import csv
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv


class FortiCloudAPI:
    """FortiCloud API client with automatic account discovery."""

    def __init__(self, username: str, password: str, auth_url: str, api_base_url: str, debug: bool = False):
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.api_base_url = api_base_url.rstrip('/')
        self.debug = debug
        
        self.asset_token: Optional[str] = None
        self.org_token: Optional[str] = None
        self.iam_token: Optional[str] = None
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FortiCloud-API-Script/2.0'
        })

    def _log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def authenticate(self, client_id: str) -> str:
        """Authenticate with FortiCloud API for specific service."""
        try:
            self._log(f"Authenticating with {client_id} API...")
            
            payload = {
                "username": self.username,
                "password": self.password,
                "client_id": client_id,
                "grant_type": "password"
            }
            
            response = self.session.post(self.auth_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            token = data.get('access_token')
            
            if not token:
                raise Exception(f"No access token received for {client_id}")
            
            self._log(f"{client_id} authentication successful")
            return token
            
        except Exception as e:
            print(f"ERROR: Authentication failed for {client_id}: {e}")
            raise

    def discover_accounts(self) -> tuple[List[int], Dict[int, Dict]]:
        """Automatically discover all accessible account IDs and their metadata."""
        print("Discovering accounts...")
        
        try:
            # Get organizational units
            self.org_token = self.authenticate("organization")
            org_data = self._get_organizational_units()
            
            org_id = org_data.get('organizationUnits', {}).get('orgId')
            ou_list = org_data.get('organizationUnits', {}).get('orgUnits', [])
            
            self._log(f"Found organization {org_id} with {len(ou_list)} OUs")
            
            # Build OU mapping
            ou_map = {}
            for ou in ou_list:
                ou_map[ou['id']] = ou.get('name', 'Unknown OU')
            if org_id:
                ou_map[org_id] = org_data.get('organizationUnits', {}).get('name', 'Main Organization')
            
            # Get accounts for each OU
            self.iam_token = self.authenticate("iam")
            all_accounts = []
            account_ids_set = set()
            account_metadata = {}
            
            if org_id:
                accounts = self._get_accounts(org_id)
                all_accounts.extend(accounts)
            
            for ou in ou_list:
                accounts = self._get_accounts(ou['id'])
                all_accounts.extend(accounts)
            
            for account in all_accounts:
                account_id = account['id']
                if account_id not in account_ids_set:
                    account_ids_set.add(account_id)
                    parent_id = account.get('parentId')
                    account_metadata[account_id] = {
                        'company': account.get('company', 'N/A'),
                        'email': account.get('email', 'N/A'),
                        'parent_id': parent_id,
                        'ou_name': ou_map.get(parent_id, 'Unknown')
                    }
            
            account_ids = sorted(list(account_ids_set))
            print(f"Discovered {len(account_ids)} account(s)")
            
            return account_ids, account_metadata
            
        except Exception as e:
            print(f"ERROR: Account discovery failed: {e}")
            raise

    def _get_organizational_units(self) -> dict:
        """Get all organizational units."""
        url = "https://support.fortinet.com/ES/api/organization/v1/units/list"
        headers = {'Authorization': f'Bearer {self.org_token}'}
        
        response = self.session.post(url, headers=headers, json={}, timeout=30)
        response.raise_for_status()
        
        return response.json()

    def _get_accounts(self, parent_id: int) -> List[Dict]:
        """Get accounts for a specific OU."""
        url = "https://support.fortinet.com/ES/api/iam/v1/accounts/list"
        headers = {'Authorization': f'Bearer {self.iam_token}'}
        
        response = self.session.post(url, headers=headers, json={'parentId': parent_id}, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get('accounts', []) if data.get('status') == 0 else []

    def get_devices(self, account_id: int, serial_patterns: List[str] = None) -> List[Dict]:
        """Retrieve devices from a specific account using multiple serial patterns."""
        if serial_patterns is None:
            serial_patterns = ["F", "S"]  # FortiSwitch devices can start with F or S
        
        all_devices = []
        seen_serials = set()
        
        try:
            if not self.asset_token:
                self.asset_token = self.authenticate("assetmanagement")
            
            for pattern in serial_patterns:
                self._log(f"Querying account {account_id} with pattern '{pattern}'...")
                
                headers = {'Authorization': f'Bearer {self.asset_token}'}
                
                payload = {
                    'serialNumber': pattern,
                    'accountId': account_id
                }
                
                endpoint = f"{self.api_base_url}/products/list"
                response = self.session.post(endpoint, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 429:
                    print(f"  WARNING: Rate limit reached for account {account_id}")
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 0:
                    assets = data.get('assets')
                    if assets is None:
                        assets = []
                    
                    # Deduplicate by serial number
                    for asset in assets:
                        serial = asset.get('serialNumber')
                        if serial and serial not in seen_serials:
                            seen_serials.add(serial)
                            all_devices.append(asset)
                
        except Exception as e:
            print(f"  ERROR: Failed to retrieve devices for account {account_id}: {e}")
        
        self._log(f"Account {account_id}: Retrieved {len(all_devices)} unique devices")
        return all_devices

    def close(self) -> None:
        """Close the session."""
        self.session.close()


def flatten_device_data(devices: List[Dict], account_metadata: Dict[int, Dict]) -> List[Dict]:
    """Flatten device data to include one row per entitlement per device."""
    flattened = []
    
    for device in devices:
        serial_number = device.get('serialNumber', 'N/A')
        description = device.get('description', '')
        product_model = device.get('productModel', 'N/A')
        registration_date = device.get('registrationDate', 'N/A')
        folder_path = device.get('folderPath', 'N/A')
        account_id = device.get('accountId')
        device_status = device.get('status', 'N/A')
        is_decommissioned = device.get('isDecommissioned', False)
        
        # Get account metadata
        account_info = account_metadata.get(account_id, {})
        company = account_info.get('company', 'N/A')
        ou_name = account_info.get('ou_name', 'N/A')
        
        entitlements = device.get('entitlements', [])
        
        if not entitlements:
            flattened.append({
                'Serial Number': serial_number,
                'Product Model': product_model,
                'Description': description,
                'Account ID': account_id,
                'Company': company,
                'Organizational Unit': ou_name,
                'Registration Date': registration_date,
                'Device Status': device_status,
                'Is Decommissioned': 'Yes' if is_decommissioned else 'No',
                'Folder Path': folder_path,
                'Support Level': 'No Coverage',
                'Support Type': 'N/A',
                'Start Date': 'N/A',
                'End Date': 'N/A',
                'Contract Status': 'Expired/None'
            })
        else:
            for entitlement in entitlements:
                start_date = entitlement.get('startDate', 'N/A')
                end_date = entitlement.get('endDate', 'N/A')
                
                contract_status = 'Active'
                if end_date != 'N/A':
                    try:
                        from dateutil import parser
                        end_dt = parser.parse(end_date)
                        if end_dt < datetime.now(end_dt.tzinfo):
                            contract_status = 'Expired'
                    except:
                        contract_status = 'Unknown'
                
                flattened.append({
                    'Serial Number': serial_number,
                    'Product Model': product_model,
                    'Description': description,
                    'Account ID': account_id,
                    'Company': company,
                    'Organizational Unit': ou_name,
                    'Registration Date': registration_date,
                    'Device Status': device_status,
                    'Is Decommissioned': 'Yes' if is_decommissioned else 'No',
                    'Folder Path': folder_path,
                    'Support Level': entitlement.get('levelDesc', 'N/A'),
                    'Support Type': entitlement.get('typeDesc', 'N/A'),
                    'Start Date': start_date,
                    'End Date': end_date,
                    'Contract Status': contract_status
                })
    
    return flattened


def export_to_csv(data: List[Dict], filename: str) -> bool:
    """Export data to CSV file."""
    if not data:
        print("WARNING: No data to export")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Serial Number', 'Product Model', 'Description',
                'Account ID', 'Company', 'Organizational Unit',
                'Registration Date', 'Device Status', 'Is Decommissioned',
                'Folder Path', 'Support Level', 'Support Type',
                'Start Date', 'End Date', 'Contract Status'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"SUCCESS: Data exported to {filename}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to export CSV: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 70)
    print("FortiCloud API - FortiSwitch Device Export")
    print("=" * 70)
    print()
    
    # Load environment variables
    load_dotenv()
    
    username = os.getenv('FORTICLOUD_CLIENT_ID')
    password = os.getenv('FORTICLOUD_CLIENT_SECRET')
    auth_url = os.getenv('FORTICLOUD_AUTH_URL')
    api_base_url = os.getenv('FORTICLOUD_API_BASE_URL')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    if not all([username, password, auth_url, api_base_url]):
        print("ERROR: Missing required environment variables.")
        sys.exit(1)
    
    api = FortiCloudAPI(username, password, auth_url, api_base_url, debug)
    
    try:
        # Step 1: Discover accounts
        print("Step 1: Discovering accounts...")
        account_ids, account_metadata = api.discover_accounts()
        print(f"Found {len(account_ids)} account(s)")
        print()
        
        # Step 2: Retrieve all devices then filter by product model
        print(f"Step 2: Retrieving all devices from {len(account_ids)} account(s)...")
        all_devices = []
        for account_id in account_ids:
            devices = api.get_devices(account_id)
            all_devices.extend(devices)
            print(f"  Account {account_id}: {len(devices)} devices")
        print(f"Retrieved {len(all_devices)} total devices")
        print()
        
        # Step 3: Filter for FortiSwitch devices only
        print("Step 3: Filtering FortiSwitch devices...")
        fortiswitch_devices = [
            d for d in all_devices 
            if d.get('productModel', '').startswith('FortiSwitch')
        ]
        print(f"Found {len(fortiswitch_devices)} FortiSwitch devices")
        print()
        
        if not fortiswitch_devices:
            print("WARNING: No FortiSwitch devices found")
            sys.exit(0)
        
        # Step 4: Process data
        print("Step 4: Processing device data...")
        flattened_data = flatten_device_data(fortiswitch_devices, account_metadata)
        print(f"Processed {len(flattened_data)} rows (including entitlements)")
        print()
        
        # Step 5: Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'fortiswitch_devices_{timestamp}.csv'
        
        print(f"Step 5: Exporting to CSV ({output_filename})...")
        if export_to_csv(flattened_data, output_filename):
            print()
            print("=" * 70)
            print("EXPORT COMPLETE!")
            print("=" * 70)
            print(f"Output file: {output_filename}")
            print(f"Total rows: {len(flattened_data)}")
            print(f"Unique devices: {len(fortiswitch_devices)}")
            print()
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        api.close()


if __name__ == '__main__':
    main()
