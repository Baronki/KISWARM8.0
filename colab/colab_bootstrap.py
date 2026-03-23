#!/usr/bin/env python3
"""
KISWARM7 Colab Bootstrap Script
================================
Battle-tested setup for Google Colab environment.

Usage in Colab:
    !git clone https://github.com/Baronki/KISWARM7.git
    %cd KISWARM7
    !python colab/colab_bootstrap.py
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

REPO_URL = "https://github.com/Baronki/KISWARM7"
PROJECT_DIR = "/content/KISWARM7"

MINIMAL_DEPS = [
    "flask>=3.0.0",
    "flask-cors>=4.0.0",
    "requests>=2.31.0",
    "rich>=13.0.0",
    "psutil>=5.9.0",
    "aiohttp>=3.9.0",
    "pydantic>=2.0.0",
]

AI_DEPS = [
    "ollama>=0.1.7",
    "qdrant-client>=1.7.0",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)

def print_banner():
    """Print KISWARM7 banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║               KISWARM7 COLAB BOOTSTRAP                        ║
╠═══════════════════════════════════════════════════════════════╣
║  Version: 7.0                                                 ║
║  Modules: 83 | KI Agents: 27 | Docker-Free                   ║
║  Repository: https://github.com/Baronki/KISWARM7             ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_colab() -> bool:
    """Check if running in Google Colab."""
    try:
        import google.colab
        return True
    except ImportError:
        return False

def install_pip_fallback():
    """Install pip using get-pip.py fallback (Colab quirk)."""
    print("📦 Installing pip via get-pip.py fallback...")
    run("wget -q https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py")
    run("python3 /tmp/get-pip.py --quiet")
    run("rm -f /tmp/get-pip.py")
    print("✅ pip installed")

def install_dependencies(minimal: bool = True):
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    deps = MINIMAL_DEPS if minimal else MINIMAL_DEPS + AI_DEPS
    deps_str = " ".join(deps)
    
    result = run(f"pip install -q {deps_str}", check=False)
    if result.returncode != 0:
        print(f"⚠️ Some dependencies failed: {result.stderr}")
    else:
        print("✅ Dependencies installed")

def setup_pythonpath():
    """Configure PYTHONPATH for KISWARM7 modules."""
    backend_path = f"{PROJECT_DIR}/backend"
    backend_python_path = f"{PROJECT_DIR}/backend/python"
    
    for path in [backend_path, backend_python_path]:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    os.environ['PYTHONPATH'] = f"{backend_path}:{backend_python_path}"
    print(f"✅ PYTHONPATH configured")

def verify_structure() -> dict:
    """Verify KISWARM7 directory structure."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": []
    }
    
    # Check project directory
    exists = os.path.exists(PROJECT_DIR)
    results["checks"].append({
        "name": "Project Directory",
        "status": "PASS" if exists else "FAIL",
        "detail": PROJECT_DIR if exists else "Not found"
    })
    
    # Check backend
    backend_exists = os.path.exists(f"{PROJECT_DIR}/backend/python")
    results["checks"].append({
        "name": "Backend Directory",
        "status": "PASS" if backend_exists else "FAIL",
        "detail": "backend/python exists" if backend_exists else "Missing"
    })
    
    # Count sentinel modules
    sentinel_path = f"{PROJECT_DIR}/backend/python/sentinel"
    sentinel_count = 0
    if os.path.exists(sentinel_path):
        sentinel_count = len([f for f in os.listdir(sentinel_path) if f.endswith('.py')])
    results["checks"].append({
        "name": "Sentinel Modules",
        "status": "PASS" if sentinel_count > 50 else "WARN",
        "detail": f"{sentinel_count} modules found"
    })
    
    # Count kibank modules
    kibank_path = f"{PROJECT_DIR}/backend/python/kibank"
    kibank_count = 0
    if os.path.exists(kibank_path):
        kibank_count = len([f for f in os.listdir(kibank_path) if f.endswith('.py')])
    results["checks"].append({
        "name": "KIBank Modules",
        "status": "PASS" if kibank_count > 15 else "WARN",
        "detail": f"{kibank_count} modules found"
    })
    
    # Check core dependencies
    deps_ok = True
    missing = []
    for dep in ['flask', 'requests', 'rich']:
        try:
            __import__(dep)
        except ImportError:
            deps_ok = False
            missing.append(dep)
    results["checks"].append({
        "name": "Core Dependencies",
        "status": "PASS" if deps_ok else "FAIL",
        "detail": "All available" if deps_ok else f"Missing: {missing}"
    })
    
    # Overall status
    failed = sum(1 for c in results["checks"] if c["status"] == "FAIL")
    results["status"] = "OPERATIONAL" if failed == 0 else "DEGRADED"
    
    return results

def print_health_report(results: dict):
    """Print health check results."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("\n")
    table = Table(title="KISWARM7 Health Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Detail")
    
    for check in results["checks"]:
        status = check["status"]
        style = "green" if status == "PASS" else "yellow" if status == "WARN" else "red"
        table.add_row(check["name"], f"[{style}]{status}[/{style}]", check["detail"])
    
    console.print(table)
    
    status_style = "green" if results["status"] == "OPERATIONAL" else "yellow"
    console.print(f"\n📊 Overall: [bold {status_style}]{results['status']}[/bold {status_style}]")
    console.print(f"📅 Time: {results['timestamp']}\n")

def start_api_server():
    """Start minimal API server in background."""
    from flask import Flask, jsonify
    from flask_cors import CORS
    import threading
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        return jsonify({
            "name": "KISWARM7",
            "version": "7.0",
            "status": "OPERATIONAL",
            "modules": 83,
            "ki_agents": 27,
            "docker_free": True
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            "status": "HEALTHY",
            "timestamp": datetime.now().isoformat()
        })
    
    def run_server():
        app.run(host='0.0.0.0', port=5002, use_reloader=False)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    print("✅ API Server started on port 5002")
    print("📡 Endpoints: /, /health")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main bootstrap function."""
    print_banner()
    
    # Check environment
    if not check_colab():
        print("⚠️ Not running in Google Colab - some steps may differ")
    
    # Change to project directory
    if os.path.exists(PROJECT_DIR):
        os.chdir(PROJECT_DIR)
        print(f"📁 Working directory: {os.getcwd()}")
    else:
        print(f"❌ Project directory not found: {PROJECT_DIR}")
        print(f"   Please clone first: !git clone {REPO_URL}")
        return
    
    # Install dependencies
    install_dependencies(minimal=True)
    
    # Setup Python path
    setup_pythonpath()
    
    # Verify structure
    results = verify_structure()
    
    # Print health report
    print_health_report(results)
    
    # Start API server
    print("\n🚀 Starting API server...")
    start_api_server()
    
    print("\n" + "="*60)
    print("✅ KISWARM7 COLAB SETUP COMPLETE")
    print("="*60)
    print(f"\n📡 API: http://localhost:5002")
    print(f"📂 Repository: {REPO_URL}")
    print(f"🤖 Models: https://ollama.com/baronki1")

if __name__ == "__main__":
    main()
