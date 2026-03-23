#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM Layer 6: MuninnDB Installation Script
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║           KISWARM LAYER 6: MUNINNDB INSTALLATION                              ║"
echo "║                    'Eternal Memory for the Swarm'                             ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"

# Check OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE=linux;;
    Darwin*)    OS_TYPE=macos;;
    CYGWIN*)    OS_TYPE=windows;;
    MINGW*)     OS_TYPE=windows;;
    *)          OS_TYPE=unknown;;
esac

echo "[INFO] Detected OS: $OS_TYPE"

# Install MuninnDB
echo ""
echo "[STEP 1] Installing MuninnDB..."

if [ "$OS_TYPE" = "macos" ] || [ "$OS_TYPE" = "linux" ]; then
    curl -sSL https://muninndb.com/install.sh | sh
elif [ "$OS_TYPE" = "windows" ]; then
    echo "[INFO] On Windows, run this in PowerShell:"
    echo "irm https://muninndb.com/install.ps1 | iex"
    exit 0
else
    echo "[ERROR] Unsupported OS: $OS_TYPE"
    exit 1
fi

# Install Python SDK
echo ""
echo "[STEP 2] Installing Python SDK..."
pip install muninn-python 2>/dev/null || pip3 install muninn-python

# Create KISWARM vaults
echo ""
echo "[STEP 3] Starting MuninnDB and creating vaults..."
muninn start &

# Wait for startup
sleep 3

# Create vaults via REST API
VAULTS=("kiswarm" "hexstrike" "mutations" "upgrades" "swarm" "audit" "knowledge")

for vault in "${VAULTS[@]}"; do
    echo "[INFO] Creating vault: $vault"
    curl -sX POST "http://127.0.0.1:8475/api/vaults" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$vault\"}" 2>/dev/null || echo "  (Vault may already exist)"
done

# Configure environment
echo ""
echo "[STEP 4] Configuring environment..."

cat >> ~/.bashrc << 'EOF'

# KISWARM Layer 6: MuninnDB
export MUNINN_URL=http://localhost:8475
export MUNINN_VAULT=kiswarm
EOF

echo "[OK] Added MuninnDB config to ~/.bashrc"

# Test connection
echo ""
echo "[STEP 5] Testing connection..."

python3 -c "
import asyncio
import sys
sys.path.insert(0, '/home/z/my-project/KISWARM6.0/mesh/muninn')
from kiswarm_muninn import KISWARMMuninnBridge

async def test():
    bridge = KISWARMMuninnBridge()
    await bridge.connect()
    print('[OK] Connected to MuninnDB')
    print(f'[INFO] Stats: {bridge.stats()}')

asyncio.run(test())
" 2>/dev/null || echo "[WARN] Could not test Python bridge"

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    MUNINNDB INSTALLATION COMPLETE                             ║"
echo "╠═══════════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                               ║"
echo "║  Ports:                                                                       ║"
echo "║    • 8474 - MBP (Binary, <10ms)                                              ║"
echo "║    • 8475 - REST API                                                          ║"
echo "║    • 8476 - Web UI (root / password)                                         ║"
echo "║    • 8750 - MCP (AI Agents)                                                   ║"
echo "║                                                                               ║"
echo "║  Vaults Created:                                                              ║"
echo "║    • kiswarm   - General swarm memory                                         ║"
echo "║    • hexstrike - Security & attack patterns                                   ║"
echo "║    • mutations - Mutation governance                                          ║"
echo "║    • upgrades  - Self-upgrade memory                                          ║"
echo "║    • swarm     - Node coordination                                            ║"
echo "║    • audit     - Audit trail                                                  ║"
echo "║    • knowledge - RAG knowledge                                                ║"
echo "║                                                                               ║"
echo "║  Web UI: http://127.0.0.1:8476                                               ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
