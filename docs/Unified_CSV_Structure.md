# Unified CSV Structure Specification

**Version:** 1.0  
**Last Updated:** October 2, 2025  
**Status:** Production Ready

---

## Overview

This document defines the unified CSV output structure used by all asset export scripts across FortiManager, FortiCloud, and TopDesk systems. All 9 scripts output the same 60 fields in the same order, enabling direct comparison and analysis across systems.

---

## Design Philosophy

### Core Principles

1. **Universal Structure** - ALL 9 scripts output the same 60 fields in the same order
   - FortiManager: FortiGate, FortiSwitch, FortiAP
   - FortiCloud: FortiGate, FortiSwitch, FortiAP  
   - TopDesk: FortiGate, FortiSwitch, FortiAP

2. **Keep ALL Fields** - Even if a system doesn't populate them
   - Empty fields show what data is missing
   - Enables future data enrichment
   - Helps identify data quality gaps
   - Maintains CSV alignment when opened side-by-side

3. **Standardized Naming** - Same concept = Same field name
   - Consistent capitalization and spacing
   - No abbreviations except industry-standard (IP, HA, VDOM)
   - Clear, descriptive names

4. **Standardized Formats** - Directly comparable values
   - **Dates:** Always `YYYY-MM-DD` format
   - **Booleans:** Always `Yes` or `No` (never True/False, 1/0)
   - **Empty:** Always empty string (never "N/A", "None", "null")
   - **Integers:** Plain numbers, no decimals
   - **Strings:** Trimmed whitespace, preserve original casing

5. **Device-Agnostic** - One structure for all device types
   - FortiGate-specific fields present but empty for Switches/APs
   - FortiSwitch/AP-specific fields present but empty for FortiGates
   - Makes all exports structurally identical

---

## Complete Field Specification

**Total Fields: 60**

### Section 1: Core Identification (7 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 1 | Serial Number | String | ✓ | ✓ | ✓ | Unique device serial number |
| 2 | Device Name | String | ✓ | ✓ | ✓ | User-assigned device name |
| 3 | Hostname | String | ✓ | ~ | ✓ | Device hostname (FC always empty) |
| 4 | Model | String | ✓ | ✓ | ✓ | Device model (e.g., "FortiGate-60F") |
| 5 | Description | String | ✓ | ✓ | ✓ | Device description or summary |
| 6 | Asset Type | String | ✓ | ✓ | ✓ | "Firewall", "Switch", or "Access Point" |
| 7 | Source System | String | ✓ | ✓ | ✓ | "FortiManager", "FortiCloud", or "TopDesk" |

### Section 2: Network & Connection (4 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 8 | Management IP | IP Address | ✓ | ✗ | ✗ | Device management IP address |
| 9 | Connection Status | String | ✓ | ✓ | ✓ | Connection/operational status |
| 10 | Management Mode | String | ✓ | ✗ | ✗ | Management mode (FMG only) |
| 11 | Firmware Version | String | ✓ | ✗ | ✗ | OS/Firmware version |

### Section 3: Organization & Location (7 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 12 | Company | String | ~ | ✓ | ~ | Company/organization name |
| 13 | Organizational Unit | String | ✓ | ✓ | ✗ | ADOM or OU name |
| 14 | Branch | String | ✗ | ✗ | ✓ | Branch location (TD only) |
| 15 | Location | String | ~ | ✗ | ~ | Physical location |
| 16 | Folder Path | String | ✗ | ✓ | ✗ | Asset folder path (FC only) |
| 17 | Folder ID | String | ✗ | ✓ | ✗ | Asset folder ID (FC only) |
| 18 | Vendor | String | ✓ | ✓ | ✓ | Always "Fortinet" |

### Section 4: Contract Information (9 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 19 | Contract Number | String | ✗ | ✓ | ✓ | Support contract number/name |
| 20 | Contract SKU | String | ✗ | ✓ | ✗ | Contract SKU (FC only) |
| 21 | Contract Type | String | ✗ | ✗ | ✓ | Contract type (TD only) |
| 22 | Contract Summary | String | ✗ | ✗ | ✓ | Contract description (TD only) |
| 23 | Contract Start Date | Date | ✗ | ✓ | ✓ | Contract start date |
| 24 | Contract Expiration Date | Date | ✗ | ✓ | ✓ | Contract expiration date |
| 25 | Contract Status | String | ✗ | ~ | ✓ | Contract status |
| 26 | Contract Support Type | String | ✗ | ✓ | ✗ | Support type (FC only) |
| 27 | Contract Archived | Boolean | ✗ | ✗ | ✓ | Contract archived status |

### Section 5: Entitlement Information (4 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 28 | Entitlement Level | String | ✗ | ✓ | ✗ | Entitlement level (FC only) |
| 29 | Entitlement Type | String | ✗ | ✓ | ✗ | Entitlement type (FC only) |
| 30 | Entitlement Start Date | Date | ✗ | ✓ | ✗ | Entitlement start (FC only) |
| 31 | Entitlement End Date | Date | ✗ | ✓ | ✗ | Entitlement end (FC only) |

