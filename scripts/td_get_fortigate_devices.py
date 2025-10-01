#!/usr/bin/env python3
"""
TopDesk API - Get FortiGate/FortiWiFi Devices

Idempotent script that:
1. Connects to TopDesk using Basic Authentication
2. Retrieves all Fortinet FortiGate and FortiWiFi firewall devices
3. Gets device details including branch, location, and support contracts
4. Exports to CSV for reporting

Author: TopDesk API Project
Date: October 1, 2025
Version: 1.0
"""

import os
import sys
import csv
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from typing import Dict, List, Optional

class TopDeskAPI:
    """TopDesk API client with Basic Authentication."""

    def __init__(self, host: str, username: str, password: str, debug: bool = False):
        self.host = host.rstrip('/')
        if not self.host.startswith('http'):
            self.host = f'https://{self.host}'
        self.username = username
        self.password = password
        self.debug = debug
        self.base_url = f'{self.host}/tas/api/assetmgmt'
        
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'Accept': 'application/x.topdesk-am-assets-v2+json',
            'User-Agent': 'TopDesk-API-Script/1.0'
        })

    def _log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def get_assets_by_template(self, template_name: str, page_size: int = 1000) -> List[Dict]:
        """
        Get all assets by template name with pagination.

        Args:
            template_name: Template name to filter by
            page_size: Number of results per page (max 1000)

        Returns:
            List of asset dictionaries
        """
        all_assets = []
        page_start = 0  # Use pageStart, not start!
        
        while True:
            params = {
                'templateName': template_name,
                'pageSize': page_size,
                'pageStart': page_start,  # Correct parameter name
                'fields': 'name,@type,@@summary,@assignments,@status,modificationDate,creationDate,serienummer,model,ip-address,host-name,software-versie,vendor,environment-1,aanschafdatum'
            }
            
            self._log(f"Request: GET /assets with params: {params}")
            
            try:
                response = self.session.get(
                    f"{self.base_url}/assets",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                assets = data.get('dataSet', [])
                
                if not assets:
                    break
                
                all_assets.extend(assets)
                self._log(f"Retrieved {len(assets)} assets (total: {len(all_assets)})")
                
                # Check if there are more results
                if len(assets) < page_size:
                    break
                    
                page_start += page_size  # Increment pageStart
                
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed: {e}")
                raise
        
        return all_assets

    def get_linked_assets(self, asset_unid: str) -> List[Dict]:
        """
        Get assets linked to a specific asset (e.g., contracts).

        Args:
            asset_unid: UUID of the source asset

        Returns:
            List of linked asset dictionaries
        """
        try:
            response = self.session.get(
                f"{self.base_url}/assetLinks",
                params={'sourceId': asset_unid},
                headers={'Accept': 'application/json'},  # Use basic JSON accept header
                timeout=30
            )
            response.raise_for_status()
            
            links = response.json()
            self._log(f"Found {len(links)} linked assets for {asset_unid}")
            return links
            
        except requests.exceptions.RequestException as e:
            # Silently log but don't stop execution
            self._log(f"Failed to retrieve linked assets for {asset_unid}: {e}")
            return []
    
    def get_asset_detail(self, asset_id: str) -> Optional[Dict]:
        """
        Get full details of a specific asset including all custom fields.

        Args:
            asset_id: The unique identifier of the asset

        Returns:
            Dictionary with full asset details or None if failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/assets/{asset_id}",
                headers={'Accept': 'application/json'},
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log(f"Failed to retrieve asset detail for {asset_id}: {e}")
            return None

    def close(self) -> None:
        """Close the session."""
        self.session.close()


def filter_fortigate_devices(assets: List[Dict]) -> List[Dict]:
    """
    Filter assets to only include Fortinet FortiGate and FortiWiFi firewalls.
    
    Excludes FortiWAF and other non-FortiGate Fortinet devices.

    Args:
        assets: List of all asset dictionaries

    Returns:
        Filtered list of FortiGate/FortiWiFi devices
    """
    fortigate_devices = []
    
    for asset in assets:
        summary = asset.get('@@summary', '').lower()
        name = asset.get('name', '').lower()
        type_name = asset.get('@type', {}).get('name', '').lower()
        
        # Must be a firewall type
        if not ('firewall' in type_name or 'fwl' in type_name):
            continue
        
        # Must have Fortinet in summary
        if 'fortinet' not in summary:
            continue
        
        # Exclude FortiWAF explicitly
        if 'fortiwaf' in summary:
            continue
        
        # Include if any of these patterns match:
        # - "fortigate" or "fortiwifi" explicitly mentioned
        # - "fgt" (FortiGate abbreviation)
        # - "fg-" (FortiGate prefix)
        # - "fortinet vm" (VM models)
        # - Model numbers like "40F", "60F", "70G", "100F", etc.
        if any([
            'fortigate' in summary,
            'fortiwifi' in summary,
            'fgt' in summary or 'fgt' in name,
            'fg-' in summary or 'fg-' in name,
            'fortinet vm' in summary,
            # Common FortiGate model patterns
            any(model in summary for model in [
                '30e', '40f', '60f', '70g', '80f', '90g', '100f', '200f', '300f',
                '600f', '40f-3g4g', 'vm01v', 'vm02v', 'vm04v', 'vm08v'
            ])
        ]):
            fortigate_devices.append(asset)
    
    return fortigate_devices


def enrich_with_contracts(api: TopDeskAPI, devices: List[Dict]) -> List[Dict]:
    """
    Enrich device data with support contract information including dates.

    Args:
        api: TopDeskAPI instance
        devices: List of device dictionaries

    Returns:
        List of enriched device dictionaries
    """
    print("Retrieving support contracts for devices...")
    
    for i, device in enumerate(devices, 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(devices)} devices...")
        
        asset_unid = device.get('unid')
        if not asset_unid:
            continue
        
        # Get linked assets
        linked_assets = api.get_linked_assets(asset_unid)
        
        # Filter for support contracts and enrich with full details
        contracts = []
        for link in linked_assets:
            if 'support' in link.get('type', '').lower() or 'contract' in link.get('type', '').lower() or 'license' in link.get('type', '').lower():
                # Get full contract details including dates
                contract_id = link.get('assetId')
                if contract_id:
                    contract_detail = api.get_asset_detail(contract_id)
                    if contract_detail and 'data' in contract_detail:
                        data = contract_detail['data']
                        contracts.append({
                            'name': link.get('name', 'N/A'),
                            'type': link.get('type', 'N/A'),
                            'summary': link.get('summary', 'N/A'),
                            'status': link.get('status', 'N/A'),
                            'archived': link.get('archived', False),
                            'start_date': data.get('aanschafdatum', 'N/A'),  # Purchase/start date
                            'expiration_date': data.get('vervaldatum', 'N/A'),  # Expiration date
                            'vendor_id': data.get('vendor', 'N/A'),
                            'contract_type_id': data.get('contract-type', 'N/A')
                        })
                    else:
                        # Fallback to basic info if detail retrieval fails
                        contracts.append({
                            'name': link.get('name', 'N/A'),
                            'type': link.get('type', 'N/A'),
                            'summary': link.get('summary', 'N/A'),
                            'status': link.get('status', 'N/A'),
                            'archived': link.get('archived', False),
                            'start_date': 'N/A',
                            'expiration_date': 'N/A',
                            'vendor_id': 'N/A',
                            'contract_type_id': 'N/A'
                        })
        
        device['contracts'] = contracts
    
    print(f"  Completed contract retrieval for {len(devices)} devices")
    return devices


def format_date(date_str: str) -> str:
    """
    Format TopDesk date string to YYYY-MM-DD format.
    
    Args:
        date_str: Date string in format '2024-11-19T23:00:00.000' or 'N/A'
    
    Returns:
        Formatted date string 'YYYY-MM-DD' or 'N/A'
    """
    if not date_str or date_str == 'N/A':
        return 'N/A'
    
    try:
        # TopDesk format: '2024-11-19T23:00:00.000'
        return date_str.split('T')[0]  # Extract just the date part
    except:
        return date_str  # Return as-is if parsing fails


def extract_serial_from_text(text: str) -> Optional[str]:
    """
    Extract Fortinet serial number from text (contracts, names, etc.).
    
    FortiGate serials start with: FG, FGT, FGVM
    Also checks for SUP.SERIALNUMBER pattern in contract names.
    Returns first match or None.
    """
    import re
    
    # First try FortiGate serial patterns: FG/FGT/FGVM followed by alphanumeric
    matches = re.findall(r'\b(FG[TVW]?[A-Z0-9]{6,})\b', text, re.IGNORECASE)
    if matches:
        return matches[0]
    
    # Try contract pattern: SUP.IDENTIFIER.SERIALNUMBER or SUP.SERIALNUMBER
    # Extract the last part after SUP. which should be the serial
    sup_matches = re.findall(r'SUP\.(?:[A-Z0-9]+\.)?([A-Z0-9]{8,})', text, re.IGNORECASE)
    if sup_matches:
        return sup_matches[0]
    
    return None


def flatten_device_data(devices: List[Dict]) -> List[Dict]:
    """
    Flatten device data for CSV export with comparable fields to FortiManager/FortiCloud.

    Args:
        devices: List of device dictionaries

    Returns:
        List of flattened dictionaries for CSV export
    """
    flattened = []
    
    for device in devices:
        # Extract base information
        name = device.get('name', 'N/A')
        summary = device.get('@@summary', 'N/A')
        type_name = device.get('@type', {}).get('name', 'N/A')
        status = device.get('@status', 'N/A')
        archived = device.get('archived', False)
        mod_date = device.get('modificationDate', 'N/A')
        
        # Extract additional fields - TopDesk returns them as direct properties
        serial_number_td = device.get('serienummer', '') or ''
        model_td = device.get('model', '') or ''
        ip_address_td = device.get('ip-address', '') or ''
        hostname_td = device.get('host-name', '') or ''
        firmware_td = device.get('software-versie', '') or ''
        vendor_td = device.get('vendor', '') or ''
        environment_td = device.get('environment-1', '') or ''
        creation_date_td = device.get('creationDate', '') or ''
        purchase_date_td = device.get('aanschafdatum', '') or ''
        
        # Use vendor from TopDesk field if available, otherwise parse from summary
        vendor = vendor_td if vendor_td else ('Fortinet' if 'fortinet' in summary.lower() else 'Unknown')
        
        # Use model from TopDesk field if available, otherwise parse from summary
        model = model_td  # Use the direct field first
        
        # If model field is empty, try to extract from summary
        if not model and 'fortinet' in summary.lower():
            parts = summary.split()
            for i, part in enumerate(parts):
                if 'fortigate' in part.lower() or 'fortiwifi' in part.lower():
                    if i + 1 < len(parts):
                        model = f"{part} {parts[i+1]}"
                    else:
                        model = part
                    break
        
        if not model:
            model = 'Unknown'
        
        # Extract location information
        assignments = device.get('@assignments', {})
        locations = assignments.get('locations', [])
        
        branch_name = 'N/A'
        location_name = 'N/A'
        
        if locations:
            first_location = locations[0]
            branch = first_location.get('branch', {})
            branch_name = branch.get('name', 'N/A')
            
            location = first_location.get('location', {})
            if location:
                location_name = location.get('name', 'N/A')
        
        # Try to extract serial number from various sources
        serial_number = serial_number_td or ''
        
        # Extract contract information and look for serial in contract names
        contracts = device.get('contracts', [])
        contract_serials = []
        
        for contract in contracts:
            contract_name = contract.get('name', '')
            # Try to extract serial from contract name (e.g., "SUP.FGT70GTK25008471")
            serial_from_contract = extract_serial_from_text(contract_name)
            if serial_from_contract:
                contract_serials.append(serial_from_contract)
        
        # Use first found serial
        if not serial_number and contract_serials:
            serial_number = contract_serials[0]
        
        # Try to extract from summary or name as fallback
        if not serial_number:
            serial_number = extract_serial_from_text(summary) or extract_serial_from_text(name) or 'N/A'
        
        # Build unified 60-field structure
        if contracts:
            # Create a row for each contract
            for contract in contracts:
                row = {
                    # Section 1: Core Identification
                    'Serial Number': serial_number,
                    'Device Name': name,
                    'Hostname': hostname_td or name,
                    'Model': model,
                    'Description': summary,
                    'Asset Type': 'Firewall',
                    'Source System': 'TopDesk',
                    
                    # Section 2: Network & Connection
                    'Management IP': ip_address_td or '',
                    'Connection Status': status,
                    'Management Mode': '',
                    'Firmware Version': firmware_td or '',
                    
                    # Section 3: Organization & Location
                    'Company': '',
                    'Organizational Unit': '',
                    'Branch': branch_name if branch_name != 'N/A' else '',
                    'Location': location_name if location_name != 'N/A' else '',
                    'Folder Path': '',
                    'Folder ID': '',
                    'Vendor': vendor,
                    
                    # Section 4: Contract Information
                    'Contract Number': contract.get('name', ''),
                    'Contract SKU': '',
                    'Contract Type': contract.get('type', ''),
                    'Contract Summary': contract.get('summary', ''),
                    'Contract Start Date': format_date(contract.get('start_date', '')),
                    'Contract Expiration Date': format_date(contract.get('expiration_date', '')),
                    'Contract Status': contract.get('status', ''),
                    'Contract Support Type': '',
                    'Contract Archived': 'Yes' if contract.get('archived', False) else 'No',
                    
                    # Section 5: Entitlement Information (empty)
                    'Entitlement Level': '',
                    'Entitlement Type': '',
                    'Entitlement Start Date': '',
                    'Entitlement End Date': '',
                    
                    # Section 6: Lifecycle & Status
                    'Status': status,
                    'Is Decommissioned': '',
                    'Archived': 'Yes' if archived else 'No',
                    'Registration Date': '',
                    'Product EoR': '',
                    'Product EoS': '',
                    'Last Updated': mod_date,
                    
                    # Section 7: Account Information (empty)
                    'Account ID': '',
                    'Account Email': '',
                    'Account OU ID': '',
                    
                    # Section 8: FortiGate-Specific Fields (empty)
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
                flattened.append(row)
        else:
            # Create a single row without contract
            row = {
                # Section 1: Core Identification
                'Serial Number': serial_number,
                'Device Name': name,
                'Hostname': hostname_td or name,
                'Model': model,
                'Description': summary,
                'Asset Type': 'Firewall',
                'Source System': 'TopDesk',
                
                # Section 2: Network & Connection
                'Management IP': ip_address_td or '',
                'Connection Status': status,
                'Management Mode': '',
                'Firmware Version': firmware_td or '',
                
                # Section 3: Organization & Location
                'Company': '',
                'Organizational Unit': '',
                'Branch': branch_name if branch_name != 'N/A' else '',
                'Location': location_name if location_name != 'N/A' else '',
                'Folder Path': '',
                'Folder ID': '',
                'Vendor': vendor,
                
                # Section 4: Contract Information (empty)
                'Contract Number': '',
                'Contract SKU': '',
                'Contract Type': '',
                'Contract Summary': '',
                'Contract Start Date': '',
                'Contract Expiration Date': '',
                'Contract Status': '',
                'Contract Support Type': '',
                'Contract Archived': '',
                
                # Section 5: Entitlement Information (empty)
                'Entitlement Level': '',
                'Entitlement Type': '',
                'Entitlement Start Date': '',
                'Entitlement End Date': '',
                
                # Section 6: Lifecycle & Status
                'Status': status,
                'Is Decommissioned': '',
                'Archived': 'Yes' if archived else 'No',
                'Registration Date': '',
                'Product EoR': '',
                'Product EoS': '',
                'Last Updated': mod_date,
                
                # Section 7: Account Information (empty)
                'Account ID': '',
                'Account Email': '',
                'Account OU ID': '',
                
                # Section 8: FortiGate-Specific Fields (empty)
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
            flattened.append(row)
    
    return flattened


def export_to_csv(data: List[Dict], filename: str) -> bool:
    """Export data to CSV file."""
    if not data:
        print("WARNING: No data to export")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
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
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"SUCCESS: Data exported to {filename}")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to export CSV: {e}")
        return False


def load_config_from_file(filepath: str) -> Dict[str, str]:
    """
    Load configuration from a key=value format file.

    Args:
        filepath: Path to config file

    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    if not os.path.exists(filepath):
        return config
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"WARNING: Failed to read config file {filepath}: {e}")
    
    return config


