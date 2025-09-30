# Fortinet API Asset Management

Automated scripts to retrieve and export FortiGate, FortiSwitch, and FortiAP device information from FortiCloud and FortiManager using their respective APIs.

## 📦 What's Included

- **FortiCloud Scripts** - Asset management and contract tracking
- **FortiManager Scripts** - Operational device management and status monitoring

## 🎯 Features

- **Automatic Account Discovery** - No manual account ID configuration needed
- **Multi-Device Support** - Separate scripts for FortiGate, FortiSwitch, and FortiAP
- **Complete Data** - Includes active AND decommissioned devices
- **Rich Metadata** - Account, OU, company information in every export
- **Contract History** - All entitlements including expired support contracts
- **CSV Export** - Easy-to-use format for Excel, Power BI, or other tools

## 📋 Prerequisites

- **Python 3.12+**
- **FortiCloud API User** with Organization scope
  - Access to Organization API
  - Access to IAM API  
  - Access to Asset Management API

## 🚀 Quick Start

### 1. Install Python Dependencies

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 2. Configure API Credentials

Copy `env.template` to `.env` and add your credentials:

```bash
FORTICLOUD_CLIENT_ID=your_api_user_id
FORTICLOUD_CLIENT_SECRET=your_api_password
FORTICLOUD_AUTH_URL=https://customerapiauth.fortinet.com/api/v1/oauth/token
FORTICLOUD_API_BASE_URL=https://support.fortinet.com/ES/api/registration/v3
DEBUG=false
```

Get your API credentials from:  
`FortiCloud Portal` → `IAM` → `API Users` → `Create API User`

**Important:** API user must have **Organization scope** type.

### 3. Run Scripts

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Export FortiSwitch devices
python scripts/get_fortiswitch_devices.py

# Export FortiAP devices
python scripts/get_fortiap_devices.py

# Export FortiGate/FortiWiFi devices
python scripts/get_fortigate_devices.py
```

Each script will:
1. Auto-discover all accessible accounts and OUs
2. Retrieve all devices from all accounts
3. Filter by device type
4. Export to timestamped CSV file

## 📊 CSV Output Format

All CSVs include the following columns:

| Column | Description |
|--------|-------------|
| **Serial Number** | Device serial number |
| **Product Model** | Device model (e.g., FortiSwitch 124F POE) |
| **Description** | User-defined description |
| **Account ID** | FortiCloud account ID |
| **Company** | Company name |
| **Organizational Unit** | OU/sub-account name |
| **Registration Date** | When device was registered |
| **Device Status** | Registration status (Registered, Pending, etc.) |
| **Is Decommissioned** | Yes/No - marks retired devices |
| **Folder Path** | Asset folder in FortiCloud |
| **Support Level** | Support tier (e.g., Premium, Advanced HW) |
| **Support Type** | Contract type (e.g., Hardware, Technical Support) |
| **Start Date** | Contract start date |
| **End Date** | Contract expiration date |
| **Contract Status** | Active, Expired, or Unknown |

**Note:** Each device may have multiple rows (one per entitlement/contract).

## 🔍 Understanding the Data

### Decommissioned Devices

Extra devices marked as "Decommissioned: Yes" are **legitimate devices** that:
- Are no longer active in production
- Are filtered out of FortiCloud GUI exports by default
- Provide complete asset history and inventory tracking

To filter them out in Excel: Apply filter on "Is Decommissioned" column → Show only "No"

### Multiple Rows Per Device

Devices appear multiple times when they have:
- Multiple support contracts (current + historical)
- Multiple entitlement types (Hardware, Firmware, Technical Support)

Use Excel pivot tables or `UNIQUE()` function to get device counts.

## 📁 Project Structure

```
forticloud-assets/
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── env.template            # Environment template
├── docs/
│   ├── FortiCloud_API_Research.md    # FortiCloud API documentation
│   └── FortiManager_API_Research.md  # FortiManager API documentation
├── scripts/
│   ├── get_fortigate_devices.py      # FortiCloud FortiGate export
│   ├── get_fortiswitch_devices.py    # FortiCloud FortiSwitch export
│   ├── get_fortiap_devices.py        # FortiCloud FortiAP export
│   ├── fmg_get_fortigate_devices.py  # FortiManager FortiGate export
│   ├── fmg_get_fortiswitch_devices.py # FortiManager FortiSwitch export
│   ├── fmg_get_fortiap_devices.py    # FortiManager FortiAP export
│   └── test_connection.py            # Test API connectivity
└── venv/                   # Python virtual environment
```

## 🛠️ Test Connection

To verify your API credentials:

```powershell
python scripts/test_connection.py
```

This will validate:
- Python dependencies
- Environment variables
- API authentication
- Account discovery

## ⚙️ Technical Details

### How Account Discovery Works

The scripts automatically:
1. Authenticate with **Organization API** to get all OUs
2. Authenticate with **IAM API** to query accounts per OU
3. Build metadata mapping (Account ID → Company, OU name)
4. Use **Asset Management API** to retrieve devices from each account

**No manual configuration needed!**

### Serial Number Patterns

**Important:** FortiSwitch devices have serial numbers starting with **both "F" and "S"**:
- `F` prefix: FS1E48T... (FortiSwitch 1024E, 1048E)
- `S` prefix: S108EN..., S124FPTF... (all other models)

The scripts handle this automatically by querying both patterns and deduplicating.

### API Rate Limiting

- Sequential account queries (no parallelization)
- ~50-75 seconds for 17 accounts with 1000+ devices
- No rate limit issues observed

## 📝 Documentation

- **`docs/FortiCloud_API_Research.md`** - Complete API reference with endpoints, authentication, patterns, and best practices

## 🐛 Troubleshooting

### "Missing required environment variables"
→ Ensure `.env` file exists and contains all required variables

### "Authentication failed: invalid_client"
→ Verify API User ID and Password are correct

### "Request should include a positive number for accountId"
→ API user must have **Organization scope** type (not Account scope)

### No devices found
→ Verify API user has access to Asset Management API

### Python/pip not found
→ Install Python 3.12+ and ensure it's in your PATH

---

## 🔧 FortiManager Scripts

Additional scripts are provided for FortiManager to retrieve operational device information.

### FortiManager Features

- **Real-time Device Status** - Connection status and health monitoring
- **ADOM-based Organization** - Multi-tenancy support
- **Detailed Version Info** - OS version, build numbers, patch levels
- **HA Configuration** - High availability status and cluster info
- **No Licensing Needed** - Direct API access with API key

### FortiManager Quick Start

#### 1. Configure API Access

Create a `fortimanagerapikey` file in the project root:

```
apikey=your_api_key_here
url=your.fortimanager.hostname
```

Or use environment variables:

```bash
FORTIMANAGER_HOST=your.fortimanager.hostname
FORTIMANAGER_API_KEY=your_api_key_here
FORTIMANAGER_VERIFY_SSL=true
DEBUG=false
```

#### 2. Generate API Key

On FortiManager CLI:

```
config system admin user
    edit api_user_001
        set user_type api
        set rpc-permit read-write
    next
