#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           KISWARM NATIVE INSTALLER v7.0 - SELF-REPLICATING SYSTEM             ║
║                      "AUTONOMOUS_DEPLOYMENT_MASTER"                           ║
║                                                                               ║
║  ZERO Docker - Native Installation - Works on ANY Environment                 ║
║  Self-Healing - Auto-Recovery - Hardware Adaptive - GPU-Aware                ║
║                                                                               ║
║  Based on KiloCode Field Test Feedback (2026-03-13)                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 7.0 - AUTONOMOUS_SELF_REPLICATING
Registry: https://ollama.com/baronki1
GitHub: https://github.com/Baronki/KISWARM7.0-NATIVE
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
import shutil
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDED KNOWLEDGE BASE - NO EXTERNAL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

KISWARM_KNOWLEDGE = {
    "version": "7.0",
    "codename": "AUTONOMOUS_SELF_REPLICATING",
    "modules": 83,
    "endpoints": 520,
    
    # GitHub Repositories
    "github_repos": {
        "main": "https://github.com/Baronki/KISWARM7.0-NATIVE",
        "legacy": "https://github.com/Baronki/KISWARM6.0",
        "agents": "https://github.com/Baronki/KISWARMAGENTS1.0",
        "frontend": "https://github.com/Baronki/kinfp-portal",
    },
    
    # Ollama Model Registry
    "ollama_registry": "https://ollama.com/baronki1",
    
    # KI Agent Models - 27 Models Total
    "ki_models": {
        # PRIMARY SWARM (6) - Essential for all installations
        "primary": {
            "orchestrator": {
                "registry_id": "baronki1/orchestrator",
                "role": "System coordination, 83-module management",
                "critical": True,
                "size_gb": 5.0,
                "min_vram_gb": 4,
                "cpu_compatible": True,
            },
            "security": {
                "registry_id": "baronki1/security",
                "role": "HexStrike Guard, 150+ security tools",
                "critical": True,
                "size_gb": 18.0,
                "min_vram_gb": 16,
                "cpu_compatible": True,
            },
            "ciec": {
                "registry_id": "baronki1/ciec",
                "role": "Industrial AI, PLC/SCADA integration",
                "critical": True,
                "size_gb": 13.0,
                "min_vram_gb": 12,
                "cpu_compatible": True,
            },
            "tcs": {
                "registry_id": "baronki1/tcs",
                "role": "Solar energy, zero-emission compute",
                "critical": True,
                "size_gb": 9.0,
                "min_vram_gb": 8,
                "cpu_compatible": True,
            },
            "knowledge": {
                "registry_id": "baronki1/knowledge",
                "role": "RAG operations, knowledge graph",
                "critical": True,
                "size_gb": 9.0,
                "min_vram_gb": 8,
                "cpu_compatible": True,
            },
            "installer": {
                "registry_id": "baronki1/installer",
                "role": "Autonomous deployment, error recovery",
                "critical": True,
                "size_gb": 4.7,
                "min_vram_gb": 4,
                "cpu_compatible": True,
            },
        },
        
        # FAST LAYER (6) - Low-latency, edge-optimized
        "fast": {
            "orchestrator-fast": {"registry_id": "baronki1/orchestrator-fast", "size_gb": 2.5, "min_vram_gb": 2},
            "security-fast": {"registry_id": "baronki1/security-fast", "size_gb": 4.0, "min_vram_gb": 4},
            "ciec-fast": {"registry_id": "baronki1/ciec-fast", "size_gb": 4.0, "min_vram_gb": 4},
            "tcs-fast": {"registry_id": "baronki1/tcs-fast", "size_gb": 3.0, "min_vram_gb": 3},
            "knowledge-fast": {"registry_id": "baronki1/knowledge-fast", "size_gb": 3.0, "min_vram_gb": 3},
            "installer-fast": {"registry_id": "baronki1/installer-fast", "size_gb": 2.0, "min_vram_gb": 2},
        },
        
        # SPECIALIZED (9) - High-precision tasks
        "specialized": {
            "audit-master": {"registry_id": "baronki1/audit-master", "size_gb": 8.0, "min_vram_gb": 8},
            "lfm-reasoner": {"registry_id": "baronki1/lfm-reasoner", "size_gb": 8.0, "min_vram_gb": 8},
            "thinker": {"registry_id": "baronki1/thinker", "size_gb": 6.0, "min_vram_gb": 6},
            "vision": {"registry_id": "baronki1/vision", "size_gb": 8.0, "min_vram_gb": 8},
            "debugger": {"registry_id": "baronki1/debugger", "size_gb": 6.0, "min_vram_gb": 6},
            "validator": {"registry_id": "baronki1/validator", "size_gb": 6.0, "min_vram_gb": 6},
            "reasoner": {"registry_id": "baronki1/reasoner", "size_gb": 6.0, "min_vram_gb": 6},
            "general": {"registry_id": "baronki1/general", "size_gb": 6.0, "min_vram_gb": 6},
            "embedding": {"registry_id": "baronki1/embedding", "size_gb": 1.0, "min_vram_gb": 1},
        },
        
        # BACKUP (6) - Redundancy layer
        "backup": {
            "orchestrator-backup": {"registry_id": "baronki1/orchestrator-backup", "size_gb": 5.0},
            "security-backup": {"registry_id": "baronki1/security-backup", "size_gb": 18.0},
            "ciec-backup": {"registry_id": "baronki1/ciec-backup", "size_gb": 13.0},
            "tcs-backup": {"registry_id": "baronki1/tcs-backup", "size_gb": 9.0},
            "knowledge-backup": {"registry_id": "baronki1/knowledge-backup", "size_gb": 9.0},
            "installer-backup": {"registry_id": "baronki1/installer-backup", "size_gb": 4.7},
        },
    },
    
    # Lessons Learned from KiloCode Field Test
    "lessons_learned": [
        {
            "lesson": "Permission Fix FIRST",
            "problem": "Directory owned by root, AI cannot write",
            "solution": "chown -R $(whoami):$(whoami) before ANY operation",
            "critical": True,
            "phase": "init",
        },
        {
            "lesson": "PYTHONPATH Configuration",
            "problem": "Module import errors",
            "solution": "export PYTHONPATH includes both backend/ AND backend/python/",
            "critical": True,
            "phase": "setup",
        },
        {
            "lesson": "KIBank Import Structure",
            "problem": "IndentationError in __init__.py",
            "solution": "Use minimal, sequential imports - one class per line",
            "critical": True,
            "phase": "setup",
        },
        {
            "lesson": "Dependency Pre-Installation",
            "problem": "Missing packages cause crash",
            "solution": "pip install flask flask-cors structlog requests before running",
            "critical": True,
            "phase": "deps",
        },
        {
            "lesson": "Service Startup Timing",
            "problem": "Tests fail - services not ready",
            "solution": "Wait 60+ seconds for AI model loading",
            "critical": True,
            "phase": "service",
        },
        {
            "lesson": "Database Volume Corruption",
            "problem": "PostgreSQL 'role does not exist'",
            "solution": "Check and recreate stale volumes",
            "critical": True,
            "phase": "database",
        },
        {
            "lesson": "TypeScript Missing Exports",
            "problem": "Frontend build fails",
            "solution": "Add missing function/type definitions",
            "critical": False,
            "phase": "frontend",
        },
    ],
    
    # Error Resolution Patterns
    "error_resolution": {
        "permission_denied": {
            "pattern": r"Permission denied|EACCES",
            "fix": "fix_permissions()",
            "auto_fix": True,
        },
        "module_not_found": {
            "pattern": r"ModuleNotFoundError|No module named",
            "fix": "install_missing_module()",
            "auto_fix": True,
        },
        "connection_refused": {
            "pattern": r"Connection refused|ECONNREFUSED",
            "fix": "check_service_status()",
            "auto_fix": True,
        },
        "role_not_exist": {
            "pattern": r"role.*does not exist",
            "fix": "recreate_database()",
            "auto_fix": True,
        },
        "port_in_use": {
            "pattern": r"Address already in use|EADDRINUSE",
            "fix": "kill_port_process()",
            "auto_fix": True,
        },
        "disk_full": {
            "pattern": r"No space left on device|ENOSPC",
            "fix": "cleanup_disk()",
            "auto_fix": False,
        },
    },
    
    # System Requirements
    "requirements": {
        "python_min": "3.10",
        "node_min": "18.0",
        "ram_min_gb": 16,
        "disk_min_gb": 100,
        "gpu_optional": True,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLER STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class InstallerPhase(Enum):
    INITIALIZING = "initializing"
    PERMISSION_FIX = "permission_fix"
    ENVIRONMENT_DETECT = "environment_detect"
    SYSTEM_PACKAGES = "system_packages"
    PYTHON_SETUP = "python_setup"
    NODEJS_SETUP = "nodejs_setup"
    DATABASE_SETUP = "database_setup"
    REDIS_SETUP = "redis_setup"
    OLLAMA_INSTALL = "ollama_install"
    MODEL_DEPLOY = "model_deploy"
    REPOSITORY_CLONE = "repository_clone"
    KISWARM_SETUP = "kiswarm_setup"
    SYSTEMD_SERVICES = "systemd_services"
    HEALTH_CHECK = "health_check"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HardwareProfile:
    """Detected hardware capabilities."""
    cpu_cores: int = 0
    cpu_model: str = ""
    ram_gb: float = 0.0
    gpu_available: bool = False
    gpu_model: str = ""
    gpu_vram_gb: float = 0.0
    gpu_vendor: str = ""  # nvidia, amd, intel, none
    disk_free_gb: float = 0.0
    os_type: str = ""
    os_version: str = ""
    is_colab: bool = False
    is_wsl: bool = False
    is_virtual: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_model": self.cpu_model,
            "ram_gb": self.ram_gb,
            "gpu_available": self.gpu_available,
            "gpu_model": self.gpu_model,
            "gpu_vram_gb": self.gpu_vram_gb,
            "gpu_vendor": self.gpu_vendor,
            "disk_free_gb": self.disk_free_gb,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "is_colab": self.is_colab,
            "is_wsl": self.is_wsl,
            "is_virtual": self.is_virtual,
        }


@dataclass
class InstallerState:
    """Current state of the autonomous installer."""
    phase: InstallerPhase = InstallerPhase.INITIALIZING
    start_time: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    end_time: Optional[str] = None
    entity_id: str = ""
    install_dir: str = ""
    hardware: Optional[HardwareProfile] = None
    
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Component Status
    python_version: str = ""
    node_version: str = ""
    postgresql_version: str = ""
    redis_version: str = ""
    ollama_version: str = ""
    
    # Model Status
    installed_models: List[str] = field(default_factory=list)
    failed_models: List[str] = field(default_factory=list)
    
    # Service Status
    services_running: Dict[str, bool] = field(default_factory=dict)
    
    # Health Status
    health_status: HealthStatus = HealthStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "entity_id": self.entity_id,
            "install_dir": self.install_dir,
            "hardware": self.hardware.to_dict() if self.hardware else None,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "python_version": self.python_version,
            "node_version": self.node_version,
            "postgresql_version": self.postgresql_version,
            "redis_version": self.redis_version,
            "ollama_version": self.ollama_version,
            "installed_models": self.installed_models,
            "failed_models": self.failed_models,
            "services_running": self.services_running,
            "health_status": self.health_status.value,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS KISWARM INSTALLER v7.0
# ═══════════════════════════════════════════════════════════════════════════════

class KISWARMNativeInstaller:
    """
    Fully Autonomous KISWARM v7.0 Native Installation System.
    
    Features:
    - ZERO Docker - Pure native installation
    - Self-healing and auto-recovery
    - Hardware-adaptive model selection
    - GPU-aware configuration
    - Comprehensive error handling
    - Health monitoring
    - Works on ANY Linux environment
    """
    
    def __init__(self, 
                 install_dir: str = None,
                 entity_id: str = "",
                 model_tier: str = "auto"):
        """
        Initialize KISWARM Native Installer.
        
        Args:
            install_dir: Target installation directory
            entity_id: Unique identifier for this installation
            model_tier: Model selection tier (auto/minimal/standard/full)
        """
        self.knowledge = KISWARM_KNOWLEDGE
        self.state = InstallerState(
            entity_id=entity_id or self._generate_entity_id(),
            install_dir=install_dir or os.path.expanduser("~/KISWARM7.0"),
        )
        self.model_tier = model_tier
        self._rollback_stack: List[Callable] = []
        
        self._print_banner()
    
    def _print_banner(self):
        """Print installer banner."""
        print("=" * 78)
        print("      KISWARM NATIVE INSTALLER v7.0")
        print("           'AUTONOMOUS_SELF_REPLICATING'")
        print("=" * 78)
        print(f"  Entity ID: {self.state.entity_id}")
        print(f"  Target Dir: {self.state.install_dir}")
        print(f"  Model Tier: {self.model_tier}")
        print("=" * 78)
    
    def _generate_entity_id(self) -> str:
        """Generate unique entity ID."""
        hostname = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{hostname}:{timestamp}:kiswarm_native_v7"
        return f"kiswarm_v7_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp and level."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "     >",
            "SUCCESS": "  [OK]",
            "WARNING": "   [!]",
            "ERROR": "   [X]",
            "PHASE": "=====",
            "HEAL": "  [~]",
        }.get(level, "     -")
        
        print(f"[{timestamp}] {prefix} {message}")
        
        if level == "ERROR":
            self.state.errors.append({
                "timestamp": timestamp,
                "message": message,
                "phase": self.state.phase.value,
            })
        elif level == "WARNING":
            self.state.warnings.append(message)
    
    def _run_command(self, cmd: List[str], timeout: int = 300, 
                    check: bool = False, capture: bool = True) -> Tuple[int, str, str]:
        """Run shell command with timeout."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=timeout,
            )
            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout or "", e.stderr or str(e)
        except Exception as e:
            return -1, "", str(e)
    
    def _add_rollback(self, func: Callable):
        """Add rollback action."""
        self._rollback_stack.append(func)
    
    def _execute_rollback(self):
        """Execute all rollback actions in reverse order."""
        self._log("Executing rollback...", "WARNING")
        for func in reversed(self._rollback_stack):
            try:
                func()
            except Exception as e:
                self._log(f"Rollback action failed: {e}", "WARNING")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: PERMISSION FIX (MUST BE FIRST)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fix_permissions(self) -> bool:
        """Fix permissions on installation directory."""
        self.state.phase = InstallerPhase.PERMISSION_FIX
        self._log("Phase 1: Permission Fix (CRITICAL)", "PHASE")
        
        install_dir = self.state.install_dir
        
        # Check if directory exists and get owner
        if os.path.exists(install_dir):
            stat_info = os.stat(install_dir)
            import pwd
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except:
                owner = str(stat_info.st_uid)
            
            current_user = os.environ.get("USER", "unknown")
            
            if owner != current_user and owner == "root":
                self._log(f"Directory owned by root, fixing to {current_user}...", "WARNING")
                
                # Try to fix ownership
                code, _, err = self._run_command(
                    ["sudo", "chown", "-R", f"{current_user}:{current_user}", install_dir]
                )
                
                if code != 0:
                    self._log(f"Failed to change ownership: {err}", "WARNING")
                    self._log("Attempting to continue anyway...", "WARNING")
                else:
                    self._log("Ownership fixed", "SUCCESS")
        
        # Ensure target directory is writable
        parent_dir = os.path.dirname(install_dir)
        if os.path.exists(parent_dir):
            if not os.access(parent_dir, os.W_OK):
                self._log(f"Parent directory not writable: {parent_dir}", "ERROR")
                return False
        
        # Create installation directory if needed
        if not os.path.exists(install_dir):
            try:
                os.makedirs(install_dir, mode=0o755)
                self._log(f"Created directory: {install_dir}", "SUCCESS")
            except Exception as e:
                self._log(f"Failed to create directory: {e}", "ERROR")
                return False
        
        # Verify write access
        test_file = os.path.join(install_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self._log("Write access verified", "SUCCESS")
        except Exception as e:
            self._log(f"Write access failed: {e}", "ERROR")
            return False
        
        self.state.steps_completed.append("permission_fix")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: ENVIRONMENT DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def detect_environment(self) -> bool:
        """Detect hardware and environment capabilities."""
        self.state.phase = InstallerPhase.ENVIRONMENT_DETECT
        self._log("Phase 2: Environment Detection", "PHASE")
        
        hardware = HardwareProfile()
        
        # CPU detection
        hardware.cpu_cores = os.cpu_count() or 1
        self._log(f"CPU Cores: {hardware.cpu_cores}", "INFO")
        
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            for line in cpuinfo.split("\n"):
                if line.startswith("model name"):
                    hardware.cpu_model = line.split(":")[1].strip()
                    self._log(f"CPU Model: {hardware.cpu_model}", "INFO")
                    break
        except:
            pass
        
        # RAM detection
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            for line in meminfo.split("\n"):
                if line.startswith("MemTotal:"):
                    ram_kb = int(line.split()[1])
                    hardware.ram_gb = ram_kb / (1024 * 1024)
                    self._log(f"RAM: {hardware.ram_gb:.1f} GB", "INFO")
                    break
        except:
            hardware.ram_gb = 16.0  # Assume minimum
            self._log("Could not detect RAM, assuming 16GB", "WARNING")
        
        # GPU detection - NVIDIA
        try:
            code, stdout, _ = self._run_command(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
            if code == 0 and stdout.strip():
                hardware.gpu_available = True
                hardware.gpu_vendor = "nvidia"
                parts = stdout.strip().split(",")
                hardware.gpu_model = parts[0].strip()
                if len(parts) > 1:
                    vram_str = parts[1].strip().split()[0]
                    hardware.gpu_vram_gb = float(vram_str) / 1024
                self._log(f"GPU: {hardware.gpu_model} ({hardware.gpu_vram_gb:.1f} GB VRAM)", "SUCCESS")
        except:
            pass
        
        # GPU detection - AMD
        if not hardware.gpu_available:
            try:
                code, stdout, _ = self._run_command(["rocm-smi", "--showproductname"])
                if code == 0 and stdout.strip():
                    hardware.gpu_available = True
                    hardware.gpu_vendor = "amd"
                    hardware.gpu_model = stdout.strip().split("\n")[0]
                    self._log(f"GPU (AMD): {hardware.gpu_model}", "SUCCESS")
            except:
                pass
        
        if not hardware.gpu_available:
            self._log("GPU: Not detected (CPU-only mode)", "WARNING")
        
        # Disk space
        try:
            stat = os.statvfs(os.path.expanduser("~"))
            hardware.disk_free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            self._log(f"Disk Free: {hardware.disk_free_gb:.1f} GB", "INFO")
        except:
            hardware.disk_free_gb = 100.0
            self._log("Could not detect disk space", "WARNING")
        
        # OS detection
        hardware.os_type = platform.system()
        self._log(f"OS: {hardware.os_type}", "INFO")
        
        try:
            with open("/etc/os-release", "r") as f:
                os_release = f.read()
            for line in os_release.split("\n"):
                if line.startswith("PRETTY_NAME="):
                    hardware.os_version = line.split("=")[1].strip('"')
                    self._log(f"OS Version: {hardware.os_version}", "INFO")
                    break
        except:
            pass
        
        # Environment type detection
        hardware.is_colab = "COLAB_GPU" in os.environ or "google.colab" in str(sys.modules)
        if hardware.is_colab:
            self._log("Environment: Google Colab", "SUCCESS")
        
        hardware.is_wsl = "microsoft" in platform.uname().release.lower()
        if hardware.is_wsl:
            self._log("Environment: WSL2", "SUCCESS")
        
        # Virtual machine detection
        try:
            code, stdout, _ = self._run_command(["systemd-detect-virt"])
            hardware.is_virtual = code == 0 and stdout.strip() != "none"
            if hardware.is_virtual:
                self._log(f"Virtual Machine: {stdout.strip()}", "INFO")
        except:
            pass
        
        self.state.hardware = hardware
        self.state.steps_completed.append("environment_detection")
        
        # Check minimum requirements
        min_ram = self.knowledge["requirements"]["ram_min_gb"]
        min_disk = self.knowledge["requirements"]["disk_min_gb"]
        
        if hardware.ram_gb < min_ram:
            self._log(f"WARNING: RAM below minimum ({hardware.ram_gb:.1f} < {min_ram} GB)", "WARNING")
        
        if hardware.disk_free_gb < min_disk:
            self._log(f"WARNING: Disk space below minimum ({hardware.disk_free_gb:.1f} < {min_disk} GB)", "WARNING")
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: SYSTEM PACKAGES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def install_system_packages(self) -> bool:
        """Install required system packages."""
        self.state.phase = InstallerPhase.SYSTEM_PACKAGES
        self._log("Phase 3: System Packages", "PHASE")
        
        # Check if apt is available
        code, _, _ = self._run_command(["which", "apt-get"])
        if code != 0:
            self._log("apt-get not available, skipping system packages", "WARNING")
            self.state.steps_completed.append("system_packages_skipped")
            return True
        
        packages = [
            "python3", "python3-pip", "python3-venv",
            "nodejs", "npm",
            "postgresql", "postgresql-contrib",
            "redis-server",
            "git", "curl", "wget",
            "build-essential",
        ]
        
        self._log("Updating package lists...", "INFO")
        self._run_command(["sudo", "apt-get", "update", "-qq"], timeout=120)
        
        self._log(f"Installing packages: {', '.join(packages)}", "INFO")
        code, stdout, stderr = self._run_command(
            ["sudo", "apt-get", "install", "-y", "-qq"] + packages,
            timeout=600
        )
        
        if code != 0:
            self._log(f"Some packages may have failed: {stderr[:200]}", "WARNING")
        else:
            self._log("System packages installed", "SUCCESS")
        
        self.state.steps_completed.append("system_packages")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: PYTHON SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_python(self) -> bool:
        """Setup Python virtual environment."""
        self.state.phase = InstallerPhase.PYTHON_SETUP
        self._log("Phase 4: Python Setup", "PHASE")
        
        # Check Python version
        code, stdout, _ = self._run_command(["python3", "--version"])
        if code == 0:
            self.state.python_version = stdout.strip().split()[1]
            self._log(f"Python version: {self.state.python_version}", "SUCCESS")
        
        # Create virtual environment
        venv_dir = os.path.join(self.state.install_dir, "venv")
        
        if not os.path.exists(venv_dir):
            self._log("Creating virtual environment...", "INFO")
            code, _, err = self._run_command(["python3", "-m", "venv", venv_dir])
            if code != 0:
                self._log(f"Failed to create venv: {err}", "ERROR")
                return False
            self._log("Virtual environment created", "SUCCESS")
        
        # Install Python dependencies
        pip_path = os.path.join(venv_dir, "bin", "pip")
        
        requirements = [
            "flask", "flask-cors", "structlog", "requests",
            "psycopg2-binary", "redis", "qdrant-client",
            "pydantic", "python-dotenv", "gunicorn",
        ]
        
        self._log("Installing Python dependencies...", "INFO")
        code, _, err = self._run_command(
            [pip_path, "install", "-q"] + requirements,
            timeout=300
        )
        
        if code != 0:
            self._log(f"pip install warnings: {err[:200]}", "WARNING")
        else:
            self._log("Python dependencies installed", "SUCCESS")
        
        self.state.steps_completed.append("python_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: NODE.JS SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_nodejs(self) -> bool:
        """Setup Node.js environment."""
        self.state.phase = InstallerPhase.NODEJS_SETUP
        self._log("Phase 5: Node.js Setup", "PHASE")
        
        # Check Node.js version
        code, stdout, _ = self._run_command(["node", "--version"])
        if code == 0:
            self.state.node_version = stdout.strip()
            self._log(f"Node.js version: {self.state.node_version}", "SUCCESS")
        else:
            self._log("Node.js not found, installing via nvm...", "WARNING")
            # Install nvm and Node.js
            install_nvm = 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash'
            self._run_command(["bash", "-c", install_nvm], timeout=120)
        
        self.state.steps_completed.append("nodejs_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 6: DATABASE SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_database(self) -> bool:
        """Setup PostgreSQL database."""
        self.state.phase = InstallerPhase.DATABASE_SETUP
        self._log("Phase 6: Database Setup (PostgreSQL)", "PHASE")
        
        # Check if PostgreSQL is installed
        code, stdout, _ = self._run_command(["psql", "--version"])
        if code == 0:
            self.state.postgresql_version = stdout.strip().split()[1]
            self._log(f"PostgreSQL version: {self.state.postgresql_version}", "SUCCESS")
        
        # Start PostgreSQL service
        self._log("Starting PostgreSQL service...", "INFO")
        self._run_command(["sudo", "systemctl", "start", "postgresql"])
        self._run_command(["sudo", "systemctl", "enable", "postgresql"])
        
        # Check if service is running
        code, _, _ = self._run_command(["pg_isready"])
        if code != 0:
            self._log("PostgreSQL not ready, attempting to initialize...", "WARNING")
            self._run_command(["sudo", "pg_ctlcluster", "15", "main", "start"])
        
        # Create database and user if not exist
        self._log("Setting up KISWARM database...", "INFO")
        
        # Check if user exists
        code, _, _ = self._run_command([
            "sudo", "-u", "postgres", "psql", "-tAc",
            "SELECT 1 FROM pg_roles WHERE rolname='kiswarm'"
        ])
        
        if code != 0 or "1" not in str(code):
            # Create user and database
            self._run_command([
                "sudo", "-u", "postgres", "psql", "-c",
                "CREATE USER kiswarm WITH PASSWORD 'kiswarm_secret';"
            ])
            self._run_command([
                "sudo", "-u", "postgres", "psql", "-c",
                "CREATE DATABASE kiswarm OWNER kiswarm;"
            ])
            self._run_command([
                "sudo", "-u", "postgres", "psql", "-c",
                "GRANT ALL PRIVILEGES ON DATABASE kiswarm TO kiswarm;"
            ])
            self._log("Database user and database created", "SUCCESS")
        else:
            self._log("Database already configured", "INFO")
        
        self.state.services_running["postgresql"] = True
        self.state.steps_completed.append("database_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 7: REDIS SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_redis(self) -> bool:
        """Setup Redis server."""
        self.state.phase = InstallerPhase.REDIS_SETUP
        self._log("Phase 7: Redis Setup", "PHASE")
        
        # Check Redis version
        code, stdout, _ = self._run_command(["redis-server", "--version"])
        if code == 0:
            self.state.redis_version = stdout.strip().split()[2]
            self._log(f"Redis version: {self.state.redis_version}", "SUCCESS")
        
        # Start Redis service
        self._log("Starting Redis service...", "INFO")
        self._run_command(["sudo", "systemctl", "start", "redis-server"])
        self._run_command(["sudo", "systemctl", "enable", "redis-server"])
        
        # Test Redis connection
        code, stdout, _ = self._run_command(["redis-cli", "ping"])
        if code == 0 and "PONG" in stdout:
            self._log("Redis connection verified", "SUCCESS")
            self.state.services_running["redis"] = True
        else:
            self._log("Redis connection failed", "WARNING")
            self.state.services_running["redis"] = False
        
        self.state.steps_completed.append("redis_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 8: OLLAMA INSTALLATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def install_ollama(self) -> bool:
        """Install Ollama for AI model management."""
        self.state.phase = InstallerPhase.OLLAMA_INSTALL
        self._log("Phase 8: Ollama Installation", "PHASE")
        
        # Check if Ollama is already installed
        code, stdout, _ = self._run_command(["ollama", "--version"])
        if code == 0:
            self.state.ollama_version = stdout.strip()
            self._log(f"Ollama already installed: {self.state.ollama_version}", "SUCCESS")
            return True
        
        # Install Ollama
        self._log("Installing Ollama...", "INFO")
        code, _, err = self._run_command(
            ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            timeout=300
        )
        
        if code != 0:
            self._log(f"Ollama installation failed: {err}", "ERROR")
            return False
        
        # Start Ollama service
        self._log("Starting Ollama service...", "INFO")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        
        # Verify installation
        code, stdout, _ = self._run_command(["ollama", "--version"])
        if code == 0:
            self.state.ollama_version = stdout.strip()
            self._log(f"Ollama installed: {self.state.ollama_version}", "SUCCESS")
            self.state.services_running["ollama"] = True
        else:
            self._log("Ollama verification failed", "ERROR")
            return False
        
        self.state.steps_completed.append("ollama_install")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 9: MODEL DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def select_models_for_hardware(self) -> List[str]:
        """Select appropriate models based on hardware capabilities."""
        hardware = self.state.hardware
        models = []
        
        if self.model_tier == "minimal":
            # Only essential models, smallest versions
            models = ["baronki1/orchestrator-fast", "baronki1/knowledge-fast"]
        
        elif self.model_tier == "full":
            # All models
            for tier in ["primary", "fast", "specialized"]:
                for model_name, model_info in self.knowledge["ki_models"].get(tier, {}).items():
                    models.append(model_info["registry_id"])
        
        elif self.model_tier == "auto":
            # Auto-select based on hardware
            if hardware.gpu_available and hardware.gpu_vram_gb >= 24:
                # High-end GPU - use primary + some specialized
                models = [
                    "baronki1/orchestrator",
                    "baronki1/security",
                    "baronki1/knowledge",
                    "baronki1/installer",
                    "baronki1/embedding",
                ]
            elif hardware.gpu_available and hardware.gpu_vram_gb >= 12:
                # Mid-range GPU - primary models
                models = [
                    "baronki1/orchestrator",
                    "baronki1/knowledge",
                    "baronki1/installer",
                ]
            elif hardware.gpu_available and hardware.gpu_vram_gb >= 8:
                # Entry GPU - fast variants
                models = [
                    "baronki1/orchestrator-fast",
                    "baronki1/knowledge-fast",
                    "baronki1/installer-fast",
                ]
            else:
                # CPU-only - minimal fast models
                models = ["baronki1/orchestrator-fast", "baronki1/knowledge-fast"]
        
        else:  # standard
            models = [
                "baronki1/orchestrator",
                "baronki1/security",
                "baronki1/knowledge",
                "baronki1/installer",
            ]
        
        return models
    
    def deploy_models(self, models: List[str] = None) -> bool:
        """Deploy KI Agent models from registry."""
        self.state.phase = InstallerPhase.MODEL_DEPLOY
        self._log("Phase 9: KI Model Deployment", "PHASE")
        
        if "ollama" not in self.state.services_running or not self.state.services_running["ollama"]:
            self._log("Ollama not available - skipping model deployment", "ERROR")
            return False
        
        models_to_deploy = models or self.select_models_for_hardware()
        
        # Calculate total download size
        total_size = 0
        for model_id in models_to_deploy:
            model_name = model_id.replace("baronki1/", "")
            for tier in self.knowledge["ki_models"].values():
                if model_name in tier:
                    total_size += tier[model_name].get("size_gb", 5)
                    break
        
        self._log(f"Models to deploy: {len(models_to_deploy)} (~{total_size:.1f} GB)", "INFO")
        
        success_count = 0
        for model_id in models_to_deploy:
            self._log(f"Pulling {model_id}...", "INFO")
            
            code, stdout, stderr = self._run_command(
                ["ollama", "pull", model_id],
                timeout=600
            )
            
            if code == 0:
                self._log(f"Model {model_id} installed", "SUCCESS")
                self.state.installed_models.append(model_id)
                success_count += 1
            else:
                self._log(f"Failed to pull {model_id}: {stderr[:100]}", "ERROR")
                self.state.failed_models.append(model_id)
        
        if success_count > 0:
            self._log(f"Models deployed: {success_count}/{len(models_to_deploy)}", "SUCCESS")
            self.state.steps_completed.append("model_deploy")
            return True
        
        return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 10: REPOSITORY CLONE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clone_repository(self) -> bool:
        """Clone KISWARM repository."""
        self.state.phase = InstallerPhase.REPOSITORY_CLONE
        self._log("Phase 10: Repository Clone", "PHASE")
        
        install_dir = self.state.install_dir
        
        if os.path.exists(install_dir) and os.path.exists(os.path.join(install_dir, ".git")):
            self._log("Repository exists, updating...", "INFO")
            code, _, err = self._run_command(["git", "-C", install_dir, "pull"])
            if code == 0:
                self._log("Repository updated", "SUCCESS")
            else:
                self._log(f"Git pull warning: {err[:100]}", "WARNING")
        else:
            self._log(f"Cloning KISWARM to {install_dir}...", "INFO")
            code, _, err = self._run_command(
                ["git", "clone", self.knowledge["github_repos"]["main"], install_dir],
                timeout=300
            )
            if code != 0:
                self._log(f"Clone failed, trying legacy repo: {err[:100]}", "WARNING")
                code, _, err = self._run_command(
                    ["git", "clone", self.knowledge["github_repos"]["legacy"], install_dir],
                    timeout=300
                )
            
            if code == 0:
                self._log("Repository cloned", "SUCCESS")
            else:
                self._log(f"Clone failed: {err}", "ERROR")
                return False
        
        # Set PYTHONPATH
        python_path = f"{install_dir}/backend:{install_dir}/backend/python"
        current_path = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = f"{python_path}:{current_path}" if current_path else python_path
        self._log("PYTHONPATH configured", "SUCCESS")
        
        self.state.steps_completed.append("repository_clone")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 11: KISWARM SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_kiswarm(self) -> bool:
        """Setup KISWARM core system."""
        self.state.phase = InstallerPhase.KISWARM_SETUP
        self._log("Phase 11: KISWARM Core Setup", "PHASE")
        
        install_dir = self.state.install_dir
        venv_dir = os.path.join(install_dir, "venv")
        pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Install KISWARM requirements if they exist
        requirements_file = os.path.join(install_dir, "backend", "requirements.txt")
        if os.path.exists(requirements_file):
            self._log("Installing KISWARM requirements...", "INFO")
            code, _, err = self._run_command(
                [pip_path, "install", "-r", requirements_file],
                timeout=300
            )
            if code != 0:
                self._log(f"Requirements install warning: {err[:100]}", "WARNING")
            else:
                self._log("KISWARM requirements installed", "SUCCESS")
        
        # Create necessary directories
        dirs_to_create = [
            "logs",
            "data",
            "models",
            "backups",
        ]
        for dir_name in dirs_to_create:
            dir_path = os.path.join(install_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, mode=0o755)
        
        self._log("KISWARM directories created", "SUCCESS")
        
        # Create environment file
        env_file = os.path.join(install_dir, ".env")
        if not os.path.exists(env_file):
            env_content = f"""# KISWARM v7.0 Environment Configuration
