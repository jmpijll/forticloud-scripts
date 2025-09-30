#!/usr/bin/env python3
"""
FortiManager API - Get FortiGate/FortiWiFi Devices

Idempotent script that:
1. Connects to FortiManager using API key
2. Retrieves all managed FortiGate and FortiWiFi devices
3. Gets device details including ADOM, status, and version info
4. Exports to CSV for reporting

Author: FortiManager API Project
Date: September 30, 2025
Version: 1.0
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
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.debug = debug
        self.base_url = f'{self.host}/jsonrpc'
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'FortiManager-API-Script/1.0'
        })

    def _log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def _make_request(self, method: str, url: str, params: dict = None) -> dict:
        """
        Make a JSON RPC request to FortiManager.

        Args:
            method: JSON RPC method (get, set, add, delete, exec)
            url: API endpoint URL
            params: Additional parameters for the request

        Returns:
            Response data dictionary
        """
        request_id = 1
        
        payload = {
            "id": request_id,
            "method": method,
            "params": [{
                "url": url
            }],
            "session": None  # Using token auth
        }
        
        if params:
            payload["params"][0].update(params)
        
        self._log(f"Request: {payload}")
        
        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self._log(f"Response: {data}")
            
            # Check for API errors
            if "result" in data and len(data["result"]) > 0:
                result = data["result"][0]
                if "status" in result:
                    status_code = result["status"].get("code", 0)
                    if status_code != 0:
                        error_msg = result["status"].get("message", "Unknown error")
                        raise Exception(f"API Error {status_code}: {error_msg}")
                return result
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {e}")
            raise

    def get_adoms(self) -> List[Dict]:
        """
        Get list of all ADOMs (Administrative Domains).

        Returns:
            List of ADOM dictionaries
        """
        print("Retrieving ADOMs...")
        
        try:
            result = self._make_request(
                method="get",
                url="/dvmdb/adom",
                params={
                    "fields": ["name", "desc"],
                    "filter": ["restricted_prds", "==", "fos"],
                    "loadsub": 0
                }
            )
            
            adoms = result.get("data", [])
            self._log(f"Found {len(adoms)} ADOMs")
            return adoms
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve ADOMs: {e}")
            raise

    def get_devices(self, adom: str = None) -> List[Dict]:
        """
        Get all managed devices, optionally filtered by ADOM.

        Args:
            adom: ADOM name to filter by (None for all devices)

        Returns:
            List of device dictionaries
        """
        if adom:
            url = f"/dvmdb/adom/{adom}/device"
            print(f"Retrieving devices from ADOM '{adom}'...")
        else:
            url = "/dvmdb/device"
            print("Retrieving all devices...")
        
        try:
            result = self._make_request(
                method="get",
                url=url,
                params={
                    "option": ["extra info", "assignment info"],
                    "loadsub": 1  # Need loadsub=1 to get HA member details
                }
            )
            
            devices = result.get("data", [])
            self._log(f"Retrieved {len(devices)} devices")
            return devices
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve devices: {e}")
            raise

    def close(self) -> None:
        """Close the session."""
        self.session.close()


def filter_fortigate_devices(devices: List[Dict]) -> List[Dict]:
    """
    Filter devices to only include FortiGate and FortiWiFi.

    Args:
        devices: List of all device dictionaries

    Returns:
        Filtered list of FortiGate/FortiWiFi devices
    """
    fortigate_devices = []
    
    for device in devices:
        platform = device.get('platform_str', '')
        os_type = device.get('os_type', '')
        
        # Filter for FortiGate and FortiWiFi devices
        # os_type 0 = FOS (FortiOS)
        if (platform.startswith('FortiGate') or 
            platform.startswith('FortiWiFi') or
            (os_type == 0 and 'Forti' in platform)):
            fortigate_devices.append(device)
    
    return fortigate_devices


def flatten_device_data(devices: List[Dict]) -> List[Dict]:
    """
    Flatten device data for CSV export.
    
    Expands HA clusters so each member gets its own row.

    Args:
        devices: List of device dictionaries

    Returns:
        List of flattened dictionaries for CSV export
    """
    flattened = []
    
    for device in devices:
        # Check if this is an HA device with members
        ha_mode = device.get('ha_mode', 0)
        ha_slave = device.get('ha_slave', [])
        ha_group_name = device.get('ha_group_name', '')
        
        # If HA cluster with members, create a row for each member
        if ha_mode != 0 and ha_slave:
            for member in ha_slave:
                flattened_member = _create_device_row(device, member, ha_group_name)
                flattened.append(flattened_member)
        else:
            # Standalone device or HA without slave info
            flattened_member = _create_device_row(device, None, '')
            flattened.append(flattened_member)
    
    return flattened


def _create_device_row(device: Dict, ha_member: Optional[Dict], ha_cluster_name: str) -> Dict:
    """
    Create a CSV row for a device or HA member.
    
    Args:
        device: Original device dictionary from API
        ha_member: HA member info if part of cluster, None otherwise
        ha_cluster_name: Name of HA cluster
    
    Returns:
        Dictionary for CSV export
    """
    # If this is an HA member, use member-specific info
    if ha_member:
        serial_number = ha_member.get('sn', 'N/A')
        name = ha_member.get('name', 'N/A')
        
        # Determine HA role
        role = ha_member.get('role', -1)
        role_str = {
            0: 'Secondary',
            1: 'Primary',
            2: 'Standalone'
        }.get(role, f'Unknown ({role})')
        
        # Member status
        status = ha_member.get('status', 0)
        member_status = {
            0: 'Offline',
            1: 'Online',
            2: 'Unknown'
        }.get(status, f'Unknown ({status})')
        
        # Priority
        priority = ha_member.get('prio', 0)
        
    else:
        serial_number = device.get('sn', 'N/A')
        name = device.get('name', 'N/A')
        role_str = 'N/A'
        member_status = 'N/A'
        priority = 0
    
    # Common device info (from parent device record)
    hostname = device.get('hostname', name)
    platform = device.get('platform_str', 'N/A')
    description = device.get('desc', '')
    ip_address = device.get('ip', 'N/A')
    
    # Get ADOM from extra info
    extra_info = device.get('extra info', {})
    adom = extra_info.get('adom', 'N/A') if extra_info else 'N/A'
    
    # Connection status (from parent device)
    conn_status = device.get('conn_status', 0)
    conn_status_str = {
        0: 'Unknown',
        1: 'Connected',
        2: 'Disconnected'
    }.get(conn_status, f'Unknown ({conn_status})')
    
    # Management mode
    mgmt_mode = device.get('mgmt_mode', 0)
    mgmt_mode_str = {
        0: 'Unreg',
        1: 'FMGFAZ',
        2: 'FMGFAI',
        3: 'Normal'
    }.get(mgmt_mode, f'Unknown ({mgmt_mode})')
    
    # OS Version
    os_ver = device.get('os_ver', 0)
    mr = device.get('mr', 0)
    build = device.get('build', 0)
    patch = device.get('patch', 0)
    version_str = f"{os_ver}.{mr}.{patch}-build{build}" if os_ver else 'N/A'
    
    # HA Configuration
    ha_mode = device.get('ha_mode', 0)
    ha_mode_str = {
        0: 'Standalone',
        1: 'Active-Active',
        2: 'Active-Passive',
        3: 'Cluster'
    }.get(ha_mode, f'Unknown ({ha_mode})')
    
    # Last communication
    last_checked = device.get('last_checked', 0)
    last_checked_str = datetime.fromtimestamp(last_checked).strftime('%Y-%m-%d %H:%M:%S') if last_checked else 'Never'
    
    # VDOM count
    maxvdom = device.get('maxvdom', 1)
    
    # Meta fields (custom metadata)
    meta_fields = device.get('meta fields', {})
    company = meta_fields.get('Company/Organization', '') if meta_fields else ''
    
    return {
        'Serial Number': serial_number,
        'Device Name': name,
        'Hostname': hostname,
        'Product Model': platform,
        'Description': description,
        'ADOM': adom,
        'Company': company,
        'Management IP': ip_address,
        'Connection Status': conn_status_str,
        'Management Mode': mgmt_mode_str,
        'OS Version': version_str,
        'HA Mode': ha_mode_str,
        'HA Cluster Name': ha_cluster_name if ha_cluster_name else 'N/A',
        'HA Role': role_str,
        'HA Member Status': member_status if ha_member else 'N/A',
        'HA Priority': priority if ha_member else 'N/A',
        'Max VDOMs': maxvdom,
        'Last Checked': last_checked_str
    }


def export_to_csv(data: List[Dict], filename: str) -> bool:
    """Export data to CSV file."""
    if not data:
        print("WARNING: No data to export")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Serial Number', 'Device Name', 'Hostname', 'Product Model',
                'Description', 'ADOM', 'Company', 'Management IP',
                'Connection Status', 'Management Mode', 'OS Version',
                'HA Mode', 'HA Cluster Name', 'HA Role', 'HA Member Status', 'HA Priority',
                'Max VDOMs', 'Last Checked'
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
    print("FortiManager API - FortiGate/FortiWiFi Device Export")
    print("=" * 70)
    print()
    
    # Try loading from config file first
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fortimanagerapikey')
    file_config = load_config_from_file(config_file)
    
    # Get configuration from file or environment
    host = file_config.get('url') or os.getenv('FORTIMANAGER_HOST')
    api_key = file_config.get('apikey') or os.getenv('FORTIMANAGER_API_KEY')
    verify_ssl = os.getenv('FORTIMANAGER_VERIFY_SSL', 'true').lower() == 'true'
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Validate configuration
    if not all([host, api_key]):
        print("ERROR: Missing required configuration.")
        print("Please provide configuration either via:")
        print("  1. 'fortimanagerapikey' file with 'url' and 'apikey' fields")
        print("  2. Environment variables:")
        print("     - FORTIMANAGER_HOST")
        print("     - FORTIMANAGER_API_KEY")
        sys.exit(1)
    
    print(f"FortiManager Host: {host}")
    print(f"SSL Verification: {verify_ssl}")
    print(f"Debug Mode: {debug}")
    print()
    
    # Initialize API client
    api = FortiManagerAPI(host, api_key, verify_ssl, debug)
    
    try:
        # Step 1: Get all devices
        print("Step 1: Retrieving devices...")
        all_devices = api.get_devices()
        print(f"Retrieved {len(all_devices)} total devices")
        print()
        
        # Step 2: Filter for FortiGate/FortiWiFi devices
        print("Step 2: Filtering FortiGate/FortiWiFi devices...")
        fortigate_devices = filter_fortigate_devices(all_devices)
        print(f"Found {len(fortigate_devices)} FortiGate/FortiWiFi devices")
        print()
        
        if not fortigate_devices:
            print("WARNING: No FortiGate/FortiWiFi devices found")
            sys.exit(0)
        
        # Step 3: Process device data
        print("Step 3: Processing device data...")
        flattened_data = flatten_device_data(fortigate_devices)
        print(f"Processed {len(flattened_data)} rows")
        print()
        
        # Step 4: Export to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'fmg_fortigate_devices_{timestamp}.csv'
        
        print(f"Step 4: Exporting to CSV ({output_filename})...")
        if export_to_csv(flattened_data, output_filename):
            print()
            print("=" * 70)
            print("EXPORT COMPLETE!")
            print("=" * 70)
            print(f"Output file: {output_filename}")
            print(f"Total devices: {len(flattened_data)}")
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
