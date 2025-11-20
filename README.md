SecureScan: Automated Credentials Leak Detector

SecureScan is a lightweight, local security tool designed to detect hardcoded secrets (API keys, passwords, tokens) in source code repositories. It consists of a Python Flask backend that performs the regex-based scanning and a React frontend dashboard for visualizing the findings.

🚀 Features

Local & Remote Scanning: Scan local directories or clone and scan public GitHub repositories.
Real-time Detection: Identifying secrets like AWS Access Keys, GitHub PATs, Stripe Keys, and more.
Custom Rule Management: Add, edit, and delete regex rules directly from the dashboard.
Interactive Dashboard: Visualizes findings with severity levels (Critical, High, Low) and file locations.
Secure & Private: Runs entirely on your local machine; no code is uploaded to external servers.

🛠️ Tech Stack

Backend: Python, Flask, Waitress, GitPython
Frontend: React, Tailwind CSS, Lucide React (via CDN)
Scanning Engine: Custom Python Regex Engine

📋 Prerequisites

Python 3.8+ installed on your machine.
Git installed and added to your system PATH.

⚙️ Installation

1. Clone the Repository
git clone [https://github.com/Kavya132003/SecureScan-Dashboard.git](https://github.com/Kavya132003/SecureScan-Dashboard)
cd SecureScan-Dashboard

2. Install Python Dependencies
Create a requirements.txt file if you haven't already, or install directly:
pip install flask flask-cors waitress GitPython

🏃‍♂️ Usage

1. Start the Backend API

The API handles the scanning logic and git operations. Open a terminal in the project root and run:
python api_service.py
You should see "🚀 SecureScan API Service starting..." indicating the server is running on http://127.0.0.1:8000.

2. Launch the Dashboard

Since the frontend is built as a standalone HTML file, you do not need a Node.js server.
Navigate to the project folder.
Double-click index.html to open it in your web browser.

3. Run a Scan

Remote Repo: Paste a GitHub URL (e.g., https://github.com/OWASP/NodeGoat.git) into the input field and click Scan.
Local Folder: Paste the absolute path to a folder on your computer.

📂 Project Structure
SecureScan/
├── api_service.py       # Main Flask application entry point
├── secret_scanner.py    # Core logic for regex pattern matching
├── git_cloner.py        # Utility to handle git cloning and cleanup
├── rules.json           # Configuration file storing detection rules
├── index.html           # The React Dashboard (Frontend)
└── README.md            # Project documentation

🛡️ Default Rules

The scanner comes pre-configured to detect:
AWS Access Key IDs
GitHub Personal Access Tokens
Generic API Keys & Secrets
Stripe Secret Keys
Database Passwords in config files
...and you can add more via the "Manage Rules" button!

📝 License
This project is open-source and available for educational and security testing purposes.