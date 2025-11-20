from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime

# --- Import Custom Modules ---
try:
    from secret_scanner import SecretScanner
    from git_cloner import clone_repo, cleanup_repo
except ImportError as e:
    print(f"FATAL: Missing dependency module. Ensure secret_scanner.py and git_cloner.py exist.\nError: {e}")
    sys.exit(1)

app = Flask('api_service')
CORS(app) # Enable CORS for frontend communication

RULES_FILE = 'rules.json'

# --- Rules Management Helpers ---

def load_rules():
    """Loads rules from the JSON file or returns defaults if missing."""
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: rules.json is invalid. Using defaults.")
    
    # Fallback defaults if file doesn't exist or is broken
    return {
        "AWS_KEY": {
            "pattern": r"(A3[A-Z0-9]|AKIA|ASIA|AGIA|AROA)[A-Z0-9]{16,}",
            "severity": "Critical",
            "description": "AWS Access Key ID"
        },
        "SECRET_KEY": {
            "pattern": r"(SECRET|API|TOKEN|KEY)[\s_=\-:]+['\"]([a-zA-Z0-9+/=]{16,})['\"]",
            "severity": "High",
            "description": "Generic API/Secret Key"
        }
    }

def save_rules(rules):
    """Saves the rules dictionary to rules.json."""
    try:
        with open(RULES_FILE, 'w') as f:
            json.dump(rules, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving rules: {e}")
        return False

# Initialize scanner with current rules
scanner = SecretScanner(load_rules())

# --- API Endpoints ---

@app.route('/api/v1/scan', methods=['POST'])
def scan_endpoint():
    """
    Handles scanning requests.
    Accepts 'target' (URL or local path) OR 'directory_path' (legacy support).
    """
    data = request.get_json()
    
    # FIX: Support both 'target' and 'directory_path' to prevent 400 errors
    scan_target = data.get('target') or data.get('directory_path')

    if not scan_target:
        return jsonify({"error": "Missing scan target (URL or path) in request body."}), 400

    print(f"[API] Received request to scan: {scan_target}")
    
    local_repo_path = None
    # Refresh rules before scanning to pick up any changes
    scanner.rules = load_rules()
    scanner._compile_rules()

    try:
        # 1. Handle Remote GitHub URL
        if scan_target.startswith(('http://', 'https://')):
            # Clone to temp folder
            local_repo_path = clone_repo(scan_target)
            path_to_scan = local_repo_path
            print(f"[SCAN] Scanning cloned repo at: {local_repo_path}")

        # 2. Handle Local Directory
        elif os.path.isdir(scan_target):
            path_to_scan = scan_target
            print(f"[SCAN] Scanning local directory: {path_to_scan}")

        else:
            return jsonify({"error": f"Invalid target. Must be a URL or valid local path: {scan_target}"}), 400

        # 3. Perform Scan
        findings = scanner.scan_directory(path_to_scan)
        
        # Convert findings to dictionaries
        findings_json = [f._asdict() for f in findings]

        return jsonify({
            "status": "success",
            "target": scan_target,
            "scanned_path": local_repo_path if local_repo_path else scan_target,
            "findings_count": len(findings_json),
            "findings": findings_json,
            "timestamp": datetime.now().isoformat()
        })

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ERROR] Scan failed: {e}")
        # Return 500 but with a clean error message for the frontend
        return jsonify({"error": f"Scan execution failed: {str(e)}"}), 500
    finally:
        # 4. Cleanup Temp Files
        if local_repo_path:
            cleanup_repo(local_repo_path)

# --- Rule Management Endpoints ---

@app.route('/api/v1/rules', methods=['GET'])
def get_rules():
    """Returns all current rules."""
    return jsonify({"status": "success", "rules": load_rules()})

@app.route('/api/v1/rules/<rule_id>', methods=['POST'])
def add_update_rule(rule_id):
    """Adds or updates a rule."""
    data = request.get_json()
    pattern = data.get('pattern')
    severity = data.get('severity', 'High')
    description = data.get('description', '')

    if not pattern:
        return jsonify({"error": "Missing 'pattern' field"}), 400

    rules = load_rules()
    rules[rule_id] = {
        "pattern": pattern,
        "severity": severity,
        "description": description
    }
    
    if save_rules(rules):
        return jsonify({"status": "success", "message": f"Rule '{rule_id}' saved."})
    else:
        return jsonify({"error": "Failed to save rule to disk."}), 500

@app.route('/api/v1/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Deletes a rule."""
    rules = load_rules()
    if rule_id in rules:
        del rules[rule_id]
        save_rules(rules)
        return jsonify({"status": "success", "message": f"Rule '{rule_id}' deleted."})
    else:
        return jsonify({"error": "Rule not found."}), 404

# --- Server Startup ---

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 8000
    print("---------------------------------------------------------")
    print("🚀 SecureScan API Service starting...")
    print(f"   Listening on http://{HOST}:{PORT}")
    print(f"   Example Scan URL: https://github.com/OWASP/NodeGoat.git") 
    print("---------------------------------------------------------")
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)