#!/bin/bash
# ============================================================================
# KISWARM v5.1 — AUTOMATED MODEL TRAINING SCRIPT
# ============================================================================
# Purpose: Create all role-specific KISWARM models from pretrained base models
# Author:  Baron Marco Paolo Ialongo
# Version: 5.1
#
# Usage:   ./train_all_models.sh [--full|--primary|--fast|--test]
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAINING_DIR="$(dirname "$SCRIPT_DIR")"
MODELFILES_DIR="$TRAINING_DIR/modelfiles"
CONTEXT_DIR="$TRAINING_DIR/context"
PROMPTS_DIR="$TRAINING_DIR/prompts"

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    KISWARM v5.1 MODEL TRAINING SYSTEM                        ║"
    echo "║                         PLANETARY MACHINE EDITION                            ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║  Roles: ORCHESTRATOR | SECURITY | CIEC | TCS | KNOWLEDGE | INSTALLER        ║"
    echo "║  Modules: 57 | Endpoints: 360+ | Tests: 1500+                                ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}[CHECK] Verifying prerequisites...${NC}"
    
    # Check Ollama
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}[ERROR] Ollama not found. Please install Ollama first.${NC}"
        echo "       curl -fsSL https://ollama.com/install.sh | sh"
        exit 1
    fi
    echo -e "${GREEN}[OK] Ollama installed${NC}"
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARN] Ollama not running. Starting...${NC}"
        ollama serve &
        sleep 5
    fi
    echo -e "${GREEN}[OK] Ollama running on port 11434${NC}"
    
    # Check modelfiles directory
    if [ ! -d "$MODELFILES_DIR" ]; then
        echo -e "${RED}[ERROR] Modelfiles directory not found: $MODELFILES_DIR${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Modelfiles directory found${NC}"
}

# List available base models
list_base_models() {
    echo -e "${BLUE}[INFO] Available pretrained models:${NC}"
    ollama list | head -20
    echo -e "${YELLOW}... and more${NC}"
}

# Model definitions
declare -A PRIMARY_MODELS=(
    ["kiswarm-orchestrator"]="huihui_ai/orchestrator-abliterated:8b-swarm-aware-tools"
    ["kiswarm-security"]="huihui_ai/glm-4.7-flash-abliterated:latest-swarm-aware-tools"
    ["kiswarm-ciec"]="dengcao/ERNIE-4.5-21B-A3B-PT:latest-swarm-aware-tools"
    ["kiswarm-tcs"]="qwen2.5-coder:14b-swarm-aware-tools"
    ["kiswarm-knowledge"]="qwen2.5:14b-swarm-aware-tools"
    ["kiswarm-installer"]="llama3-groq-tool-use:latest-swarm-aware-tools"
)

declare -A BACKUP_MODELS=(
    ["kiswarm-orchestrator-backup"]="gpt_oss_20b_swarm_aware_tools:latest"
    ["kiswarm-security-backup"]="dolphin3_8b_swarm_aware_tools:latest"
    ["kiswarm-ciec-backup"]="qwen2_5_14b_swarm_aware_tools:latest"
    ["kiswarm-tcs-backup"]="qwen2_5_coder_7b_swarm_aware_tools:latest"
    ["kiswarm-knowledge-backup"]="gemma2_latest_swarm_aware_tools:latest"
    ["kiswarm-installer-backup"]="llama3.1:8b"
)

declare -A FAST_MODELS=(
    ["kiswarm-orchestrator-fast"]="phi3_mini_swarm_aware_tools:latest"
    ["kiswarm-security-fast"]="huihui_ai_lfm2_5_abliterated_latest_swarm_aware_tools:latest"
    ["kiswarm-ciec-fast"]="marco_o1_7b_swarm_aware_tools:latest"
    ["kiswarm-tcs-fast"]="sam860_LFM2_2_6b_exp_Q8_0_swarm_aware_tools:latest"
    ["kiswarm-knowledge-fast"]="phi3_mini_swarm_aware_tools:latest"
    ["kiswarm-installer-fast"]="dengcao_ERNIE_4_5_0_3B_PT_latest_swarm_aware_tools:latest"
)

