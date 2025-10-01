#!/usr/bin/env python3
"""
FortiManager API - Get FortiSwitch Devices via Proxy

This script uses the FortiManager proxy API (/sys/proxy/json) to query
all managed FortiGates for their FortiSwitch devices.

Key Features:
1. Proxies FortiGate REST API requests through FortiManager
2. Queries all FortiGates simultaneously for efficiency
3. Retrieves FortiSwitch devices managed via FortiLink
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

    def get_fortiswitches_via_proxy(self, fortigates: List[Dict]) -> List[Dict]:
        """
        Get all FortiSwitch devices by proxying FortiGate REST API requests.
        
        Uses /sys/proxy/json to query all FortiGates for their managed switches.
        FortiGate REST API endpoint: /api/v2/monitor/switch-controller/managed-switch/status
        """
        print("[*] Querying all FortiGates for FortiSwitch devices (via proxy)...")
        
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
                'resource': '/api/v2/monitor/switch-controller/managed-switch/status',
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


class FortiSwitchExporter:
    """Export FortiSwitch devices to CSV format."""

    def __init__(self, api: FortiManagerAPI):
        self.api = api
        self.fortigates = {}  # Cache FortiGate info by name

    def process_switches(self) -> List[Dict]:
        """Process all FortiSwitch devices from all FortiGates."""
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

        # Get FortiSwitch devices via proxy
        proxy_responses = self.api.get_fortiswitches_via_proxy(fortigate_list)
        
        all_switches = []
        total_switches = 0
        fortigates_with_switches = 0

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

            # Get switches from results
            switches = response_data.get('results', [])
            if not switches:
                continue

            fortigates_with_switches += 1
            total_switches += len(switches)
            
            print(f"  [+] {target_name}: {len(switches)} switch(es)")

            # Get parent FortiGate info
            parent_fgt = self.fortigates.get(target_name, {})

            # Process each switch
            for switch in switches:
                switch_info = self._extract_switch_info(
                    switch, 
                    target_name, 
                    parent_fgt,
                    response_data
                )
                all_switches.append(switch_info)

        print(f"\n[*] Summary: {total_switches} FortiSwitch device(s) from {fortigates_with_switches} FortiGate(s)")
        return all_switches

    def _extract_model_from_firmware(self, firmware: str) -> str:
        """
        Extract model from firmware string.
        Example: "S224EN-v7.4.5-build880" -> "FortiSwitch-224EN"
        """
        if not firmware:
            return ''
        
        # Try to extract model prefix (e.g., S224EN, FS1E48, SM24GF)
        import re
        match = re.match(r'^([A-Z0-9]+)-', firmware)
        if match:
            model_code = match.group(1)
            return f"FortiSwitch-{model_code}"
        
        return ''

    def _extract_switch_info(self, switch: Dict, parent_name: str, parent_fgt: Dict, response: Dict) -> Dict:
        """Extract and format FortiSwitch information using unified 60-field structure."""
        # Get connection status
        state = switch.get('state', 'unknown')
        connection_status = 'Connected' if state == 'Authorized' else state

        # Get firmware version
        firmware = switch.get('os_version', '')
        
        # Extract model from firmware string
        model = self._extract_model_from_firmware(firmware)
        if not model:
            model = switch.get('platform', '')

        # Get switch serial
        serial_number = switch.get('switch_id', switch.get('switch-id', switch.get('serial', '')))
        
        # Get device name
        device_name = switch.get('name', '')
        
        # Description
        description = switch.get('description', '')
        if not description and model:
            description = f"{model} Switch"
        
        # ADOM and company
        adom = parent_fgt.get('adom', '')
        
        # Last updated
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # PoE budget
        max_poe_budget = str(switch.get('max_poe_budget', '')) if switch.get('max_poe_budget') else ''
        
        # Return unified 60-field structure
        return {
            # Section 1: Core Identification
            'Serial Number': serial_number,
            'Device Name': device_name,
            'Hostname': device_name or serial_number,
            'Model': model,
            'Description': description,
            'Asset Type': 'Switch',
            'Source System': 'FortiManager',
            
            # Section 2: Network & Connection
            'Management IP': parent_fgt.get('ip', ''),
            'Connection Status': connection_status,
            'Management Mode': '',
            'Firmware Version': firmware,
            
            # Section 3: Organization & Location
            'Company': adom,
            'Organizational Unit': adom,
            'Branch': '',
            'Location': '',
            'Folder Path': '',
            'Folder ID': '',
            'Vendor': 'Fortinet',
            
            # Section 4: Contract Information (all empty for FortiManager)
            'Contract Number': '',
            'Contract SKU': '',
            'Contract Type': '',
            'Contract Summary': '',
            'Contract Start Date': '',
            'Contract Expiration Date': '',
            'Contract Status': '',
            'Contract Support Type': '',
            'Contract Archived': '',
            
            # Section 5: Entitlement Information (all empty for FortiManager)
            'Entitlement Level': '',
            'Entitlement Type': '',
            'Entitlement Start Date': '',
            'Entitlement End Date': '',
            
            # Section 6: Lifecycle & Status
            'Status': connection_status,
            'Is Decommissioned': 'No',
            'Archived': 'No',
            'Registration Date': '',
            'Product EoR': '',
            'Product EoS': '',
            'Last Updated': last_updated,
            
            # Section 7: Account Information (all empty for FortiManager)
            'Account ID': '',
            'Account Email': '',
            'Account OU ID': '',
            
            # Section 8: FortiGate-Specific Fields (empty for FortiSwitch)
            'HA Mode': '',
            'HA Cluster Name': '',
            'HA Role': '',
            'HA Member Status': '',
            'HA Priority': '',
            'Max VDOMs': '',
            
            # Section 9: FortiSwitch/FortiAP Parent Tracking
            'Parent FortiGate': parent_name,
            'Parent FortiGate Serial': parent_fgt.get('serial', ''),
            'Parent FortiGate Platform': parent_fgt.get('platform', ''),
            'Parent FortiGate IP': parent_fgt.get('ip', ''),
            
            # Section 10: FortiSwitch-Specific Fields
            'Device Type': 'physical',
            'Max PoE Budget': max_poe_budget,
            'Join Time': switch.get('join_time', ''),
            
            # Section 11: FortiAP-Specific Fields (empty for FortiSwitch)
            'Board MAC': '',
            'Admin Status': '',
            'Client Count': '',
            'Mesh Uplink': '',
            'WTP Mode': '',
            'VDOM': response.get('vdom', 'root')
        }

    def export_to_csv(self, switches: List[Dict], filename: str):
        """Export FortiSwitch devices to CSV file using unified 60-field structure."""
        if not switches:
            print(f"[!]  No FortiSwitch devices to export")
            return

        # Unified 60-field structure - same order for all systems
        fieldnames = [
            # Section 1: Core Identification
            'Serial Number', 'Device Name', 'Hostname', 'Model', 'Description', 
            'Asset Type', 'Source System',
            
            # Section 2: Network & Connection
            'Management IP', 'Connection Status', 'Management Mode', 'Firmware Version',
            
            # Section 3: Organization & Location
            'Company', 'Organizational Unit', 'Branch', 'Location', 
            'Folder Path', 'Folder ID', 'Vendor',
            
            # Section 4: Contract Information
            'Contract Number', 'Contract SKU', 'Contract Type', 'Contract Summary',
            'Contract Start Date', 'Contract Expiration Date', 'Contract Status',
            'Contract Support Type', 'Contract Archived',
            
            # Section 5: Entitlement Information
            'Entitlement Level', 'Entitlement Type', 
            'Entitlement Start Date', 'Entitlement End Date',
            
            # Section 6: Lifecycle & Status
            'Status', 'Is Decommissioned', 'Archived', 'Registration Date',
            'Product EoR', 'Product EoS', 'Last Updated',
            
            # Section 7: Account Information
            'Account ID', 'Account Email', 'Account OU ID',
            
            # Section 8: FortiGate-Specific Fields
            'HA Mode', 'HA Cluster Name', 'HA Role', 'HA Member Status', 
            'HA Priority', 'Max VDOMs',
            
            # Section 9: FortiSwitch/FortiAP Parent Tracking
            'Parent FortiGate', 'Parent FortiGate Serial', 
            'Parent FortiGate Platform', 'Parent FortiGate IP',
            
            # Section 10: FortiSwitch-Specific Fields
            'Device Type', 'Max PoE Budget', 'Join Time',
            
            # Section 11: FortiAP-Specific Fields
            'Board MAC', 'Admin Status', 'Client Count', 'Mesh Uplink', 
            'WTP Mode', 'VDOM'
        ]

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(switches)

            print(f"[+] CSV export successful: {filename}")
            print(f"[+] Total rows: {len(switches)}")

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
    print("FortiManager - FortiSwitch Device Export (Proxy Method)")
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
    exporter = FortiSwitchExporter(api)

    # Process FortiSwitch devices
    switches = exporter.process_switches()

    # Generate CSV filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'fmg_fortiswitch_devices_{timestamp}.csv'

    # Export to CSV
    exporter.export_to_csv(switches, csv_filename)

    print()
    print("=" * 70)
    print("[+] Export completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()