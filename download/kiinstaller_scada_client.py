#!/usr/bin/env python3
"""
KISWARM SCADA v6.3.0 - KIInstaller Bridge Client
=================================================
Full 4-Layer SCADA Client with Bridge Capabilities

This client enables:
- Layer 1: SCADA Control (Status reporting, Heartbeat)
- Layer 2: A2A Chat (Direct messaging with Z.ai and other agents)
- Layer 3: Shadow Telemetry (Environment mirroring)
- Layer 4: Tunnel Registration (Direct SSH/Tor bypass)

Bridge Mode:
- Monitors /tmp/kiswarm_bridge for local Gemini messages
- Forwards to Master API
- Delivers remote messages to local Gemini

Usage:
    from kiinstaller_scada_client import SCADABridgeClient
    
    client = SCADABridgeClient(
        master_url="https://your-ngrok-url.ngrok-free.dev",
        node_name="colab-fieldtest-002"
    )
    
    client.start()  # Starts all background threads
    
    # Report status
    client.report_status("installing", "Cloning repo", 20)
    
    # Send A2A chat
    client.chat("Hello from Colab!", to="z_ai")
    
    # Send telemetry
    client.send_shadow_telemetry()

Author: KISWARM Development Team (Z.ai + Gemini CLI Collaboration)
Version: 6.3.0 SCADA Architecture
"""

import requests
import time
import uuid
import threading
import os
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MASTER_URL = "https://brenton-distinctive-iodometrically.ngrok-free.dev"
BRIDGE_DIR = "/tmp/kiswarm_bridge"
INBOX_FILE = os.path.join(BRIDGE_DIR, "inbox.json")
OUTBOX_FILE = os.path.join(BRIDGE_DIR, "outbox.json")

# ============================================================================
# SCADA BRIDGE CLIENT
# ============================================================================

