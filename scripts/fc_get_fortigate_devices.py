#!/usr/bin/env python3
"""
FortiCloud API - Get FortiGate/FortiWiFi Devices

Idempotent script that:
1. Authenticates with FortiCloud using OAuth 2.0 Password Grant
2. Discovers all organizational units and accounts
3. Retrieves all FortiGate and FortiWiFi devices
4. Exports to CSV with contract and entitlement information

Author: FortiCloud API Project
Date: October 1, 2025
Version: 2.0
"""

import os
import sys
import csv
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

class FortiCloudAPI:
    """FortiCloud API client with OAuth 2.0 authentication."""

    def __init__(self, username: str, password: str, auth_url: str, debug: bool = False):
        self.username = username
        self.password = password
        self.auth_url = auth_url
        self.debug = debug
        
        # API base URLs
        self.org_base_url = "https://support.fortinet.com/ES/api/organization/v1"
        self.iam_base_url = "https://support.fortinet.com/ES/api/iam/v1"
        self.asset_base_url = "https://support.fortinet.com/ES/api/registration/v3"
        
        # Token cache
        self.tokens = {}

    def _log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def get_token(self, client_id: str) -> Optional[str]:
        """
        Get OAuth token for specific service.
        
        Args:
            client_id: Service client ID (organization, iam, assetmanagement)
        
        Returns:
            Access token string or None if authentication fails
        """
        if client_id in self.tokens:
            return self.tokens[client_id]
        
        self._log(f"Requesting token for client_id: {client_id}")
        
        try:
            response = requests.post(
                self.auth_url,
                json={
                    "username": self.username,
                    "password": self.password,
                    "client_id": client_id,
                    "grant_type": "password"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            token = data.get('access_token')
            
            if token:
                self.tokens[client_id] = token
                self._log(f"Successfully obtained token for {client_id}")
                return token
            else:
                print(f"ERROR: No access_token in response for {client_id}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to get token for {client_id}: {e}")
            return None

    def get_organizational_units(self) -> List[Dict]:
        """
        Get all organizational units.
        
        Returns:
            List of OU dictionaries with id, name, parentID
        """
        token = self.get_token("organization")
        if not token:
            return []
        
        self._log("Retrieving organizational units")
        
        try:
            response = requests.post(
                f"{self.org_base_url}/units/list",
                json={},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 0:
                org_units = data.get('organizationUnits', {}).get('orgUnits', [])
                self._log(f"Found {len(org_units)} organizational units")
                return org_units
            else:
                print(f"ERROR: API returned status {data.get('status')}: {data.get('message')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to get organizational units: {e}")
            return []

    def get_accounts_for_ou(self, ou_id: int) -> List[Dict]:
        """
        Get all accounts for a specific OU.
        
        Args:
            ou_id: Organizational unit ID
        
        Returns:
            List of account dictionaries
        """
        token = self.get_token("iam")
        if not token:
            return []
        
        self._log(f"Retrieving accounts for OU {ou_id}")
        
        try:
            response = requests.post(
                f"{self.iam_base_url}/accounts/list",
                json={"parentId": ou_id},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 0:
                accounts = data.get('accounts', [])
                self._log(f"Found {len(accounts)} accounts in OU {ou_id}")
                return accounts
            else:
                print(f"ERROR: API returned status {data.get('status')}: {data.get('message')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to get accounts for OU {ou_id}: {e}")
            return []

    def get_devices_for_account(self, account_id: int, serial_pattern: str) -> List[Dict]:
        """
        Get all devices for an account matching serial pattern.
        
        Args:
            account_id: Account ID
            serial_pattern: Serial number pattern to match (e.g., "F" for FortiGate)
        
        Returns:
            List of device dictionaries
        """
        token = self.get_token("assetmanagement")
        if not token:
            return []
        
        self._log(f"Retrieving devices for account {account_id} with pattern '{serial_pattern}'")
        
        try:
            response = requests.post(
                f"{self.asset_base_url}/products/list",
                json={
                    "accountId": account_id,
                    "serialNumber": serial_pattern
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 0:
                devices = data.get('assets', [])
                if devices is None:
                    devices = []
                self._log(f"Found {len(devices)} devices for account {account_id}")
                return devices
            else:
                # Status != 0 might just mean no devices found
                if data.get('status') != 1008:  # 1008 = No records found
                    self._log(f"API returned status {data.get('status')}: {data.get('message')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to get devices for account {account_id}: {e}")
            return []


def discover_all_accounts(api: FortiCloudAPI) -> Dict[int, Dict]:
    """
    Discover all accounts across all OUs.
    
    Returns:
        Dictionary mapping account_id to account metadata
    """
    print("Discovering organizational structure...")
    
    ous = api.get_organizational_units()
    if not ous:
        print("ERROR: No organizational units found")
        return {}
    
    print(f"Found {len(ous)} organizational units")
    
    accounts_map = {}
    
    for ou in ous:
        ou_id = ou.get('id')
        ou_name = ou.get('name', 'Unknown')
        
        print(f"  Querying accounts in OU: {ou_name} (ID: {ou_id})")
        
        accounts = api.get_accounts_for_ou(ou_id)
        
        for account in accounts:
            account_id = account.get('id')
            if account_id and account_id not in accounts_map:
                accounts_map[account_id] = {
                    'id': account_id,
                    'company': account.get('company', ''),
                    'email': account.get('email', ''),
                    'ou_name': ou_name,
                    'ou_id': ou_id
                }
        
        print(f"    Found {len(accounts)} accounts")
    
    print(f"\nTotal unique accounts discovered: {len(accounts_map)}")
    return accounts_map


def retrieve_fortigate_devices(api: FortiCloudAPI, accounts_map: Dict[int, Dict]) -> List[Dict]:
    """
    Retrieve all FortiGate/FortiWiFi devices across all accounts.
    
    Returns:
        List of device dictionaries enriched with account metadata
    """
    print("\nRetrieving FortiGate/FortiWiFi devices...")
    
    all_devices = []
    serial_pattern = "F"  # FortiGate devices start with F
    
    for account_id, account_info in accounts_map.items():
        company = account_info.get('company', 'Unknown')
        print(f"  Querying account: {company} (ID: {account_id})")
        
        devices = api.get_devices_for_account(account_id, serial_pattern)
        
        # Filter for FortiGate/FortiWiFi only
        fortigate_devices = [
            d for d in devices 
            if d.get('productModel', '').startswith(('FortiGate', 'FortiWiFi'))
        ]
        
        # Enrich with account metadata
        for device in fortigate_devices:
            device['account_company'] = account_info.get('company', '')
            device['account_email'] = account_info.get('email', '')
            device['account_ou_name'] = account_info.get('ou_name', '')
            device['account_ou_id'] = account_info.get('ou_id', '')
        
        all_devices.extend(fortigate_devices)
        
        if fortigate_devices:
            print(f"    Found {len(fortigate_devices)} FortiGate/FortiWiFi devices")
    
    print(f"\nTotal FortiGate/FortiWiFi devices retrieved: {len(all_devices)}")
    return all_devices


def flatten_device_data(device: Dict) -> Dict:
    """
    Flatten device data for CSV export with comparable fields to other systems.
    
    Args:
        device: Device dictionary from API
    
    Returns:
        Flattened dictionary for CSV row
    """
    # Extract primary contract (first contract if exists)
    contracts = device.get('contracts', [])
    primary_contract = contracts[0] if contracts else {}
    
    # Extract primary contract term (first term if exists)
    terms = primary_contract.get('terms', [])
    primary_term = terms[0] if terms else {}
    
    # Extract primary entitlement (first entitlement if exists)
    entitlements = device.get('entitlements', [])
    primary_entitlement = entitlements[0] if entitlements else {}
    
    # Unified 60-field structure
    return {
        # Section 1: Core Identification
        'Serial Number': device.get('serialNumber', ''),
        'Device Name': device.get('description', ''),
        'Hostname': '',
        'Model': device.get('productModel', ''),
        'Description': device.get('description', ''),
        'Asset Type': 'Firewall',
        'Source System': 'FortiCloud',
        
        # Section 2: Network & Connection
        'Management IP': '',
        'Connection Status': device.get('status', ''),
        'Management Mode': '',
        'Firmware Version': '',
        
        # Section 3: Organization & Location
        'Company': device.get('account_company', ''),
        'Organizational Unit': device.get('account_ou_name', ''),
        'Branch': '',
        'Location': '',
        'Folder Path': device.get('folderPath', ''),
        'Folder ID': str(device.get('folderId', '')) if device.get('folderId') else '',
        'Vendor': 'Fortinet',
        
        # Section 4: Contract Information
        'Contract Number': primary_contract.get('contractNumber', ''),
        'Contract SKU': primary_contract.get('sku', ''),
        'Contract Type': '',
        'Contract Summary': '',
        'Contract Start Date': format_date(primary_term.get('startDate')),
        'Contract Expiration Date': format_date(primary_term.get('endDate')),
        'Contract Status': 'OPERATIONAL' if device.get('status') == 'Registered' else '',
        'Contract Support Type': primary_term.get('supportType', ''),
        'Contract Archived': 'No',
        
        # Section 5: Entitlement Information
        'Entitlement Level': primary_entitlement.get('levelDesc', ''),
        'Entitlement Type': primary_entitlement.get('typeDesc', ''),
        'Entitlement Start Date': format_date(primary_entitlement.get('startDate')),
        'Entitlement End Date': format_date(primary_entitlement.get('endDate')),
        
        # Section 6: Lifecycle & Status
        'Status': device.get('status', ''),
        'Is Decommissioned': 'Yes' if device.get('isDecommissioned') else 'No',
        'Archived': 'Yes' if device.get('isDecommissioned') else 'No',
        'Registration Date': format_date(device.get('registrationDate')),
        'Product EoR': format_date(device.get('productModelEoR')),
        'Product EoS': format_date(device.get('productModelEoS')),
        'Last Updated': format_date(device.get('registrationDate')),
        
        # Section 7: Account Information
        'Account ID': str(device.get('accountId', '')) if device.get('accountId') else '',
        'Account Email': device.get('account_email', ''),
        'Account OU ID': str(device.get('account_ou_id', '')) if device.get('account_ou_id') else '',
        
        # Section 8: FortiGate-Specific Fields (empty for FortiCloud)
        'HA Mode': '',
        'HA Cluster Name': '',
        'HA Role': '',
        'HA Member Status': '',
        'HA Priority': '',
        'Max VDOMs': '',
        
        # Section 9: FortiSwitch/FortiAP Parent Tracking (empty)
        'Parent FortiGate': '',
        'Parent FortiGate Serial': '',
        'Parent FortiGate Platform': '',
        'Parent FortiGate IP': '',
        
        # Section 10: FortiSwitch-Specific Fields (empty)
        'Device Type': '',
        'Max PoE Budget': '',
        'Join Time': '',
        
        # Section 11: FortiAP-Specific Fields (empty)
        'Board MAC': '',
        'Admin Status': '',
        'Client Count': '',
        'Mesh Uplink': '',
        'WTP Mode': '',
        'VDOM': ''
    }


def format_date(date_str: Optional[str]) -> str:
    """
    Format date string to YYYY-MM-DD.
    
    Args:
        date_str: Date string in ISO format (e.g., "2023-05-15T10:20:30")
    
    Returns:
        Formatted date string or empty string if invalid
    """
    if not date_str:
        return ''
    
    try:
        # Handle ISO format with time
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        # Handle date-only format
        else:
            return date_str.split(' ')[0]  # Take date part only
    except (ValueError, AttributeError):
        return date_str  # Return as-is if parsing fails


def export_to_csv(devices: List[Dict], output_file: str) -> None:
    """
    Export devices to CSV file.
    
    Args:
        devices: List of flattened device dictionaries
        output_file: Path to output CSV file
    """
    if not devices:
        print("No devices to export")
        return
    
    # Unified 60-field structure - same order for all systems
    fieldnames = [
        'Serial Number', 'Device Name', 'Hostname', 'Model', 'Description', 
        'Asset Type', 'Source System',
        'Management IP', 'Connection Status', 'Management Mode', 'Firmware Version',
        'Company', 'Organizational Unit', 'Branch', 'Location', 
        'Folder Path', 'Folder ID', 'Vendor',
        'Contract Number', 'Contract SKU', 'Contract Type', 'Contract Summary',
        'Contract Start Date', 'Contract Expiration Date', 'Contract Status',
        'Contract Support Type', 'Contract Archived',
        'Entitlement Level', 'Entitlement Type', 
        'Entitlement Start Date', 'Entitlement End Date',
        'Status', 'Is Decommissioned', 'Archived', 'Registration Date',
        'Product EoR', 'Product EoS', 'Last Updated',
        'Account ID', 'Account Email', 'Account OU ID',
        'HA Mode', 'HA Cluster Name', 'HA Role', 'HA Member Status', 
        'HA Priority', 'Max VDOMs',
        'Parent FortiGate', 'Parent FortiGate Serial', 
        'Parent FortiGate Platform', 'Parent FortiGate IP',
        'Device Type', 'Max PoE Budget', 'Join Time',
        'Board MAC', 'Admin Status', 'Client Count', 'Mesh Uplink', 
        'WTP Mode', 'VDOM'
    ]
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(devices)
        
        print(f"\nSuccessfully exported {len(devices)} devices to: {output_file}")
        
    except IOError as e:
        print(f"ERROR: Failed to write CSV file: {e}")


def load_credentials() -> Dict[str, str]:
    """
    Load FortiCloud credentials from environment or .env file.
    
    Returns:
        Dictionary with credentials
    """
    load_dotenv()
    
    username = os.getenv('FORTICLOUD_USERNAME') or os.getenv('FORTICLOUD_CLIENT_ID')
    password = os.getenv('FORTICLOUD_PASSWORD') or os.getenv('FORTICLOUD_CLIENT_SECRET')
    auth_url = os.getenv('FORTICLOUD_AUTH_URL')
    
    if not all([username, password, auth_url]):
        print("ERROR: Missing required environment variables:")
        if not username:
            print("  - FORTICLOUD_USERNAME (or FORTICLOUD_CLIENT_ID)")
        if not password:
            print("  - FORTICLOUD_PASSWORD (or FORTICLOUD_CLIENT_SECRET)")
        if not auth_url:
            print("  - FORTICLOUD_AUTH_URL")
        print("\nPlease set these in your .env file or environment.")
        sys.exit(1)
    
    return {
        'username': username,
        'password': password,
        'auth_url': auth_url
    }


def main():
    """Main execution function."""
    print("=" * 80)
    print("FortiCloud API - FortiGate/FortiWiFi Device Export")
    print("=" * 80)
    print()
    
    # Load credentials
    creds = load_credentials()
    
    # Initialize API client
    api = FortiCloudAPI(
        username=creds['username'],
        password=creds['password'],
        auth_url=creds['auth_url'],
        debug=False
    )
    
    # Discover all accounts
    accounts_map = discover_all_accounts(api)
    if not accounts_map:
        print("ERROR: No accounts found. Cannot proceed.")
        sys.exit(1)
    
    # Retrieve devices
    devices = retrieve_fortigate_devices(api, accounts_map)
    if not devices:
        print("WARNING: No FortiGate/FortiWiFi devices found.")
    
    # Flatten device data
    flattened_devices = [flatten_device_data(d) for d in devices]
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'fc_fortigate_devices_{timestamp}.csv'
    
    # Export to CSV
    export_to_csv(flattened_devices, output_file)
    
    print("\n" + "=" * 80)
    print("Export complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

