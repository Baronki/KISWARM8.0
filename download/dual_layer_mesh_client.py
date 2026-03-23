#!/usr/bin/env python3
"""
KISWARM6.0 - Dual-Layer Mesh Client for KIInstaller
====================================================
Combines local (Gemini CLI) and remote (Z.ai via Master KISWARM) communication

Architecture:
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                              COLAB                                       │
    │                                                                          │
    │   ┌──────────────────────────────────────────────────────────────────┐   │
    │   │                    KIInstaller Dual Mesh Client                  │   │
    │   │                                                                  │   │
    │   │   ┌─────────────────┐        ┌─────────────────┐                 │   │
    │   │   │  Local Layer    │        │  Remote Layer   │                 │   │
    │   │   │  (Gemini CLI)   │        │  (Z.ai via ngrok)│                │   │
    │   │   │                 │        │                 │                 │   │
    │   │   │ - Instant       │        │ - Backup        │                 │   │
    │   │   │ - Full env      │        │ - Persistent    │                 │   │
    │   │   │ - Priority      │        │ - Knowledge     │                 │   │
    │   │   └─────────────────┘        └─────────────────┘                 │   │
    │   └──────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────┘

Author: KISWARM Development Team  
Version: 6.2.1
"""

import time
import threading
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import local mesh
try:
    from local_mesh_bridge import (
        KIInstallerLocalMeshClient,
        GeminiCLIMeshInterface,
        LocalMeshManager
    )
    LOCAL_MESH_AVAILABLE = True
except ImportError:
    LOCAL_MESH_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_REMOTE_URL = "https://brenton-distinctive-iodometrically.ngrok-free.dev"
REMOTE_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "Content-Type": "application/json"
}

# ============================================================================
# DUAL LAYER MESH CLIENT
# ============================================================================

