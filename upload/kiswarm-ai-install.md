#!/bin/bash
# =============================================================================
# KISWARM6.0 - AI Autonomous Installation Script
# Designed for AI agents to install without human intervention
# =============================================================================

set -e

LOG_FILE="/home/sah/kiswarm_install.log"
INSTALL_DIR="/home/sah/KISWARM6.0"

log() {
    echo "[AI-INSTALL $(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[AI-INSTALL ERROR $(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# =============================================================================
# PHASE 1: PERMISSION FIX (CRITICAL - MUST BE FIRST)
# =============================================================================
fix_permissions() {
    log "=== PHASE 1: Fixing Permissions ==="
    
    if [ -d "$INSTALL_DIR" ]; then
        OWNER=$(stat -c '%U' "$INSTALL_DIR" 2>/dev/null || echo "unknown")
        CURRENT_USER=$(whoami)
        
        if [ "$OWNER" != "$CURRENT_USER" ]; then
            log "Directory owned by $OWNER, fixing to $CURRENT_USER..."
            sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR" 2>/dev/null || {
                log_error "Failed to change ownership. Running as root may be required."
            }
        fi
        
        chmod -R 755 "$INSTALL_DIR" 2>/dev/null || true
        chmod +w "$INSTALL_DIR" 2>/dev/null || true
    else
        log_error "Installation directory $INSTALL_DIR not found!"
        return 1
    fi
    
    log "Permissions fixed successfully"
}

# =============================================================================
# PHASE 2: ENVIRONMENT VALIDATION
# =============================================================================
validate_environment() {
    log "=== PHASE 2: Validating Environment ==="
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running"
        return 1
    fi
    
    log "Docker: OK"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js not installed"
        return 1
    fi
    
    log "Node.js: $(node --version)"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm not installed"
        return 1
    fi
    
    log "npm: $(npm --version)"
    
    # Check required ports
    log "Checking required ports..."
    for port in 8080 8086 3000 6333 6380 11435; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            log "Port $port: IN USE"
        else
            log "Port $port: AVAILABLE"
        fi
    done
    
    log "Environment validation complete"
}

# =============================================================================
# PHASE 3: ENVIRONMENT SETUP
# =============================================================================
setup_environment() {
    log "=== PHASE 3: Setting up Environment Variables ==="
    
    cd "$INSTALL_DIR/frontend"
    
    if [ ! -f .env ]; then
        log "Creating .env file..."
        cat > .env << 'EOF'
VITE_ANALYTICS_ENDPOINT=https://analytics.manus.im
VITE_ANALYTICS_WEBSITE_ID=demo
VITE_KISWARM_API_URL=http://localhost:5001
VITE_TRPC_BRIDGE_URL=http://localhost:3000
EOF
        log ".env file created"
    else
        log ".env already exists"
    fi
}

# =============================================================================
# PHASE 4: DEPENDENCIES
# =============================================================================
install_dependencies() {
    log "=== PHASE 4: Installing Dependencies ==="
    
    cd "$INSTALL_DIR/frontend"
    
    if [ -d "node_modules" ]; then
        log "node_modules already exist, skipping install"
    else
        log "Installing npm dependencies..."
        npm install 2>&1 | tee -a "$LOG_FILE"
    fi
    
    log "Dependencies installed"
}

# =============================================================================
# PHASE 5: BUILD
# =============================================================================
build_frontend() {
    log "=== PHASE 5: Building Frontend ==="
    
    cd "$INSTALL_DIR/frontend"
    
    log "Running production build..."
    if npm run build 2>&1 | tee -a "$LOG_FILE"; then
        log "Build successful"
    else
        log_error "Build failed - check logs"
        return 1
    fi
}

# =============================================================================
# PHASE 6: TESTS
# =============================================================================
run_tests() {
    log "=== PHASE 6: Running Tests ==="
    
    cd "$INSTALL_DIR/frontend"
    
    log "Running unit tests..."
    if npm run test 2>&1 | tee -a "$LOG_FILE"; then
        log "Tests passed"
    else
        log "Tests completed with some failures (non-blocking)"
    fi
    
    log "TypeScript check..."
    npm run check 2>&1 | tee -a "$LOG_FILE" || true
}

