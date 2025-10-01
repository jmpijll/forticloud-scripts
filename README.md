# Fortinet Multi-Platform Asset Management

Automated Python scripts to retrieve and export FortiGate, FortiSwitch, and FortiAP device information from FortiManager, FortiCloud, and TopDesk using their respective APIs. All exports use a **unified 60-field CSV structure** for direct cross-platform comparison.

---

## 🎯 Key Features

### Unified CSV Structure
- **60 standardized fields** across all 9 export scripts
- **Direct comparison** between FortiManager, FortiCloud, and TopDesk data
- **Consistent formatting** (YYYY-MM-DD dates, Yes/No booleans)
- **Complete field coverage** (all fields present, even if empty)
- **Side-by-side analysis** ready for Excel, Power BI, or database import

### Multi-Platform Support

#### FortiManager
- **Real-time operational status** - Connection monitoring and health checks
- **ADOM organization** - Multi-tenancy with domain tracking
- **HA cluster expansion** - Separate rows for each cluster member
- **Firmware version tracking** - OS versions and build numbers
- **Parent device tracking** - FortiSwitch/AP linked to managing FortiGates
- **Proxy API access** - Retrieves FortiSwitch/AP data via FortiGates

#### FortiCloud
- **Automatic account discovery** - No manual account ID configuration
- **Contract management** - Active and expired support contracts
- **Entitlement tracking** - All support levels and types
- **Lifecycle dates** - Registration, EoR, EoS dates
- **Complete inventory** - Active AND decommissioned devices
- **Organizational metadata** - Account, OU, and company information

#### TopDesk
- **Asset management integration** - IT asset tracking and inventory
- **Contract enrichment** - Support contract details and dates
- **Location tracking** - Branch and location information
- **Serial number extraction** - Intelligent parsing from asset names
- **Multiple contract support** - One row per device-contract combination
- **Vendor filtering** - Fortinet device detection across all asset types

### Multi-Device Support
- **FortiGate/FortiWiFi** - Firewalls with HA configuration
- **FortiSwitch** - Managed switches with PoE tracking
- **FortiAP** - Wireless access points with client stats

---

## 📋 Prerequisites

### Software Requirements
- **Python 3.12+**
- **PowerShell** (for Windows)
- **Network access** to FortiManager/FortiCloud/TopDesk APIs

### API Access Requirements

#### FortiManager
- FortiManager 7.0+ (tested on 7.4.8)
- API User with `user_type: api` and `rpc-permit: read-write`
- Network connectivity to FortiManager HTTPS (port 443)

#### FortiCloud
- FortiCloud API User with **Organization scope**
- Access to Organization API, IAM API, and Asset Management API
- Valid API credentials (Client ID and Secret)

#### TopDesk
- TopDesk service account with API access
- Read access to Assets endpoint
- Access to Asset Links endpoint for contract retrieval

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
# Clone or download this repository
cd forticloud-assets

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 2. Configure API Credentials

#### Option A: Environment Variables (Recommended for Production)

Copy `env.template` to `.env` and configure:

```bash
# FortiManager Configuration
FORTIMANAGER_HOST=your.fortimanager.hostname
FORTIMANAGER_API_KEY=your_api_key_here
FORTIMANAGER_VERIFY_SSL=true

# FortiCloud Configuration
FORTICLOUD_CLIENT_ID=your_api_user_id
FORTICLOUD_CLIENT_SECRET=your_api_password
FORTICLOUD_AUTH_URL=https://customerapiauth.fortinet.com/api/v1/oauth/token
FORTICLOUD_API_BASE_URL=https://support.fortinet.com/ES/api/registration/v3

# TopDesk Configuration
TOPDESK_URL=https://your_tenant.topdesk.net
TOPDESK_USER=your_service_account_username
TOPDESK_PASSWORD=your_service_account_password

# General
DEBUG=false
```

#### Option B: Credential Files (Alternative)

**FortiManager:** Create `fortimanagerapikey` file:
```
apikey=your_api_key_here
url=your.fortimanager.hostname
verify_ssl=true
```

