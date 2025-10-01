#!/usr/bin/env python3
"""
FortiManager API - Get FortiAP Devices via Proxy

This script uses the FortiManager proxy API (/sys/proxy/json) to query
all managed FortiGates for their FortiAP devices.

Key Features:
1. Proxies FortiGate REST API requests through FortiManager
2. Queries all FortiGates simultaneously for efficiency
3. Retrieves FortiAP devices managed via wireless controller
4. Exports comprehensive device information to CSV

Author: FortiManager API Project
Date: September 30, 2025
Version: 2.0 (Proxy Implementation)
"""

import os
import sys
import csv
import requests
import urllib3
from datetime import datetime
from typing import Dict, List, Optional

# Disable SSL warnings if verify_ssl is False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiManagerAPI:
    """FortiManager API client with token-based authentication."""

    def __init__(self, host: str, api_key: str, verify_ssl: bool = True, debug: bool = False):
        self.host = host.rstrip('/')
        if not self.host.startswith('http'):
            self.host = f'https://{self.host}'
        
        self.api_url = f'{self.host}/jsonrpc'
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        })

    def exec_request(self, method: str, params: List[Dict], request_id: int = 1) -> Dict:
        """Execute a JSON RPC request to FortiManager."""
        payload = {
            'id': request_id,
            'method': method,
            'params': params
        }

        if self.debug:
            print(f"\nDEBUG Request:")
            import json
            print(json.dumps(payload, indent=2))

        try:
            response = self.session.post(
                self.api_url,
                json=payload,
                verify=self.verify_ssl,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            if self.debug:
                print(f"\nDEBUG Response:")
                print(json.dumps(result, indent=2)[:1000])

            return result

        except requests.exceptions.RequestException as e:
            print(f"[!] API Request failed: {e}")
            sys.exit(1)

    def get_all_fortigates(self) -> List[Dict]:
        """Get all managed FortiGate devices with their ADOM assignments."""
        print("[*] Retrieving all FortiGate devices...")
        
        params = [{
            'url': '/dvmdb/device',
            'option': ['extra info'],
            'fields': ['name', 'sn', 'platform_str', 'ip', 'conn_status'],
            'loadsub': 0
        }]

        response = self.exec_request('get', params)
        
        if not response.get('result'):
            print("[!] No result in response")
            return []

        result = response['result'][0]
        if result.get('status', {}).get('code') != 0:
            print(f"[!] Error: {result.get('status', {}).get('message')}")
            return []

        devices = result.get('data', [])
        print(f"[+] Found {len(devices)} FortiGate devices")
        return devices

    def get_fortiaps_via_proxy(self, fortigates: List[Dict]) -> List[Dict]:
        """
        Get all FortiAP devices by proxying FortiGate REST API requests.
        
        Uses /sys/proxy/json to query all FortiGates for their managed APs.
        FortiGate REST API endpoint: /api/v2/monitor/wifi/managed_ap
        """
        print("[*] Querying all FortiGates for FortiAP devices (via proxy)...")
        
        # Build target list from FortiGate devices
        targets = []
        for fgt in fortigates:
            adom = fgt.get('extra info', {}).get('adom', 'root')
            device_name = fgt.get('name')
            if device_name:
                targets.append(f'adom/{adom}/device/{device_name}')
        
        if not targets:
            print("[!] No FortiGate devices to query")
            return []
        
        print(f"[*] Querying {len(targets)} FortiGate device(s)...")
        
        params = [{
            'url': '/sys/proxy/json',
            'data': {
                'action': 'get',
                'resource': '/api/v2/monitor/wifi/managed_ap',
                'target': targets,
                'timeout': 90
            }
        }]

        response = self.exec_request('exec', params)
        
        if not response.get('result'):
            print("[!] No result in response")
            return []

        result = response['result'][0]
        if result.get('status', {}).get('code') != 0:
            print(f"[!] Error: {result.get('status', {}).get('message')}")
            return []

        return result.get('data', [])


class FortiAPExporter:
    """Export FortiAP devices to CSV format."""

    def __init__(self, api: FortiManagerAPI):
        self.api = api
        self.fortigates = {}  # Cache FortiGate info by name

    def process_aps(self) -> List[Dict]:
        """Process all FortiAP devices from all FortiGates."""
        # First, get all FortiGates to build a lookup table
        fortigate_list = self.api.get_all_fortigates()
        for fgt in fortigate_list:
            self.fortigates[fgt.get('name')] = {
                'serial': fgt.get('sn'),
                'platform': fgt.get('platform_str'),
                'ip': fgt.get('ip'),
                'adom': fgt.get('extra info', {}).get('adom', 'Unknown'),
                'conn_status': fgt.get('conn_status', 0)
            }

        # Get FortiAP devices via proxy
        proxy_responses = self.api.get_fortiaps_via_proxy(fortigate_list)
        
        all_aps = []
        total_aps = 0
        fortigates_with_aps = 0
        total_clients = 0

        for device_response in proxy_responses:
            target_name = device_response.get('target', 'Unknown')
            status = device_response.get('status', {})
            response_data = device_response.get('response', {})

            # Check if query was successful
            if status.get('code') != 0:
                if self.api.debug:
                    print(f"  [!]  {target_name}: {status.get('message')}")
                continue

            # Check if FortiGate response was successful
            if response_data.get('status') != 'success':
                if self.api.debug:
                    print(f"  [!]  {target_name}: FortiGate query failed")
                continue

            # Get APs from results
            aps = response_data.get('results', [])
            if not aps:
                continue

            fortigates_with_aps += 1
            total_aps += len(aps)
            
            # Calculate total clients
            ap_clients = sum(ap.get('client_count', 0) for ap in aps)
            total_clients += ap_clients
            
            print(f"  [+] {target_name}: {len(aps)} AP(s), {ap_clients} client(s)")

            # Get parent FortiGate info
            parent_fgt = self.fortigates.get(target_name, {})

            # Process each AP
            for ap in aps:
                ap_info = self._extract_ap_info(
                    ap, 
                    target_name, 
                    parent_fgt,
                    response_data
                )
                all_aps.append(ap_info)

        print(f"\n[*] Summary: {total_aps} FortiAP device(s) from {fortigates_with_aps} FortiGate(s)")
        print(f"[*] Total clients: {total_clients}")
        return all_aps

    def _extract_model_from_firmware(self, firmware: str) -> str:
        """Extract model from firmware string. Example: "FP231F-v7.2-build0318" -> "FortiAP-231F" """
        if not firmware:
            return ''
        import re
        match = re.match(r'^([A-Z0-9]+)-', firmware)
        if match:
            model_code = match.group(1)
            return f"FortiAP-{model_code}"
        return ''

    def _extract_ap_info(self, ap: Dict, parent_name: str, parent_fgt: Dict, response: Dict) -> Dict:
        """Extract and format FortiAP information using unified 60-field structure."""
        # Get firmware version
        firmware = ap.get('os_version', ap.get('firmware', ''))
        
        # Extract model
        model = self._extract_model_from_firmware(firmware)
        
        # Get serial and name
        serial_number = ap.get('wtp_id', '')
        device_name = ap.get('wtp_name', '')
        
        # Description
        description = f"{model} Access Point" if model else ''
        
        # Location
        location = ap.get('location', '') or ap.get('region', '')
        
        # ADOM
        adom = parent_fgt.get('adom', '')
        
        # Connection status
        connection_state = ap.get('connection_state', 'Unknown')
        
        # Client count
        client_count = str(ap.get('client_count', '')) if ap.get('client_count', '') != '' else ''
        
        # Last updated
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Return unified 60-field structure
        return {
            'Serial Number': serial_number,
            'Device Name': device_name,
            'Hostname': '',
            'Model': model,
            'Description': description,
            'Asset Type': 'Access Point',
            'Source System': 'FortiManager',
            'Management IP': parent_fgt.get('ip', ''),
            'Connection Status': connection_state,
            'Management Mode': '',
            'Firmware Version': firmware,
            'Company': adom,
            'Organizational Unit': adom,
            'Branch': '',
            'Location': location,
            'Folder Path': '',
            'Folder ID': '',
            'Vendor': 'Fortinet',
            'Contract Number': '',
            'Contract SKU': '',
            'Contract Type': '',
            'Contract Summary': '',
            'Contract Start Date': '',
            'Contract Expiration Date': '',
            'Contract Status': '',
            'Contract Support Type': '',
            'Contract Archived': '',
            'Entitlement Level': '',
            'Entitlement Type': '',
            'Entitlement Start Date': '',
            'Entitlement End Date': '',
            'Status': connection_state,
            'Is Decommissioned': 'No',
            'Archived': 'No',
            'Registration Date': '',
            'Product EoR': '',
            'Product EoS': '',
            'Last Updated': last_updated,
            'Account ID': '',
            'Account Email': '',
            'Account OU ID': '',
            'HA Mode': '',
            'HA Cluster Name': '',
            'HA Role': '',
            'HA Member Status': '',
            'HA Priority': '',
            'Max VDOMs': '',
            'Parent FortiGate': parent_name,
            'Parent FortiGate Serial': parent_fgt.get('serial', ''),
            'Parent FortiGate Platform': parent_fgt.get('platform', ''),
            'Parent FortiGate IP': parent_fgt.get('ip', ''),
            'Device Type': '',
            'Max PoE Budget': '',
            'Join Time': '',
            'Board MAC': ap.get('board_mac', ''),
            'Admin Status': ap.get('admin_status', ''),
            'Client Count': client_count,
            'Mesh Uplink': ap.get('mesh_uplink', ''),
            'WTP Mode': ap.get('wtp_mode', ''),
            'VDOM': response.get('vdom', 'root')
        }

    def export_to_csv(self, aps: List[Dict], filename: str):
        """Export FortiAP devices to CSV file."""
        if not aps:
            print(f"[!]  No FortiAP devices to export")
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
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(aps)

            print(f"[+] CSV export successful: {filename}")
            print(f"[+] Total rows: {len(aps)}")

        except Exception as e:
            print(f"[!] Failed to write CSV: {e}")
            sys.exit(1)


def load_config(config_file: str = 'fortimanagerapikey') -> Dict[str, str]:
    """Load configuration from file or environment variables."""
    config = {}

    # Try to load from config file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    config_path = os.path.join(project_root, config_file)

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            print(f"[!]  Error reading config file: {e}")

    # Environment variables override config file
    if os.getenv('FORTIMANAGER_HOST'):
        config['url'] = os.getenv('FORTIMANAGER_HOST')
    if os.getenv('FORTIMANAGER_API_KEY'):
        config['apikey'] = os.getenv('FORTIMANAGER_API_KEY')

    return config


def main():
    """Main execution function."""
    # Set console encoding for Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    print("=" * 70)
    print("FortiManager - FortiAP Device Export (Proxy Method)")
    print("=" * 70)
    print()

    # Load configuration
    config = load_config()

    if not config.get('url') or not config.get('apikey'):
        print("[!] Missing configuration!")
        print()
        print("Please create a 'fortimanagerapikey' file with:")
        print("  apikey=your_api_key_here")
        print("  url=your.fortimanager.hostname")
        print()
        print("Or set environment variables:")
        print("  FORTIMANAGER_HOST=your.fortimanager.hostname")
        print("  FORTIMANAGER_API_KEY=your_api_key_here")
        sys.exit(1)

    # Configuration
    host = config['url']
    api_key = config['apikey']
    verify_ssl_str = config.get('verify_ssl', os.getenv('FORTIMANAGER_VERIFY_SSL', 'true'))
    verify_ssl = verify_ssl_str.lower() == 'true'
    debug = os.getenv('DEBUG', 'false').lower() == 'true'

    print(f"[*] FortiManager: {host}")
    print(f"[*] SSL Verification: {'Enabled' if verify_ssl else 'Disabled'}")
    if debug:
        print(f"[*] Debug Mode: Enabled")
    print()

    # Initialize API client
    api = FortiManagerAPI(host, api_key, verify_ssl=verify_ssl, debug=debug)

    # Initialize exporter
    exporter = FortiAPExporter(api)

    # Process FortiAP devices
    aps = exporter.process_aps()

    # Generate CSV filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'fmg_fortiap_devices_{timestamp}.csv'

    # Export to CSV
    exporter.export_to_csv(aps, csv_filename)

    print()
    print("=" * 70)
    print("[+] Export completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()