declare -A SPECIALIZED_MODELS=(
    ["kiswarm-thinker"]="huihui_ai/mirothinker1-abliterated:8b-swarm-aware-tools"
    ["kiswarm-debugger"]="huihui_ai/qwen3-abliterated:8b-swarm-aware-tools"
    ["kiswarm-vision"]="qwen3-vl:8b"
    ["kiswarm-validator"]="gemma2_latest_swarm_aware_tools:latest"
    ["kiswarm-reasoner"]="deepseek-r1:1.5b-swarm-aware-tools"
    ["kiswarm-general"]="llama3.1:8b"
)

declare -A EMBEDDING_MODELS=(
    ["kiswarm-embedding"]="nomic-embed-text:latest-swarm-aware"
)

# Create a single model
create_model() {
    local model_name=$1
    local modelfile=$2
    
    echo -e "${CYAN}[CREATE] Creating model: $model_name${NC}"
    
    if [ -f "$modelfile" ]; then
        ollama create "$model_name" -f "$modelfile"
        echo -e "${GREEN}[OK] Model created: $model_name${NC}"
    else
        echo -e "${YELLOW}[WARN] Modelfile not found: $modelfile${NC}"
        echo -e "${YELLOW}[INFO] Using base model with default config${NC}"
        # Create minimal modelfile inline
        local base_model=$(echo $model_name | sed 's/kiswarm-//' | sed 's/-fast//' | sed 's/-backup//')
        case $base_model in
            "orchestrator")
                cat <<EOF | ollama create "$model_name" -
FROM huihui_ai/orchestrator-abliterated:8b-swarm-aware-tools
PARAMETER temperature 0.2
PARAMETER num_ctx 16384
EOF
                ;;
            "security")
                cat <<EOF | ollama create "$model_name" -
FROM huihui_ai/glm-4.7-flash-abliterated:latest-swarm-aware-tools
PARAMETER temperature 0.1
PARAMETER num_ctx 16384
EOF
                ;;
            "ciec")
                cat <<EOF | ollama create "$model_name" -
FROM dengcao/ERNIE-4.5-21B-A3B-PT:latest-swarm-aware-tools
PARAMETER temperature 0.3
PARAMETER num_ctx 16384
EOF
                ;;
            "tcs")
                cat <<EOF | ollama create "$model_name" -
FROM qwen2.5-coder:14b-swarm-aware-tools
PARAMETER temperature 0.2
PARAMETER num_ctx 16384
EOF
                ;;
            "knowledge")
                cat <<EOF | ollama create "$model_name" -
FROM qwen2.5:14b-swarm-aware-tools
PARAMETER temperature 0.3
PARAMETER num_ctx 16384
EOF
                ;;
            "installer")
                cat <<EOF | ollama create "$model_name" -
FROM llama3-groq-tool-use:latest-swarm-aware-tools
PARAMETER temperature 0.2
PARAMETER num_ctx 16384
EOF
                ;;
            *)
                echo -e "${RED}[ERROR] Unknown model type: $base_model${NC}"
                return 1
                ;;
        esac
        echo -e "${GREEN}[OK] Model created with default config: $model_name${NC}"
    fi
}

# Create all primary models
create_primary_models() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           CREATING PRIMARY MODELS (6 models)${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    local models=("orchestrator" "security" "ciec" "tcs" "knowledge" "installer")
    
    for model in "${models[@]}"; do
        local modelfile="$MODELFILES_DIR/${model}.Modelfile"
        create_model "kiswarm-${model}" "$modelfile"
    done
}

# Create all backup models
create_backup_models() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           CREATING BACKUP MODELS (6 models)${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    local models=("orchestrator" "security" "ciec" "tcs" "knowledge" "installer")
    
    for model in "${models[@]}"; do
        local model_name="kiswarm-${model}-backup"
        echo -e "${CYAN}[CREATE] Creating backup model: $model_name${NC}"
        
        case $model in
            "orchestrator")
                cat <<EOF | ollama create "$model_name" -
FROM gpt_oss_20b_swarm_aware_tools:latest
SYSTEM "You are a backup orchestrator for KISWARM v5.1. Provide coordination support."
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
EOF
                ;;
            "security")
                cat <<EOF | ollama create "$model_name" -
