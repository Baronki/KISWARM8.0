#!/usr/bin/env bash
#
# KISWARM6.0 Health Check Script
# ===============================
# Checks the health of all KISWARM6.0 services:
# - Backend API health
# - Frontend health
# - Database connection
# - Qdrant vector DB (if configured)
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

# Source environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    export $(cat "${PROJECT_ROOT}/.env" | grep -v '^#' | xargs)
fi

# Ports (with defaults)
BACKEND_PORT=${BACKEND_PORT:-5001}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BRIDGE_PORT=${BRIDGE_PORT:-3000}

# URLs
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRENDEND_URL="http://localhost:${FRONTEND_PORT}"
BRIDGE_URL="http://localhost:${BRIDGE_PORT}"

# Database settings
DATABASE_URL=${DATABASE_URL:-""}
QDRANT_URL=${QDRANT_URL:-"http://localhost:6333"}

# Timeout for health checks (seconds)
HEALTH_TIMEOUT=5

# Results tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Logo
print_logo() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           KISWARM6.0 HEALTH CHECK                             ║"
    echo "╠══════════════════════════════════════━━━━━━━━━━━━━━━━━━━━━━━━━╣"
    echo "║  Version: 6.0.0                                               ║"
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
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

# Print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
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

# HTTP health check
http_health_check() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    print_info "Checking ${name}..."
    
    if command_exists curl; then
        local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${HEALTH_TIMEOUT} "${url}" 2>/dev/null)
        
        if [ "$response" = "$expected_status" ]; then
            print_success "${name} is healthy (HTTP ${response})"
            return 0
        else
            print_error "${name} returned HTTP ${response:-"no response"}"
            return 1
        fi
    elif command_exists wget; then
        local response=$(wget -q -O /dev/null --timeout=${HEALTH_TIMEOUT} --server-response "${url}" 2>&1 | grep "HTTP/" | tail -1 | awk '{print $2}')
        
        if [ "$response" = "$expected_status" ]; then
            print_success "${name} is healthy (HTTP ${response})"
            return 0
        else
            print_error "${name} returned HTTP ${response:-"no response"}"
            return 1
        fi
    else
        print_warning "Neither curl nor wget available for HTTP health check"
        return 1
    fi
}

# Check if port is listening
check_port_listening() {
    local name=$1
    local port=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    print_info "Checking if ${name} is listening on port ${port}..."
    
    if command_exists lsof; then
        if lsof -i :${port} >/dev/null 2>&1; then
            print_success "${name} is listening on port ${port}"
            return 0
        fi
    elif command_exists ss; then
        if ss -tuln | grep -q ":${port} "; then
            print_success "${name} is listening on port ${port}"
            return 0
        fi
    elif command_exists netstat; then
        if netstat -tuln | grep -q ":${port} "; then
            print_success "${name} is listening on port ${port}"
            return 0
        fi
    fi
    
    print_error "${name} is not listening on port ${port}"
    return 1
}

# Check backend health
check_backend_health() {
    print_section "Backend Health Checks"
    
    # Check port
    check_port_listening "Backend" $BACKEND_PORT
    
    # Check API status endpoint
    http_health_check "Backend API" "${BACKEND_URL}/api/v6/status"
    
    # Check detailed API status
    print_info "Fetching detailed backend status..."
    
    if command_exists curl; then
        local status=$(curl -s --max-time ${HEALTH_TIMEOUT} "${BACKEND_URL}/api/v6/status" 2>/dev/null)
        
        if [ -n "$status" ]; then
            echo -e "${CYAN}${status}${NC}" | python3 -m json.tool 2>/dev/null || echo -e "${CYAN}${status}${NC}"
        fi
    fi
}

# Check frontend health
check_frontend_health() {
    print_section "Frontend Health Checks"
    
    # Check port
    check_port_listening "Frontend" $FRONTEND_PORT
    
    # Check frontend root
    http_health_check "Frontend" "${FRENDEND_URL}/"
}

# Check tRPC bridge health
check_bridge_health() {
    print_section "tRPC Bridge Health Checks"
    
    # Check port
    check_port_listening "tRPC Bridge" $BRIDGE_PORT
    
    # Check bridge health (if it has an endpoint)
    http_health_check "tRPC Bridge" "${BRIDGE_URL}/health"
}

