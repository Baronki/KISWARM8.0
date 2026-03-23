# KISWARM Zero-Failure Colab Deployment v6.3.4

## 🎯 Overview

This deployment creates a **fully autonomous KISWARM node** in Google Colab with:
- ✅ Automatic Ollama installation
- ✅ 5-Layer Mesh redundancy
- ✅ Sentinel Watch email monitoring
- ✅ Unique persistent node identity
- ✅ Zero single point of failure

---

## 📋 Prerequisites

### Gmail App Password (for Layer 4 - Email Beacon)

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Search for "App passwords" or go to https://myaccount.google.com/apppasswords
4. Create a new App Password:
   - App name: `KISWARM Sentinel Watch`
   - Copy the generated 16-character password (e.g., `abcd efgh ijkl mnop`)
5. **Keep this password safe** - you'll need it for the deployment

---

## 🚀 Colab Deployment Cells

### Cell 1: Environment Setup

```python
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM COLAB ENVIRONMENT SETUP v6.3.4
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys

# Set environment flags
os.environ['COLAB_GPU'] = '1'

# Install required packages
!pip install -q flask flask-cors requests pyngrok

print("="*60)
print("KISWARM Colab Environment Ready")
print(f"Python: {sys.version}")
print("="*60)
```

---

### Cell 2: Download Standalone Installer

```python
# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD STANDALONE ZERO-FAILURE INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════

import urllib.request

# Download standalone installer (includes embedded Sentinel Watch)
installer_url = "https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/zero_failure_mesh_installer_standalone.py"
installer_path = "/content/zero_failure_mesh_installer_standalone.py"

try:
    urllib.request.urlretrieve(installer_url, installer_path)
    print(f"[OK] Downloaded installer to {installer_path}")
except Exception as e:
    print(f"[!] Could not download from GitHub: {e}")
    print("[!] Creating installer inline...")

    # Create installer inline if download fails
    # (This would contain the full installer code)
    print("[!] Please upload the installer file manually")
```

---

### Cell 3: Install Ollama

```python
# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA INSTALLATION FOR COLAB
# ═══════════════════════════════════════════════════════════════════════════════

import subprocess
import time

print("="*60)
print("Installing Ollama for Google Colab...")
print("="*60)

# Method 1: Official install script
print("\n[1/3] Trying official Ollama install script...")
result = subprocess.run(
    "curl -fsSL https://ollama.com/install.sh | sh",
    shell=True, capture_output=True, text=True, timeout=180
)

if result.returncode == 0:
    print("[OK] Ollama installed via official script")
else:
    print(f"[!] Official script failed: {result.stderr[:100]}")

    # Method 2: Direct binary download
    print("\n[2/3] Trying direct binary download...")
    subprocess.run("mkdir -p /usr/local/bin", shell=True)

    result = subprocess.run(
        "curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o /usr/local/bin/ollama",
        shell=True, capture_output=True, text=True, timeout=120
    )

    if result.returncode == 0:
        subprocess.run("chmod +x /usr/local/bin/ollama", shell=True)
        print("[OK] Ollama binary downloaded")
    else:
        print(f"[!] Binary download failed: {result.stderr[:100]}")

# Verify installation
print("\n[3/3] Verifying Ollama installation...")
result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)

if result.returncode == 0:
    print(f"[OK] Ollama version: {result.stdout.strip()}")
else:
    print(f"[!] Ollama verification failed")

# Start Ollama server
print("\n[4/4] Starting Ollama server...")
subprocess.Popen(
    ["ollama", "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Wait for server to start
for i in range(30):
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] Ollama server started after {i+1} seconds")
            break
    except:
        pass
    time.sleep(1)
else:
    print("[!] Ollama server did not start within 30 seconds")

print("="*60)
print("Ollama Installation Complete")
print("="*60)
```

---

### Cell 4: Deploy KISWARM

```python
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM ZERO-FAILURE DEPLOYMENT
# ═══════════════════════════════════════════════════════════════════════════════

import sys
sys.path.insert(0, '/content')

from zero_failure_mesh_installer_standalone import zero_failure_deploy

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTANT: Email Password Configuration
# ═══════════════════════════════════════════════════════════════════════════════
#
# To enable Layer 4 (Email Beacon / Sentinel Watch):
# 1. Generate a Gmail App Password at https://myaccount.google.com/apppasswords
# 2. Replace "YOUR_GMAIL_APP_PASSWORD" below with your 16-character app password
# 3. Remove spaces from the password (e.g., "abcdefghijklmnop")
#
# Without an email password, the system will still work but Layer 4 will be inactive.
# ═══════════════════════════════════════════════════════════════════════════════

EMAIL_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"  # Replace with your Gmail App Password

# Execute deployment
result = zero_failure_deploy(
    email_password=EMAIL_PASSWORD,
    skip_ollama=False,   # We already installed Ollama
    skip_models=False    # Pull default models
)

# Display results
print("\n" + "="*60)
print("DEPLOYMENT RESULT:")
print("="*60)
print(f"Status: {result['status']}")
print(f"Node ID: {result['node_id']}")
print(f"Ollama: {'Available' if result.get('has_ollama') else 'Not Available'}")
print(f"Mesh Connections: {len(result['mesh_connections'])}")
for conn in result['mesh_connections']:
    print(f"  • {conn['layer']}: {conn['endpoint']}")
print(f"Sentinel Watch: {result['sentinel_watch']}")
print(f"Warnings: {len(result['warnings'])}")
print(f"Errors: {len(result['errors'])}")
print("="*60)
```