end

execute api-user generate-key api_user_001
```

#### 3. Run FortiManager Scripts

```powershell
# Export FortiGate devices from FortiManager
python scripts/fmg_get_fortigate_devices.py

# Export FortiSwitch devices from FortiManager
python scripts/fmg_get_fortiswitch_devices.py

# Export FortiAP devices from FortiManager
python scripts/fmg_get_fortiap_devices.py
```

### FortiManager CSV Output

FortiManager exports include:

| Column | Description |
|--------|-------------|
| **Serial Number** | Device serial number |
| **Device Name** | Device name in FortiManager |
| **Hostname** | Device hostname |
| **Product Model** | Device model/platform |
| **ADOM** | Administrative Domain |
| **Management IP** | Device management IP address |
| **Connection Status** | Connected, Disconnected, Unknown |
| **Management Mode** | Normal, Unreg, etc. |
| **OS Version** | FortiOS version and build |
| **HA Mode** | Standalone, Active-Passive, Cluster |
| **HA Cluster Name** | Name of HA cluster (if applicable) |
| **HA Role** | Primary or Secondary (for HA members) |
| **HA Member Status** | Online, Offline status of HA member |
| **HA Priority** | Failover priority value |
| **Last Checked** | Last communication timestamp |

**Note:** HA clusters are expanded into separate rows for each member, making it easy to identify and track individual cluster devices.

### FortiCloud vs FortiManager

| Feature | FortiCloud | FortiManager |
|---------|------------|--------------|
| **License Tracking** | ✅ Yes | ❌ No |
| **Support Contracts** | ✅ Yes | ❌ No |
| **Registration Dates** | ✅ Yes | ❌ No |
| **Real-time Status** | ❌ Limited | ✅ Yes |
| **OS Version Details** | ❌ Limited | ✅ Yes |
| **Configuration Access** | ❌ No | ✅ Yes |
| **HA Configuration** | ❌ No | ✅ Yes |

**Recommendation:** Use both for complete visibility:
- **FortiCloud** for contract/license management
- **FortiManager** for operational status and configuration

### Documentation

- **FortiCloud API**: `docs/FortiCloud_API_Research.md`
- **FortiManager API**: `docs/FortiManager_API_Research.md`

---

## 🔒 Security

- **Never commit `.env` file** (already in `.gitignore`)
- **Never commit `fortimanagerapikey` file** (already in `.gitignore`)
- API credentials provide read-only access to asset information
- FortiManager API keys are permanent - rotate regularly
- Rotate API credentials quarterly
- Store CSV exports securely (contain asset inventory)

## 📜 License

This project is provided as-is for FortiCloud API interaction.

## 🤝 Support

For FortiCloud API issues:  
→ https://support.fortinet.com/

For script issues:  
→ Review `docs/FortiCloud_API_Research.md` for API details

---

**Last Updated:** September 30, 2025  
**FortiCloud API Version:** Asset Management V3, Organization V1, IAM V1  
**FortiManager API Version:** JSON RPC (7.4.8)