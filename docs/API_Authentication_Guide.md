# FortiCloud API Authentication Guide

## Overview

To access FortiCloud APIs (Organization, IAM, and Asset Management), you need an OAuth token obtained through the FortiAuthenticator API.

## API Base URLs

| API | Base URL |
|-----|----------|
| **Asset Management V3** | `https://support.fortinet.com/ES/api/registration/v3/` |
| **Organization V1** | `https://support.fortinet.com/ES/api/organization/v1/` |
| **IAM V1** | `https://support.fortinet.com/ES/api/iam/v1/` |
| **Authentication** | `https://customerapiauth.fortinet.com/api/v1/oauth/token/` |

## Authentication Process

### Step 1: Create an API User

1. Log into FortiCloud portal: https://support.fortinet.com
2. Navigate to **IAM** (Identity & Access Management)
3. Follow the instructions in [Adding an API user](http://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/927656/api-users)
4. **Important:** The API user should be given:
   - Access to Organization and/or IAM portal by permission profile
   - **Organization scope type** for some functionalities (recommended for accessing multiple accounts)
5. Download the credential file - it contains:
   - `apiId` (your username)
   - `password` (your password)
   - Multiple `clientId` values for different services

### Step 2: Understand Client IDs

Different FortiCloud services require different `client_id` values during authentication:

| Service | Client ID | Use Case |
|---------|-----------|----------|
| Asset Management | `assetmanagement` | Retrieve devices, contracts, licenses |
| IAM | `iam` | Manage accounts, users, permissions |
| Organization | `organization` | Manage organizational units (OUs) |
| FortiGate Cloud | `fortigatecloud` | FortiGate-specific cloud features |
| FortiManager Cloud | `FortiManager` | FortiManager cloud management |
| FortiFlex | `flexvm` | License/FlexVM management |

**Note:** Use the appropriate `client_id` based on which API you're calling.

### Step 3: Obtain OAuth Token

Send a POST request to the authentication endpoint:

**Endpoint:** `https://customerapiauth.fortinet.com/api/v1/oauth/token/`

**Method:** POST

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "YOUR_API_ID",
  "password": "YOUR_PASSWORD",
  "client_id": "assetmanagement",
  "grant_type": "password"
}
```

**Response:**
```json
{
  "access_token": "jVSjRMx5hpw5ZfASk8Hjo16X",
  "expires_in": 3660,
  "token_type": "Bearer",
  "scope": "read write",
  "refresh_token": "...",
  "message": "successfully authenticated",
  "status": "success"
}
```

**Python Example:**
```python
import requests

auth_payload = {
    "username": "509B0E64-6867-4FB8-B5D7-F4CF0FA3475E",
    "password": "your_password_here",
    "client_id": "assetmanagement",
    "grant_type": "password"
}

response = requests.post(
    "https://customerapiauth.fortinet.com/api/v1/oauth/token/",
    json=auth_payload
)

token = response.json()['access_token']
```

### Step 4: Use Token in API Requests

Include the OAuth token in the Authorization header with the Bearer scheme:

**Header:**
```
Authorization: Bearer jVSjRMx5hpw5ZfASk8Hjo16X
```

**Example Request:**
```python
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://support.fortinet.com/ES/api/registration/v3/products/list',
    headers=headers,
    json={'serialNumber': 'F', 'status': 'Registered', 'accountId': 883938}
)
```

## Token Management

- **Expiration:** Tokens typically expire after **3660 seconds** (~61 minutes)
- **Refresh:** Use the `refresh_token` to obtain a new access token without re-authenticating
- **Best Practice:** Store tokens securely and refresh before expiration

## API User Scope Types

### Local Scope
- Access to a single account
- `accountId` parameter is optional in API requests

### Organization Scope (Recommended)
- Access to multiple accounts across organizational units
- `accountId` parameter is **mandatory** in most API requests
- Allows querying across all accessible accounts

## Getting Account IDs

For Organization-scope API users, you need to specify which account(s) to query:

### Method 1: Use the Discovery Script
```bash
python scripts/get_all_account_ids.py
```

This script will:
1. Authenticate with Organization API
2. Get all organizational units (OUs)
3. Authenticate with IAM API
4. Query accounts from each OU
5. Display all accessible account IDs

### Method 2: Manual Discovery

**Step 1:** Get OUs
```python
# Authenticate with "organization" client_id
org_token = authenticate(username, password, "organization", auth_url)

# Get organizational units
response = requests.post(
    "https://support.fortinet.com/ES/api/organization/v1/units/list",
    headers={'Authorization': f'Bearer {org_token}'},
    json={}
)
```

**Step 2:** Get Accounts
```python
# Authenticate with "iam" client_id
iam_token = authenticate(username, password, "iam", auth_url)

# Get accounts for each OU
for ou_id in ou_ids:
    response = requests.post(
        "https://support.fortinet.com/ES/api/iam/v1/accounts/list",
        headers={'Authorization': f'Bearer {iam_token}'},
        json={'parentId': ou_id}
    )
```

## Common Response Format

All FortiCloud APIs use a consistent response format:

```json
{
  "status": 0,
  "message": "Request processed successfully",
  "error": null,
  "version": "3.0",
  "build": "1.0.0",
  "token": "...",
  "data": { ... }
}
```

- **status: 0** = Success
- **status: -1** = Error (check `message` and `error` fields)

## Error Handling

Common error scenarios:

| Status Code | Meaning | Solution |
|-------------|---------|----------|
| 401 | Unauthorized | Token expired or invalid - re-authenticate |
| 400 | Bad Request | Check required parameters (e.g., accountId) |
| 403 | Forbidden | API user lacks permissions |
| 404 | Not Found | Incorrect endpoint URL |
| 429 | Too Many Requests | Rate limit exceeded - implement backoff |

## Security Best Practices

1. **Never commit credentials** to version control
2. Use environment variables (`.env` files)
3. Rotate API credentials regularly (every 90 days)
4. Use separate API users for different purposes
5. Monitor API usage in FortiCloud IAM portal
6. Implement token refresh logic
7. Use HTTPS for all API calls (enforced by FortiCloud)

## References

- [FortiCloud IAM Documentation](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/)
- [FortiAuthenticator REST API Guide](http://docs.fortinet.com/document/fortiauthenticator/6.1.2/rest-api-solution-guide/498666/oauth-server-token-oauth-token)
- [Adding an API User](http://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/927656/api-users)

---

*Last Updated: September 30, 2025*
