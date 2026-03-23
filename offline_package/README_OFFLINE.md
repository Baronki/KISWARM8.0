# KISWARM7 OFFLINE INSTALLATION PACKAGE

**Complete Air-Gapped Deployment Solution**

---

## 📦 Package Contents

```
offline_package/
├── pip_wheels/              # Python dependency wheels
├── scripts/                 # Installation scripts
│   └── kiswarm_offline_installer.py
├── docs/                    # Documentation
├── models_manifest/         # KI model manifests
│   └── ki_models.json
├── requirements-offline.txt # Complete requirements list
└── README_OFFLINE.md        # This file
```

---

## 🚀 Quick Start

### Option 1: Copy-Paste Deployment (Recommended)

1. Copy the entire `offline_package/` directory to target machine
2. Run:

```bash
cd offline_package/scripts
python3 kiswarm_offline_installer.py
```

### Option 2: Manual Installation

```bash
# 1. Install Python dependencies from wheels
pip install --no-index --find-links=offline_package/pip_wheels -r offline_package/requirements-offline.txt

# 2. Install Ollama (requires internet or offline script)
curl -fsSL https://ollama.com/install.sh | sh

# 3. Clone KISWARM7
git clone https://github.com/Baronki/KISWARM7.git ~/KISWARM7

# 4. Pull KI models
ollama pull baronki1/installer
ollama pull baronki1/orchestrator

# 5. Initialize KISWARM
cd ~/KISWARM7
export PYTHONPATH="$(pwd)/backend:$(pwd)/backend/python"
python3 -c "from sentinel.sentinel_api import app; print('KISWARM Ready!')"
```

---

## 📋 Preparing the Offline Package

### Step 1: Download Pip Wheels

```bash
cd offline_package
pip download -r requirements-offline.txt -d pip_wheels/
```

This downloads all Python dependencies as `.whl` files.

### Step 2: Download Ollama Installer (Optional)

```bash
curl -fsSL https://ollama.com/install.sh -o scripts/install_ollama_offline.sh
chmod +x scripts/install_ollama_offline.sh
```

### Step 3: Download KI Models (Optional but Recommended)

```bash
# Install Ollama first
ollama pull baronki1/installer
ollama pull baronki1/orchestrator
ollama pull baronki1/knowledge
ollama pull baronki1/security

# Export models for offline transfer
ollama save baronki1/installer -o models_manifest/installer.tar
ollama save baronki1/orchestrator -o models_manifest/orchestrator.tar
```

### Step 4: Bundle KISWARM Source (For Complete Offline)

```bash
# Clone the repository
git clone --depth 1 https://github.com/Baronki/KISWARM7.git kiswarm_source
```

---

## 🔧 Model Tiers

| Tier | Models | Size | Use Case |
|------|--------|------|----------|
| **essential** | installer, orchestrator | ~10 GB | Minimum viable deployment |
| **recommended** | installer, orchestrator, knowledge, security | ~40 GB | Standard production |
| **full** | All 6 primary models | ~60 GB | Complete KISWARM capabilities |

---

## 📋 Requirements

### Minimum System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11+ |
| RAM | 16 GB | 32 GB+ |
| Disk | 100 GB | 500 GB+ |
| GPU | Optional | NVIDIA 12GB+ VRAM |

### Supported Platforms

- ✅ Ubuntu 22.04+
- ✅ Debian 11+
- ✅ CentOS 8+
- ✅ RHEL 8+
- ✅ WSL2 (Windows)
- ✅ Google Colab (with internet for Ollama)

---

## 🧠 KI Models

The KISWARM7 system uses pretrained KI models from the Ollama registry:

| Model | Role | Size | VRAM |
|-------|------|------|------|
| `baronki1/orchestrator` | System coordination | 5 GB | 4 GB |
| `baronki1/installer` | Self-replication | 4.7 GB | 4 GB |
| `baronki1/security` | HexStrike Guard | 18 GB | 16 GB |
| `baronki1/ciec` | Industrial AI | 13 GB | 12 GB |
| `baronki1/tcs` | Solar/Energy | 9 GB | 8 GB |
| `baronki1/knowledge` | RAG/Memory | 9 GB | 8 GB |

**Registry:** https://ollama.com/baronki1

---

## 🛠️ Troubleshooting

### Pip wheel installation fails

```bash
# Try installing core packages first
pip install flask flask-cors requests rich psutil --no-index --find-links=pip_wheels/

# Then install remaining
pip install -r requirements-offline.txt --no-index --find-links=pip_wheels/
```

### Ollama not available

For complete offline installation, Ollama must be installed beforehand. Download from:
https://ollama.com/download

### KI models fail to pull

If offline, ensure models were exported with `ollama save` and import with:
```bash
ollama load < models_manifest/installer.tar
```

---

## 📚 Related Documentation

- [COLAB_QUICKSTART.md](../COLAB_QUICKSTART.md) - Google Colab deployment
- [SINGLE_COMMAND_DEPLOYMENT.md](../kiinstaller/SINGLE_COMMAND_DEPLOYMENT.md) - Single-command install
- [README.md](../README.md) - Main project documentation

---

## 🔗 Repository

- **Main:** https://github.com/Baronki/KISWARM7
- **Legacy:** https://github.com/Baronki/KISWARM6.0
- **Models:** https://ollama.com/baronki1

---

*"A synchronized swarm is a sovereign swarm."*
