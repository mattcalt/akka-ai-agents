import requests
import os
import json
import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from typing import Optional, List, Tuple

# Cache for JWT token
_jwt_cache = {
    'token': None,
    'expires_at': 0
}

def get_github_app_token() -> Tuple[Optional[str], Optional[str]]:
    """Generate a JWT token for GitHub App authentication with caching."""
    try:
        # Check if we have a valid cached token
        current_time = int(time.time())
        if _jwt_cache['token'] and current_time < _jwt_cache['expires_at']:
            return _jwt_cache['token'], None

        # Get GitHub App configuration
        app_id = os.getenv('GITHUB_APP_ID')
        private_key_path = os.getenv('GITHUB_APP_PRIVATE_KEY')
        
        if not all([app_id, private_key_path]):
            return None, "Missing GitHub App configuration"

        # Read the private key file
        try:
            with open(private_key_path, 'rb') as key_file:
                private_key_bytes = key_file.read()
        except FileNotFoundError:
            return None, f"Private key file not found at: {private_key_path}"
        except Exception as e:
            return None, f"Error reading private key file: {str(e)}"

        # Generate JWT
        current_time = int(time.time())
        payload = {
            'iat': current_time,
            'exp': current_time + 600,  # JWT expiration time (10 minutes)
            'iss': app_id
        }

        # Load the private key
        try:
            private_key_obj = serialization.load_pem_private_key(
                private_key_bytes,
                password=None,
                backend=default_backend()
            )
        except Exception as e:
            return None, f"Error loading private key: {str(e)}"

        # Generate the JWT
        try:
            token = jwt.encode(
                payload,
                private_key_obj,
                algorithm='RS256'
            )
        except Exception as e:
            return None, f"Error encoding JWT: {str(e)}"

        # Cache the token
        _jwt_cache['token'] = token
        _jwt_cache['expires_at'] = current_time + 540  # Cache for 9 minutes

        return token, None
    except Exception as e:
        # Catch any unexpected errors during the process
        return None, f"Unexpected error generating JWT: {str(e)}"

# Cache for installation token
_installation_cache = {
    'token': None,
    'expires_at': 0
}

def get_installation_token(jwt_token: str) -> Tuple[Optional[str], Optional[str]]:
    """Get installation access token with caching."""
    try:
        # Check if we have a valid cached installation token
        current_time = int(time.time())
        if _installation_cache['token'] and current_time < _installation_cache['expires_at']:
            return _installation_cache['token'], None

        # Prepare headers for GitHub API request
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28" # Specify API version
        }
        
        # Get the installation ID
        installations_url = "https://api.github.com/app/installations"
        try:
            response = requests.get(installations_url, headers=headers, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            return None, f"Failed to get installations: {str(e)}"
        
        installations = response.json()
        if not installations:
            return None, "No installations found for this GitHub App"
        
        # Assuming the first installation is the correct one
        installation_id = installations[0]['id']
        
        # Get installation access token
        access_token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        try:
            response = requests.post(access_token_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return None, f"Failed to get installation token: {str(e)}"
        
        token_data = response.json()
        installation_token = token_data['token']
        expires_at_str = token_data['expires_at']
        
        # Cache the installation token
        _installation_cache['token'] = installation_token
        try:
            # Parse the expiration time string
            expires_at_dt = time.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%SZ")
            _installation_cache['expires_at'] = int(time.mktime(expires_at_dt)) - 60 # Cache until 1 minute before expiration
        except ValueError:
            # Fallback if time parsing fails, cache for a default duration (e.g., 50 minutes)
            _installation_cache['expires_at'] = current_time + 3000


        return installation_token, None
    except Exception as e:
        # Catch any unexpected errors
        return None, f"Unexpected error getting installation token: {str(e)}" 