#!/usr/bin/env python3
"""
Generate Google OAuth2 refresh token for Google Ads API access.

Usage:
    uv run python scripts/generate_google_token.py

Requires:
    GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in config/credentials.env
    (or set as environment variables)
"""

import os
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

# Load credentials.env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "config" / "credentials.env")

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

if not CLIENT_ID or CLIENT_ID == "your_oauth_client_id_here":
    print("ERROR: Set GOOGLE_CLIENT_ID in config/credentials.env first.")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/adwords",
    "https://www.googleapis.com/auth/analytics.readonly",
]

params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "scope": " ".join(SCOPES),
    "response_type": "code",
    "access_type": "offline",
    "prompt": "consent",
}
auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)

print("\n=== Google OAuth2 Token Generator ===\n")
print("Step 1: Opening browser for authorization...")
print(f"URL: {auth_url}\n")
webbrowser.open(auth_url)

code = input("Step 2: Paste the authorization code here: ").strip()

# Exchange code for tokens
import urllib.request
import json

data = urlencode({
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "grant_type": "authorization_code",
}).encode()

req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

try:
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"\nERROR: {e.read().decode()}")
    sys.exit(1)

refresh_token = tokens.get("refresh_token")
if not refresh_token:
    print("\nERROR: No refresh_token returned. Make sure you used 'prompt=consent'.")
    sys.exit(1)

print(f"\n✅ Success! Add this to config/credentials.env:\n")
print(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")
