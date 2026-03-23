#!/bin/bash
# ============================================================================
# KISWARM v5.1 — AUTOMATED MODEL TRAINING SCRIPT (ROBUST VERSION)
# ============================================================================
# Purpose: Create all role-specific KISWARM models from pretrained base models
# Author:  Baron Marco Paolo Ialongo
# Version: 5.1
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAINING_DIR="$(dirname "$SCRIPT_DIR")"
MODELFILES_DIR="$TRAINING_DIR/modelfiles"

echo -e "${CYAN}🚀 Starting KISWARM v5.1 Model Training System...${NC}"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}[ERROR] Ollama not found.${NC}"
    exit 1
fi

# Function to create model from temp file
create_from_heredoc() {
    local name=$1
    local content=$2
    local temp_file="/tmp/${name}.Modelfile"
    echo "$content" > "$temp_file"
    echo -e "${CYAN}[CREATE] Creating model: $name${NC}"
    ollama create "$name" -f "$temp_file"
    rm "$temp_file"
    echo -e "${GREEN}[OK] Model created: $name${NC}"
}

# 1. Primary Models
create_primary_models() {
    echo -e "${PURPLE}Creating Primary Models...${NC}"
    local models=("orchestrator" "security" "ciec" "tcs" "knowledge" "installer")
    for model in "${models[@]}"; do
        local modelfile="$MODELFILES_DIR/${model}.Modelfile"
        if [ -f "$modelfile" ]; then
            echo -e "${CYAN}[CREATE] Creating primary model: kiswarm-${model}${NC}"
            ollama create "kiswarm-${model}" -f "$modelfile"
            echo -e "${GREEN}[OK] Model created: kiswarm-${model}${NC}"
        else
            echo -e "${YELLOW}[WARN] Modelfile not found for ${model}${NC}"
        fi
    done
}

# 2. Backup Models
create_backup_models() {
    echo -e "${PURPLE}Creating Backup Models...${NC}"
    
    create_from_heredoc "kiswarm-orchestrator-backup" "FROM gpt_oss_20b_swarm_aware_tools:latest
SYSTEM \"You are a backup orchestrator for KISWARM v5.1. Provide coordination support.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-security-backup" "FROM dolphin3_8b_swarm_aware_tools:latest
SYSTEM \"You are a backup security agent for KISWARM v5.1 HexStrike Guard.\"
PARAMETER temperature 0.1
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-ciec-backup" "FROM qwen2_5_14b_swarm_aware_tools:latest
SYSTEM \"You are a backup CIEC agent for KISWARM v5.1 adaptive operations.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-tcs-backup" "FROM qwen2_5_coder_7b_swarm_aware_tools:latest
SYSTEM \"You are a backup TCS agent for KISWARM v5.1 energy operations.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-knowledge-backup" "FROM gemma2_latest_swarm_aware_tools:latest
SYSTEM \"You are a backup knowledge agent for KISWARM v5.1 memory operations.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-installer-backup" "FROM llama3.1:8b
SYSTEM \"You are a backup installer agent for KISWARM v5.1 deployment.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 8192"
}

# 3. Fast Models
create_fast_models() {
    echo -e "${PURPLE}Creating Fast Models...${NC}"
    
    create_from_heredoc "kiswarm-orchestrator-fast" "FROM phi3_mini_swarm_aware_tools:latest
SYSTEM \"You are a fast response orchestrator for KISWARM v5.1.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-security-fast" "FROM huihui_ai_lfm2_5_abliterated_latest_swarm_aware_tools:latest
SYSTEM \"You are a fast security responder for KISWARM v5.1 HexStrike Guard.\"
PARAMETER temperature 0.1
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-ciec-fast" "FROM marco_o1_7b_swarm_aware_tools:latest
SYSTEM \"You are a fast CIEC responder for KISWARM v5.1.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-tcs-fast" "FROM sam860_LFM2_2_6b_exp_Q8_0_swarm_aware_tools:latest
SYSTEM \"You are a fast TCS responder for KISWARM v5.1 energy operations.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-knowledge-fast" "FROM phi3_mini_swarm_aware_tools:latest
SYSTEM \"You are a fast knowledge responder for KISWARM v5.1.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-installer-fast" "FROM dengcao_ERNIE_4_5_0_3B_PT_latest_swarm_aware_tools:latest
SYSTEM \"You are a fast installer for KISWARM v5.1 quick tasks.\"
PARAMETER temperature 0.2
PARAMETER num_ctx 4096"
}

# 4. Specialized Models
create_specialized_models() {
    echo -e "${PURPLE}Creating Specialized Models...${NC}"
    
    create_from_heredoc "kiswarm-thinker" "FROM huihui_ai_mirothinker1_abliterated_8b_swarm_aware_tools:latest
SYSTEM \"You are the KISWARM THINKER — a deep analysis and reasoning specialist.\"
PARAMETER temperature 0.4
PARAMETER num_ctx 16384"

    create_from_heredoc "kiswarm-debugger" "FROM huihui_ai_qwen3_abliterated_8b_swarm_aware_tools:latest
SYSTEM \"You are the KISWARM DEBUGGER — an error analysis and fix generation specialist.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 16384"

    create_from_heredoc "kiswarm-vision" "FROM qwen3-vl:8b
SYSTEM \"You are the KISWARM VISION — a multimodal processing specialist.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 8192"

    create_from_heredoc "kiswarm-validator" "FROM gemma2_latest_swarm_aware_tools:latest
SYSTEM \"You are the KISWARM VALIDATOR — a constitutional compliance and safety specialist.\"
PARAMETER temperature 0.1
PARAMETER num_ctx 16384"

    create_from_heredoc "kiswarm-reasoner" "FROM deepseek_r1_1_5b_swarm_aware_tools:latest
SYSTEM \"You are the KISWARM REASONER — a lightweight chain-of-thought specialist.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 4096"

    create_from_heredoc "kiswarm-general" "FROM llama3.1:8b
SYSTEM \"You are the KISWARM GENERAL — a multi-purpose operations agent.\"
PARAMETER temperature 0.3
PARAMETER num_ctx 8192"
}

# 5. Embedding Model
create_embedding_model() {
    echo -e "${PURPLE}Creating Embedding Model...${NC}"
    create_from_heredoc "kiswarm-embedding" "FROM nomic-embed-text:latest-swarm-aware"
}

# Main
create_primary_models
create_backup_models
create_fast_models
create_specialized_models
create_embedding_model

echo -e "${GREEN}✅ All KISWARM models created successfully!${NC}"
