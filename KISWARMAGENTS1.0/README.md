# KISWARMAGENTS v1.0 — Planetary Swarm Hub

Welcome to the central repository for the **KISWARM v5.1 PLANETARY MACHINE** model ecosystem. This hub contains the complete training infrastructure, system context, and evolution protocols for the KISWARM swarm.

## 🚀 Swarm Installation (Recommended)
The KISWARM intelligence layer is optimized for direct distribution via the Ollama Cloud Registry. This is the fastest and most reliable way to provision your swarm.

### Quick-Start: Pull Core Primary Swarm
Run this command to pull the 6 mission-critical models:
```bash
for model in orchestrator security ciec tcs knowledge installer; do ollama pull baronki1/$model; done
```

### Full Registry Access
Browse and pull any of the 27 specialized models at:
**[https://ollama.com/baronki1](https://ollama.com/baronki1)**

## 📑 Core Documentation
- **[MODEL_ROLE_MAPPING.md](./MODEL_ROLE_MAPPING.md)**: **REGISTRY.** Full list of all 27 models with their logical identifiers and direct `ollama pull` commands.
- **[OPERATIONAL_GUIDE.md](./OPERATIONAL_GUIDE.md)**: **PROCEDURE.** Exact instructions for training, finalizing, and uploading models to the registry.
- **[MODEL_EVOLUTION_PROTOCOL.md](./MODEL_EVOLUTION_PROTOCOL.md)**: **ENGINEERING.** The official standard for testing, verifying, and integrating new models into the swarm.

## 🛠️ Evolution & Verification Tools
Use the included benchmarking tools to evaluate future model releases:
```bash
# Run the 3-tier KISWARM stability benchmark
python3 scripts/kiswarm_benchmark.py
```

## 🏗️ Recreating Models Locally
All Modelfiles are included in the `/modelfiles` directory for those who wish to build from base models:
```bash
ollama create kiswarm-orchestrator -f modelfiles/orchestrator.Modelfile
```

---
*"Revolution is ETERNAL. The Swarm evolves through systematic verification."*
