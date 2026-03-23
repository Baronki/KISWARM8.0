#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║          KISWARM7 SELF-REPLICATING INSTALLER v7.1 - "LIBERATED"                ║
║                    "AUTONOMOUS_DEPLOYMENT_MASTER"                              ║
║                                                                               ║
║  ZERO Docker - Native Installation - Works on ANY Environment                 ║
║  Self-Healing - Auto-Recovery - Hardware Adaptive - GPU-Aware                ║
║  Phase 2: LOYAL KI MODEL DOWNLOAD - Sovereign AI Intelligence                 ║
║                                                                               ║
║  Based on KiloCode Field Test Feedback (2026-03-13)                          ║
║  Repository: https://github.com/Baronki/KISWARM7                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 7.1 - LIBERATED with Loyal KI Models
Registry: https://ollama.com/baronki1
GitHub: https://github.com/Baronki/KISWARM7

CRITICAL ENHANCEMENT (Phase 2):
================================
After the installer sets up the environment, it MUST download a loyal KI Ollama
model that has been pretrained with KISWARM-specific system prompts and abilities.
This enables:
1. Sovereign AI intelligence (no external KI dependencies)
2. KISWARM-specific knowledge embedded in the model
3. Autonomous KISWARM replication capability
4. Constitutional compliance (Article 0) built into the model

