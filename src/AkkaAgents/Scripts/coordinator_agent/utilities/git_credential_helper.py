#!/usr/bin/env python

import sys
import os
import requests
import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from typing import Optional, Tuple, Dict

# --- Token Management Logic (adapted from github_token_manager.py) ---
# Using global caches within this script's process lifetime
_jwt_cache: Dict[str, any] = {'token': None, 'expires_at': 0}
_installation_cache: Dict[str, any] = {'token': None, 'expires_at': 0}

def get_github_app_token() -> Tuple[Optional[str], Optional[str]]:
    """Generate a JWT token for GitHub App authentication with caching."""
    global _jwt_cache
    try:
        current_time = int(time.time())
        if _jwt_cache['token'] and current_time < _jwt_cache['expires_at']:
            return _jwt_cache['token'], None

        app_id = os.getenv('GITHUB_APP_ID')
        private_key_path = os.getenv('GITHUB_APP_PRIVATE_KEY')
        
        if not all([app_id, private_key_path]):
            return None, "Missing GitHub App configuration environment variables (GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)"

        try:
            with open(private_key_path, 'rb') as key_file:
                private_key_bytes = key_file.read()
        except FileNotFoundError:
            return None, f"Private key file not found at: {private_key_path}"
        except Exception as e:
            return None, f"Error reading private key file: {str(e)}"

        payload = {
            'iat': current_time,
            'exp': current_time + 600, 
            'iss': app_id
        }

        try:
            private_key_obj = serialization.load_pem_private_key(
                private_key_bytes, password=None, backend=default_backend()
            )
            token = jwt.encode(payload, private_key_obj, algorithm='RS256')
        except Exception as e:
            return None, f"Error generating JWT: {str(e)}"

        _jwt_cache['token'] = token
        _jwt_cache['expires_at'] = current_time + 540
        return token, None
    except Exception as e:
        return None, f"Unexpected error generating JWT: {str(e)}"

def get_installation_token(jwt_token: str) -> Tuple[Optional[str], Optional[str]]:
    """Get installation access token with caching."""
    global _installation_cache
    try:
        current_time = int(time.time())
        if _installation_cache['token'] and current_time < _installation_cache['expires_at']:
            return _installation_cache['token'], None

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        installations_url = "https://api.github.com/app/installations"
        try:
            response = requests.get(installations_url, headers=headers, timeout=10)
            response.raise_for_status()
            installations = response.json()
        except requests.exceptions.RequestException as e:
            return None, f"Failed to get installations: {str(e)}"
        
        if not installations:
            return None, "No installations found for this GitHub App"
        
        installation_id = installations[0]['id']
        
        access_token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        try:
            response = requests.post(access_token_url, headers=headers, timeout=10)
            response.raise_for_status()
            token_data = response.json()
        except requests.exceptions.RequestException as e:
            return None, f"Failed to get installation token: {str(e)}"
        
        installation_token = token_data['token']
        expires_at_str = token_data['expires_at']
        
        _installation_cache['token'] = installation_token
        try:
            expires_at_dt = time.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%SZ")
            _installation_cache['expires_at'] = int(time.mktime(expires_at_dt)) - 60
        except ValueError:
            _installation_cache['expires_at'] = current_time + 3000 # Fallback cache 50 mins

        return installation_token, None
    except Exception as e:
        return None, f"Unexpected error getting installation token: {str(e)}"

# --- Credential Helper Logic ---

def main():
    # Read input from Git (stdin)
    input_data = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            key, value = line.split('=', 1)
            input_data[key] = value
        except ValueError:
            pass # Ignore malformed lines

    # Check if it's for github.com via https
    if input_data.get('protocol') == 'https' and input_data.get('host') == 'github.com':
        # Get tokens
        jwt_token, jwt_error = get_github_app_token()
        if jwt_error:
            # Exit silently if token generation fails, Git will handle the auth failure
            sys.exit(1)
        
        installation_token, inst_error = get_installation_token(jwt_token)
        if inst_error:
            # Exit silently if token generation fails
            sys.exit(1)

        # Print credentials to stdout for Git
        print(f"username=x-access-token")
        print(f"password={installation_token}")
        sys.exit(0) # Indicate success

    # If not for github.com/https or if token fails, exit silently
    # Git will then fail authentication or try other methods
    sys.exit(1)

if __name__ == "__main__":
    # Basic error logging to stderr for debugging the helper itself, NOT for Git interaction
    # Git only cares about stdout.
    try:
        main()
    except Exception as e:
        print(f"Credential helper error: {e}", file=sys.stderr)
        sys.exit(1) 