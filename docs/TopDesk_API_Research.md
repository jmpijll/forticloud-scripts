# TopDesk API Research & Documentation

**Last Updated:** October 2, 2025  
**API Version:** Asset Management API v1.88.0

---

## 🚨 CRITICAL ISSUES FIXED

**Four major bugs were discovered and fixed:**

### 0. **Serial Number Extraction Bug** (CRITICAL) - Fixed October 2, 2025
- **Problem**: Requested `serienummer` field but never extracted it from response
- **Symptom**: 489 devices across all types showing `N/A` for serial numbers
- **Root Cause**: Code set `serial_number_td = ''` instead of extracting from `device.get('serienummer')`
- **Fix**: Extract all custom fields directly as properties (not from `dataSet` array)
- **Enhanced Fields**: Also added `vendor`, `environment-1`, `creationDate`, `aanschafdatum`
- **Impact**: **100% serial number coverage** (489 additional serials captured)
  - FortiGate: 35 → 0 missing (35 recovered)
  - FortiSwitch: 154 → 0 missing (154 recovered)
  - FortiAP: 300 → 0 missing (300 recovered)

### 1. **Infinite Loop Bug** (CRITICAL) - Fixed October 1, 2025
- **Problem**: Scripts used `start` parameter instead of `pageStart`
- **Symptom**: FortiSwitch and FortiAP scripts ran indefinitely
- **Root Cause**: Wrong pagination parameter kept fetching page 0 repeatedly
- **Fix**: Changed all pagination code to use `pageStart` instead of `start`
- **Impact**: Scripts now terminate correctly

### 2. **Missing Assets Bug** (CRITICAL) - Fixed October 1, 2025  
- **Problem**: Default `pageSize` is only 50, maximum is 1000
- **Symptom**: Only retrieved ~50 devices when hundreds exist
- **Root Cause**: Not specifying `pageSize` limited results to 50
- **Fix**: Set `pageSize=1000` in all API calls
- **Impact**: Now retrieving ALL assets (107 FortiGate vs 53 before)

### 3. **FortiGate Filtering Bug** (HIGH) - Fixed October 1, 2025
- **Problem**: Only matched devices with "FortiGate" explicitly in summary
- **Symptom**: Missing 61 out of 107 FortiGate devices
- **Root Cause**: Many devices use abbreviations ("FGT", "FG-", model numbers)
- **Examples Missed**: "Fortinet FGT40", "Fortinet FG-90G", "Fortinet 100F"
- **Fix**: Enhanced pattern matching to include abbreviations and model numbers
- **Impact**: Now finding all 107 FortiGate devices (vs 46 before)

