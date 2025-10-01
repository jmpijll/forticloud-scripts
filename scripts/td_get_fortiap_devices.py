#!/usr/bin/env python3
"""
TopDesk API - FortiAP Device Export

This script retrieves all Fortinet FortiAP devices from TopDesk
and exports them to a CSV file with contract information including dates.
"""

import os
import csv
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
from datetime import datetime


class TopDeskAPI:
    def __init__(self, base_url: str, username: str, password: str, debug: bool = False):
        """Initialize TopDesk API client."""
        self.base_url = base_url.rstrip('/') + '/tas/api/assetmgmt'
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'Accept': 'application/x.topdesk-am-assets-v2+json',
            'Content-Type': 'application/json'
        })
        self.debug = debug

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
        page_start = 0

        while True:
            params = {
                'templateName': template_name,
                'pageSize': page_size,
                'pageStart': page_start,
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

                page_start += page_size

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
                headers={'Accept': 'application/json'},
                timeout=30
            )
            response.raise_for_status()

            links = response.json()
            self._log(f"Found {len(links)} linked assets for {asset_unid}")
            return links

        except requests.exceptions.RequestException as e:
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


def load_config():
    """Load configuration from environment or config file."""
    config_file = 'topdeskapikey'

    if os.path.exists(config_file):
        config = {}
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

        return {
            'url': config.get('topdesk-url'),
            'username': config.get('topdesk-user'),
            'password': config.get('topdesk-pass')
        }
    else:
        return {
            'url': os.getenv('TOPDESK_URL'),
            'username': os.getenv('TOPDESK_USER'),
            'password': os.getenv('TOPDESK_PASSWORD')
        }


def filter_fortiap_devices(assets: List[Dict]) -> List[Dict]:
    """
    Filter assets to get only FortiAP devices.
    
    Uses OR logic to match ANY of these conditions:
    - Summary contains "FortiAP"
    - Summary contains "Fortinet" with common FortiAP patterns
    - Common FortiAP model numbers
    
    Args:
        assets: List of all assets
        
    Returns:
        List of FortiAP devices
    """
    fortiap_devices = []
    
    for asset in assets:
        summary = asset.get('@@summary', '').lower()
        name = asset.get('name', '').lower()
        type_name = asset.get('@type', {}).get('name', '').lower()

        if not ('access point' in type_name or 'wap' in type_name or 'wireless' in type_name):
            continue

        is_fortiap = any([
            'fortiap' in summary,
            'fortinet' in summary and 'fap-' in summary,
            'fortinet' in summary and 'fap' in summary.split(),
            any(model in summary for model in [
                '112', '221', '223', '224', '231', '233', '234',
                '321', '323', '331', '332', '431', '432', '433',
                'fap-112', 'fap-221', 'fap-223', 'fap-224',
                'fap-231', 'fap-233', 'fap-234', 'fap-321',
                'fap-323', 'fap-331', 'fap-332', 'fap-431',
                'fap-432', 'fap-433', 'u231f', 'u234f', 'u431f'
            ])
        ])

        if is_fortiap:
            fortiap_devices.append(asset)

    return fortiap_devices


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

        linked_assets = api.get_linked_assets(asset_unid)

        contracts = []
        for link in linked_assets:
            if 'support' in link.get('type', '').lower() or 'contract' in link.get('type', '').lower() or 'license' in link.get('type', '').lower():
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
                            'start_date': data.get('aanschafdatum', 'N/A'),
                            'expiration_date': data.get('vervaldatum', 'N/A'),
                            'vendor_id': data.get('vendor', 'N/A'),
                            'contract_type_id': data.get('contract-type', 'N/A')
                        })
                    else:
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
    """Format TopDesk date string to YYYY-MM-DD format."""
    if not date_str or date_str == 'N/A':
        return 'N/A'
    
    try:
        return date_str.split('T')[0]
    except:
        return date_str


