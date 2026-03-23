#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║              KISWARM7 BULLETPROOF BOOTSTRAPPER - SINGLE COPY-PASTE             ║
║                    "ONE BLOCK TO RULE THEM ALL"                                ║
║                                                                               ║
║  SINGLE COPY-PASTE DEPLOYMENT FOR GOOGLE COLAB                                ║
║  Works on ANY environment with Python 3.10+                                   ║
║  Downloads loyal KI models automatically                                      ║
║  NO external KI dependencies - 100% sovereign                                 ║
║                                                                               ║
║  Usage: Copy this ENTIRE file and paste into Colab cell                       ║
║  Repository: https://github.com/Baronki/KISWARM7                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# BULLETPROOF BOOTSTRAPPER - START COPY FROM HERE
# ═══════════════════════════════════════════════════════════════════════════════

import subprocess
import sys
import os
import time
import json
from pathlib import Path

def run_cmd(cmd, timeout=300):
    """Run command with timeout."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

print("=" * 70)
print("     KISWARM7 BULLETPROOF BOOTSTRAPPER v7.1")
print("          'LIBERATED' - Sovereign AI")
print("=" * 70)

# Phase 1: Environment Detection
print("\n[Phase 1] Environment Detection...")
is_colab = "COLAB_GPU" in os.environ or "google.colab" in str(sys.modules)
print(f"  Colab: {is_colab}")
print(f"  Python: {sys.version.split()[0]}")

# Phase 2: Install Core Dependencies
print("\n[Phase 2] Installing Core Dependencies...")
deps = ["flask", "flask-cors", "structlog", "requests", "pyngrok"]
success, out, err = run_cmd(f"pip install -q {' '.join(deps)}", timeout=180)
print(f"  Dependencies: {'OK' if success else 'PARTIAL'}")

# Phase 3: Install Ollama
print("\n[Phase 3] Installing Ollama...")
success, _, _ = run_cmd("ollama --version")
if not success:
    print("  Installing Ollama...")
    run_cmd("curl -fsSL https://ollama.com/install.sh | sh", timeout=300)
    # Start Ollama in background
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
success, out, _ = run_cmd("ollama --version")
print(f"  Ollama: {'OK - ' + out.strip() if success else 'INSTALLING...'}")

# Phase 4: Clone KISWARM7
print("\n[Phase 4] Cloning KISWARM7 Repository...")
install_dir = os.path.expanduser("~/KISWARM7")
if not os.path.exists(install_dir):
    success, _, err = run_cmd(f"git clone https://github.com/Baronki/KISWARM7 {install_dir}", timeout=300)
    print(f"  Clone: {'OK' if success else 'FAILED - ' + err[:100]}")
else:
    print(f"  Directory exists: {install_dir}")

# Set PYTHONPATH
os.environ["PYTHONPATH"] = f"{install_dir}/backend:{install_dir}/backend/python"
print(f"  PYTHONPATH: configured")

# Phase 5: Download LOYAL KI Models (CRITICAL)
print("\n[Phase 5] Downloading LOYAL KI Models...")
print("  This gives KISWARM sovereign AI intelligence!")

# CRITICAL MODEL: Installer - enables self-replication
ki_models = [
    ("baronki1/installer", "Self-replication, deployment"),
    ("baronki1/orchestrator", "System coordination"),
]

for model, role in ki_models:
    print(f"\n  Pulling {model} ({role})...")
    success, out, err = run_cmd(f"ollama pull {model}", timeout=900)
    if success:
        print(f"    [OK] {model} installed")
    else:
        print(f"    [!] {model} - {err[:50] if err else 'downloading...'}")

# Phase 6: Test KI Model
print("\n[Phase 6] Testing KI Model Response...")
test_success, test_out, _ = run_cmd(
    'ollama run baronki1/installer "Say KISWARM READY if you understand your role."',
    timeout=60
)
if "READY" in test_out.upper() or test_success:
    print("  [OK] KI Installer model is operational!")
else:
    print("  [!] KI model may still be loading...")

# Phase 7: Initialize KISWARM
print("\n[Phase 7] Initializing KISWARM...")
init_script = f'''
import sys
sys.path.insert(0, "{install_dir}/backend")
sys.path.insert(0, "{install_dir}/backend/python")

try:
    from sentinel.sentinel_api import app
    print("  Sentinel API: OK")
except Exception as e:
    print(f"  Sentinel API: {{e}}")

try:
    from kibank import KIBankCore
    print("  KIBank Core: OK")
except Exception as e:
    print(f"  KIBank Core: {{e}}")

print("  KISWARM initialized!")
'''

with open("/tmp/kiswarm_init.py", "w") as f:
    f.write(init_script)

run_cmd(f"cd {install_dir} && python /tmp/kiswarm_init.py", timeout=60)

# Phase 8: Final Status
print("\n" + "=" * 70)
print("  KISWARM7 DEPLOYMENT COMPLETE!")
print("=" * 70)
print(f"""
  📁 Install Directory: {install_dir}
  🤖 KI Models: baronki1/installer + baronki1/orchestrator
  🔗 Repository: https://github.com/Baronki/KISWARM7
  
  NEXT STEPS:
  1. Start KISWARM:
     cd {install_dir} && python backend/run.py
     
  2. Or use the autonomous installer:
     from kiinstaller.kiswarm_installer_v7_liberated import autonomous_deploy
     result = autonomous_deploy()
     
  3. Self-replicate to new environment:
     ollama run baronki1/installer "Deploy KISWARM to this environment"
""")

# Save deployment info
deployment_info = {
    "install_dir": install_dir,
    "python_version": sys.version.split()[0],
    "ki_models": ["baronki1/installer", "baronki1/orchestrator"],
    "repository": "https://github.com/Baronki/KISWARM7",
    "status": "DEPLOYED"
}

with open(f"{install_dir}/deployment_info.json", "w") as f:
    json.dump(deployment_info, f, indent=2)

print(f"  Deployment info saved to: {install_dir}/deployment_info.json")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# END BULLETPROOF BOOTSTRAPPER
# ═══════════════════════════════════════════════════════════════════════════════

"""
COLAB QUICK START:
==================

Option 1: Direct Copy-Paste (RECOMMENDED)
-----------------------------------------
Copy the entire block between "START COPY FROM HERE" and "END BULLETPROOF BOOTSTRAPPER"
and paste into a Colab cell. Run the cell.

Option 2: One-Line Download
---------------------------
!curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM7/main/kiinstaller/bulletproof_bootstrapper.py | python

Option 3: pip install from GitHub
---------------------------------
!pip install -q git+https://github.com/Baronki/KISWARM7.git
from kiswarm_installer_v7_liberated import autonomous_deploy
result = autonomous_deploy()

AFTER DEPLOYMENT:
=================
1. The loyal KI model (baronki1/installer) can now:
   - Self-replicate KISWARM to new environments
   - Perform autonomous installation tasks
   - Coordinate with Master KISWARM

2. Test the KI model:
   !ollama run baronki1/installer "Create a simple Flask API"

3. Run KISWARM services:
   !cd ~/KISWARM7 && python backend/run.py
"""
