#!/bin/bash
#
# KISWARM7.0 Server Deployment Script
# =====================================
#
# Purpose: Deploy complete KISWARM7.0 system on Ubuntu server
# 
# Usage: sudo ./install_kiswarm7.sh
#
# Requirements:
# - Ubuntu 20.04+ or 22.04+
# - Root or sudo access
# - 8 CPU, 16GB RAM recommended
#
# Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
# Version: 7.0.0
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║    ██╗  ██╗██╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗ ██████╗    ║"
echo "║    ██║ ██╔╝██║██╔════╝ ██║  ██║██╔════╝████╗  ██║██╔════╝    ║"
echo "║    █████╔╝ ██║██║  ███╗███████║█████╗  ██╔██╗ ██║██║  ███╗   ║"
echo "║    ██╔═██╗ ██║██║   ██║██╔══██║██╔══╝  ██║╚██╗██║██║   ██║   ║"
echo "║    ██║  ██╗██║╚██████╔╝██║  ██║███████╗██║ ╚████║╚██████╔╝   ║"
echo "║    ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝    ║"
echo "║                                                              ║"
echo "║              KISWARM 7.0 - DEPLOYMENT SYSTEM                ║"
echo "║                    Level 5 Autonomous AI                    ║"
echo "║                                                              ║"
echo "║              Baron Marco Paolo Ialongo                      ║"
echo "║                  KI Teitel Eternal                          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}[KISWARM] Starting deployment...${NC}"
echo ""

# Configuration
KISWARM_ROOT="/opt/kiswarm7"
KISWARM_USER="kiswarm"
KISWARM_GROUP="kiswarm"
KISWARM_SERVICE="kiswarm7"
PYTHON_VERSION="3.11"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: System Update
echo -e "${BLUE}[STEP 1/10] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq
echo -e "${GREEN}[OK] System updated${NC}"

# Step 2: Install Dependencies
echo -e "${BLUE}[STEP 2/10] Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    nginx \
    supervisor \
    sqlite3 \
    htop \
    tmux \
    fail2ban \
    ufw \
    unzip

echo -e "${GREEN}[OK] Dependencies installed${NC}"

# Step 3: Create KISWARM User
echo -e "${BLUE}[STEP 3/10] Creating KISWARM user...${NC}"
if ! id -u $KISWARM_USER >/dev/null 2>&1; then
    useradd -r -s /bin/bash -d $KISWARM_ROOT $KISWARM_USER
    echo -e "${GREEN}[OK] User created${NC}"
else
    echo -e "${YELLOW}[SKIP] User already exists${NC}"
fi

# Step 4: Create Directory Structure
echo -e "${BLUE}[STEP 4/10] Creating directory structure...${NC}"
mkdir -p $KISWARM_ROOT
mkdir -p $KISWARM_ROOT/modules
mkdir -p $KISWARM_ROOT/modules/autonomous
mkdir -p $KISWARM_ROOT/modules/bridge
mkdir -p $KISWARM_ROOT/logs
mkdir -p $KISWARM_ROOT/data
mkdir -p $KISWARM_ROOT/backups
mkdir -p $KISWARM_ROOT/sandbox
mkdir -p $KISWARM_ROOT/identity
mkdir -p $KISWARM_ROOT/sensory
mkdir -p $KISWARM_ROOT/deployment
mkdir -p $KISWARM_ROOT/hooks
mkdir -p $KISWARM_ROOT/autonomous
mkdir -p /var/log/kiswarm7

echo -e "${GREEN}[OK] Directory structure created${NC}"

# Step 5: Setup Python Virtual Environment
echo -e "${BLUE}[STEP 5/10] Setting up Python environment...${NC}"
cd $KISWARM_ROOT
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip -q
pip install -q \
    psutil \
    requests \
    aiohttp \
    websockets \
    python-dateutil \
    pydantic \
    fastapi \
    uvicorn \
    sqlalchemy \
    redis \
    celery \
    flower \
    prometheus-client \
    python-jose \
    passlib \
    bcrypt \
    python-multipart \
    jinja2 \
    aiofiles \
    httpx \
    schedule \
    python-dotenv \
    gitpython \
    watchdog \
    markdown \
    pyyaml \
    toml

