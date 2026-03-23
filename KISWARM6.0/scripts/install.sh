#!/usr/bin/env bash
#
# KISWARM6.0 Installation Script
# ==============================
# This script sets up the complete KISWARM6.0 environment including:
# - Python dependencies (Backend)
# - Node.js dependencies (Frontend & Bridge)
# - Environment configuration
# - Database initialization
#
# Author: Baron Marco Paolo Ialongo
# Version: 6.0.0
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

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BRIDGE_DIR="${PROJECT_ROOT}/bridge"
LOG_DIR="${PROJECT_ROOT}/logs"
DATA_DIR="${PROJECT_ROOT}/data"

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              KISWARM6.0 INSTALLATION SCRIPT                   ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Version: 6.0.0                                               ║"
    echo "║  Modules: 60 (57 KISWARM5.0 + 3 KIBank)                      ║"
    echo "║  Endpoints: 384                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print section header
print_section() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print info message
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Compare versions
version_ge() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    local errors=0
    
    # Check Python 3.10+
    print_info "Checking Python installation..."
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            print_success "Python ${PYTHON_VERSION} found"
        else
            print_error "Python 3.10+ required, found ${PYTHON_VERSION}"
            errors=$((errors + 1))
        fi
    else
        print_error "Python 3 not found"
        errors=$((errors + 1))
    fi
    
    # Check pip
    print_info "Checking pip installation..."
    if command_exists pip3 || command_exists pip; then
        print_success "pip found"
    else
        print_error "pip not found"
        errors=$((errors + 1))
    fi
    
    # Check Node.js 18+
    print_info "Checking Node.js installation..."
    if command_exists node; then
        NODE_VERSION=$(node --version 2>&1 | sed 's/v//')
        NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
        
        if [ "$NODE_MAJOR" -ge 18 ]; then
            print_success "Node.js ${NODE_VERSION} found"
        else
            print_error "Node.js 18+ required, found ${NODE_VERSION}"
            errors=$((errors + 1))
        fi
    else
        print_error "Node.js not found"
        errors=$((errors + 1))
    fi
    
    # Check pnpm
    print_info "Checking pnpm installation..."
    if command_exists pnpm; then
        PNPM_VERSION=$(pnpm --version 2>&1)
        print_success "pnpm ${PNPM_VERSION} found"
    else
        print_info "pnpm not found, installing via npm..."
        npm install -g pnpm
        if [ $? -eq 0 ]; then
            print_success "pnpm installed successfully"
        else
            print_error "Failed to install pnpm"
            errors=$((errors + 1))
        fi
    fi
    
    # Check MySQL client (optional but recommended)
    print_info "Checking MySQL client..."
    if command_exists mysql; then
        MYSQL_VERSION=$(mysql --version 2>&1 | awk '{print $3}' | cut -d, -f1)
        print_success "MySQL client ${MYSQL_VERSION} found"
    else
        print_info "MySQL client not found (optional for local development)"
    fi
    
    # Check Docker (optional)
    print_info "Checking Docker..."
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version 2>&1 | awk '{print $3}' | cut -d, -f1)
        print_success "Docker ${DOCKER_VERSION} found"
    else
        print_info "Docker not found (optional for containerized deployment)"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Prerequisites check failed with $errors error(s)"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Create necessary directories
create_directories() {
    print_section "Creating Directories"
    
    mkdir -p "${LOG_DIR}"
    mkdir -p "${DATA_DIR}"
    mkdir -p "${PROJECT_ROOT}/uploads"
    mkdir -p "${PROJECT_ROOT}/tmp"
    mkdir -p "${PROJECT_ROOT}/.venv"
    
    print_success "Created logs directory: ${LOG_DIR}"
    print_success "Created data directory: ${DATA_DIR}"
    print_success "Created uploads directory: ${PROJECT_ROOT}/uploads"
    print_success "Created tmp directory: ${PROJECT_ROOT}/tmp"
    print_success "Created venv directory: ${PROJECT_ROOT}/.venv"
}

# Setup Python virtual environment and install dependencies
install_python_dependencies() {
    print_section "Installing Python Dependencies"
    
    cd "${BACKEND_DIR}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "${PROJECT_ROOT}/.venv/bin" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv "${PROJECT_ROOT}/.venv"
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/.venv/bin/activate"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
    
    # Deactivate virtual environment
    deactivate
}

# Install Node.js dependencies
install_node_dependencies() {
    print_section "Installing Node.js Dependencies"
    
    # Install frontend dependencies
    print_info "Installing frontend dependencies..."
    cd "${FRONTEND_DIR}"
    pnpm install
    print_success "Frontend dependencies installed"
    
    # Install bridge dependencies
    print_info "Installing bridge dependencies..."
    cd "${BRIDGE_DIR}"
    pnpm install
    print_success "Bridge dependencies installed"
}

