#!/usr/bin/env python3
"""Refresh TikTok token"""
import sys
sys.path.insert(0, '.')
from tiktok_api import refresh_token, load_token

print("="*50)
print("Token Refresh Test")
print("="*50)

token = load_token()
if token:
    refresh = token.get("refresh_token", "")
    print(f"Refresh token: {refresh[:30]}..." if refresh else "No refresh token")
    print()
    print("Calling refresh_token()...")
    new_token = refresh_token()
    
    if new_token:
        print()
        print("SUCCESS! New token:")
        print(f"  access_token: {new_token.get('access_token', 'N/A')[:30]}...")
        print(f"  expires_in: {new_token.get('expires_in', 'N/A')} seconds")
    else:
        print("FAILED to refresh - need re-authorization")
else:
    print("No token file found")