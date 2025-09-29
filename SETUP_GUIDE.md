# FortiCloud API Project - Setup Guide

Welcome to the FortiCloud API Scripts project! This guide will walk you through the complete setup process.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8 or higher** installed
  - Check with: `python --version` or `python3 --version`
  - Download from: https://www.python.org/downloads/

- [ ] **Git** installed (for version control)
  - Check with: `git --version`
  - Download from: https://git-scm.com/download/win

- [ ] **FortiCloud Account** with IAM access
  - You need access to create API users

- [ ] **Text Editor** (VS Code, Notepad++, or any editor)

## Step-by-Step Setup

### Step 1: Install Git (if needed)

If you don't have Git installed:

1. Download Git from: https://git-scm.com/download/win
2. Run the installer with default options
3. Restart your terminal/PowerShell
4. Verify installation: `git --version`

### Step 2: Initialize Git Repository

Open PowerShell in the project directory and run:

```powershell
git init
git add .
git commit -m "Initial commit: FortiCloud API project setup"
```

### Step 3: Install Python Dependencies

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

Or if you have both Python 2 and 3:

```powershell
pip3 install -r requirements.txt
```

### Step 4: Create FortiCloud API Credentials

1. **Log in to FortiCloud:**
   - Go to: https://support.fortinet.com
   - Sign in with your credentials

2. **Navigate to IAM:**
   - Go to **Account** → **Identity & Access Management**
   - Or directly: https://support.fortinet.com/iam/

3. **Create API User:**
   - Click **"Add API User"** or **"Create New API User"**
   - Give it a name (e.g., "API-Script-Access")
   - **Save the Client ID and Client Secret** - you won't be able to see them again!

4. **Assign Permissions:**
   - Ensure the API user has **"Read"** access to:
     - Asset/Device Management
     - Contract Information
     - Registration Data

### Step 5: Configure Environment Variables

1. **Create the .env file:**

   Since `.env` files are protected, create it manually:

   ```powershell
   # Copy the example file
   Copy-Item .env.example .env
   ```

   Or create a new file named `.env` in the project root.

2. **Edit the .env file:**

   Open `.env` in your text editor and fill in your credentials:

   ```env
   # FortiCloud IAM API Credentials
   FORTICLOUD_CLIENT_ID=your_actual_client_id_here
   FORTICLOUD_CLIENT_SECRET=your_actual_client_secret_here

   # FortiCloud API URLs (these are usually correct as-is)
   FORTICLOUD_AUTH_URL=https://customerapiauth.fortinet.com/api/v1/oauth/token/
   FORTICLOUD_API_BASE_URL=https://support.fortinet.com/ES/api/

   # Optional: Enable debug mode for troubleshooting
   DEBUG=false
   ```

3. **Save the file** (make sure it's named exactly `.env` with no extension)

### Step 6: Test the Installation

Run a quick Python test to verify everything is set up:

```powershell
python -c "import requests; import dotenv; print('SUCCESS: All dependencies installed correctly!')"
```

### Step 7: Run Your First Script

Execute the FortiGate device retrieval script:

```powershell
python scripts/get_fortigate_devices.py
```

Or if you need to specify Python 3:

```powershell
python3 scripts/get_fortigate_devices.py
```

**Expected Output:**

```
======================================================================
FortiCloud API - FortiGate/FortiWiFi Device Export
======================================================================

Step 1: Authenticating with FortiCloud...
SUCCESS: Authentication complete

Step 2: Retrieving FortiGate devices...
Retrieved X FortiGate devices

Step 3: Retrieving FortiWiFi devices...
Retrieved Y FortiWiFi devices

Total devices: Z

Step 4: Processing device data...
Processed N rows (including contracts)

Step 5: Exporting to CSV (fortigate_devices_20250929_HHMMSS.csv)...
SUCCESS: Data exported to fortigate_devices_20250929_HHMMSS.csv

======================================================================
EXPORT COMPLETE!
======================================================================
Output file: fortigate_devices_20250929_HHMMSS.csv
Total rows: N
Unique devices: Z
```

## Troubleshooting

### Issue: "git is not recognized"

**Solution:** Install Git from https://git-scm.com/download/win and restart your terminal.

### Issue: "python is not recognized"

**Solution:** 
- Install Python from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Restart your terminal

### Issue: "No module named 'requests'"

**Solution:** Install dependencies with `pip install -r requirements.txt`

### Issue: "ERROR: Authentication failed"

**Possible causes:**
1. **Wrong credentials:** Double-check your Client ID and Secret in `.env`
2. **Expired credentials:** API credentials may have been revoked or expired
3. **Network issues:** Check your internet connection
4. **URL incorrect:** Verify the FORTICLOUD_AUTH_URL is correct

**Debug steps:**
1. Enable debug mode in `.env`: `DEBUG=true`
2. Run the script again to see detailed logs
3. Verify credentials in FortiCloud IAM portal

### Issue: "ERROR: Missing required environment variables"

**Solution:** 
1. Ensure `.env` file exists in the project root (same folder as `README.md`)
2. Check that all required variables are filled in (no empty values)
3. Ensure there are no extra spaces or quotes around values

### Issue: "No devices found"

**Possible causes:**
1. **No devices registered:** Your FortiCloud account has no devices
2. **Insufficient permissions:** API user doesn't have read access
3. **API endpoint changed:** The API URL may have changed

**Debug steps:**
1. Log in to FortiCloud portal and verify you can see devices
2. Check API user permissions in IAM
3. Enable debug mode to see actual API responses

### Issue: CSV file contains "No Contract" entries

**This is normal** if:
- Devices don't have any contracts attached
- Contracts were removed or never added
- Device is newly registered

## Next Steps

Now that your project is set up:

1. ✅ Review the generated CSV file
2. ✅ Read `docs/FortiCloud_API_Research.md` for API documentation
3. ✅ Explore creating additional scripts for other FortiCloud data
4. ✅ Set up a regular schedule to run the script (e.g., weekly)
5. ✅ Consider implementing data analysis or reporting on the CSV output

## Getting Help

- **API Documentation:** `docs/FortiCloud_API_Research.md`
- **Fortinet Developer Network:** https://fndn.fortinet.net/
- **FortiCloud Support:** https://support.fortinet.com

## Security Reminders

- ✅ **NEVER commit your `.env` file** to Git (it's in `.gitignore`)
- ✅ **Don't share your API credentials** via email or chat
- ✅ **Rotate credentials regularly** (every 90 days recommended)
- ✅ **Use separate API users** for different scripts/purposes
- ✅ **Monitor API usage** in FortiCloud IAM portal

---

**Happy scripting! 🚀**
