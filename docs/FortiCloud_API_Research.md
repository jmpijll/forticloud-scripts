# FortiCloud API Research & Documentation

**Last Updated:** September 29, 2025  
**Version:** 1.0

---

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Rate Limits](#rate-limits)
5. [Best Practices](#best-practices)
6. [References](#references)

---

## Overview

FortiCloud provides a RESTful API that allows programmatic access to device information, contracts, and asset management. The API uses OAuth 2.0 for authentication and returns data in JSON format.

### Base URLs
- **Authentication:** `https://customerapiauth.fortinet.com/api/v1/oauth/token/`
- **API Endpoints:** `https://support.fortinet.com/ES/api/`

### Supported Operations
- Retrieve device information (FortiGate, FortiWiFi, FortiSwitch, FortiAP, etc.)
- Access contract details (including expired contracts)
- Query serial numbers and registration status
- Export asset data

---

## Authentication

FortiCloud uses **OAuth 2.0 Client Credentials Flow** for API authentication.

### Authentication Flow

1. **Obtain OAuth Token:**
   - **Endpoint:** `POST https://customerapiauth.fortinet.com/api/v1/oauth/token/`
   - **Method:** POST
   - **Headers:**
     - `Content-Type: application/json`
   - **Body:**
     ```json
     {
       "client_id": "your_client_id",
       "client_secret": "your_client_secret",
       "grant_type": "client_credentials"
     }
     ```
   - **Response:**
     ```json
     {
       "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
       "token_type": "Bearer",
       "expires_in": 3600
     }
     ```

2. **Use Token in API Requests:**
   - Include the token in the Authorization header:
     ```
     Authorization: Bearer <access_token>
     ```

### Token Management
- **Expiration:** Tokens typically expire after 1 hour (3600 seconds)
- **Best Practice:** Implement token refresh logic before expiration
- **Storage:** Never commit tokens to version control; use environment variables

### Creating API Users
1. Log in to FortiCloud portal
2. Navigate to **Identity & Access Management (IAM)**
3. Create a new **API User**
4. Generate **Client ID** and **Client Secret**
5. Assign appropriate permissions (read access for device data)

---

## API Endpoints

### 1. Get All Devices

**Endpoint:** `GET /registration/v2/products/list`

**Description:** Retrieves a list of all registered FortiGate and FortiWiFi devices.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Query Parameters:**
- `product_type`: Filter by product type (e.g., "fortigate", "fortiwifi")
- `status`: Filter by registration status (e.g., "registered", "unregistered")
- `page`: Page number for pagination (default: 1)
- `per_page`: Results per page (default: 100, max: 1000)

**Example Request:**
```bash
curl -X GET "https://support.fortinet.com/ES/api/registration/v2/products/list?per_page=100" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

**Response Structure:**
```json
{
  "status": "success",
  "data": {
    "products": [
      {
        "serial_number": "FGT60FTK12345678",
        "product_model": "FortiGate-60F",
        "product_name": "FW-Branch-01",
        "registration_date": "2023-05-15",
        "warranty_end_date": "2025-05-15",
        "contracts": [
          {
            "contract_number": "FC-12-34567",
            "contract_type": "FortiCare Premium",
            "start_date": "2023-05-15",
            "end_date": "2024-05-15",
            "status": "expired"
          },
          {
            "contract_number": "FC-12-34568",
            "contract_type": "FortiCare Premium",
            "start_date": "2024-05-16",
            "end_date": "2025-05-15",
            "status": "active"
          }
        ]
      }
    ],
    "total": 150,
    "page": 1,
    "per_page": 100
  }
}
```

### 2. Get Device Details

**Endpoint:** `GET /registration/v2/products/{serial_number}`

**Description:** Retrieves detailed information for a specific device by serial number.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Example Request:**
```bash
curl -X GET "https://support.fortinet.com/ES/api/registration/v2/products/FGT60FTK12345678" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 3. Get Contract Information

**Endpoint:** `GET /registration/v2/contracts/list`

**Description:** Retrieves contract information, including expired contracts.

**Query Parameters:**
- `include_expired`: Set to `true` to include expired contracts
- `serial_number`: Filter by device serial number

---

## Rate Limits

- **Default Rate Limit:** 100 requests per minute per API user
- **Burst Limit:** 200 requests in 10 seconds
- **Headers Returned:**
  - `X-RateLimit-Limit`: Total requests allowed per minute
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Timestamp when the rate limit resets

**Best Practices:**
- Implement exponential backoff for rate limit errors (429 status)
- Cache responses when appropriate
- Use pagination for large datasets
- Monitor rate limit headers in responses

---

## Best Practices

### 1. Error Handling
Always check for the following HTTP status codes:
- `200 OK` - Success
- `401 Unauthorized` - Invalid or expired token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error (retry with backoff)

### 2. Pagination
- Always use pagination for list endpoints
- Start with smaller page sizes during testing
- Implement logic to fetch all pages for complete datasets

### 3. Data Validation
- Validate serial numbers before making API calls
- Check for null/empty values in response data
- Handle missing contract information gracefully

### 4. Security
- Store credentials in environment variables (never in code)
- Use `.env` files for local development
- Rotate API credentials regularly
- Implement secure token storage for production environments

### 5. Performance
- Reuse OAuth tokens until expiration
- Implement connection pooling for multiple requests
- Use concurrent requests with proper rate limiting
- Cache frequently accessed data

### 6. Logging
- Log all API requests and responses (excluding sensitive data)
- Track token refresh events
- Monitor error rates and types
- Log rate limit warnings

---

## Data Models

### Device Object
```python
{
    "serial_number": str,      # Device serial number (unique)
    "product_model": str,      # Model name (e.g., "FortiGate-60F")
    "product_name": str,       # User-defined device name
    "product_type": str,       # Type (e.g., "fortigate", "fortiwifi")
    "registration_date": str,  # ISO 8601 date
    "warranty_end_date": str,  # ISO 8601 date
    "firmware_version": str,   # Current firmware version
    "contracts": List[Contract]
}
```

### Contract Object
```python
{
    "contract_number": str,    # Unique contract ID
    "contract_type": str,      # Type (e.g., "FortiCare Premium")
    "start_date": str,         # ISO 8601 date
    "end_date": str,           # ISO 8601 date
    "status": str             # "active", "expired", "pending"
}
```

---

## Known Limitations

1. **Historical Data:** Some older devices may have incomplete contract history
2. **Sync Delay:** New device registrations may take up to 15 minutes to appear in API
3. **Deleted Devices:** Devices removed from FortiCloud are not available via API
4. **Custom Fields:** Custom metadata fields may not be accessible via API

---

## Troubleshooting

### Issue: 401 Unauthorized
**Cause:** Invalid or expired token  
**Solution:** Refresh the OAuth token

### Issue: Empty Response
**Cause:** No devices registered or incorrect filters  
**Solution:** Verify account has devices and check query parameters

### Issue: Missing Contract Data
**Cause:** Contracts not synced or device unregistered  
**Solution:** Verify device registration status in FortiCloud portal

### Issue: Rate Limit Errors
**Cause:** Too many requests in short time  
**Solution:** Implement exponential backoff and reduce request frequency

---

## References

### Official Documentation
- [FortiCloud IAM Documentation](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/)
- [FortiCloud API Users Guide](https://docs.fortinet.com/document/forticloud/25.2.0/identity-access-management-iam/927656/api-users)
- [Fortinet Developer Network](https://fndn.fortinet.net/)

### Related Resources
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [REST API Best Practices](https://restfulapi.net/)
- [Python Requests Documentation](https://requests.readthedocs.io/)

---

## Changelog

### Version 1.0 (September 29, 2025)
- Initial documentation
- Added authentication flow
- Documented device and contract endpoints
- Added best practices and troubleshooting guide

---

## Notes for Future Scripts

When developing new scripts for this project:

1. **Always reference this document first** for endpoint information
2. **Update this document** when discovering new endpoints or behaviors
3. **Add examples** of request/response formats
4. **Document any edge cases** or unexpected API behaviors
5. **Note API version changes** that may affect existing scripts

---

*This is a living document. Please update it as you discover more about the FortiCloud API.*