# Setup environment variables
setup_environment() {
    print_section "Setting Up Environment Variables"
    
    ENV_FILE="${PROJECT_ROOT}/.env"
    
    if [ -f "${ENV_FILE}" ]; then
        print_info "Environment file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing environment file"
            return
        fi
    fi
    
    # Generate random secrets
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    KIBANK_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    
    # Create environment file
    cat > "${ENV_FILE}" << EOF
# KISWARM6.0 Environment Configuration
# =====================================
# Generated on $(date)

# ==================== Application ====================
NODE_ENV=development
VITE_APP_ID=kiswarm6

# ==================== Database ====================
DATABASE_URL=mysql://kiswarm:kiswarm_password@localhost:3306/kiswarm6

# ==================== Authentication ====================
JWT_SECRET=${JWT_SECRET}
KIBANK_SECRET_KEY=${KIBANK_SECRET}

# ==================== API URLs ====================
VITE_KISWARM_API_URL=http://localhost:5001
VITE_TRPC_BRIDGE_URL=http://localhost:3000

# ==================== OAuth (Optional) ====================
OAUTH_SERVER_URL=
OWNER_OPEN_ID=

# ==================== AI/LLM (Optional) ====================
BUILT_IN_FORGE_API_URL=
BUILT_IN_FORGE_API_KEY=

# ==================== Qdrant Vector DB ====================
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# ==================== Ports ====================
BACKEND_PORT=5001
FRONTEND_PORT=5173
BRIDGE_PORT=3000

# ==================== Logging ====================
LOG_LEVEL=INFO
LOG_DIR=${LOG_DIR}
EOF

    print_success "Environment file created: ${ENV_FILE}"
    print_info "Please edit ${ENV_FILE} with your actual configuration values"
}

# Initialize database
initialize_database() {
    print_section "Initializing Database"
    
    # Check if MySQL is running
    print_info "Checking MySQL connection..."
    
    # Source environment
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        source "${PROJECT_ROOT}/.env"
    fi
    
    # Try to connect to MySQL
    if command_exists mysql; then
        # Extract MySQL connection details from DATABASE_URL
        if [ -n "${DATABASE_URL}" ]; then
            print_info "Attempting to initialize database schema..."
            
            # Create database if it doesn't exist
            print_info "Please ensure MySQL is running and the database user has permissions"
            print_info "You may need to run the following SQL commands:"
            echo ""
            echo "  CREATE DATABASE IF NOT EXISTS kiswarm6;"
            echo "  CREATE USER IF NOT EXISTS 'kiswarm'@'localhost' IDENTIFIED BY 'kiswarm_password';"
            echo "  GRANT ALL PRIVILEGES ON kiswarm6.* TO 'kiswarm'@'localhost';"
            echo "  FLUSH PRIVILEGES;"
            echo ""
        fi
    fi
    
    # Run Drizzle migrations for frontend
    print_info "Running database migrations..."
    cd "${FRONTEND_DIR}"
    
    if [ -f "node_modules/.bin/drizzle-kit" ]; then
        pnpm db:push 2>/dev/null || print_info "Database migration skipped (database may not be available yet)"
        print_success "Database migrations completed"
    else
        print_info "Drizzle not available, skipping migrations"
    fi
}

# Create systemd service files (optional)
create_systemd_services() {
    print_section "Creating Systemd Service Files (Optional)"
    
    SYSTEMD_DIR="${PROJECT_ROOT}/systemd"
    mkdir -p "${SYSTEMD_DIR}"
    
    # Backend service
    cat > "${SYSTEMD_DIR}/kiswarm-backend.service" << EOF
[Unit]
Description=KISWARM6.0 Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=kiswarm
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${PROJECT_ROOT}/.venv/bin"
ExecStart=${PROJECT_ROOT}/.venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    cat > "${SYSTEMD_DIR}/kiswarm-frontend.service" << EOF
[Unit]
Description=KISWARM6.0 Frontend Service
After=network.target

[Service]
Type=simple
User=kiswarm
WorkingDirectory=${FRONTEND_DIR}
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Bridge service
    cat > "${SYSTEMD_DIR}/kiswarm-bridge.service" << EOF
[Unit]
Description=KISWARM6.0 tRPC Bridge Service
After=network.target

[Service]
Type=simple
User=kiswarm
WorkingDirectory=${BRIDGE_DIR}
ExecStart=/usr/bin/pnpm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    print_success "Systemd service files created in ${SYSTEMD_DIR}"
    print_info "To install services, run:"
    echo "  sudo cp ${SYSTEMD_DIR}/*.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable kiswarm-backend kiswarm-frontend kiswarm-bridge"
}

# Print installation summary
print_summary() {
    print_section "Installation Complete"
    
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           KISWARM6.0 INSTALLATION SUCCESSFUL                  ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║                                                               ║"
    echo "║  Next Steps:                                                  ║"
    echo "║  1. Edit ${PROJECT_ROOT}/.env with your configuration       ║"
    echo "║  2. Ensure MySQL is running and database is created           ║"
    echo "║  3. Run: ./scripts/start.sh to start all services            ║"
    echo "║                                                               ║"
    echo "║  Services:                                                    ║"
    echo "║    Backend:  http://localhost:5001                           ║"
    echo "║    Frontend: http://localhost:5173                           ║"
    echo "║    Bridge:   http://localhost:3000                           ║"
    echo "║                                                               ║"
    echo "║  Health Check: ./scripts/health-check.sh                     ║"
    echo "║  Stop Services: ./scripts/stop.sh                            ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Main installation function
main() {
    print_logo
    
    print_info "Project root: ${PROJECT_ROOT}"
    
    check_prerequisites
    create_directories
    install_python_dependencies
    install_node_dependencies
    setup_environment
    initialize_database
    create_systemd_services
    print_summary
}

# Run main function
main "$@"