# Check database connection
check_database_health() {
    print_section "Database Health Checks"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -z "${DATABASE_URL}" ]; then
        print_warning "DATABASE_URL not configured"
        return 0
    fi
    
    print_info "Checking MySQL database connection..."
    
    # Extract database info from DATABASE_URL
    # Format: mysql://user:password@host:port/database
    
    if [[ "${DATABASE_URL}" =~ mysql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        local db_user="${BASH_REMATCH[1]}"
        local db_pass="${BASH_REMATCH[2]}"
        local db_host="${BASH_REMATCH[3]}"
        local db_port="${BASH_REMATCH[4]}"
        local db_name="${BASH_REMATCH[5]}"
        
        if command_exists mysql; then
            if mysql -h "$db_host" -P "$db_port" -u "$db_user" -p"$db_pass" -e "SELECT 1;" >/dev/null 2>&1; then
                print_success "MySQL database connection successful"
                
                # Get some database stats
                local db_size=$(mysql -h "$db_host" -P "$db_port" -u "$db_user" -p"$db_pass" -N -e "
                    SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 
                    FROM information_schema.tables 
                    WHERE table_schema = '$db_name';" 2>/dev/null)
                
                print_info "Database size: ${db_size:-"unknown"} MB"
            else
                print_error "MySQL database connection failed"
            fi
        else
            print_warning "MySQL client not available for connection test"
        fi
    else
        print_warning "Could not parse DATABASE_URL"
    fi
}

# Check Qdrant vector database
check_qdrant_health() {
    print_section "Qdrant Vector DB Health Checks"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -z "${QDRANT_URL}" ]; then
        print_info "Qdrant URL not configured, skipping"
        return 0
    fi
    
    print_info "Checking Qdrant connection..."
    
    # Check Qdrant health endpoint
    if command_exists curl; then
        local response=$(curl -s --max-time ${HEALTH_TIMEOUT} "${QDRANT_URL}/health" 2>/dev/null)
        
        if [ -n "$response" ]; then
            print_success "Qdrant is healthy"
            
            # Get collections info
            local collections=$(curl -s --max-time ${HEALTH_TIMEOUT} "${QDRANT_URL}/collections" 2>/dev/null)
            if [ -n "$collections" ]; then
                print_info "Collections: ${collections}"
            fi
        else
            print_warning "Qdrant health check failed (may not be running)"
        fi
    fi
}

# Check system resources
check_system_resources() {
    print_section "System Resources"
    
    # CPU usage
    if command_exists top; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
        print_info "CPU Usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    if [ -f /proc/meminfo ]; then
        local total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local free_mem=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        local used_mem=$((total_mem - free_mem))
        local mem_percent=$((used_mem * 100 / total_mem))
        print_info "Memory Usage: ${mem_percent}% (${used_mem}/${total_mem} KB)"
    fi
    
    # Disk usage
    if command_exists df; then
        local disk_usage=$(df -h "${PROJECT_ROOT}" | tail -1 | awk '{print $5}' | tr -d '%')
        local disk_avail=$(df -h "${PROJECT_ROOT}" | tail -1 | awk '{print $4}')
        print_info "Disk Usage: ${disk_usage}% (${disk_avail} available)"
        
        if [ "$disk_usage" -gt 90 ]; then
            print_warning "Disk usage is above 90%"
        fi
    fi
    
    # Check if running in Docker
    if [ -f /.dockerenv ]; then
        print_info "Running inside Docker container"
    fi
}

# Check process health
check_process_health() {
    print_section "Process Health"
    
    local pid_dir="${PROJECT_ROOT}/tmp/pids"
    
    # Check backend process
    if [ -f "${pid_dir}/backend.pid" ]; then
        local backend_pid=$(cat "${pid_dir}/backend.pid")
        if kill -0 $backend_pid 2>/dev/null; then
            print_success "Backend process running (PID: ${backend_pid})"
        else
            print_error "Backend process not running (stale PID file)"
        fi
    else
        print_info "No backend PID file found"
    fi
    
    # Check frontend process
    if [ -f "${pid_dir}/frontend.pid" ]; then
        local frontend_pid=$(cat "${pid_dir}/frontend.pid")
        if kill -0 $frontend_pid 2>/dev/null; then
            print_success "Frontend process running (PID: ${frontend_pid})"
        else
            print_error "Frontend process not running (stale PID file)"
        fi
    else
        print_info "No frontend PID file found"
    fi
    
    # Check bridge process
    if [ -f "${pid_dir}/bridge.pid" ]; then
        local bridge_pid=$(cat "${pid_dir}/bridge.pid")
        if kill -0 $bridge_pid 2>/dev/null; then
            print_success "Bridge process running (PID: ${bridge_pid})"
        else
            print_error "Bridge process not running (stale PID file)"
        fi
    else
        print_info "No bridge PID file found"
    fi
}

# Generate report
generate_report() {
    print_section "Health Check Report"
    
    local timestamp=$(date -Iseconds)
    
    echo -e "${CYAN}"
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│                    HEALTH CHECK SUMMARY                     │"
    echo "├─────────────────────────────────────────────────────────────┤"
    printf "│  %-25s: %-30s │\n" "Timestamp" "$timestamp"
    printf "│  %-25s: %-30s │\n" "Total Checks" "$TOTAL_CHECKS"
    printf "│  %-25s: ${GREEN}%-30s${CYAN} │\n" "Passed" "$PASSED_CHECKS"
    printf "│  %-25s: ${RED}%-30s${CYAN} │\n" "Failed" "$FAILED_CHECKS"
    echo "├─────────────────────────────────────────────────────────────┤"
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo "│                ${GREEN}ALL SYSTEMS OPERATIONAL${CYAN}                 │"
    else
        echo "│                ${RED}SOME CHECKS FAILED${CYAN}                      │"
    fi
    
    echo "└─────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
    
    # Save report to file
    local report_file="${PROJECT_ROOT}/logs/health-check-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "total_checks": $TOTAL_CHECKS,
    "passed": $PASSED_CHECKS,
    "failed": $FAILED_CHECKS,
    "status": "$([ $FAILED_CHECKS -eq 0 ] && echo "healthy" || echo "unhealthy")"
}
EOF
    
    print_info "Report saved to: ${report_file}"
    
    # Return exit code based on health
    if [ $FAILED_CHECKS -gt 0 ]; then
        return 1
    fi
    return 0
}

# Main function
main() {
    print_logo
    
    check_backend_health
    check_frontend_health
    check_bridge_health
    check_database_health
    check_qdrant_health
    check_system_resources
    check_process_health
    
    generate_report
}

# Run main function
main "$@"
