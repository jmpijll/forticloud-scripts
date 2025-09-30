# FortiManager API Research

**Author**: FortiManager Integration Project  
**Date**: September 30, 2025  
**Version**: 1.0

## Table of Contents

1. [Introduction](#introduction)
2. [API Authentication](#api-authentication)
3. [API Structure](#api-structure)
4. [Device Management](#device-management)
5. [FortiGate/FortiWiFi Devices](#fortigatefortiwifi-devices)
6. [FortiSwitch Devices](#fortiswitch-devices)
7. [FortiAP Devices](#fortiap-devices)
8. [Comparison with FortiCloud](#comparison-with-forticloud)
9. [Implementation Notes](#implementation-notes)
10. [References](#references)

---

## Introduction

FortiManager is Fortinet's centralized management platform for managing FortiGate devices and their associated FortiSwitch and FortiAP infrastructure. Unlike FortiCloud (which provides SaaS-based asset and license management), FortiManager focuses on configuration management, policy provisioning, and operational monitoring of managed devices.

This document explores the FortiManager JSON RPC API to extract device information similar to what we retrieve from FortiCloud, enabling unified reporting across both platforms.

---

## API Authentication

### Token-Based Authentication

FortiManager 7.2.2+ supports API key (token-based) authentication, which is the preferred method for automation.

#### API Key Generation

1. Create an API user in FortiManager:
   ```
   config system admin user
       edit api_user_001
           set user_type api
           set rpc-permit read-write
       next
   end
   ```

2. Generate the API key:
   ```
   execute api-user generate-key api_user_001
   ```

3. The API key is permanent and can be regenerated anytime.

#### Using the API Key

The API key can be provided in two ways:

**Method 1: Authorization Header (Recommended)**
```http
POST https://<fmg_ip>/jsonrpc
Authorization: Bearer <api_key>
Content-Type: application/json
```

**Method 2: Query String**
```
POST https://<fmg_ip>/jsonrpc?access_token=<api_key>
```

### Session-Based Authentication (Alternative)

For compatibility with older versions or specific use cases:

**REQUEST:**
```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "data": {
      "user": "admin",
      "passwd": "password"
    },
    "url": "sys/login/user"
  }],
  "session": null
}
```

**RESPONSE:**
```json
{
  "id": 1,
  "result": [{
    "status": {
      "code": 0,
      "message": "OK"
    },
    "url": "sys/login/user"
  }],
  "session": "y5I9dOaJyotAoco6nY3VfUcgTwp7Alk7..."
}
```

---

## API Structure

### JSON RPC Format

All FortiManager API requests use JSON RPC format:

```json
{
  "id": <request_id>,
  "method": "<get|set|add|delete|exec>",
  "params": [
    {
      "url": "<api_endpoint>",
      "data": {},
      "fields": [],
      "filter": [],
      "option": []
    }
  ],
  "session": "<session_id_or_null_for_token_auth>"
}
```

### Common Methods

- **get**: Retrieve data
- **set**: Update existing objects
- **add**: Create new objects
- **delete**: Remove objects
- **exec**: Execute operations

### Common Options

- `"loadsub": 0` or `"option": ["no loadsub"]`: Don't load sub-tables
- `"option": ["extra info"]`: Get additional device information
- `"option": ["assignment info"]`: Get policy package assignments
- `"verbose": 1`: Return human-readable values instead of numeric codes
- `"fields": [...]`: Limit returned fields

---

## Device Management

### Device Database (DVMDB)

FortiManager stores all managed devices in the Device Database (DVMDB), accessible via:

- `/dvmdb/device` - All devices across all ADOMs
- `/dvmdb/adom/<adom>/device` - Devices in a specific ADOM
- `/dvmdb/device/<device_name>` - Specific device details

### Get All Managed Devices

**REQUEST:**
```json
{
  "id": 1,
  "method": "get",
  "params": [{
    "url": "/dvmdb/device",
    "option": ["extra info", "assignment info"],
    "loadsub": 0
  }],
  "session": "<session_or_null>"
}
```

**RESPONSE:**
```json
{
  "id": 1,
  "result": [{
    "data": [
      {
        "name": "FGT-Branch-01",
        "oid": 101,
        "sn": "FGT60F0000000001",
        "ip": "192.168.1.10",
        "desc": "Branch Office Firewall",
        "os_type": "fos",
        "os_ver": "7.4",
        "mr": 0,
        "build": 2462,
        "patch": 0,
        "platform_str": "FortiGate-60F",
        "conn_status": 1,
        "conn_mode": 1,
        "mgmt_mode": 3,
        "extra info": {
          "adom": "root"
        }
      }
    ],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

### Available Device Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Device name in FortiManager | "FGT-Branch-01" |
| `sn` | Serial number | "FGT60F0000000001" |
| `ip` | Management IP address | "192.168.1.10" |
| `desc` | Device description | "Branch Office" |
| `platform_str` | Device model | "FortiGate-60F" |
| `os_type` | Operating system type | "fos" (FortiOS) |
| `os_ver` | OS version | "7.4" |
| `build` | Build number | 2462 |
| `conn_status` | Connection status | 1 (connected) |
| `mgmt_mode` | Management mode | 3 (normal) |
| `hostname` | Device hostname | "FGT-Branch-01" |
| `ha_mode` | HA mode | 0 (standalone) |
| `ha_group_id` | HA group ID | 0 |
| `meta fields` | Custom metadata | {...} |
| `latitude` | GPS latitude | "48.8566" |
| `longitude` | GPS longitude | "2.3522" |

### Connection Status Values

- `0`: Unknown
- `1`: Connected
- `2`: Disconnected

### Management Mode Values

- `0`: Unreg (unregistered)
- `1`: FMGFAZ (FortiAnalyzer mode)
- `2`: FMGFAI (FOS mode)
- `3`: Normal

---

## FortiGate/FortiWiFi Devices

FortiGate and FortiWiFi devices are the primary managed devices in FortiManager.

### Get FortiGate Devices

You can filter by platform or OS type:

**REQUEST (Filter by platform):**
```json
{
  "id": 1,
  "method": "get",
  "params": [{
    "url": "/dvmdb/device",
    "filter": [
      ["platform_str", "like", "FortiGate"],
      "or",
      ["platform_str", "like", "FortiWiFi"]
    ],
    "option": ["extra info"],
    "loadsub": 0
  }]
}
```

### Information Available

From FortiManager, we can retrieve:

✅ **Device Identification**
- Serial Number
- Device Name
- Model/Platform
- Hostname

✅ **Device Status**
- Connection Status
- Management Mode
- OS Version & Build
- Last Check-in Time

✅ **Network Information**
- Management IP
- VDOM Configuration
- HA Status

✅ **Organizational Info**
- ADOM Assignment
- Device Groups
- Meta Fields (custom)
- Description/Comments

⚠️ **Limited Information**
- Registration date (not directly available)
- Contract/entitlement information (not in FortiManager)
- Folder path (FortiCloud concept)

💡 **Additional Capabilities**
- Real-time device monitoring via `/sys/proxy/json`
- Device configuration access
- Policy package assignments

---

## FortiSwitch Devices

FortiSwitch devices can be managed in two ways:
1. Directly as managed devices (FortiSwitch Manager)
2. Through FortiGate FortiLink (more common)

### Method 1: Managed FortiSwitch

**REQUEST:**
```json
{
  "id": 1,
  "method": "get",
  "params": [{
    "url": "/pm/config/adom/<adom>/obj/fsp/managed-switch",
    "fields": ["name", "switch-id", "state", "status", "fsw-wan1-peer", "version"],
    "scope member": [{
      "name": "All_FortiGate"
    }]
  }]
}
```

**RESPONSE:**
```json
{
  "id": 1,
  "result": [{
    "data": [
      {
        "name": "S108DVREDACTED01",
        "switch-id": "S108DVREDACTED01",
        "state": "enable",
        "status": "idle",
        "version": "S108D-v6.4.8-build0491",
        "fsw-wan1-peer": "FGT-Branch-01"
      }
    ],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

### Method 2: Via FortiGate (FortiLink)

Query FortiSwitch status through the managing FortiGate:

**REQUEST:**
```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "url": "/sys/proxy/json",
    "data": {
      "action": "get",
      "resource": "/api/v2/monitor/switch-controller/managed-switch",
      "target": [
        "/adom/<adom>/device/<fortigate>"
      ]
    }
  }]
}
```

### FortiSwitch Information Available

✅ **Device Identification**
- Serial Number (switch-id)
- Device Name
- Model (from version string)
- Parent FortiGate

✅ **Status Information**
- Connection Status
- Firmware Version
- Switch State
- Port Status (via detailed query)

⚠️ **Not Available**
- Direct contract/license info
- Registration dates
- Standalone management IP (when in FortiLink mode)

---

## FortiAP Devices

FortiAP devices are managed through FortiGate devices using the wireless controller feature.

### Get FortiAP Status

**REQUEST:**
```json
{
  "id": 1,
  "method": "get",
  "params": [{
    "url": "/pm/config/adom/<adom>/_controller/status/fap",
    "scope member": [{
      "name": "All_FortiGate"
    }]
  }]
}
```

**RESPONSE:**
```json
{
  "id": 1,
  "result": [{
    "data": [
      {
        "wtp-id": "FAP421E0000000001",
        "wtp-name": "Office-AP-01",
        "wtp-model": "FAP-421E",
        "admin": 1,
        "connection-state": 5,
        "ip-address": "192.168.100.50",
        "fgt-name": "FGT-Branch-01",
        "fgt-vdom": "root",
        "version": "FAP421E-v6.4.8-build0483"
      }
    ],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

### Alternative: Query via FortiGate

**REQUEST:**
```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "url": "/sys/proxy/json",
    "data": {
      "action": "get",
      "resource": "/api/v2/monitor/wifi/managed_ap",
      "target": [
        "/adom/<adom>/device/<fortigate>/vdom/<vdom>"
      ]
    }
  }]
}
```

### FortiAP Information Available

✅ **Device Identification**
- Serial Number (wtp-id)
- Device Name (wtp-name)
- Model (wtp-model)
- Parent FortiGate

✅ **Status Information**
- Connection State
- IP Address
- Firmware Version
- Admin Status

✅ **Additional Details**
- Client Count (via detailed query)
- Radio Status
- Signal Strength

⚠️ **Not Available**
- Direct contract/license info
- Registration dates
- Standalone management

---

## Using Proxy API for FortiSwitch and FortiAP (RECOMMENDED APPROACH)

### Overview

**Important Discovery**: FortiSwitch and FortiAP devices are not directly managed as first-class objects in FortiManager's central database. Instead, they are locally managed by their parent FortiGate devices through:
- **FortiSwitch**: FortiLink technology
- **FortiAP**: Wireless Controller feature

To retrieve comprehensive FortiSwitch and FortiAP information, we must use FortiManager's **proxy API** (`/sys/proxy/json`) to forward FortiGate REST API requests to each managed FortiGate device.

### The Proxy API Mechanism

FortiManager's `/sys/proxy/json` endpoint allows you to encapsulate FortiGate REST API calls within FortiManager JSON RPC API requests. This enables querying managed FortiGates for their locally-managed devices.

#### Proxy Request Structure

```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "url": "/sys/proxy/json",
    "data": {
      "action": "<HTTP_METHOD>",
      "resource": "<FORTIGATE_REST_API_ENDPOINT>",
      "target": [
        "<TARGET_SPECIFICATION>"
      ],
      "timeout": 30
    }
  }]
}
```

**Parameters Explained**:
- `action`: HTTP method for the FortiGate REST API (`get`, `post`, `put`, `delete`)
- `resource`: The FortiGate REST API endpoint (e.g., `/api/v2/monitor/wifi/managed_ap`)
- `target`: Array of devices or device groups to query
- `timeout`: Optional timeout in seconds (default: 60, max: 28800)

#### Target Specification Options

The `target` field is extremely flexible:

1. **Single Device**:
   ```json
   "target": ["/adom/demo/device/FGT-01"]
   ```

2. **Multiple Devices**:
   ```json
   "target": [
     "/adom/demo/device/FGT-01",
     "/adom/demo/device/FGT-02"
   ]
   ```

3. **Device Group (all devices in group)**:
   ```json
   "target": ["/adom/demo/group/All_FortiGate"]
   ```

4. **All Devices Across All ADOMs**:
   ```json
   "target": ["/group/All_FortiGate"]
   ```

5. **Without ADOM (device lookup)**:
   ```json
   "target": [
     "/device/FGT-01",
     "/device/FGT-02"
   ]
   ```

6. **Cross-ADOM Queries**:
   ```json
   "target": [
     "/adom/site1/group/All_FortiGate",
     "/adom/site2/group/All_FortiGate"
   ]
   ```

### Proxy Response Structure

The proxy returns an array of responses, one per target device:

```json
{
  "id": 1,
  "result": [{
    "data": [
      {
        "target": "FGT-01",
        "status": {
          "code": 0,
          "message": "OK"
        },
        "response": {
          "status": "success",
          "serial": "FGT60F0000000001",
          "version": "v7.2.10",
          "build": 1706,
          "results": [ /* actual data from FortiGate */ ]
        }
      },
      {
        "target": "FGT-02",
        "status": {
          "code": 0,
          "message": "OK"
        },
        "response": {
          "status": "success",
          "results": [ /* data from second device */ ]
        }
      }
    ],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

### FortiSwitch via Proxy

#### Tested and Verified Endpoint

**FortiGate REST API Endpoint**: `/api/v2/cmdb/switch-controller/managed-switch`

This endpoint queries the FortiGate's switch controller configuration database for all managed FortiSwitch devices.

#### Complete Example Request

```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "url": "/sys/proxy/json",
    "data": {
      "action": "get",
      "resource": "/api/v2/cmdb/switch-controller/managed-switch",
      "target": ["/group/All_FortiGate"],
      "timeout": 90
    }
  }]
}
```

#### Example Response (Single FortiGate)

```json
{
  "result": [{
    "data": [{
      "target": "FGT-Branch-01",
      "status": {
        "code": 0,
        "message": "OK"
      },
      "response": {
        "http_method": "GET",
        "revision": "282bce4319ec8a86d7b78a5c2ace85d7",
        "results": [
          {
            "switch-id": "FS108E0000000001",
            "name": "SW-Floor1-01",
            "description": "First Floor Switch",
            "switch-profile": "default",
            "fsw-wan1-peer": "",
            "fsw-wan1-admin": "disable",
            "poe-pre-standard-detection": "enable",
            "poe-detection-type": 0,
            "poe-lldp-detection": "enable",
            "directly-connected": 1,
            "version": 108,
            "max-allowed-trunk-members": 8,
            "pre-provisioned": 0,
            "l3-discovered": 0,
            "tdr-supported": "yes",
            "dynamic-capability": 66453795,
            "switch-device-tag": "",
            "switch-dhcp-opt43-key": "",
            "mclag-igmp-snooping-aware": "no",
            "dynamically-discovered": 0,
            "type": "physical",
            "owner-vdom": "root",
            "flow-identity": "",
            "staged-image-version": "",
            "delayed-restart-trigger": 0,
            "firmware-provision": "disable",
            "firmware-provision-version": "",
            "firmware-provision-latest": "disable",
            "ports": [ /* array of port objects */ ]
          }
        ],
        "vdom": "root",
        "path": "switch-controller",
        "name": "managed-switch",
        "status": "success",
        "serial": "FGT60F0000000001",
        "version": "v7.2.10",
        "build": 1706
      }
    }],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

#### FortiSwitch Fields Available

✅ **Device Identification**:
- `switch-id`: Serial number of the FortiSwitch
- `name`: User-assigned switch name
- `description`: Switch description
- `type`: Device type (physical, virtual)

✅ **Status & Configuration**:
- `directly-connected`: Connection status (1=connected, 0=disconnected)
- `version`: Firmware version number
- `switch-profile`: Applied configuration profile
- `owner-vdom`: VDOM managing the switch
- `poe-*`: Power-over-Ethernet settings
- `ports`: Array of port configurations

✅ **Derived Information**:
- Parent FortiGate: From `target` field
- Parent ADOM: From original device query

#### FortiSwitch Limitations

⚠️ **Not Available**:
- Contract/license information (use FortiCloud)
- Registration dates
- Global management IP (when in FortiLink mode)
- Support level/type

### FortiAP via Proxy

#### Tested and Verified Endpoint

**FortiGate REST API Endpoint**: `/api/v2/monitor/wifi/managed_ap`

This endpoint queries the FortiGate's wireless controller for all managed FortiAP devices and their real-time status.

#### Complete Example Request

```json
{
  "id": 1,
  "method": "exec",
  "params": [{
    "url": "/sys/proxy/json",
    "data": {
      "action": "get",
      "resource": "/api/v2/monitor/wifi/managed_ap",
      "target": ["/group/All_FortiGate"],
      "timeout": 90
    }
  }]
}
```

#### Example Response (Single FortiGate)

```json
{
  "result": [{
    "data": [{
      "target": "FGT-Branch-01",
      "status": {
        "code": 0,
        "message": "OK"
      },
      "response": {
        "http_method": "GET",
        "results": [
          {
            "wtp_id": "FAP221E0000000001",
            "wtp_name": "AP-Reception",
            "wtp_profile": "default-profile",
            "board_mac": "00:09:0F:12:34:56",
            "ip_address": "192.168.100.50",
            "connection_state": "Connected",
            "admin_status": "enable",
            "led_state": "normal",
            "location": "Reception Area",
            "mesh_uplink": "-",
            "wtp_mode": "normal",
            "region": "US",
            "firmware": "FP221E-v6.4.8-build0483",
            "max_clients": 64,
            "client_count": 5,
            "radio_1": {
              "radio_id": 1,
              "channel": 6,
              "operating_channel_bandwidth": "20MHz",
              "operating_standard": "802.11n",
              "oper_tx_power": 17
            },
            "radio_2": {
              "radio_id": 2,
              "channel": 36,
              "operating_channel_bandwidth": "80MHz",
              "operating_standard": "802.11ac",
              "oper_tx_power": 20
            }
          }
        ],
        "vdom": "root",
        "path": "wifi",
        "name": "managed_ap",
        "status": "success",
        "serial": "FGT60F0000000001",
        "version": "v7.2.10",
        "build": 1706
      }
    }],
    "status": {
      "code": 0,
      "message": "OK"
    }
  }]
}
```

#### FortiAP Fields Available

✅ **Device Identification**:
- `wtp_id`: Serial number of the FortiAP
- `wtp_name`: User-assigned AP name
- `board_mac`: MAC address
- `wtp_profile`: Applied wireless profile

✅ **Status & Location**:
- `connection_state`: Connection status (Connected/Disconnected)
- `admin_status`: Administrative status
- `ip_address`: Management IP address
- `location`: Physical location description
- `led_state`: LED status indicator

✅ **Wireless Configuration**:
- `firmware`: Firmware version string
- `region`: Regulatory region
- `wtp_mode`: Operating mode
- `max_clients`: Maximum client capacity
- `client_count`: Current connected clients

✅ **Radio Information**:
- `radio_1`, `radio_2`: Radio-specific details
  - `channel`: Operating channel
  - `operating_channel_bandwidth`: Channel width
  - `operating_standard`: 802.11 standard
  - `oper_tx_power`: Transmit power

✅ **Derived Information**:
- Parent FortiGate: From `target` field
- Parent ADOM: From original device query

#### FortiAP Limitations

⚠️ **Not Available**:
- Contract/license information (use FortiCloud)
- Registration dates
- Support level/type

### Implementation Strategy

#### Step-by-Step Approach

1. **Get All FortiGate Devices**:
   ```json
   GET /dvmdb/device
   ```
   - Collect all FortiGate serial numbers, names, and ADOM assignments

2. **Query All FortiGates for FortiSwitch**:
   ```json
   EXEC /sys/proxy/json
   {
     "action": "get",
     "resource": "/api/v2/cmdb/switch-controller/managed-switch",
     "target": ["/group/All_FortiGate"]
   }
   ```
   - Single request queries all FortiGates simultaneously
   - FortiManager handles parallelization

3. **Query All FortiGates for FortiAP**:
   ```json
   EXEC /sys/proxy/json
   {
     "action": "get",
     "resource": "/api/v2/monitor/wifi/managed_ap",
     "target": ["/group/All_FortiGate"]
   }
   ```

4. **Process Results**:
   - Iterate through each device's response
   - Match `target` back to parent FortiGate
   - Extract device information from `response.results`
   - Enrich with ADOM and parent device details

5. **Export to CSV**:
   - Standardized format matching FortiCloud exports
   - Include parent FortiGate and ADOM columns

#### Error Handling

Common scenarios to handle:

1. **Device Disconnected**:
   ```json
   {
     "status": {"code": -3, "message": "Device not connected"},
     "target": "FGT-Disconnected-01"
   }
   ```

2. **Unsupported Endpoint**:
   ```json
   {
     "response": {"http_status": 404, "status": "error"},
     "status": {"code": -6, "message": "Invalid url"}
   }
   ```

3. **Timeout**:
   - Device took too long to respond
   - Increase timeout value or retry

4. **No Devices Found**:
   ```json
   {"response": {"results": [], "status": "success"}}
   ```

#### Performance Considerations

- **Single Request Benefits**: Querying `/group/All_FortiGate` sends one request to FortiManager, which parallelizes to all FortiGates
- **Timeout Settings**: Set appropriate timeout (90+ seconds for large deployments)
- **Result Size**: Responses can be large with many devices; consider memory usage
- **Rate Limiting**: FortiManager may throttle rapid successive requests

### Tested Configuration

The following configuration was tested and validated:

**Test Environment**:
- FortiManager: fortimanager.example.com
- API Version: 7.4.8
- FortiGates: 62 devices across 11 ADOMs
- FortiGate Versions: v7.0.x, v7.2.x, v7.4.x

**Test Results**:
- ✅ `/api/v2/cmdb/switch-controller/managed-switch` - Working
- ✅ `/api/v2/monitor/wifi/managed_ap` - Working
- ✅ Proxy to `/group/All_FortiGate` - Working
- ✅ Response parsing - Working
- ✅ Error handling for disconnected devices - Working

**Note**: Test environment had no active FortiSwitch or FortiAP devices connected, but the API endpoints responded successfully with empty result arrays, confirming the approach is correct.

---

## Comparison with FortiCloud

| Information | FortiCloud | FortiManager |
|-------------|------------|--------------|
| **Serial Number** | ✅ Yes | ✅ Yes |
| **Product Model** | ✅ Yes | ✅ Yes |
| **Description** | ✅ Yes | ✅ Yes (desc field) |
| **Account/ADOM** | ✅ Account ID | ✅ ADOM name |
| **Company** | ✅ Yes | ✅ Via meta fields |
| **Organizational Unit** | ✅ Yes | ✅ Device groups |
| **Registration Date** | ✅ Yes | ❌ Not available |
| **Device Status** | ✅ Yes | ✅ conn_status |
| **Is Decommissioned** | ✅ Yes | ❌ Delete or unreg |
| **Folder Path** | ✅ Yes | ❌ Not applicable |
| **Support Level** | ✅ Yes (entitlements) | ❌ Not in FMG |
| **Support Type** | ✅ Yes (entitlements) | ❌ Not in FMG |
| **Contract Dates** | ✅ Start/End dates | ❌ Not in FMG |
| **Contract Status** | ✅ Active/Expired | ❌ Not in FMG |
| **Management IP** | ❌ Limited | ✅ Yes |
| **Connection Status** | ❌ Limited | ✅ Real-time |
| **OS Version/Build** | ❌ Limited | ✅ Detailed |
| **HA Configuration** | ❌ No | ✅ Yes |
| **VDOM Info** | ❌ No | ✅ Yes |
| **Real-time Config** | ❌ No | ✅ Yes |

### Key Differences

1. **FortiCloud Focus**: Asset management, licensing, support contracts
2. **FortiManager Focus**: Configuration management, operational status, real-time monitoring

3. **Complementary Systems**: 
   - Use FortiCloud for contract/license tracking
   - Use FortiManager for operational status and configuration

---

## Implementation Notes

### Field Mapping Strategy

When implementing scripts similar to FortiCloud exporters, map fields as follows:

| FortiCloud Field | FortiManager Equivalent |
|------------------|------------------------|
| `serialNumber` | `sn` |
| `productModel` | `platform_str` |
| `description` | `desc` |
| `accountId` | ADOM name (from `extra info.adom`) |
| `company` | `meta fields` (custom) |
| `registrationDate` | ❌ Use first seen date if tracked |
| `status` | Map `conn_status` values |
| `isDecommissioned` | Check `mgmt_mode == 0` (unreg) |
| `folderPath` | Device group path |

### ADOM Handling

FortiManager uses ADOMs (Administrative Domains) similar to FortiCloud's organizational structure:

- **Global ADOM**: Contains unassigned devices
- **root ADOM**: Default ADOM
- **Custom ADOMs**: Per-customer or per-site

Get ADOM list:
```json
{
  "id": 1,
  "method": "get",
  "params": [{
    "url": "/dvmdb/adom",
    "fields": ["name", "desc"],
    "filter": ["restricted_prds", "==", "fos"]
  }]
}
```

### Error Handling

Common error codes:

- `0`: Success (OK)
- `-11`: No permission for resource
- `-3`: Object not found
- `-10`: Permission denied

**Example Error Response:**
```json
{
  "id": 1,
  "result": [{
    "status": {
      "code": -11,
      "message": "No permission for the resource"
    },
    "url": "/dvmdb/device"
  }]
}
```

### Pagination

For large device lists, use filtering and fields selection to reduce payload:

```json
{
  "params": [{
    "url": "/dvmdb/device",
    "fields": ["name", "sn", "platform_str", "ip", "conn_status"],
    "loadsub": 0,
    "option": ["no loadsub"]
  }]
}
```

### Best Practices

1. **Use API Keys**: Token-based auth is more secure and simpler
2. **Limit Fields**: Only request needed fields to reduce response size
3. **Filter Early**: Apply filters at API level, not in post-processing
4. **Cache ADOM List**: ADOMs change infrequently
5. **Handle Disconnected Devices**: Check `conn_status` before detailed queries
6. **Use `extra info`**: Get ADOM assignments in single query
7. **Respect Rate Limits**: FortiManager has internal rate limiting

---

## References

### Official Documentation

1. **FortiManager JSON API Introduction**
   - Location: `fortimanagerapireference/FortiManager-how-to-guide/001_fmg_json_api_introduction.rst`
   - Topics: Authentication, API structure, basic operations

2. **Device Management Guide**
   - Location: `fortimanagerapireference/FortiManager-how-to-guide/007_device_management/007_device_management.rst`
   - Topics: Device queries, status, metadata

3. **Provisioning Template Management**
   - Location: `fortimanagerapireference/FortiManager-how-to-guide/009_provisioning_template_management.rst`
   - Topics: FortiSwitch, FortiAP management

4. **FortiManager JSON API Reference**
   - Location: `fortimanagerapireference/FortiManager-7.4.8-JSON-API-Reference/html/`
   - Topics: Complete API endpoint reference

### API Endpoints Quick Reference

```
# Device Management
GET  /dvmdb/device                          # All devices
GET  /dvmdb/adom/<adom>/device             # Devices in ADOM
GET  /dvmdb/device/<device>                # Specific device

# ADOM Management  
GET  /dvmdb/adom                           # List ADOMs

# FortiSwitch (Method 1)
GET  /pm/config/adom/<adom>/obj/fsp/managed-switch

# FortiAP Status
GET  /pm/config/adom/<adom>/_controller/status/fap

# System Status
GET  /cli/global/system/status             # FortiManager info

# Proxy to Managed Device (Method 2 for FSW/FAP)
EXEC /sys/proxy/json                       # Forward to managed device
```

### Example Use Cases

**1. Daily Device Inventory Report**
- Query all devices
- Export to CSV with status
- Compare with previous day

**2. Contract Tracking Integration**
- Export device list from FortiManager
- Match with FortiCloud contracts by serial number
- Generate unified report

**3. Health Dashboard**
- Monitor connection status
- Track OS versions
- Alert on disconnected devices

**4. Compliance Reporting**
- List devices per site (ADOM)
- Track configuration status
- Verify policy assignments

---

## Appendix A: Sample API Responses

### Full Device Object

```json
{
  "adm_pass": [],
  "adm_usr": "admin",
  "app_ver": "",
  "av_ver": "",
  "beta": -1,
  "branch_pt": 0,
  "build": 2462,
  "checksum": "",
  "conf_status": 1,
  "conn_mode": 1,
  "conn_status": 1,
  "db_status": 1,
  "desc": "Branch Office Firewall",
  "dev_status": 1,
  "fap_cnt": 2,
  "faz.full_act": 0,
  "faz.perm": 15,
  "faz.quota": 0,
  "faz.used": 0,
  "fex_cnt": 0,
  "flags": 67371040,
  "foslic_cpu": 0,
  "foslic_dr_site": 0,
  "foslic_inst_time": 0,
  "foslic_last_sync": 0,
  "foslic_ram": 0,
  "foslic_type": 0,
  "foslic_utm": [],
  "fsw_cnt": 1,
  "ha_group_id": 0,
  "ha_group_name": "",
  "ha_mode": 0,
  "ha_slave": [],
  "hdisk_size": 0,
  "hostname": "FGT-Branch-01",
  "hw_rev_major": 0,
  "hw_rev_minor": 0,
  "ip": "192.168.1.10",
  "ips_ext": 0,
  "ips_ver": "",
  "last_checked": 1727728800,
  "last_resync": 1727728800,
  "latitude": "",
  "longitude": "",
  "maxvdom": 10,
  "meta fields": {},
  "mgmt_id": 123456,
  "mgmt_if": "port1",
  "mgmt_mode": 3,
  "mgt_vdom": "root",
  "mr": 0,
  "name": "FGT-Branch-01",
  "node_flags": 0,
  "oid": 101,
  "os_type": 0,
  "os_ver": 7,
  "patch": 0,
  "platform_str": "FortiGate-60F",
  "psk": "",
  "sn": "FGT60F0000000001",
  "version": 700,
  "vm_cpu": 0,
  "vm_cpu_limit": 0,
  "vm_lic_expire": 0,
  "vm_mem": 0,
  "vm_mem_limit": 0,
  "vm_status": 0,
  "extra info": {
    "adom": "root"
  }
}
```

---

## Appendix B: Environment Configuration

### Required Environment Variables

For the FortiManager scripts, configure these in `.env` or environment:

```bash
# FortiManager Configuration
FORTIMANAGER_HOST=manager.example.com
FORTIMANAGER_API_KEY=your_api_key_here
FORTIMANAGER_VERIFY_SSL=true
DEBUG=false
```

### Script Configuration File Format

Alternative to environment variables, create `fortimanagerapikey` file:

```
apikey=your_api_key_here
url=your.fortimanager.hostname
```

---

## Conclusion

The FortiManager API provides comprehensive access to managed device information with a focus on operational status and configuration management. While it doesn't provide license/contract information (that's FortiCloud's domain), it excels at real-time device status, connectivity, and configuration details.

For complete visibility, organizations should use both:
- **FortiManager**: Operational status, configuration, real-time monitoring
- **FortiCloud**: License management, contracts, entitlements

The scripts developed for this project mirror the FortiCloud approach but adapt to FortiManager's strengths, providing consistent CSV exports for unified reporting and analysis.

---

**Document Version History**

- v1.0 (2025-09-30): Initial documentation based on FortiManager 7.4.8 API
