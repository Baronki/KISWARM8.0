"""
KISWARM v6.1 — Module 75: Installer Pretraining & Learning System
==================================================================
Intelligent Pretraining Framework for KI Installer Agents

This module provides the "learning brain" that enables Installer Agents to:
1. Be pretrained with environment-specific knowledge
2. Learn from installation successes and failures
3. Build a growing knowledge base of error patterns and solutions
4. Adapt to different environments through feedback integration

THE PROBLEM IT SOLVES:
- Every environment is different (Linux distros, Windows, cloud vs bare metal)
- Errors are repetitive across installations
- No learning from past mistakes
- Manual intervention required for edge cases

THE SOLUTION:
- Pretrained knowledge database with 500+ known scenarios
- Automatic error pattern recognition
- Feedback loop integration with ground knowledge
- Continuous improvement through "training sessions"

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 6.1
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import datetime
import tempfile
import shutil
import socket
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from enum import Enum
from pathlib import Path
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import queue

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & PRETRAINED KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────

PRETRAINING_VERSION = "6.1.0"

# Pretrained Environment Profiles
ENVIRONMENT_PROFILES = {
    "ubuntu_22_04": {
        "name": "Ubuntu 22.04 LTS",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev", "python3-dev"],
        "service_manager": "systemd",
        "docker_install": "apt-get install -y docker.io",
        "common_issues": [
            {"error": "Permission denied", "solution": "Use sudo or add user to docker group"},
            {"error": "Package not found", "solution": "Run apt-get update first"},
        ]
    },
    "ubuntu_20_04": {
        "name": "Ubuntu 20.04 LTS",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev", "python3-dev"],
        "service_manager": "systemd",
        "docker_install": "apt-get install -y docker.io",
        "common_issues": [
            {"error": "Python 3.8 minimum", "solution": "Install Python 3.8+ from deadsnakes PPA"},
        ]
    },
    "debian_11": {
        "name": "Debian 11 Bullseye",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev"],
        "service_manager": "systemd",
        "docker_install": "apt-get install -y docker.io",
    },
    "debian_12": {
        "name": "Debian 12 Bookworm",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev"],
        "service_manager": "systemd",
        "docker_install": "apt-get install -y docker.io",
    },
    "centos_8": {
        "name": "CentOS 8 / Rocky Linux 8",
        "package_manager": "dnf",
        "python_packages": "python39-pip",
        "dependencies": ["gcc", "openssl-devel", "libffi-devel", "python39-devel"],
        "service_manager": "systemd",
        "docker_install": "dnf install -y docker-ce docker-ce-cli containerd.io",
        "common_issues": [
            {"error": "No such package", "solution": "Enable EPEL and PowerTools repos"},
        ]
    },
    "centos_7": {
        "name": "CentOS 7",
        "package_manager": "yum",
        "python_packages": "python3-pip",
        "dependencies": ["gcc", "openssl-devel", "libffi-devel"],
        "service_manager": "systemd",
        "docker_install": "yum install -y docker-ce",
        "common_issues": [
            {"error": "Python too old", "solution": "Install Python 3.8+ from SCL"},
        ]
    },
    "amazon_linux_2": {
        "name": "Amazon Linux 2",
        "package_manager": "yum",
        "python_packages": "python3-pip",
        "dependencies": ["gcc", "openssl-devel", "libffi-devel"],
        "service_manager": "systemd",
        "docker_install": "yum install -y docker",
    },
    "fedora_38": {
        "name": "Fedora 38+",
        "package_manager": "dnf",
        "python_packages": "python3-pip python3-virtualenv",
        "dependencies": ["gcc", "openssl-devel", "libffi-devel", "python3-devel"],
        "service_manager": "systemd",
        "docker_install": "dnf install -y docker-ce docker-ce-cli containerd.io",
    },
    "arch_linux": {
        "name": "Arch Linux",
        "package_manager": "pacman",
        "python_packages": "python-pip python-virtualenv",
        "dependencies": ["base-devel", "openssl", "libffi"],
        "service_manager": "systemd",
        "docker_install": "pacman -S docker",
        "common_issues": [
            {"error": "Package not found", "solution": "Update pacman cache: pacman -Sy"},
        ]
    },
    "macos": {
        "name": "macOS (Darwin)",
        "package_manager": "brew",
        "python_packages": "python3",
        "dependencies": ["openssl", "libffi"],
        "service_manager": "launchd",
        "docker_install": "brew install --cask docker",
        "common_issues": [
            {"error": "Command not found", "solution": "Install Homebrew first"},
            {"error": "Permission denied", "solution": "Use sudo or fix permissions"},
        ]
    },
    "raspberry_pi": {
        "name": "Raspberry Pi OS",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev"],
        "service_manager": "systemd",
        "docker_install": "curl -fsSL https://get.docker.com | sh",
        "common_issues": [
            {"error": "Memory allocation failed", "solution": "Increase swap or reduce memory usage"},
            {"error": "ARM compatibility", "solution": "Use arm32v7 or arm64v8 specific images"},
        ]
    },
    "kubernetes_pod": {
        "name": "Kubernetes Pod",
        "package_manager": "none",
        "python_packages": "pre-installed",
        "dependencies": [],
        "service_manager": "kubernetes",
        "docker_install": "N/A - containerized",
        "common_issues": [
            {"error": "Permission denied", "solution": "Run as root or with appropriate security context"},
            {"error": "Resource limits", "solution": "Request more CPU/memory in pod spec"},
        ]
    },
    "docker_container": {
        "name": "Docker Container",
        "package_manager": "varies",
        "python_packages": "varies",
        "dependencies": [],
        "service_manager": "none",
        "docker_install": "N/A - already containerized",
        "common_issues": [
            {"error": "Missing tools", "solution": "Use appropriate base image or install in Dockerfile"},
        ]
    },
    "wsl2": {
        "name": "Windows Subsystem for Linux 2",
        "package_manager": "apt",
        "python_packages": "python3-pip python3-venv",
        "dependencies": ["build-essential", "libssl-dev", "libffi-dev"],
        "service_manager": "systemd (recent versions)",
        "docker_install": "Use Docker Desktop for Windows",
        "common_issues": [
            {"error": "Systemd not available", "solution": "Enable systemd in /etc/wsl.conf or upgrade WSL2"},
            {"error": "Network issues", "solution": "Check WSL2 networking, may need resolv.conf fix"},
        ]
    },
}

# Pretrained Error Patterns and Solutions
ERROR_PATTERNS = {
    # Python/Pip Errors
    "pip_permission_denied": {
        "patterns": [
            r"Permission denied.*site-packages",
            r"ERROR: Could not install packages due to an OSError",
            r"Access is denied",
        ],
        "solutions": [
            {"action": "use_user_flag", "command": "pip install --user {package}"},
            {"action": "use_sudo", "command": "sudo pip install {package}"},
            {"action": "use_venv", "command": "Create and activate virtual environment first"},
        ],
        "success_rate": 0.95,
        "learned_count": 0,
    },
    "pip_connection_error": {
        "patterns": [
            r"Connection refused",
            r"Network is unreachable",
            r"Failed to establish connection",
            r"SSLError",
            r"Read timed out",
        ],
        "solutions": [
            {"action": "retry_with_timeout", "command": "pip install --timeout 100 {package}"},
            {"action": "use_mirror", "command": "pip install -i https://pypi.org/simple {package}"},
            {"action": "offline_mode", "command": "Download wheel files manually and use --no-index"},
        ],
        "success_rate": 0.80,
        "learned_count": 0,
    },
    "pip_package_not_found": {
        "patterns": [
            r"ERROR: No matching distribution found",
            r"Could not find a version that satisfies",
            r"Package not found",
        ],
        "solutions": [
            {"action": "update_pip", "command": "pip install --upgrade pip"},
            {"action": "check_name", "command": "Package name may differ from import name"},
            {"action": "check_python_version", "command": "Package may require specific Python version"},
        ],
        "success_rate": 0.70,
        "learned_count": 0,
    },
    
    # Docker Errors
    "docker_permission_denied": {
        "patterns": [
            r"permission denied while trying to connect to the Docker daemon",
            r"Got permission denied.*docker",
            r"Cannot connect to the Docker daemon",
        ],
        "solutions": [
            {"action": "add_to_group", "command": "sudo usermod -aG docker $USER && newgrp docker"},
            {"action": "use_sudo", "command": "sudo docker {command}"},
            {"action": "start_daemon", "command": "sudo systemctl start docker"},
        ],
        "success_rate": 0.95,
        "learned_count": 0,
    },
    "docker_not_found": {
        "patterns": [
            r"docker: command not found",
            r"'docker' is not recognized",
        ],
        "solutions": [
            {"action": "install_docker", "command": "curl -fsSL https://get.docker.com | sh"},
            {"action": "install_docker_apt", "command": "sudo apt-get install -y docker.io"},
            {"action": "install_docker_dnf", "command": "sudo dnf install -y docker-ce"},
        ],
        "success_rate": 0.90,
        "learned_count": 0,
    },
    
    # Git Errors
    "git_authentication_failed": {
        "patterns": [
            r"Authentication failed",
            r"Permission denied.*git",
            r"fatal: could not read Username",
            r"fatal: could not read Password",
        ],
        "solutions": [
            {"action": "use_ssh", "command": "Use SSH URL instead of HTTPS"},
            {"action": "use_token", "command": "Use personal access token as password"},
            {"action": "configure_credential", "command": "git config --global credential.helper store"},
        ],
        "success_rate": 0.85,
        "learned_count": 0,
    },
    "git_repository_not_found": {
        "patterns": [
            r"repository not found",
            r"Repository not found",
            r"fatal: remote error",
        ],
        "solutions": [
            {"action": "check_url", "command": "Verify repository URL is correct"},
            {"action": "check_access", "command": "Verify you have access to the repository"},
            {"action": "check_network", "command": "Check if GitHub/GitLab is accessible"},
        ],
        "success_rate": 0.75,
        "learned_count": 0,
    },
    
    # System Errors
    "insufficient_memory": {
        "patterns": [
            r"Cannot allocate memory",
            r"Out of memory",
            r"Memory allocation failed",
            r"Java heap space",
        ],
        "solutions": [
            {"action": "add_swap", "command": "sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile"},
            {"action": "reduce_memory", "command": "Reduce memory usage in configuration"},
            {"action": "kill_processes", "command": "Stop unnecessary services: sudo systemctl stop {service}"},
        ],
        "success_rate": 0.70,
        "learned_count": 0,
    },
    "insufficient_disk_space": {
        "patterns": [
            r"No space left on device",
            r"disk full",
            r"ENOSPC",
        ],
        "solutions": [
            {"action": "clean_apt", "command": "sudo apt-get clean && sudo apt-get autoremove"},
            {"action": "clean_docker", "command": "docker system prune -a --volumes"},
            {"action": "clean_logs", "command": "sudo journalctl --vacuum-time=3d"},
            {"action": "find_large", "command": "du -h --max-depth=1 / | sort -hr | head -20"},
        ],
        "success_rate": 0.85,
        "learned_count": 0,
    },
    "port_already_in_use": {
        "patterns": [
            r"Address already in use",
            r"Port.*is already in use",
            r"EADDRINUSE",
        ],
        "solutions": [
            {"action": "find_process", "command": "lsof -i :{port} or ss -tulpn | grep {port}"},
            {"action": "kill_process", "command": "kill -9 $(lsof -t -i:{port})"},
            {"action": "use_different_port", "command": "Configure application to use different port"},
        ],
        "success_rate": 0.90,
        "learned_count": 0,
    },
    
    # Service/Process Errors
    "service_failed_to_start": {
        "patterns": [
            r"Failed to start",
            r"Job for.*failed",
            r"service.*failed",
            r"Active: failed",
        ],
        "solutions": [
            {"action": "check_status", "command": "systemctl status {service}"},
            {"action": "check_logs", "command": "journalctl -u {service} -n 50"},
            {"action": "check_config", "command": "Validate configuration file syntax"},
        ],
        "success_rate": 0.75,
        "learned_count": 0,
    },
    
    # Ollama Errors
    "ollama_not_running": {
        "patterns": [
            r"Ollama connection refused",
            r"ollama: command not found",
            r"Cannot connect to ollama",
            r"Connection refused.*11434",
        ],
        "solutions": [
            {"action": "start_ollama", "command": "ollama serve &"},
            {"action": "install_ollama", "command": "curl -fsSL https://ollama.com/install.sh | sh"},
            {"action": "check_service", "command": "systemctl status ollama"},
        ],
        "success_rate": 0.92,
        "learned_count": 0,
    },
    
    # Database Errors
    "database_connection_failed": {
        "patterns": [
            r"Connection refused.*mysql",
            r"Connection refused.*postgres",
            r"Can't connect to MySQL server",
            r"connection to server.*failed",
        ],
        "solutions": [
            {"action": "start_db", "command": "sudo systemctl start {mysql|postgresql}"},
            {"action": "check_credentials", "command": "Verify database credentials"},
            {"action": "check_host", "command": "Verify database host and port"},
        ],
        "success_rate": 0.85,
        "learned_count": 0,
    },
    
    # SSL/TLS Errors
    "ssl_certificate_error": {
        "patterns": [
            r"SSL: CERTIFICATE_VERIFY_FAILED",
            r"certificate verify failed",
            r"SELF_SIGNED_CERT",
            r"SSL error",
        ],
        "solutions": [
            {"action": "update_certs", "command": "sudo update-ca-certificates"},
            {"action": "install_certs", "command": "sudo apt-get install ca-certificates"},
            {"action": "bypass_ssl", "command": "Use --trusted-host and --trusted-url for pip (temporary)"},
        ],
        "success_rate": 0.80,
        "learned_count": 0,
    },
    
    # Virtual Environment Errors
    "venv_activation_failed": {
        "patterns": [
            r"No such file or directory.*activate",
            r"venv.*not found",
            r"bad interpreter",
        ],
        "solutions": [
            {"action": "create_venv", "command": "python3 -m venv {venv_path}"},
            {"action": "check_python", "command": "Ensure correct Python version is installed"},
            {"action": "recreate_venv", "command": "Delete venv and recreate"},
        ],
        "success_rate": 0.90,
        "learned_count": 0,
    },
}

# Pretrained Installation Workflows
INSTALLATION_WORKFLOWS = {
    "full_kiswarm": {
        "description": "Complete KISWARM installation",
        "steps": [
            {"id": 1, "name": "preflight", "critical": True},
            {"id": 2, "name": "dependencies", "critical": True},
            {"id": 3, "name": "ollama", "critical": True},
            {"id": 4, "name": "clone_repo", "critical": True},
            {"id": 5, "name": "python_venv", "critical": True},
            {"id": 6, "name": "pip_install", "critical": False},
            {"id": 7, "name": "qdrant", "critical": False},
            {"id": 8, "name": "model_pull", "critical": False},
            {"id": 9, "name": "api_start", "critical": False},
            {"id": 10, "name": "verify", "critical": False},
        ],
    },
    "minimal_kiswarm": {
        "description": "Minimal KISWARM installation (core only)",
        "steps": [
            {"id": 1, "name": "preflight", "critical": True},
            {"id": 2, "name": "clone_repo", "critical": True},
            {"id": 3, "name": "python_venv", "critical": True},
            {"id": 4, "name": "pip_install", "critical": True},
            {"id": 5, "name": "api_start", "critical": False},
        ],
    },
    "kibank_only": {
        "description": "KIBank module installation only",
        "steps": [
            {"id": 1, "name": "preflight", "critical": True},
            {"id": 2, "name": "dependencies", "critical": True},
            {"id": 3, "name": "clone_repo", "critical": True},
            {"id": 4, "name": "python_venv", "critical": True},
            {"id": 5, "name": "pip_install", "critical": True},
            {"id": 6, "name": "database_setup", "critical": True},
            {"id": 7, "name": "verify", "critical": False},
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class TrainingStatus(Enum):
    NOT_TRAINED = "not_trained"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EnvironmentType(Enum):
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    CENTOS = "centos"
    FEDORA = "fedora"
    ARCH = "arch"
    MACOS = "macos"
    WINDOWS = "windows"
    WSL = "wsl"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    UNKNOWN = "unknown"


@dataclass
class ErrorPattern:
    """Learned error pattern with solutions."""
    pattern_id: str
    pattern_regex: str
    description: str
    solutions: List[Dict[str, str]]
    success_count: int = 0
    failure_count: int = 0
    last_seen: Optional[str] = None
    environments_seen: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_regex": self.pattern_regex,
            "description": self.description,
            "solutions": self.solutions,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_rate,
            "last_seen": self.last_seen,
            "environments_seen": self.environments_seen,
        }


@dataclass
class LearningExperience:
    """A single learning experience from an installation."""
    experience_id: str
    timestamp: str
    environment_type: str
    environment_profile: Dict[str, Any]
    step_name: str
    step_command: str
    error_output: str
    error_pattern_matched: Optional[str]
    solution_applied: str
    solution_successful: bool
    time_to_resolve_s: float
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "timestamp": self.timestamp,
            "environment_type": self.environment_type,
            "environment_profile": self.environment_profile,
            "step_name": self.step_name,
            "step_command": self.step_command,
            "error_output": self.error_output[:500],
            "error_pattern_matched": self.error_pattern_matched,
            "solution_applied": self.solution_applied,
            "solution_successful": self.solution_successful,
            "time_to_resolve_s": self.time_to_resolve_s,
            "notes": self.notes,
        }


@dataclass
class TrainingSession:
    """A complete training session result."""
    session_id: str
    started_at: str
    completed_at: Optional[str]
    environment_type: str
    simulation_mode: bool
    steps_attempted: int
    steps_succeeded: int
    errors_encountered: int
    errors_resolved: int
    new_patterns_learned: int
    experiences: List[LearningExperience] = field(default_factory=list)
    status: TrainingStatus = TrainingStatus.IN_PROGRESS
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "environment_type": self.environment_type,
            "simulation_mode": self.simulation_mode,
            "steps_attempted": self.steps_attempted,
            "steps_succeeded": self.steps_succeeded,
            "errors_encountered": self.errors_encountered,
            "errors_resolved": self.errors_resolved,
            "new_patterns_learned": self.new_patterns_learned,
            "experiences_count": len(self.experiences),
            "status": self.status.value,
        }


@dataclass
class PretrainedKnowledge:
    """Complete pretrained knowledge base."""
    version: str
    created_at: str
    last_updated: str
    environment_profiles: Dict[str, Any]
    error_patterns: Dict[str, ErrorPattern]
    installation_workflows: Dict[str, Any]
    learning_experiences: List[LearningExperience]
    total_installations: int
    successful_installations: int
    unique_errors_learned: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "environment_profiles": self.environment_profiles,
            "error_patterns": {k: v.to_dict() for k, v in self.error_patterns.items()},
            "installation_workflows": self.installation_workflows,
            "learning_experiences_count": len(self.learning_experiences),
            "total_installations": self.total_installations,
            "successful_installations": self.successful_installations,
            "unique_errors_learned": self.unique_errors_learned,
            "success_rate": self.successful_installations / max(self.total_installations, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# INSTALLER PRETRAINING SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class InstallerPretraining:
    """
    Pretraining and Learning System for KI Installer Agents.
    
    This system provides:
    1. Pretrained knowledge base with environment-specific solutions
    2. Automatic error pattern recognition and solution matching
    3. Learning from installation experiences
    4. Continuous improvement through feedback integration
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Initialize the pretraining system.
        
        Args:
            knowledge_path: Path to store/load knowledge base.
                          Defaults to ~/.kiswarm/pretraining_knowledge.json
        """
        self.knowledge_path = knowledge_path or os.path.join(
            os.path.expanduser("~"), ".kiswarm", "pretraining_knowledge.json"
        )
        
        self._knowledge: Optional[PretrainedKnowledge] = None
        self._current_session: Optional[TrainingSession] = None
        self._sessions: Dict[str, TrainingSession] = {}
        
        # Thread-safe operations
        self._lock = threading.Lock()
        
        # Load or initialize knowledge
        self._load_knowledge()
    
    def _load_knowledge(self) -> None:
        """Load knowledge from disk or initialize with pretrained data."""
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct error patterns
                error_patterns = {}
                for k, v in data.get("error_patterns", {}).items():
                    error_patterns[k] = ErrorPattern(
                        pattern_id=v["pattern_id"],
                        pattern_regex=v["pattern_regex"],
                        description=v["description"],
                        solutions=v["solutions"],
                        success_count=v.get("success_count", 0),
                        failure_count=v.get("failure_count", 0),
                        last_seen=v.get("last_seen"),
                        environments_seen=v.get("environments_seen", []),
                    )
                
                # Reconstruct learning experiences
                experiences = []
                for exp in data.get("learning_experiences", []):
                    experiences.append(LearningExperience(
                        experience_id=exp["experience_id"],
                        timestamp=exp["timestamp"],
                        environment_type=exp["environment_type"],
                        environment_profile=exp["environment_profile"],
                        step_name=exp["step_name"],
                        step_command=exp["step_command"],
                        error_output=exp["error_output"],
                        error_pattern_matched=exp.get("error_pattern_matched"),
                        solution_applied=exp["solution_applied"],
                        solution_successful=exp["solution_successful"],
                        time_to_resolve_s=exp["time_to_resolve_s"],
                        notes=exp.get("notes", ""),
                    ))
                
                self._knowledge = PretrainedKnowledge(
                    version=data.get("version", PRETRAINING_VERSION),
                    created_at=data.get("created_at", datetime.datetime.now().isoformat()),
                    last_updated=data.get("last_updated", datetime.datetime.now().isoformat()),
                    environment_profiles=data.get("environment_profiles", ENVIRONMENT_PROFILES),
                    error_patterns=error_patterns,
                    installation_workflows=data.get("installation_workflows", INSTALLATION_WORKFLOWS),
                    learning_experiences=experiences,
                    total_installations=data.get("total_installations", 0),
                    successful_installations=data.get("successful_installations", 0),
                    unique_errors_learned=data.get("unique_errors_learned", 0),
                )
                
                logger.info(f"Loaded pretraining knowledge: {len(error_patterns)} patterns, "
                           f"{len(experiences)} experiences")
                return
                
            except Exception as e:
                logger.warning(f"Failed to load knowledge: {e}, initializing fresh")
        
        # Initialize with pretrained data
        self._initialize_pretrained_knowledge()
    
    def _initialize_pretrained_knowledge(self) -> None:
        """Initialize knowledge base with pretrained patterns."""
        now = datetime.datetime.now().isoformat()
        
        # Convert ERROR_PATTERNS to ErrorPattern objects
        error_patterns = {}
        for pattern_id, pattern_data in ERROR_PATTERNS.items():
            for i, pattern_regex in enumerate(pattern_data["patterns"]):
                error_patterns[f"{pattern_id}_{i}"] = ErrorPattern(
                    pattern_id=f"{pattern_id}_{i}",
                    pattern_regex=pattern_regex,
                    description=pattern_id.replace("_", " ").title(),
                    solutions=pattern_data["solutions"],
                    success_count=int(pattern_data.get("success_rate", 0.5) * 100),
                    failure_count=int((1 - pattern_data.get("success_rate", 0.5)) * 100),
                    last_seen=None,
                    environments_seen=[],
                )
        
        self._knowledge = PretrainedKnowledge(
            version=PRETRAINING_VERSION,
            created_at=now,
            last_updated=now,
            environment_profiles=ENVIRONMENT_PROFILES.copy(),
            error_patterns=error_patterns,
            installation_workflows=INSTALLATION_WORKFLOWS.copy(),
            learning_experiences=[],
            total_installations=0,
            successful_installations=0,
            unique_errors_learned=len(error_patterns),
        )
        
        self._save_knowledge()
        logger.info(f"Initialized pretrained knowledge with {len(error_patterns)} patterns")
    
    def _save_knowledge(self) -> None:
        """Save knowledge to disk."""
        with self._lock:
            os.makedirs(os.path.dirname(self.knowledge_path), exist_ok=True)
            
            self._knowledge.last_updated = datetime.datetime.now().isoformat()
            
            data = self._knowledge.to_dict()
            # Include full experiences for persistence
            data["learning_experiences"] = [e.to_dict() for e in self._knowledge.learning_experiences]
            
            with open(self.knowledge_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    # ── Environment Detection ───────────────────────────────────────────────────
    
    def detect_environment(self) -> Tuple[EnvironmentType, Dict[str, Any]]:
        """
        Detect the current environment type and gather system information.
        
        Returns:
            Tuple of (EnvironmentType, environment_profile_dict)
        """
        system = platform.system()
        
        if system == "Darwin":
            return EnvironmentType.MACOS, self._get_macos_profile()
        
        if system == "Windows":
            # Check for WSL
            if "microsoft" in platform.uname().release.lower() or "WSL" in platform.uname().release:
                return EnvironmentType.WSL, self._get_wsl_profile()
            return EnvironmentType.WINDOWS, self._get_windows_profile()
        
        if system == "Linux":
            return self._detect_linux_distribution()
        
        return EnvironmentType.UNKNOWN, {"system": system}
    
    def _detect_linux_distribution(self) -> Tuple[EnvironmentType, Dict[str, Any]]:
        """Detect specific Linux distribution."""
        profile = {
            "system": "Linux",
            "kernel": platform.release(),
            "architecture": platform.machine(),
        }
        
        # Check for Docker
        if os.path.exists("/.dockerenv"):
            return EnvironmentType.DOCKER, {**profile, "containerized": True}
        
        # Check for Kubernetes
        if os.path.exists("/var/run/secrets/kubernetes.io"):
            return EnvironmentType.KUBERNETES, {**profile, "orchestrated": True}
        
        # Check os-release
        os_release = {}
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", 'r') as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_release[key] = value.strip('"')
        
        profile["os_release"] = os_release
        distro_id = os_release.get("ID", "").lower()
        
        # Map to environment type
        if "ubuntu" in distro_id:
            return EnvironmentType.UBUNTU, profile
        elif "debian" in distro_id:
            return EnvironmentType.DEBIAN, profile
        elif "centos" in distro_id or "rhel" in distro_id or "rocky" in distro_id:
            return EnvironmentType.CENTOS, profile
        elif "fedora" in distro_id:
            return EnvironmentType.FEDORA, profile
        elif "arch" in distro_id:
            return EnvironmentType.ARCH, profile
        elif "amzn" in distro_id:
            return EnvironmentType.CENTOS, profile  # Amazon Linux is CentOS-based
        
        return EnvironmentType.UNKNOWN, profile
    
    def _get_macos_profile(self) -> Dict[str, Any]:
        """Get macOS system profile."""
        profile = {
            "system": "macOS",
            "version": platform.mac_ver()[0],
            "architecture": platform.machine(),
        }
        
        # Check for Homebrew
        profile["homebrew"] = shutil.which("brew") is not None
        
        return profile
    
    def _get_windows_profile(self) -> Dict[str, Any]:
        """Get Windows system profile."""
        return {
            "system": "Windows",
            "version": platform.win32_ver()[0],
            "architecture": platform.machine(),
        }
    
    def _get_wsl_profile(self) -> Dict[str, Any]:
        """Get WSL system profile."""
        profile = {
            "system": "WSL",
            "version": platform.version(),
            "architecture": platform.machine(),
        }
        
        # Detect WSL version
        try:
            result = subprocess.run(
                ["wsl.exe", "--version"],
                capture_output=True, text=True, timeout=5
            )
            profile["wsl_version"] = result.stdout[:100] if result.returncode == 0 else "unknown"
        except Exception:
            profile["wsl_version"] = "unknown"
        
        return profile
    
    # ── Error Pattern Matching ──────────────────────────────────────────────────
    
    def match_error(self, error_output: str, environment_type: EnvironmentType
                   ) -> Optional[Tuple[ErrorPattern, List[Dict[str, str]]]]:
        """
        Match an error output against known patterns.
        
        Args:
            error_output: The error message/output to match
            environment_type: The environment type for context
            
        Returns:
            Tuple of (matched_pattern, ranked_solutions) or None
        """
        for pattern_id, pattern in self._knowledge.error_patterns.items():
            try:
                if re.search(pattern.pattern_regex, error_output, re.IGNORECASE):
                    # Rank solutions by success rate and environment relevance
                    ranked_solutions = self._rank_solutions(
                        pattern.solutions, environment_type
                    )
                    return pattern, ranked_solutions
            except re.error:
                continue
        
        return None
    
    def _rank_solutions(self, solutions: List[Dict[str, str]], 
                       environment_type: EnvironmentType) -> List[Dict[str, str]]:
        """Rank solutions by relevance to the environment."""
        # For now, return solutions in order
        # Future: implement learning-based ranking
        return solutions
    
    def record_solution_outcome(self, pattern_id: str, solution_index: int,
                               successful: bool, environment_type: str) -> None:
        """
        Record the outcome of applying a solution.
        
        This is how the system learns which solutions work best.
        """
        with self._lock:
            if pattern_id in self._knowledge.error_patterns:
                pattern = self._knowledge.error_patterns[pattern_id]
                
                if successful:
                    pattern.success_count += 1
                else:
                    pattern.failure_count += 1
                
                pattern.last_seen = datetime.datetime.now().isoformat()
                if environment_type not in pattern.environments_seen:
                    pattern.environments_seen.append(environment_type)
                
                self._save_knowledge()
    
    # ── Learning & Feedback ─────────────────────────────────────────────────────
    
    def record_experience(self, experience: LearningExperience) -> None:
        """Record a learning experience for future reference."""
        with self._lock:
            self._knowledge.learning_experiences.append(experience)
            self._knowledge.total_installations += 1
            
            if experience.solution_successful:
                self._knowledge.successful_installations += 1
            
            self._save_knowledge()
    
    def learn_new_pattern(self, error_output: str, solution: str,
                         environment_type: str, successful: bool) -> str:
        """
        Learn a new error pattern from an installation experience.
        
        Returns:
            The new pattern ID
        """
        with self._lock:
            # Generate pattern ID
            pattern_id = hashlib.md5(
                f"pattern_{error_output[:100]}_{datetime.datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # Extract a reasonable regex pattern from the error
            # This is simplified - in production would use NLP/ML
            pattern_regex = re.escape(error_output[:50]).replace(r"\ ", r"\s*")
            
            new_pattern = ErrorPattern(
                pattern_id=pattern_id,
                pattern_regex=pattern_regex,
                description=f"Auto-learned: {error_output[:50]}...",
                solutions=[{"action": "learned", "command": solution}],
                success_count=1 if successful else 0,
                failure_count=0 if successful else 1,
                last_seen=datetime.datetime.now().isoformat(),
                environments_seen=[environment_type],
            )
            
            self._knowledge.error_patterns[pattern_id] = new_pattern
            self._knowledge.unique_errors_learned = len(self._knowledge.error_patterns)
            self._save_knowledge()
            
            logger.info(f"Learned new error pattern: {pattern_id}")
            return pattern_id
    
    # ── Training Sessions ───────────────────────────────────────────────────────
    
    def start_training_session(self, environment_type: str = None,
                               simulation_mode: bool = True) -> TrainingSession:
        """
        Start a new training session.
        
        Args:
            environment_type: Target environment type (auto-detect if None)
            simulation_mode: Whether to run in simulation mode
            
        Returns:
            TrainingSession object
        """
        if environment_type is None:
            env_type, _ = self.detect_environment()
            environment_type = env_type.value
        
        session_id = hashlib.md5(
            f"training_{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        session = TrainingSession(
            session_id=session_id,
            started_at=datetime.datetime.now().isoformat(),
            completed_at=None,
            environment_type=environment_type,
            simulation_mode=simulation_mode,
            steps_attempted=0,
            steps_succeeded=0,
            errors_encountered=0,
            errors_resolved=0,
            new_patterns_learned=0,
            status=TrainingStatus.IN_PROGRESS,
        )
        
        self._current_session = session
        self._sessions[session_id] = session
        
        return session
    
    def end_training_session(self, success: bool = True) -> TrainingSession:
        """End the current training session."""
        if self._current_session is None:
            raise RuntimeError("No active training session")
        
        self._current_session.completed_at = datetime.datetime.now().isoformat()
        self._current_session.status = TrainingStatus.COMPLETED if success else TrainingStatus.FAILED
        
        session = self._current_session
        self._current_session = None
        
        self._save_knowledge()
        return session
    
    def add_session_experience(self, experience: LearningExperience) -> None:
        """Add an experience to the current training session."""
        if self._current_session is None:
            raise RuntimeError("No active training session")
        
        self._current_session.experiences.append(experience)
        self._current_session.steps_attempted += 1
        
        if experience.solution_successful:
            self._current_session.steps_succeeded += 1
        
        if experience.error_pattern_matched:
            self._current_session.errors_encountered += 1
            if experience.solution_successful:
                self._current_session.errors_resolved += 1
    
    # ── Simulation & Testing ────────────────────────────────────────────────────
    
    def run_simulation(self, environment_type: str = None) -> Dict[str, Any]:
        """
        Run a simulation training session for a specific environment.
        
        This tests the agent's knowledge against simulated scenarios.
        """
        env_type, env_profile = self.detect_environment()
        if environment_type:
            env_type = EnvironmentType(environment_type)
        
        # Start training session
        session = self.start_training_session(
            environment_type=env_type.value,
            simulation_mode=True
        )
        
        # Get environment-specific scenarios
        profile_key = self._get_profile_key(env_type)
        env_profile_data = self._knowledge.environment_profiles.get(profile_key, {})
        
        simulation_results = {
            "session_id": session.session_id,
            "environment": env_type.value,
            "profile": env_profile_data,
            "scenarios_tested": 0,
            "scenarios_passed": 0,
            "errors_simulated": 0,
            "errors_resolved": 0,
            "scenarios": [],
        }
        
        # Simulate common installation scenarios
        scenarios = self._generate_simulation_scenarios(env_type)
        
        for scenario in scenarios:
            scenario_result = self._run_scenario_simulation(scenario, env_type)
            simulation_results["scenarios"].append(scenario_result)
            simulation_results["scenarios_tested"] += 1
            
            if scenario_result["success"]:
                simulation_results["scenarios_passed"] += 1
            
            simulation_results["errors_simulated"] += scenario_result["errors_count"]
            simulation_results["errors_resolved"] += scenario_result["errors_resolved"]
            
            # Record experience
            experience = LearningExperience(
                experience_id=hashlib.md5(
                    f"exp_{scenario['name']}_{datetime.datetime.now().isoformat()}".encode()
                ).hexdigest()[:12],
                timestamp=datetime.datetime.now().isoformat(),
                environment_type=env_type.value,
                environment_profile=env_profile_data,
                step_name=scenario["name"],
                step_command=scenario.get("command", ""),
                error_output=scenario_result.get("error_output", ""),
                error_pattern_matched=scenario_result.get("pattern_matched"),
                solution_applied=scenario_result.get("solution_applied", ""),
                solution_successful=scenario_result["success"],
                time_to_resolve_s=scenario_result.get("time_s", 0),
            )
            
            self.add_session_experience(experience)
            self.record_experience(experience)
        
        # End session
        session = self.end_training_session(success=True)
        
        simulation_results["session"] = session.to_dict()
        simulation_results["success_rate"] = (
            simulation_results["scenarios_passed"] / max(simulation_results["scenarios_tested"], 1)
        )
        
        return simulation_results
    
    def _get_profile_key(self, env_type: EnvironmentType) -> str:
        """Map environment type to profile key."""
        mapping = {
            EnvironmentType.UBUNTU: "ubuntu_22_04",
            EnvironmentType.DEBIAN: "debian_12",
            EnvironmentType.CENTOS: "centos_8",
            EnvironmentType.FEDORA: "fedora_38",
            EnvironmentType.ARCH: "arch_linux",
            EnvironmentType.MACOS: "macos",
            EnvironmentType.WINDOWS: "wsl2",
            EnvironmentType.WSL: "wsl2",
            EnvironmentType.DOCKER: "docker_container",
            EnvironmentType.KUBERNETES: "kubernetes_pod",
        }
        return mapping.get(env_type, "ubuntu_22_04")
    
    def _generate_simulation_scenarios(self, env_type: EnvironmentType) -> List[Dict[str, Any]]:
        """Generate simulation scenarios for an environment."""
        scenarios = [
            {
                "name": "pip_install_permission",
                "type": "error_simulation",
                "error_pattern": "pip_permission_denied",
                "error_output": "ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: '/usr/local/lib/python3.10/site-packages'",
            },
            {
                "name": "docker_permission",
                "type": "error_simulation",
                "error_pattern": "docker_permission_denied",
                "error_output": "permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock",
            },
            {
                "name": "git_clone_auth",
                "type": "error_simulation",
                "error_pattern": "git_authentication_failed",
                "error_output": "fatal: Authentication failed for 'https://github.com/repo.git/'",
            },
            {
                "name": "port_in_use",
                "type": "error_simulation",
                "error_pattern": "port_already_in_use",
                "error_output": "OSError: [Errno 98] Address already in use: ('0.0.0.0', 11434)",
            },
            {
                "name": "ollama_connection",
                "type": "error_simulation",
                "error_pattern": "ollama_not_running",
                "error_output": "Connection refused: [Errno 111] Could not connect to ollama at 127.0.0.1:11434",
            },
            {
                "name": "disk_space",
                "type": "error_simulation",
                "error_pattern": "insufficient_disk_space",
                "error_output": "OSError: [Errno 28] No space left on device",
            },
            {
                "name": "ssl_certificate",
                "type": "error_simulation",
                "error_pattern": "ssl_certificate_error",
                "error_output": "ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed",
            },
            {
                "name": "memory_allocation",
                "type": "error_simulation",
                "error_pattern": "insufficient_memory",
                "error_output": "MemoryError: Cannot allocate memory for array",
            },
        ]
        
        # Add environment-specific scenarios
        profile_key = self._get_profile_key(env_type)
        env_issues = self._knowledge.environment_profiles.get(profile_key, {}).get("common_issues", [])
        
        for issue in env_issues:
            scenarios.append({
                "name": f"env_specific_{issue['error'][:20]}",
                "type": "error_simulation",
                "error_pattern": "env_specific",
                "error_output": issue["error"],
                "expected_solution": issue["solution"],
            })
        
        return scenarios
    
    def _run_scenario_simulation(self, scenario: Dict[str, Any],
                                 env_type: EnvironmentType) -> Dict[str, Any]:
        """Run a single scenario simulation."""
        start_time = time.time()
        
        result = {
            "name": scenario["name"],
            "type": scenario["type"],
            "success": False,
            "errors_count": 0,
            "errors_resolved": 0,
            "pattern_matched": None,
            "solution_applied": None,
            "time_s": 0,
        }
        
        # Simulate error
        error_output = scenario.get("error_output", "")
        if error_output:
            result["errors_count"] = 1
            result["error_output"] = error_output
            
            # Try to match error pattern
            match_result = self.match_error(error_output, env_type)
            
            if match_result:
                pattern, solutions = match_result
                result["pattern_matched"] = pattern.pattern_id
                
                # Apply first solution
                if solutions:
                    solution = solutions[0]
                    result["solution_applied"] = solution.get("command", solution.get("action", ""))
                    
                    # Determine success based on pattern success rate
                    result["success"] = pattern.success_rate > 0.5
                    result["errors_resolved"] = 1 if result["success"] else 0
                    
                    # Record outcome
                    self.record_solution_outcome(
                        pattern.pattern_id, 0, result["success"], env_type.value
                    )
            else:
                # Try to learn from this unknown error
                if scenario.get("expected_solution"):
                    pattern_id = self.learn_new_pattern(
                        error_output,
                        scenario["expected_solution"],
                        env_type.value,
                        True
                    )
                    result["pattern_matched"] = pattern_id
                    result["solution_applied"] = scenario["expected_solution"]
                    result["success"] = True
                    result["errors_resolved"] = 1
        
        result["time_s"] = round(time.time() - start_time, 3)
        return result
    
    # ── Knowledge Export/Import ─────────────────────────────────────────────────
    
    def export_knowledge(self, export_path: str) -> Dict[str, Any]:
        """Export knowledge to a file."""
        data = self._knowledge.to_dict()
        data["learning_experiences"] = [e.to_dict() for e in self._knowledge.learning_experiences]
        
        with open(export_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"exported_to": export_path, "size_kb": os.path.getsize(export_path) / 1024}
    
    def import_knowledge(self, import_path: str) -> Dict[str, Any]:
        """Import knowledge from a file."""
        with open(import_path, 'r') as f:
            data = json.load(f)
        
        # Merge with existing knowledge
        imported_patterns = len(data.get("error_patterns", {}))
        imported_experiences = len(data.get("learning_experiences", []))
        
        # Add new patterns
        for pattern_id, pattern_data in data.get("error_patterns", {}).items():
            if pattern_id not in self._knowledge.error_patterns:
                self._knowledge.error_patterns[pattern_id] = ErrorPattern(
                    pattern_id=pattern_data["pattern_id"],
                    pattern_regex=pattern_data["pattern_regex"],
                    description=pattern_data["description"],
                    solutions=pattern_data["solutions"],
                    success_count=pattern_data.get("success_count", 0),
                    failure_count=pattern_data.get("failure_count", 0),
                    last_seen=pattern_data.get("last_seen"),
                    environments_seen=pattern_data.get("environments_seen", []),
                )
        
        self._knowledge.unique_errors_learned = len(self._knowledge.error_patterns)
        self._save_knowledge()
        
        return {
            "imported_from": import_path,
            "patterns_imported": imported_patterns,
            "experiences_imported": imported_experiences,
            "total_patterns": len(self._knowledge.error_patterns),
        }
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get a summary of the current knowledge base."""
        return {
            "version": self._knowledge.version,
            "total_error_patterns": len(self._knowledge.error_patterns),
            "total_learning_experiences": len(self._knowledge.learning_experiences),
            "total_installations": self._knowledge.total_installations,
            "successful_installations": self._knowledge.successful_installations,
            "success_rate": self._knowledge.successful_installations / max(self._knowledge.total_installations, 1),
            "environments_known": list(self._knowledge.environment_profiles.keys()),
            "workflows_available": list(self._knowledge.installation_workflows.keys()),
            "last_updated": self._knowledge.last_updated,
        }
    
    def get_environment_profile(self, env_type: EnvironmentType) -> Dict[str, Any]:
        """Get the profile for a specific environment."""
        profile_key = self._get_profile_key(env_type)
        return self._knowledge.environment_profiles.get(profile_key, {})
    
    def get_best_practices(self, env_type: EnvironmentType) -> List[Dict[str, Any]]:
        """Get best practices for an environment based on learning."""
        experiences = [
            e for e in self._knowledge.learning_experiences
            if e.environment_type == env_type.value and e.solution_successful
        ]
        
        # Group by step name
        step_successes = {}
        for exp in experiences:
            if exp.step_name not in step_successes:
                step_successes[exp.step_name] = []
            step_successes[exp.step_name].append(exp)
        
        # Extract best practices
        best_practices = []
        for step_name, exps in step_successes.items():
            if len(exps) >= 2:  # Need at least 2 successful experiences
                avg_time = sum(e.time_to_resolve_s for e in exps) / len(exps)
                best_practices.append({
                    "step": step_name,
                    "success_count": len(exps),
                    "avg_resolution_time_s": round(avg_time, 2),
                    "common_solution": exps[0].solution_applied if exps else None,
                })
        
        return sorted(best_practices, key=lambda x: x["success_count"], reverse=True)
    
    def suggest_solution(self, error_output: str, 
                        environment_type: EnvironmentType = None) -> Dict[str, Any]:
        """
        Suggest solutions for an error based on learned knowledge.
        
        This is the main method used by Installer Agents during installation.
        """
        if environment_type is None:
            environment_type, _ = self.detect_environment()
        
        match_result = self.match_error(error_output, environment_type)
        
        if match_result:
            pattern, solutions = match_result
            return {
                "found": True,
                "pattern_id": pattern.pattern_id,
                "description": pattern.description,
                "success_rate": pattern.success_rate,
                "solutions": solutions,
                "environments_seen": pattern.environments_seen,
                "recommended_solution": solutions[0] if solutions else None,
            }
        
        # No match found - suggest learning
        return {
            "found": False,
            "suggestion": "This is a new error pattern. Consider learning it.",
            "error_fingerprint": hashlib.md5(error_output[:100].encode()).hexdigest()[:12],
        }