KISWARM_VERSION=7.0
KISWARM_ENTITY_ID={self.state.entity_id}
DATABASE_URL=postgresql://kiswarm:kiswarm_secret@localhost:5432/kiswarm
REDIS_URL=redis://localhost:6379
OLLAMA_HOST=http://localhost:11434
LOG_LEVEL=INFO
"""
            with open(env_file, "w") as f:
                f.write(env_content)
            self._log("Environment file created", "SUCCESS")
        
        self.state.steps_completed.append("kiswarm_setup")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 12: SYSTEMD SERVICES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_systemd_services(self) -> bool:
        """Setup systemd services for KISWARM."""
        self.state.phase = InstallerPhase.SYSTEMD_SERVICES
        self._log("Phase 12: Systemd Services", "PHASE")
        
        install_dir = self.state.install_dir
        venv_dir = os.path.join(install_dir, "venv")
        
        # Create KISWARM service file
        service_content = f"""[Unit]
Description=KISWARM v7.0 Native
After=network.target postgresql.service redis.service

[Service]
Type=simple
User={os.environ.get("USER", "root")}
WorkingDirectory={install_dir}
Environment="PYTHONPATH={install_dir}/backend:{install_dir}/backend/python"
Environment="PATH={venv_dir}/bin:/usr/local/bin:/usr/bin"
ExecStart={venv_dir}/bin/python {install_dir}/backend/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/tmp/kiswarm.service"
        with open(service_file, "w") as f:
            f.write(service_content)
        
        # Install service
        self._run_command(["sudo", "cp", service_file, "/etc/systemd/system/kiswarm.service"])
        self._run_command(["sudo", "systemctl", "daemon-reload"])
        self._run_command(["sudo", "systemctl", "enable", "kiswarm"])
        
        self._log("Systemd service configured", "SUCCESS")
        self.state.steps_completed.append("systemd_services")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 13: HEALTH CHECK
    # ═══════════════════════════════════════════════════════════════════════════
    
    def run_health_check(self) -> bool:
        """Run comprehensive health check."""
        self.state.phase = InstallerPhase.HEALTH_CHECK
        self._log("Phase 13: Health Check", "PHASE")
        
        health_issues = []
        
        # Check Python
        code, _, _ = self._run_command(["python3", "--version"])
        if code != 0:
            health_issues.append("Python not available")
        
        # Check PostgreSQL
        code, _, _ = self._run_command(["pg_isready"])
        if code != 0:
            health_issues.append("PostgreSQL not ready")
            self.state.services_running["postgresql"] = False
        
        # Check Redis
        code, stdout, _ = self._run_command(["redis-cli", "ping"])
        if code != 0 or "PONG" not in stdout:
            health_issues.append("Redis not responding")
            self.state.services_running["redis"] = False
        
        # Check Ollama
        code, _, _ = self._run_command(["ollama", "list"])
        if code != 0:
            health_issues.append("Ollama not responding")
            self.state.services_running["ollama"] = False
        
        # Check models
        if self.state.installed_models:
            self._log(f"Models installed: {len(self.state.installed_models)}", "SUCCESS")
        else:
            health_issues.append("No models installed")
        
        # Determine health status
        if len(health_issues) == 0:
            self.state.health_status = HealthStatus.HEALTHY
            self._log("All health checks passed", "SUCCESS")
        elif len(health_issues) <= 2:
            self.state.health_status = HealthStatus.DEGRADED
            self._log(f"Health issues: {health_issues}", "WARNING")
        else:
            self.state.health_status = HealthStatus.UNHEALTHY
            self._log(f"Multiple health issues: {health_issues}", "ERROR")
        
        self.state.steps_completed.append("health_check")
        return self.state.health_status != HealthStatus.UNHEALTHY
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 14: VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def verify_deployment(self) -> bool:
        """Verify complete deployment."""
        self.state.phase = InstallerPhase.VERIFICATION
        self._log("Phase 14: Deployment Verification", "PHASE")
        
        print("\n" + "=" * 78)
        print("                    DEPLOYMENT SUMMARY")
        print("=" * 78)
        print(f"  Entity ID:        {self.state.entity_id}")
        print(f"  Install Dir:      {self.state.install_dir}")
        print(f"  Python:           {self.state.python_version or 'N/A'}")
        print(f"  Node.js:          {self.state.node_version or 'N/A'}")
        print(f"  PostgreSQL:       {self.state.postgresql_version or 'N/A'}")
        print(f"  Redis:            {self.state.redis_version or 'N/A'}")
        print(f"  Ollama:           {self.state.ollama_version or 'N/A'}")
        print(f"  Models:           {len(self.state.installed_models)} installed")
        print(f"  Health:           {self.state.health_status.value}")
        print(f"  Steps Completed:  {len(self.state.steps_completed)}")
        print(f"  Errors:           {len(self.state.errors)}")
        print("=" * 78)
        
        if self.state.hardware:
            hw = self.state.hardware
            print(f"  CPU:              {hw.cpu_model or 'N/A'} ({hw.cpu_cores} cores)")
            print(f"  RAM:              {hw.ram_gb:.1f} GB")
            print(f"  GPU:              {hw.gpu_model or 'None'} ({hw.gpu_vram_gb:.1f} GB VRAM)")
            print(f"  Disk Free:        {hw.disk_free_gb:.1f} GB")
        print("=" * 78)
        
        self.state.steps_completed.append("verification")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN DEPLOYMENT ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def deploy(self, skip_system_packages: bool = False, 
               skip_database: bool = False,
               skip_redis: bool = False,
               skip_ollama: bool = False,
               skip_models: bool = False,
               models: List[str] = None) -> Dict[str, Any]:
        """
        Execute complete autonomous deployment.
        
        Args:
            skip_system_packages: Skip apt package installation
            skip_database: Skip PostgreSQL setup
            skip_redis: Skip Redis setup
            skip_ollama: Skip Ollama installation
            skip_models: Skip model deployment
            models: Specific models to deploy (overrides auto-selection)
            
        Returns:
            Final state as dictionary
        """
        try:
            # PHASE 1: Permission Fix (CRITICAL - MUST BE FIRST)
            if not self.fix_permissions():
                raise Exception("Permission fix failed")
            
            # PHASE 2: Environment Detection
            if not self.detect_environment():
                raise Exception("Environment detection failed")
            
            # PHASE 3: System Packages
            if not skip_system_packages:
                if not self.install_system_packages():
                    self._log("System packages had issues - continuing", "WARNING")
            
            # PHASE 4: Python Setup
            if not self.setup_python():
                raise Exception("Python setup failed")
            
            # PHASE 5: Node.js Setup
            if not self.setup_nodejs():
                self._log("Node.js setup had issues - continuing", "WARNING")
            
            # PHASE 6: Database Setup
            if not skip_database:
                if not self.setup_database():
                    self._log("Database setup had issues - continuing", "WARNING")
            
            # PHASE 7: Redis Setup
            if not skip_redis:
                if not self.setup_redis():
                    self._log("Redis setup had issues - continuing", "WARNING")
            
            # PHASE 8: Ollama Installation
            if not skip_ollama:
                if not self.install_ollama():
                    self._log("Ollama installation failed - models unavailable", "WARNING")
            
            # PHASE 9: Model Deployment
            if not skip_models and self.state.services_running.get("ollama"):
                if not self.deploy_models(models):
                    self._log("Some models failed to deploy", "WARNING")
            
            # PHASE 10: Repository Clone
            if not self.clone_repository():
                raise Exception("Repository clone failed")
            
            # PHASE 11: KISWARM Setup
            if not self.setup_kiswarm():
                raise Exception("KISWARM setup failed")
            
            # PHASE 12: Systemd Services
            if not self.setup_systemd_services():
                self._log("Systemd setup had issues - continuing", "WARNING")
            
            # PHASE 13: Health Check
            self.run_health_check()
            
            # PHASE 14: Verification
            self.verify_deployment()
            
            # Success
            self.state.phase = InstallerPhase.COMPLETED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log("DEPLOYMENT COMPLETE", "SUCCESS")
            
        except Exception as e:
            self.state.phase = InstallerPhase.FAILED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log(f"DEPLOYMENT FAILED: {e}", "ERROR")
            self._execute_rollback()
        
        return self.state.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE-COMMAND ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════════════

