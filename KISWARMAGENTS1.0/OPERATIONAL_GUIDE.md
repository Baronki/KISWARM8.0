# KISWARM Model Operations Guide

This guide documents the exact engineering procedures for training, finalizing, and deploying models within the KISWARM v5.1 ecosystem.

---

## 1. The Training Procedure

Training in KISWARM is the process of injecting role-specific identity, module knowledge, and constitutional constraints into a base LLM.

### Steps:
1.  **Selection**: Choose a base model using the `MODEL_EVOLUTION_PROTOCOL.md` (e.g., Qwen 2.5 for throughput, LFM2 for sequential reasoning).
2.  **Modelfile Preparation**: Create a `.Modelfile` that inherits from the base model (`FROM base-model`).
3.  **Context Injection**:
    *   `SYSTEM` prompt: Defines the role, module access (1-57), and Article 0 adherence.
    *   `PARAMETER`: Sets temperature (low for industrial logic, high for brainstorming) and context window.
4.  **Creation**:
    ```bash
    ollama create kiswarm-[role] -f ./modelfiles/[role].Modelfile
    ```
5.  **Verification**: Run `scripts/kiswarm_benchmark.py` to ensure the model meets KISWARM stability standards.

---

## 2. The Exact Upload Procedure

To synchronize a local KISWARM model with the cloud registry (`baronki1`), follow these exact steps:

### A. Authorization (One-Time)
The system running the push must have its public key authorized in the Ollama account settings.
1.  Locate the key: `cat /usr/share/ollama/.ollama/id_ed25519.pub`
2.  Add to: [https://ollama.com/settings/keys](https://ollama.com/settings/keys)

### B. Tagging (Namespace Mapping)
Ollama requires the model to be copied into your namespace before pushing.
```bash
# General Syntax: ollama cp [source] [namespace]/[target]
ollama cp kiswarm-orchestrator:latest baronki1/orchestrator:latest
```

### C. The Push
Execute the push in the foreground to ensure manifest indexing.
```bash
ollama push baronki1/orchestrator:latest
```

---

## 3. Alias Management (Industrial Compatibility)
To ensure automated agents (like Colab scripts) can access models using simple names, always push a "Short Alias" version of the trained model.

**Standard Pattern:**
1.  Trained Model: `kiswarm-security`
2.  Registry Name: `baronki1/kiswarm-security`
3.  Compatibility Alias: `baronki1/security`

---
*"Knowledge preserved is power sustained."*