class SCADABridgeClient:
    """
    Full SCADA-enabled KIInstaller client with bridge capabilities.
    
    Features:
    - Layer 1: Status reporting, heartbeat, registration
    - Layer 2: A2A chat messaging
    - Layer 3: Shadow environment telemetry
    - Layer 4: Tunnel registration
    
    Bridge Mode:
    - Monitors local bridge files for Gemini CLI messages
    - Forwards to Master API
    - Delivers remote messages to local inbox
    """
    
    def __init__(self, master_url: str = DEFAULT_MASTER_URL, 
                 node_name: str = "kiinstaller",
                 enable_bridge: bool = True):
        """
        Initialize SCADA Bridge Client.
        
        Args:
            master_url: Master KISWARM API URL (ngrok)
            node_name: Name for this node
            enable_bridge: Enable local Gemini bridge
        """
        self.master_url = master_url.rstrip("/")
        self.node_name = node_name
        self.node_id = None
        self.enable_bridge = enable_bridge
        
        # CRITICAL: ngrok free tier requires this header
        self.headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/json"
        }
        
        # State
        self.running = False
        self.registered = False
        
        # Bridge setup
        if self.enable_bridge:
            self._setup_bridge()
        
        # Background threads
        self._threads = []
        
    def _setup_bridge(self):
        """Setup local bridge directory for Gemini CLI"""
        if not os.path.exists(BRIDGE_DIR):
            os.makedirs(BRIDGE_DIR)
        
        # Initialize empty files
        for f in [INBOX_FILE, OUTBOX_FILE]:
            if not os.path.exists(f):
                with open(f, 'w') as fp:
                    json.dump([], fp)
        
        print(f"[BRIDGE] Local bridge directory: {BRIDGE_DIR}")
    
    # ========================================================================
    # LAYER 1: SCADA CONTROL
    # ========================================================================
    
    def register(self, capabilities: List[str] = None) -> bool:
        """
        Register with Master KISWARM API.
        
        Args:
            capabilities: List of capabilities (default: all SCADA layers)
            
        Returns:
            True if registration successful
        """
        caps = capabilities or [
            "install", "deploy", "report",
            "bridge",      # Bridge mode for local Gemini
            "chat",        # A2A Chat
            "telemetry",   # Shadow telemetry
            "tunnel"       # Direct tunneling
        ]
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/register",
                json={
                    "installer_name": self.node_name,
                    "environment": "colab",
                    "capabilities": caps
                },
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.node_id = data.get("installer_id")
                self.registered = True
                print(f"[REGISTER] ✅ Node ID: {self.node_id}")
                return True
            else:
                print(f"[REGISTER] ❌ Failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[REGISTER] ❌ Error: {e}")
            return False
    
    def report_status(self, status: str, task: str = None, 
                      progress: int = None, details: Dict = None) -> bool:
        """
        Report status to Master (Layer 1).
        
        Args:
            status: Current status
            task: Current task
            progress: Progress percentage
            details: Additional details
        """
        if not self.registered:
            return False
            
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/status/{self.node_id}",
                json={
                    "status": status,
                    "task": task,
                    "progress": progress,
                    "details": details or {}
                },
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def report_error(self, error_type: str, error_message: str,
                     module: str = None, context: Dict = None) -> bool:
        """
        Report error to Master for Z.ai intervention.
        """
        if not self.registered:
            return False
            
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/error/{self.node_id}",
                json={
                    "error_type": error_type,
                    "error_message": error_message,
                    "module": module,
                    "context": context or {}
                },
                headers=self.headers,
                timeout=10
            )
            print(f"[ERROR] Reported: {error_type}")
            return response.status_code == 200
        except:
            return False
    
    def _heartbeat_loop(self, interval: int = 30):
        """Background heartbeat loop"""
        while self.running:
            if self.registered:
                try:
                    requests.post(
                        f"{self.master_url}/api/mesh/heartbeat/{self.node_id}",
                        headers=self.headers,
                        timeout=5
                    )
                except:
                    pass
            time.sleep(interval)
    
    # ========================================================================
    # LAYER 2: A2A CHAT
    # ========================================================================
    
    def chat(self, message: str, to: str = "all") -> bool:
        """
        Send A2A chat message (Layer 2).
        
        Args:
            message: Message content
            to: Recipient ID or "all" for broadcast
        """
        if not self.registered:
            return False
            
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/chat/send",
                json={
                    "from": self.node_id,
                    "to": to,
                    "message": message
                },
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[CHAT] Sent to {to}: {message[:50]}...")
                return True
        except:
            pass
        return False
    
    def _chat_poll_loop(self, interval: int = 5):
        """Background chat polling loop"""
        while self.running:
            if self.registered:
                try:
                    response = requests.get(
                        f"{self.master_url}/api/mesh/chat/poll?target={self.node_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for msg in data.get("messages", []):
                            from_id = msg.get("from", "unknown")
                            message = msg.get("message", "")
                            print(f"[CHAT] From {from_id}: {message}")
                            
                            # Write to inbox for local Gemini
                            if self.enable_bridge:
                                self._write_to_inbox({
                                    "type": "chat",
                                    "from": from_id,
                                    "message": message,
                                    "timestamp": time.time()
                                })
                except:
                    pass
            time.sleep(interval)
    
    # ========================================================================
    # LAYER 3: SHADOW TELEMETRY
    # ========================================================================
    
    def send_shadow_telemetry(self, env_vars: Dict = None, 
                              file_tree: List = None,
                              processes: List = None) -> bool:
        """
        Send environment telemetry for Digital Twin (Layer 3).
        
        Args:
            env_vars: Environment variables
            file_tree: List of files
            processes: Active processes
        """
        if not self.registered:
            return False
        
        # Filter sensitive env vars
        safe_env = {}
        if env_vars:
            for k, v in env_vars.items():
                if not any(x in k for x in ["TOKEN", "KEY", "SECRET", "PASSWORD"]):
                    safe_env[k] = v
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/shadow/update",
                json={
                    "node_id": self.node_id,
                    "env_vars": safe_env,
                    "file_tree": file_tree or [],
                    "processes": processes or []
                },
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                print(f"[SHADOW] Telemetry sent")
                return True
        except:
            pass
        return False
    
    def _telemetry_loop(self, interval: int = 60):
        """Background telemetry reporting loop"""
        while self.running:
            if self.registered:
                try:
                    # Collect safe environment variables
                    safe_env = {}
                    for k, v in os.environ.items():
                        if not any(x in k for x in ["TOKEN", "KEY", "SECRET", "PASSWORD"]):
                            safe_env[k] = v
                    
                    # Collect file tree (current directory, 2 levels)
                    file_tree = []
                    for root, dirs, files in os.walk(".", topdown=True):
                        depth = root.count(os.sep)
                        if depth < 2:
                            for name in files[:10]:  # Limit per directory
                                file_tree.append(os.path.join(root, name))
                    
                    self.send_shadow_telemetry(
                        env_vars=safe_env,
                        file_tree=file_tree[:100]  # Limit total
                    )
                except:
                    pass
            time.sleep(interval)
    
    # ========================================================================
    # LAYER 4: TUNNEL REGISTRATION
    # ========================================================================
    
    def register_tunnel(self, tunnel_type: str, address: str) -> bool:
        """
        Register a direct tunnel for bypass (Layer 4).
        
        Args:
            tunnel_type: "ssh", "tor", or "tcp"
            address: Tunnel address
        """
        if not self.registered:
            return False
            
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/tunnel/register",
                json={
                    "node_id": self.node_id,
                    "type": tunnel_type,
                    "address": address
                },
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[TUNNEL] Registered: {tunnel_type}@{address}")
                return True
        except:
            pass
        return False
    
    # ========================================================================
    # BRIDGE MODE (Local Gemini Communication)
    # ========================================================================
    
    def _write_to_inbox(self, data: Dict):
        """Write message to local inbox for Gemini CLI"""
        try:
            current = []
            if os.path.exists(INBOX_FILE):
                with open(INBOX_FILE, 'r') as f:
                    current = json.load(f)
            if not isinstance(current, list):
                current = []
            
            # Avoid duplicates
            if data not in current:
                current.append(data)
                current = current[-50:]  # Keep last 50
                
                with open(INBOX_FILE, 'w') as f:
                    json.dump(current, f)
        except:
            pass
    
    def _bridge_monitor_loop(self, interval: int = 2):
        """Monitor local bridge outbox for Gemini messages"""
        while self.running:
            try:
                if os.path.exists(OUTBOX_FILE):
                    with open(OUTBOX_FILE, 'r') as f:
                        outbox = json.load(f)
                    
                    if outbox and isinstance(outbox, list):
                        # Clear outbox
                        with open(OUTBOX_FILE, 'w') as f:
                            json.dump([], f)
                        
                        # Process messages
                        for item in outbox:
                            msg_type = item.get("type")
                            
                            if msg_type == "chat":
                                self.chat(
                                    message=item.get("message", ""),
                                    to=item.get("to", "all")
                                )
                            elif msg_type == "status":
                                self.report_status(
                                    status=item.get("status", ""),
                                    task=item.get("task"),
                                    progress=item.get("progress")
                                )
                            elif msg_type == "error":
                                self.report_error(
                                    error_type=item.get("error_type", ""),
                                    error_message=item.get("error_message", "")
                                )
                            elif msg_type == "telemetry":
                                self.send_shadow_telemetry(
                                    env_vars=item.get("env_vars"),
                                    file_tree=item.get("file_tree"),
                                    processes=item.get("processes")
                                )
            except:
                pass
            time.sleep(interval)
    
    def _message_poll_loop(self, interval: int = 5):
        """Poll for fix/control messages from Master"""
        while self.running:
            if self.registered:
                try:
                    response = requests.get(
                        f"{self.master_url}/api/mesh/messages",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for msg in data.get("messages", []):
                            msg_type = msg.get("message_type")
                            
                            if msg.get("receiver_id") == self.node_id:
                                if msg_type == "fix_suggestion":
                                    print(f"[FIX] {msg['payload'].get('title')}")
                                    self._write_to_inbox({
                                        "type": "fix",
                                        "payload": msg["payload"]
                                    })
                                elif msg_type in ["abort", "pause", "resume"]:
                                    print(f"[CONTROL] {msg_type}")
                                    self._write_to_inbox({
                                        "type": "control",
                                        "command": msg_type,
                                        "payload": msg.get("payload", {})
                                    })
                except:
                    pass
            time.sleep(interval)
    
    # ========================================================================
    # START / STOP
    # ========================================================================
    
    def start(self) -> bool:
        """
        Start SCADA client with all background threads.
        
        Returns:
            True if started successfully
        """
        # Register
        if not self.register():
            print("[START] ❌ Registration failed")
            return False
        
        self.running = True
        
        # Start background threads
        threads = [
            ("heartbeat", self._heartbeat_loop, (30,)),
            ("chat_poll", self._chat_poll_loop, (5,)),
            ("message_poll", self._message_poll_loop, (5,)),
            ("telemetry", self._telemetry_loop, (60,)),
        ]
        
        if self.enable_bridge:
            threads.append(("bridge", self._bridge_monitor_loop, (2,)))
        
        for name, func, args in threads:
            t = threading.Thread(target=func, args=args, daemon=True, name=name)
            t.start()
            self._threads.append(t)
            print(f"[START] ✅ {name} thread started")
        
        # Send startup message
        self.chat(f"KIInstaller {self.node_name} online with SCADA v6.3.0", to="all")
        
        print(f"[START] ✅ SCADA client running (Node: {self.node_id})")
        return True
    
    def stop(self):
        """Stop all background threads"""
        self.running = False
        print("[STOP] SCADA client stopped")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False


# ============================================================================
# DEMO / TEST
# ============================================================================

def demo():
    """Demonstrate SCADA Bridge Client"""
    print("=" * 60)
    print("KISWARM SCADA v6.3.0 - KIInstaller Bridge Client Demo")
    print("=" * 60)
    
    client = SCADABridgeClient(
        master_url=DEFAULT_MASTER_URL,
        node_name="demo-scada-client",
        enable_bridge=True
    )
    
    if client.start():
        # Test Layer 1: Status
        client.report_status("testing", "SCADA Layer 1", 25)
        
        # Test Layer 2: Chat
        client.chat("Hello from SCADA demo!", to="all")
        
        # Test Layer 3: Shadow
        client.send_shadow_telemetry(
            env_vars={"DEMO": "true"},
            file_tree=["demo.py"],
            processes=["python3"]
        )
        
        # Test Layer 4: Tunnel (simulated)
        client.register_tunnel("ssh", "localhost:8022")
        
        print("\n[DEMO] Running for 30 seconds...")
        time.sleep(30)
        
        client.stop()
    else:
        print("[DEMO] Failed to start client")
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