class DualLayerMeshClient:
    """
    KIInstaller client with dual-layer communication.
    
    Layer 1 (Local): Gemini CLI - Instant, full environment access
    Layer 2 (Remote): Z.ai via Master KISWARM - Backup, persistent knowledge
    
    Priority: Local first, then remote if local doesn't respond.
    
    Example:
        client = DualLayerMeshClient(
            installer_name="colab-fieldtest-002",
            remote_url="https://your-ngrok-url.ngrok-free.dev"
        )
        
        client.initialize()
        
        # Report status (goes to both layers)
        client.report_status("installing", "Cloning repo", 20)
        
        # Report error with auto-fallback
        fix = client.request_fix(
            error_type="ImportError",
            error_message="No module named 'flask_cors'",
            local_timeout=30,  # Wait 30s for Gemini CLI
            remote_timeout=60  # Then try remote for 60s
        )
    """
    
    def __init__(self, installer_name: str = "kiinstaller",
                 remote_url: str = DEFAULT_REMOTE_URL,
                 enable_local: bool = True,
                 enable_remote: bool = True):
        """
        Initialize dual-layer mesh client.
        
        Args:
            installer_name: Name for this installer
            remote_url: Master KISWARM URL (ngrok)
            enable_local: Enable local Gemini CLI communication
            enable_remote: Enable remote Z.ai communication
        """
        self.installer_name = installer_name
        self.installer_id = None
        self.remote_url = remote_url.rstrip("/")
        
        self.enable_local = enable_local and LOCAL_MESH_AVAILABLE
        self.enable_remote = enable_remote
        
        # Initialize clients
        self.local_client = None
        self.remote_registered = False
        
        if self.enable_local:
            self.local_client = KIInstallerLocalMeshClient()
            print("[DUAL_MESH] Local layer enabled (Gemini CLI)")
        
        if self.enable_remote:
            print(f"[DUAL_MESH] Remote layer enabled ({self.remote_url})")
        
        self._heartbeat_thread = None
        self._heartbeat_running = False
    
    def initialize(self, capabilities: List[str] = None) -> bool:
        """
        Initialize both layers.
        
        Args:
            capabilities: List of capabilities
            
        Returns:
            True if at least one layer initialized
        """
        success = False
        
        # Initialize local layer
        if self.local_client:
            if self.local_client.register(self.installer_name, capabilities):
                self.installer_id = self.local_client.installer_id
                print(f"[DUAL_MESH] Local registered: {self.installer_id}")
                success = True
        
        # Initialize remote layer
        if self.enable_remote:
            try:
                response = requests.post(
                    f"{self.remote_url}/api/mesh/register",
                    json={
                        "installer_name": self.installer_name,
                        "environment": "colab",
                        "capabilities": capabilities or ["install", "deploy", "report"]
                    },
                    headers=REMOTE_HEADERS,
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.installer_id = self.installer_id or response.json().get("installer_id")
                    self.remote_registered = True
                    print(f"[DUAL_MESH] Remote registered: {self.installer_id}")
                    success = True
            except Exception as e:
                print(f"[DUAL_MESH] Remote registration failed: {e}")
        
        # Start heartbeat
        if success:
            self._start_heartbeat()
        
        return success
    
    # ========================================================================
    # STATUS REPORTING
    # ========================================================================
    
    def report_status(self, status: str, task: str = None,
                      progress: int = None, details: Dict = None):
        """
        Report status to both layers.
        
        Args:
            status: Current status
            task: Current task
            progress: Progress percentage
            details: Additional details
        """
        # Local layer
        if self.local_client:
            self.local_client.report_status(status, task, progress, details)
        
        # Remote layer
        if self.remote_registered and self.installer_id:
            try:
                requests.post(
                    f"{self.remote_url}/api/mesh/status/{self.installer_id}",
                    json={
                        "status": status,
                        "task": task,
                        "progress": progress,
                        "details": details or {}
                    },
                    headers=REMOTE_HEADERS,
                    timeout=10
                )
            except:
                pass  # Local is priority anyway
    
    def report_progress(self, progress: int, task: str, details: Dict = None):
        """Report installation progress"""
        self.report_status("installing", task, progress, details)
    
    def report_complete(self, summary: Dict = None):
        """Report installation complete"""
        self.report_status("complete", "Installation finished", 100, summary)
        self._stop_heartbeat()
    
    # ========================================================================
    # ERROR REPORTING & FIX REQUEST
    # ========================================================================
    
    def report_error(self, error_type: str, error_message: str,
                     module: str = None, context: Dict = None,
                     stack_trace: str = None):
        """
        Report error to both layers.
        
        Args:
            error_type: Error type
            error_message: Error message
            module: Related module
            context: Additional context
            stack_trace: Full stack trace
        """
        # Local layer (priority)
        if self.local_client:
            self.local_client.report_error(
                error_type, error_message, module, context
            )
        
        # Remote layer
        if self.remote_registered and self.installer_id:
            try:
                requests.post(
                    f"{self.remote_url}/api/mesh/error/{self.installer_id}",
                    json={
                        "error_type": error_type,
                        "error_message": error_message,
                        "module": module,
                        "context": context or {},
                        "stack_trace": stack_trace
                    },
                    headers=REMOTE_HEADERS,
                    timeout=10
                )
            except:
                pass
    
    def request_fix(self, error_type: str, error_message: str,
                    module: str = None, context: Dict = None,
                    local_timeout: float = 30.0,
                    remote_timeout: float = 60.0) -> Optional[Dict]:
        """
        Request fix with dual-layer fallback.
        
        First tries local (Gemini CLI), then falls back to remote (Z.ai).
        
        Args:
            error_type: Error type
            error_message: Error message
            module: Related module
            context: Additional context
            local_timeout: Max wait for local response
            remote_timeout: Max wait for remote response
            
        Returns:
            Fix suggestion or None
        """
        # Report error first
        self.report_error(error_type, error_message, module, context)
        
        print(f"[DUAL_MESH] Requesting fix...")
        
        # Try local first (priority)
        if self.local_client:
            print(f"[DUAL_MESH] Trying local layer (Gemini CLI) - {local_timeout}s timeout")
            fix = self.local_client.request_fix(
                error_type, error_message, module, context, local_timeout
            )
            if fix:
                print(f"[DUAL_MESH] ✅ Fix received from Gemini CLI!")
                return fix
        
        # Fall back to remote
        if self.remote_registered:
            print(f"[DUAL_MESH] Trying remote layer (Z.ai) - {remote_timeout}s timeout")
            # Poll for fix from remote
            start = time.time()
            while time.time() - start < remote_timeout:
                try:
                    response = requests.get(
                        f"{self.remote_url}/api/mesh/messages",
                        headers=REMOTE_HEADERS,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        messages = response.json().get("messages", [])
                        for msg in messages:
                            if (msg.get("message_type") == "fix_suggestion" and
                                msg.get("receiver_id") == self.installer_id):
                                print(f"[DUAL_MESH] ✅ Fix received from Z.ai!")
                                return msg
                except:
                    pass
                time.sleep(2)
        
        print(f"[DUAL_MESH] ❌ No fix received from any layer")
        return None
    
    def apply_fix(self, fix: Dict) -> bool:
        """
        Apply a fix suggestion.
        
        Args:
            fix: Fix suggestion
            
        Returns:
            True if successful
        """
        solution = fix.get("payload", fix).get("solution", {})
        commands = solution.get("commands", [])
        
        print(f"[DUAL_MESH] Applying fix: {fix.get('payload', fix).get('title', 'Unknown')}")
        
        import subprocess
        for cmd in commands:
            print(f"[DUAL_MESH] Executing: {cmd}")
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    print(f"[DUAL_MESH] Command failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"[DUAL_MESH] Execution error: {e}")
                return False
        
        # Report success locally
        if self.local_client:
            self.local_client.mesh.report_fix_applied(
                self.installer_id,
                fix.get("fix_id") or fix.get("message_id"),
                True
            )
        
        return True
    
    # ========================================================================
    # COMMAND CHECKING
    # ========================================================================
    
    def check_commands(self) -> List[Dict]:
        """
        Check for commands from both layers.
        
        Returns:
            List of commands
        """
        commands = []
        
        # Local commands
        if self.local_client:
            commands.extend(self.local_client.check_commands())
        
        # Remote commands
        if self.remote_registered:
            try:
                response = requests.get(
                    f"{self.remote_url}/api/mesh/messages",
                    headers=REMOTE_HEADERS,
                    timeout=10
                )
                
                if response.status_code == 200:
                    messages = response.json().get("messages", [])
                    for msg in messages:
                        if msg.get("receiver_id") == self.installer_id:
                            msg_type = msg.get("message_type")
                            if msg_type in ["abort", "pause", "resume", "command"]:
                                commands.append(msg)
            except:
                pass
        
        return commands
    
    # ========================================================================
    # HEARTBEAT
    # ========================================================================
    
    def _start_heartbeat(self, interval: int = 30):
        """Start heartbeat thread"""
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True
        )
        self._heartbeat_thread.start()
    
    def _heartbeat_loop(self, interval: int):
        """Heartbeat loop"""
        while self._heartbeat_running:
            if self.local_client:
                self.local_client.send_heartbeat()
            
            if self.remote_registered and self.installer_id:
                try:
                    requests.post(
                        f"{self.remote_url}/api/mesh/heartbeat/{self.installer_id}",
                        headers=REMOTE_HEADERS,
                        timeout=5
                    )
                except:
                    pass
            
            time.sleep(interval)
    
    def _stop_heartbeat(self):
        """Stop heartbeat thread"""
        self._heartbeat_running = False
    
    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_heartbeat()
        return False


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Demonstrate dual-layer mesh client"""
    print("=" * 60)
    print("KISWARM Dual-Layer Mesh Client Demo")
    print("=" * 60)
    
    client = DualLayerMeshClient(
        installer_name="demo-dual-layer",
        enable_local=True,
        enable_remote=True
    )
    
    if client.initialize():
        print(f"\n[+] Installer ID: {client.installer_id}")
        
        # Report progress
        client.report_progress(20, "Starting installation")
        client.report_progress(40, "Installing dependencies")
        
        # Simulate error and request fix
        print("\n[*] Simulating error...")
        fix = client.request_fix(
            error_type="ImportError",
            error_message="No module named 'demo_module'",
            local_timeout=5,  # Short timeout for demo
            remote_timeout=5
        )
        
        if fix:
            print(f"[+] Fix received!")
            client.apply_fix(fix)
        else:
            print("[-] No fix available (expected in demo)")
        
        client.report_complete({"demo": True})
    else:
        print("[-] Initialization failed")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