def extract_serial_from_text(text: str) -> Optional[str]:
    """Extract Fortinet serial number from text."""
    import re
    
    matches = re.findall(r'\b(FP[A-Z0-9]{6,}|FAP[A-Z0-9]{6,}|F\d{3}[A-Z]{2}[A-Z0-9]{6,})\b', text, re.IGNORECASE)
    if matches:
        return matches[0]
    
    sup_matches = re.findall(r'SUP\.(?:[A-Z0-9]+\.)?([A-Z0-9]{8,})', text, re.IGNORECASE)
    if sup_matches:
        return sup_matches[0]
    
    return None


def flatten_device_data(devices: List[Dict]) -> List[Dict]:
    """Flatten device data for CSV export."""
    flattened = []

    for device in devices:
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
        if not model:
            summary_parts = summary.split()
            for part in summary_parts:
                if 'ap' in part.lower() or 'fap' in part.lower():
                    idx = summary_parts.index(part)
                    if idx + 1 < len(summary_parts):
                        model = summary_parts[idx] + ' ' + summary_parts[idx + 1]
                        break
        
        if not model:
            model = 'Unknown'

        branch_name = 'N/A'
        location_name = 'N/A'

        assignments = device.get('@assignments', [])
        if assignments and isinstance(assignments, list) and len(assignments) > 0:
            first_assignment = assignments[0]
            branch = first_assignment.get('branch', {})
            if branch:
                branch_name = branch.get('name', 'N/A')

            location = first_assignment.get('location', {})
            if location:
                location_name = location.get('name', 'N/A')

        serial_number = serial_number_td or ''

        contracts = device.get('contracts', [])
        contract_serials = []

        for contract in contracts:
            contract_name = contract.get('name', '')
            serial_from_contract = extract_serial_from_text(contract_name)
            if serial_from_contract:
                contract_serials.append(serial_from_contract)

        if not serial_number and contract_serials:
            serial_number = contract_serials[0]

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
                    'Asset Type': 'Access Point',
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
                'Asset Type': 'Access Point',
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

        return True
    except Exception as e:
        print(f"ERROR: Failed to write CSV: {e}")
        return False


def main():
    """Main execution function."""
    print("="*70)
    print("TopDesk API - FortiAP Device Export")
    print("="*70)
    print()

    config = load_config()

    if not all([config['url'], config['username'], config['password']]):
        print("ERROR: Missing configuration. Set environment variables or create topdeskapikey file.")
        return

    print(f"TopDesk URL: {config['url']}")
    print(f"Username: {config['username']}")
    print(f"Debug Mode: False")
    print()

    api = TopDeskAPI(config['url'], config['username'], config['password'])

    print("Step 1: Retrieving all access point assets...")
    all_aps = api.get_assets_by_template('Access Point [WAP]')
    print(f"Retrieved {len(all_aps)} total access point assets")
    print()

    print("Step 2: Filtering for Fortinet FortiAP devices...")
    fortiap_devices = filter_fortiap_devices(all_aps)
    print(f"Found {len(fortiap_devices)} Fortinet FortiAP devices")
    print()

    print("Step 3: Enriching with support contracts...")
    enriched_devices = enrich_with_contracts(api, fortiap_devices)
    print()

    print("Step 4: Processing device data...")
    flattened_data = flatten_device_data(enriched_devices)
    print(f"Processed {len(flattened_data)} rows")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"td_fortiap_devices_{timestamp}.csv"

    print(f"Step 5: Exporting to CSV ({filename})...")
    if export_to_csv(flattened_data, filename):
        print(f"SUCCESS: Data exported to {filename}")
    else:
        print("ERROR: Export failed")
        return

    print()
    print("="*70)
    print("EXPORT COMPLETE!")
    print("="*70)
    print(f"Output file: {filename}")
    print(f"Total devices: {len(fortiap_devices)}")
    print(f"Total rows (with contracts): {len(flattened_data)}")
    print()


if __name__ == "__main__":
    main()

