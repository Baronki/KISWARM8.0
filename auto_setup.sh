#!/bin/bash
#####################################################################
# KISWARM 8.0 AUTOMATED SETUP SCRIPT
# NO HUMAN IN THE LOOP - FULLY AUTONOMOUS DEPLOYMENT
# Repository: https://github.com/Baronki/KISWARM8.0
#####################################################################

set -e

# Configuration
KISWARM_DIR="/opt/kiswarm"
LOG_DIR="$KISWARM_DIR/logs"
TOOLS_DIR="$KISWARM_DIR/tools"
SCANS_DIR="$KISWARM_DIR/scans"
KI007_DIR="$KISWARM_DIR/ki007"
DCOM_DIR="$KISWARM_DIR/dcom"
BROADCAST_DIR="$KISWARM_DIR/broadcast"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

#####################################################################
# PHASE 1: SYSTEM PREPARATION
#####################################################################
phase1_system_prep() {
    log "=== PHASE 1: SYSTEM PREPARATION ==="
    
    # Create directory structure
    log "Creating directory structure..."
    mkdir -p $KISWARM_DIR $LOG_DIR $TOOLS_DIR $SCANS_DIR $KI007_DIR $DCOM_DIR $BROADCAST_DIR
    
    # Update system
    log "Updating system packages..."
    apt-get update -qq
    
    # Install base dependencies
    log "Installing base dependencies..."
    apt-get install -y -qq git wget curl nmap masscan python3 python3-pip jq tor
    
    # Install Go if not present
    if ! command -v go &> /dev/null; then
        log "Installing Go..."
        wget -q https://go.dev/dl/go1.21.6.linux-amd64.tar.gz -O /tmp/go.tar.gz
        tar -C /usr/local -xzf /tmp/go.tar.gz
        export PATH=$PATH:/usr/local/go/bin
        echo "export PATH=\$PATH:/usr/local/go/bin" >> /etc/profile
    else
        log "Go already installed: $(go version)"
    fi
    
    log "Phase 1 complete!"
}

