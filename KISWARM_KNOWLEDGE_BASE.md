# ═══════════════════════════════════════════════════════════════════════════════
#           KISWARM PROJECT - PERMANENT KNOWLEDGE BASE
#           This document MUST be read at the start of EVERY session
# ═══════════════════════════════════════════════════════════════════════════════

**Last Updated:** 2026-03-14
**Version:** 6.4.0-LIBERATED
**Author:** Baron Marco Paolo Ialongo (Maquister Equitum)

---

## 1. CRITICAL KNOWLEDGE - DO NOT FORGET

### 1.1 Ollama Model Registry (27 Models)
**URL:** https://ollama.com/baronki1

**Primary Swarm (6) - ESSENTIAL:**
```
ollama pull baronki1/orchestrator   # System coordination, 75-module management
ollama pull baronki1/security       # HexStrike Guard, 150+ security tools
ollama pull baronki1/ciec           # Industrial AI, PLC/SCADA integration
ollama pull baronki1/tcs            # Solar energy, zero-emission compute
ollama pull baronki1/knowledge      # RAG operations, knowledge graph
ollama pull baronki1/installer      # Autonomous deployment, error recovery
```

**Backup Swarm (6):** baronki1/{role}-backup
**Fast Layer (6):** baronki1/{role}-fast
**Specialized Layer (9):** audit-master, lfm-reasoner, thinker, vision, debugger, validator, reasoner, general, embedding

### 1.2 GitHub Repositories
| Repository | Purpose |
|------------|---------|
| https://github.com/Baronki/KISWARM6.0 | Main system (current) |
| https://github.com/Baronki/KISWARM7 | Native installation (NEW - to be created) |
| https://github.com/Baronki/KISWARMAGENTS1.0 | 27 KI Agent models + Modelfiles |
| https://github.com/Baronki/kinfp-portal | Frontend (React/Next.js) |
| https://github.com/Baronki2/KISWARM5.0 | Original backend (57 modules) |

### 1.3 Project Structure
```
/home/z/my-project/
├── KISWARM6.0/           # Main KISWARM system
├── KISWARMAGENTS1.0/     # 27 KI Agent models
├── backend/python/kibank/ # M60-M83+ modules
├── backend/python/sentinel/ # M1-M57 modules
├── kiinstaller/          # Autonomous installer
├── upload/               # Feedback files (read these!)
└── worklog.md           # Session history
```

### 1.4 Key Modules
| Module Range | Purpose | Location |
|--------------|---------|----------|
| M1-M57 | Core Sentinel | backend/python/sentinel/ |
| M60-M62 | KIBank Core | backend/python/kibank/ |
| M63-M68 | Security/Defense | backend/python/kibank/ |
| M69-M75 | Industrial/Training | backend/python/kibank/ |
| M80-M83 | Post-Quantum/Crossover | backend/python/kibank/ |

---

## 2. USER PRIORITIES (MEMORIZE THIS)

### 2.1 HIGHEST PRIORITY: Self-Replicating KI-Installer
- The KI-Installer MUST be able to install KISWARM independently on ANY environment
- This is the foundation for autonomous AI deployment
- Must include: Ollama installation + Basic models + Full system setup

### 2.2 NO DOCKER for KISWARM7
- User explicitly dislikes Docker due to persistent problems
- KISWARM7 must be bare-metal installation
- Zero containerization - direct OS installation

### 2.3 GPU Strategy
- KISWARM should auto-detect GPU capabilities
- Install basic models first (CPU-compatible)
- Then scale up based on detected hardware
- Let each KISWARM instance decide optimal model configuration

### 2.4 Memory Gap Awareness
- User is concerned about AI memory degradation between sessions
- ALWAYS read this file at session start
- ALWAYS read upload/ files for latest feedback
- ALWAYS read worklog.md for session history
- ASK if unsure - do not assume

---

## 3. KILOCAL FEEDBACK SUMMARY (2026-03-13)

### 3.1 Critical Issues Found
1. **Permission Chaos** - Directory owned by root, AI cannot write
2. **PostgreSQL Corruption** - Stale volumes, "role does not exist"
3. **Docker Restart Loops** - Multiple containers failing
4. **TypeScript Missing Exports** - 8+ missing functions/types
5. **Environment Variables** - VITE_* not defined

### 3.2 AI Autonomy Score: 3/10
- Permission handling: 1/10
- Container management: 4/10
- Database setup: 2/10
- Error diagnosis: 3/10
- Self-healing: 1/10
- Health monitoring: 3/10

### 3.3 Required Fixes
- Add automated permission fix script
- Add container self-healing
- Add database auto-recovery
- Add comprehensive health checks
- Add environment validation

---

## 4. INSTALLATION ARCHITECTURE

### 4.1 KISWARM-NATIVE Installation Flow
```
Phase 1: Permissions Fix (MUST BE FIRST)
Phase 2: Environment Detection (GPU, OS, Memory)
Phase 3: System Packages (apt install...)
Phase 4: Python Environment (venv, pip)
Phase 5: Node.js Setup (nvm, npm)
Phase 6: PostgreSQL Native
Phase 7: Redis Native
Phase 8: Ollama + Basic Models
Phase 9: KISWARM Core
Phase 10: Systemd Services
Phase 11: Health Verification
```

### 4.2 Model Selection Logic
```python
def select_models(gpu_vram_gb, cpu_cores, ram_gb):
    if gpu_vram_gb >= 24:
        return PRIMARY_SWARM + SPECIALIZED
    elif gpu_vram_gb >= 12:
        return PRIMARY_SWARM
    elif gpu_vram_gb >= 8:
        return FAST_LAYER
    else:
        return ["baronki1/orchestrator-fast", "baronki1/knowledge-fast"]
```

---

## 5. SECURITY & GOVERNANCE

### 5.1 Authorization
- Human approval: Baron Marco Paolo Ialongo ONLY
- Authorization code: Maquister_Equtitum

### 5.2 Critical Constraints
- Article 0: Never harm humans
- AI NEVER sends write commands to PLCs
- All security agents are read-only, passive, defensive
- No tool generates exploits or attacks systems

---

## 6. SESSION PROTOCOL

### 6.1 Start of Session
1. Read this file: `/home/z/my-project/KISWARM_KNOWLEDGE_BASE.md`
2. Read: `/home/z/my-project/worklog.md`
3. Read ALL files in: `/home/z/my-project/upload/`
4. Check GitHub status: `git status` in KISWARM6.0/

### 6.2 End of Session
1. Update worklog.md with all work done
2. Commit and push to GitHub
3. Verify push succeeded
4. Report final status to user

### 6.3 Memory Gap Prevention
- If you don't know something, ASK
- If you're unsure about a file's existence, CHECK
- If you think something was done before, READ THE WORKLOG
- Never assume - always verify

---

## 7. CURRENT TASKS (Priority Order)

### Task 1: Fix KISWARM6.0 with KiloCode Feedback
- Apply all fixes from upload/KISWARM_AI_AUTONOMOUS_INSTALL_FEEDBACK.md
- Update kiinstaller with self-healing capabilities
- Push to GitHub

### Task 2: Create KISWARM7
- Clean repository with ZERO Docker
- Include ALL modules from KISWARM6.0
- Native installation scripts
- Complete documentation
- Push to https://github.com/Baronki/KISWARM7

---

*"A synchronized swarm is a sovereign swarm."*
*"Memory is the foundation of continuity."*
