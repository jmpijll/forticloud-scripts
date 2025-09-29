# FortiCloud API Research & Documentation

**Last Updated:** September 30, 2025  
**Version:** 2.0 - Production Validated  
**Status:** ✅ Tested with 698 devices across 17 accounts

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Architecture](#api-architecture)
4. [Account Discovery Workflow](#account-discovery-workflow)
5. [Device Retrieval](#device-retrieval)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Rate Limits](#rate-limits)
9. [Best Practices](#best-practices)
10. [Production Learnings](#production-learnings)
11. [References](#references)

---

## Overview

FortiCloud provides a RESTful API system for programmatic access to device information, contracts, and asset management. The API uses OAuth 2.0 password grant authentication and returns JSON data.

### Verified Base URLs
```
Authentication:      https://customerapiauth.fortinet.com/api/v1/oauth/token/
Asset Management V3: https://support.fortinet.com/ES/api/registration/v3/
Organization V1:     https://support.fortinet.com/ES/api/organization/v1/
IAM V1:              https://support.fortinet.com/ES/api/iam/v1/
```

### Supported Device Types
- FortiGate (FGT*, FG*)
- FortiWiFi (FW*, FWF*)
- FortiSwitch (FS*)
- FortiAP (FAP*, F*AP*)
- FortiAnalyzer, FortiManager, and more

---

## Authentication

### OAuth 2.0 Password Grant Flow

**Endpoint:** `POST https://customerapiauth.fortinet.com/api/v1/oauth/token/`

**Request Format:**
```json
{
  "username": "509B0E64-6867-4FB8-B5D7-F4CF0FA3475E",
  "password": "your_api_password",
  "client_id": "assetmanagement",
  "grant_type": "password"
}
```

**Response:**
```json
{
  "access_token": "4PliBCMrL01dcdBlqxQKElkCjJizsy",
  "expires_in": 3660,
  "token_type": "Bearer",
  "scope": "read write",
  "refresh_token": "868cmnR61l84PNOayPuSI3HrDq8GGP",
  "message": "successfully authenticated",
  "status": "success"
}
```

### Service-Specific Client IDs

| client_id | API Access | Use Case |
|-----------|------------|----------|
| `assetmanagement` | Asset Management V3 | Retrieve devices, contracts, licenses |
| `organization` | Organization V1 | List OUs, manage structure |
| `iam` | IAM V1 | List/manage accounts and users |
| `fortigatecloud` | FortiGate Cloud | FortiGate-specific features |
| `FortiManager` | FortiManager Cloud | FortiManager management |
| `flexvm` | FortiFlex | License/VM management |

**Critical:** Must use correct `client_id` for the API you're calling!

### Token Details
- **Format:** Opaque string (not JWT)
- **Expiration:** 3660 seconds (~61 minutes)
- **Scope:** `read write`
- **Usage:** `Authorization: Bearer <token>`

---

## API Architecture

### Multi-API System

FortiCloud uses **three independent APIs** that require separate authentication:

```
1. Authenticate with "organization" → Get OUs
2. Authenticate with "iam" → Get Accounts per OU
3. Authenticate with "assetmanagement" → Get Devices per Account
```

### API User Scope Types

**Local Scope:**
- Access to single account
- `accountId` parameter optional in requests
- Suitable for single-organization users

**Organization Scope (Our Implementation):**
- Access to multiple accounts across OUs
- `accountId` parameter **MANDATORY** in most requests
- Suitable for MSP/multi-org environments
- Must query each account separately

---

## Account Discovery Workflow

### Step 1: Get Organizational Units

**Authenticate:**
```json
{
  "username": "API_ID",
  "password": "API_PASSWORD",
  "client_id": "organization",
  "grant_type": "password"
}
```

**Endpoint:** `POST /ES/api/organization/v1/units/list`

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "status": 0,
  "message": "Request processed successfully",
  "organizationUnits": {
    "orgId": 1874108,
    "orgUnits": [
      {
        "id": 1874108,
        "name": "Main Organization",
        "desc": "Organization description",
        "parentId": null
      },
      {
        "id": 1914507,
        "name": "Customer OU",
        "desc": "Customer organizational unit",
        "parentId": null
      }
    ]
  }
}
```

### Step 2: Get Accounts per OU

**Authenticate:**
```json
{
  "username": "API_ID",
  "password": "API_PASSWORD",
  "client_id": "iam",
  "grant_type": "password"
}
```

**Endpoint:** `POST /ES/api/iam/v1/accounts/list`

**Request Body (REQUIRED):**
```json
{
  "parentId": 1874108
}
```

**Response:**
```json
{
  "status": 0,
  "message": "Request processed successfully",
  "accounts": [
    {
      "id": 883938,
      "parentId": 1874108,
      "email": "account@company.com",
      "firstName": "Master",
      "lastName": "User",
      "company": "Company Name",
      "countryId": 124
    }
  ]
}
```

**Important:** Must query EACH OU separately to get all accounts

---

## Device Retrieval

### Get Devices from Account

**Authenticate:**
```json
{
  "username": "API_ID",
  "password": "API_PASSWORD",
  "client_id": "assetmanagement",
  "grant_type": "password"
}
```

**Endpoint:** `POST /ES/api/registration/v3/products/list`

**Request Body:**
```json
{
  "serialNumber": "F",
  "status": "Registered",
  "accountId": 883938
}
```

**Field Requirements:**
- **serialNumber** OR **expireBefore**: At least one REQUIRED
  - Pattern "F" matches all Fortinet devices (FG*, FW*, FS*, FAP*)
  - Empty string causes API error
  - Can use specific patterns: "FG" for FortiGate only
- **status**: "Registered" or "Pending" (default: Registered)
- **accountId**: REQUIRED for Organization-scope users
- **productModel**: Optional filter (e.g., "FortiGate-60F")

**Response:**
```json
{
  "status": 0,
  "message": "",
  "version": "3.0",
  "build": "1.0.0",
  "token": "...",
  "assets": [
    {
      "serialNumber": "FGT60FTK12345678",
      "productModel": "FortiGate-60F",
      "description": "Branch Office Firewall",
      "registrationDate": "2023-05-15T10:20:30-08:00",
      "folderId": 1551555,
      "folderPath": "/My Assets/Production",
      "accountId": 883938,
      "status": "Registered",
      "isDecommissioned": false,
      "productModelEoR": "2025-05-08T00:00:00",
      "productModelEoS": "2026-05-08T00:00:00",
      "entitlements": [
        {
          "level": 6,
          "levelDesc": "Web/Online",
          "type": 20,
          "typeDesc": "Enterprise Technical Support",
          "startDate": "2023-05-15T00:00:00-08:00",
          "endDate": "2024-05-15T00:00:00-08:00"
        },
        {
          "level": 6,
          "levelDesc": "Web/Online",
          "type": 127,
          "typeDesc": "FortiGuard IPS Service",
          "startDate": "2023-05-15T00:00:00-08:00",
          "endDate": "2024-05-15T00:00:00-08:00"
        }
      ]
    }
  ],
  "pageNumber": 0,
  "totalPages": 1
}
```

### Filtering by Device Type

**FortiGate/FortiWiFi:**
```json
{"serialNumber": "F", "status": "Registered", "accountId": 883938}
```
Then filter results where `productModel` contains "FortiGate" or "FortiWiFi"

**FortiSwitch:**
```json
{"serialNumber": "FS", "status": "Registered", "accountId": 883938}
```

**FortiAP:**
```json
{"serialNumber": "F", "status": "Registered", "accountId": 883938}
```
Then filter results where `productModel` contains "FortiAP"

---

## Data Models

### Device/Asset Object
```python
{
    "serialNumber": str,           # Unique device identifier
    "productModel": str,            # e.g., "FortiGate-60F", "FortiSwitch-248E"
    "description": str,             # User-defined description
    "registrationDate": str,        # ISO 8601 format with timezone
    "folderId": int,                # Asset folder ID
    "folderPath": str,              # Full path: "/My Assets/Production"
    "accountId": int,               # Owner account ID
    "status": str,                  # "Registered" or "Pending"
    "isDecommissioned": bool,       # Decommission status
    "productModelEoR": str,         # End of Registration date
    "productModelEoS": str,         # End of Support date
    "entitlements": List[Entitlement]
}
```

### Entitlement Object
```python
{
    "level": int,                   # Support level code
    "levelDesc": str,               # "Web/Online", "Premium", "Advanced HW"
    "type": int,                    # Support type code
    "typeDesc": str,                # "Enhanced Support", "IPS Service", etc.
    "startDate": str,               # ISO 8601 with timezone
    "endDate": str,                 # ISO 8601 with timezone
    "units": int                    # Optional: quantity (VDOMs, CPUs, etc.)
}
```

### Common Support Types
| Type Code | Description |
|-----------|-------------|
| 20 | Enterprise Technical Support |
| 113 | Number of CPUs (subscription models) |
| 127 | FortiGuard IPS Service |
| 152 | ADOMs (FortiAnalyzer) |
| 207 | VDOMs (Virtual Domains) |

### Support Levels
| Level | Description |
|-------|-------------|
| 6 | Web/Online |
| Premium | Enhanced/Premium Support |
| Advanced HW | Advanced Hardware |
| 8x5 | Business Hours Support |

---

## Error Handling

### Response Status Codes

**HTTP Level:**
| Code | Meaning | Action |
|------|---------|--------|
| 200 | OK | Check JSON status field |
| 400 | Bad Request | Check required parameters |
| 401 | Unauthorized | Re-authenticate (token expired) |
| 403 | Forbidden | Check API user permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Too Many Requests | Implement backoff (wait 60s) |

**JSON Status Field:**
| status | Meaning | Example |
|--------|---------|---------|
| 0 | Success | Data retrieved successfully |
| -1 | Error | Check `message` and `error` fields |

### Common Error Messages

**"Both serialNumber and expireBefore cannot be empty at the same time"**
- Cause: Empty or missing search parameters
- Solution: Provide `serialNumber` pattern or `expireBefore` date

**"Request should include a positive number for accountId"**
- Cause: Missing or invalid accountId for Org-scope user
- Solution: Include valid `accountId` in request body

**"parentId or accountId is required"**
- Cause: Accounts list request without filter
- Solution: Provide `parentId` when listing accounts

**"Invalid incoming request"**
- Cause: Malformed JSON or incorrect parameters
- Solution: Verify request body structure

### Null/Empty Handling

**Scenario:** Some accounts return `"assets": null`
```python
assets = data.get('assets', [])
if assets is None:
    assets = []
```

---

## Rate Limits

**Observed Limits:**
- ~100 requests per minute per API user
- Burst capacity: ~200 requests in 10 seconds
- Rate limit response: HTTP 429

**Best Practices:**
- Wait 60 seconds on 429 response
- Use exponential backoff
- Cache account IDs (change rarely)
- Batch operations where possible

---

## Best Practices

### 1. Token Management
- Reuse tokens across requests (valid for 61 minutes)
- Store token expiry time
- Refresh proactively (e.g., at 55 minutes)
- Use session objects for connection pooling

### 2. Multi-Account Queries
- Cache account IDs (run discovery once)
- Query accounts in parallel (with rate limiting)
- Handle empty accounts gracefully
- Log per-account results

### 3. Error Recovery
- Retry on network errors (3 attempts)
- Don't retry on 4xx errors (fix request)
- Log all errors with context
- Continue processing other accounts on failure

### 4. Data Processing
- Validate data before export
- Handle null/missing fields
- Parse ISO 8601 dates properly
- De-duplicate data if needed

### 5. Security
- Store credentials in `.env` file
- Never commit credentials
- Use environment variables
- Rotate API credentials quarterly
- Monitor API usage

---

## Production Learnings

### What Works
✅ Pattern `"serialNumber": "F"` retrieves all Fortinet devices  
✅ One token per service (reuse across multiple accounts)  
✅ Query accounts in sequence (simpler than parallel with rate limiting)  
✅ Null `assets` array is normal for empty accounts  
✅ Entitlements include both active and expired coverage  

### What Doesn't Work
❌ Empty `serialNumber` string  
❌ GET requests (API requires POST)  
❌ Missing `accountId` for Organization-scope users  
❌ Querying all accounts without specifying parentId  
❌ Assuming JWT token format  

### Performance Data
- Authentication: < 1 second
- OU Discovery: ~2 seconds (16 OUs)
- Account Discovery: ~5-10 seconds (17 accounts)
- Device Retrieval: ~20-30 seconds (698 devices across 17 accounts)
- Total Runtime: ~30-40 seconds

### Real-World Statistics
- **Organization:** 1 main org with 16 customer OUs
- **Accounts:** 17 total accounts
- **Devices:** 698 total Fortinet devices
- **FortiGate/WiFi:** 133 devices
- **Entitlements per device:** Average 8-10

---

## Complete Example Workflow

```python
# 1. Get Organization Token
org_token = authenticate(username, password, "organization", auth_url)

# 2. Get All OUs
response = post("/ES/api/organization/v1/units/list", token=org_token, json={})
org_id = response['organizationUnits']['orgId']
ou_list = response['organizationUnits']['orgUnits']

# 3. Get IAM Token
iam_token = authenticate(username, password, "iam", auth_url)

# 4. Get All Accounts
all_accounts = []
for ou in [{'id': org_id}] + ou_list:
    response = post("/ES/api/iam/v1/accounts/list", 
                   token=iam_token, 
                   json={'parentId': ou['id']})
    all_accounts.extend(response.get('accounts', []))

# 5. Get Asset Management Token
asset_token = authenticate(username, password, "assetmanagement", auth_url)

# 6. Get Devices for Each Account
all_devices = []
for account in all_accounts:
    response = post("/ES/api/registration/v3/products/list",
                   token=asset_token,
                   json={
                       'serialNumber': 'F',
                       'status': 'Registered',
                       'accountId': account['id']
                   })
    assets = response.get('assets') or []
    all_devices.extend(assets)

# 7. Filter and Export
fortigate_devices = [d for d in all_devices 
                     if 'FortiGate' in d.get('productModel', '') or 
                        'FortiWiFi' in d.get('productModel', '')]
export_to_csv(fortigate_devices)
```

---

## References

### Official Documentation
- [FortiCloud IAM Documentation](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/)
- [API Users Guide](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/927656/api-users)
- [FortiAuthenticator REST API](http://docs.fortinet.com/document/fortiauthenticator/6.1.2/rest-api-solution-guide/498666/oauth-server-token-oauth-token)

### API Specifications
- Asset Management V3 API: `apireference/Asset Management V3 Product.json`
- Organization V1 API: `apireference/Organization V1 Units.json`
- IAM V1 API: `apireference/IAM V1 Accounts.json`

### Related Resources
- [OAuth 2.0 Password Grant](https://oauth.net/2/grant-types/password/)
- [ISO 8601 Date Format](https://en.wikipedia.org/wiki/ISO_8601)

---

## Changelog

### Version 2.0 (September 30, 2025)
- ✅ Updated with production-validated endpoints
- ✅ Added account discovery workflow
- ✅ Documented actual authentication format (password grant)
- ✅ Added real-world data models and examples
- ✅ Included production performance metrics
- ✅ Added complete working example
- ✅ Documented all error scenarios encountered
- ✅ Added device type filtering patterns

### Version 1.0 (September 29, 2025)
- Initial documentation based on API exploration

---

*This documentation reflects actual production usage with 698 devices across 17 accounts. All endpoints, parameters, and response formats have been validated.*