### Section 6: Lifecycle & Status (7 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 32 | Status | String | ✓ | ✓ | ✓ | Device/connection status |
| 33 | Is Decommissioned | Boolean | ✗ | ✓ | ✗ | Device decommissioned (FC only) |
| 34 | Archived | Boolean | ✗ | ~ | ✓ | Device archived status |
| 35 | Registration Date | Date | ✗ | ✓ | ✗ | Registration date (FC only) |
| 36 | Product EoR | Date | ✗ | ✓ | ✗ | End of Release (FC only) |
| 37 | Product EoS | Date | ✗ | ✓ | ✗ | End of Support (FC only) |
| 38 | Last Updated | DateTime | ✓ | ~ | ✓ | Last update timestamp |

### Section 7: Account Information (3 fields)

| # | Field Name | Data Type | FMG | FC | TD | Description |
|---|------------|-----------|-----|----|----|-------------|
| 39 | Account ID | String | ✗ | ✓ | ✗ | Account ID (FC only) |
| 40 | Account Email | String | ✗ | ✓ | ✗ | Account email (FC only) |
| 41 | Account OU ID | String | ✗ | ✓ | ✗ | Account OU ID (FC only) |

### Section 8: FortiGate-Specific Fields (6 fields)

*Only populated for FortiGate devices from FortiManager*

| # | Field Name | Data Type | Description |
|---|------------|-----------|-------------|
| 42 | HA Mode | String | HA mode (Standalone, Active-Passive, Cluster) |
| 43 | HA Cluster Name | String | HA cluster name |
| 44 | HA Role | String | HA role (Primary, Secondary) |
| 45 | HA Member Status | String | HA member status (Online, Offline) |
| 46 | HA Priority | Integer | HA failover priority |
| 47 | Max VDOMs | Integer | Maximum VDOMs supported |

### Section 9: FortiSwitch/FortiAP Parent Tracking (4 fields)

*Only populated for FortiSwitch/FortiAP devices from FortiManager*

| # | Field Name | Data Type | Description |
|---|------------|-----------|-------------|
| 48 | Parent FortiGate | String | Managing FortiGate name |
| 49 | Parent FortiGate Serial | String | Managing FortiGate serial |
| 50 | Parent FortiGate Platform | String | Managing FortiGate model |
| 51 | Parent FortiGate IP | String | Managing FortiGate IP |

### Section 10: FortiSwitch-Specific Fields (3 fields)

*Only populated for FortiSwitch devices from FortiManager*

| # | Field Name | Data Type | Description |
|---|------------|-----------|-------------|
| 52 | Device Type | String | Device type (physical, virtual) |
| 53 | Max PoE Budget | Integer | Maximum PoE budget in Watts |
| 54 | Join Time | String | Time switch joined FortiGate |

### Section 11: FortiAP-Specific Fields (6 fields)

*Only populated for FortiAP devices from FortiManager*

| # | Field Name | Data Type | Description |
|---|------------|-----------|-------------|
| 55 | Board MAC | String | Access point MAC address |
| 56 | Admin Status | String | Administrative status |
| 57 | Client Count | Integer | Number of connected clients |
| 58 | Mesh Uplink | String | Uplink type (ethernet, mesh) |
| 59 | WTP Mode | String | Wireless Termination Point mode |
| 60 | VDOM | String | Virtual Domain name |

---

## CSV Header (Copy-Paste Ready)

```csv
Serial Number,Device Name,Hostname,Model,Description,Asset Type,Source System,Management IP,Connection Status,Management Mode,Firmware Version,Company,Organizational Unit,Branch,Location,Folder Path,Folder ID,Vendor,Contract Number,Contract SKU,Contract Type,Contract Summary,Contract Start Date,Contract Expiration Date,Contract Status,Contract Support Type,Contract Archived,Entitlement Level,Entitlement Type,Entitlement Start Date,Entitlement End Date,Status,Is Decommissioned,Archived,Registration Date,Product EoR,Product EoS,Last Updated,Account ID,Account Email,Account OU ID,HA Mode,HA Cluster Name,HA Role,HA Member Status,HA Priority,Max VDOMs,Parent FortiGate,Parent FortiGate Serial,Parent FortiGate Platform,Parent FortiGate IP,Device Type,Max PoE Budget,Join Time,Board MAC,Admin Status,Client Count,Mesh Uplink,WTP Mode,VDOM
```

---

## Data Format Standards

### Date Fields
- **Format:** `YYYY-MM-DD`
- **Examples:** `2025-10-02`, `2024-11-19`, `2023-05-15`
- **Empty:** Empty string `""` (not "N/A", "0000-00-00", or "null")

**Source Conversions:**
- FortiManager: `2025-10-01 16:05:29` → `2025-10-01`
- FortiCloud: `2025-01-23T10:20:30Z` → `2025-01-23`
- TopDesk: `2025-08-22T14:46:42.200` → `2025-08-22`

