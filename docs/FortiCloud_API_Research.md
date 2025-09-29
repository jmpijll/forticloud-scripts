# FortiCloud API Research & Documentation

**Last Updated:** September 30, 2025  
**API Versions:** Asset Management V3, Organization V1, IAM V1

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Account Discovery](#account-discovery)
4. [Device Retrieval](#device-retrieval)
5. [Serial Number Patterns](#serial-number-patterns)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Production Statistics](#production-statistics)

---

## Overview

### API Architecture

FortiCloud uses a **multi-API system** with separate services:

| API | Base URL | Purpose | Client ID |
|-----|----------|---------|-----------|
| **Organization V1** | `https://support.fortinet.com/ES/api/organization/v1/` | List OUs and organizational structure | `organization` |
| **IAM V1** | `https://support.fortinet.com/ES/api/iam/v1/` | List accounts within OUs | `iam` |
| **Asset Management V3** | `https://support.fortinet.com/ES/api/registration/v3/` | Retrieve device/asset information | `assetmanagement` |

**Key Point:** Each API requires authentication with a **service-specific `client_id`**.

### Authentication Server

All APIs authenticate through:
```
https://customerapiauth.fortinet.com/api/v1/oauth/token
```

---

## Authentication

### OAuth 2.0 Password Grant

FortiCloud uses **OAuth 2.0 Password Grant** (not client credentials).

**Request:**
```json
POST https://customerapiauth.fortinet.com/api/v1/oauth/token
Content-Type: application/json

{
  "username": "apiuser-XXXXXXXXXX",
  "password": "your_password",
  "client_id": "assetmanagement",
  "grant_type": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "Bearer",
  "expires_in": 3660
}
```

### Service-Specific Client IDs

| Service | client_id Value |
|---------|----------------|
| Organization API | `"organization"` |
| IAM API | `"iam"` |
| Asset Management API | `"assetmanagement"` |

**Important:** Use the correct `client_id` for each API service!

### Token Usage

```python
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
```

Tokens expire after **~61 minutes**. Reuse tokens across requests to the same service.

---

## Account Discovery

### Step 1: Get Organizational Units

**Authenticate with `client_id: "organization"`**

```http
POST /ES/api/organization/v1/units/list
Authorization: Bearer {org_token}
Content-Type: application/json

{}
```

**Response:**
```json
{
  "status": 0,
  "message": "Request processed successfully",
  "organizationUnits": {
    "orgId": 1234567,
    "name": "Main Organization",
    "orgUnits": [
      {
        "id": 1234567,
        "name": "Main Organization",
        "parentID": 0,
        "desc": ""
      },
      {
        "id": 7654321,
        "name": "Customer Sub-OU",
        "parentID": 1234567,
        "desc": ""
      }
    ]
  }
}
```

### Step 2: Get Accounts Per OU

**Authenticate with `client_id: "iam"`**

```http
POST /ES/api/iam/v1/accounts/list
Authorization: Bearer {iam_token}
Content-Type: application/json

{
  "parentId": 1234567
}
```

**Response:**
```json
{
  "status": 0,
  "message": "Request processed successfully",
  "accounts": [
    {
      "id": 123456,
      "parentId": 1234567,
      "company": "Example Company",
      "email": "api.user@example.com",
      "firstName": "API",
      "lastName": "User"
    }
  ]
}
```

**Process:**
1. Query main `orgId`
2. Query each OU in `orgUnits` list
3. Deduplicate account IDs
4. Build metadata map: `accountId` → `{company, ou_name}`

---

## Device Retrieval

### Get Devices from Account

**Authenticate with `client_id: "assetmanagement"`**

```http
POST /ES/api/registration/v3/products/list
Authorization: Bearer {asset_token}
Content-Type: application/json

{
  "serialNumber": "F",
  "accountId": 123456
}
```

**Field Requirements:**
- **serialNumber** - Required (pattern to match)
- **accountId** - Required for Organization-scope users

**Optional fields** (not used in current implementation):
- ~~`status`~~ - Removed to include all devices (Registered + Decommissioned)
- ~~`productModel`~~ - Filter after retrieval for flexibility
- ~~`expireBefore`~~ - Not used

**Response:**
```json
{
  "status": 0,
  "message": "Request processed successfully",
  "assets": [
    {
      "serialNumber": "FGT60FTK12345678",
      "productModel": "FortiGate-60F",
      "description": "Main Firewall",
      "accountId": 123456,
      "status": "Registered",
      "isDecommissioned": false,
      "registrationDate": "2023-05-15T10:20:30",
      "folderId": 1551555,
      "folderPath": "/My Assets/Production",
      "productModelEoR": null,
      "productModelEoS": null,
      "entitlements": [
        {
          "level": 6,
          "levelDesc": "Web/Online",
          "type": 2,
          "typeDesc": "Firmware & General Updates",
          "startDate": "2023-05-15T00:00:00",
          "endDate": "2024-05-15T00:00:00"
        }
      ],
      "contracts": [
        {
          "contractNumber": "1234ABC",
          "sku": "FC-10-F60FT-247-02-12",
          "terms": [
            {
              "endDate": "2024-05-15T00:00:00",
              "startDate": "2023-05-15T00:00:00",
              "supportType": "Hardware"
            }
          ]
        }
      ]
    }
  ],
  "pageNumber": 1,
  "totalPages": 1
}
```

### Filtering Strategy

**Current Implementation:**
1. Retrieve ALL devices using serial patterns
2. Apply `productModel.startswith()` filter after retrieval
3. Include decommissioned devices (filter in CSV if needed)

**Rationale:**
- More flexible than API-side filtering
- Ensures complete data retrieval
- Single codebase for all device types

---

## Serial Number Patterns

### Critical Discovery: Multi-Pattern Requirements

Different Fortinet devices have different serial number prefixes:

#### FortiSwitch - **REQUIRES MULTIPLE PATTERNS** ⚠️

FortiSwitch devices start with **TWO** different patterns:

| Pattern | Example Serials | Models |
|---------|-----------------|--------|
| **F** | FS1E48T422003020 | FortiSwitch 1024E, 1048E |
| **S** | S108EN5918003626, S124FPTF24009790, S148FFTF23026095 | All other models (108E/F, 124E/F, 148F, 224E, 248E, 424E, 448E, etc.) |

**Solution:**
```python
# Query with BOTH patterns
for pattern in ['F', 'S']:
    devices = api.get_devices(account_id, pattern)
    all_devices.extend(devices)

# Deduplicate by serial number
unique_devices = deduplicate_by_serial(all_devices)

# Filter by product model
fortiswitches = [d for d in unique_devices 
                 if d['productModel'].startswith('FortiSwitch')]
```

**Impact:** Using only pattern `"F"` retrieves only 5% of FortiSwitches!

#### FortiAP - Single Pattern

```
Pattern: "F"
Examples: FP221E5519055049, FP231GTF25002845, FP433FTF23013157
All models: FortiAP 221E, 223E, 231F, 231G, 233G, 234G, 431F, 432G, 433F, etc.
```

#### FortiGate/FortiWiFi - Single Pattern

```
Pattern: "F"
Examples: FGT60FTK12345678, FG100FTK19012345, FW40F3G19000123
All models: FortiGate 30E through 600E, FortiGate VM, FortiWiFi 40F, etc.
```

### Implementation

```python
def get_devices(account_id, serial_patterns):
    """Retrieve devices using multiple patterns if needed."""
    all_devices = []
    seen_serials = set()
    
    for pattern in serial_patterns:
        payload = {
            'serialNumber': pattern,
            'accountId': account_id
        }
        response = api.post('/products/list', json=payload)
        assets = response.json().get('assets', [])
        
        # Deduplicate
        for asset in assets:
            serial = asset['serialNumber']
            if serial not in seen_serials:
                seen_serials.add(serial)
                all_devices.append(asset)
    
    return all_devices
```

---

## Data Models

### Device/Asset Object

```python
{
    "serialNumber": str,
    "productModel": str,
    "description": str,
    "accountId": int,
    "status": str,  # "Registered", "Pending"
    "isDecommissioned": bool,
    "registrationDate": str,  # ISO 8601
    "folderId": int,
    "folderPath": str,
    "productModelEoR": str | null,  # End of Repair
    "productModelEoS": str | null,  # End of Support
    "entitlements": List[Entitlement],
    "contracts": List[Contract],
    "assetGroups": List[str]
}
```

### Entitlement Object

```python
{
    "level": int,
    "levelDesc": str,  # "Premium", "Advanced HW", "Web/Online"
    "type": int,
    "typeDesc": str,  # "Hardware", "Firmware & General Updates", "Technical Support"
    "startDate": str,  # ISO 8601
    "endDate": str     # ISO 8601
}
```

### Contract Object

```python
{
    "contractNumber": str,
    "sku": str,
    "terms": List[{
        "endDate": str,
        "startDate": str,
        "supportType": str
    }]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Check `status` field in JSON |
| 401 | Unauthorized | Re-authenticate (token expired) |
| 403 | Forbidden | Check API user permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Too Many Requests | Implement backoff (wait 60s) |

### JSON Status Field

| status | Meaning | Example |
|--------|---------|---------|
| 0 | Success | Data retrieved successfully |
| -1 | Error | Check `message` and `error` fields |

### Common Errors

**"Both serialNumber and expireBefore cannot be empty"**
- Cause: Missing search parameters
- Solution: Provide `serialNumber` pattern

**"Request should include a positive number for accountId"**
- Cause: Missing or invalid accountId
- Solution: Include valid `accountId` in request body
- **Note:** API user must have **Organization scope**

**"parentId or accountId is required"**
- Cause: Accounts list request without filter
- Solution: Provide `parentId` when listing accounts

### Null/Empty Handling

```python
# assets can be null
assets = data.get('assets')
if assets is None:
    assets = []
```

---

## Best Practices

### 1. Token Management
- Reuse tokens across requests (valid for 61 minutes)
- One token per service (organization, iam, assetmanagement)
- Use session objects for connection pooling

### 2. Account Discovery
- Run once per execution (accounts change rarely)
- Cache results if running multiple scripts
- Query all OUs to ensure complete coverage

### 3. Multi-Pattern Queries
- **Always use ["F", "S"] for FortiSwitch**
- Use ["F"] for FortiAP and FortiGate
- Deduplicate by serial number

### 4. Data Processing
- Filter by `productModel` after retrieval
- Handle null/missing fields gracefully
- Include decommissioned devices for complete inventory

### 5. Error Recovery
- Retry on network errors (3 attempts with backoff)
- Don't retry on 4xx errors (fix request instead)
- Continue processing other accounts on failure

---

## Production Statistics

### Real-World Data (September 2025)

**Organization Structure:**
- 1 main organization
- 16 customer OUs
- 17 total accounts

**Device Inventory:**
- **FortiGate/WiFi:** 133 devices (23 models)
- **FortiSwitch:** 359 devices (29 models)
- **FortiAP:** 520 devices (10 models)
- **Total:** 1012 unique devices

**Decommissioned Devices:**
- FortiGate: 8 (6%)
- FortiSwitch: 17 (5%)
- FortiAP: 38 (7%)

**Performance:**
- Authentication: ~3 seconds (3 tokens)
- Account Discovery: ~5-10 seconds (17 accounts, 16 OUs)
- Device Retrieval: ~50-75 seconds (34 FortiSwitch queries: 17 accounts × 2 patterns)
- **Total Runtime:** ~60-90 seconds for complete export

**API Calls Per Export:**
- FortiSwitch: 34 calls (17 accounts × 2 patterns)
- FortiAP: 17 calls (17 accounts × 1 pattern)
- FortiGate: 17 calls (17 accounts × 1 pattern)

---

## Validation Results

### Correlation with GUI Export

Compared API retrieval against FortiCloud Portal GUI export:

| Device Type | GUI Export | API Retrieval | Delta | Notes |
|-------------|-----------|---------------|-------|-------|
| FortiSwitch | 342 | 359 | +17 | Decommissioned devices |
| FortiAP | 482 | 520 | +38 | Decommissioned devices |
| FortiGate/WiFi | 125 | 133 | +8 | Decommissioned devices |

**Result:** ✅ **100% match** - All GUI devices found by API, plus decommissioned devices

**Conclusion:** API provides MORE complete data than GUI export.

---

## Quick Reference

### Complete Workflow

```python
# 1. Authenticate with Organization API
org_token = authenticate(username, password, "organization")

# 2. Get all OUs
org_data = post("/ES/api/organization/v1/units/list", token=org_token, json={})
org_id = org_data['organizationUnits']['orgId']
ou_list = org_data['organizationUnits']['orgUnits']

# 3. Build OU mapping
ou_map = {ou['id']: ou['name'] for ou in ou_list}
ou_map[org_id] = "Main Organization"

# 4. Authenticate with IAM API
iam_token = authenticate(username, password, "iam")

# 5. Get all accounts
all_accounts = []
for ou_id in [org_id] + [ou['id'] for ou in ou_list]:
    response = post("/ES/api/iam/v1/accounts/list",
                   token=iam_token,
                   json={'parentId': ou_id})
    all_accounts.extend(response.get('accounts', []))

# 6. Build account metadata
account_metadata = {}
for account in all_accounts:
    account_metadata[account['id']] = {
        'company': account.get('company'),
        'ou_name': ou_map.get(account['parentId'])
    }

# 7. Authenticate with Asset Management API
asset_token = authenticate(username, password, "assetmanagement")

# 8. Get devices for FortiSwitch (requires both patterns!)
all_devices = []
for account_id in account_ids:
    for pattern in ['F', 'S']:
        response = post("/ES/api/registration/v3/products/list",
                       token=asset_token,
                       json={'serialNumber': pattern, 'accountId': account_id})
        all_devices.extend(response.get('assets', []))

# 9. Deduplicate and filter
unique_devices = deduplicate_by_serial(all_devices)
fortiswitches = [d for d in unique_devices 
                 if d['productModel'].startswith('FortiSwitch')]

# 10. Enhance with metadata and export
for device in fortiswitches:
    account_id = device['accountId']
    device['company'] = account_metadata[account_id]['company']
    device['ou_name'] = account_metadata[account_id]['ou_name']

export_to_csv(fortiswitches)
```

---

## References

### Official Documentation
- [FortiCloud IAM Documentation](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/)
- [API Users Guide](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/927656/api-users)
- [OAuth 2.0 Password Grant](https://oauth.net/2/grant-types/password/)

### API Specifications
Located in `apireference/` directory:
- Asset Management V3 Product.json
- Organization V1 Units.json
- IAM V1 Accounts.json

---

**Document Version:** 3.0  
**Last Updated:** September 30, 2025  
**Validated Against:** Production API with 1000+ devices across 17 accounts