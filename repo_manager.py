import git
import tempfile
import os
import re
from datetime import datetime

# Define a temporary directory base for cloning
TEMP_BASE_DIR = os.path.join(tempfile.gettempdir(), "securescan_repos")
os.makedirs(TEMP_BASE_DIR, exist_ok=True)

def is_github_url(path_or_url):
    """Checks if the input string looks like a GitHub repository URL."""
    # Matches common GitHub formats (https, git, ssh)
    github_regex = re.compile(r'^(https?|git|ssh):\/\/github\.com\/[^\/]+\/[^\/]+(\.git)?$')
    return bool(github_regex.match(path_or_url))

def clone_repo(repo_url):
    """
    Clones a remote repository into a unique temporary directory.

    Args:
        repo_url (str): The URL of the repository (e.g., https://github.com/owner/repo.git).

    Returns:
        tuple: (local_path, display_name) or (None, error_message) if cloning fails.
    """
    if not is_github_url(repo_url):
        return None, "Input is not a recognized GitHub URL."

    # Create a unique temporary directory for the clone
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    repo_name = os.path.basename(repo_url).replace(".git", "")
    local_path = os.path.join(TEMP_BASE_DIR, f"{repo_name}_{timestamp}")

    print(f"[REPO] Attempting to clone {repo_url} into {local_path}")
    try:
        # Clone the repository
        git.Repo.clone_from(repo_url, local_path)
        print(f"[REPO] Successfully cloned {repo_url}")
        
        # Determine the display name (repo/branch)
        repo = git.Repo(local_path)
        branch = repo.active_branch.name
        
        display_name = f"{repo_name}/{branch}"
        
        return local_path, display_name
    except git.GitCommandError as e:
        print(f"[REPO] Git command failed: {e}")
        # Clean up the failed directory creation if necessary
        if os.path.exists(local_path):
            cleanup_repo(local_path)
        return None, f"Git clone failed. Check the URL and ensure git is installed: {e}"
    except Exception as e:
        print(f"[REPO] An unexpected error occurred during cloning: {e}")
        return None, f"An unexpected error occurred during cloning: {e}"

def cleanup_repo(local_path):
    """
    Removes the cloned temporary directory.
    
    Args:
        local_path (str): The path to the temporary cloned repository.
    """
    if os.path.exists(local_path) and os.path.abspath(local_path).startswith(os.path.abspath(TEMP_BASE_DIR)):
        try:
            import shutil
            shutil.rmtree(local_path)
            print(f"[REPO] Successfully cleaned up temporary directory: {local_path}")
        except Exception as e:
            print(f"[REPO] Failed to cleanup directory {local_path}: {e}")
    else:
        print(f"[REPO] Skipping cleanup for non-temp or non-existent path: {local_path}")

if __name__ == '__main__':
    # Example usage:
    # 1. Test cloning a valid repo
    # local_path, error = clone_repo("https://github.com/Kavya132003/countdown-project.git")
    # if local_path:
    #     print(f"Cloned successfully to: {local_path}")
    #     # Do scan here
    #     cleanup_repo(local_path)
    # else:
    #     print(f"Cloning failed: {error}")
    pass