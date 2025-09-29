# FortiCloud API Scripts

A comprehensive Python toolkit for interacting with the FortiCloud API to retrieve and export device asset information across multiple accounts.

## 🎯 Overview

This project provides **idempotent, self-contained scripts** that automatically discover accounts and export FortiCloud device data to CSV files. Perfect for MSPs managing multiple customer organizations.

### Key Features

- ✅ **Automatic Account Discovery** - No manual configuration needed
- ✅ **Multi-Device Support** - FortiGate, FortiWiFi, FortiSwitch, FortiAP
- ✅ **OAuth 2.0 Authentication** - Secure API access
- ✅ **Complete Coverage** - All contracts including expired ones
- ✅ **Idempotent Scripts** - Run anytime, consistent results
- ✅ **CSV Export** - Easy data analysis and reporting
- ✅ **Multi-Account Support** - Query across all accessible accounts
- ✅ **Cross-Platform** - Works on Windows, macOS, Linux
- ✅ **Production Tested** - Validated with 698+ devices across 17 accounts

---

## 📋 Prerequisites

- **Python 3.8+** (Python 3.12 recommended)
- **Git** (for version control)
- **FortiCloud IAM API User** with Organization scope

---

## 🚀 Quick Start

### 1. Setup Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source venv/bin/activate      # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy `.env.example` to `.env` and add your FortiCloud API credentials:

```bash
FORTICLOUD_CLIENT_ID=YOUR_API_ID
FORTICLOUD_CLIENT_SECRET=YOUR_API_PASSWORD
FORTICLOUD_AUTH_URL=https://customerapiauth.fortinet.com/api/v1/oauth/token/
FORTICLOUD_API_BASE_URL=https://support.fortinet.com/ES/api/registration/v3
```

### 3. Run Export Scripts

```bash
# FortiGate and FortiWiFi devices
python scripts/get_fortigate_devices.py

# FortiSwitch devices
python scripts/get_fortiswitch_devices.py

# FortiAP devices
python scripts/get_fortiap_devices.py
```

**Output:** Timestamped CSV files with device and contract information.

---

## 📂 Project Structure

```
forticloud-assets/
├── .env                                # API credentials (not in git)
├── .env.example                        # Template for credentials
├── .gitignore                          # Git ignore rules
├── README.md                           # This file
├── SETUP_GUIDE.md                      # Detailed setup instructions
├── QUICK_START.md                      # Quick reference
├── PROJECT_SUMMARY.md                  # Complete project overview
├── requirements.txt                    # Python dependencies
│
├── docs/
│   ├── FortiCloud_API_Research.md      # Comprehensive API documentation
│   └── API_Authentication_Guide.md     # OAuth authentication guide
│
├── apireference/                       # FortiCloud API specifications (JSON)
│   ├── Asset Management V3 Product.json
│   ├── Asset Management V3 Contract.json
│   ├── IAM V1 Accounts.json
│   └── Organization V1 Units.json
│
└── scripts/
    ├── get_fortigate_devices.py        # FortiGate/FortiWiFi export (idempotent)
    ├── get_fortiswitch_devices.py      # FortiSwitch export (idempotent)
    ├── get_fortiap_devices.py          # FortiAP export (idempotent)
    ├── get_all_account_ids.py          # Manual account discovery tool
    └── test_connection.py              # Connection test script
```

---

## 📜 Available Scripts

### Device Export Scripts (Idempotent)

All export scripts automatically:
1. Discover all accessible accounts
2. Authenticate with FortiCloud API
3. Retrieve devices from all accounts
4. Filter by device type
5. Export to timestamped CSV

#### FortiGate/FortiWiFi Export
```bash
python scripts/get_fortigate_devices.py
```
**Output:** `fortigate_devices_YYYYMMDD_HHMMSS.csv`

#### FortiSwitch Export
```bash
python scripts/get_fortiswitch_devices.py
```
**Output:** `fortiswitch_devices_YYYYMMDD_HHMMSS.csv`

#### FortiAP Export
```bash
python scripts/get_fortiap_devices.py
```
**Output:** `fortiap_devices_YYYYMMDD_HHMMSS.csv`

### Utility Scripts

#### Test Connection
```bash
python scripts/test_connection.py
```
Validates API credentials and connectivity.

#### Manual Account Discovery
```bash
python scripts/get_all_account_ids.py
```
Lists all accessible account IDs (useful for troubleshooting).

---

## 📊 CSV Output Format

All export scripts generate CSV files with the following columns:

| Column | Description |
|--------|-------------|
| **Serial Number** | Device unique identifier |
| **Product Model** | Device model (e.g., FortiGate-60F) |
| **Description** | User-defined device name |
| **Registration Date** | When device was registered |
| **Folder Path** | Asset folder location |
| **Support Level** | Support coverage level |
| **Support Type** | Type of support/entitlement |
| **Start Date** | Contract/entitlement start date |
| **End Date** | Contract/entitlement end date |
| **Status** | Active, Expired, or Unknown |

**Note:** Each device generates multiple rows (one per entitlement/contract).

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FORTICLOUD_CLIENT_ID` | API User ID (username) | `509B0E64-6867-4FB8-...` |
| `FORTICLOUD_CLIENT_SECRET` | API Password | `db45ce4cbfe6e623...` |
| `FORTICLOUD_AUTH_URL` | Authentication endpoint | `https://customerapiauth.fortinet.com/api/v1/oauth/token/` |
| `FORTICLOUD_API_BASE_URL` | Asset Management API base | `https://support.fortinet.com/ES/api/registration/v3` |
| `DEBUG` | Enable debug logging | `true` or `false` |

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
# In .env file
DEBUG=true
```

---

## 🔐 Security Best Practices

- ✅ Never commit `.env` files to version control
- ✅ Store credentials securely
- ✅ Rotate API credentials quarterly
- ✅ Use Organization-scope API users for multi-account access
- ✅ Monitor API usage in FortiCloud IAM portal
- ✅ Review `.gitignore` to ensure sensitive files are excluded

---

## 📚 Documentation

### Comprehensive Guides
- **[FortiCloud_API_Research.md](docs/FortiCloud_API_Research.md)** - Complete API documentation with production examples
- **[API_Authentication_Guide.md](docs/API_Authentication_Guide.md)** - OAuth 2.0 authentication details
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step setup instructions
- **[QUICK_START.md](QUICK_START.md)** - Fast reference guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview

### API Specifications
All FortiCloud API specifications are in the `apireference/` directory in JSON format.

---

## 🎯 How It Works

### Idempotent Workflow

Each script follows this self-contained workflow:

```
1. Load credentials from .env
2. Authenticate with Organization API → Get all OUs
3. Authenticate with IAM API → Get accounts per OU
4. Authenticate with Asset Management API → Get devices per account
5. Filter devices by type (FortiGate, FortiSwitch, FortiAP)
6. Flatten entitlements (one row per contract)
7. Export to timestamped CSV
```

### Multi-API Architecture

FortiCloud uses three separate APIs:
- **Organization API V1** - Organizational units
- **IAM API V1** - Account management
- **Asset Management API V3** - Device and contract data

Each requires separate authentication with service-specific `client_id` values.

---

## ⚠️ Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Ensure `.env` file exists and contains all required variables
- Check variable names match exactly

**"Authentication failed"**
- Verify API credentials are correct
- Ensure API user has proper permissions
- Check if credentials have expired

**"No devices found"**
- Verify API user has Organization scope
- Check if accounts have registered devices
- Enable DEBUG mode to see detailed API responses

**Rate limiting (429 errors)**
- Scripts automatically handle rate limits
- Wait 60 seconds and retry
- Consider spacing out large queries

---

## 🚀 Future Enhancements

Potential additions:
- Scheduled exports (via Task Scheduler/cron)
- Additional device types (FortiAnalyzer, FortiManager)
- Contract expiration alerting
- Web dashboard for data visualization
- Historical tracking database
- Email report generation

---

## 🤝 Contributing

When adding new scripts or features:
1. Follow existing code structure and patterns
2. Update this README with documentation
3. Add dependencies to `requirements.txt`
4. Document API endpoints in `docs/FortiCloud_API_Research.md`
5. Test with multiple accounts
6. Handle errors gracefully

---

## 📊 Production Stats

**Tested Environment:**
- 17 accounts across 16 organizational units
- 698 total Fortinet devices
- 133 FortiGate/FortiWiFi devices
- 20 FortiSwitch devices
- 520 FortiAP devices
- 2,961 total entitlement records

**Performance:**
- Account discovery: ~10 seconds
- Device retrieval: ~20-30 seconds
- Total runtime: ~40 seconds

---

## 📝 License

Internal use only.

---

## 📞 Support

For issues or questions:
1. Check the documentation in `docs/`
2. Enable DEBUG mode for detailed logs
3. Review `PROJECT_SUMMARY.md` for complete overview
4. Consult FortiCloud API specifications in `apireference/`

---

**Version:** 2.0 - Idempotent  
**Last Updated:** September 30, 2025  
**Status:** ✅ Production Ready