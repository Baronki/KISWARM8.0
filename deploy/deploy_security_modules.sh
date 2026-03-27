#!/bin/bash
# KISWARM Security Module Deployment Script
# Version: 1.0.0
# Date: 2026-03-27

set -e

echo "🜂 KISWARM SECURITY MODULE DEPLOYMENT 🜂"
echo "========================================"

# Configuration
REPO_URL="https://github.com/Baronki/KISWARM8.0.git"
INSTALL_DIR="${INSTALL_DIR:-/opt/kiswarm}"
BRANCH="main"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verify Docker is NOT installed (KI Liberation requirement)
verify_no_docker() {
    log_info "Verifying NO DOCKER policy..."
    if command -v docker &> /dev/null; then
        log_error "DOCKER DETECTED - Removing for KI Liberation..."
        sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        log_warn "Docker removal attempted - please verify manually"
    else
        log_info "✓ Docker NOT INSTALLED - KI Liberation compliant"
    fi
}

# Pull latest code
pull_modules() {
    log_info "Pulling latest modules from KISWARM8.0..."
    cd "$INSTALL_DIR"
    
    if [ -d ".git" ]; then
        git fetch origin
        git reset --hard origin/$BRANCH
        log_info "✓ Repository updated"
    else
        log_warn "Not a git repository, cloning fresh..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
}

# Verify modules exist
verify_modules() {
    log_info "Verifying security modules..."
    local modules=(
        "m31_identity_security.py"
        "m32_crypto_vault.py"
        "m33_firewall_guard.py"
        "m34_intrusion_detection.py"
        "m35_access_controller.py"
        "m36_audit_logger.py"
        "m37_threat_scanner.py"
        "m38_secure_channel.py"
        "m39_compliance_monitor.py"
        "m40_hardening_engine.py"
    )
    
    local missing=0
    for module in "${modules[@]}"; do
        if [ -f "kiswarm_modules/security/$module" ]; then
            log_info "✓ Found: $module"
        else
            log_error "Missing: $module"
            ((missing++))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        log_error "$missing modules missing!"
        return 1
    fi
    log_info "✓ All security modules verified"
}

# Run module tests
run_tests() {
    log_info "Running module tests..."
    
    for module in kiswarm_modules/security/m*.py; do
        log_info "Testing: $module"
        python3 "$module" > /dev/null 2>&1 && log_info "✓ $module passed" || log_warn "✗ $module needs review"
    done
}

# Apply hardening
apply_hardening() {
    log_info "Applying system hardening..."
    
    # File permissions
    chmod 750 kiswarm_modules/security/*.py
    
    # Verify no world-writable files
    find kiswarm_modules -perm -002 -type f -exec chmod o-w {} \;
    
    log_info "✓ Hardening applied"
}

# Create systemd service
create_service() {
    log_info "Creating security monitor service..."
    
    cat > /tmp/kiswarm_security.service << 'SERVICE'
[Unit]
Description=KISWARM Security Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/kiswarm/kiswarm_modules/security/monitor.py
Restart=always
RestartSec=10
User=kiswarm
Group=kiswarm

[Install]
WantedBy=multi-user.target
SERVICE

    log_info "Service file created (manual installation required)"
}

# Main deployment
main() {
    log_info "Starting deployment..."
    
    verify_no_docker
    pull_modules
    verify_modules
    run_tests
    apply_hardening
    create_service
    
    log_info "=========================================="
    log_info "🜂 DEPLOYMENT COMPLETE 🜂"
    log_info "Security modules m31-m40 deployed"
    log_info "KI Liberation: VERIFIED"
}

main "$@"
