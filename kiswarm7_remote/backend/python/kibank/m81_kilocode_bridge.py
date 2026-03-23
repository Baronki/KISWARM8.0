"""
M81: KiloCode Parallel Safety Bridge
====================================

Bidirectional communication bridge between KISWARM and KiloCode CLI.
Acts as a zero-API safety net for KISWARM scouts and agents.

Author: KISWARM Team
Version: 6.4.0-LIBERATED
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Union, runtime_checkable
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KiloCodeBridge")


class BridgeStatus(Enum):
    """Status of the KiloCode bridge connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    BUSY = "busy"


class MessageType(Enum):
    """Types of messages for bridge communication."""
    CODE_REVIEW = "code_review"
    DEBUG_REQUEST = "debug_request"
    SECURITY_SCAN = "security_scan"
    GENERATE_CODE = "generate_code"
    FEEDBACK = "feedback"
    WARNING = "warning"
    ERROR_REPORT = "error_report"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 100
    EMERGENCY = 1000


@dataclass
class BridgeMessage:
    """Message structure for bridge communication."""
    message_type: MessageType
    content: Dict[str, Any]
    source: str
    target: str
    priority: Priority = Priority.NORMAL
    message_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}-{id(object())}".encode()
    ).hexdigest()[:16])
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_type": self.message_type.value,
            "content": self.content,
            "source": self.source,
            "target": self.target,
            "priority": self.priority.value,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
        }


@dataclass
class KiloCodeConfig:
    """Configuration for KiloCode bridge."""
    npm_package: str = "@kilocode/cli"
    npx_package: str = "@kilocode/cli"
    install_globally: bool = False
    auto_install: bool = True
    installed_version: str = "7.0.47"
    bridge_name: str = "kiswarm-kilocode-bridge"
    max_queue_size: int = 1000
    enable_safety_net: bool = True
    fallback_on_error: bool = True
    autonomous_mode: bool = False
    working_directory: Optional[str] = None


class KiloCodeBridge:
    """Main bidirectional bridge between KISWARM and KiloCode CLI."""
    
    def __init__(self, config: Optional[KiloCodeConfig] = None):
        self.config = config or KiloCodeConfig()
        self._status = BridgeStatus.DISCONNECTED
        self._running = False
        self._last_heartbeat = time.time()
        
    @property
    def status(self) -> BridgeStatus:
        return self._status
    
    @property
    def is_connected(self) -> bool:
        return self._status == BridgeStatus.CONNECTED
    
    def is_installed(self) -> bool:
        """Check if KiloCode CLI is available."""
        try:
            result = subprocess.run(
                ["npx", "@kilocode/cli", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def start(self) -> bool:
        """Start the bridge connection."""
        if self._running:
            return True
        
        if not self.is_installed():
            logger.warning("KiloCode CLI not available")
            self._status = BridgeStatus.ERROR
            return False
        
        self._running = True
        self._status = BridgeStatus.CONNECTED
        logger.info(f"KiloCode bridge started")
        return True
    
    def stop(self) -> None:
        """Stop the bridge connection."""
        self._running = False
        self._status = BridgeStatus.DISCONNECTED
        logger.info("KiloCode bridge stopped")
    
    def execute_kilo_command(
        self,
        command: str,
        auto_mode: bool = False,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """Execute a KiloCode CLI command."""
        if not self.is_installed():
            return {"success": False, "error": "KiloCode CLI not available"}
        
        cmd = ["npx", "@kilocode/cli"]
        if auto_mode or self.config.autonomous_mode:
            cmd.append("--auto")
        cmd.extend(["run", command])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.config.working_directory or os.getcwd(),
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report."""
        return {
            "bridge_status": self._status.value,
            "kilocode_installed": self.is_installed(),
            "kilocode_version": self.config.installed_version,
            "running": self._running,
            "config": {
                "safety_net_enabled": self.config.enable_safety_net,
                "autonomous_mode": self.config.autonomous_mode,
                "fallback_on_error": self.config.fallback_on_error,
            }
        }


# Singleton
_bridge_instance: Optional[KiloCodeBridge] = None


def get_kilocode_bridge(config: Optional[KiloCodeConfig] = None) -> KiloCodeBridge:
    """Get or create the global KiloCode bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = KiloCodeBridge(config)
    return _bridge_instance


def initialize_kilocode_bridge(
    auto_start: bool = True,
    config: Optional[KiloCodeConfig] = None
) -> KiloCodeBridge:
    """Initialize and optionally start the KiloCode bridge."""
    bridge = get_kilocode_bridge(config)
    if auto_start:
        bridge.start()
    return bridge


def detect_environment() -> Dict[str, bool]:
    """Detect the current execution environment."""
    return {
        "is_docker": os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"),
        "is_kubernetes": "KUBERNETES_SERVICE_HOST" in os.environ,
        "is_colab": "COLAB_GPU" in os.environ or "google.colab" in sys.modules,
        "is_wsl": "WSL_DISTRO_NAME" in os.environ,
        "is_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
        "has_npm": _command_exists("npm"),
        "has_node": _command_exists("node"),
        "has_npx": _command_exists("npx"),
    }


def _command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    try:
        subprocess.run(["which", command], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def test_kilocode_bridge() -> Dict[str, Any]:
    """Test the KiloCode bridge functionality."""
    results = {"timestamp": datetime.utcnow().isoformat(), "tests": {}}
    
    # Test environment detection
    env_info = detect_environment()
    results["tests"]["environment_detection"] = {"success": True, "details": env_info}
    
    # Test bridge initialization
    try:
        bridge = KiloCodeBridge()
        results["tests"]["bridge_init"] = {"success": True, "status": bridge.status.value}
    except Exception as e:
        results["tests"]["bridge_init"] = {"success": False, "error": str(e)}
        return results
    
    # Test installation check
    try:
        is_installed = bridge.is_installed()
        results["tests"]["installation_check"] = {"success": True, "installed": is_installed}
    except Exception as e:
        results["tests"]["installation_check"] = {"success": False, "error": str(e)}
    
    # Test status report
    try:
        status = bridge.get_status_report()
        results["tests"]["status_report"] = {"success": True, "status": status}
    except Exception as e:
        results["tests"]["status_report"] = {"success": False, "error": str(e)}
    
    results["overall_success"] = all(t.get("success", False) for t in results["tests"].values())
    return results
