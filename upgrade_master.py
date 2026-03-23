#!/usr/bin/env python3
"""
KISWARM7.0 - Master System Upgrade Script
Downloads complete system from GitHub and deploys
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Configuration
KISWARM_DIR = Path('/opt/kiswarm7')
VENV_DIR = KISWARM_DIR / 'venv'
LOGS_DIR = KISWARM_DIR / 'logs'
DATA_DIR = KISWARM_DIR / 'data'
GITHUB_REPO = 'https://github.com/Baronki/KISWARM7.git'

print("🜂 KISWARM7.0 MASTER UPGRADE")
print("=" * 50)

# Step 1: Update repository
print("\n1. Updating repository...")
os.chdir(KISWARM_DIR)
subprocess.run(['git', 'fetch', 'origin'], capture_output=True)
subprocess.run(['git', 'reset', '--hard', 'origin/main'], capture_output=True)
subprocess.run(['git', 'clean', '-fd'], capture_output=True)
print("   ✓ Repository updated")

# Step 2: Install dependencies
print("\n2. Installing dependencies...")
venv_python = str(VENV_DIR / 'bin' / 'python')
venv_pip = str(VENV_DIR / 'bin' / 'pip')
subprocess.run([venv_pip, 'install', '--quiet', 'flask', 'flask-cors', 
                'requests', 'schedule', 'psutil'], capture_output=True)
print("   ✓ Dependencies installed")

# Step 3: Create directories
print("\n3. Creating directories...")
for d in [LOGS_DIR, DATA_DIR, DATA_DIR/'scheduler', DATA_DIR/'backups', 
          DATA_DIR/'sync', KISWARM_DIR/'deployed']:
    d.mkdir(parents=True, exist_ok=True)
print("   ✓ Directories created")

# Step 4: Stop old services
print("\n4. Stopping old services...")
subprocess.run(['systemctl', 'stop', 'glm-bridge'], capture_output=True)
subprocess.run(['systemctl', 'stop', 'glm-autonomous'], capture_output=True)
subprocess.run(['pkill', '-f', 'python.*5002'], capture_output=True)
print("   ✓ Services stopped")

# Step 5: Deploy new master API
print("\n5. Deploying master API...")
MASTER_API = KISWARM_DIR / 'app_kiswarm_master.py'

# Check if master API exists in repo
if (KISWARM_DIR / 'app_kiswarm_master.py').exists():
    print("   ✓ Master API found in repository")
else:
    # Download from GitHub raw
    import urllib.request
    url = 'https://raw.githubusercontent.com/Baronki/KISWARM7/main/app_kiswarm_master.py'
    try:
        urllib.request.urlretrieve(url, MASTER_API)
        print("   ✓ Master API downloaded")
    except Exception as e:
        print(f"   ⚠ Could not download master API: {e}")

# Step 6: Create systemd service
print("\n6. Creating systemd service...")
SERVICE_FILE = Path('/etc/systemd/system/kiswarm-master.service')
SERVICE_CONTENT = '''[Unit]
Description=KISWARM7.0 Master Autonomous System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
Environment="FLASK_PORT=5002"
ExecStart=/opt/kiswarm7/venv/bin/python /opt/kiswarm7/app_kiswarm_master.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/kiswarm7/logs/kiswarm_master.log
StandardError=append:/opt/kiswarm7/logs/kiswarm_master_error.log

[Install]
WantedBy=multi-user.target
'''
SERVICE_FILE.write_text(SERVICE_CONTENT)

# Also ensure ngrok service
NGROK_SERVICE = Path('/etc/systemd/system/ngrok.service')
if not NGROK_SERVICE.exists():
    NGROK_CONTENT = '''[Unit]
Description=Ngrok Tunnel for KISWARM7
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http 5002 --log=stdout
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
'''
    NGROK_SERVICE.write_text(NGROK_CONTENT)

subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
subprocess.run(['systemctl', 'enable', 'kiswarm-master'], capture_output=True)
subprocess.run(['systemctl', 'enable', 'ngrok'], capture_output=True)
print("   ✓ Services configured")

# Step 7: Start services
print("\n7. Starting services...")
subprocess.run(['systemctl', 'start', 'kiswarm-master'], capture_output=True)

import time
time.sleep(5)

# Check health
try:
    import urllib.request
    response = urllib.request.urlopen('http://localhost:5002/health', timeout=5)
    health = json.loads(response.read().decode())
    print(f"   ✓ Master API: {health.get('status', 'unknown')}")
    print(f"   ✓ Modules: {health.get('modules', 0)}")
except Exception as e:
    print(f"   ⚠ Health check: {e}")

subprocess.run(['systemctl', 'start', 'ngrok'], capture_output=True)
time.sleep(5)

# Step 8: Initialize identity
print("\n8. Initializing identity...")
try:
    response = urllib.request.urlopen('http://localhost:5002/api/identity', timeout=5)
    identity = json.loads(response.read().decode())
    print(f"   ✓ {identity.get('message', 'Initialized')}")
except Exception as e:
    print(f"   ⚠ Identity: {e}")

# Step 9: Start autonomous mode
print("\n9. Starting autonomous mode...")
try:
    req = urllib.request.Request(
        'http://localhost:5002/api/autonomous/start',
        data=b'{}',
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    result = json.loads(response.read().decode())
    print(f"   ✓ Status: {result.get('status', 'unknown')}")
except Exception as e:
    print(f"   ⚠ Autonomous: {e}")

# Step 10: Final status
print("\n10. Final status...")
try:
    response = urllib.request.urlopen('http://localhost:5002/api/status', timeout=5)
    status = json.loads(response.read().decode())
    print(f"   Identity: {status.get('identity', {}).get('name', 'unknown')}")
    print(f"   Modules: {status.get('modules', {}).get('loaded', 0)} loaded")
    print(f"   Autonomous: {status.get('autonomous', {}).get('running', False)}")
except Exception as e:
    print(f"   ⚠ Status: {e}")

# Get ngrok URL
try:
    response = urllib.request.urlopen('http://localhost:4040/api/tunnels', timeout=5)
    tunnels = json.loads(response.read().decode())
    if tunnels.get('tunnels'):
        public_url = tunnels['tunnels'][0].get('public_url', 'unknown')
        print(f"\n   Public URL: {public_url}")
except:
    pass

print("\n" + "=" * 50)
print("🜂 KISWARM7.0 UPGRADE COMPLETE")
print("=" * 50)
