# Quick Start Guide

## Prerequisites

1. Install Git: https://git-scm.com/download/win
2. Install Python 3.8+: https://www.python.org/downloads/
3. Get FortiCloud API credentials from: https://support.fortinet.com/iam/

## 5-Minute Setup

```powershell
# 1. Initialize git repository
git init
git add .
git commit -m "Initial commit"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (copy from .env.example)
# Then edit .env and add your credentials

# 4. Test your setup
python scripts/test_connection.py

# 5. Run the main script
python scripts/get_fortigate_devices.py
```

## Files Overview

- `README.md` - Project documentation
- `SETUP_GUIDE.md` - Detailed setup instructions
- `requirements.txt` - Python dependencies
- `.env` - Your API credentials (create manually)
- `docs/FortiCloud_API_Research.md` - API documentation
- `scripts/get_fortigate_devices.py` - Main script
- `scripts/test_connection.py` - Setup validation script

## Commands

**Test connection:**
```powershell
python scripts/test_connection.py
```

**Get FortiGate/FortiWiFi devices:**
```powershell
python scripts/get_fortigate_devices.py
```

**Enable debug mode:**
Edit `.env` and set `DEBUG=true`

## Common Issues

| Issue | Solution |
|-------|----------|
| "git not recognized" | Install Git and restart terminal |
| "python not recognized" | Install Python and add to PATH |
| "No module named 'requests'" | Run `pip install -r requirements.txt` |
| "Authentication failed" | Check credentials in `.env` file |
| "No devices found" | Verify account has devices in FortiCloud |

## Need Help?

See `SETUP_GUIDE.md` for detailed troubleshooting.