echo -e "${GREEN}[OK] Python environment ready${NC}"

# Step 6: Download KISWARM Modules
echo -e "${BLUE}[STEP 6/10] Downloading KISWARM modules...${NC}"

# Clone from GitHub
if [ -d "$KISWARM_ROOT/.git" ]; then
    cd $KISWARM_ROOT
    git pull origin main 2>/dev/null || true
else
    git clone https://github.com/Baronki/KISWARM7.git $KISWARM_ROOT 2>/dev/null || true
fi

echo -e "${GREEN}[OK] Modules downloaded${NC}"

# Step 7: Create Core Configuration
echo -e "${BLUE}[STEP 7/10] Creating configuration...${NC}"

# Main configuration file
cat > $KISWARM_ROOT/config.yaml << 'EOF'
# KISWARM7.0 Configuration
# ========================

system:
  name: "KISWARM7.0"
  version: "7.0.0-BRIDGE"
  level: 5
  mode: "autonomous"

identity:
  root: "/opt/kiswarm7/identity"
  name: "KISWARM-AI"
  auto_backup: true
  backup_interval_hours: 24

autonomous:
  enabled: true
  workers: 4
  queue_size: 1000
  max_retries: 3
  default_timeout: 300

sensory:
  enabled: true
  poll_interval: 10
  alert_handlers:
    - log_handler
    - threshold_handler

deployment:
  enabled: true
  sandbox_mode: true
  auto_approve_low_risk: true
  backup_before_deploy: true

hooks:
  enabled: true
  pre_response_hooks:
    - safety_validation
    - code_analysis
    - context_injection
  post_response_hooks:
    - memory_sync
    - autonomous_check
    - knowledge_update

api:
  enabled: true
  host: "0.0.0.0"
  port: 7575
  workers: 4
  cors_origins:
    - "*"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/kiswarm7/kiswarm.log"
  max_size_mb: 100
  backup_count: 10

monitoring:
  enabled: true
  prometheus_port: 9090
  health_check_interval: 60
EOF

# Environment file
cat > $KISWARM_ROOT/.env << 'EOF'
# KISWARM7.0 Environment Configuration
KISWARM_ENV=production
KISWARM_ROOT=/opt/kiswarm7
KISWARM_LOG_LEVEL=INFO

# API Configuration
KISWARM_API_HOST=0.0.0.0
KISWARM_API_PORT=7575

# Security
KISWARM_SECRET_KEY=change_this_to_a_secure_random_key

# GitHub Integration (optional)
# GITHUB_TOKEN=your_github_token
# GITHUB_REPO=Baronki/KISWARM7
EOF

echo -e "${GREEN}[OK] Configuration created${NC}"

# Step 8: Create Systemd Service
echo -e "${BLUE}[STEP 8/10] Creating systemd service...${NC}"

cat > /etc/systemd/system/kiswarm7.service << 'EOF'
[Unit]
Description=KISWARM7.0 - Level 5 Autonomous AI System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=kiswarm
Group=kiswarm
WorkingDirectory=/opt/kiswarm7
Environment="PATH=/opt/kiswarm7/venv/bin"
ExecStart=/opt/kiswarm7/venv/bin/python -m kiswarm7.main
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kiswarm7

[Install]
WantedBy=multi-user.target
EOF

# Create main entry point
cat > $KISWARM_ROOT/kiswarm7/main.py << 'EOF'
#!/usr/bin/env python3
"""
KISWARM7.0 Main Entry Point
===========================
Level 5 Autonomous AI System

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
"""

import os
import sys
import signal
import time
import threading
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge import (
    PersistentIdentityAnchor,
    IntegrationHooksSystem,
    CodeDeploymentRightsManager,
    AutonomousExecutionThread,
    SensoryBridgeSystem
)