### DateTime Fields (Last Updated only)
- **Format:** `YYYY-MM-DD HH:MM:SS`
- **Examples:** `2025-10-02 00:14:37`, `2025-08-22 14:46:42`
- **Empty:** Empty string `""`

### Boolean Fields
- **Format:** `Yes` or `No` (case-sensitive)
- **Fields:** Is Decommissioned, Archived, Contract Archived
- **Empty:** Empty string `""` (if field doesn't apply to system)

**Source Conversions:**
- Python: `True` → `Yes`, `False` → `No`
- JSON: `true` → `Yes`, `false` → `No`

### Integer Fields
- **Format:** Plain integer, no decimals or thousand separators
- **Fields:** HA Priority, Max VDOMs, Max PoE Budget, Client Count
- **Examples:** `128`, `10`, `1500`, `0`
- **Empty:** Empty string `""` (not `0`)

### String Fields
- **Trimming:** Remove leading and trailing whitespace
- **Empty:** Empty string `""` (never "N/A", "None", "null", or "Unknown")
  - **Exception:** If source explicitly provides "Unknown" as a value, keep it
- **Case:** Preserve original casing from source system

### IP Address Fields
- **Format:** Standard IPv4 dotted notation
- **Examples:** `192.168.1.1`, `10.0.0.254`
- **Empty:** Empty string `""`

---

## Implementation Guidelines

### Adding a New Field

If you need to add a new field to the structure:

1. **Choose the Correct Section** - Add to appropriate section based on field purpose
2. **Determine Population** - Identify which systems (FMG/FC/TD) will populate it
3. **Update ALL Scripts** - Add field to all 9 scripts (even if empty)
4. **Standardize Format** - Follow data format standards
5. **Update This Document** - Add field to specification with clear description
6. **Test All Exports** - Verify all 9 CSVs still have aligned columns

### Removing or Renaming a Field

1. **Update ALL Scripts** - Modify all 9 scripts simultaneously
2. **Maintain Order** - If renaming, keep same position
3. **If Removing** - Consider leaving empty instead for historical compatibility
4. **Update This Document** - Reflect changes in specification
5. **Test Alignment** - Verify CSVs can still be compared side-by-side

### Modifying Data Formats

1. **Update Format Standards** - Document new format in this document
2. **Update ALL Scripts** - Implement format change in all applicable scripts
3. **Update Helper Functions** - Modify date/boolean/integer formatting functions
4. **Test Consistency** - Verify format is applied correctly across all systems
5. **Document Conversions** - Add source conversion examples

### Best Practices

**DO:**
- Keep field order consistent across all scripts
- Use descriptive field names
- Document which systems populate each field
- Include empty fields for unpopulated data
- Follow established format standards
- Test with real data after changes

**DON'T:**
- Use different field names for same concept across scripts
- Use abbreviations unless industry-standard
- Mix formats (e.g., Yes/No and True/False)
- Remove fields without testing impact
- Add fields without updating all 9 scripts
- Use special characters in field names

---

## Validation Checklist

After making any changes to the structure, verify:

- [ ] All 9 scripts have exactly 60 fields
- [ ] Field names are identical across all scripts
- [ ] Field order is identical across all scripts
- [ ] All dates use YYYY-MM-DD format
- [ ] All booleans use Yes/No format
- [ ] Empty fields are truly empty (not "N/A")
- [ ] All 9 scripts run without errors
- [ ] Generated CSVs can be opened side-by-side with aligned columns
- [ ] This documentation is updated to reflect changes
- [ ] Field mappings in each script match this specification

---

## System-Specific Notes

### FortiManager
- Provides real-time operational data
- Rich HA configuration details
- Parent device tracking for FortiSwitch/FortiAP
- No contract or license information
- Model extraction required for FortiSwitch/FortiAP from firmware string

### FortiCloud
- Comprehensive contract and entitlement data
- Registration and lifecycle dates
- Account and organizational structure
- No real-time operational status
- No parent device tracking

### TopDesk
- Asset management and contract tracking
- Branch and location information
- Serial numbers may need extraction from contract names
- Multiple rows per device if multiple contracts
- Limited technical device details

---

## Example Row (FortiGate from FortiManager)

```csv
FGT60F123456789,Corp-FW-01,corp-fw-01.example.local,FortiGate-60F,Corporate Firewall,Firewall,FortiManager,10.0.1.1,Connected,Normal,v7.4.1-build2463,ACME Corp,Production,,,,,Fortinet,,,,,,,,,,,,,Connected,No,No,,,,2025-10-02 00:14:37,,,Standalone,,,,,10,,,,,,,,,,,,
```

---

## Support & Maintenance

**Version History:**
- v1.0 (2025-10-02): Initial unified structure with 60 fields

**Questions or Issues:**
- Review this document for field specifications
- Check `scripts/` folder for implementation examples
- See `README.md` for project overview

---

**Document Status:** Production Ready  
**Maintained By:** Project Team  
**Review Frequency:** As needed when structure changes

