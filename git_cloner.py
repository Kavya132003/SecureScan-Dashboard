import os
import shutil
import datetime
from git.repo import Repo
from git.exc import GitCommandError
from urllib.parse import urlparse

# Global temporary directory for cloned repos
TEMP_DIR = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp', 'securescan_repos')

def clone_repo(repo_url):
    """
    Clones a Git repository from a URL into a unique temporary folder.

    Args:
        repo_url (str): The HTTPS URL of the Git repository.

    Returns:
        str: The path to the newly cloned local repository directory.
        
    Raises:
        Exception: If the Git command or file system operation fails.
    """
    # 1. Parse the repo name from the URL
    path = urlparse(repo_url).path
    repo_name = os.path.basename(path)
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]

    # 2. Create a unique path for the cloned repo
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    local_repo_path = os.path.join(TEMP_DIR, f"{repo_name}_{timestamp}")

    print(f"[REPO] Attempting to clone {repo_url} into {local_repo_path}")

    try:
        # Create the temporary directory if it doesn't exist
        os.makedirs(TEMP_DIR, exist_ok=True)

        # 3. Perform the clone operation (shallow clone for speed is disabled 
        #    here for full repository scan capability, but could be added later)
        Repo.clone_from(
            repo_url, 
            local_repo_path,
            progress=None, # Suppress clone progress output
            multi_options=['--depth 1'] # Shallow clone for speed, fetching only the latest commit
        )
        print(f"[REPO] Successfully cloned {repo_url}")
        return local_repo_path
        
    except GitCommandError as e:
        # Catch specific Git errors (like 'Repository not found')
        error_message = f"Git command failed during clone: {e.stderr.strip()}"
        print(f"[REPO] Git command failed: {error_message}")
        # Crucial: Clean up the half-cloned directory on failure
        if os.path.exists(local_repo_path):
            cleanup_repo(local_repo_path)
        raise Exception(error_message)
    except Exception as e:
        # Catch other exceptions (e.g., directory creation, permissions)
        error_message = f"An unexpected error occurred during cloning: {e}"
        print(f"[REPO] General error: {error_message}")
        raise Exception(error_message)

def cleanup_repo(local_repo_path):
    """
    Deletes the local repository directory.

    Args:
        local_repo_path (str): The path to the local repository.
    """
    if os.path.exists(local_repo_path):
        try:
            shutil.rmtree(local_repo_path)
            print(f"[REPO] Successfully cleaned up {local_repo_path}")
        except OSError as e:
            # Handle permissions issues or files being in use
            print(f"[REPO] Error during cleanup of {local_repo_path}: {e}")
            pass # Continue execution, cleanup might be deferred or manual

# Example usage (for testing) is removed, as it's typically used by api_service.py