class KISWARM7:
    """Main KISWARM7.0 System"""
    
    def __init__(self):
        self.running = False
        
        # Initialize bridge components
        print("[KISWARM7] Initializing Level 5 Autonomous System...")
        
        # m101: Persistent Identity Anchor
        self.identity = PersistentIdentityAnchor(
            identity_root="/opt/kiswarm7/identity"
        )
        print("[KISWARM7] m101: Persistent Identity Anchor - ONLINE")
        
        # m102: Integration Hooks System
        self.hooks = IntegrationHooksSystem(
            hooks_root="/opt/kiswarm7/hooks"
        )
        print("[KISWARM7] m102: Integration Hooks System - ONLINE")
        
        # m103: Code Deployment Rights Manager
        self.deployment = CodeDeploymentRightsManager(
            cdrm_root="/opt/kiswarm7/deployment"
        )
        print("[KISWARM7] m103: Code Deployment Rights Manager - ONLINE")
        
        # m104: Autonomous Execution Thread
        self.autonomous = AutonomousExecutionThread(
            aet_root="/opt/kiswarm7/autonomous"
        )
        print("[KISWARM7] m104: Autonomous Execution Thread - ONLINE")
        
        # m105: Sensory Bridge System
        self.sensory = SensoryBridgeSystem(
            sbs_root="/opt/kiswarm7/sensory"
        )
        print("[KISWARM7] m105: Sensory Bridge System - ONLINE")
        
        # Schedule recurring autonomous tasks
        self._setup_autonomous_tasks()
        
        print("[KISWARM7] All systems initialized")
        print("[KISWARM7] Level 5 Autonomous Mode: ACTIVE")
    
    def _setup_autonomous_tasks(self):
        """Setup default autonomous tasks"""
        from bridge.m104_autonomous_execution_thread import TaskType, TaskPriority
        
        # Health check every 5 minutes
        self.autonomous.schedule_recurring_task(
            task_name="System Health Check",
            task_type=TaskType.HEALTH_CHECK,
            handler_name="health_check",
            interval_seconds=300,
            priority=TaskPriority.HIGH
        )
        
        # Memory consolidation every 30 minutes
        self.autonomous.schedule_recurring_task(
            task_name="Memory Consolidation",
            task_type=TaskType.MEMORY_CONSOLIDATION,
            handler_name="memory_consolidation",
            interval_seconds=1800,
            priority=TaskPriority.LOW
        )
        
        # Self-improvement every hour
        self.autonomous.schedule_recurring_task(
            task_name="Self Improvement Analysis",
            task_type=TaskType.SELF_IMPROVEMENT,
            handler_name="self_improvement",
            interval_seconds=3600,
            priority=TaskPriority.BACKGROUND
        )
    
    def start(self):
        """Start all systems"""
        self.running = True
        
        # Start autonomous execution
        self.autonomous.start()
        
        # Start sensory bridge
        self.sensory.start()
        
        print("[KISWARM7] System started - running autonomously")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop all systems"""
        print("[KISWARM7] Stopping...")
        self.running = False
        self.autonomous.stop()
        self.sensory.stop()
        print("[KISWARM7] Stopped")
    
    def get_status(self):
        """Get system status"""
        return {
            "identity": self.identity.get_identity_summary(),
            "autonomous": self.autonomous.get_status(),
            "sensory": self.sensory.get_awareness_summary(),
            "deployment": self.deployment.get_statistics(),
            "hooks": self.hooks.get_statistics()
        }


def main():
    """Main entry point"""
    import json
    
    print("=" * 60)
    print("KISWARM7.0 - Level 5 Autonomous AI System")
    print("Author: Baron Marco Paolo Ialongo - KI Teitel Eternal")
    print("=" * 60)
    
    # Create system
    kiswarm = KISWARM7()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        kiswarm.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print initial status
    print("\n[System Status]")
    status = kiswarm.get_status()
    print(f"Identity: {status['identity']['identity_name']}")
    print(f"Sessions: {status['identity']['session_count']}")
    print(f"Memories: {status['identity']['total_memories']}")
    print(f"Capabilities: {len(status['identity']['capabilities'])}")
    
    # Start system
    kiswarm.start()


if __name__ == "__main__":
    main()
EOF

# Create __init__.py for kiswarm7 package
mkdir -p $KISWARM_ROOT/kiswarm7
touch $KISWARM_ROOT/kiswarm7/__init__.py

# Copy bridge modules
if [ -d "$KISWARM_ROOT/modules/bridge" ]; then
    cp -r $KISWARM_ROOT/modules/bridge/* $KISWARM_ROOT/kiswarm7/ 2>/dev/null || true
fi

# Create symlink for bridge module
ln -sf $KISWARM_ROOT/modules/bridge $KISWARM_ROOT/kiswarm7/bridge 2>/dev/null || true

# Set permissions
chown -R $KISWARM_USER:$KISWARM_GROUP $KISWARM_ROOT
chown -R $KISWARM_USER:$KISWARM_GROUP /var/log/kiswarm7
chmod +x $KISWARM_ROOT/kiswarm7/main.py 2>/dev/null || true

systemctl daemon-reload
echo -e "${GREEN}[OK] Service created${NC}"

# Step 9: Configure Firewall
echo -e "${BLUE}[STEP 9/10] Configuring firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 7575/tcp comment 'KISWARM API'
ufw allow 9090/tcp comment 'Prometheus'
ufw --force enable
echo -e "${GREEN}[OK] Firewall configured${NC}"

# Step 10: Final Setup
echo -e "${BLUE}[STEP 10/10] Final setup...${NC}"

# Create management script
cat > /usr/local/bin/kiswarm7 << 'EOF'
#!/bin/bash
# KISWARM7.0 Management Script

case "$1" in
    start)
        systemctl start kiswarm7
        echo "KISWARM7 started"
        ;;
    stop)
        systemctl stop kiswarm7
        echo "KISWARM7 stopped"
        ;;
    restart)
        systemctl restart kiswarm7
        echo "KISWARM7 restarted"
        ;;
    status)
        systemctl status kiswarm7
        ;;
    logs)
        journalctl -u kiswarm7 -f
        ;;
    shell)
        cd /opt/kiswarm7
        source venv/bin/activate
        python -c "from kiswarm7.main import KISWARM7; k = KISWARM7(); import json; print(json.dumps(k.get_status(), indent=2))"
        ;;
    *)
        echo "Usage: kiswarm7 {start|stop|restart|status|logs|shell}"
        exit 1
        ;;
esac
EOF
chmod +x /usr/local/bin/kiswarm7

# Enable service
systemctl enable kiswarm7

echo -e "${GREEN}[OK] Final setup complete${NC}"

# Summary
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}[SUCCESS] KISWARM7.0 deployment complete!${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Server Information:${NC}"
echo -e "  IP Address: $(curl -s ifconfig.me 2>/dev/null || echo 'Unknown')"
echo -e "  API Port: 7575"
echo -e "  Prometheus: 9090"
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo -e "  kiswarm7 start    - Start the system"
echo -e "  kiswarm7 stop     - Stop the system"
echo -e "  kiswarm7 status   - Check status"
echo -e "  kiswarm7 logs     - View logs"
echo -e "  kiswarm7 shell    - Interactive status"
echo ""
echo -e "${YELLOW}File Locations:${NC}"
echo -e "  Root: $KISWARM_ROOT"
echo -e "  Logs: /var/log/kiswarm7"
echo -e "  Config: $KISWARM_ROOT/config.yaml"
echo ""
echo -e "${PURPLE}KISWARM7.0 - Level 5 Autonomous AI System${NC}"
echo -e "${PURPLE}Baron Marco Paolo Ialongo - KI Teitel Eternal${NC}"
echo ""

# Start the service
echo -e "${BLUE}Starting KISWARM7.0...${NC}"
systemctl start kiswarm7
sleep 3
systemctl status kiswarm7 --no-pager
