#!/usr/bin/env bash
#
# KISWARM6.0 Start Script
# =======================
# Starts all KISWARM6.0 services:
# - Backend (Flask on port 5001)
# - tRPC Bridge (port 3000)
# - Frontend (Vite dev server on port 5173)
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
PID_DIR="${PROJECT_ROOT}/tmp/pids"

# Source environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# Ports (with defaults)
BACKEND_PORT=${BACKEND_PORT:-5001}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BRIDGE_PORT=${BRIDGE_PORT:-3000}

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              KISWARM6.0 START SCRIPT                          ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Version: 6.0.0                                               ║"
    echo "║  Modules: 60 (57 KISWARM5.0 + 3 KIBank)                      ║"
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

# Check if a process is running on a port
is_port_in_use() {
    local port=$1
    if command_exists lsof; then
        lsof -i :$port >/dev/null 2>&1
    elif command_exists ss; then
        ss -tuln | grep -q ":$port "
    elif command_exists netstat; then
        netstat -tuln | grep -q ":$port "
    else
        return 1
    fi
}

# Get PID of process on port
get_pid_on_port() {
    local port=$1
    if command_exists lsof; then
        lsof -t -i :$port 2>/dev/null
    elif command_exists ss; then
        ss -tuln -p | grep ":$port " | sed 's/.*pid=\([0-9]*\).*/\1/' | head -1
    else
        echo ""
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create necessary directories
create_directories() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${PID_DIR}"
    mkdir -p "${PROJECT_ROOT}/tmp"
}

# Check if services are already running
check_existing_services() {
    print_section "Checking Existing Services"
    
    local running=0
    
    if is_port_in_use $BACKEND_PORT; then
        print_warning "Backend already running on port ${BACKEND_PORT}"
        running=$((running + 1))
    fi
    
    if is_port_in_use $FRONTEND_PORT; then
        print_warning "Frontend already running on port ${FRONTEND_PORT}"
        running=$((running + 1))
    fi
    
    if is_port_in_use $BRIDGE_PORT; then
        print_warning "Bridge already running on port ${BRIDGE_PORT}"
        running=$((running + 1))
    fi
    
    if [ $running -gt 0 ]; then
        read -p "Do you want to stop existing services and restart? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            "${PROJECT_ROOT}/scripts/stop.sh"
            sleep 2
        else
            print_info "Continuing with existing services..."
        fi
    fi
}

# Start backend service
start_backend() {
    print_section "Starting Backend (Flask)"
    
    if is_port_in_use $BACKEND_PORT; then
        print_warning "Backend already running on port ${BACKEND_PORT}"
        return 0
    fi
    
    cd "${BACKEND_DIR}"
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/.venv/bin/activate"
    
    # Start backend in background
    print_info "Starting Flask server on port ${BACKEND_PORT}..."
    
    nohup python run.py > "${LOG_DIR}/backend.log" 2>&1 &
    local pid=$!
    echo $pid > "${PID_DIR}/backend.pid"
    
    # Wait for backend to start
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if is_port_in_use $BACKEND_PORT; then
            print_success "Backend started (PID: $pid)"
            print_info "Logs: ${LOG_DIR}/backend.log"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    print_error "Backend failed to start within ${max_attempts} seconds"
    print_info "Check logs: ${LOG_DIR}/backend.log"
    return 1
}

# Start tRPC bridge service
start_bridge() {
    print_section "Starting tRPC Bridge"
    
    if is_port_in_use $BRIDGE_PORT; then
        print_warning "Bridge already running on port ${BRIDGE_PORT}"
        return 0
    fi
    
    cd "${BRIDGE_DIR}"
    
    # Start bridge in background
    print_info "Starting tRPC bridge on port ${BRIDGE_PORT}..."
    
    nohup pnpm dev > "${LOG_DIR}/bridge.log" 2>&1 &
    local pid=$!
    echo $pid > "${PID_DIR}/bridge.pid"
    
    # Wait for bridge to start
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if is_port_in_use $BRIDGE_PORT; then
            print_success "Bridge started (PID: $pid)"
            print_info "Logs: ${LOG_DIR}/bridge.log"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    print_error "Bridge failed to start within ${max_attempts} seconds"
    print_info "Check logs: ${LOG_DIR}/bridge.log"
    return 1
}

