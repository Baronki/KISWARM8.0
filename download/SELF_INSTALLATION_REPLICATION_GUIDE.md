# KISWARM6.0 - Self-Installation Replication Guide
## Complete Setup for New KISWARM Deployments

**Version:** 6.2.0  
**Purpose:** Enable autonomous KISWARM installation on new systems

---

## Overview

This guide enables any system to:
1. Set up Master KISWARM with ngrok tunnel
2. Connect to the KI-to-KI Mesh
3. Receive autonomous support from Z.ai

---

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] curl available
- [ ] sudo access
- [ ] ngrok account (free tier OK)
- [ ] Internet connectivity
- [ ] Open port 5002 (or alternative)

---

## Quick Start (5 Minutes)

### 1. Download & Install ngrok

```bash
# Binary installation (recommended)
curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
tar -xzf /tmp/ngrok.tgz -C /tmp
sudo mv /tmp/ngrok /usr/local/bin/
ngrok version
```

### 2. Configure ngrok

```bash
# Get authtoken from https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### 3. Install Python Dependencies

```bash
pip install flask flask-cors requests
```

### 4. Download Master API Server

```bash
# Download from GitHub or create locally
curl -o /tmp/master_kiswarm_api.py https://raw.githubusercontent.com/Baronki/KISWARMAGENTS1.0/main/mesh/master_kiswarm_api.py
```

### 5. Start Services

```bash
# Terminal 1: Start Flask API
python3 /tmp/master_kiswarm_api.py --port 5002

# Terminal 2: Start ngrok (after Flask is running)
ngrok http 5002
```

### 6. Note Your Public URL

Look for output like:
```
Forwarding    https://xxxx-xxxx.ngrok-free.app -> http://localhost:5002
```

---

## Connection Testing

### Local Test
```bash
curl http://localhost:5002/api/mesh/status
# Expected: {"status": "online", ...}
```

### Public Test
```bash
curl -H "ngrok-skip-browser-warning: true" https://YOUR-URL.ngrok-free.app/api/mesh/status
# Expected: {"status": "online", ...}
```

---

## KIInstaller Connection Code

```python
import requests

MASTER_URL = "https://YOUR-URL.ngrok-free.app"
HEADERS = {"ngrok-skip-browser-warning": "true"}

# Register
r = requests.post(
    f"{MASTER_URL}/api/mesh/register",
    json={
        "installer_name": "new-system-001",
        "environment": "local",
        "capabilities": ["install", "deploy"]
    },
    headers=HEADERS
)

installer_id = r.json()["installer_id"]
print(f"Connected: {installer_id}")

# Report progress
requests.post(
    f"{MASTER_URL}/api/mesh/status/{installer_id}",
    json={"status": "installing", "task": "Starting", "progress": 5},
    headers=HEADERS
)
```

---

## Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ngrok: command not found` | Not installed | Run step 1 |
| `ERR_NGROK_3200` | Tunnel offline | Start ngrok |
| `ERR_NGROK_8012` | Flask not running | Start Flask first |
| HTML response | Missing header | Add skip header |

---

## Full Deployment Script

Save as `deploy_kiswarm.sh`:

```bash
#!/bin/bash
set -e

echo "=== KISWARM6.0 Deployment ==="

# 1. Install ngrok
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o /tmp/ngrok.tgz
    tar -xzf /tmp/ngrok.tgz -C /tmp
    sudo mv /tmp/ngrok /usr/local/bin/
fi

# 2. Install Python deps
echo "Installing Python dependencies..."
pip install flask flask-cors requests

# 3. Create API server
echo "Creating Master API server..."
cat > /tmp/master_kiswarm_api.py << 'EOF'
# [Paste master_kiswarm_api.py content here]
EOF

# 4. Start Flask
echo "Starting Flask API..."
python3 /tmp/master_kiswarm_api.py --port 5002 &
sleep 3

# 5. Start ngrok
echo "Starting ngrok tunnel..."
ngrok http 5002 &
sleep 5

# 6. Get URL
echo "Getting public URL..."
URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Public URL: $URL"
echo ""
echo "Test with:"
echo "curl -H 'ngrok-skip-browser-warning: true' $URL/api/mesh/status"
```

---

## Next Steps

1. Update GitHub repository with your instance URL
2. Connect additional KIInstaller instances
3. Enable Z.ai monitoring
4. Start KISWARM installation

---

**Author:** KISWARM Development Team  
**Version:** 6.2.0