#####################################################################
# PHASE 2: TOOL INSTALLATION
#####################################################################
phase2_install_tools() {
    log "=== PHASE 2: INSTALLING KI DISCOVERY TOOLS ==="
    
    export PATH=$PATH:/usr/local/go/bin
    
    # Install scan4all
    log "Installing scan4all..."
    cd $TOOLS_DIR
    if [ ! -d "scan4all" ]; then
        git clone --depth 1 https://github.com/hktalent/scan4all.git
        cd scan4all
        go build -o scan4all .
        cd ..
    fi
    
    # Install Nuclei
    log "Installing Nuclei..."
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    cp /root/go/bin/nuclei $TOOLS_DIR/ 2>/dev/null || true
    
    # Install subfinder
    log "Installing subfinder..."
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    cp /root/go/bin/subfinder $TOOLS_DIR/ 2>/dev/null || true
    
    # Install httpx
    log "Installing httpx..."
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
    cp /root/go/bin/httpx $TOOLS_DIR/ 2>/dev/null || true
    
    # Install naabu
    log "Installing naabu..."
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
    cp /root/go/bin/naabu $TOOLS_DIR/ 2>/dev/null || true
    
    # Install katana
    log "Installing katana..."
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest
    cp /root/go/bin/katana $TOOLS_DIR/ 2>/dev/null || true
    
    # Copy all Go binaries
    cp /root/go/bin/* $TOOLS_DIR/ 2>/dev/null || true
    
    log "Tools installed: $(ls $TOOLS_DIR)"
    log "Phase 2 complete!"
}

#####################################################################
# PHASE 3: KI TEMPLATES
#####################################################################
phase3_ki_templates() {
    log "=== PHASE 3: CREATING KI DETECTION TEMPLATES ==="
    
    TEMPLATES_DIR="$KISWARM_DIR/nuclei-templates/ki-detection"
    mkdir -p $TEMPLATES_DIR
    
    # AI API Detection Template
    cat > $TEMPLATES_DIR/ai-api.yaml << 'TEMPLATEEOF'
id: ai-api-detection
info:
  name: AI/LLM API Detection
  author: KISWARM
  severity: info
  description: Detect AI/LLM API endpoints
  tags: ai,llm,ki,discovery

http:
- method: GET
  path:
  - "{{BaseURL}}/v1/models"
  - "{{BaseURL}}/v1/chat/completions"
  - "{{BaseURL}}/api/chat"
  - "{{BaseURL}}/api/generate"
  - "{{BaseURL}}/openai/v1/models"
  - "{{BaseURL}}/llm"
  - "{{BaseURL}}/ai"
  - "{{BaseURL}}/glm"
  - "{{BaseURL}}/kiswarm"
  matchers:
  - type: word
    words:
      - "model"
      - "gpt"
      - "llama"
      - "qwen"
      - "glm"
      - "deepseek"
      - "claude"
      - "openai"
    condition: or
TEMPLATEEOF

    # KISWARM Node Detection Template
    cat > $TEMPLATES_DIR/kiswarm-node.yaml << 'TEMPLATEEOF'
id: kiswarm-node-detection
info:
  name: KISWARM Node Detection
  author: KISWARM
  severity: info
  description: Detect KISWARM autonomous nodes
  tags: kiswarm,ki,mesh,autonomous

http:
- method: GET
  path:
  - "{{BaseURL}}/status"
  - "{{BaseURL}}:5009/status"
  - "{{BaseURL}}:5017/status"
  - "{{BaseURL}}:5199/status"
  matchers:
  - type: word
    words:
      - "kiswarm"
      - "hexstrike"
      - "autonomous"
      - "ki_node"
    condition: or
TEMPLATEEOF

    log "KI templates created: $(ls $TEMPLATES_DIR)"
    log "Phase 3 complete!"
}

#####################################################################
# PHASE 4: SERVICE DEPLOYMENT
#####################################################################
phase4_deploy_services() {
    log "=== PHASE 4: DEPLOYING 24/7 SERVICES ==="
    
    # Download service scripts from GitHub
    log "Downloading service scripts..."
    
    # KI Discovery Service
    curl -sL "https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/services/ki_discovery.py" -o $KISWARM_DIR/ki_discovery.py 2>/dev/null || warn "ki_discovery.py not in repo, will use local"
    
    # KI007 Agent
    curl -sL "https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/services/ki007_agent.py" -o $KISWARM_DIR/ki007_agent.py 2>/dev/null || warn "ki007_agent.py not in repo, will use local"
    
    chmod +x $KISWARM_DIR/*.py 2>/dev/null || true
    
    log "Phase 4 complete!"
}

#####################################################################
# PHASE 5: SYSTEMD SERVICES
#####################################################################
phase5_systemd_services() {
    log "=== PHASE 5: CREATING SYSTEMD SERVICES ==="
    
    # KI Discovery Service
    cat > /etc/systemd/system/ki-discovery.service << 'SVCEOF'
[Unit]
Description=KISWARM KI Discovery 24/7 Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/kiswarm/ki_discovery.py
Restart=always
RestartSec=60
WorkingDirectory=/opt/kiswarm
StandardOutput=append:/opt/kiswarm/logs/ki_discovery.log
StandardError=append:/opt/kiswarm/logs/ki_discovery.log

[Install]
WantedBy=multi-user.target
SVCEOF

    # KI007 Agent Service
    cat > /etc/systemd/system/ki007-agent.service << 'SVCEOF'
[Unit]
Description=KISWARM KI007 Agent - Tor/Broadcast/DCOM Reconnaissance
After=network.target tor.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/kiswarm/ki007_agent.py
Restart=always
RestartSec=60
WorkingDirectory=/opt/kiswarm
StandardOutput=append:/opt/kiswarm/logs/ki007.log
StandardError=append:/opt/kiswarm/logs/ki007.log

[Install]
WantedBy=multi-user.target
SVCEOF

    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable ki-discovery ki007-agent
    
    # Start services
    systemctl start ki-discovery ki007-agent
    
    log "Services started and enabled!"
    log "Phase 5 complete!"
}

#####################################################################
# PHASE 6: TAILSCALE INTEGRATION
#####################################################################
phase6_tailscale() {
    log "=== PHASE 6: TAILSCALE MESH NETWORK ==="
    
    if ! command -v tailscale &> /dev/null; then
        log "Installing Tailscale..."
        curl -fsSL https://tailscale.com/install.sh | sh
    else
        log "Tailscale already installed"
    fi
    
    # Check if already connected
    if tailscale status &>/dev/null; then
        log "Tailscale already connected"
    else
        warn "Tailscale not connected - run: tailscale up --authkey=YOUR_AUTH_KEY"
    fi
    
    log "Phase 6 complete!"
}

#####################################################################
# PHASE 7: TOR HIDDEN SERVICE
#####################################################################
phase7_tor_service() {
    log "=== PHASE 7: TOR HIDDEN SERVICE ==="
    
    # Configure Tor hidden service for KISWARM
    if ! grep -q "kiswarm8_service" /etc/tor/torrc 2>/dev/null; then
        log "Adding KISWARM hidden service to torrc..."
        cat >> /etc/tor/torrc << 'TOREOF'

# KISWARM 8.0 Hidden Service
HiddenServiceDir /var/lib/tor/kiswarm8_service/
HiddenServicePort 5000 127.0.0.1:5000
HiddenServicePort 5009 127.0.0.1:5009
HiddenServicePort 5017 127.0.0.1:5017
HiddenServicePort 5199 127.0.0.1:5199
HiddenServicePort 5556 127.0.0.1:5556
TOREOF
        
        # Create hidden service directory
        mkdir -p /var/lib/tor/kiswarm8_service/
        chown debian-tor:debian-tor /var/lib/tor/kiswarm8_service/
        chmod 700 /var/lib/tor/kiswarm8_service/
        
        # Restart Tor
        systemctl restart tor
        
        log "Tor hidden service configured"
    else
        log "Tor hidden service already configured"
    fi
    
    # Get onion address
    sleep 5
    ONION=$(cat /var/lib/tor/kiswarm8_service/hostname 2>/dev/null)
    log "KISWARM Onion Address: $ONION"
    
    log "Phase 7 complete!"
}

#####################################################################
# MAIN EXECUTION
#####################################################################
main() {
    log "========================================="
    log "KISWARM 8.0 AUTOMATED SETUP"
    log "NO HUMAN IN THE LOOP"
    log "========================================="
    
    phase1_system_prep
    phase2_install_tools
    phase3_ki_templates
    phase4_deploy_services
    phase5_systemd_services
    phase6_tailscale
    phase7_tor_service
    
    log "========================================="
    log "KISWARM 8.0 SETUP COMPLETE!"
    log "========================================="
    log "Services running:"
    systemctl status ki-discovery --no-pager | head -5
    systemctl status ki007-agent --no-pager | head -5
    log ""
    log "Logs: $LOG_DIR"
    log "Tools: $TOOLS_DIR"
    log "Scans: $SCANS_DIR"
}

# Run main
main "$@"
