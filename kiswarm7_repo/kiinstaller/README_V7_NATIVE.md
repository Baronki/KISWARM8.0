# KISWARM v7.0 NATIVE INSTALLER

**Self-Replicating Autonomous Installation System**

---

## 🔗 REPOSITORY URL

```
https://github.com/Baronki/KISWARM7
```

**For Google Colab:**
```python
!git clone https://github.com/Baronki/KISWARM7.git
%cd KISWARM7
```

---

## Overview

The KISWARM v7.0 Native Installer is a fully autonomous deployment system that installs KISWARM without Docker. It incorporates all lessons learned from the KiloCode field test and is designed for:

- **Zero human intervention** - Fully autonomous operation
- **Self-healing** - Automatic error detection and recovery
- **Hardware-adaptive** - GPU-aware model selection
- **Universal compatibility** - Works on any Linux environment

---

## Key Features

### 1. Permission Auto-Fix (Phase 1 - CRITICAL)
The installer fixes ownership issues FIRST, preventing the most common failure mode identified in KiloCode testing.

### 2. Hardware Detection (Phase 2)
Automatically detects:
- CPU cores and model
- RAM availability
- GPU (NVIDIA/AMD) with VRAM
- Disk space
- Operating system
- Environment type (Colab, WSL, VM, bare metal)

### 3. Model Selection Logic

```python
# Auto-selection based on GPU VRAM
GPU VRAM >= 24GB: Primary + Specialized models
GPU VRAM >= 12GB: Primary models (orchestrator, security, knowledge, installer)
GPU VRAM >= 8GB:  Fast variants (orchestrator-fast, knowledge-fast, installer-fast)
CPU Only:         Minimal (orchestrator-fast, knowledge-fast)
```

### 4. Self-Healing Capabilities

| Error Pattern | Auto-Fix |
|---------------|----------|
| Permission denied | chown -R $(whoami) |
| Module not found | pip install missing |
| Connection refused | Check and restart service |
| Role does not exist | Recreate database |
| Port in use | Kill conflicting process |

### 5. 14-Phase Installation

1. Permission Fix (CRITICAL)
2. Environment Detection
3. System Packages (apt)
4. Python Setup (venv)
5. Node.js Setup
6. PostgreSQL Setup
7. Redis Setup
8. Ollama Installation
9. Model Deployment
10. Repository Clone
11. KISWARM Setup
12. Systemd Services
13. Health Check
14. Verification

---

## Usage

### Quick Deploy (Single Command)

```python
from kiswarm_installer_v7_native import quick_deploy
result = quick_deploy()
```

### Custom Installation

```python
from kiswarm_installer_v7_native import autonomous_deploy

result = autonomous_deploy(
    install_dir="/opt/kiswarm",
    model_tier="auto"  # auto, minimal, standard, full
)
```

### Command Line

```bash
# Full installation
python kiswarm_installer_v7_native.py

# Minimal (skip heavy components)
python kiswarm_installer_v7_native.py --model-tier minimal

# Skip specific phases
python kiswarm_installer_v7_native.py --skip-ollama --skip-models

# Specific models only
python kiswarm_installer_v7_native.py --models baronki1/orchestrator baronki1/knowledge
```

---

## Model Tiers

| Tier | Models | Total Size | Use Case |
|------|--------|------------|----------|
| minimal | 2 fast models | ~4 GB | Testing, minimal hardware |
| standard | 4 primary models | ~40 GB | Production |
| auto | Hardware-adaptive | Varies | Recommended |
| full | 21 models | ~150 GB | Complete deployment |

---

## Supported Environments

- ✅ Ubuntu 22.04+ (Recommended)
- ✅ Debian 11+
- ✅ Google Colab
- ✅ WSL2 (Windows Subsystem for Linux)
- ✅ Cloud VMs (AWS, Azure, GCP)
- ✅ Bare Metal Servers

---

## Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10 | 3.11+ |
| Node.js | 18.0 | 20.0+ |
| RAM | 16 GB | 32 GB+ |
| Disk | 100 GB | 500 GB+ |
| GPU | Optional | NVIDIA 12GB+ VRAM |

---

## KI Agent Models (27 Total)

### Primary Swarm (6)
```
baronki1/orchestrator   - System coordination
baronki1/security       - HexStrike Guard
baronki1/ciec           - Industrial AI
baronki1/tcs            - Solar energy
baronki1/knowledge      - RAG operations
baronki1/installer      - Deployment agent
```

### Fast Layer (6)
CPU-optimized variants with 50% smaller size.

### Specialized (9)
Deep analysis models for specific tasks.

### Backup (6)
Redundancy layer for failover.

---

## Lessons Learned from KiloCode Testing

1. **Permission Fix FIRST** - Always fix ownership before any operation
2. **PYTHONPATH** - Include both backend/ and backend/python/
3. **Minimal imports** - Avoid nested parentheses in __init__.py
4. **Pre-install deps** - pip install flask flask-cors structlog first
5. **Service timing** - Wait 60+ seconds for AI model loading
6. **Database volumes** - Check and recreate stale PostgreSQL volumes

---

## GitHub Repositories

| Repository | Purpose |
|------------|---------|
| https://github.com/Baronki/KISWARM7 | Main v7.0 repository |
| https://github.com/Baronki/KISWARM6.0 | Legacy system |
| https://github.com/Baronki/KISWARMAGENTS1.0 | Model definitions |
| https://ollama.com/baronki1 | Model registry |

---

## Support

For issues or questions:
- Check the worklog: `/home/z/my-project/worklog.md`
- Read the knowledge base: `/home/z/my-project/KISWARM_KNOWLEDGE_BASE.md`
- Review uploaded feedback: `/home/z/my-project/upload/`

---

*"A synchronized swarm is a sovereign swarm."*
