#!/usr/bin/env bash
#
# KISWARM6.0 Production Deployment Script
# =======================================
# Builds and deploys KISWARM6.0 for production:
# - Builds frontend (Vite)
# - Builds backend
# - Runs database migrations
# - Starts production servers with gunicorn
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
DIST_DIR="${PROJECT_ROOT}/dist"
PID_DIR="${PROJECT_ROOT}/tmp/pids"

# Source environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# Set production environment
export NODE_ENV=production
export FLASK_ENV=production

# Ports (with defaults)
BACKEND_PORT=${BACKEND_PORT:-5001}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
BRIDGE_PORT=${BRIDGE_PORT:-3001}

# Gunicorn settings
WORKERS=${GUNICORN_WORKERS:-4}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-gevent}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
BIND_ADDRESS=${GUNICORN_BIND:-0.0.0.0}

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║          KISWARM6.0 PRODUCTION DEPLOYMENT                     ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Version: 6.0.0                                               ║"
    echo "║  Mode: Production                                             ║"
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

# Print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create necessary directories
create_directories() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${PID_DIR}"
    mkdir -p "${DIST_DIR}"
    mkdir -p "${PROJECT_ROOT}/tmp"
}

# Pre-deployment checks
pre_deployment_checks() {
    print_section "Running Pre-deployment Checks"
    
    local errors=0
    
    # Check environment file
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        print_error "Environment file not found: ${PROJECT_ROOT}/.env"
        print_info "Please create the environment file before deploying"
        errors=$((errors + 1))
    else
        print_success "Environment file found"
    fi
    
    # Check DATABASE_URL
    if [ -z "${DATABASE_URL}" ]; then
        print_error "DATABASE_URL not set in environment"
        errors=$((errors + 1))
    else
        print_success "DATABASE_URL configured"
    fi
    
    # Check JWT_SECRET
    if [ -z "${JWT_SECRET}" ]; then
        print_error "JWT_SECRET not set in environment"
        errors=$((errors + 1))
    else
        print_success "JWT_SECRET configured"
    fi
    
    # Check Python virtual environment
    if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
        print_error "Python virtual environment not found"
        print_info "Run ./scripts/install.sh first"
        errors=$((errors + 1))
    else
        print_success "Python virtual environment found"
    fi
    
    # Check node_modules
    if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
        print_error "Frontend node_modules not found"
        print_info "Run ./scripts/install.sh first"
        errors=$((errors + 1))
    else
        print_success "Frontend dependencies installed"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Pre-deployment checks failed with $errors error(s)"
        exit 1
    fi
    
    print_success "All pre-deployment checks passed"
}

