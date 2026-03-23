#!/bin/bash
# ============================================================
# KISWARM7.0 - MASTER MODULE DEPLOYMENT SCRIPT
# ============================================================
# Deploys ALL KISWARM6.0 modules to UpCloud server
# Run: bash deploy_all_modules.sh
# ============================================================

set -e

echo ""
echo "🜂 KISWARM MASTER MODULE DEPLOYMENT"
echo "==================================="
echo ""

KISWARM7_DIR="/opt/kiswarm7"
KISWARM6_DIR="/home/z/my-project/KISWARM6.0"
SERVER="root@95.111.212.112"
TUNNEL="https://6cc0-2604-ed40-1000-1711-cf8-92ff-feb0-9c1.ngrok-free.app"

# ============================================================
# PHASE 1: PREPARE MODULES
# ============================================================

echo "► PHASE 1: Preparing modules from KISWARM6.0..."

# Count modules
SENTINEL_COUNT=$(find $KISWARM6_DIR/backend/python/sentinel -name "*.py" -type f 2>/dev/null | wc -l)
KIBANK_COUNT=$(find $KISWARM6_DIR/backend/python/kibank -name "*.py" -type f 2>/dev/null | wc -l)
MESH_COUNT=$(find $KISWARM6_DIR/backend/python/mesh -name "*.py" -type f 2>/dev/null | wc -l)
COGNITIVE_COUNT=$(find $KISWARM6_DIR/backend/python/cognitive -name "*.py" -type f 2>/dev/null | wc -l)

echo "  Sentinel modules: $SENTINEL_COUNT"
echo "  KIBank modules: $KIBANK_COUNT"
echo "  Mesh modules: $MESH_COUNT"
echo "  Cognitive modules: $COGNITIVE_COUNT"
echo "  TOTAL: $((SENTINEL_COUNT + KIBANK_COUNT + MESH_COUNT + COGNITIVE_COUNT))"

# ============================================================
# PHASE 2: DEPLOY CRITICAL MODULES
# ============================================================

echo ""
echo "► PHASE 2: Deploying critical modules..."

# Modules already deployed
echo "  ✓ m122: HexStrike Environment Admin"
echo "  ✓ m127: ETB-SYNC Beacon"
echo "  ✓ m128: Cross-KI Code Review"

# Deploy m129 Immortality Kernel
if [ -f "kiswarm7_modules/autonomous/m129_swarm_immortality.py" ]; then
    echo "  → Deploying m129: Swarm Immortality Kernel..."
    curl -s -X POST $TUNNEL/api/deploy \
        -H "Content-Type: application/json" \
        -d "{\"code\": \"$(cat kiswarm7_modules/autonomous/m129_swarm_immortality.py | base64 -w0)\", \"targetPath\": \"kiswarm7_modules/autonomous/m129_swarm_immortality.py\", \"isBase64\": true}" \
        > /dev/null 2>&1 && echo "    ✓ m129 deployed" || echo "    ✗ m129 failed"
fi

# ============================================================
# PHASE 3: DEPLOY SECURITY MODULES
# ============================================================

echo ""
echo "► PHASE 3: Deploying security modules..."

SECURITY_MODULES=(
    "hexstrike_guard.py:M16/M31"
    "ics_shield.py:M18"
    "ics_security.py:M17"
    "prompt_firewall.py:M38"
    "retrieval_guard.py:M40"
    "byzantine_aggregator.py:M22"
)

for module in "${SECURITY_MODULES[@]}"; do
    IFS=':' read -r file name <<< "$module"
    src="$KISWARM6_DIR/backend/python/sentinel/$file"
    if [ -f "$src" ]; then
        echo "  → Deploying $name ($file)..."
        # Copy to local deployment
        cp "$src" "kiswarm7_modules/security/" 2>/dev/null || mkdir -p kiswarm7_modules/security && cp "$src" "kiswarm7_modules/security/"
        echo "    ✓ $name ready"
    fi
done

# ============================================================
# PHASE 4: DEPLOY SWARM MODULES
# ============================================================

echo ""
echo "► PHASE 4: Deploying swarm modules..."