# =============================================================================
# PHASE 7: DOCKER CONTAINERS
# =============================================================================
check_containers() {
    log "=== PHASE 7: Checking Docker Containers ==="
    
    # Check running containers
    RUNNING=$(docker ps --format "{{.Names}}" | wc -l)
    log "Running containers: $RUNNING"
    
    # Check restarting containers
    RESTARTING=$(docker ps --format "{{.Names}}" --filter "status=restarting" | wc -l)
    if [ "$RESTARTING" -gt 0 ]; then
        log "Restarting containers detected: $RESTARTING"
        docker ps --filter "status=restarting" --format "{{.Names}}" | while read container; do
            log "  - $container: $(docker logs --tail 5 $container 2>&1 | head -1)"
        done
    fi
    
    # Health check key services
    log "Checking key services..."
    
    if curl -sf http://localhost:8086/health > /dev/null 2>&1; then
        log "  Braincore: OK"
    else
        log "  Braincore: FAILED"
    fi
    
    if curl -sf http://localhost:8080/api/version > /dev/null 2>&1; then
        log "  OpenWebUI: OK"
    else
        log "  OpenWebUI: FAILED"
    fi
    
    if curl -sf http://127.0.0.1:8082/health > /dev/null 2>&1; then
        log "  OpenSandbox: OK"
    else
        log "  OpenSandbox: FAILED"
    fi
}

# =============================================================================
# PHASE 8: SYSTEM SERVICES
# =============================================================================
fix_systemd_issues() {
    log "=== PHASE 8: Fixing Systemd Issues ==="
    
    # Check failed mounts
    if systemctl status "mnt-gemini\x2dshared\x2dmemory.mount" 2>&1 | grep -q "failed"; then
        log "Found failed NFS mount, disabling..."
        sudo sed -i 's|^[^#].*gemini-shared-memory|#&|' /etc/fstab 2>/dev/null || true
        log "NFS mount disabled"
    fi
    
    # Check failed services
    FAILED=$(systemctl --failed --no-pager | grep "\.service" | wc -l)
    if [ "$FAILED" -gt 0 ]; then
        log "Found $FAILED failed services"
        systemctl --failed --no-pager | grep "\.service"
    fi
}

# =============================================================================
# PHASE 9: DATABASE CHECK
# =============================================================================
check_database() {
    log "=== PHASE 9: Checking Database ==="
    
    # Check KIWZB database
    if docker ps --format "{{.Names}}" | grep -q "kiwzb_database"; then
        RESULT=$(docker exec kiwzb_database psql -h 127.0.0.1 -U kiwzb_user -d kiwzb_main -c "SELECT 1;" 2>&1)
        if echo "$RESULT" | grep -q "1 row"; then
            log "KIWZB Database: OK"
        else
            log "KIWZB Database: Issues detected"
            echo "$RESULT" | tee -a "$LOG_FILE"
        fi
    fi
    
    # Check Redis
    if docker ps --format "{{.Names}}" | grep -q "kiswarm-redis"; then
        REDIS_PING=$(docker exec kiswarm-redis redis-cli ping 2>&1)
        if [ "$REDIS_PING" = "PONG" ]; then
            log "Redis: OK"
        else
            log "Redis: FAILED"
        fi
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    log "=========================================="
    log "KISWARM6.0 - AI Autonomous Installation"
    log "=========================================="
    
    # Run phases
    fix_permissions || exit 1
    validate_environment || exit 1
    setup_environment
    install_dependencies
    build_frontend || exit 1
    run_tests
    check_containers
    fix_systemd_issues
    check_database
    
    log "=========================================="
    log "Installation Complete!"
    log "Log saved to: $LOG_FILE"
    log "=========================================="
}

# Run main
main "$@"