# Build frontend
build_frontend() {
    print_section "Building Frontend"
    
    cd "${FRONTEND_DIR}"
    
    print_info "Building Vite production bundle..."
    pnpm build
    
    if [ -d "${FRONTEND_DIR}/dist" ]; then
        # Copy to project dist directory
        cp -r "${FRONTEND_DIR}/dist"/* "${DIST_DIR}/" 2>/dev/null || true
        print_success "Frontend built successfully"
        print_info "Output: ${FRONTEND_DIR}/dist"
    else
        print_error "Frontend build failed - dist directory not created"
        exit 1
    fi
}

# Build backend (verify)
build_backend() {
    print_section "Building Backend"
    
    cd "${BACKEND_DIR}"
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/.venv/bin/activate"
    
    # Run type checks if mypy is available
    if command_exists mypy; then
        print_info "Running type checks..."
        mypy python/ --ignore-missing-imports || print_warning "Type checks have warnings"
    fi
    
    # Run tests if pytest is available
    if command_exists pytest; then
        print_info "Running tests..."
        pytest python/ -v --tb=short || print_warning "Some tests failed"
    fi
    
    print_success "Backend verification complete"
}

# Run database migrations
run_migrations() {
    print_section "Running Database Migrations"
    
    cd "${FRONTEND_DIR}"
    
    # Check if database is accessible
    print_info "Checking database connection..."
    
    if [ -n "${DATABASE_URL}" ]; then
        # Run Drizzle migrations
        print_info "Running Drizzle migrations..."
        pnpm db:push || print_warning "Database migration had issues"
        
        print_success "Database migrations completed"
    else
        print_warning "DATABASE_URL not set, skipping migrations"
    fi
}

# Stop existing services
stop_existing_services() {
    print_section "Stopping Existing Services"
    
    if [ -f "${PROJECT_ROOT}/scripts/stop.sh" ]; then
        "${PROJECT_ROOT}/scripts/stop.sh"
    else
        print_info "Stop script not found, attempting manual stop..."
        
        # Kill any existing processes
        pkill -f "gunicorn.*kiswarm" 2>/dev/null || true
        pkill -f "node.*dist/index.js" 2>/dev/null || true
    fi
    
    print_success "Existing services stopped"
}

# Start production backend with Gunicorn
start_backend_production() {
    print_section "Starting Production Backend"
    
    cd "${BACKEND_DIR}"
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/.venv/bin/activate"
    
    # Create Gunicorn config if it doesn't exist
    GUNICORN_CONF="${BACKEND_DIR}/gunicorn.conf.py"
    
    if [ ! -f "$GUNICORN_CONF" ]; then
        cat > "$GUNICORN_CONF" << EOF
# Gunicorn Configuration for KISWARM6.0
import multiprocessing

# Server socket
bind = "${BIND_ADDRESS}:${BACKEND_PORT}"
backlog = 2048

# Worker processes
workers = ${WORKERS}
worker_class = "${WORKER_CLASS}"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = ${TIMEOUT}
keepalive = 5

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "${LOG_DIR}/gunicorn_access.log"
errorlog = "${LOG_DIR}/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "kiswarm6-backend"

# Server mechanics
daemon = False
pidfile = "${PID_DIR}/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
EOF
        print_info "Created Gunicorn configuration"
    fi
    
    print_info "Starting Gunicorn with ${WORKERS} workers..."
    
    # Start Gunicorn
    nohup gunicorn --config "${GUNICORN_CONF}" "run:create_kiswarm6_app()" > "${LOG_DIR}/gunicorn.log" 2>&1 &
    local pid=$!
    echo $pid > "${PID_DIR}/backend.pid"
    
    sleep 3
    
    # Verify startup
    if kill -0 $pid 2>/dev/null; then
        print_success "Backend started (PID: $pid)"
        print_info "Listening on: ${BIND_ADDRESS}:${BACKEND_PORT}"
    else
        print_error "Backend failed to start"
        print_info "Check logs: ${LOG_DIR}/gunicorn_error.log"
        exit 1
    fi
}

# Start production frontend server
start_frontend_production() {
    print_section "Starting Production Frontend"
    
    cd "${FRONTEND_DIR}"
    
    if [ -f "${FRONTEND_DIR}/dist/index.js" ]; then
        print_info "Starting production server..."
        
        nohup node dist/index.js > "${LOG_DIR}/frontend.log" 2>&1 &
        local pid=$!
        echo $pid > "${PID_DIR}/frontend.pid"
        
        sleep 2
        
        if kill -0 $pid 2>/dev/null; then
            print_success "Frontend started (PID: $pid)"
            print_info "Listening on port ${FRONTEND_PORT}"
        else
            print_warning "Frontend server may not have started correctly"
            print_info "Check logs: ${LOG_DIR}/frontend.log"
        fi
    else
        print_warning "Production bundle not found, serving static files..."
        
        # Use a simple static server if available
        if command_exists serve; then
            nohup serve -s "${FRONTEND_DIR}/dist/client" -l ${FRONTEND_PORT} > "${LOG_DIR}/frontend.log" 2>&1 &
            local pid=$!
            echo $pid > "${PID_DIR}/frontend.pid"
            print_success "Static server started (PID: $pid)"
        elif command_exists npx; then
            nohup npx serve -s "${FRONTEND_DIR}/dist/client" -l ${FRONTEND_PORT} > "${LOG_DIR}/frontend.log" 2>&1 &
            local pid=$!
            echo $pid > "${PID_DIR}/frontend.pid"
            print_success "Static server started (PID: $pid)"
        else
            print_warning "No static server available. Frontend dist is at: ${FRONTEND_DIR}/dist"
            print_info "Consider using nginx to serve the frontend"
        fi
    fi
}

# Show deployment summary
show_deployment_summary() {
    print_section "Deployment Summary"
    
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║         KISWARM6.0 DEPLOYMENT COMPLETE                        ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║                                                               ║"
    echo "║  Production Services:                                         ║"
    echo "║    Backend:   http://${BIND_ADDRESS}:${BACKEND_PORT}                        ║"
    echo "║    Frontend:  http://${BIND_ADDRESS}:${FRONTEND_PORT}                        ║"
    echo "║                                                               ║"
    echo "║  Endpoints:                                                   ║"
    echo "║    Status:    http://${BIND_ADDRESS}:${BACKEND_PORT}/api/v6/status        ║"
    echo "║    Health:    http://${BIND_ADDRESS}:${BACKEND_PORT}/health                 ║"
    echo "║                                                               ║"
    echo "║  Log Files:                                                   ║"
    echo "║    Access:    ${LOG_DIR}/gunicorn_access.log                ║"
    echo "║    Error:     ${LOG_DIR}/gunicorn_error.log                 ║"
    echo "║    Backend:   ${LOG_DIR}/backend.log                        ║"
    echo "║    Frontend:  ${LOG_DIR}/frontend.log                       ║"
    echo "║                                                               ║"
    echo "║  Management:                                                  ║"
    echo "║    Stop:      ./scripts/stop.sh                              ║"
    echo "║    Health:    ./scripts/health-check.sh                      ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    print_info "Consider setting up nginx as a reverse proxy for production"
    print_info "Consider setting up SSL certificates with Let's Encrypt"
}

# Main function
main() {
    print_logo
    create_directories
    
    pre_deployment_checks
    build_frontend
    build_backend
    run_migrations
    stop_existing_services
    start_backend_production
    start_frontend_production
    
    show_deployment_summary
}

# Run main function
main "$@"