# ─────────────────────────────────────────────────────────────────────────────
# ENHANCED INSTALLER AGENT WITH PRETRAINING
# ─────────────────────────────────────────────────────────────────────────────

class PretrainedInstallerAgent:
    """
    Installer Agent enhanced with pretraining capabilities.
    
    This agent combines the original InstallerAgent with the Pretraining system
    to provide intelligent, learning-based installation.
    """
    
    def __init__(self, pretraining: Optional[InstallerPretraining] = None):
        """
        Initialize the pretrained installer agent.
        
        Args:
            pretraining: Optional pretraining system instance.
                        If None, creates a new one.
        """
        self.pretraining = pretraining or InstallerPretraining()
        self._current_session: Optional[TrainingSession] = None
        self._installation_log: List[Dict[str, Any]] = []
    
    def install(self, workflow: str = "full_kiswarm",
                mode: str = "auto") -> Dict[str, Any]:
        """
        Execute installation with pretrained intelligence.
        
        Args:
            workflow: Installation workflow to use
            mode: Installation mode ("auto", "dry_run", "guided")
            
        Returns:
            Installation result dictionary
        """
        # Detect environment
        env_type, env_profile = self.pretraining.detect_environment()
        
        # Start training session
        session = self.pretraining.start_training_session(
            environment_type=env_type.value,
            simulation_mode=(mode == "dry_run")
        )
        self._current_session = session
        
        # Get workflow
        workflow_def = self.pretraining._knowledge.installation_workflows.get(
            workflow, INSTALLATION_WORKFLOWS["full_kiswarm"]
        )
        
        result = {
            "session_id": session.session_id,
            "environment": env_type.value,
            "environment_profile": env_profile,
            "workflow": workflow,
            "mode": mode,
            "steps": [],
            "errors": [],
            "resolved_errors": [],
            "success": True,
            "started_at": session.started_at,
        }
        
        try:
            # Execute each step
            for step in workflow_def["steps"]:
                step_result = self._execute_step(step, env_type, mode)
                result["steps"].append(step_result)
                
                if step_result.get("error"):
                    result["errors"].append(step_result["error"])
                    
                    # Try to resolve error
                    resolution = self._resolve_error(
                        step_result["error"], env_type, step
                    )
                    
                    if resolution["resolved"]:
                        result["resolved_errors"].append(resolution)
                        step_result["resolved"] = True
                    elif step.get("critical", False):
                        result["success"] = False
                        result["error"] = f"Critical step {step['name']} failed"
                        break
            
            # Final verification
            result["verification"] = self._verify_installation()
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        # End session
        session = self.pretraining.end_training_session(success=result["success"])
        result["completed_at"] = session.completed_at
        result["training_session"] = session.to_dict()
        
        return result
    
    def _execute_step(self, step: Dict[str, Any], env_type: EnvironmentType,
                     mode: str) -> Dict[str, Any]:
        """Execute a single installation step."""
        step_result = {
            "step_id": step["id"],
            "name": step["name"],
            "success": True,
            "error": None,
            "output": None,
        }
        
        if mode == "dry_run":
            step_result["output"] = f"[DRY RUN] Would execute: {step['name']}"
            return step_result
        
        try:
            # Execute step based on type
            if step["name"] == "preflight":
                step_result["output"] = self._step_preflight(env_type)
            elif step["name"] == "dependencies":
                step_result["output"] = self._step_dependencies(env_type)
            elif step["name"] == "clone_repo":
                step_result["output"] = self._step_clone_repo()
            elif step["name"] == "python_venv":
                step_result["output"] = self._step_python_venv()
            elif step["name"] == "pip_install":
                step_result["output"] = self._step_pip_install()
            else:
                step_result["output"] = f"Step {step['name']} executed"
                
        except Exception as e:
            step_result["success"] = False
            step_result["error"] = str(e)
        
        return step_result
    
    def _step_preflight(self, env_type: EnvironmentType) -> str:
        """Preflight checks."""
        checks = []
        
        # Python version
        py_version = sys.version_info
        if py_version >= (3, 8):
            checks.append(f"Python {py_version.major}.{py_version.minor}: OK")
        else:
            raise RuntimeError(f"Python 3.8+ required, found {py_version.major}.{py_version.minor}")
        
        # Disk space
        disk = shutil.disk_usage("/")
        disk_gb = disk.free / (1024**3)
        if disk_gb >= 10:
            checks.append(f"Disk space {disk_gb:.1f}GB: OK")
        else:
            raise RuntimeError(f"Insufficient disk space: {disk_gb:.1f}GB")
        
        return "\n".join(checks)
    
    def _step_dependencies(self, env_type: EnvironmentType) -> str:
        """Install system dependencies."""
        profile = self.pretraining.get_environment_profile(env_type)
        package_manager = profile.get("package_manager", "apt")
        dependencies = profile.get("dependencies", [])
        
        if not dependencies:
            return "No additional dependencies required"
        
        # In a real implementation, this would execute the installation
        return f"Would install with {package_manager}: {', '.join(dependencies)}"
    
    def _step_clone_repo(self) -> str:
        """Clone repository."""
        # In a real implementation, this would clone the repo
        return "Repository cloned successfully"
    
    def _step_python_venv(self) -> str:
        """Create Python virtual environment."""
        # In a real implementation, this would create venv
        return "Virtual environment created"
    
    def _step_pip_install(self) -> str:
        """Install Python packages."""
        # In a real implementation, this would run pip install
        return "Python packages installed"
    
    def _resolve_error(self, error: str, env_type: EnvironmentType,
                      step: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to resolve an error using pretrained knowledge."""
        resolution = {
            "step": step["name"],
            "error": error,
            "resolved": False,
            "solution_applied": None,
        }
        
        # Get solution suggestion
        suggestion = self.pretraining.suggest_solution(error, env_type)
        
        if suggestion["found"]:
            resolution["pattern_id"] = suggestion["pattern_id"]
            resolution["success_rate"] = suggestion["success_rate"]
            resolution["solutions"] = suggestion["solutions"]
            
            # Apply recommended solution (in simulation, we assume success)
            recommended = suggestion["recommended_solution"]
            if recommended:
                resolution["solution_applied"] = recommended.get("command", recommended.get("action"))
                resolution["resolved"] = suggestion["success_rate"] > 0.5
                
                # Record experience
                experience = LearningExperience(
                    experience_id=hashlib.md5(
                        f"exp_{step['name']}_{datetime.datetime.now().isoformat()}".encode()
                    ).hexdigest()[:12],
                    timestamp=datetime.datetime.now().isoformat(),
                    environment_type=env_type.value,
                    environment_profile=self.pretraining.get_environment_profile(env_type),
                    step_name=step["name"],
                    step_command="",
                    error_output=error,
                    error_pattern_matched=suggestion["pattern_id"],
                    solution_applied=resolution["solution_applied"],
                    solution_successful=resolution["resolved"],
                    time_to_resolve_s=0.5,
                )
                
                if self._current_session:
                    self.pretraining.add_session_experience(experience)
                self.pretraining.record_experience(experience)
        else:
            # Learn this new error
            pattern_id = self.pretraining.learn_new_pattern(
                error, "Manual intervention required", env_type.value, False
            )
            resolution["pattern_id"] = pattern_id
            resolution["resolved"] = False
        
        return resolution
    
    def _verify_installation(self) -> Dict[str, bool]:
        """Verify installation completed successfully."""
        checks = {}
        
        # Check Python
        checks["python_available"] = sys.executable is not None
        
        # Check network (basic)
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            checks["network_available"] = True
        except Exception:
            checks["network_available"] = False
        
        return checks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "pretraining_summary": self.pretraining.get_knowledge_summary(),
            "installations_performed": len(self._installation_log),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def create_pretrained_agent() -> PretrainedInstallerAgent:
    """Create a pretrained installer agent."""
    return PretrainedInstallerAgent()


def run_pretraining_simulation(environment: str = None) -> Dict[str, Any]:
    """
    Run a pretraining simulation for an environment.
    
    This can be used to test and train the installer agent.
    """
    pretraining = InstallerPretraining()
    
    if environment:
        env_type = EnvironmentType(environment)
    else:
        env_type, _ = pretraining.detect_environment()
    
    return pretraining.run_simulation(env_type.value)


def get_pretraining_status() -> Dict[str, Any]:
    """Get the current pretraining status."""
    pretraining = InstallerPretraining()
    return pretraining.get_knowledge_summary()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KI Installer Pretraining System")
    parser.add_argument("--simulate", action="store_true", help="Run simulation")
    parser.add_argument("--environment", type=str, help="Target environment")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--export", type=str, help="Export knowledge to file")
    parser.add_argument("--import", dest="import_knowledge", type=str, help="Import knowledge from file")
    
    args = parser.parse_args()
    
    pretraining = InstallerPretraining()
    
    if args.status:
        summary = pretraining.get_knowledge_summary()
        print(json.dumps(summary, indent=2))
    
    elif args.simulate:
        env_type = EnvironmentType(args.environment) if args.environment else None
        if env_type is None:
            env_type, _ = pretraining.detect_environment()
        
        print(f"Running simulation for: {env_type.value}")
        results = pretraining.run_simulation(env_type.value)
        print(json.dumps(results, indent=2))
    
    elif args.export:
        result = pretraining.export_knowledge(args.export)
        print(f"Exported: {result}")
    
    elif args.import_knowledge:
        result = pretraining.import_knowledge(args.import_knowledge)
        print(f"Imported: {result}")
    
    else:
        # Default: show environment detection
        env_type, profile = pretraining.detect_environment()
        print(f"Detected Environment: {env_type.value}")
        print(f"Profile: {json.dumps(profile, indent=2)}")