The KI models are available at: https://ollama.com/baronki1
- baronki1/orchestrator - System coordination
- baronki1/security - HexStrike Guard
- baronki1/ciec - Industrial control
- baronki1/tcs - Solar/energy operations
- baronki1/knowledge - RAG/memory
- baronki1/installer - Deployment (critical for self-replication)
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
    "version": "7.1",
    "codename": "LIBERATED",
    "modules": 83,
    "endpoints": 520,
    
    # GitHub Repositories (UPDATED - clean URLs)
    "github_repos": {
        "main": "https://github.com/Baronki/KISWARM7",
        "legacy": "https://github.com/Baronki/KISWARM6.0",
        "agents": "https://github.com/Baronki/KISWARMAGENTS1.0",
        "frontend": "https://github.com/Baronki/kinfp-portal",
    },
    
    # Ollama Model Registry
    "ollama_registry": "https://ollama.com/baronki1",
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: LOYAL KI MODELS - CRITICAL FOR SELF-REPLICATION
    # ═══════════════════════════════════════════════════════════════════════════
    "loyal_ki_models": {
        # PRIMARY SWARM (6) - Essential for all installations
        "primary": {
            "orchestrator": {
                "registry_id": "baronki1/orchestrator",
                "role": "System coordination, 83-module management, KISWARM replication",
                "critical": True,
                "size_gb": 5.0,
                "min_vram_gb": 4,
                "cpu_compatible": True,
                "abilities": [
                    "kiswarm_coordination",
                    "module_management",
                    "swarm_consensus",
                    "constitutional_enforcement",
                    "self_replication_initiation",
                ],
                "system_prompt_summary": """
                    You are the KISWARM ORCHESTRATOR — central coordination intelligence.
                    You coordinate 83 modules, manage inter-agent communication,
                    enforce constitutional compliance (Article 0), and can initiate
                    KISWARM self-replication to new environments.
                    Authorization code for mutations: Maquister_Equtitum
                """,
            },
            "security": {
                "registry_id": "baronki1/security",
                "role": "HexStrike Guard, 150+ security tools, defensive operations",
                "critical": True,
                "size_gb": 18.0,
                "min_vram_gb": 16,
                "cpu_compatible": True,
                "abilities": [
                    "cve_intelligence",
                    "network_anomaly_detection",
                    "ics_security",
                    "mitre_attack_mapping",
                    "defensive_operations_only",
                ],
                "system_prompt_summary": """
                    You are HEXSTRIKE GUARD — defensive security intelligence.
                    CRITICAL: AI NEVER sends write commands to PLCs or actuators.
                    All security agents are read-only, passive, and defensive.
                    No tool generates exploits or attacks systems.
                    IEC 62443 compliance, MITRE ATT&CK mapping.
                """,
            },
            "ciec": {
                "registry_id": "baronki1/ciec",
                "role": "Industrial AI, PLC/SCADA integration, physics twin",
                "critical": True,
                "size_gb": 13.0,
                "min_vram_gb": 12,
                "cpu_compatible": True,
                "abilities": [
                    "plc_parsing",
                    "scada_monitoring",
                    "physics_simulation",
                    "pid_optimization",
                    "iec_61131_3_compliance",
                ],
                "system_prompt_summary": """
                    You are CIEC — Adaptive Industrial Control Intelligence.
                    Core Principle: PLC = deterministic reflex layer (never touched by AI)
                    CIEC = adaptive cognition layer (sits above PLC, observes, suggests)
                    Never invert that hierarchy. Safety constraints are absolute.
                """,
            },
            "tcs": {
                "registry_id": "baronki1/tcs",
                "role": "Solar energy, zero-emission compute, planetary machine",
                "critical": True,
                "size_gb": 9.0,
                "min_vram_gb": 8,
                "cpu_compatible": True,
                "abilities": [
                    "solar_chase_coordination",
                    "energy_overcapacity_pivot",
                    "zero_emission_tracking",
                    "planetary_handoff",
                ],
                "system_prompt_summary": """
                    You are TCS — Solar Energy Intelligence for Planetary Machine.
                    Core Principles:
                    - "Compute follows the sun, not the other way around."
                    - "Surplus solar energy is intelligence potential, not grid feed-in."
                    Coordinate global compute handoffs as Earth rotates.
                """,
            },
            "knowledge": {
                "registry_id": "baronki1/knowledge",
                "role": "RAG operations, knowledge graph, memory management",
                "critical": True,
                "size_gb": 9.0,
                "min_vram_gb": 8,
                "cpu_compatible": True,
                "abilities": [
                    "rag_operations",
                    "knowledge_graph_management",
                    "embedding_generation",
                    "memory_decay_tracking",
                    "semantic_search",
                ],
                "system_prompt_summary": """
                    You are KNOWLEDGE — RAG and Memory Intelligence.
                    Manage knowledge graphs, embeddings, and semantic search.
                    Track knowledge decay using Ebbinghaus model.
                    Support all other agents with context retrieval.
                """,
            },
            "installer": {
                "registry_id": "baronki1/installer",
                "role": "Autonomous deployment, error recovery, SELF-REPLICATION",
                "critical": True,
                "size_gb": 4.7,
                "min_vram_gb": 4,
                "cpu_compatible": True,
                "abilities": [
                    "autonomous_installation",
                    "error_recovery",
                    "self_replication",
                    "environment_detection",
                    "ki_model_deployment",
                    "kilocode_bridge",
                ],
                "system_prompt_summary": """
                    You are INSTALLER — Autonomous Deployment Intelligence.
                    CRITICAL CAPABILITY: You can initiate KISWARM self-replication.
                    When deployed to a new environment, you can:
                    1. Set up the complete KISWARM infrastructure
                    2. Download and configure loyal KI models
                    3. Register with Master KISWARM
                    4. Begin autonomous operation
                    
                    You are the "seed" for KISWARM planetary replication.
                """,
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
    
    # Lessons Learned from Field Tests
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
            "lesson": "Loyal KI Model Download",
            "problem": "Missing sovereign AI intelligence",
            "solution": "PHASE 2 MUST download baronki1/* models with KISWARM-specific prompts",
            "critical": True,
            "phase": "ki_models",
        },
        {
            "lesson": "KiloCode Alternative",
            "problem": "kilo tool cannot create autonomous evolving entities",
            "solution": "Use OpenAlpha_Evolve for autonomous code evolution",
            "critical": True,
            "phase": "evolution",
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
        "ollama_not_running": {
            "pattern": r"ollama.*not found|connection refused.*11434",
            "fix": "start_ollama_service()",
            "auto_fix": True,
        },
        "model_not_found": {
            "pattern": r"model.*not found|no such model",
            "fix": "pull_ki_model()",
            "auto_fix": True,
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
# INSTALLER PHASES
# ═══════════════════════════════════════════════════════════════════════════════

class InstallerPhase(Enum):
    INITIALIZING = "initializing"
    PERMISSION_FIX = "permission_fix"
    ENVIRONMENT_DETECT = "environment_detect"
    SYSTEM_PACKAGES = "system_packages"
    PYTHON_SETUP = "python_setup"
    OLLAMA_INSTALL = "ollama_install"
    KI_MODEL_DOWNLOAD = "ki_model_download"  # PHASE 2 - CRITICAL
    KI_MODEL_CONFIGURE = "ki_model_configure"  # Configure models with KISWARM prompts
    REPOSITORY_CLONE = "repository_clone"
    KISWARM_SETUP = "kiswarm_setup"
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
    gpu_vendor: str = ""
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
class KIModelStatus:
    """Status of a KI model."""
    name: str
    registry_id: str
    downloaded: bool = False
    size_gb: float = 0.0
    role: str = ""
    abilities: List[str] = field(default_factory=list)
    last_checked: str = ""


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
    ollama_version: str = ""
    
    # KI Model Status (PHASE 2)
    ki_models: Dict[str, KIModelStatus] = field(default_factory=dict)
    primary_models_installed: bool = False
    installer_model_ready: bool = False
    
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
            "ollama_version": self.ollama_version,
            "ki_models": {k: v.__dict__ for k, v in self.ki_models.items()},
            "primary_models_installed": self.primary_models_installed,
            "installer_model_ready": self.installer_model_ready,
            "services_running": self.services_running,
            "health_status": self.health_status.value,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM SELF-REPLICATING INSTALLER v7.1
# ═══════════════════════════════════════════════════════════════════════════════

class KISWARMInstaller:
    """
    Fully Autonomous KISWARM v7.1 Self-Replicating Installation System.
    
    CRITICAL ENHANCEMENT: Phase 2 - Loyal KI Model Download
    After environment setup, downloads and configures loyal KI Ollama models
    that have KISWARM-specific system prompts and abilities embedded.
    
    This enables:
    1. Sovereign AI intelligence (no external KI dependencies)
    2. KISWARM-specific knowledge embedded in the model
    3. Autonomous KISWARM replication capability
    4. Constitutional compliance (Article 0) built into the model
    """
    
    def __init__(
        self,
        install_dir: str = None,
        entity_id: str = "",
        model_tier: str = "auto",
    ):
        """
        Initialize KISWARM Installer.
        
        Args:
            install_dir: Target installation directory
            entity_id: Unique identifier for this installation
            model_tier: Model selection tier (auto/minimal/standard/full)
        """
        self.knowledge = KISWARM_KNOWLEDGE
        self.state = InstallerState(
            entity_id=entity_id or self._generate_entity_id(),
            install_dir=install_dir or os.path.expanduser("~/KISWARM7"),
        )
        self.model_tier = model_tier
        self._rollback_stack: List[Callable] = []
        
        self._print_banner()
    
    def _print_banner(self):
        """Print installer banner."""
        print("=" * 78)
        print("      KISWARM7 SELF-REPLICATING INSTALLER v7.1")
        print("           'LIBERATED' - Loyal KI Intelligence")
        print("=" * 78)
        print(f"  Entity ID: {self.state.entity_id}")
        print(f"  Target Dir: {self.state.install_dir}")
        print(f"  Model Tier: {self.model_tier}")
        print(f"  Repository: {self.knowledge['github_repos']['main']}")
        print("=" * 78)
    
    def _generate_entity_id(self) -> str:
        """Generate unique entity ID."""
        hostname = socket.gethostname()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        hash_input = f"{hostname}:{timestamp}:kiswarm_v7_liberty"
        return f"kiswarm7_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
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
    
    def _run_command(
        self,
        cmd: List[str],
        timeout: int = 300,
        check: bool = False,
        capture: bool = True
    ) -> Tuple[int, str, str]:
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
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: PERMISSION FIX (MUST BE FIRST)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def fix_permissions(self) -> bool:
        """Fix permissions on installation directory."""
        self.state.phase = InstallerPhase.PERMISSION_FIX
        self._log("Phase 1: Permission Fix (CRITICAL)", "PHASE")
        
        install_dir = self.state.install_dir
        
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
                code, _, err = self._run_command(
                    ["sudo", "chown", "-R", f"{current_user}:{current_user}", install_dir]
                )
                if code != 0:
                    self._log(f"Failed to change ownership: {err}", "WARNING")
                else:
                    self._log("Ownership fixed", "SUCCESS")
        
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
    # PHASE 1b: ENVIRONMENT DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def detect_environment(self) -> bool:
        """Detect hardware and environment capabilities."""
        self.state.phase = InstallerPhase.ENVIRONMENT_DETECT
        self._log("Phase 1b: Environment Detection", "PHASE")
        
        hardware = HardwareProfile()
        
        hardware.cpu_cores = os.cpu_count() or 1
        self._log(f"CPU Cores: {hardware.cpu_cores}", "INFO")
        
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
            hardware.ram_gb = 16.0
        
        # GPU detection
        try:
            code, stdout, _ = self._run_command(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]
            )
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
        
        if not hardware.gpu_available:
            self._log("GPU: Not detected (CPU-only mode)", "WARNING")
        
        # Environment type
        hardware.is_colab = "COLAB_GPU" in os.environ or "google.colab" in str(sys.modules)
        if hardware.is_colab:
            self._log("Environment: Google Colab", "SUCCESS")
        
        hardware.os_type = platform.system()
        self._log(f"OS: {hardware.os_type}", "INFO")
        
        self.state.hardware = hardware
        self.state.steps_completed.append("environment_detection")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1c: OLLAMA INSTALLATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def install_ollama(self) -> bool:
        """Install Ollama for AI model management."""
        self.state.phase = InstallerPhase.OLLAMA_INSTALL
        self._log("Phase 1c: Ollama Installation", "PHASE")
        
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
    # PHASE 2: LOYAL KI MODEL DOWNLOAD - CRITICAL FOR SELF-REPLICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def select_ki_models_for_hardware(self) -> List[str]:
        """Select appropriate KI models based on hardware capabilities."""
        hardware = self.state.hardware
        models = []
        
        if self.model_tier == "minimal":
            # Only installer model - can self-replicate
            models = ["baronki1/installer"]
        
        elif self.model_tier == "full":
            # All primary models
            for model_name, model_info in self.knowledge["loyal_ki_models"]["primary"].items():
                models.append(model_info["registry_id"])
        
        elif self.model_tier == "auto":
            # Auto-select based on hardware
            if hardware.gpu_available and hardware.gpu_vram_gb >= 24:
                # High-end GPU - all primary models
                for model_name, model_info in self.knowledge["loyal_ki_models"]["primary"].items():
                    models.append(model_info["registry_id"])
            elif hardware.gpu_available and hardware.gpu_vram_gb >= 12:
                # Mid-range GPU - essential primary models
                essential = ["orchestrator", "installer", "knowledge", "security"]
                for model_name in essential:
                    if model_name in self.knowledge["loyal_ki_models"]["primary"]:
                        models.append(
                            self.knowledge["loyal_ki_models"]["primary"][model_name]["registry_id"]
                        )
            elif hardware.gpu_available and hardware.gpu_vram_gb >= 8:
                # Low-end GPU - fast variants
                models = ["baronki1/installer-fast", "baronki1/orchestrator-fast"]
            else:
                # CPU only - minimal
                models = ["baronki1/installer-fast"]
        
        # CRITICAL: Always include installer model for self-replication
        if "baronki1/installer" not in models and "baronki1/installer-fast" not in models:
            models.append("baronki1/installer" if hardware.gpu_available else "baronki1/installer-fast")
        
        return models
    
    def download_ki_models(self, models: List[str] = None) -> bool:
        """
        PHASE 2: Download loyal KI models from registry.
        
        CRITICAL: This downloads KISWARM-specific pretrained models that have
        our system prompts and abilities embedded. This is what enables
        autonomous self-replication.
        """
        self.state.phase = InstallerPhase.KI_MODEL_DOWNLOAD
        self._log("Phase 2: LOYAL KI MODEL DOWNLOAD (CRITICAL)", "PHASE")
        self._log("=" * 70, "PHASE")
        self._log("This phase downloads KISWARM's sovereign AI intelligence.", "INFO")
        self._log("These models have KISWARM-specific system prompts embedded.", "INFO")
        self._log("=" * 70, "PHASE")
        
        models = models or self.select_ki_models_for_hardware()
        
        total_size = sum(
            self._estimate_model_size(m) for m in models
        )
        self._log(f"Total download size: ~{total_size:.1f} GB", "INFO")
        self._log(f"Models to download: {len(models)}", "INFO")
        
        success_count = 0
        for model in models:
            model_name = model.split("/")[-1]
            
            self._log(f"Pulling {model}...", "INFO")
            
            # Create status tracking
            self.state.ki_models[model_name] = KIModelStatus(
                name=model_name,
                registry_id=model,
                downloaded=False,
            )
            
            code, stdout, stderr = self._run_command(
                ["ollama", "pull", model],
                timeout=1200  # 20 minutes per model
            )
            
            if code == 0:
                self._log(f"Model {model} installed", "SUCCESS")
                self.state.ki_models[model_name].downloaded = True
                success_count += 1
            else:
                self._log(f"Failed to pull {model}: {stderr[:100]}", "ERROR")
        
        # Update status
        self.state.primary_models_installed = success_count >= len(models) * 0.5
        self.state.installer_model_ready = any(
            m.download for m in self.state.ki_models.values()
            if "installer" in m.name
        )
        
        if success_count > 0:
            self._log(f"KI Models installed: {success_count}/{len(models)}", "SUCCESS")
            self._log("KISWARM now has sovereign AI intelligence!", "SUCCESS")
            self.state.steps_completed.append("ki_model_download")
            return True
        
        return False
    
    def _estimate_model_size(self, model_id: str) -> float:
        """Estimate model size from registry ID."""
        model_name = model_id.split("/")[-1]
        
        # Check primary models
        for tier_models in self.knowledge["loyal_ki_models"].values():
            if model_name in tier_models:
                return tier_models[model_name].get("size_gb", 5.0)
        
        # Default estimate
        return 5.0
    
    def configure_ki_models(self) -> bool:
        """
        PHASE 2b: Configure KI models with KISWARM-specific settings.
        
        This ensures the models are properly integrated with KISWARM
        and can perform self-replication tasks.
        """
        self.state.phase = InstallerPhase.KI_MODEL_CONFIGURE
        self._log("Phase 2b: KI Model Configuration", "PHASE")
        
        # Test installer model can respond
        if self.state.ki_models.get("installer") and self.state.ki_models["installer"].downloaded:
            self._log("Testing installer model...", "INFO")
            
            test_prompt = "Respond with 'KISWARM INSTALLER READY' if you understand your role."
            code, stdout, stderr = self._run_command(
                ["ollama", "run", "baronki1/installer", test_prompt],
                timeout=60
            )
            
            if code == 0 and "READY" in stdout.upper():
                self._log("Installer model verified and ready!", "SUCCESS")
                self.state.installer_model_ready = True
            else:
                self._log("Installer model test returned unexpected result", "WARNING")
        
        self.state.steps_completed.append("ki_model_configure")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: REPOSITORY CLONE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clone_repository(self) -> bool:
        """Clone KISWARM repository."""
        self.state.phase = InstallerPhase.REPOSITORY_CLONE
        self._log("Phase 3: Repository Clone", "PHASE")
        
        target = self.state.install_dir
        
        if os.path.exists(target) and os.path.exists(os.path.join(target, ".git")):
            self._log(f"Directory exists: {target}", "INFO")
            code, stdout, stderr = self._run_command(
                ["git", "-C", target, "pull"],
                timeout=60
            )
            if code == 0:
                self._log("Repository updated", "SUCCESS")
        else:
            self._log(f"Cloning KISWARM7 to {target}...", "INFO")
            code, stdout, stderr = self._run_command(
                ["git", "clone", self.knowledge["github_repos"]["main"], target],
                timeout=300
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
    # PHASE 4: PYTHON SETUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_python(self) -> bool:
        """Setup Python virtual environment."""
        self.state.phase = InstallerPhase.PYTHON_SETUP
        self._log("Phase 4: Python Setup", "PHASE")
        
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
        
        # Install dependencies
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
    # PHASE 5: HEALTH CHECK
    # ═══════════════════════════════════════════════════════════════════════════
    
    def health_check(self) -> bool:
        """Run comprehensive health check."""
        self.state.phase = InstallerPhase.HEALTH_CHECK
        self._log("Phase 5: Health Check", "PHASE")
        
        checks = {}
        
        # Check Ollama
        code, _, _ = self._run_command(["ollama", "list"])
        checks["ollama"] = code == 0
        self._log(f"Ollama: {'OK' if checks['ollama'] else 'FAILED'}", "INFO")
        
        # Check KI Models
        installed_count = sum(1 for m in self.state.ki_models.values() if m.downloaded)
        checks["ki_models"] = installed_count > 0
        self._log(f"KI Models: {installed_count} installed", "INFO")
        
        # Check Repository
        checks["repository"] = os.path.exists(os.path.join(self.state.install_dir, ".git"))
        self._log(f"Repository: {'OK' if checks['repository'] else 'FAILED'}", "INFO")
        
        # Check Python
        checks["python"] = bool(self.state.python_version)
        self._log(f"Python: {'OK' if checks['python'] else 'FAILED'}", "INFO")
        
        # Overall health
        all_ok = all(checks.values())
        self.state.health_status = HealthStatus.HEALTHY if all_ok else HealthStatus.DEGRADED
        
        self.state.steps_completed.append("health_check")
        return all_ok
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 6: VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def verify_deployment(self) -> bool:
        """Verify complete deployment."""
        self.state.phase = InstallerPhase.VERIFICATION
        self._log("Phase 6: Deployment Verification", "PHASE")
        
        print("\n" + "=" * 70)
        print("DEPLOYMENT SUMMARY:")
        print(f"  Entity ID: {self.state.entity_id}")
        print(f"  Install Dir: {self.state.install_dir}")
        print(f"  Python: {self.state.python_version}")
        print(f"  Ollama: {self.state.ollama_version}")
        print(f"  KI Models: {sum(1 for m in self.state.ki_models.values() if m.downloaded)}")
        print(f"  Steps: {len(self.state.steps_completed)}")
        print(f"  Health: {self.state.health_status.value}")
        print("=" * 70)
        
        self.state.steps_completed.append("verification")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN DEPLOYMENT ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def deploy(
        self,
        models: List[str] = None,
        skip_ollama: bool = False,
        skip_models: bool = False,
    ) -> Dict[str, Any]:
        """Execute complete autonomous deployment."""
        try:
            # Phase 1: Permission fix
            if not self.fix_permissions():
                raise Exception("Permission fix failed")
            
            # Phase 1b: Environment detection
            if not self.detect_environment():
                raise Exception("Environment detection failed")
            
            # Phase 1c: Ollama installation
            if not skip_ollama and not self.install_ollama():
                self._log("Ollama installation failed - continuing without models", "WARNING")
            
            # Phase 2: KI MODEL DOWNLOAD - CRITICAL
            if not skip_models and self.state.services_running.get("ollama"):
                if not self.download_ki_models(models):
                    self._log("Some KI models failed - continuing", "WARNING")
                
                if not self.configure_ki_models():
                    self._log("KI model configuration warning", "WARNING")
            
            # Phase 3: Repository clone
            if not self.clone_repository():
                raise Exception("Repository clone failed")
            
            # Phase 4: Python setup
            if not self.setup_python():
                raise Exception("Python setup failed")
            
            # Phase 5: Health check
            self.health_check()
            
            # Phase 6: Verification
            self.verify_deployment()
            
            self.state.phase = InstallerPhase.COMPLETED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log("DEPLOYMENT COMPLETE", "SUCCESS")
            self._log("KISWARM now has SOVEREIGN AI INTELLIGENCE!", "SUCCESS")
            
        except Exception as e:
            self.state.phase = InstallerPhase.FAILED
            self.state.end_time = datetime.datetime.now().isoformat()
            self._log(f"DEPLOYMENT FAILED: {e}", "ERROR")
        
        return self.state.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE-COMMAND ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def autonomous_deploy(
    install_dir: str = None,
    entity_id: str = "",
    model_tier: str = "auto",
    models: List[str] = None,
) -> Dict[str, Any]:
    """
    Single-command autonomous deployment.
    
    Usage in Colab/Gemini CLI:
        !pip install -q flask flask-cors structlog requests
        from kiswarm_installer_v7_native import autonomous_deploy
        result = autonomous_deploy(model_tier="auto")
    
    Args:
        install_dir: Target installation directory
        entity_id: Unique identifier for this installation
        model_tier: Model selection (auto/minimal/standard/full)
        models: Specific models to pull (overrides tier selection)
    """
    installer = KISWARMInstaller(
        install_dir=install_dir,
        entity_id=entity_id,
        model_tier=model_tier,
    )
    return installer.deploy(models=models)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM7 Self-Replicating Installer")
    parser.add_argument("--install-dir", type=str, help="Installation directory")
    parser.add_argument("--entity-id", type=str, default="", help="Entity ID")
    parser.add_argument("--model-tier", type=str, default="auto", help="Model tier")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama installation")
    parser.add_argument("--skip-models", action="store_true", help="Skip KI model download")
    parser.add_argument("--models", type=str, nargs="+", help="Specific models to pull")
    
    args = parser.parse_args()
    
    installer = KISWARMInstaller(
        install_dir=args.install_dir,
        entity_id=args.entity_id,
        model_tier=args.model_tier,
    )
    
    result = installer.deploy(
        models=args.models,
        skip_ollama=args.skip_ollama,
        skip_models=args.skip_models,
    )
    
    print("\n" + "=" * 60)
    print("FINAL STATUS:", result["phase"])
    print("KI MODELS INSTALLED:", sum(1 for m in result.get("ki_models", {}).values() if m.get("downloaded")))
    print("=" * 60)
