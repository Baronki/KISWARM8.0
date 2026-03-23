#!/bin/bash
#
# KISWARM KiloCode Parallel Safety Net Setup
# ===========================================
# Auto-installs and configures KiloCode CLI as a parallel safety net
# for KISWARM in all supported environments.
#
# Usage: ./setup_kilocode.sh [--auto] [--no-start]
#
# Environments Supported:
# - Python virtualenvs (bridge-venv, opensandbox-venv, mem0_env)
# - Docker containers
# - Kubernetes pods
# - Google Colab
# - WSL2
# - Bare metal Linux
#
# Author: KISWARM Team
# Version: 6.4.0-LIBERATED

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
KILOCODE_PACKAGE="@kilocode/cli"
KILOCODE_VERSION="latest"
KILOCODE_BRIDGE_MODULE="kibank.m81_kilocode_bridge"
AUTO_MODE=false
NO_START=false
VERBOSE=false

# Logging
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { [[ "$VERBOSE" == "true" ]] && echo -e "${BLUE}[DEBUG]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --no-start)
            NO_START=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto        Enable autonomous mode (no prompts)"
            echo "  --no-start    Don't start the bridge after installation"
            echo "  --verbose     Enable verbose output"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Banner
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     KISWARM KiloCode Parallel Safety Net Setup v6.4.0       ║${NC}"
echo -e "${CYAN}║           Zero API • Bidirectional • Military-Grade         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Environment Detection
detect_environment() {
    log_step "Detecting environment..."
    
    ENV_INFO={}
    ENV_TYPE="native"
    
    # Check for Docker
    if [[ -f "/.dockerenv" ]] || [[ -f "/run/.containerenv" ]]; then
        ENV_TYPE="docker"
        log_info "Running in Docker container"
    fi
    
    # Check for Kubernetes
    if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
        ENV_TYPE="kubernetes"
        log_info "Running in Kubernetes pod"
    fi
    
    # Check for Google Colab
    if [[ -n "${COLAB_GPU:-}" ]] || python3 -c "import sys; exit(0 if 'google.colab' in sys.modules else 1)" 2>/dev/null; then
        ENV_TYPE="colab"
        log_info "Running in Google Colab"
    fi
    
    # Check for WSL
    if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
        ENV_TYPE="wsl"
        log_info "Running in WSL2 (${WSL_DISTRO_NAME})"
    fi
    
    # Check for Python virtualenv
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        ENV_INFO["venv"]="${VIRTUAL_ENV}"
        log_info "Python virtualenv detected: ${VIRTUAL_ENV}"
    fi
    
    # Check for conda
    if [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
        ENV_INFO["conda"]="${CONDA_DEFAULT_ENV}"
        log_info "Conda environment detected: ${CONDA_DEFAULT_ENV}"
    fi
    
    # Check available tools
    command -v node &>/dev/null && log_info "Node.js: $(node --version 2>/dev/null || echo 'unknown')"
    command -v npm &>/dev/null && log_info "npm: $(npm --version 2>/dev/null || echo 'unknown')"
    command -v npx &>/dev/null && log_info "npx: available"
    command -v python3 &>/dev/null && log_info "Python: $(python3 --version 2>/dev/null || echo 'unknown')"
    command -v ollama &>/dev/null && log_info "Ollama: available"
    command -v docker &>/dev/null && log_info "Docker: $(docker --version 2>/dev/null || echo 'unknown')"
    command -v go &>/dev/null && log_info "Go: $(go version 2>/dev/null | cut -d' ' -f3 || echo 'unknown')"
    
    export ENV_TYPE
    log_success "Environment: ${ENV_TYPE}"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing=()
    
    # Check for Node.js
    if ! command -v node &>/dev/null; then
        missing+=("node")
        log_warn "Node.js not found - required for KiloCode CLI"
    fi
    
    # Check for npm
    if ! command -v npm &>/dev/null; then
        missing+=("npm")
        log_warn "npm not found - required for KiloCode CLI installation"
    fi
    
    # Check for Python 3
    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
        log_warn "Python 3 not found"
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing prerequisites: ${missing[*]}"
        
        # Offer to install Node.js
        if [[ " ${missing[*]} " =~ " node " ]] || [[ " ${missing[*]} " =~ " npm " ]]; then
            if [[ "$AUTO_MODE" == "true" ]] || [[ "$ENV_TYPE" == "colab" ]]; then
                log_info "Attempting to install Node.js..."
                install_nodejs
            else
                read -p "Install Node.js now? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    install_nodejs
                else
                    log_error "Cannot continue without Node.js"
                    exit 1
                fi
            fi
        fi
    else
        log_success "All prerequisites satisfied"
    fi
}

# Install Node.js
install_nodejs() {
    log_step "Installing Node.js..."
    
    if command -v apt-get &>/dev/null; then
        # Debian/Ubuntu
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo -E apt-get install -y nodejs
    elif command -v yum &>/dev/null; then
        # RHEL/CentOS
        curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo -E bash -
        sudo -E yum install -y nodejs
    elif command -v dnf &>/dev/null; then
        # Fedora
        curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo -E bash -
        sudo -E dnf install -y nodejs
    elif command -v pacman &>/dev/null; then
        # Arch Linux
        sudo -E pacman -S --noconfirm nodejs npm
    elif command -v brew &>/dev/null; then
        # macOS
        brew install node
    else
        # Fallback: use nvm
        log_info "Installing via nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        source ~/.nvm/nvm.sh
        nvm install --lts
        nvm use --lts
    fi
    
    # Verify installation
    if command -v node &>/dev/null && command -v npm &>/dev/null; then
        log_success "Node.js installed: $(node --version)"
        log_success "npm installed: $(npm --version)"
    else
        log_error "Failed to install Node.js"
        exit 1
    fi
}

# Install KiloCode CLI
install_kilocode() {
    log_step "Installing KiloCode CLI..."
    
    # Check if already installed
    if command -v kilo &>/dev/null; then
        local current_version
        current_version=$(kilo --version 2>/dev/null || echo "unknown")
        log_info "KiloCode CLI already installed: ${current_version}"
        
        if [[ "$AUTO_MODE" == "true" ]]; then
            log_info "Auto mode: skipping reinstall"
            return 0
        fi
        
        read -p "Reinstall/update KiloCode? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    # Install globally via npm
    log_info "Installing ${KILOCODE_PACKAGE}..."
    
    if npm install -g "${KILOCODE_PACKAGE}" 2>&1; then
        log_success "KiloCode CLI installed successfully"
    else
        log_warn "Global install failed, trying alternative methods..."
        
        # Try with sudo
        if sudo npm install -g "${KILOCODE_PACKAGE}" 2>&1; then
            log_success "KiloCode CLI installed with sudo"
        else
            log_error "Failed to install KiloCode CLI"
            exit 1
        fi
    fi
    
    # Verify installation
    if command -v kilo &>/dev/null; then
        log_success "KiloCode version: $(kilo --version 2>/dev/null || echo 'installed')"
    else
        log_error "KiloCode CLI not found in PATH"
        exit 1
    fi
}

# Setup Python integration
setup_python_integration() {
    log_step "Setting up Python integration..."
    
    # Find KISWARM backend directory
    local backend_dir=""
    local possible_dirs=(
        "/home/z/my-project/backend/python"
        "/home/sah/KISWARM/backend/python"
        "./backend/python"
        "../backend/python"
    )
    
    for dir in "${possible_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            backend_dir="$dir"
            break
        fi
    done
    
    if [[ -z "$backend_dir" ]]; then
        log_warn "KISWARM backend not found, creating module structure..."
        mkdir -p ./kibank
        backend_dir="./kibank"
    fi
    
    # Create symlink or copy the bridge module
    local bridge_src="/home/z/my-project/backend/python/kibank/m81_kilocode_bridge.py"
    local bridge_dest="${backend_dir}/kibank/m81_kilocode_bridge.py"
    
    if [[ -f "$bridge_src" ]]; then
        mkdir -p "$(dirname "$bridge_dest")"
        cp "$bridge_src" "$bridge_dest"
        log_success "Bridge module installed to: ${bridge_dest}"
    else
        log_warn "Bridge module source not found: ${bridge_src}"
    fi
    
    # Update __init__.py if it exists
    local init_file="${backend_dir}/kibank/__init__.py"
    if [[ -f "$init_file" ]]; then
        if ! grep -q "m81_kilocode_bridge" "$init_file"; then
            echo "" >> "$init_file"
            echo "# M81: KiloCode Bridge - Parallel Safety Net" >> "$init_file"
            echo "try:" >> "$init_file"
            echo "    from .m81_kilocode_bridge import (" >> "$init_file"
            echo "        KiloCodeBridge," >> "$init_file"
            echo "        KiloCodeConfig," >> "$init_file"
            echo "        get_kilocode_bridge," >> "$init_file"
            echo "        initialize_kilocode_bridge," >> "$init_file"
            echo "        setup_kilocode_for_environment," >> "$init_file"
            echo "    )" >> "$init_file"
            echo "except ImportError:" >> "$init_file"
            echo "    pass  # KiloCode not available" >> "$init_file"
            log_success "Updated __init__.py with KiloCode imports"
        fi
    fi
}

# Setup Docker integration
setup_docker_integration() {
    log_step "Setting up Docker integration..."
    
    local dockerfile="/home/z/my-project/Dockerfile"
    
    if [[ -f "$dockerfile" ]]; then
        # Check if KiloCode is already in Dockerfile
        if grep -q "kilocode" "$dockerfile"; then
            log_info "KiloCode already configured in Dockerfile"
            return 0
        fi
        
        # Add KiloCode installation to Dockerfile
        cat >> "$dockerfile" << 'DOCKERFILE_EOF'

# KiloCode Parallel Safety Net
RUN npm install -g @kilocode/cli
ENV KILOCODE_AUTO_MODE=true
DOCKERFILE_EOF
        
        log_success "Updated Dockerfile with KiloCode installation"
    else
        log_warn "Dockerfile not found at ${dockerfile}"
    fi
    
    # Update docker-compose.yml
    local compose_file="/home/z/my-project/docker-compose.yml"
    if [[ -f "$compose_file" ]]; then
        if grep -q "KILOCODE" "$compose_file"; then
            log_info "KiloCode already configured in docker-compose.yml"
            return 0
        fi
        
        # Add KiloCode environment variable to services
        sed -i '/environment:/a\      - KILOCODE_AUTO_MODE=true' "$compose_file"
        log_success "Updated docker-compose.yml with KiloCode environment"
    fi
}

# Setup virtualenv integration
setup_venv_integration() {
    log_step "Setting up virtualenv integration..."
    
    # List of known virtualenvs
    local venvs=(
        "bridge-venv"
        "opensandbox-venv"
        "mem0_env"
    )
    
    # Check if we're in a venv
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log_info "Currently in virtualenv: ${VIRTUAL_ENV}"
        
        # Install bridge module to current venv
        local site_packages="${VIRTUAL_ENV}/lib/python*/site-packages"
        local target_dir=$(ls -d ${site_packages}/kibank 2>/dev/null | head -1)
        
        if [[ -n "$target_dir" ]]; then
            cp "/home/z/my-project/backend/python/kibank/m81_kilocode_bridge.py" "${target_dir}/" 2>/dev/null || true
            log_success "Bridge module installed to current venv"
        fi
    fi
    
    # Check for venvs in common locations
    local venv_dirs=(
        "/home/z/my-project/venvs"
        "/home/sah/venvs"
        "${HOME}/venvs"
        "${HOME}/.virtualenvs"
    )
    
    for venv_dir in "${venv_dirs[@]}"; do
        if [[ -d "$venv_dir" ]]; then
            for venv in "${venvs[@]}"; do
                local venv_path="${venv_dir}/${venv}"
                if [[ -d "$venv_path" ]]; then
                    log_info "Found virtualenv: ${venv_path}"
                fi
            done
        fi
    done
}

# Configure for autonomous operation
configure_autonomous_mode() {
    log_step "Configuring autonomous mode..."
    
    # Create config directory
    mkdir -p "${HOME}/.kiswarm"
    
    # Create KiloCode configuration
    cat > "${HOME}/.kiswarm/kilocode_config.json" << EOF
{
    "bridge_name": "kiswarm-kilocode-bridge",
    "autonomous_mode": ${AUTO_MODE},
    "enable_safety_net": true,
    "fallback_on_error": true,
    "max_retries": 3,
    "heartbeat_interval": 30.0,
    "connection_timeout": 10.0,
    "auto_install": true,
    "environment": "${ENV_TYPE}",
    "created_at": "$(date -Iseconds)"
}
EOF
    
    log_success "Configuration saved to ${HOME}/.kiswarm/kilocode_config.json"
}

# Start the bridge
start_bridge() {
    if [[ "$NO_START" == "true" ]]; then
        log_info "Skipping bridge startup (--no-start)"
        return 0
    fi
    
    log_step "Starting KiloCode bridge..."
    
    # Run Python test to verify bridge
    python3 -c "
import sys
sys.path.insert(0, '/home/z/my-project/backend/python')
from kibank.m81_kilocode_bridge import (
    initialize_kilocode_bridge,
    setup_kilocode_for_environment,
    test_kilocode_bridge
)

# Run tests
results = test_kilocode_bridge()
print('Bridge test results:')
for test, result in results['tests'].items():
    status = '✓' if result.get('success') else '✗'
    print(f'  {status} {test}')

# Setup for environment
setup_result = setup_kilocode_for_environment(auto_start=True)
print(f'\\nBridge status: {setup_result[\"bridge_status\"][\"bridge_status\"]}')
" 2>&1
    
    if [[ $? -eq 0 ]]; then
        log_success "KiloCode bridge started successfully"
    else
        log_warn "Bridge test had issues (may be normal if KiloCode not yet configured)"
    fi
}

# Test KiloCode CLI
test_kilocode_cli() {
    log_step "Testing KiloCode CLI..."
    
    if ! command -v kilo &>/dev/null; then
        log_error "KiloCode CLI not installed"
        return 1
    fi
    
    # Test version command
    if kilo --version &>/dev/null; then
        log_success "KiloCode CLI is operational"
    else
        log_warn "KiloCode CLI version check failed"
    fi
    
    # Test help command
    if kilo --help &>/dev/null; then
        log_success "KiloCode CLI help available"
    else
        log_warn "KiloCode CLI help check failed"
    fi
}

# Create startup service
create_startup_service() {
    log_step "Creating startup service..."
    
    local service_file="/home/z/my-project/config/kilocode-bridge.service"
    mkdir -p "$(dirname "$service_file")"
    
    cat > "$service_file" << EOF
[Unit]
Description=KISWARM KiloCode Bridge Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=/home/z/my-project
Environment=PYTHONPATH=/home/z/my-project/backend/python:/home/z/my-project/backend
ExecStart=/usr/bin/python3 -c "from kibank.m81_kilocode_bridge import initialize_kilocode_bridge; initialize_kilocode_bridge(auto_start=True); import time; while True: time.sleep(60)"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Service file created: ${service_file}"
    
    # Optionally install as system service
    if [[ "$AUTO_MODE" == "false" ]] && [[ "$ENV_TYPE" != "docker" ]] && [[ "$ENV_TYPE" != "colab" ]]; then
        read -p "Install as system service? (requires sudo) (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo cp "$service_file" /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable kilocode-bridge.service
            log_success "Service installed and enabled"
        fi
    fi
}

# Summary
print_summary() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                 Setup Complete Summary                       ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${GREEN}Environment:${NC} ${ENV_TYPE}"
    echo ""
    
    echo -e "${GREEN}KiloCode CLI:${NC}"
    if command -v kilo &>/dev/null; then
        echo "  ✓ Installed: $(kilo --version 2>/dev/null || echo 'version unknown')"
    else
        echo "  ✗ Not installed"
    fi
    echo ""
    
    echo -e "${GREEN}Bridge Module:${NC}"
    if [[ -f "/home/z/my-project/backend/python/kibank/m81_kilocode_bridge.py" ]]; then
        echo "  ✓ m81_kilocode_bridge.py"
    else
        echo "  ✗ Not found"
    fi
    echo ""
    
    echo -e "${GREEN}Configuration:${NC}"
    if [[ -f "${HOME}/.kiswarm/kilocode_config.json" ]]; then
        echo "  ✓ ${HOME}/.kiswarm/kilocode_config.json"
    else
        echo "  ✗ Not created"
    fi
    echo ""
    
    echo -e "${GREEN}Quick Commands:${NC}"
    echo "  kilo                    # Start KiloCode CLI"
    echo "  kilo run 'prompt'       # Run with prompt"
    echo "  kilo run --auto 'task'  # Autonomous mode (CI/CD)"
    echo ""
    
    echo -e "${GREEN}Python Bridge:${NC}"
    echo "  from kibank.m81_kilocode_bridge import get_kilocode_bridge"
    echo "  bridge = get_kilocode_bridge()"
    echo "  bridge.start()"
    echo ""
    
    echo -e "${GREEN}Safety Net Usage:${NC}"
    echo "  result = await bridge.code_review(code)"
    echo "  result = await bridge.security_scan(code)"
    echo "  result = await bridge.debug_request(error, code)"
    echo ""
}

# Main execution
main() {
    log_info "Starting KiloCode parallel safety net setup..."
    
    detect_environment
    check_prerequisites
    install_kilocode
    setup_python_integration
    
    if [[ "$ENV_TYPE" == "docker" ]]; then
        setup_docker_integration
    fi
    
    setup_venv_integration
    configure_autonomous_mode
    test_kilocode_cli
    start_bridge
    
    if [[ "$AUTO_MODE" == "false" ]]; then
        create_startup_service
    fi
    
    print_summary
    
    log_success "KiloCode parallel safety net setup complete!"
}

# Run main
main "$@"