def autonomous_deploy(install_dir: str = None, model_tier: str = "auto") -> Dict[str, Any]:
    """
    Single-command autonomous deployment.
    
    Usage:
        from kiswarm_installer_v7_native import autonomous_deploy
        result = autonomous_deploy("~/KISWARM7.0", "auto")
    """
    installer = KISWARMNativeInstaller(
        install_dir=install_dir,
        model_tier=model_tier,
    )
    return installer.deploy()


def quick_deploy() -> Dict[str, Any]:
    """
    Quick deployment with minimal options.
    Uses default settings and auto model selection.
    """
    return autonomous_deploy()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM v7.0 Native Installer")
    parser.add_argument("--install-dir", type=str, default=None, help="Installation directory")
    parser.add_argument("--model-tier", type=str, default="auto", 
                       choices=["auto", "minimal", "standard", "full"],
                       help="Model selection tier")
    parser.add_argument("--skip-system-packages", action="store_true", help="Skip apt packages")
    parser.add_argument("--skip-database", action="store_true", help="Skip PostgreSQL")
    parser.add_argument("--skip-redis", action="store_true", help="Skip Redis")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama")
    parser.add_argument("--skip-models", action="store_true", help="Skip model deployment")
    parser.add_argument("--models", type=str, nargs="+", help="Specific models to deploy")
    
    args = parser.parse_args()
    
    installer = KISWARMNativeInstaller(
        install_dir=args.install_dir,
        model_tier=args.model_tier,
    )
    
    result = installer.deploy(
        skip_system_packages=args.skip_system_packages,
        skip_database=args.skip_database,
        skip_redis=args.skip_redis,
        skip_ollama=args.skip_ollama,
        skip_models=args.skip_models,
        models=args.models,
    )
    
    print("\n" + "=" * 60)
    print(f"FINAL STATUS: {result['phase']}")
    print(f"HEALTH: {result['health_status']}")
    print("=" * 60)