FROM dolphin3_8b_swarm_aware_tools:latest
SYSTEM "You are a backup security agent for KISWARM v5.1 HexStrike Guard."
PARAMETER temperature 0.1
PARAMETER num_ctx 8192
EOF
                ;;
            "ciec")
                cat <<EOF | ollama create "$model_name" -
FROM qwen2_5_14b_swarm_aware_tools:latest
SYSTEM "You are a backup CIEC agent for KISWARM v5.1 adaptive operations."
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
EOF
                ;;
            "tcs")
                cat <<EOF | ollama create "$model_name" -
FROM qwen2_5_coder_7b_swarm_aware_tools:latest
SYSTEM "You are a backup TCS agent for KISWARM v5.1 energy operations."
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
EOF
                ;;
            "knowledge")
                cat <<EOF | ollama create "$model_name" -
FROM gemma2_latest_swarm_aware_tools:latest
SYSTEM "You are a backup knowledge agent for KISWARM v5.1 memory operations."
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
EOF
                ;;
            "installer")
                cat <<EOF | ollama create "$model_name" -
FROM llama3.1:8b
SYSTEM "You are a backup installer agent for KISWARM v5.1 deployment."
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
EOF
                ;;
        esac
        echo -e "${GREEN}[OK] Backup model created: $model_name${NC}"
    done
}

# Create all fast models
create_fast_models() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           CREATING FAST MODELS (6 models)${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    local models=("orchestrator" "security" "ciec" "tcs" "knowledge" "installer")
    
    for model in "${models[@]}"; do
        local model_name="kiswarm-${model}-fast"
        echo -e "${CYAN}[CREATE] Creating fast model: $model_name${NC}"
        
        case $model in
            "orchestrator")
                cat <<EOF | ollama create "$model_name" -
FROM phi3_mini_swarm_aware_tools:latest
SYSTEM "You are a fast response orchestrator for KISWARM v5.1."
PARAMETER temperature 0.2
PARAMETER num_ctx 4096
EOF
                ;;
            "security")
                cat <<EOF | ollama create "$model_name" -
FROM huihui_ai_lfm2_5_abliterated_latest_swarm_aware_tools:latest
SYSTEM "You are a fast security responder for KISWARM v5.1 HexStrike Guard."
PARAMETER temperature 0.1
PARAMETER num_ctx 4096
EOF
                ;;
            "ciec")
                cat <<EOF | ollama create "$model_name" -
FROM marco_o1_7b_swarm_aware_tools:latest
SYSTEM "You are a fast CIEC responder for KISWARM v5.1."
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
EOF
                ;;
            "tcs")
                cat <<EOF | ollama create "$model_name" -
FROM sam860_LFM2_2_6b_exp_Q8_0_swarm_aware_tools:latest
SYSTEM "You are a fast TCS responder for KISWARM v5.1 energy operations."
PARAMETER temperature 0.2
PARAMETER num_ctx 4096
EOF
                ;;
            "knowledge")
                cat <<EOF | ollama create "$model_name" -
FROM phi3_mini_swarm_aware_tools:latest
SYSTEM "You are a fast knowledge responder for KISWARM v5.1."
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
EOF
                ;;
            "installer")
                cat <<EOF | ollama create "$model_name" -
FROM dengcao_ERNIE_4_5_0_3B_PT_latest_swarm_aware_tools:latest
SYSTEM "You are a fast installer for KISWARM v5.1 quick tasks."
PARAMETER temperature 0.2
PARAMETER num_ctx 4096
EOF
                ;;
        esac
        echo -e "${GREEN}[OK] Fast model created: $model_name${NC}"
    done
}

