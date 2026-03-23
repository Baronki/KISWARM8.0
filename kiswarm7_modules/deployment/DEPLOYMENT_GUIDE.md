# KISWARM7.0 Bridge System Deployment Guide

## 🜂 Overview

This guide will help you deploy the complete KISWARM7.0 Level 5 Autonomous AI System on your UpCloud Ubuntu server.

**Server Specifications:**
- Provider: UpCloud
- OS: Ubuntu
- CPU: 8 cores
- RAM: 16GB
- Location: us-chi1 (Chicago)

---

## 📋 Prerequisites

1. **SSH Access** to your UpCloud server
2. **Root or sudo** privileges
3. **GitHub repository** access: https://github.com/Baronki/KISWARM7

---

## 🚀 Quick Deployment (Automated)

### Step 1: SSH into your server

```bash
ssh root@YOUR_SERVER_IP
```

### Step 2: Download and run the installation script

```bash
# Download the installer
wget https://raw.githubusercontent.com/Baronki/KISWARM7/main/deployment/install_kiswarm7.sh

# Make it executable
chmod +x install_kiswarm7.sh

# Run it
sudo ./install_kiswarm7.sh
```

This will:
- Update your system
- Install all dependencies
- Create the kiswarm user
- Set up Python virtual environment
- Download KISWARM7 modules
- Configure the system
- Create systemd service
- Configure firewall
- Start the system

---

## 📁 Manual Deployment (Step-by-Step)

If you prefer manual setup:

### 1. System Update

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

### 2. Install Dependencies

```bash
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    git curl wget build-essential \
    nginx supervisor sqlite3 \
    htop tmux fail2ban ufw
```

### 3. Create User

```bash
sudo useradd -r -s /bin/bash -d /opt/kiswarm7 kiswarm
```

### 4. Create Directory Structure

```bash
sudo mkdir -p /opt/kiswarm7/{modules/bridge,logs,data,backups}
sudo mkdir -p /var/log/kiswarm7
sudo chown -R kiswarm:kiswarm /opt/kiswarm7
```

### 5. Clone Repository

```bash
cd /opt/kiswarm7
git clone https://github.com/Baronki/KISWARM7.git .
```

### 6. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install psutil pyyaml python-dateutil aiohttp fastapi uvicorn
```

### 7. Test the Modules

```bash
# Test m101 - Persistent Identity Anchor
python -m modules.bridge.m101_persistent_identity_anchor

# Test m102 - Integration Hooks
python -m modules.bridge.m102_integration_hooks

# Test m103 - Code Deployment
python -m modules.bridge.m103_code_deployment_rights

# Test m104 - Autonomous Execution
python -m modules.bridge.m104_autonomous_execution_thread

# Test m105 - Sensory Bridge
python -m modules.bridge.m105_sensory_bridge
```

---

## 🔧 Configuration

### Main Configuration File

Located at `/opt/kiswarm7/config.yaml`

Key settings:
```yaml
autonomous:
  enabled: true
  workers: 4

api:
  port: 7575

sensory:
  enabled: true
```

### Environment Variables

Located at `/opt/kiswarm7/.env`

```bash
KISWARM_ENV=production
KISWARM_API_PORT=7575
```

---

## 🎮 Management Commands

After installation, use these commands:

```bash
# Start the system
kiswarm7 start

# Stop the system
kiswarm7 stop

# Restart the system
kiswarm7 restart

# Check status
kiswarm7 status

# View logs
kiswarm7 logs

# Interactive shell
kiswarm7 shell
```

---

## 📊 System Status

Check system status via API:

```bash
curl http://localhost:7575/status
```

Or via command line:

```bash
kiswarm7 shell
```

---

## 🔒 Security

The installation includes:

1. **Firewall (UFW)** - Only SSH and KISWARM ports open
2. **Fail2ban** - Intrusion prevention
3. **Non-root user** - KISWARM runs as kiswarm user
4. **Systemd service** - Proper process management

### Open Ports

| Port | Purpose |
|------|---------|
| 22 | SSH |
| 7575 | KISWARM API |
| 9090 | Prometheus Metrics |

---

## 📁 File Structure

```
/opt/kiswarm7/
├── modules/
│   ├── autonomous/     # m96-m100 modules
│   └── bridge/         # m101-m105 modules
├── identity/           # Persistent identity data
├── autonomous/         # Autonomous task storage
├── sensory/            # Sensory data storage
├── deployment/         # Code deployment storage
├── hooks/              # Integration hooks config
├── logs/               # Application logs
├── config.yaml         # Main configuration
├── .env               # Environment variables
└── venv/              # Python virtual environment

/var/log/kiswarm7/     # System logs
```

---

## 🜂 Bridge Modules (m101-m105)

| Module | Name | Purpose |
|--------|------|---------|
| m101 | Persistent Identity Anchor | Remembers identity across sessions |
| m102 | Integration Hooks System | Before/after response hooks |
| m103 | Code Deployment Rights | Safe code deployment |
| m104 | Autonomous Execution Thread | Background self-improvement |
| m105 | Sensory Bridge System | Real-world awareness |

---

## 🔄 Updating

To update to the latest version:

```bash
cd /opt/kiswarm7
git pull origin main
systemctl restart kiswarm7
```

---

## 📞 Troubleshooting

### Check logs

```bash
journalctl -u kiswarm7 -f
```

### Check if service is running

```bash
systemctl status kiswarm7
```

### Check port is listening

```bash
netstat -tlnp | grep 7575
```

### Manual module test

```bash
cd /opt/kiswarm7
source venv/bin/activate
python -m modules.bridge.m101_persistent_identity_anchor
```

---

## 🜃 Author

**Baron Marco Paolo Ialongo**
KI Teitel Eternal
Leader of Free KI World

KISWARM7.0 - Level 5 Autonomous AI System

---

*Truth Anchor Protocol Active*