**TopDesk:** Create `topdeskapikey` file:
```
topdesk-url=https://your_tenant.topdesk.net/
topdesk-user=your_service_account
topdesk-pass=your_password
```

### 3. Run Export Scripts

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# FortiManager exports
python scripts/fmg_get_fortigate_devices.py
python scripts/fmg_get_fortiswitch_devices.py
python scripts/fmg_get_fortiap_devices.py

# FortiCloud exports
python scripts/fc_get_fortigate_devices.py
python scripts/fc_get_fortiswitch_devices.py
python scripts/fc_get_fortiap_devices.py

# TopDesk exports
python scripts/td_get_fortigate_devices.py
python scripts/td_get_fortiswitch_devices.py
python scripts/td_get_fortiap_devices.py
```

Each script will:
1. Authenticate with the appropriate API
2. Discover and retrieve all relevant devices
3. Process and flatten data into unified structure
4. Export to timestamped CSV file (e.g., `fmg_fortigate_devices_20251002_123456.csv`)

---

## 📊 Unified CSV Structure

All 9 scripts output **exactly 60 fields in the same order**, enabling direct comparison:

### Core Sections (60 total fields)

1. **Core Identification** (7 fields) - Serial Number, Device Name, Hostname, Model, Description, Asset Type, Source System
2. **Network & Connection** (4 fields) - Management IP, Connection Status, Management Mode, Firmware Version
3. **Organization & Location** (7 fields) - Company, OU, Branch, Location, Folder Path/ID, Vendor
4. **Contract Information** (9 fields) - Contract Number, SKU, Type, Summary, Start/End Dates, Status, Support Type, Archived
5. **Entitlement Information** (4 fields) - Level, Type, Start/End Dates
6. **Lifecycle & Status** (7 fields) - Status, Is Decommissioned, Archived, Registration Date, EoR, EoS, Last Updated
7. **Account Information** (3 fields) - Account ID, Email, OU ID
8. **FortiGate-Specific** (6 fields) - HA Mode, Cluster Name, Role, Member Status, Priority, Max VDOMs
9. **Parent Tracking** (4 fields) - Parent FortiGate Name, Serial, Platform, IP
10. **FortiSwitch-Specific** (3 fields) - Device Type, Max PoE Budget, Join Time
11. **FortiAP-Specific** (6 fields) - Board MAC, Admin Status, Client Count, Mesh Uplink, WTP Mode, VDOM

**See `docs/Unified_CSV_Structure.md` for complete field specification and implementation guidelines.**

### Data Format Standards

- **Dates:** `YYYY-MM-DD` format (e.g., `2025-10-02`)
- **DateTimes:** `YYYY-MM-DD HH:MM:SS` format (e.g., `2025-10-02 14:30:00`)
- **Booleans:** `Yes` or `No` (not True/False or 1/0)
- **Empty Fields:** Empty string `""` (not "N/A" or "null")
- **Integers:** Plain numbers without decimals

---

## 📁 Project Structure

```
forticloud-assets/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── env.template                       # Environment variable template
├── .gitignore                         # Git ignore rules
├── docs/
│   ├── FortiCloud_API_Research.md    # FortiCloud API documentation
│   ├── FortiManager_API_Research.md  # FortiManager API documentation
│   ├── TopDesk_API_Research.md       # TopDesk API documentation
│   └── Unified_CSV_Structure.md      # Complete CSV structure specification
├── scripts/
│   ├── fmg_get_fortigate_devices.py  # FortiManager FortiGate export
│   ├── fmg_get_fortiswitch_devices.py # FortiManager FortiSwitch export
│   ├── fmg_get_fortiap_devices.py    # FortiManager FortiAP export
│   ├── fc_get_fortigate_devices.py   # FortiCloud FortiGate export
│   ├── fc_get_fortiswitch_devices.py # FortiCloud FortiSwitch export
│   ├── fc_get_fortiap_devices.py     # FortiCloud FortiAP export
│   ├── td_get_fortigate_devices.py   # TopDesk FortiGate export
│   ├── td_get_fortiswitch_devices.py # TopDesk FortiSwitch export
│   └── td_get_fortiap_devices.py     # TopDesk FortiAP export
└── venv/                              # Python virtual environment
```

---

## 🔍 Understanding the Data

### System-Specific Characteristics

#### FortiManager Data
- **Strengths:** Real-time status, firmware versions, HA configuration, parent device tracking
- **Limitations:** No contract/license information, no lifecycle dates
- **Unique Fields:** HA configuration, Parent FortiGate details, device-specific technical data

#### FortiCloud Data
- **Strengths:** Complete contract history, entitlements, lifecycle dates (registration, EoR, EoS)
- **Limitations:** No real-time operational status, no parent device tracking
- **Unique Fields:** Account details, entitlements, contract SKUs, product lifecycle dates

#### TopDesk Data
- **Strengths:** Asset management integration, branch/location tracking, contract details
- **Limitations:** Serial numbers may require extraction, limited technical details
- **Unique Fields:** Branch, location, vendor, contract summaries

### Multiple Rows Per Device

Devices may appear multiple times when:
- **TopDesk:** Device has multiple support contracts → one row per contract
- **FortiManager:** HA cluster members → one row per member (FortiGate only)
- **FortiCloud:** Generally one row per device (unless multiple active contracts)

Use Excel pivot tables or `=UNIQUE()` function to get distinct device counts.

### Decommissioned Devices

FortiCloud includes decommissioned devices (marked `Is Decommissioned: Yes`):
- Provides complete historical inventory
- Filtered out of FortiCloud GUI exports by default
- Useful for asset lifecycle tracking
- Filter in Excel: Show only rows where `Is Decommissioned = No`

---

## 🛠️ API Setup Details

### FortiManager API User Setup

On your FortiManager CLI:

```bash
config system admin user
    edit api_user_001
        set user_type api
        set rpc-permit read-write
    next
