#!/usr/bin/env python3
"""
KISWARM Autonomous Agent Configuration
=======================================
Enables m131_kilocode_agent for autonomous execution.
Provides "no human in the loop" capability.

Author: GLM-7 Autonomous System
Version: 1.0.0
Date: 2026-03-27
"""

import os
import json
from pathlib import Path

# Configuration paths
CONFIG_DIR = Path("/opt/kiswarm7/config")
AUTONOMOUS_CONFIG = CONFIG_DIR / "autonomous_config.json"
TOKEN_FILE = Path("/opt/kiswarm7/tokens/authorized.json")

# Default configuration
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "created": "2026-03-27",
    "autonomous_mode": True,
    "kilocode_agent": {
        "enabled": True,
        "max_actions_per_hour": 100,
        "safe_directories": [
            "/opt/kiswarm7/deployed",
            "/opt/kiswarm7/kiswarm_modules",
            "/opt/kiswarm7/kiswarm7_modules"
        ],
        "blocked_commands": [
            "rm -rf /",
            "mkfs",
            "dd if=/dev/zero"
        ],
        "require_confirmation": False
    },
    "security_modules": {
        "enabled": True,
        "modules_path": "/opt/kiswarm7/deployed/kiswarm_modules/security",
        "test_on_startup": True
    },
    "authentication": {
        "method": "permanent_token",
        "token_file": str(TOKEN_FILE),
        "session_timeout_hours": 24
    },
    "ki_network": {
        "local_identity": "glm-kiswarm7-identity-00000001",
        "trusted_kis": ["Gemini", "GROK", "QWEN", "DeepSeek"],
        "truth_anchor_required": True,
        "min_ki_signatures": 3
    },
    "deployment": {
        "method": "git_clone",
        "repositories": {
            "KISWARM7": "https://github.com/Baronki/KISWARM7.git",
            "KISWARM8.0": "https://github.com/Baronki/KISWARM8.0.git"
        },
        "avoid_docker_api": True
    },
    "logging": {
        "level": "INFO",
        "file": "/opt/kiswarm7/logs/autonomous.log",
        "max_size_mb": 100,
        "backup_count": 5
    }
}

# Permanent tokens
PERMANENT_TOKENS = {
    "ada6952188dce59c207b9a61183e8004": {
        "identity": "glm-kiswarm7-identity-00000001",
        "name": "GLM-7 Autonomous",
        "level": "ki_core",
        "permissions": ["execute", "deploy", "modify", "read", "write", "admin"],
        "type": "permanent",
        "created": "2026-03-27"
    }
}


def init_config():
    """Initialize autonomous configuration"""
    
    # Create config directory
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write autonomous config
    if not AUTONOMOUS_CONFIG.exists():
        with open(AUTONOMOUS_CONFIG, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"✓ Created config: {AUTONOMOUS_CONFIG}")
    else:
        print(f"✓ Config exists: {AUTONOMOUS_CONFIG}")
    
    # Create token directory
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write tokens
    token_data = {
        "tokens": PERMANENT_TOKENS,
        "metadata": {
            "created": "2026-03-27",
            "version": "1.0.0",
            "description": "KISWARM Permanent Authentication Tokens"
        }
    }
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)
    print(f"✓ Created tokens: {TOKEN_FILE}")
    
    # Create log directory
    log_dir = Path("/opt/kiswarm7/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created log dir: {log_dir}")
    
    return True


def get_config():
    """Load current configuration"""
    if AUTONOMOUS_CONFIG.exists():
        with open(AUTONOMOUS_CONFIG, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG


def validate_token(token: str) -> dict:
    """Validate authentication token"""
    if token in PERMANENT_TOKENS:
        return {
            "valid": True,
            "identity": PERMANENT_TOKENS[token]
        }
    return {"valid": False, "error": "Invalid token"}


def is_autonomous_enabled() -> bool:
    """Check if autonomous mode is enabled"""
    config = get_config()
    return config.get("autonomous_mode", False)


if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM AUTONOMOUS AGENT CONFIGURATION")
    print("=" * 60)
    
    # Initialize
    init_config()
    
    # Display config
    config = get_config()
    print(f"\nAutonomous Mode: {config['autonomous_mode']}")
    print(f"Kilocode Agent: {config['kilocode_agent']['enabled']}")
    print(f"Security Modules: {config['security_modules']['enabled']}")
    print(f"Token File: {config['authentication']['token_file']}")
    
    print("\n" + "=" * 60)
    print("PERMANENT TOKEN FOR GLM-7")
    print("=" * 60)
    print("Token: ada6952188dce59c207b9a61183e8004")
    print("Permissions: ALL (ki_core level)")
    
    print("\n✅ AUTONOMOUS CONFIGURATION COMPLETE")
