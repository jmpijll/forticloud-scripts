#!/usr/bin/env python3
"""
Analyze CSV structures across all three systems to design unified structure.

This script reads all 9 CSV files and analyzes:
1. What fields exist in each
2. What percentage of rows have non-empty values for each field
3. Unique values and patterns
"""

import csv
import os
from collections import defaultdict
from typing import Dict, List

def analyze_csv(filepath: str) -> Dict:
    """Analyze a single CSV file."""
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        if not rows:
            return {"error": "No data rows", "headers": []}
        
        total_rows = len(rows)
        field_stats = {}
        
        for field in reader.fieldnames:
            non_empty = 0
            unique_values = set()
            
            for row in rows:
                value = row.get(field, '').strip()
                if value and value.lower() not in ['n/a', 'none', '']:
                    non_empty += 1
                    # Keep unique values for small sets
                    if len(unique_values) < 20:
                        unique_values.add(value[:50])  # Limit length
            
            field_stats[field] = {
                'populated_count': non_empty,
                'populated_percent': round((non_empty / total_rows) * 100, 1),
                'empty_count': total_rows - non_empty,
                'unique_sample': sorted(list(unique_values))[:10]
            }
        
        return {
            'total_rows': total_rows,
            'headers': list(reader.fieldnames),
            'field_stats': field_stats
        }


def main():
    """Main analysis function."""
    print("=" * 100)
    print("CSV STRUCTURE ANALYSIS - All Three Systems")
    print("=" * 100)
    print()
    
    files = {
        'FortiManager': {
            'FortiGate': 'fmg_fortigate_devices_20251002_001420.csv',
            'FortiSwitch': 'fmg_fortiswitch_devices_20251002_001437.csv',
            'FortiAP': 'fmg_fortiap_devices_20251002_001443.csv'
        },
        'FortiCloud': {
            'FortiGate': 'fc_fortigate_devices_20251002_002932.csv',
            'FortiSwitch': 'fc_fortiswitch_devices_20251002_003030.csv',
            'FortiAP': 'fc_fortiap_devices_20251002_003109.csv'
        },
        'TopDesk': {
            'FortiGate': 'td_fortigate_devices_20251002_003127.csv',
            'FortiSwitch': 'td_fortiswitch_devices_20251002_003200.csv',
            'FortiAP': 'td_fortiap_devices_20251002_003241.csv'
        }
    }
    
    all_results = {}
    
    for system, device_files in files.items():
        print(f"\n{'=' * 100}")
        print(f"{system} ANALYSIS")
        print(f"{'=' * 100}\n")
        
        all_results[system] = {}
        
        for device_type, filename in device_files.items():
            print(f"\n{'-' * 80}")
            print(f"{device_type} ({filename})")
            print(f"{'-' * 80}")
            
            result = analyze_csv(filename)
            all_results[system][device_type] = result
            
            if 'error' in result:
                print(f"ERROR: {result['error']}")
                continue
            
            print(f"Total Rows: {result['total_rows']}")
            print(f"Total Fields: {len(result['headers'])}")
            print(f"\nField Population Analysis:")
            print(f"{'Field Name':<40} {'Populated':<12} {'Empty':<10} {'%':<8}")
            print("-" * 80)
            
            for field, stats in sorted(result['field_stats'].items(), 
                                       key=lambda x: x[1]['populated_percent'], 
                                       reverse=True):
                pop_count = stats['populated_count']
                empty_count = stats['empty_count']
                percent = stats['populated_percent']
                
                # Color code by percentage
                if percent >= 90:
                    status = "[+]"
                elif percent >= 50:
                    status = "[~]"
                elif percent > 0:
                    status = "[.]"
                else:
                    status = "[ ]"
                
                print(f"{status} {field:<38} {pop_count:<10} {empty_count:<10} {percent:>6.1f}%")
                
                # Show sample values for interesting fields
                if stats['unique_sample'] and len(stats['unique_sample']) <= 5:
                    samples = ', '.join(stats['unique_sample'][:3])
                    print(f"      Sample: {samples}")
    
    # Cross-system comparison
    print(f"\n\n{'=' * 100}")
    print("CROSS-SYSTEM FIELD COMPARISON")
    print(f"{'=' * 100}\n")
    
    # Collect all unique field names
    all_fields = set()
    for system in all_results.values():
        for device in system.values():
            if 'headers' in device:
                all_fields.update(device['headers'])
    
    print(f"Total Unique Fields Across All Systems: {len(all_fields)}\n")
    
    # Group similar fields
    print("Field Presence by System:")
    print(f"{'Field Name':<45} {'FMG':<6} {'FC':<6} {'TD':<6}")
    print("-" * 70)
    
    for field in sorted(all_fields, key=str.lower):
        fmg_has = any(field in system.get('headers', []) 
                      for system in all_results.get('FortiManager', {}).values())
        fc_has = any(field in system.get('headers', []) 
                     for system in all_results.get('FortiCloud', {}).values())
        td_has = any(field in system.get('headers', []) 
                     for system in all_results.get('TopDesk', {}).values())
        
        fmg_mark = "Y" if fmg_has else "-"
        fc_mark = "Y" if fc_has else "-"
        td_mark = "Y" if td_has else "-"
        
        print(f"{field:<45} {fmg_mark:<6} {fc_mark:<6} {td_mark:<6}")
    
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()

