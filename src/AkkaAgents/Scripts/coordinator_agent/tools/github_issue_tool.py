from google.adk.tools import FunctionTool
import requests
import os
import json
from typing import Optional, List

# Moved caches and token functions to utilities
from ..utilities.github_token_manager import get_github_app_token, get_installation_token

def create_github_issue(title: str, body: str, labels: Optional[List[str]] = None) -> dict:
    """
    Creates a new GitHub issue in the configured repository using GitHub App authentication.
    The function handles JWT token generation, installation token retrieval, and issue creation.
    Returns a dictionary with status, issue URL, and error details if applicable.

    Args:
        title (str): The title of the issue
        body (str): The body/description of the issue
        labels (Optional[List[str]], optional): List of labels to apply to the issue. Defaults to None.

    Returns:
        dict: A dictionary containing:
            - status: "success" or "error"
            - issue_url: URL of the created issue (if successful)
            - issue_number: The number of the created issue (if successful)
            - error_message: Error details (if failed)
    """
    try:
        # Get GitHub repository
        github_repo = os.getenv('GITHUB_REPOSITORY')

        if not github_repo:
            return {
                "status": "error",
                "error_message": "Missing GITHUB_REPOSITORY environment variable."
            }

        # Get JWT token
        jwt_token, error = get_github_app_token()
        if error:
            return {
                "status": "error",
                "error_message": error
            }

        # Get installation token
        installation_token, error = get_installation_token(jwt_token)
        if error:
            return {
                "status": "error",
                "error_message": error
            }

        # Prepare the issue data
        issue_data = {
            "title": title,
            "body": body
        }
        
        if labels:
            issue_data["labels"] = labels

        # Make the API request with installation token
        headers = {
            "Authorization": f"Bearer {installation_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.post(
            f"https://api.github.com/repos/{github_repo}/issues",
            headers=headers,
            json=issue_data
        )

        if response.status_code == 201:
            return {
                "status": "success",
                "issue_url": response.json()["html_url"],
                "issue_number": response.json()["number"]
            }
        else:
            return {
                "status": "error",
                "error_message": f"Failed to create issue: {response.text}"
            }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating issue: {str(e)}"
        }

# Create the function tool
create_issue_tool = FunctionTool(func=create_github_issue) 