def main():
    """Main execution function."""
    print("=" * 70)
    print("TopDesk API - FortiGate/FortiWiFi Device Export")
    print("=" * 70)
    print()
    
    # Try loading from config file first
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'topdeskapikey')
    file_config = load_config_from_file(config_file)
    
    # Get configuration from file or environment
    host = file_config.get('topdesk-url') or os.getenv('TOPDESK_URL')
    username = file_config.get('topdesk-user') or os.getenv('TOPDESK_USER')
    password = file_config.get('topdesk-pass') or os.getenv('TOPDESK_PASSWORD')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Validate configuration
    if not all([host, username, password]):
        print("ERROR: Missing required configuration.")
        print("Please provide configuration either via:")
        print("  1. 'topdeskapikey' file with 'topdesk-url', 'topdesk-user', 'topdesk-pass' fields")
        print("  2. Environment variables:")
        print("     - TOPDESK_URL")
        print("     - TOPDESK_USER")
        print("     - TOPDESK_PASSWORD")
        sys.exit(1)
    
    print(f"TopDesk URL: {host}")
    print(f"Username: {username}")
    print(f"Debug Mode: {debug}")
    print()
    
    # Initialize API client
    api = TopDeskAPI(host, username, password, debug)
    
    try:
        # Step 1: Get all Firewall [FWL] assets
        print("Step 1: Retrieving all Firewall [FWL] assets...")
        all_assets = api.get_assets_by_template('Firewall [FWL]')
        print(f"Retrieved {len(all_assets)} firewall assets")
        print()
        
        # Step 2: Filter for Fortinet FortiGate/FortiWiFi devices
        print("Step 2: Filtering for Fortinet FortiGate/FortiWiFi devices...")
        fortigate_devices = filter_fortigate_devices(all_assets)
        print(f"Found {len(fortigate_devices)} Fortinet FortiGate/FortiWiFi devices")
        print()
        
        if not fortigate_devices:
            print("WARNING: No FortiGate/FortiWiFi devices found")
            sys.exit(0)
        
        # Step 3: Enrich with contract information
        print("Step 3: Enriching with support contracts...")
        enriched_devices = enrich_with_contracts(api, fortigate_devices)
        print()
        
        # Step 4: Flatten device data
        print("Step 4: Processing device data...")
        flattened_data = flatten_device_data(enriched_devices)
        print(f"Processed {len(flattened_data)} rows")
        print()
        
        # Step 5: Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'td_fortigate_devices_{timestamp}.csv'
        
        print(f"Step 5: Exporting to CSV ({output_filename})...")
        if export_to_csv(flattened_data, output_filename):
            print()
            print("=" * 70)
            print("EXPORT COMPLETE!")
            print("=" * 70)
            print(f"Output file: {output_filename}")
            print(f"Total devices: {len(fortigate_devices)}")
            print(f"Total rows (with contracts): {len(flattened_data)}")
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