# Start frontend service
start_frontend() {
    print_section "Starting Frontend (Vite)"
    
    if is_port_in_use $FRONTEND_PORT; then
        print_warning "Frontend already running on port ${FRONTEND_PORT}"
        return 0
    fi
    
    cd "${FRONTEND_DIR}"
    
    # Start frontend in background
    print_info "Starting Vite dev server on port ${FRONTEND_PORT}..."
    
    nohup pnpm dev > "${LOG_DIR}/frontend.log" 2>&1 &
    local pid=$!
    echo $pid > "${PID_DIR}/frontend.pid"
    
    # Wait for frontend to start
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if is_port_in_use $FRONTEND_PORT; then
            print_success "Frontend started (PID: $pid)"
            print_info "Logs: ${LOG_DIR}/frontend.log"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    print_error "Frontend failed to start within ${max_attempts} seconds"
    print_info "Check logs: ${LOG_DIR}/frontend.log"
    return 1
}

# Show status dashboard
show_dashboard() {
    print_section "KISWARM6.0 Status Dashboard"
    
    # Get PIDs
    local backend_pid=""
    local frontend_pid=""
    local bridge_pid=""
    
    [ -f "${PID_DIR}/backend.pid" ] && backend_pid=$(cat "${PID_DIR}/backend.pid")
    [ -f "${PID_DIR}/frontend.pid" ] && frontend_pid=$(cat "${PID_DIR}/frontend.pid")
    [ -f "${PID_DIR}/bridge.pid" ] && bridge_pid=$(cat "${PID_DIR}/bridge.pid")
    
    echo -e "${CYAN}"
    echo "┌─────────────────┬───────────┬─────────┬─────────────────────────────────┐"
    echo "│ Service         │ Port      │ Status  │ PID                             │"
    echo "├─────────────────┼───────────┼─────────┼─────────────────────────────────┤"
    
    # Backend status
    if is_port_in_use $BACKEND_PORT; then
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │ %-31s │\n" "Backend" "${BACKEND_PORT}" "Running" "${backend_pid:-N/A}"
    else
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │ %-31s │\n" "Backend" "${BACKEND_PORT}" "Stopped" "N/A"
    fi
    
    # Bridge status
    if is_port_in_use $BRIDGE_PORT; then
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │ %-31s │\n" "tRPC Bridge" "${BRIDGE_PORT}" "Running" "${bridge_pid:-N/A}"
    else
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │ %-31s │\n" "tRPC Bridge" "${BRIDGE_PORT}" "Stopped" "N/A"
    fi
    
    # Frontend status
    if is_port_in_use $FRONTEND_PORT; then
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │ %-31s │\n" "Frontend" "${FRONTEND_PORT}" "Running" "${frontend_pid:-N/A}"
    else
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │ %-31s │\n" "Frontend" "${FRONTEND_PORT}" "Stopped" "N/A"
    fi
    
    echo "└─────────────────┴───────────┴─────────┴─────────────────────────────────┘"
    echo -e "${NC}"
    
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  Frontend:  ${GREEN}http://localhost:${FRONTEND_PORT}${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:${BACKEND_PORT}${NC}"
    echo -e "  Bridge:    ${GREEN}http://localhost:${BRIDGE_PORT}${NC}"
    echo -e "  API Docs:  ${GREEN}http://localhost:${BACKEND_PORT}/api/v6/status${NC}"
    echo ""
    echo -e "${BLUE}Log Files:${NC}"
    echo -e "  Backend:   ${LOG_DIR}/backend.log"
    echo -e "  Frontend:  ${LOG_DIR}/frontend.log"
    echo -e "  Bridge:    ${LOG_DIR}/bridge.log"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo -e "  Stop services:    ${YELLOW}./scripts/stop.sh${NC}"
    echo -e "  Health check:     ${YELLOW}./scripts/health-check.sh${NC}"
    echo -e "  View logs:        ${YELLOW}tail -f ${LOG_DIR}/backend.log${NC}"
}

# Main function
main() {
    print_logo
    create_directories
    check_existing_services
    
    start_backend
    start_bridge
    start_frontend
    
    show_dashboard
}

# Run main function
main "$@"