---

### Cell 5: Pull KISWARM Models (Optional)

```python
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM MODEL PULLING
# ═══════════════════════════════════════════════════════════════════════════════

import subprocess

# Primary KISWARM models
MODELS = [
    "llama3.1:8b",           # General purpose
    "qwen2.5:14b",           # Knowledge/Reasoning
    "nomic-embed-text",      # Embeddings for RAG
]

print("="*60)
print("Pulling KISWARM Models")
print("="*60)

for model in MODELS:
    print(f"\n[>] Pulling {model}...")
    result = subprocess.run(
        ["ollama", "pull", model],
        capture_output=True, text=True, timeout=600
    )
    if result.returncode == 0:
        print(f"[OK] {model} pulled successfully")
    else:
        print(f"[!] Failed to pull {model}: {result.stderr[:100]}")

print("\n" + "="*60)
print("Model Pulling Complete")
print("="*60)

# List installed models
print("\nInstalled Models:")
result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
print(result.stdout)
```

---

### Cell 6: Test Sentinel Watch (Optional)

```python
# ═══════════════════════════════════════════════════════════════════════════════
# SENTINEL WATCH TEST
# ═══════════════════════════════════════════════════════════════════════════════

# To test the Sentinel Watch (Layer 4):
#
# 1. From any email client, send an email to: sahgreenki@gmail.com
# 2. Use one of these subject lines:
#
#    [KISWARM-CMD] ALL: REPORT STATUS
#    → All nodes will reply with their status
#
#    [KISWARM-CMD] KISWARM-XXXXXXXX: RESTART TUNNEL
#    → Specific node will restart its tunnel
#
#    [KISWARM-CMD] ALL: DISCOVER NODES
#    → All nodes will announce themselves
#
# 3. Check the inbox for [KISWARM-ACK] replies from nodes
#
# ═══════════════════════════════════════════════════════════════════════════════

print("="*60)
print("Sentinel Watch Test Instructions")
print("="*60)
print("""
To test Layer 4 (Email Beacon):

1. Send an email to: sahgreenki@gmail.com
2. Use subject: [KISWARM-CMD] ALL: REPORT STATUS
3. Wait 60 seconds for the node to check inbox
4. Check for [KISWARM-ACK] reply in the same inbox

Your Node ID is shown in the deployment result above.
""")
print("="*60)
```

---

## 📊 5-Layer Architecture Reference

| Layer | Name | Availability | Description |
|-------|------|--------------|-------------|
| 0 | Local Master API | Development only | Z.ai environment (blocked externally) |
| 1 | Gemini CLI Mesh Router | Session-based | Google Cloud relay |
| 2 | GitHub Actions Mesh Router | 99.99% | 24/7 permanent infrastructure |
| 3 | P2P Direct Mesh | Variable | Distributed mesh |
| 4 | Email Beacon (Sentinel Watch) | 99.9% | Email-based command & control |

---

## 🔗 Repository Redundancy

| Repository | Administrator | Purpose |
|------------|---------------|---------|
| **Baronki/KISWARM6.0** | Super Z (Z.ai) | Primary development, all 75 modules |
| **Baronki/KISWARMAGENTS1.0** | Gemini CLI (Local) | Model agents, alternative mesh |

---

## ✅ Success Criteria

After deployment, verify:

- [ ] Node ID generated (e.g., `KISWARM-A1B2C3D4`)
- [ ] At least 1 mesh connection active
- [ ] Ollama server running
- [ ] (Optional) Sentinel Watch active if email password provided

---

## 🆘 Troubleshooting

### Ollama Installation Fails
```python
# Try alternative installation
!apt-get update && apt-get install -y curl
!curl -fsSL https://ollama.com/install.sh | sh
```

### Email Beacon Not Working
1. Verify you're using an **App Password**, not your regular Gmail password
2. Check that 2-Factor Authentication is enabled
3. Ensure the password has no spaces

### No Mesh Connections
This is normal in Colab - the node operates in standalone mode with Layer 4 (Email) as the ultimate fallback.

---

*Version: 6.3.4 STANDALONE_ZERO_FAILURE*
*Classification: MILITARY-GRADE INFRASTRUCTURE*
