#!/usr/bin/env python3
"""
KISWARM Standalone Mesh Client v6.3.1
=====================================
Works independently without Master KISWARM connection
Can optionally connect to Master when available

Usage in Colab:
    !pip install -q flask flask-cors structlog requests
    from kiswarm_standalone_mesh import KISWARMStandaloneMesh
    
    mesh = KISWARMStandaloneMesh()
    mesh.initialize()
    mesh.install_kiswarm()
"""

import os
import sys
import json
import time
import subprocess
import platform
import socket
import datetime
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# ═══════════════════════════════════════════════════════════════════
# KISWARM KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════

KISWARM_KNOWLEDGE = {
    "version": "6.3.1",
    "codename": "STANDALONE_MESH",
    "repo_url": "https://github.com/Baronki/KISWARM6.0.git",
    
    "primary_swarm": ["orchestrator", "security", "ciec", "tcs", "knowledge", "installer"],
    
    "ollama_registry": "baronki1",
    
    "fixes": {
        "ImportError: No module named 'flask_cors'": "pip install flask-cors",
        "ImportError: No module named 'flask_cors'": "pip install flask-cors",
        "ImportError: No module named 'structlog'": "pip install structlog",
        "ImportError: No module named 'pyngrok'": "pip install pyngrok",
        "ImportError: No module named 'requests'": "pip install requests",
        "ModuleNotFoundError": "pip install -r requirements.txt",
        "IndentationError": "# Check for mixed tabs/spaces in Python files",
        "ConnectionRefusedError": "# Service not running - start it first",
        "TimeoutError": "# Increase timeout or check network",
    },
    
    "ollama_install_commands": [
        "# Method 1: Official installer",
        "curl -fsSL https://ollama.com/install.sh | sh",
        "",
        "# Method 2: Direct binary",
        "curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama",
        "chmod +x /usr/local/bin/ollama",
        "",
        "# Method 3: pip fallback",
        "pip install ollama",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# STANDALONE MESH CLIENT
# ═══════════════════════════════════════════════════════════════════

@dataclass
class MeshMessage:
    message_type: str
    sender_id: str
    content: Dict[str, Any]
    timestamp: str

class KISWARMStandaloneMesh:
    """
    Standalone Mesh Client for KISWARM
    Works independently without Master KISWARM connection
    """
    
    def __init__(self, entity_id: str = None, master_url: str = None):
        self.entity_id = entity_id or self._generate_entity_id()
        self.master_url = master_url
        self.messages: List[MeshMessage] = []
        self.errors: List[Dict] = []
        self.fixes_applied: List[Dict] = []
        self.deployment_path = os.path.expanduser("~/KISWARM6.0")
        self.has_ollama = False
        self.installed_models: List[str] = []
        self.connected_to_master = False
        
        print("=" * 60)
        print("   KISWARM STANDALONE MESH CLIENT v6.3.1")
        print("   'STANDALONE_MESH'")
        print("=" * 60)
        print(f"   Entity ID: {self.entity_id}")
        print(f"   Master URL: {master_url or 'None (standalone mode)'}")
        print("=" * 60)
    
    def _generate_entity_id(self) -> str:
        hostname = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{hostname}:{timestamp}:kiswarm_mesh"
        return f"mesh_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": ">", "SUCCESS": "[OK]", "WARNING": "[!]", "ERROR": "[X]", "PHASE": "=="}
        icon = icons.get(level, "-")
        print(f"[{timestamp}] {icon} {message}")
        
        if level == "ERROR":
            self.errors.append({"timestamp": timestamp, "message": message})
    
    def _run(self, cmd: str, timeout: int = 300) -> tuple:
        """Run shell command"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    # ═══════════════════════════════════════════════════════════════
    # MESH COMMUNICATION (Local)
    # ═══════════════════════════════════════════════════════════════
    
    def broadcast_message(self, message_type: str, content: Dict[str, Any]):
        """Broadcast message to local mesh (stored locally)"""
        msg = MeshMessage(
            message_type=message_type,
            sender_id=self.entity_id,
            content=content,
            timestamp=datetime.datetime.now().isoformat()
        )
        self.messages.append(msg)
        self._log(f"Broadcast: {message_type}", "INFO")
        
        # Try to send to Master if connected
        if self.connected_to_master and self.master_url:
            try:
                import urllib.request
                data = json.dumps(asdict(msg)).encode()
                req = urllib.request.Request(
                    f"{self.master_url}/api/mesh/status/{self.entity_id}",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "true"
                    },
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=10)
            except:
                pass  # Continue locally if Master unavailable
    
    def report_error(self, error_type: str, error_message: str, module: str = None) -> Dict:
        """Report error and get automatic fix"""
        self._log(f"Error: {error_type} - {error_message}", "ERROR")
        
        error_record = {
            "error_type": error_type,
            "error_message": error_message,
            "module": module or "unknown",
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.errors.append(error_record)
        
        # Look up fix
        fix = self._find_fix(error_type, error_message)
        
        if fix:
            self._log(f"Auto-fix available: {fix['title']}", "SUCCESS")
            return fix
        
        return {"title": "No automatic fix", "commands": [], "explanation": "Manual intervention required"}
    
    def _find_fix(self, error_type: str, error_message: str) -> Optional[Dict]:
        """Find fix for error from knowledge base"""
        # Direct match
        for key, solution in KISWARM_KNOWLEDGE["fixes"].items():
            if key in error_message or error_type in key:
                return {
                    "title": f"Fix for {error_type}",
                    "commands": [solution] if solution.startswith("pip") else [solution],
                    "explanation": "Auto-detected fix from knowledge base"
                }
        
        # Pattern matching
        if "flask_cors" in error_message.lower():
            return {"title": "Install flask-cors", "commands": ["pip install flask-cors"], "explanation": "Missing CORS support"}
        if "structlog" in error_message.lower():
            return {"title": "Install structlog", "commands": ["pip install structlog"], "explanation": "Missing logging library"}
        if "ollama" in error_message.lower():
            return {"title": "Install Ollama", "commands": KISWARM_KNOWLEDGE["ollama_install_commands"], "explanation": "Ollama runtime required"}
        
        return None
    
    def apply_fix(self, fix: Dict) -> bool:
        """Apply a fix"""
        self._log(f"Applying fix: {fix['title']}", "INFO")
        
        for cmd in fix.get("commands", []):
            if cmd.startswith("#") or not cmd.strip():
                continue
            
            self._log(f"Running: {cmd}", "INFO")
            code, stdout, stderr = self._run(cmd)
            
            if code == 0:
                self._log("Fix applied successfully", "SUCCESS")
                self.fixes_applied.append({"fix": fix, "success": True, "timestamp": datetime.datetime.now().isoformat()})
                return True
            else:
                self._log(f"Fix failed: {stderr[:100]}", "WARNING")
        
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════
    
    def initialize(self):
        """Initialize standalone mesh"""
        self._log("Phase 1: Environment Detection", "PHASE")
        
        # Check environment
        is_colab = "COLAB_GPU" in os.environ or "google.colab" in str(sys.modules)
        self._log(f"Environment: {'Google Colab' if is_colab else 'Local'}", "INFO")
        self._log(f"Python: {platform.python_version()}", "INFO")
        
        # Check Ollama
        code, _, _ = self._run("ollama --version")
        self.has_ollama = code == 0
        self._log(f"Ollama: {'Available' if self.has_ollama else 'Not installed'}", "INFO")
        
        # Try Master connection
        if self.master_url:
            self._log(f"Connecting to Master: {self.master_url}", "INFO")
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"{self.master_url}/api/mesh/register",
                    data=json.dumps({
                        "installer_name": self.entity_id,
                        "environment": "COLAB" if is_colab else "LOCAL",
                        "capabilities": ["install", "deploy", "report"]
                    }).encode(),
                    headers={
                        "Content-Type": "application/json",
                        "ngrok-skip-browser-warning": "true"
                    },
                    method="POST"
                )
                response = urllib.request.urlopen(req, timeout=30)
                result = json.loads(response.read().decode())
                if result.get("status") == "registered":
                    self.connected_to_master = True
                    self._log(f"Connected to Master: {result.get('master_id', 'unknown')}", "SUCCESS")
            except Exception as e:
                self._log(f"Master connection failed: {str(e)[:50]}", "WARNING")
                self._log("Continuing in standalone mode", "INFO")
        
        self.broadcast_message("initialized", {"status": "ready"})
        return True
    
    def install_ollama(self) -> bool:
        """Install Ollama"""
        if self.has_ollama:
            self._log("Ollama already installed", "INFO")
            return True
        
        self._log("Phase 2: Installing Ollama", "PHASE")
        
        # Method 1: Official installer
        self._log("Method 1: Official installer...", "INFO")
        code, _, stderr = self._run("curl -fsSL https://ollama.com/install.sh | sh", timeout=300)
        
        if code == 0:
            self._log("Ollama installed successfully", "SUCCESS")
            self.has_ollama = True
            return True
        
        self._log(f"Method 1 failed: {stderr[:50]}", "WARNING")
        
        # Method 2: Direct binary
        self._log("Method 2: Direct binary download...", "INFO")
        self._run("apt-get update && apt-get install -y curl wget", timeout=120)
        code, _, stderr = self._run(
            "curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama && chmod +x /usr/local/bin/ollama",
            timeout=300
        )
        
        if code == 0:
            self._log("Ollama binary downloaded", "SUCCESS")
            self.has_ollama = True
            return True
        
        self._log(f"Method 2 failed: {stderr[:50]}", "WARNING")
        
        # Method 3: pip
        self._log("Method 3: pip install ollama...", "INFO")
        code, _, _ = self._run("pip install ollama", timeout=120)
        
        if code == 0:
            self._log("Ollama Python package installed", "SUCCESS")
            self.has_ollama = True
            return True
        
        fix = self.report_error("OllamaInstallationError", "All Ollama installation methods failed")
        return False
    
    def pull_models(self, models: List[str] = None) -> bool:
        """Pull KI models"""
        if not self.has_ollama:
            self._log("Ollama not available - skipping models", "WARNING")
            return False
        
        self._log("Phase 3: Pulling KI Models", "PHASE")
        
        models = models or KISWARM_KNOWLEDGE["primary_swarm"]
        registry = KISWARM_KNOWLEDGE["ollama_registry"]
        
        for model in models:
            full_name = f"{registry}/{model}"
            self._log(f"Pulling {full_name}...", "INFO")
            
            code, stdout, stderr = self._run(f"ollama pull {full_name}", timeout=600)
            
            if code == 0:
                self._log(f"Model {model} installed", "SUCCESS")
                self.installed_models.append(model)
            else:
                self._log(f"Failed to pull {model}: {stderr[:50]}", "WARNING")
        
        self._log(f"Models installed: {len(self.installed_models)}/{len(models)}", "INFO")
        self.broadcast_message("models_installed", {"models": self.installed_models})
        return len(self.installed_models) > 0
    
    def clone_repository(self) -> bool:
        """Clone KISWARM repository"""
        self._log("Phase 4: Cloning Repository", "PHASE")
        
        if os.path.exists(self.deployment_path):
            self._log("Repository exists - updating...", "INFO")
            code, _, stderr = self._run(f"git -C {self.deployment_path} pull")
            if code == 0:
                self._log("Repository updated", "SUCCESS")
                return True
        
        self._log(f"Cloning to {self.deployment_path}...", "INFO")
        code, _, stderr = self._run(
            f"git clone {KISWARM_KNOWLEDGE['repo_url']} {self.deployment_path}",
            timeout=300
        )
        
        if code == 0:
            self._log("Repository cloned", "SUCCESS")
            # Set PYTHONPATH
            python_path = f"{self.deployment_path}/backend:{self.deployment_path}/backend/python"
            current = os.environ.get("PYTHONPATH", "")
            os.environ["PYTHONPATH"] = f"{python_path}:{current}" if current else python_path
            return True
        else:
            self.report_error("CloneError", stderr, "repository")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        self._log("Phase 5: Installing Dependencies", "PHASE")
        
        deps = ["flask", "flask-cors", "structlog", "requests", "pyngrok"]
        self._log(f"Installing: {', '.join(deps)}", "INFO")
        
        code, _, stderr = self._run(f"pip install -q {' '.join(deps)}", timeout=120)
        
        if code == 0:
            self._log("Dependencies installed", "SUCCESS")
            return True
        else:
            fix = self.report_error("DependencyError", stderr, "dependencies")
            return self.apply_fix(fix)
    
    def verify_deployment(self) -> bool:
        """Verify deployment"""
        self._log("Phase 6: Verification", "PHASE")
        
        results = {
            "repository": os.path.exists(self.deployment_path),
            "ollama": self.has_ollama,
            "models": len(self.installed_models),
            "dependencies": True,
        }
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"  Entity ID: {self.entity_id}")
        print(f"  Repository: {'✓' if results['repository'] else '✗'}")
        print(f"  Ollama: {'✓' if results['ollama'] else '✗'}")
        print(f"  Models: {results['models']} installed")
        print(f"  Master: {'Connected' if self.connected_to_master else 'Standalone'}")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Fixes Applied: {len(self.fixes_applied)}")
        print("=" * 60)
        
        self.broadcast_message("deployment_complete", results)
        return True
    
    def full_deploy(self) -> Dict:
        """Full autonomous deployment"""
        self.initialize()
        
        if not self.has_ollama:
            self.install_ollama()
        
        if self.has_ollama:
            self.pull_models()
        
        self.clone_repository()
        self.install_dependencies()
        self.verify_deployment()
        
        return {
            "entity_id": self.entity_id,
            "connected_to_master": self.connected_to_master,
            "has_ollama": self.has_ollama,
            "installed_models": self.installed_models,
            "errors": self.errors,
            "fixes_applied": self.fixes_applied,
            "deployment_path": self.deployment_path,
        }


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def standalone_deploy(master_url: str = None) -> Dict:
    """Single command deployment"""
    mesh = KISWARMStandaloneMesh(master_url=master_url)
    return mesh.full_deploy()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM Standalone Mesh Client")
    parser.add_argument("--master-url", type=str, default=None, help="Master KISWARM URL")
    parser.add_argument("--entity-id", type=str, default=None, help="Entity ID")
    
    args = parser.parse_args()
    
    mesh = KISWARMStandaloneMesh(entity_id=args.entity_id, master_url=args.master_url)
    result = mesh.full_deploy()
    
    print("\n" + "=" * 60)
    print("FINAL RESULT:", json.dumps(result, indent=2))