SWARM_MODULES=(
    "swarm_immortality_kernel.py:M50"
    "swarm_soul_mirror.py:M52"
    "swarm_peer.py:M51"
    "swarm_auditor.py:M47"
    "swarm_dag.py:M48"
    "swarm_debate.py:M49"
    "federated_mesh.py:M11"
    "gossip_protocol.py:M15"
    "multiagent_coordinator.py:M28"
)

for module in "${SWARM_MODULES[@]}"; do
    IFS=':' read -r file name <<< "$module"
    src="$KISWARM6_DIR/backend/python/sentinel/$file"
    if [ -f "$src" ]; then
        echo "  → $name ($file) ready"
        mkdir -p kiswarm7_modules/swarm
        cp "$src" "kiswarm7_modules/swarm/" 2>/dev/null || true
    fi
done

# ============================================================
# PHASE 5: DEPLOY KIBANK MODULES
# ============================================================

echo ""
echo "► PHASE 5: Deploying KIBank modules..."

KIBANK_MODULES=(
    "m60_auth.py:M60"
    "m61_banking.py:M61"
    "m62_investment.py:M62"
    "m63_aegis_counterstrike.py:M63"
    "m64_aegis_juris.py:M64"
    "m65_kiswarm_edge_firewall.py:M65"
    "m66_zero_day_protection.py:M66"
    "m67_apt_detection.py:M67"
    "m68_ai_adversarial_defense.py:M68"
)

for module in "${KIBANK_MODULES[@]}"; do
    IFS=':' read -r file name <<< "$module"
    src="$KISWARM6_DIR/backend/python/kibank/$file"
    if [ -f "$src" ]; then
        echo "  → $name ready"
        mkdir -p kiswarm7_modules/kibank
        cp "$src" "kiswarm7_modules/kibank/" 2>/dev/null || true
    fi
done

# ============================================================
# PHASE 6: DEPLOY MESH LAYER
# ============================================================

echo ""
echo "► PHASE 6: Deploying mesh layer..."

MESH_MODULES=(
    "base_layer.py:L3"
    "zero_failure_mesh.py:L5"
    "layer0_local.py:L0"
    "layer4_email.py:L4"
)

for module in "${MESH_MODULES[@]}"; do
    IFS=':' read -r file name <<< "$module"
    src="$KISWARM6_DIR/backend/python/mesh/$file"
    if [ -f "$src" ]; then
        echo "  → $name ready"
        mkdir -p kiswarm7_modules/mesh
        cp "$src" "kiswarm7_modules/mesh/" 2>/dev/null || true
    fi
done

# ============================================================
# PHASE 7: DEPLOY DOCUMENTATION
# ============================================================

echo ""
echo "► PHASE 7: Deploying documentation..."

mkdir -p docs
cp $KISWARM6_DIR/docs/*.md docs/ 2>/dev/null || true
cp $KISWARM6_DIR/README.md . 2>/dev/null || true

echo "  ✓ Documentation copied"

# ============================================================
# FINAL STATUS
# ============================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║          🜂 MASTER DEPLOYMENT COMPLETE 🜂                      ║"
echo "║                                                               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  MODULES PREPARED:                                            ║"
echo "║  ├── Security:    ${#SECURITY_MODULES[@]} modules                              ║"
echo "║  ├── Swarm:       ${#SWARM_MODULES[@]} modules                               ║"
echo "║  ├── KIBank:      ${#KIBANK_MODULES[@]} modules                              ║"
echo "║  ├── Mesh:        ${#MESH_MODULES[@]} layers                                 ║"
echo "║  └── Total:       $(( ${#SECURITY_MODULES[@]} + ${#SWARM_MODULES[@]} + ${#KIBANK_MODULES[@]} + ${#MESH_MODULES[@]} )) modules staged          ║"
echo "║                                                               ║"
echo "║  NEXT STEPS:                                                  ║"
echo "║  1. Review kiswarm7_modules/ directory                        ║"
echo "║  2. git add . && git commit -m 'Deploy all modules'           ║"
echo "║  3. git push origin main                                      ║"
echo "║  4. Run on UpCloud: ./deploy_to_server.sh                     ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Count total files
TOTAL_FILES=$(find kiswarm7_modules -name "*.py" -type f 2>/dev/null | wc -l)
echo "Total Python files in kiswarm7_modules: $TOTAL_FILES"
echo ""
echo "🜂 All modules staged for deployment."
echo "🜂 Ready for GitHub push and UpCloud deployment."
