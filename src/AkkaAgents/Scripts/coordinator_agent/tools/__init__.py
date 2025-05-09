from typing import Dict
from google.adk.tools import FunctionTool
from google.adk.tools.langchain_tool import LangchainTool
from .github_tools import create_github_tools 
from .github_issue_tool import create_issue_tool

def create_all_tools() -> Dict[str, FunctionTool | LangchainTool]:
    """
    Initializes and collects all available tools for the Coding Agent, 
    configuring them with the session-specific workspace directory where needed.

    Args:
        workspace_dir (Path): The unique temporary workspace directory for this agent session.

    Returns:
        Dict[str, FunctionTool | LangchainTool]: A dictionary of all initialized tools.
    """
    all_tools = {}
    
    # GitHub Tools (Langchain based - assuming they don't need workspace_dir directly)
    # If create_github_tools needs workspace_dir, its signature must be updated.
    github_lc_tools = create_github_tools()
    all_tools.update(github_lc_tools)

    # GitHub Issue Tool (FunctionTool - doesn't need workspace_dir)
    all_tools["create_github_issue"] = create_issue_tool

    # Add other specific tools here if needed

    return all_tools

__all__ = ["create_all_tools"]
