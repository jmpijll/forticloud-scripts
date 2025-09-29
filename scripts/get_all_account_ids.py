#!/usr/bin/env python3
"""
FortiCloud API - Get All Account IDs

This script retrieves all account IDs that the API user has access to
using the Organization and IAM APIs.

Author: FortiCloud API Project
Date: September 29, 2025
"""

import os
import json
import requests
from dotenv import load_dotenv


def authenticate(username: str, password: str, client_id: str, auth_url: str) -> str:
    """
    Authenticate with FortiCloud API using specific client_id.
    
    Args:
        username: API user ID
        password: API password
        client_id: Service client ID (e.g., 'iam', 'organization', 'assetmanagement')
        auth_url: Authentication endpoint URL
        
    Returns:
        OAuth access token
    """
    payload = {
        "username": username,
        "password": password,
        "client_id": client_id,
        "grant_type": "password"
    }
    
    response = requests.post(auth_url, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    return data['access_token']


def get_organization_units(token: str, base_url: str) -> dict:
    """
    Get all organizational units (OUs) that the API user has access to.
    
    Args:
        token: OAuth access token
        base_url: Organization API base URL
        
    Returns:
        Organization units response data
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/units/list"
    response = requests.post(url, headers=headers, json={}, timeout=30)
    response.raise_for_status()
    
    return response.json()


def get_accounts(token: str, base_url: str, parent_id: int = None) -> list:
    """
    Get all accounts, optionally filtered by parent OU ID.
    
    Args:
        token: OAuth access token
        base_url: IAM API base URL
        parent_id: Optional parent OU ID to filter accounts
        
    Returns:
        List of account dictionaries
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {}
    if parent_id:
        payload['parentId'] = parent_id
    
    url = f"{base_url}/accounts/list"
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    if data.get('status') == 0:
        return data.get('accounts', [])
    else:
        print(f"WARNING: API returned status {data.get('status')}: {data.get('message')}")
        return []


def main():
    """Main execution function."""
    print("=" * 70)
    print("FortiCloud API - Retrieve All Account IDs")
    print("=" * 70)
    print()
    
    # Load environment variables
    load_dotenv()
    
    username = os.getenv('FORTICLOUD_CLIENT_ID')
    password = os.getenv('FORTICLOUD_CLIENT_SECRET')
    auth_url = os.getenv('FORTICLOUD_AUTH_URL')
    
    org_base_url = "https://support.fortinet.com/ES/api/organization/v1"
    iam_base_url = "https://support.fortinet.com/ES/api/iam/v1"
    
    if not all([username, password, auth_url]):
        print("ERROR: Missing required environment variables.")
        print("Please ensure FORTICLOUD_CLIENT_ID, FORTICLOUD_CLIENT_SECRET,")
        print("and FORTICLOUD_AUTH_URL are set in your .env file.")
        return
    
    try:
        # Step 1: Authenticate with Organization API
        print("Step 1: Authenticating with Organization API...")
        org_token = authenticate(username, password, "organization", auth_url)
        print("SUCCESS: Organization API authentication complete")
        print()
        
        # Step 2: Get organizational units
        print("Step 2: Retrieving organizational units...")
        org_data = get_organization_units(org_token, org_base_url)
        
        if org_data.get('status') == 0:
            org_units = org_data.get('organizationUnits', {})
            org_id = org_units.get('orgId')
            ou_list = org_units.get('orgUnits', [])
            
            print(f"Organization ID: {org_id}")
            print(f"Found {len(ou_list)} organizational unit(s)")
            
            for ou in ou_list:
                print(f"  - OU {ou.get('id')}: {ou.get('name')} (Parent: {ou.get('parentId')})")
            print()
        else:
            print(f"WARNING: Organization API returned status {org_data.get('status')}")
            ou_list = []
        
        # Step 3: Authenticate with IAM API
        print("Step 3: Authenticating with IAM API...")
        iam_token = authenticate(username, password, "iam", auth_url)
        print("SUCCESS: IAM API authentication complete")
        print()
        
        # Step 4: Get accounts for each OU
        print("Step 4: Retrieving accounts from all organizational units...")
        all_accounts = []
        account_ids_set = set()  # Use set to avoid duplicates
        
        # Get accounts for the main organization
        if org_id:
            print(f"  Querying Organization {org_id}...")
            accounts = get_accounts(iam_token, iam_base_url, org_id)
            all_accounts.extend(accounts)
            print(f"    Found {len(accounts)} account(s)")
        
        # Get accounts for each OU
        for ou in ou_list:
            ou_id = ou.get('id')
            ou_name = ou.get('name')
            print(f"  Querying OU {ou_id} ({ou_name})...")
            accounts = get_accounts(iam_token, iam_base_url, ou_id)
            all_accounts.extend(accounts)
            print(f"    Found {len(accounts)} account(s)")
        
        print()
        
        if all_accounts:
            print("=" * 70)
            print("ACCOUNT DETAILS:")
            print("=" * 70)
            
            for account in all_accounts:
                account_id = account.get('id')
                if account_id not in account_ids_set:  # Avoid duplicates
                    account_ids_set.add(account_id)
                    company = account.get('company', 'N/A')
                    email = account.get('email', 'N/A')
                    parent_id = account.get('parentId', 'N/A')
                    print(f"  Account ID: {account_id}")
                    print(f"    Company: {company}")
                    print(f"    Email: {email}")
                    print(f"    Parent OU: {parent_id}")
                    print()
            
            # Convert set to sorted list
            account_ids = sorted(list(account_ids_set))
            
            # Print summary
            print("=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Total Unique Accounts: {len(account_ids)}")
            print()
            print("Account IDs (comma-separated for .env file):")
            print(",".join(str(aid) for aid in account_ids))
            print()
            print("=" * 70)
            print("Add this line to your .env file:")
            print("=" * 70)
            print(f"FORTICLOUD_ACCOUNT_IDS={','.join(str(aid) for aid in account_ids)}")
            print("=" * 70)
            print()
            
        else:
            print("No accounts found or error retrieving accounts.")
        
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
