from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

def create_github_tools():
    """Create and wrap all GitHub tools for ADK integration."""
    github = GitHubAPIWrapper()
    toolkit = GitHubToolkit.from_github_api_wrapper(github)
    tools = toolkit.get_tools()
    
    # Debug: Print raw tools and their indexes
    print("\nGitHub Tools:")
    for idx, tool in enumerate(tools):
        print(f"Index {idx}: {tool.__class__.__name__} - {tool.name if hasattr(tool, 'name') else 'No name'}. Description: {tool.description if hasattr(tool, 'description') else 'No description'}")
    
    # Create a dictionary to store all wrapped tools
    wrapped_tools = {}
    
    # Get Issues
    get_issues_tool = tools[0]
    get_issues_tool.name = "github_get_issues"
    wrapped_tools["get_issues"] = LangchainTool(tool=get_issues_tool)
    
    # Get Issue
    get_issue_tool = tools[1]
    get_issue_tool.name = "github_get_issue"
    wrapped_tools["get_issue"] = LangchainTool(tool=get_issue_tool)
    
    # Comment on Issue
    comment_issue_tool = tools[2]
    comment_issue_tool.name = "github_comment_issue"
    wrapped_tools["comment_issue"] = LangchainTool(tool=comment_issue_tool)
    
    # List open pull requests
    list_prs_tool = tools[3]
    list_prs_tool.name = "github_list_prs"
    wrapped_tools["list_prs"] = LangchainTool(tool=list_prs_tool)
    
    # Get Pull Request
    get_pr_tool = tools[4]
    get_pr_tool.name = "github_get_pr"
    get_pr_tool.description = "Get details of a specific pull request"
    wrapped_tools["get_pr"] = LangchainTool(tool=get_pr_tool)
    
    # Overview of files in PR
    pr_files_tool = tools[5]
    pr_files_tool.name = "github_pr_files"
    wrapped_tools["pr_files"] = LangchainTool(tool=pr_files_tool)
    
    # Create Pull Request
    create_pr_tool = tools[6]
    create_pr_tool.name = "github_create_pr"
    wrapped_tools["create_pr"] = LangchainTool(tool=create_pr_tool)
    
    # List Pull Requests' Files
    list_pr_files_tool = tools[7]
    list_pr_files_tool.name = "github_list_pr_files"
    wrapped_tools["list_pr_files"] = LangchainTool(tool=list_pr_files_tool)
    
    # Create File
    create_file_tool = tools[8]
    create_file_tool.name = "github_create_file"
    wrapped_tools["create_file"] = LangchainTool(tool=create_file_tool)
    
    # Read File
    read_file_tool = tools[9]
    read_file_tool.name = "github_read_file"
    wrapped_tools["read_file"] = LangchainTool(tool=read_file_tool)
    
    # Update File
    update_file_tool = tools[10]
    update_file_tool.name = "github_update_file"
    wrapped_tools["update_file"] = LangchainTool(tool=update_file_tool)
    
    # Delete File
    delete_file_tool = tools[11]
    delete_file_tool.name = "github_delete_file"
    wrapped_tools["delete_file"] = LangchainTool(tool=delete_file_tool)
    
    # Overview of files in Main branch
    main_files_tool = tools[12]
    main_files_tool.name = "github_main_files"
    wrapped_tools["main_files"] = LangchainTool(tool=main_files_tool)
    
    # Overview of files in current branch
    current_files_tool = tools[13]
    current_files_tool.name = "github_current_files"
    wrapped_tools["current_files"] = LangchainTool(tool=current_files_tool)
    
    # List branches
    list_branches_tool = tools[14]
    list_branches_tool.name = "github_list_branches"
    wrapped_tools["list_branches"] = LangchainTool(tool=list_branches_tool)
    
    # Set active branch
    set_branch_tool = tools[15]
    set_branch_tool.name = "github_set_branch"
    wrapped_tools["set_branch"] = LangchainTool(tool=set_branch_tool)
    
    # Create branch
    create_branch_tool = tools[16]
    create_branch_tool.name = "github_create_branch"
    wrapped_tools["create_branch"] = LangchainTool(tool=create_branch_tool)
    
    # Get files from directory
    get_directory_tool = tools[17]
    get_directory_tool.name = "github_get_directory"
    wrapped_tools["get_directory"] = LangchainTool(tool=get_directory_tool)
    
    # Search issues and PRs
    search_issues_tool = tools[18]
    search_issues_tool.name = "github_search_issues"
    wrapped_tools["search_issues"] = LangchainTool(tool=search_issues_tool)
    
    # Search code
    search_code_tool = tools[19]
    search_code_tool.name = "github_search_code"
    wrapped_tools["search_code"] = LangchainTool(tool=search_code_tool)
    
    # Create review request
    create_review_tool = tools[20]
    create_review_tool.name = "github_create_review"
    wrapped_tools["create_review"] = LangchainTool(tool=create_review_tool)
    
    return wrapped_tools 