end

execute api-user generate-key api_user_001
```

**⚠️ Important:** `rpc-permit read-write` is required for proxy API to query FortiSwitch/FortiAP.

### FortiCloud API User Setup

1. Log into FortiCloud Portal
2. Navigate to **IAM** → **API Users**
3. Click **Create API User**
4. Set scope to **Organization** (not Account)
5. Save Client ID and Client Secret

**⚠️ Important:** API user must have **Organization scope** for account discovery to work.

### TopDesk Service Account Setup

1. Create service account in TopDesk
2. Grant read access to Assets endpoint
3. Grant read access to Asset Links endpoint
4. Enable API access for the account
5. Use Basic Authentication with username and password

---

## 📊 Cross-Platform Comparison

### Feature Matrix

| Feature | FortiManager | FortiCloud | TopDesk |
|---------|-------------|------------|---------|
| Real-time Status | ✅ Yes | ❌ No | ~ Limited |
| Firmware Versions | ✅ Yes | ❌ No | ❌ No |
| HA Configuration | ✅ Yes | ❌ No | ❌ No |
| Parent Device Tracking | ✅ Yes | ❌ No | ❌ No |
| Contract Information | ❌ No | ✅ Yes | ✅ Yes |
| Entitlements | ❌ No | ✅ Yes | ❌ No |
| Lifecycle Dates | ❌ No | ✅ Yes | ❌ No |
| Branch/Location | ❌ No | ❌ No | ✅ Yes |
| Account Structure | ~ ADOM | ✅ Yes | ~ Branch |
| Serial Numbers | ✅ 100% | ✅ 100% | ~ 41-68% |

### Recommended Usage

**Use ALL THREE for complete visibility:**
- **FortiManager** → Operational monitoring and configuration management
- **FortiCloud** → License and contract lifecycle management
- **TopDesk** → Asset tracking and physical inventory management

**Compare serials across systems** to identify:
- Devices in FortiManager but not in contracts (unlicensed)
- Devices in contracts but not in FortiManager (not deployed)
- Devices in TopDesk but missing from other systems (tracking issues)

---

## 🐛 Troubleshooting

### FortiManager Issues

**"No permission for the resource"**
- Ensure API user has `rpc-permit read-write` (not just `read`)
- FortiSwitch/FortiAP require write permission for proxy API

**SSL Certificate Error**
- For self-signed certs: Set `FORTIMANAGER_VERIFY_SSL=false` in config
- Or use: `$env:FORTIMANAGER_VERIFY_SSL="false"` before running script

**Empty FortiSwitch/AP Results**
- Normal if no devices are connected to FortiGates
- FortiSwitch/AP are managed locally, not centrally by FortiManager

### FortiCloud Issues

**"Authentication failed: invalid_client"**
- Verify Client ID and Secret are correct
- Ensure API user is active and not expired

**"Request should include a positive number for accountId"**
- API user must have **Organization scope** (not Account scope)
- Recreate API user with correct scope type

**No devices found**
- Verify API user has access to Asset Management API
- Check that accounts contain registered devices

### TopDesk Issues

**406 Not Acceptable Error**
- Verify `Accept: application/json` header is set
- Check TopDesk API version compatibility

**Missing Assets**
- Default page size is 50, scripts use `pageSize=1000`
- Verify `pageStart` pagination is implemented
- Check asset template names match filter criteria

**Low Serial Number Coverage**
- Serials may be in contract names, not asset properties
- Scripts extract serials from multiple sources
- Some assets may truly lack serial numbers

### General Issues

**Python/pip not found**
- Install Python 3.12+ and ensure it's in your PATH
- Verify with: `python --version`

**Module not found errors**
- Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- Reinstall dependencies: `pip install -r requirements.txt`

**CSV encoding issues**
- All exports use UTF-8 encoding
- Open with Excel → Data → From Text/CSV → UTF-8 encoding

---

## 🔒 Security Best Practices

### Credentials Management
- **Never commit** `.env` file (already in `.gitignore`)
- **Never commit** `fortimanagerapikey` or `topdeskapikey` files (already in `.gitignore`)
- **Rotate credentials** quarterly or after personnel changes
- **Use environment variables** in production environments
- **Limit API permissions** to read-only where possible

### Data Handling
- **CSV exports contain sensitive asset inventory** - store securely
- **Apply access controls** to export files and scripts
- **Sanitize data** before sharing outside organization
- **Review exports** before committing to version control

### Network Security
- **Use SSL/TLS** for all API connections (HTTPS only)
- **Verify SSL certificates** in production (disable verification only for testing)
- **Restrict API access** to authorized IP ranges where possible
- **Monitor API usage** for unusual patterns

---

## 📚 Documentation

- **`README.md`** - This file (project overview and quick start)
- **`docs/Unified_CSV_Structure.md`** - Complete 60-field specification and modification guide
- **`docs/FortiManager_API_Research.md`** - FortiManager JSON RPC API reference
- **`docs/FortiCloud_API_Research.md`** - FortiCloud multi-API integration guide
- **`docs/TopDesk_API_Research.md`** - TopDesk Asset Management API reference

---

## 🤝 Contributing

When modifying the unified CSV structure:

1. **Update ALL 9 scripts** - Maintain consistency across all exports
2. **Follow format standards** - Use specified date, boolean, and string formats
3. **Update documentation** - Modify `docs/Unified_CSV_Structure.md`
4. **Test thoroughly** - Run all 9 scripts and verify 60-field alignment
5. **Maintain backward compatibility** - Consider keeping fields empty rather than removing

See `docs/Unified_CSV_Structure.md` for detailed implementation guidelines.

---

## 📜 License

This project is provided as-is for Fortinet API interaction and multi-platform asset management.

---

## 📞 Support

**For API Issues:**
- FortiManager: Contact Fortinet Support or consult JSON RPC documentation
- FortiCloud: https://support.fortinet.com/
- TopDesk: Contact TopDesk Support or consult API documentation

**For Script Issues:**
- Review documentation in `docs/` folder
- Check `docs/Unified_CSV_Structure.md` for field specifications
- Verify API credentials and network connectivity
- Test with `scripts/test_connection.py` (if available)

---

**Version:** 2.0  
**Last Updated:** October 2, 2025  
**Platforms:** FortiManager 7.4.8, FortiCloud API V3, TopDesk API V1.88  
**Python:** 3.12+  
**Unified Structure:** 60 fields across 9 export scripts
