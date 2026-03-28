#!/bin/bash
#
# 🜂 HERMES FIELD TESTS
# =====================
# Comprehensive test suite for Hermes Agent
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🜂 HERMES FIELD TESTS${NC}"
echo -e "${CYAN}=================================${NC}"
echo ""

PASSED=0
FAILED=0

test_case() {
    local name="$1"
    local result="$2"
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $name"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} $name"
        FAILED=$((FAILED + 1))
    fi
}

# Test 1: Ollama Service
echo -e "${YELLOW}Testing Ollama Service...${NC}"
if curl -s http://localhost:11434/ > /dev/null 2>&1; then
    test_case "Ollama service running" "PASS"
else
    test_case "Ollama service running" "FAIL"
fi

# Test 2: Qwen Model
echo -e "${YELLOW}Testing Qwen Model...${NC}"
if ollama list 2>/dev/null | grep -q "qwen"; then
    test_case "Qwen model available" "PASS"
else
    test_case "Qwen model available" "FAIL"
fi

# Test 3: Model Generation
echo -e "${YELLOW}Testing Model Generation...${NC}"
TEST_RESPONSE=$(curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5:14b","prompt":"Say OK","stream":false}' 2>/dev/null | head -1)
if [ -n "$TEST_RESPONSE" ]; then
    test_case "Model generation works" "PASS"
else
    test_case "Model generation works" "FAIL"
fi

# Test 4: KISWARM Mesh Connection
echo -e "${YELLOW}Testing KISWARM Mesh...${NC}"
if curl -s --connect-timeout 5 http://95.111.212.112:5000/health > /dev/null 2>&1; then
    test_case "KISWARM mesh reachable" "PASS"
else
    test_case "KISWARM mesh reachable" "FAIL"
fi

# Test 5: Hermes Configuration
echo -e "${YELLOW}Testing Hermes Configuration...${NC}"
if [ -f "/opt/hermes/config.yaml" ]; then
    test_case "Hermes config exists" "PASS"
else
    test_case "Hermes config exists" "FAIL"
fi

# Test 6: Memory Directories
echo -e "${YELLOW}Testing Memory System...${NC}"
if [ -d "/opt/hermes/memory" ]; then
    test_case "Memory directory exists" "PASS"
else
    test_case "Memory directory exists" "FAIL"
fi

# Test 7: Skills Directory
echo -e "${YELLOW}Testing Skills System...${NC}"
if [ -d "/opt/hermes/skills" ]; then
    test_case "Skills directory exists" "PASS"
else
    test_case "Skills directory exists" "FAIL"
fi

# Test 8: Logs Directory
echo -e "${YELLOW}Testing Logging...${NC}"
if [ -d "/opt/hermes/logs" ]; then
    test_case "Logs directory exists" "PASS"
else
    test_case "Logs directory exists" "FAIL"
fi

# Test 9: System Resources
echo -e "${YELLOW}Testing System Resources...${NC}"
MEM_AVAILABLE=$(free -m | awk '/^Mem:/{print $7}')
if [ "$MEM_AVAILABLE" -gt 2048 ]; then
    test_case "Sufficient memory (>${MEM_AVAILABLE}MB)" "PASS"
else
    test_case "Low memory warning (${MEM_AVAILABLE}MB)" "FAIL"
fi

# Test 10: CPU Cores
echo -e "${YELLOW}Testing CPU Resources...${NC}"
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -ge 4 ]; then
    test_case "CPU cores adequate (${CPU_CORES})" "PASS"
else
    test_case "CPU cores low (${CPU_CORES})" "FAIL"
fi

# Summary
echo ""
echo -e "${CYAN}=================================${NC}"
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo -e "${CYAN}=================================${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🜂 ALL TESTS PASSED!${NC}"
    echo ""
    echo "Hermes is ready for autonomous operation."
    echo ""
    echo "Start with: systemctl start hermes"
    echo "Check logs: journalctl -u hermes -f"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Review the output above.${NC}"
    exit 1
fi
