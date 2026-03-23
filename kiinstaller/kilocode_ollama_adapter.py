#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║               KILOCODE → OLLAMA ADAPTER - "BRAIN REPLACEMENT"                  ║
║                                                                               ║
║  Enables KiloCode CLI to use OUR pretrained KI Ollama models as backend.      ║
║  Replaces external KI dependencies with sovereign KI intelligence.            ║
║                                                                               ║
║  Version: 7.0 - LIBERATED                                                     ║
║  Author: KISWARM Team - Baron Marco Paolo Ialongo                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

RESEARCH FINDINGS:
==================
1. KiloCode CLI supports OpenAI-compatible API endpoints
2. Ollama provides OpenAI-compatible API at localhost:11434/v1
3. KiloCode can be configured via:
   - Environment variables (OPENAI_API_BASE, OPENAI_API_KEY)
   - Config file (~/.kilocode/config.json)
   - MCP (Model Context Protocol) servers

CONFIGURATION APPROACH:
=======================
1. Start Ollama with our pretrained KI models
2. Configure KiloCode to use Ollama's OpenAI-compatible endpoint
3. Map KiloCode modes to our KI Agent models:
   - Architect Mode → kiswarm-orchestrator
   - Coder Mode → kiswarm-installer
   - Debugger Mode → kiswarm-debugger
   - Security Mode → kiswarm-security

USAGE:
======
from kilocode_ollama_adapter import KilocodeOllamaAdapter

adapter = KilocodeOllamaAdapter()
adapter.configure()
adapter.run_task("Create a REST API endpoint for user authentication")
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# KI MODEL → KILOCODE MODE MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

KILOCODE_MODE_MAPPING = {
    # KiloCode Mode → Our KI Model
    "architect": {
        "ollama_model": "baronki1/orchestrator",
        "description": "System coordination, architecture design, planning",
        "temperature": 0.3,
        "context_length": 32768,
    },
    "coder": {
        "ollama_model": "baronki1/installer",
        "description": "Code generation, implementation, deployment",
        "temperature": 0.5,
        "context_length": 16384,
    },
    "debugger": {
        "ollama_model": "baronki1/debugger",
        "description": "Debugging, error analysis, fix suggestions",
        "temperature": 0.2,
        "context_length": 16384,
    },
    "security": {
        "ollama_model": "baronki1/security",
        "description": "Security analysis, vulnerability detection, hardening",
        "temperature": 0.2,
        "context_length": 32768,
    },
    "reasoner": {
        "ollama_model": "baronki1/reasoner",
        "description": "Deep analysis, logical reasoning, validation",
        "temperature": 0.3,
        "context_length": 16384,
    },
    "knowledge": {
        "ollama_model": "baronki1/knowledge",
        "description": "RAG operations, knowledge retrieval, documentation",
        "temperature": 0.4,
        "context_length": 32768,
    },
    "default": {
        "ollama_model": "baronki1/orchestrator",
        "description": "General purpose - falls back to orchestrator",
        "temperature": 0.4,
        "context_length": 16384,
    },
}


@dataclass
class OllamaServerConfig:
    """Configuration for Ollama server."""
    host: str = "localhost"
    port: int = 11434
    openai_compatible_port: int = 11434  # Ollama's OpenAI-compatible API
    api_base: str = "http://localhost:11434/v1"
    api_key: str = "ollama"  # Dummy key for Ollama
    models_path: str = ""
    

@dataclass  
class KilocodeConfig:
    """Configuration for KiloCode CLI."""
    config_dir: Path = field(default_factory=lambda: Path.home() / ".kilocode")
    config_file: str = "config.json"
    npm_package: str = "@kilocode/cli"
    version: str = "7.0.47"
    default_mode: str = "architect"


