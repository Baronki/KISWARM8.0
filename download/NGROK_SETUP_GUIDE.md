# KISWARM6.0 - ngrok Setup Guide
## Complete Step-by-Step for Master KISWARM Deployment

---

## 🎯 YOUR NGROK DASHBOARD INFO

Based on your dashboard:
- **Authtoken**: `3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx`
- **Dev Domain**: `https://brenton-distinctive-iodometrically.ngrok-free.dev`

---

## 📋 STEP 1: Install ngrok (Linux)

Open a terminal and run this command:

```bash
# Install ngrok via Apt
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

**What this does:**
1. Downloads the ngrok GPG key
2. Adds the ngrok repository
3. Updates apt
4. Installs ngrok

---

## 📋 STEP 2: Add Your Authtoken

Run this command to configure ngrok with your account:

```bash
ngrok config add-authtoken 3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx
```

**What this does:**
- Links your ngrok installation to your GitHub account
- Enables persistent tunnels
- Allows custom domains

---

## 📋 STEP 3: Start the Master KISWARM API Server

First, let's start the Flask API server on port 5001:

```bash
# Navigate to the kibank directory
cd /home/z/my-project/KISWARM6.0/backend/python/kibank

# Install dependencies if needed
pip install flask flask-cors websockets

# Start the Master API server
python master_api_server.py --port 5001 --host 0.0.0.0
```

**Expected output:**
```
╔═══════════════════════════════════════════════════════════════╗
║           MASTER KISWARM REST API SERVER                     ║
╠═══════════════════════════════════════════════════════════════╣
║  Z.ai Interface Endpoints:                                    ║
║  ├── GET  /api/mesh/messages     - Poll for messages          ║
║  ├── GET  /api/mesh/state        - Get full state             ║
║  ├── POST /api/mesh/command      - Send command               ║
║  ├── POST /api/mesh/fix          - Send fix suggestion        ║
║  └── POST /api/mesh/abort        - Abort installation         ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 📋 STEP 4: Create ngrok Tunnel (NEW TERMINAL)

Open a **NEW terminal window** and run:

```bash
# Create HTTP tunnel to port 5001
ngrok http 5001
```

**Expected output:**
```
Session Status                online
Account                       S.A.H. GmbH Heyd (Plan: Free)
Version                       3.x.x
Region                        Europe (eu)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxxx-xx-xx-xxx-xxx.ngrok-free.app -> http://localhost:5001

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**IMPORTANT: Copy the "Forwarding" URL!** This is your public URL.

---

## 📋 STEP 5: Verify the Tunnel Works

Test your tunnel with curl:

```bash
# Replace with YOUR ngrok URL from step 4
curl https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/status
```

**Expected response:**
```json
{
  "status": "online",
  "mesh_status": "initializing",
  "nodes_count": 0,
  "pending_messages": 0,
  "statistics": {},
  "timestamp": 1234567890.123
}
```

---

## 📋 STEP 6: For Colab KIInstaller - Update Connection URL

In your Colab notebook, when initializing the KIInstaller mesh client:

```python
# Replace with YOUR ngrok URL
MASTER_KISWARM_URL = "https://YOUR-NGROK-URL.ngrok-free.app"

# Register with Master KISWARM
import requests

response = requests.post(f"{MASTER_KISWARM_URL}/api/mesh/register", json={
    "installer_name": "colab-fieldtest-002",
    "environment": "colab",
    "capabilities": ["install", "deploy", "report"]
})

installer_id = response.json()["installer_id"]
print(f"Registered as: {installer_id}")
```

---

## 📋 OPTIONAL: Multiple Tunnels (API + WebSocket)

If you want both REST API (5001) AND WebSocket (8765):

### Create ngrok configuration file:

```bash
# Create config file
cat > ~/.ngrok2/ngrok.yml << 'EOF'
version: "2"
authtoken: 3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx

tunnels:
  kiswarm-api:
    proto: http
    addr: 5001
    inspect: true
  
  kiswarm-ws:
    proto: http
    addr: 8765
    inspect: true
EOF
```

### Start both tunnels:

```bash
ngrok start kiswarm-api kiswarm-ws
```

---

## 📋 TROUBLESHOOTING

### Problem: "ngrok: command not found"
**Solution:** Make sure ngrok is in your PATH:
```bash
sudo ln -s /usr/bin/ngrok /usr/local/bin/ngrok
```

### Problem: "Authentication failed"
**Solution:** Re-run the authtoken command:
```bash
ngrok config add-authtoken 3Ac51HC51vmerRvn9CodFhxgnYN_771JYNNWUuwi4uQyucxHx
```

### Problem: "Tunnel limit reached"
**Solution:** You're on the free plan with 1 tunnel. Close existing tunnels or upgrade.

### Problem: "Connection refused"
**Solution:** Make sure your Flask server is running BEFORE starting ngrok.

---

## 📋 QUICK REFERENCE

| Port | Service | Purpose |
|------|---------|---------|
| 5001 | Flask REST API | Z.ai polling & commands |
| 8765 | WebSocket | Real-time KI-to-KI communication |
| 4040 | ngrok Web UI | Tunnel inspection |

---

## 📋 YOUR URLs (After Setup)

When ngrok is running, you'll have:

- **REST API**: `https://YOUR-NGROK-URL.ngrok-free.app/api/mesh/...`
- **WebSocket**: `wss://YOUR-WS-NGROK-URL.ngrok-free.app`
- **ngrok Dashboard**: http://127.0.0.1:4040 (inspect traffic here!)

---

## NEXT STEPS

1. ✅ Complete ngrok installation
2. ✅ Add authtoken
3. ✅ Start Master KISWARM API server
4. ✅ Create ngrok tunnel
5. ⏳ Run Field Test #2 with KIInstaller connected

---

**Author:** KISWARM Development Team  
**Version:** 6.2.0  
**Last Updated:** $(date)