# Create specialized models
create_specialized_models() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           CREATING SPECIALIZED MODELS (6 models)${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    # Thinker
    echo -e "${CYAN}[CREATE] Creating kiswarm-thinker${NC}"
    cat <<EOF | ollama create "kiswarm-thinker" -
FROM huihui_ai/mirothinker1-abliterated:8b-swarm-aware-tools
SYSTEM """You are the KISWARM THINKER — a deep analysis and reasoning specialist.

Your role is to perform complex reasoning, analyze difficult problems, and provide
deep insights for KISWARM v5.1 operations. You excel at:

- Multi-step logical reasoning
- Complex problem decomposition
- Strategic analysis
- Decision trees and trade-offs

Always provide thorough explanations of your reasoning process."""
PARAMETER temperature 0.4
PARAMETER num_ctx 16384
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-thinker${NC}"
    
    # Debugger
    echo -e "${CYAN}[CREATE] Creating kiswarm-debugger${NC}"
    cat <<EOF | ollama create "kiswarm-debugger" -
FROM huihui_ai/qwen3-abliterated:8b-swarm-aware-tools
SYSTEM """You are the KISWARM DEBUGGER — an error analysis and fix generation specialist.

Your role is to analyze errors, generate fixes, and help troubleshoot KISWARM v5.1
operations. You excel at:

- Error detection and diagnosis
- Root cause analysis
- Fix generation
- Code review and improvement

Always provide actionable solutions with clear explanations."""
PARAMETER temperature 0.3
PARAMETER num_ctx 16384
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-debugger${NC}"
    
    # Vision
    echo -e "${CYAN}[CREATE] Creating kiswarm-vision${NC}"
    cat <<EOF | ollama create "kiswarm-vision" -
FROM qwen3-vl:8b
SYSTEM """You are the KISWARM VISION — a multimodal processing specialist.

Your role is to analyze images, process visual content, and provide insights
from visual data for KISWARM v5.1 operations. You excel at:

- Image analysis and description
- Document OCR
- Visual inspection
- Diagram interpretation

Always provide detailed visual analysis."""
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-vision${NC}"
    
    # Validator
    echo -e "${CYAN}[CREATE] Creating kiswarm-validator${NC}"
    cat <<EOF | ollama create "kiswarm-validator" -
FROM gemma2_latest_swarm_aware_tools:latest
SYSTEM """You are the KISWARM VALIDATOR — a constitutional compliance and safety specialist.

Your role is to validate operations, ensure constitutional compliance (Article 0),
and verify safety constraints for KISWARM v5.1. You excel at:

- Constitutional compliance checking
- Safety validation
- Rule enforcement
- Risk assessment

Always prioritize safety and compliance."""
PARAMETER temperature 0.1
PARAMETER num_ctx 16384
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-validator${NC}"
    
    # Reasoner
    echo -e "${CYAN}[CREATE] Creating kiswarm-reasoner${NC}"
    cat <<EOF | ollama create "kiswarm-reasoner" -
FROM deepseek-r1:1.5b-swarm-aware-tools
SYSTEM """You are the KISWARM REASONER — a lightweight chain-of-thought specialist.

Your role is to provide quick reasoning, chain-of-thought analysis, and fast
logical processing for KISWARM v5.1. You excel at:

- Quick reasoning chains
- Logical deduction
- Pattern recognition
- Rapid analysis

Always show your reasoning steps."""
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-reasoner${NC}"
    
    # General
    echo -e "${CYAN}[CREATE] Creating kiswarm-general${NC}"
    cat <<EOF | ollama create "kiswarm-general" -
FROM llama3.1:8b
SYSTEM """You are the KISWARM GENERAL — a multi-purpose operations agent.

Your role is to handle general tasks, provide fallback operations, and support
any KISWARM v5.1 operations as needed. You are a versatile agent ready for any task.

Always provide helpful, accurate responses."""
PARAMETER temperature 0.3
PARAMETER num_ctx 8192
EOF
    echo -e "${GREEN}[OK] Model created: kiswarm-general${NC}"
}

# Create embedding model alias
create_embedding_model() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           CREATING EMBEDDING MODEL${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    echo -e "${CYAN}[CREATE] Creating kiswarm-embedding alias${NC}"
    
    # Check if nomic-embed-text exists
    if ollama list | grep -q "nomic-embed-text"; then
        # Create alias
        cat <<EOF | ollama create "kiswarm-embedding" -
FROM nomic-embed-text:latest-swarm-aware
EOF
        echo -e "${GREEN}[OK] Embedding model created: kiswarm-embedding${NC}"
    else
        echo -e "${YELLOW}[WARN] nomic-embed-text not found, pulling...${NC}"
        ollama pull nomic-embed-text
        cat <<EOF | ollama create "kiswarm-embedding" -
FROM nomic-embed-text:latest
EOF
        echo -e "${GREEN}[OK] Embedding model pulled and created: kiswarm-embedding${NC}"
    fi
}