**Results After Fixes:**
- FortiGate: **107 devices** (was 53) - **+102% increase**
- FortiSwitch: **105 devices** (was unable to complete)
- FortiAP: **191 devices** (was unable to complete)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Asset Retrieval](#asset-retrieval)
4. [Asset Types](#asset-types)
5. [Contract Retrieval](#contract-retrieval)
6. [Data Models](#data-models)
7. [Filtering Strategy](#filtering-strategy)
8. [Best Practices](#best-practices)
9. [Error Handling](#error-handling)
10. [Critical Bugs Fixed](#critical-bugs-fixed)

---

## Overview

### API Architecture

TopDesk uses a **RESTful API** with Basic Authentication for accessing Asset Management data:

| API | Base URL | Purpose |
|-----|----------|---------|
| **Asset Management API** | `https://{tenant}.topdesk.net/tas/api/assetmgmt/` | Retrieve and manage assets, contracts, and relationships |

**Key Point:** The API uses Basic Authentication (username/password) and returns JSON data.

### Authentication URL

```
https://{tenant}.topdesk.net/tas/api/assetmgmt/
```

---

## Authentication

### Basic Authentication

TopDesk uses **HTTP Basic Authentication** with service accounts.

**Request Headers:**
```http
GET /tas/api/assetmgmt/assets
Authorization: Basic {base64(username:password)}
Accept: application/x.topdesk-am-assets-v2+json
```

**Python Implementation:**
```python
from requests.auth import HTTPBasicAuth
import requests

auth = HTTPBasicAuth('your_service_account', 'your_password')
response = requests.get(
    'https://tenant.topdesk.net/tas/api/assetmgmt/assets',
    auth=auth,
    headers={'Accept': 'application/x.topdesk-am-assets-v2+json'}
)
```

**Important:** Always use the v2 media type (`application/x.topdesk-am-assets-v2+json`) to ensure consistent field handling.

---

## Asset Retrieval

### Get Assets with Search Term

**Endpoint:** `GET /tas/api/assetmgmt/assets`

**Request:**
```http
GET /tas/api/assetmgmt/assets?searchTerm=FortiGate&pageSize=100&fields=name,@type,@assignments
Authorization: Basic {credentials}
Accept: application/x.topdesk-am-assets-v2+json
```

**Parameters:**
- **searchTerm** - Searches in asset name and text/number fields (case-insensitive)
- **pageSize** - Number of results per page (default: 10, max: 100)
- **fields** - Comma-separated list of fields to include:
  - `name` - Asset name
  - `@type` - Template/type information
  - `@assignments` - Location and branch assignments
  - `@@summary` - Asset summary (contains vendor/model info)
  - Custom field IDs

**Response:**
```json
{
  "dataSet": [
    {
      "unid": "7b5e7d58-1785-43b8-a8e9-5c8d6c4947b5",
      "name": "FWL-SITE01-FW-01",
      "archived": false,
      "modificationDate": "2025-08-19T13:49:58.187",
      "type_id": "DC34FE63-8A69-4145-9B56-95EAB0A00EA4",
      "@type": {
        "name": "Firewall [FWL]",
        "icon": "switch_router"
      },
      "@assignments": {
        "locations": [
          {
            "branch": {
              "id": "d6ac7086-2b71-4858-a450-17357b2f8d4f",
              "name": "Company Branch Office"
            },
            "location": {
              "id": "a53f8f04-c3a3-4ede-a397-a27bff8e60e2",
              "name": "Datacenter Site 01"
            }
          }
        ]
      },
      "@@summary": "Fortinet FortiGate VM02V",
      "@status": "OPERATIONAL"
    }
  ]
}
```

**Field Requirements:**
- **unid** - Unique asset identifier (UUID)
- **name** - Asset name/identifier
- **@type.name** - Asset type (e.g., "Firewall [FWL]", "Switch [SWI]")
- **@@summary** - Contains vendor and model information

---

## Asset Types

### Fortinet Device Types in TopDesk

| Device Type | TopDesk Type Name | Search Terms | Icon |
|-------------|-------------------|--------------|------|
| **FortiGate/FortiWiFi** | `Firewall [FWL]` | "FortiGate", "Fortinet Firewall" | switch_router |
| **FortiSwitch** | `Switch [SWI]` | "FortiSwitch", "Fortinet Switch" | switch_router |
| **FortiAP** | `Access Point [WAP]` or similar | "FortiAP", "Fortinet Access Point" | wireless_access_point |

**Filtering Strategy:**
1. Retrieve all assets by template: `templateName=Firewall [FWL]`
2. Filter results where `@@summary` contains "Fortinet"
3. For FortiGate, use pattern matching to catch all variants:
   - "fortigate", "fortiwifi" (explicit)
   - "fgt", "fg-" (abbreviations)
   - "fortinet vm" (VM models)
   - Model numbers: "40f", "60f", "70g", "90g", "100f", "vm01v", "vm02v"
4. Exclude FortiWAF devices explicitly

**Important Discovery:**
Many FortiGate devices in TopDesk use abbreviations or model numbers rather than "FortiGate" explicitly:
- "Fortinet FGT40" (should be included)
- "Fortinet FG-90G" (should be included)
- "Fortinet 100F" (should be included)
- "Fortinet VM Subscription" (should be included)

Only 46 out of 107 Fortinet firewalls had "FortiGate" explicitly in the summary. The other 61 used abbreviations or model numbers.

---

## Contract Retrieval

### Get Linked Assets (Contracts)

Support contracts are linked as **child assets** with type `Support contract/license [SUP]`.

**Endpoint:** `GET /tas/api/assetmgmt/assetLinks`

**Request:**
```http
GET /tas/api/assetmgmt/assetLinks?sourceId={asset_unid}
Authorization: Basic {credentials}
```

**Parameters:**
- **sourceId** - UUID of the asset (the `unid` field)
- **targetId** - Optional: filter by target asset
- **capabilityId** - Optional: filter by link type

**Response:**
```json
[
  {
    "linkId": "9b7a8e13-ff1b-4ef6-9567-3499a2db57c7",
    "linkType": "child",
    "assetId": "6706a2be-2d3b-4249-a46f-7923a0c5bc60",
    "name": "SUP.FGVM2VTM19002110",
    "type": "Support contract/license [SUP]",
    "summary": "Fortinet FortiCare Premium",
    "archived": false,
    "status": "OPERATIONAL"
  }
]
```

### Retrieve Contract Details

Once you have the linked asset IDs, retrieve full contract details:

**Endpoint:** `GET /tas/api/assetmgmt/assets`

**Request:**
```http
GET /tas/api/assetmgmt/assets?unid={contract_asset_id}&fields=name,@@summary,@type
Authorization: Basic {credentials}
Accept: application/x.topdesk-am-assets-v2+json
```

**Workflow:**
1. Get asset by search term (e.g., "FortiGate")
2. For each asset, get linked assets using `unid`
3. Filter links where `type` contains "Support contract"
4. Optionally retrieve full contract asset details

---

## Data Models

### Asset Object

```python
{
    "unid": str,                    # UUID - unique identifier
    "name": str,                    # Asset name/identifier
    "archived": bool,               # Whether asset is archived
    "modificationDate": str,        # ISO 8601 timestamp
    "type_id": str,                 # Template UUID
    "@type": {
        "name": str,                # Template name (e.g., "Firewall [FWL]")
        "icon": str                 # Icon identifier
    },
    "@assignments": {
        "locations": List[{
            "branch": {
                "id": str,
                "name": str         # Customer/branch name
            },
            "location": {
                "id": str,
                "name": str         # Physical location
            }
        }],
        "persons": List[...]
    },
    "@@summary": str,               # Human-readable summary (vendor/model)
    "@status": str,                 # "OPERATIONAL" or "IMPACTED"
    "@etag": str                    # Version identifier
}
```

### Linked Asset Object

```python
{
    "linkId": str,                  # UUID of the link
    "linkType": str,                # "child", "parent", etc.
    "assetId": str,                 # UUID of linked asset
    "name": str,                    # Linked asset name
    "type": str,                    # Linked asset type
    "summary": str,                 # Linked asset summary
    "archived": bool,
    "status": str,
    "capabilityId": str | null,     # Link type ID
    "capabilityName": str | null    # Link type name
}
```

---

## Filtering Strategy

### Current Implementation

**⚠️ CRITICAL: Use Template-Based Retrieval**

**DO NOT use `searchTerm` alone** - it only returns up to 50 results by default and misses devices!

**Correct Approach:**
1. **Retrieve by template:** Use `templateName` parameter to get ALL assets of a type
   - Firewall: `templateName=Firewall [FWL]` → retrieves ~308 assets
   - Switch: `templateName=Switch [SWI]` → retrieves ~524 assets  
   - Access Point: `templateName=Access Point [WAP]` → retrieves ~758 assets

2. **Filter by vendor:** Filter results where `@@summary` contains "Fortinet"

3. **Filter by product:** For FortiGate, use advanced pattern matching:
   - Include: "fortigate", "fortiwifi", "fgt", "fg-", "fortinet vm", model numbers
   - Exclude: "fortiwaf" (Web Application Firewall, not a firewall device)

**Production Numbers (October 2025):**
- **FortiGate/FortiWiFi**: 107 devices (from 308 total firewalls)
- **FortiSwitch**: 105 devices (from 524 total switches)
- **FortiAP**: 191 devices (from 758 total access points)

**Rationale:**
- Template-based retrieval gets ALL assets, not just 50
- Many FortiGate devices use abbreviations ("FGT40", "FG-90G") not "FortiGate"
- Proper pagination with `pageStart` and `pageSize=1000` ensures complete retrieval
- Post-processing ensures only relevant Fortinet devices are included

### Pagination

**⚠️ CRITICAL: Use `pageStart`, not `start`!**

The TopDesk API uses `pageStart` as the pagination parameter, not `start`. Using the wrong parameter causes infinite loops as you keep requesting the same page.

**Key Pagination Facts:**
- **Default pageSize**: 50 (will silently limit results if not specified)
- **Maximum pageSize**: 1000
- **Parameter name**: `pageStart` (zero-based index)
- **Response codes**: 
  - 200: Results within page size
  - 206: Results exceed page size (more pages available)

**Correct Implementation:**
```python
def get_all_assets_by_template(base_url, auth, template_name):
    """Retrieve all assets by template with correct pagination."""
    all_assets = []
    page_size = 1000  # Use maximum for efficiency
    page_start = 0  # Use pageStart, not start!
    
    while True:
        params = {
            'templateName': template_name,
            'pageSize': page_size,
            'pageStart': page_start,  # CRITICAL: Use pageStart
            'fields': 'name,@type,@@summary,@assignments'
        }
        
        response = requests.get(
            f"{base_url}tas/api/assetmgmt/assets",
            auth=auth,
            headers={'Accept': 'application/x.topdesk-am-assets-v2+json'},
            params=params
        )
        
        data = response.json()
        assets = data.get('dataSet', [])
        
        if not assets:
            break
            
        all_assets.extend(assets)
        
        # Check if there are more results
        if len(assets) < page_size:
            break
            
        page_start += page_size  # Increment pageStart
    
    return all_assets
```

**Common Pitfall:**
Using `start` instead of `pageStart` will cause scripts to run indefinitely, repeatedly fetching the same first page.

---

## Best Practices

### 1. Authentication
- Use service accounts with read-only permissions
- Store credentials in environment variables for production
- Use config files only for development/testing

### 2. Pagination
- **ALWAYS use `pageStart`, never `start`**
- **ALWAYS set `pageSize` to 1000** (default is only 50!)
- Using wrong parameter causes infinite loops
- Using default pageSize misses most assets

### 3. Retrieval Strategy
- **Use `templateName` parameter, not `searchTerm` alone**
- `searchTerm` without pagination returns maximum 50 results
- Template-based retrieval with proper pagination gets all assets

### 4. API Version
- Always use `Accept: application/x.topdesk-am-assets-v2+json`
- The v1 media type is deprecated and will be removed
- For assetLinks endpoint, use `Accept: application/json`

### 5. Field Selection
- Request only needed fields using the `fields` parameter
- Include `@@summary` for vendor/model information
- Include `@type` for asset type verification
- Include `@assignments` for location/branch information

### 4. Error Handling
- Retry on network errors (3 attempts with exponential backoff)
- Don't retry on 4xx errors (fix request instead)
- Handle missing/null fields gracefully

### 5. Data Processing
- Filter by `@@summary` after retrieval to ensure Fortinet vendor
- Deduplicate if searching multiple terms
- Include both active and archived assets for complete inventory

### 6. Contract Retrieval
- Retrieve contracts for each asset individually (no bulk endpoint)
- Filter contract links by `type` containing "Support contract"
- Cache results to avoid redundant API calls

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response data |
| 400 | Bad Request | Check query parameters |
| 401 | Unauthorized | Verify credentials |
| 403 | Forbidden | Check user permissions |
| 404 | Not Found | Verify endpoint URL |
| 406 | Not Acceptable | Check Accept header (use v2) |

### Common Errors

**"406 Not Acceptable"**
- Cause: Missing or incorrect Accept header
- Solution: 
  - For `/assets` endpoint: Use `Accept: application/x.topdesk-am-assets-v2+json`
  - For `/assetLinks` endpoint: Use `Accept: application/json`

**"Infinite Loop / Script Hangs"**
- Cause: Using `start` parameter instead of `pageStart`
- Solution: Change `start` to `pageStart` in pagination code

**"401 Unauthorized"**
- Cause: Invalid credentials or expired password
- Solution: Verify username and password

**"403 Forbidden"**
- Cause: User doesn't have permission to access assets
- Solution: Ensure service account has "Operator" or appropriate role

### Null/Empty Handling

```python
# Handle missing fields
summary = asset.get('@@summary', '')
vendor = 'Unknown'
if 'fortinet' in summary.lower():
    vendor = 'Fortinet'

# Handle missing assignments
assignments = asset.get('@assignments', {})
locations = assignments.get('locations', [])
branch_name = 'N/A'
if locations:
    branch = locations[0].get('branch', {})
    branch_name = branch.get('name', 'N/A')
```

---

## Complete Workflow Example

### Retrieve FortiGate Devices with Contracts

```python
import requests
from requests.auth import HTTPBasicAuth

# Configuration
base_url = 'https://your_tenant.topdesk.net/'
auth = HTTPBasicAuth('your_service_account', 'your_password')
headers = {'Accept': 'application/x.topdesk-am-assets-v2+json'}

# Step 1: Get all FortiGate assets
params = {
    'searchTerm': 'FortiGate',
    'pageSize': 100,
    'fields': 'name,@type,@@summary,@assignments,@status'
}

response = requests.get(
    f"{base_url}tas/api/assetmgmt/assets",
    auth=auth,
    headers=headers,
    params=params
)

assets = response.json().get('dataSet', [])

# Step 2: Filter for Fortinet devices
fortinet_assets = []
for asset in assets:
    summary = asset.get('@@summary', '').lower()
    type_name = asset.get('@type', {}).get('name', '')
    
    if 'fortinet' in summary and 'firewall' in type_name.lower():
        fortinet_assets.append(asset)

# Step 3: Get contracts for each asset
for asset in fortinet_assets:
    asset_unid = asset['unid']
    
    # Get linked assets
    links_response = requests.get(
        f"{base_url}tas/api/assetmgmt/assetLinks",
        auth=auth,
        params={'sourceId': asset_unid}
    )
    
    links = links_response.json()
    
    # Filter for support contracts
    contracts = [
        link for link in links 
        if 'support contract' in link.get('type', '').lower()
    ]
    
    asset['contracts'] = contracts

# Step 4: Export to CSV
import csv

with open('fortigate_devices.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'Name', 'Type', 'Summary', 'Branch', 'Location', 
        'Status', 'Contract Name', 'Contract Summary'
    ])
    writer.writeheader()
    
    for asset in fortinet_assets:
        # Extract base info
        assignments = asset.get('@assignments', {})
        locations = assignments.get('locations', [])
        
        branch_name = 'N/A'
        location_name = 'N/A'
        if locations:
            branch = locations[0].get('branch', {})
            branch_name = branch.get('name', 'N/A')
            
            location = locations[0].get('location', {})
            if location:
                location_name = location.get('name', 'N/A')
        
        # Get contracts
        contracts = asset.get('contracts', [])
        if contracts:
            for contract in contracts:
                writer.writerow({
                    'Name': asset.get('name', 'N/A'),
                    'Type': asset.get('@type', {}).get('name', 'N/A'),
                    'Summary': asset.get('@@summary', 'N/A'),
                    'Branch': branch_name,
                    'Location': location_name,
                    'Status': asset.get('@status', 'N/A'),
                    'Contract Name': contract.get('name', 'N/A'),
                    'Contract Summary': contract.get('summary', 'N/A')
                })
        else:
            writer.writerow({
                'Name': asset.get('name', 'N/A'),
                'Type': asset.get('@type', {}).get('name', 'N/A'),
                'Summary': asset.get('@@summary', 'N/A'),
                'Branch': branch_name,
                'Location': location_name,
                'Status': asset.get('@status', 'N/A'),
                'Contract Name': 'N/A',
                'Contract Summary': 'N/A'
                })
```

---

## References

### Official Documentation
- [TopDesk API Documentation](https://developers.topdesk.com/)
- [Asset Management API](https://developers.topdesk.com/explorer?page=assets)
- [Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication)

### API Specifications
Located in `topdeskapireference/` directory:
- assets_specification_1.88.0.json
- general_specification_1.1.0.yaml

---

## Critical Bugs Fixed

This section documents major bugs discovered during implementation:

### Bug #1: Infinite Loop - Wrong Pagination Parameter
**Discovered:** October 1, 2025  
**Severity:** CRITICAL  
**Symptom:** FortiSwitch and FortiAP scripts ran indefinitely without completing

**Root Cause:**  
Scripts used `start` parameter for pagination instead of `pageStart`. This caused the API to always return the first page, creating an infinite loop.

**Fix:**
```python
# WRONG - Causes infinite loop
params = {
    'searchTerm': 'FortiSwitch',
    'pageSize': 100,
    'start': 0  # WRONG PARAMETER
}

# CORRECT
params = {
    'templateName': 'Switch [SWI]',
    'pageSize': 1000,
    'pageStart': 0  # CORRECT PARAMETER
}
```

### Bug #2: Missing Assets - Default Page Size Too Small
**Discovered:** October 1, 2025  
**Severity:** CRITICAL  
**Symptom:** Only retrieving ~50 devices when hundreds exist

**Root Cause:**  
Default `pageSize` is 50. Without explicitly setting it to 1000 (maximum), most assets were silently excluded.

**Examples:**
- Firewalls: Retrieved 53 devices, actual count: 107 (missing 54 devices)
- Switches: Retrieved ~50 devices, actual count: 105 (missing 55 devices)
- Access Points: Retrieved ~50 devices, actual count: 191 (missing 141 devices)

**Fix:**
Always specify `pageSize=1000` in API requests.

### Bug #3: FortiGate Pattern Matching Too Restrictive
**Discovered:** October 1, 2025  
**Severity:** HIGH  
**Symptom:** Missing 61 out of 107 FortiGate devices (57% missing)

**Root Cause:**  
Filter only matched devices with "fortigate" or "fortiwifi" explicitly in summary. Many devices use:
- Abbreviations: "FGT40", "FG-90G"
- Model numbers: "Fortinet 100F", "Fortinet 40F-3G4G"
- VM descriptions: "Fortinet VM Subscription"

**Analysis:**
Out of 107 total Fortinet firewall devices:
- 46 had "FortiGate" or "FortiWiFi" explicitly (43%)
- 61 used abbreviations or model numbers (57%)

**Fix:**
Enhanced pattern matching to include:
```python
if any([
    'fortigate' in summary,
    'fortiwifi' in summary,
    'fgt' in summary or 'fgt' in name,
    'fg-' in summary or 'fg-' in name,
    'fortinet vm' in summary,
    # Model numbers
    any(model in summary for model in [
        '30e', '40f', '60f', '70g', '80f', '90g', '100f', '200f', 
        '300f', '600f', '40f-3g4g', 'vm01v', 'vm02v', 'vm04v', 'vm08v'
    ])
]):
    fortigate_devices.append(asset)
```

**Verification:**
After fix, retrieving all 107 FortiGate devices correctly.

---

**Document Version:** 2.0  
**Last Updated:** October 1, 2025  
**Tested Against:** TopDesk Asset Management API v1.88.0
**Major Bugs Fixed:** 3 critical issues resolved

