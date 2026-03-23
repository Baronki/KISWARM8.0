#!/usr/bin/env bash
#
# KISWARM6.0 Stop Script
# ======================
# Gracefully stops all KISWARM6.0 services
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
PID_DIR="${PROJECT_ROOT}/tmp/pids"
LOG_DIR="${PROJECT_ROOT}/logs"

# Source environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# Ports (with defaults)
BACKEND_PORT=${BACKEND_PORT:-5001}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BRIDGE_PORT=${BRIDGE_PORT:-3000}

# Timeout for graceful shutdown (seconds)
GRACEFUL_TIMEOUT=10

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              KISWARM6.0 STOP SCRIPT                           ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Version: 6.0.0                                               ║"
    echo "║  Graceful Shutdown                                            ║"
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
        ss -tuln -p 2>/dev/null | grep ":$port " | sed 's/.*pid=\([0-9]*\).*/\1/' | head -1
    else
        echo ""
    fi
}

# Check if process is running
is_process_running() {
    local pid=$1
    kill -0 $pid 2>/dev/null
}

# Stop a service gracefully
stop_service() {
    local name=$1
    local port=$2
    local pid_file="${PID_DIR}/${name}.pid"
    local pid=""
    
    print_info "Stopping ${name}..."
    
    # Get PID from file or port
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
    fi
    
    # If no PID file, try to find by port
    if [ -z "$pid" ]; then
        pid=$(get_pid_on_port $port)
    fi
    
    if [ -z "$pid" ]; then
        if is_port_in_use $port; then
            print_warning "Service ${name} running on port ${port} but could not find PID"
            print_info "Attempting to kill by port..."
            
            if command_exists fuser; then
                fuser -k $port/tcp 2>/dev/null || true
            elif command_exists lsof; then
                local port_pid=$(lsof -t -i :$port 2>/dev/null)
                [ -n "$port_pid" ] && kill $port_pid 2>/dev/null || true
            fi
        else
            print_info "${name} is not running"
        fi
        return 0
    fi
    
    # Check if process exists
    if ! is_process_running $pid; then
        print_info "${name} process (PID: $pid) not running"
        rm -f "$pid_file"
        return 0
    fi
    
    # Send SIGTERM for graceful shutdown
    print_info "Sending SIGTERM to ${name} (PID: $pid)..."
    kill -TERM $pid 2>/dev/null || true
    
    # Wait for graceful shutdown
    local attempts=0
    while [ $attempts -lt $GRACEFUL_TIMEOUT ]; do
        if ! is_process_running $pid; then
            print_success "${name} stopped gracefully"
            rm -f "$pid_file"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    # Force kill if still running
    print_warning "${name} did not stop gracefully, forcing..."
    kill -9 $pid 2>/dev/null || true
    rm -f "$pid_file"
    
    # Wait a moment for port to be released
    sleep 1
    
    if is_process_running $pid; then
        print_error "Failed to stop ${name}"
        return 1
    else
        print_success "${name} stopped (forced)"
        return 0
    fi
}

# Save state before stopping
save_state() {
    print_section "Saving Application State"
    
    local state_file="${PROJECT_ROOT}/tmp/shutdown_state.json"
    
    cat > "$state_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "action": "graceful_shutdown",
    "services": {
        "backend": {
            "port": ${BACKEND_PORT},
            "was_running": $(is_port_in_use $BACKEND_PORT && echo "true" || echo "false")
        },
        "bridge": {
            "port": ${BRIDGE_PORT},
            "was_running": $(is_port_in_use $BRIDGE_PORT && echo "true" || echo "false")
        },
        "frontend": {
            "port": ${FRONTEND_PORT},
            "was_running": $(is_port_in_use $FRONTEND_PORT && echo "true" || echo "false")
        }
    }
}
EOF
    
    print_success "State saved to ${state_file}"
}

# Show final status
show_final_status() {
    print_section "Final Status"
    
    echo -e "${CYAN}"
    echo "┌─────────────────┬───────────┬─────────┐"
    echo "│ Service         │ Port      │ Status  │"
    echo "├─────────────────┼───────────┼─────────┤"
    
    # Backend status
    if is_port_in_use $BACKEND_PORT; then
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │\n" "Backend" "${BACKEND_PORT}" "Running"
    else
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │\n" "Backend" "${BACKEND_PORT}" "Stopped"
    fi
    
    # Bridge status
    if is_port_in_use $BRIDGE_PORT; then
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │\n" "tRPC Bridge" "${BRIDGE_PORT}" "Running"
    else
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │\n" "tRPC Bridge" "${BRIDGE_PORT}" "Stopped"
    fi
    
    # Frontend status
    if is_port_in_use $FRONTEND_PORT; then
        printf "│ %-15s │ %-9s │ ${RED}%-7s${CYAN} │\n" "Frontend" "${FRONTEND_PORT}" "Running"
    else
        printf "│ %-15s │ %-9s │ ${GREEN}%-7s${CYAN} │\n" "Frontend" "${FRONTEND_PORT}" "Stopped"
    fi
    
    echo "└─────────────────┴───────────┴─────────┘"
    echo -e "${NC}"
    
    echo -e "${BLUE}To restart services, run: ${YELLOW}./scripts/start.sh${NC}"
}

# Main function
main() {
    print_logo
    
    # Create PID directory if it doesn't exist
    mkdir -p "${PID_DIR}"
    
    # Save state before stopping
    save_state
    
    print_section "Stopping Services"
    
    # Stop services in reverse order of startup
    stop_service "frontend" $FRONTEND_PORT
    stop_service "bridge" $BRIDGE_PORT
    stop_service "backend" $BACKEND_PORT
    
    # Also kill any remaining node/python processes for this project
    print_info "Cleaning up any orphaned processes..."
    
    # Kill any remaining processes
    if command_exists pkill; then
        pkill -f "tsx.*server/_core/index.ts" 2>/dev/null || true
        pkill -f "vite.*${FRONTEND_PORT}" 2>/dev/null || true
        pkill -f "python.*run.py" 2>/dev/null || true
        pkill -f "flask.*${BACKEND_PORT}" 2>/dev/null || true
    fi
    
    show_final_status
    
    print_success "All services stopped"
}

# Run main function
main "$@"