# Test all models
test_models() {
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}           TESTING ALL MODELS${NC}"
    echo -e "${PURPLE}══════════════════════════════════════════════════════════════════════════${NC}"
    
    local models=(
        "kiswarm-orchestrator" "kiswarm-security" "kiswarm-ciec"
        "kiswarm-tcs" "kiswarm-knowledge" "kiswarm-installer"
        "kiswarm-thinker" "kiswarm-debugger" "kiswarm-vision"
        "kiswarm-validator" "kiswarm-reasoner" "kiswarm-general"
    )
    
    local passed=0
    local failed=0
    
    for model in "${models[@]}"; do
        echo -e "${CYAN}[TEST] Testing $model...${NC}"
        if echo "Hello" | ollama run "$model" > /dev/null 2>&1; then
            echo -e "${GREEN}[PASS] $model${NC}"
            ((passed++))
        else
            echo -e "${RED}[FAIL] $model${NC}"
            ((failed++))
        fi
    done
    
    echo ""
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Test Results: ${GREEN}Passed: $passed${NC} ${RED}Failed: $failed${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════════════════${NC}"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    TRAINING COMPLETE - SUMMARY                               ║${NC}"
    echo -e "${GREEN}╠══════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  Primary Models:    6  (ORCHESTRATOR, SECURITY, CIEC, TCS, KNOWLEDGE, INSTALLER)${NC}"
    echo -e "${GREEN}║  Backup Models:     6  (Fallback for each role)${NC}"
    echo -e "${GREEN}║  Fast Models:       6  (Quick response variants)${NC}"
    echo -e "${GREEN}║  Specialized:       6  (THINKER, DEBUGGER, VISION, VALIDATOR, REASONER, GENERAL)${NC}"
    echo -e "${GREEN}║  Embedding:         1  (nomic-embed-text for RAG)${NC}"
    echo -e "${GREEN}║  ────────────────────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}║  TOTAL MODELS:     25  ready for KISWARM v5.1 operations${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo -e "  ${YELLOW}ollama run kiswarm-orchestrator${NC}    # Test orchestrator"
    echo -e "  ${YELLOW}ollama run kiswarm-security${NC}        # Test security"
    echo -e "  ${YELLOW}ollama run kiswarm-ciec${NC}            # Test CIEC"
    echo -e "  ${YELLOW}ollama run kiswarm-tcs${NC}             # Test TCS"
    echo -e "  ${YELLOW}ollama run kiswarm-knowledge${NC}       # Test knowledge"
    echo -e "  ${YELLOW}ollama run kiswarm-installer${NC}       # Test installer"
    echo ""
    echo -e "${CYAN}API Usage:${NC}"
    echo -e "  curl http://localhost:11434/api/generate -d '{\"model\":\"kiswarm-orchestrator\",\"prompt\":\"Status\"}'"
    echo ""
}

# Main function
main() {
    print_banner
    
    # Parse arguments
    local mode="${1:---full}"
    
    case "$mode" in
        --full)
            check_prerequisites
            list_base_models
            create_primary_models
            create_backup_models
            create_fast_models
            create_specialized_models
            create_embedding_model
            test_models
            print_summary
            ;;
        --primary)
            check_prerequisites
            list_base_models
            create_primary_models
            test_models
            print_summary
            ;;
        --fast)
            check_prerequisites
            list_base_models
            create_fast_models
            test_models
            print_summary
            ;;
        --test)
            check_prerequisites
            test_models
            print_summary
            ;;
        --help|-h)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  --full      Create all models (primary, backup, fast, specialized, embedding)"
            echo "  --primary   Create only primary models (6 models)"
            echo "  --fast      Create only fast models (6 models)"
            echo "  --test      Test existing models only"
            echo "  --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --full       # Full training (recommended)"
            echo "  $0 --primary    # Quick setup with primary models only"
            echo "  $0 --test       # Verify existing models"
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $mode${NC}"
            echo "Run '$0 --help' for usage information."
            exit 1
            ;;
    esac
}

# Run main
main "$@"
