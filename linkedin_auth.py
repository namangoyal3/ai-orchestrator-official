"""
linkedin_auth.py
────────────────
One-time helper to exchange a LinkedIn OAuth 2.0 authorization code for an
access token. Run this ONCE to get your LINKEDIN_ACCESS_TOKEN.

Steps:
  1. Create a LinkedIn app at https://www.linkedin.com/developers/apps
  2. Add "Sign In with LinkedIn" + "Share on LinkedIn" products
  3. Set redirect URI to: http://localhost:8080/callback
  4. Run: python linkedin_auth.py
  5. Paste the token into your .env file

LinkedIn OAuth docs:
  https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
"""

from __future__ import annotations

import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

load_dotenv()

REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "openid profile email w_member_social"

_auth_code: str | None = None


def _require_credentials() -> tuple[str, str]:
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set before running linkedin_auth.py."
        )
    return client_id, client_secret


def _build_auth_url(client_id: str) -> str:
    return (
        "https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")

    def log_message(self, format, *args):
        pass  # suppress server logs


def get_access_token() -> None:
    global _auth_code

    client_id, client_secret = _require_credentials()
    auth_url = _build_auth_url(client_id)

    print(f"\nOpening browser for LinkedIn authorization…\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    print("Waiting for callback on http://localhost:8080/callback …")
    server.handle_request()

    if not _auth_code:
        print("ERROR: No authorization code received.")
        return

    # Exchange code for token
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    token_data = resp.json()

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", "unknown")

    print("\n" + "=" * 60)
    print("SUCCESS! Add this to your .env file:")
    print(f"\nLINKEDIN_ACCESS_TOKEN={access_token}\n")
    print(f"Token expires in: {expires_in} seconds (~{int(expires_in) // 86400} days)")
    print("=" * 60)

    # Also fetch person URN
    me_resp = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if me_resp.ok:
        person_id = me_resp.json().get("id")
        print(f"\nLINKEDIN_PERSON_URN=urn:li:person:{person_id}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    get_access_token()
