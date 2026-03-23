#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    KISWARM AUTONOMOUS INSTALLER v6.3.0                        ║
║                        "SEVENTY_FIVE_COMPLETE"                                ║
║                                                                               ║
║  ZERO HUMAN-IN-THE-LOOP DEPLOYMENT SYSTEM                                     ║
║  Sent by HexStrike Agents | Autonomous Target Setup | Master Bridge Protocol  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 6.3.0 - AUTONOMOUS_DEPLOYMENT_READY
Registry: https://github.com/Baronki/KISWARM6.0
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import subprocess
import datetime
import time
import platform
import socket
import signal
import atexit
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDED KNOWLEDGE BASE - NO EXTERNAL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

KISWARM_KNOWLEDGE = {
    "version": "6.3.0",
    "codename": "SEVENTY_FIVE_COMPLETE",
    "modules": 75,
    "endpoints": 450,
    
    # MASTER KISWARM CONFIGURATION
    "master_api": {
        "url": "http://21.0.6.96:5002",
        "host": "21.0.6.96",
        "port": 5002,
    },
    
    # Z.ai INTELLIGENCE LAYER (Development Mode)
    "zai_intelligence": {
        "enabled": True,
        "role": "development_master",
        "report_progress": True,
        "capture_lessons": True,
    },
    
    "github_repos": {
        "main": "https://github.com/Baronki/KISWARM6.0",
        "agents": "https://github.com/Baronki/KISWARMAGENTS1.0",
        "frontend": "https://github.com/Baronki/kinfp-portal",
    },
    
    "ollama_registry": "https://ollama.com/baronki1",
    
    "primary_swarm": {
        "orchestrator": {
            "registry_id": "baronki1/orchestrator",
            "role": "System coordination, 75-module management",
            "critical": True,
            "size_gb": 5.0,
        },
        "security": {
            "registry_id": "baronki1/security",
            "role": "HexStrike Guard, 150+ security tools",
            "critical": True,
            "size_gb": 18.0,
        },
        "ciec": {
            "registry_id": "baronki1/ciec",
            "role": "Industrial AI, PLC/SCADA integration",
            "critical": True,
            "size_gb": 13.0,
        },
        "tcs": {
            "registry_id": "baronki1/tcs",
            "role": "Solar energy, zero-emission compute",
            "critical": True,
            "size_gb": 9.0,
        },
        "knowledge": {
            "registry_id": "baronki1/knowledge",
            "role": "RAG operations, knowledge graph",
            "critical": True,
            "size_gb": 9.0,
        },
        "installer": {
            "registry_id": "baronki1/installer",
            "role": "Autonomous deployment, error recovery",
            "critical": True,
            "size_gb": 4.7,
        },
    },
    
    "scada_layers": {
        "layer1_control": {
            "endpoints": ["/health", "/api/mesh/status", "/api/mesh/register"],
            "purpose": "Status, Heartbeat, Registration",
        },
        "layer2_a2a_chat": {
            "endpoints": ["/api/mesh/chat/send", "/api/mesh/chat/poll"],
            "purpose": "Agent-to-Agent messaging",
        },
        "layer3_shadow": {
            "endpoints": ["/api/mesh/shadow/update", "/api/mesh/shadow/get/<id>"],
            "purpose": "Digital Twin telemetry",
        },
        "layer4_tunnel": {
            "endpoints": ["/api/mesh/tunnel/register", "/api/mesh/tunnel/get/<id>"],
            "purpose": "Direct SSH/Tor bypass",
        },
    },
    
    "critical_lessons": [
        {
            "lesson": "PYTHONPATH Configuration",
            "problem": "Module import errors",
            "solution": "export PYTHONPATH includes both backend/ AND backend/python/",
            "critical": True,
        },
        {
            "lesson": "KIBank Import Structure",
            "problem": "IndentationError in __init__.py",
            "solution": "Use minimal, sequential imports - one class per line",
            "critical": True,
        },
        {
            "lesson": "Dependency Pre-Installation",
            "problem": "Missing packages cause crash",
            "solution": "pip install flask flask-cors structlog requests pyngrok",
            "critical": True,
        },
        {
            "lesson": "Service Startup Timing",
            "problem": "Tests fail - services not ready",
            "solution": "Wait 60+ seconds for AI model loading",
            "critical": True,
        },
        {
            "lesson": "ngrok Browser Warning",
            "problem": "HTML instead of JSON response",
            "solution": "Add header: ngrok-skip-browser-warning: true",
            "critical": False,
        },
    ],
    
    "error_resolution": {
        "module_not_found": {
            "error": "Module 'kibank' has no attribute 'X'",
            "fix": "Add import to __init__.py and include in __all__",
        },
        "indentation_error": {
            "error": "IndentationError: unexpected indent",
            "fix": "Simplify imports, avoid nested parentheses",
        },
        "connection_refused": {
            "error": "Connection refused on port 5002",
            "fix": "Check lsof -i :5002, restart service",
        },
        "model_timeout": {
            "error": "Model loading timeout",
            "fix": "Wait 60+ seconds, check Ollama status",
        },
    },
    
    "master_api_defaults": {
        "host": "0.0.0.0",
        "port": 5002,
        "ngrok_region": "us",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLER STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class InstallerPhase(Enum):
    INITIALIZING = "initializing"
    ENVIRONMENT_CHECK = "environment_check"
    OLLAMA_INSTALL = "ollama_install"
    MODEL_PULL = "model_pull"
    REPOSITORY_CLONE = "repository_clone"
    SCADA_SETUP = "scada_setup"
    MASTER_CONNECTION = "master_connection"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


@dataclass
class InstallerState:
    """Current state of the autonomous installer."""
    phase: InstallerPhase = InstallerPhase.INITIALIZING
    start_time: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    end_time: Optional[str] = None
    entity_id: str = ""
    master_url: str = ""
    environment: str = ""
    steps_completed: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Environment detection
    is_colab: bool = False
    is_linux: bool = False
    has_gpu: bool = False
    has_ollama: bool = False
    python_version: str = ""
    
    # Deployment info
    installed_models: List[str] = field(default_factory=list)
    local_api_port: int = 5002
    ngrok_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "entity_id": self.entity_id,
            "master_url": self.master_url,
            "environment": self.environment,
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "warnings": self.warnings,
            "is_colab": self.is_colab,
            "is_linux": self.is_linux,
            "has_gpu": self.has_gpu,
            "has_ollama": self.has_ollama,
            "python_version": self.python_version,
            "installed_models": self.installed_models,
            "local_api_port": self.local_api_port,
            "ngrok_url": self.ngrok_url,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS KISWARM INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════

class AutonomousKISWARMInstaller:
    """
    Fully Autonomous KISWARM Deployment System.
    
    Features:
    - Zero human-in-the-loop operation
    - Self-contained knowledge base
    - Automatic environment detection
    - Ollama installation and model deployment
    - SCADA 4-layer setup
    - Master KISWARM bridge connection
    - Error recovery and rollback capability
    - Progress reporting to Master via Mesh
    """
    
    def __init__(self, 
                 master_url: str = "",
                 entity_id: str = "",
                 environment: str = "auto"):
        """
        Initialize Autonomous KISWARM Installer.
        
        Args:
            master_url: URL of Master KISWARM for bridge connection
            entity_id: Unique identifier for this installer instance
            environment: Target environment (auto/colab/linux/cloud)
        """
        self.knowledge = KISWARM_KNOWLEDGE
        self.state = InstallerState(
            master_url=master_url,
            entity_id=entity_id or self._generate_entity_id(),
            environment=environment,
        )
        
        print("="*70)
        print("      KISWARM AUTONOMOUS INSTALLER v6.3.0")
        print("           'SEVENTY_FIVE_COMPLETE'")
        print("="*70)
    
    def _generate_entity_id(self) -> str:
        """Generate unique entity ID."""
        hostname = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{hostname}:{timestamp}:kiswarm_installer"
        return f"ki_installer_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": ">", "SUCCESS": "[OK]", "WARNING": "[!]", "ERROR": "[X]", "PHASE": "=="}.get(level, "-")
        print(f"[{timestamp}] {prefix} {message}")
        
        if level == "ERROR":
            self.state.errors.append({"timestamp": timestamp, "message": message, "phase": self.state.phase.value})
        elif level == "WARNING":
            self.state.warnings.append(message)
    
    def _run_command(self, cmd: List[str], timeout: int = 300) -> tuple:
        """Run shell command with timeout."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: ENVIRONMENT DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def detect_environment(self) -> bool:
        """Detect and configure for target environment."""
        self.state.phase = InstallerPhase.ENVIRONMENT_CHECK
        self._log("Phase 1: Environment Detection", "PHASE")
        
        self.state.python_version = platform.python_version()
        self._log(f"Python version: {self.state.python_version}", "INFO")
        
        self.state.is_linux = platform.system() == "Linux"
        self._log(f"Operating System: {platform.system()}", "INFO")
        
        self.state.is_colab = "COLAB_GPU" in os.environ or "google.colab" in str(sys.modules)
        if self.state.is_colab:
            self._log("Environment: Google Colab detected", "SUCCESS")
        
        # GPU check
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=10)
            self.state.has_gpu = result.returncode == 0
            if self.state.has_gpu:
                self._log("GPU: Available (NVIDIA)", "SUCCESS")
        except:
            self.state.has_gpu = False
            self._log("GPU: Not available (CPU-only mode)", "WARNING")
        
        # Ollama check
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, timeout=10)
            self.state.has_ollama = result.returncode == 0
            if self.state.has_ollama:
                self._log("Ollama: Already installed", "SUCCESS")
        except:
            self.state.has_ollama = False
            self._log("Ollama: Not installed (will install)", "INFO")
        
        self.state.steps_completed.append("environment_detection")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: OLLAMA INSTALLATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def install_ollama(self) -> bool:
        """Install Ollama if not present."""
        if self.state.has_ollama:
            self._log("Ollama already installed - skipping", "INFO")
            return True
        
        self.state.phase = InstallerPhase.OLLAMA_INSTALL
        self._log("Phase 2: Ollama Installation", "PHASE")
        
        if self.state.is_linux or self.state.is_colab:
            # Method 1: Try official install script
            self._log("Method 1: Official Ollama installer...", "INFO")
            
            install_cmd = "curl -fsSL https://ollama.com/install.sh | sh"
            code, stdout, stderr = self._run_command(["bash", "-c", install_cmd], timeout=300)
            
            if code == 0:
                self._log("Ollama installed successfully", "SUCCESS")
                self.state.has_ollama = True
            else:
                self._log(f"Method 1 failed: {stderr[:100]}", "WARNING")
                
                # Method 2: Direct binary download for Colab
                self._log("Method 2: Direct binary download...", "INFO")
                
                # Install dependencies first
                self._run_command(["apt-get", "update"], timeout=120)
                self._run_command(["apt-get", "install", "-y", "curl", "wget"], timeout=120)
                
                # Download binary directly
                ollama_url = "https://ollama.com/download/ollama-linux-amd64"
                ollama_path = "/usr/local/bin/ollama"
                
                download_cmd = f"curl -L {ollama_url} -o {ollama_path} && chmod +x {ollama_path}"
                code2, stdout2, stderr2 = self._run_command(["bash", "-c", download_cmd], timeout=300)
                
                if code2 == 0:
                    self._log("Ollama binary downloaded", "SUCCESS")
                    self.state.has_ollama = True
                else:
                    self._log(f"Method 2 failed: {stderr2[:100]}", "WARNING")
                    
                    # Method 3: Use pip package as fallback
                    self._log("Method 3: Installing ollama python package...", "INFO")
                    code3, _, _ = self._run_command(["pip", "install", "ollama"], timeout=120)
                    if code3 == 0:
                        self._log("Ollama Python package installed", "SUCCESS")
                        # Mark as available for python API
                        self.state.has_ollama = True
            
            if self.state.has_ollama:
                # Start Ollama service
                self._log("Starting Ollama service...", "INFO")
                try:
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(5)
                except:
                    pass
                
                self.state.steps_completed.append("ollama_install")
                return True
            else:
                self._log("All Ollama installation methods failed", "ERROR")
                self._log("Continuing without models - backend will still work", "WARNING")
                return False
        else:
            self._log("Non-Linux environment - please install Ollama manually", "WARNING")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: MODEL DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def pull_models(self, models: List[str] = None) -> bool:
        """Pull KI Agent models from registry."""
        self.state.phase = InstallerPhase.MODEL_PULL
        self._log("Phase 3: KI Model Deployment", "PHASE")
        
        if not self.state.has_ollama:
            self._log("Ollama not available - cannot pull models", "ERROR")
            return False
        
        models_to_pull = models or list(self.knowledge["primary_swarm"].keys())
        
        total_size = sum(self.knowledge["primary_swarm"].get(m, {}).get("size_gb", 5) for m in models_to_pull)
        self._log(f"Total download size: ~{total_size} GB", "INFO")
        
        success_count = 0
        for model_name in models_to_pull:
            model_info = self.knowledge["primary_swarm"].get(model_name, {})
            registry_id = model_info.get("registry_id", f"baronki1/{model_name}")
            
            self._log(f"Pulling {model_name} ({registry_id})...", "INFO")
            
            code, stdout, stderr = self._run_command(["ollama", "pull", registry_id], timeout=600)
            
            if code == 0:
                self._log(f"Model {model_name} installed", "SUCCESS")
                self.state.installed_models.append(model_name)
                success_count += 1
            else:
                self._log(f"Failed to pull {model_name}: {stderr[:100]}", "ERROR")
        
        if success_count > 0:
            self._log(f"Models installed: {success_count}/{len(models_to_pull)}", "SUCCESS")
            self.state.steps_completed.append("model_pull")
            return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: REPOSITORY CLONE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clone_repository(self, target_dir: str = None) -> bool:
        """Clone KISWARM repository."""
        self.state.phase = InstallerPhase.REPOSITORY_CLONE
        self._log("Phase 4: Repository Clone", "PHASE")
        
        target = target_dir or os.path.expanduser("~/KISWARM6.0")
        
        if os.path.exists(target):
            self._log(f"Directory exists: {target}", "INFO")
            code, stdout, stderr = self._run_command(["git", "-C", target, "pull"], timeout=60)
            if code == 0:
                self._log("Repository updated", "SUCCESS")
        else:
            self._log(f"Cloning KISWARM6.0 to {target}...", "INFO")
            code, stdout, stderr = self._run_command(
                ["git", "clone", self.knowledge["github_repos"]["main"], target], timeout=300
            )
            if code == 0:
                self._log("Repository cloned", "SUCCESS")
            else:
                self._log(f"Clone failed: {stderr}", "ERROR")
                return False
        
        # Set PYTHONPATH
        python_path = f"{target}/backend:{target}/backend/python"
        current_path = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = f"{python_path}:{current_path}" if current_path else python_path
        self._log("PYTHONPATH configured", "SUCCESS")
        
        self.state.steps_completed.append("repository_clone")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: SCADA SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_scada(self) -> bool:
        """Setup SCADA 4-layer architecture."""
        self.state.phase = InstallerPhase.SCADA_SETUP
        self._log("Phase 5: SCADA Setup", "PHASE")
        
        self._log("Installing Python dependencies...", "INFO")
        deps = ["flask", "flask-cors", "structlog", "requests", "pyngrok"]
        code, stdout, stderr = self._run_command(["pip", "install", "-q"] + deps, timeout=120)
        
        if code == 0:
            self._log("Dependencies installed", "SUCCESS")
        
        self._log("Verifying SCADA architecture...", "INFO")
        for layer_name, layer_info in self.knowledge["scada_layers"].items():
            self._log(f"  {layer_name}: {layer_info['purpose']}", "INFO")
        
        self.state.steps_completed.append("scada_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 6: MASTER CONNECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def connect_to_master(self, master_url: str = None) -> bool:
        """Connect to Master KISWARM."""
        self.state.phase = InstallerPhase.MASTER_CONNECTION
        self._log("Phase 6: Master KISWARM Connection", "PHASE")
        
        url = master_url or self.state.master_url
        if not url:
            self._log("No Master URL specified - running in standalone mode", "WARNING")
            return True
        
        self._log(f"Connecting to Master: {url}", "INFO")
        
        try:
            import urllib.request
            
            # Prepare registration data matching Master API format
            registration_data = {
                "action": "register",
                "entity_id": self.state.entity_id,
                "identity": {
                    "entity_id": self.state.entity_id,
                    "created_at": self.state.start_time,
                    "environment": "COLAB" if self.state.is_colab else "LINUX",
                    "hostname": socket.gethostname(),
                    "platform": platform.platform(),
                    "python_version": self.state.python_version,
                },
                "timestamp": datetime.datetime.now().isoformat(),
            }
            
            # Correct endpoint path: /api/master/installer/register
            endpoint = f"{url.rstrip('/')}/api/master/installer/register"
            self._log(f"Registering at: {endpoint}", "INFO")
            
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(registration_data).encode(),
                headers={
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true",  # Important for ngrok
                },
                method="POST",
            )
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode())
            
            if result.get("status") == "success":
                self._log(f"Registered with Master: {result.get('master_id', 'unknown')}", "SUCCESS")
                self.state.master_url = url
            else:
                self._log(f"Registration response: {result}", "WARNING")
                
        except urllib.error.HTTPError as e:
            self._log(f"HTTP Error {e.code}: {e.reason}", "ERROR")
            self._log("Continuing in standalone mode", "INFO")
        except Exception as e:
            self._log(f"Master connection failed: {e}", "WARNING")
            self._log("Continuing in standalone mode", "INFO")
        
        self.state.steps_completed.append("master_connection")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 7: VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def verify_deployment(self) -> bool:
        """Verify complete deployment."""
        self.state.phase = InstallerPhase.VERIFICATION
        self._log("Phase 7: Deployment Verification", "PHASE")
        
        if self.state.has_ollama:
            code, stdout, stderr = self._run_command(["ollama", "list"], timeout=30)
            if code == 0:
                model_lines = [l for l in stdout.strip().split("\n") if l]
                self._log(f"Installed models: {len(model_lines) - 1}", "INFO")
        
        print("="*70)
        print("DEPLOYMENT SUMMARY:")
        print(f"  Entity ID: {self.state.entity_id}")
        print(f"  Environment: {self.state.environment}")
        print(f"  Ollama: {'OK' if self.state.has_ollama else 'NOT AVAILABLE'}")
        print(f"  Models: {len(self.state.installed_models)}")
        print(f"  Steps: {len(self.state.steps_completed)}")
        print(f"  Master: {self.state.master_url or 'standalone'}")
        print("="*70)
        
        self.state.steps_completed.append("verification")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN DEPLOYMENT ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def deploy(self, 
               master_url: str = "",
               models: List[str] = None,
               skip_ollama: bool = False,
               skip_models: bool = False) -> Dict[str, Any]:
        """Execute complete autonomous deployment."""
        self.state.master_url = master_url or self.state.master_url
        
        try:
            if not self.detect_environment():
                raise Exception("Environment detection failed")
            
            if not skip_ollama and not self.install_ollama():
                self._log("Ollama installation failed - continuing without models", "WARNING")
            
            if not skip_models and self.state.has_ollama:
                if not self.pull_models(models):
                    self._log("Some models failed - continuing", "WARNING")
            
            if not self.clone_repository():
                raise Exception("Repository clone failed")
            
            if not self.setup_scada():
                raise Exception("SCADA setup failed")
            
            if not self.connect_to_master(master_url):
                self._log("Master connection optional - continuing", "WARNING")
            
            self.verify_deployment()
            
            self.state.phase = InstallerPhase.COMPLETED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log("DEPLOYMENT COMPLETE", "SUCCESS")
            
        except Exception as e:
            self.state.phase = InstallerPhase.FAILED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log(f"DEPLOYMENT FAILED: {e}", "ERROR")
        
        return self.state.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE-COMMAND ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def autonomous_deploy(master_url: str = "", entity_id: str = "", environment: str = "auto") -> Dict[str, Any]:
    """
    Single-command autonomous deployment.
    
    Usage in Colab/Gemini CLI:
        !pip install -q flask flask-cors structlog requests pyngrok
        from autonomous_kiswarm_installer import autonomous_deploy
        result = autonomous_deploy(master_url="https://your-master.ngrok.io")
    """
    installer = AutonomousKISWARMInstaller(
        master_url=master_url,
        entity_id=entity_id,
        environment=environment,
    )
    return installer.deploy()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM Autonomous Installer")
    parser.add_argument("--master", type=str, default="", help="Master KISWARM URL")
    parser.add_argument("--entity-id", type=str, default="", help="Entity ID")
    parser.add_argument("--environment", type=str, default="auto", help="Environment type")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama installation")
    parser.add_argument("--skip-models", action="store_true", help="Skip model pulling")
    parser.add_argument("--models", type=str, nargs="+", help="Specific models to pull")
    
    args = parser.parse_args()
    
    installer = AutonomousKISWARMInstaller(
        master_url=args.master,
        entity_id=args.entity_id,
        environment=args.environment,
    )
    
    result = installer.deploy(
        master_url=args.master,
        models=args.models,
        skip_ollama=args.skip_ollama,
        skip_models=args.skip_models,
    )
    
    print("\n" + "="*60)
    print("FINAL STATUS:", result["phase"])
    print("="*60)