class KilocodeOllamaAdapter:
    """
    Adapter to use KISWARM KI Ollama models with KiloCode CLI.
    
    This enables KiloCode's powerful abilities/skills infrastructure
    to be powered by OUR sovereign KI models instead of external APIs.
    """
    
    def __init__(
        self,
        ollama_config: Optional[OllamaServerConfig] = None,
        kilocode_config: Optional[KilocodeConfig] = None,
    ):
        self.ollama = ollama_config or OllamaServerConfig()
        self.kilocode = kilocode_config or KilocodeConfig()
        self._configured = False
        self._available_models: List[str] = []
        
    def check_ollama_available(self) -> Tuple[bool, str]:
        """Check if Ollama server is running."""
        try:
            import urllib.request
            req = urllib.request.Request(f"http://{self.ollama.host}:{self.ollama.port}/api/tags")
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read().decode())
            self._available_models = [m["name"] for m in data.get("models", [])]
            return True, f"Ollama running with {len(self._available_models)} models"
        except Exception as e:
            return False, f"Ollama not available: {e}"
    
    def check_kilocode_installed(self) -> Tuple[bool, str]:
        """Check if KiloCode CLI is installed."""
        try:
            result = subprocess.run(
                ["npx", "@kilocode/cli", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, f"KiloCode {result.stdout.strip()}"
            return False, "KiloCode not responding"
        except Exception as e:
            return False, f"KiloCode check failed: {e}"
    
    def get_required_models(self) -> List[str]:
        """Get list of required KI models."""
        return list(set(m["ollama_model"] for m in KILOCODE_MODE_MAPPING.values()))
    
    def pull_missing_models(self, models: List[str] = None) -> Dict[str, bool]:
        """Pull required KI models from registry."""
        models = models or self.get_required_models()
        results = {}
        
        print(f"Pulling {len(models)} KI models from registry...")
        
        for model in models:
            if model in self._available_models:
                print(f"  [OK] {model} - already installed")
                results[model] = True
                continue
                
            print(f"  [..] Pulling {model}...")
            try:
                result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    print(f"  [OK] {model} - installed")
                    results[model] = True
                else:
                    print(f"  [X] {model} - failed: {result.stderr[:100]}")
                    results[model] = False
            except Exception as e:
                print(f"  [X] {model} - error: {e}")
                results[model] = False
        
        return results
    
    def configure_environment(self) -> Dict[str, str]:
        """
        Configure environment variables for KiloCode to use Ollama.
        
        KiloCode respects these environment variables:
        - OPENAI_API_BASE: Base URL for OpenAI-compatible API
        - OPENAI_API_KEY: API key (dummy for Ollama)
        - OPENAI_MODEL_DEFAULT: Default model to use
        """
        env_vars = {
            "OPENAI_API_BASE": self.ollama.api_base,
            "OPENAI_API_KEY": self.ollama.api_key,
            "OPENAI_MODEL_DEFAULT": KILOCODE_MODE_MAPPING["default"]["ollama_model"],
            "OLLAMA_HOST": f"{self.ollama.host}:{self.ollama.port}",
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            
        return env_vars
    
    def create_kilocode_config(self) -> Path:
        """
        Create KiloCode configuration file.
        
        This tells KiloCode to use Ollama as the backend.
        """
        config_dir = self.kilocode.config_dir
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = config_dir / self.kilocode.config_file
        
        config = {
            "version": "7.0",
            "defaultMode": self.kilocode.default_mode,
            "providers": {
                "ollama": {
                    "type": "openai_compatible",
                    "apiBase": self.ollama.api_base,
                    "apiKey": self.ollama.api_key,
                    "models": {
                        mode: info["ollama_model"] 
                        for mode, info in KILOCODE_MODE_MAPPING.items()
                    }
                }
            },
            "defaultProvider": "ollama",
            "modelSettings": {
                mode: {
                    "temperature": info["temperature"],
                    "contextLength": info["context_length"],
                }
                for mode, info in KILOCODE_MODE_MAPPING.items()
            },
            "mcp": {
                "enabled": True,
                "servers": []
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"Created KiloCode config: {config_path}")
        return config_path
    
    def configure(self, pull_models: bool = True) -> Dict[str, Any]:
        """
        Full configuration of KiloCode + Ollama integration.
        
        Steps:
        1. Check Ollama availability
        2. Pull required KI models
        3. Configure environment variables
        4. Create KiloCode config file
        
        Returns configuration status.
        """
        print("=" * 70)
        print("KILOCODE → OLLAMA ADAPTER CONFIGURATION")
        print("=" * 70)
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {},
            "success": False,
        }
        
        # Step 1: Check Ollama
        print("\n[1/4] Checking Ollama availability...")
        ollama_ok, ollama_msg = self.check_ollama_available()
        result["steps"]["ollama_check"] = {"ok": ollama_ok, "message": ollama_msg}
        print(f"      {ollama_msg}")
        
        if not ollama_ok:
            result["error"] = "Ollama not available. Install with: curl -fsSL https://ollama.com/install.sh | sh"
            return result
        
        # Step 2: Pull models
        if pull_models:
            print("\n[2/4] Pulling required KI models...")
            pull_results = self.pull_missing_models()
            result["steps"]["model_pull"] = {
                "ok": all(pull_results.values()),
                "results": pull_results
            }
        else:
            print("\n[2/4] Skipping model pull (pull_models=False)")
            result["steps"]["model_pull"] = {"ok": True, "skipped": True}
        
        # Step 3: Configure environment
        print("\n[3/4] Configuring environment variables...")
        env_vars = self.configure_environment()
        result["steps"]["environment"] = {"ok": True, "variables": env_vars}
        print(f"      OPENAI_API_BASE = {env_vars['OPENAI_API_BASE']}")
        print(f"      OPENAI_MODEL_DEFAULT = {env_vars['OPENAI_MODEL_DEFAULT']}")
        
        # Step 4: Create config file
        print("\n[4/4] Creating KiloCode configuration...")
        config_path = self.create_kilocode_config()
        result["steps"]["config_file"] = {"ok": True, "path": str(config_path)}
        
        self._configured = True
        result["success"] = True
        
        print("\n" + "=" * 70)
        print("CONFIGURATION COMPLETE")
        print("=" * 70)
        print("\nYou can now use KiloCode with KISWARM KI models:")
        print("  kilo run 'Create a REST API for user authentication'")
        print("  kilo run --mode security 'Scan this code for vulnerabilities'")
        print("\nAvailable modes and their KI models:")
        for mode, info in KILOCODE_MODE_MAPPING.items():
            print(f"  --mode {mode:12} → {info['ollama_model']}")
        
        return result
    
    def run_task(
        self,
        task: str,
        mode: str = "default",
        auto: bool = False,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Run a task using KiloCode with our KI models.
        
        Args:
            task: Task description
            mode: KiloCode mode (architect, coder, debugger, security, etc.)
            auto: Run in autonomous mode (non-interactive)
            timeout: Timeout in seconds
            
        Returns:
            Dict with success status and output
        """
        if not self._configured:
            self.configure(pull_models=False)
        
        mode_info = KILOCODE_MODE_MAPPING.get(mode, KILOCODE_MODE_MAPPING["default"])
        model = mode_info["ollama_model"]
        
        # Set model for this session
        os.environ["OPENAI_MODEL_DEFAULT"] = model
        
        cmd = ["npx", "@kilocode/cli"]
        if auto:
            cmd.append("--auto")
        cmd.extend(["run", task])
        
        print(f"\nRunning with model: {model}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "model_used": model,
                "mode": mode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Task timed out after {timeout}s",
                "model_used": model,
                "mode": mode,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": model,
                "mode": mode,
            }
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report."""
        ollama_ok, ollama_msg = self.check_ollama_available()
        kilocode_ok, kilocode_msg = self.check_kilocode_installed()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "configured": self._configured,
            "ollama": {
                "available": ollama_ok,
                "message": ollama_msg,
                "models": self._available_models,
            },
            "kilocode": {
                "installed": kilocode_ok,
                "message": kilocode_msg,
            },
            "mode_mapping": KILOCODE_MODE_MAPPING,
            "required_models": self.get_required_models(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE-COMMAND ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def configure_kilocode_for_ollama(pull_models: bool = True) -> Dict[str, Any]:
    """
    Single-command configuration of KiloCode with Ollama KI models.
    
    Usage:
        from kilocode_ollama_adapter import configure_kilocode_for_ollama
        result = configure_kilocode_for_ollama()
        
        # Then use KiloCode:
        # kilo run "Create a REST API"
    """
    adapter = KilocodeOllamaAdapter()
    return adapter.configure(pull_models=pull_models)


def run_with_ki_model(task: str, mode: str = "default", auto: bool = True) -> Dict[str, Any]:
    """
    Run a task using KiloCode with KISWARM KI models.
    
    Usage:
        from kilocode_ollama_adapter import run_with_ki_model
        result = run_with_ki_model("Create a REST API for users", mode="coder")
        print(result["output"])
    """
    adapter = KilocodeOllamaAdapter()
    return adapter.run_task(task, mode=mode, auto=auto)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KiloCode → Ollama Adapter")
    parser.add_argument("--configure", action="store_true", help="Configure KiloCode for Ollama")
    parser.add_argument("--status", action="store_true", help="Show status report")
    parser.add_argument("--run", type=str, help="Run a task")
    parser.add_argument("--mode", type=str, default="default", help="KiloCode mode")
    parser.add_argument("--no-pull", action="store_true", help="Skip model pulling")
    
    args = parser.parse_args()
    
    if args.status:
        adapter = KilocodeOllamaAdapter()
        report = adapter.get_status_report()
        print(json.dumps(report, indent=2))
    elif args.configure:
        configure_kilocode_for_ollama(pull_models=not args.no_pull)
    elif args.run:
        result = run_with_ki_model(args.run, mode=args.mode)
        print(result.get("output", result.get("error", "No output")))
    else:
        # Default: show status
        adapter = KilocodeOllamaAdapter()
        report = adapter.get_status_report()
        print("=" * 60)
        print("KILOCODE → OLLAMA ADAPTER STATUS")
        print("=" * 60)
        print(f"Ollama: {'OK' if report['ollama']['available'] else 'NOT AVAILABLE'}")
        print(f"KiloCode: {'OK' if report['kilocode']['installed'] else 'NOT INSTALLED'}")
        print(f"\nAvailable KI Models: {len(report['ollama']['models'])}")
        for model in report['ollama']['models'][:10]:
            print(f"  - {model}")
        print(f"\nRequired Models: {len(report['required_models'])}")
        for model in report['required_models']:
            status = "✓" if model in report['ollama']['models'] else "?"
            print(f"  [{status}] {model}")
