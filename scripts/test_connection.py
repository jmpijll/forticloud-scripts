#!/usr/bin/env python3
"""
FortiCloud API - Connection Test Script

This script tests the connection and authentication with FortiCloud API
without retrieving any data. Use this to validate your setup.

Author: FortiCloud API Project
Date: September 29, 2025
"""

import os
import sys
from dotenv import load_dotenv
import requests


def test_dependencies():
    """Test if all required dependencies are installed."""
    print("Testing Python dependencies...")
    
    try:
        import requests
        print(f"  [OK] requests version: {requests.__version__}")
    except ImportError:
        print("  [FAIL] requests not found")
        return False
    
    try:
        import dotenv
        print(f"  [OK] python-dotenv installed")
    except ImportError:
        print("  [FAIL] python-dotenv not found")
        return False
    
    print()
    return True


def test_env_file():
    """Test if .env file exists and has required variables."""
    print("Testing environment configuration...")
    
    if not os.path.exists('.env'):
        print("  [FAIL] .env file not found")
        print("    --> Create .env file based on .env.example")
        return False
    
    print("  [OK] .env file exists")
    
    load_dotenv()
    
    required_vars = [
        'FORTICLOUD_CLIENT_ID',
        'FORTICLOUD_CLIENT_SECRET',
        'FORTICLOUD_AUTH_URL',
        'FORTICLOUD_API_BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(var)
            print(f"  [FAIL] {var} is not set")
        else:
            # Mask sensitive values
            if 'SECRET' in var or 'ID' in var:
                display_value = value[:4] + '*' * (len(value) - 4) if len(value) > 4 else '***'
            else:
                display_value = value
            print(f"  [OK] {var} = {display_value}")
    
    print()
    
    if missing_vars:
        print(f"  [FAIL] Missing variables: {', '.join(missing_vars)}")
        return False
    
    return True


def test_authentication():
    """Test authentication with FortiCloud API."""
    print("Testing FortiCloud API authentication...")
    
    load_dotenv()
    
    # Try both username/password and client_id/client_secret formats
    username = os.getenv('FORTICLOUD_USERNAME') or os.getenv('FORTICLOUD_CLIENT_ID')
    password = os.getenv('FORTICLOUD_PASSWORD') or os.getenv('FORTICLOUD_CLIENT_SECRET')
    auth_url = os.getenv('FORTICLOUD_AUTH_URL')
    
    try:
        # FortiCloud uses username/password format
        payload = {
            "username": username,
            "password": password,
            "client_id": "assetmanagement",
            "grant_type": "password"
        }
        
        print(f"  --> Connecting to {auth_url}...")
        
        response = requests.post(
            auth_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                print("  [OK] Authentication successful!")
                print(f"  [OK] Token received (expires in {data.get('expires_in', 'unknown')} seconds)")
                print()
                return True
            else:
                print("  [FAIL] No access token in response")
                print(f"  Response: {data}")
                print()
                return False
        else:
            print(f"  [FAIL] Authentication failed (Status {response.status_code})")
            print(f"  Response: {response.text}")
            print()
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL] Connection error: Cannot reach {auth_url}")
        print(f"  Details: {e}")
        print()
        return False
    except requests.exceptions.Timeout:
        print("  [FAIL] Request timed out")
        print()
        return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        print()
        return False


def main():
    """Main test execution."""
    print("=" * 70)
    print("FortiCloud API - Connection Test")
    print("=" * 70)
    print()
    
    # Change to project root if running from scripts directory
    if os.path.basename(os.getcwd()) == 'scripts':
        os.chdir('..')
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_dependencies():
        tests_passed += 1
    
    if test_env_file():
        tests_passed += 1
    
    if test_authentication():
        tests_passed += 1
    
    # Summary
    print("=" * 70)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    print("=" * 70)
    
    if tests_passed == tests_total:
        print()
        print("[SUCCESS] All tests passed!")
        print("[SUCCESS] Your FortiCloud API setup is working correctly.")
        print()
        print("Next steps:")
        print("  1. Run: python scripts/get_fortigate_devices.py")
        print("  2. Review the generated CSV file")
        print()
        return 0
    else:
        print()
        print("[FAIL] Some tests failed. Please review the errors above.")
        print()
        print("Common solutions:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Create .env file based on .env.example")
        print("  - Verify your API credentials in FortiCloud IAM")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
