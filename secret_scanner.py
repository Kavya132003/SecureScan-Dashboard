import re
import os
from collections import namedtuple

# Named tuple for clear representation of a finding
Finding = namedtuple('Finding', ['secret_type', 'file', 'line', 'excerpt', 'severity'])

class SecretScanner:
    """
    Core class for scanning a directory for secrets based on regex rules.
    """
    def __init__(self, rules):
        """
        Initializes the scanner with a dictionary of rules.
        
        Args:
            rules (dict): A dictionary where keys are rule IDs (secret_type) and 
                          values are dictionaries containing 'pattern' (regex) and 'severity'.
        """
        self.rules = rules
        self.compiled_rules = {}
        self._compile_rules()
        print(f"[SCANNER] Initialized with {len(self.rules)} rules.")

    def _compile_rules(self):
        """
        Compiles the regex patterns for efficiency and stores them.
        """
        for secret_type, rule_data in self.rules.items():
            try:
                # Compile the regex pattern
                pattern = rule_data['pattern']
                self.compiled_rules[secret_type] = re.compile(pattern)
            except re.error as e:
                print(f"[ERROR] Failed to compile regex for rule '{secret_type}': {e}")

    def _scan_file(self, filepath):
        """
        Scans a single file for secrets matching any compiled rule.

        Args:
            filepath (str): The full path to the file to scan.

        Returns:
            list: A list of Finding named tuples.
        """
        findings = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Check each line against every compiled rule
                    for secret_type, pattern_compiled in self.compiled_rules.items():
                        match = pattern_compiled.search(line)
                        if match:
                            # Truncate the excerpt to 80 characters for the display
                            excerpt = line.strip()
                            if len(excerpt) > 80:
                                excerpt = excerpt[:77] + '...'

                            # Create a Finding object
                            finding = Finding(
                                secret_type=secret_type,
                                # Use relative path for cleaner output in the UI
                                file=filepath, 
                                line=line_num,
                                excerpt=excerpt,
                                severity=self.rules[secret_type].get('severity', 'Unknown')
                            )
                            findings.append(finding)
        except Exception as e:
            # Skip files that cannot be read (e.g., binaries, permission issues)
            print(f"[WARNING] Could not read file {filepath}: {e}")
            
        return findings

    def scan_directory(self, root_dir):
        """
        Recursively scans all files in a directory, ignoring common paths.

        Args:
            root_dir (str): The path to the directory to scan.

        Returns:
            list: A list of all Finding named tuples found.
        """
        all_findings = []
        
        # Define common directories/files to ignore to improve performance and relevance
        ignored_dirs = ['.git', '__pycache__', 'node_modules', 'venv', '.vscode']
        ignored_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bin', '.exe', '.dll', '.zip', '.tar', '.gz']
        
        # Normalize the root directory path
        root_dir = os.path.abspath(root_dir)

        # Check if the directory exists
        if not os.path.isdir(root_dir):
            raise FileNotFoundError(f"The directory or cloned repository path was not found: {root_dir}")

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Modify dirnames in place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
            
            for filename in filenames:
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension in ignored_extensions:
                    continue
                    
                filepath = os.path.join(dirpath, filename)
                
                # Make the path relative to the root_dir for cleaner UI display
                relative_filepath = os.path.relpath(filepath, root_dir)
                
                # Perform the scan on the file
                file_findings = self._scan_file(filepath)
                
                # Update findings with the relative path before adding to the main list
                updated_findings = [
                    finding._replace(file=relative_filepath) 
                    for finding in file_findings
                ]

                all_findings.extend(updated_findings)

        return all_findings

if __name__ == '__main__':
    # --- Mock Rules for Testing ---
    mock_rules = {
        "AWS_KEY": {
            "pattern": r"(A3[A-Z0-9]|AKIA|ASIA|AGIA|AROA)[A-Z0-9]{16,}",
            "severity": "Critical",
            "description": "AWS Access Key ID"
        },
        "SECRET_KEY": {
            "pattern": r"(SECRET|API|TOKEN)[\s_=\-:]+['\"]([a-zA-Z0-9+/=]{16,})['\"]",
            "severity": "High",
            "description": "Generic API/Secret Key"
        },
        "PASSWORD_IN_CONFIG": {
            "pattern": r"password[\s_=\-:]+['\"]([a-zA-Z0-9]{8,})['\"]",
            "severity": "Low",
            "description": "Password found in configuration file"
        }
    }
    
    # --- Mock Directory Setup for Testing ---
    MOCK_DIR = 'mock_repo'
    os.makedirs(MOCK_DIR, exist_ok=True)
    with open(os.path.join(MOCK_DIR, 'config.ini'), 'w') as f:
        f.write("database_url=db.local\n")
        f.write("db_password = 'MySecretPassword123'\n") # Should find
    with open(os.path.join(MOCK_DIR, 'keys.txt'), 'w') as f:
        f.write("API_KEY=a_key_that_is_too_short\n") # Should not find
        f.write("AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE\n") # Should find
        f.write("another_secret = 'this_is_a_test_token1234567890'\n") # Should find
        f.write("just_text_no_secrets\n")
        
    print(f"\n--- Testing SecretScanner on '{MOCK_DIR}' ---")
    scanner = SecretScanner(mock_rules)
    findings = scanner.scan_directory(MOCK_DIR)
    
    print(f"\n--- Results ({len(findings)} Total) ---")
    for f in findings:
        print(f"[{f.severity.upper():<8}] {f.secret_type:<20} in {f.file}:{f.line} -> {f.excerpt}")

    # Clean up mock directory (optional)
    try:
        import shutil
        shutil.rmtree(MOCK_DIR)
        print(f"\nCleaned up {MOCK_DIR}")
    except OSError as e:
        print(f"Error during cleanup: {e}")