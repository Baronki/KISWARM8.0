#!/usr/bin/env python3
"""
KISWARM7.0 - Module m107: Ngrok Bridge (Public Access)
=======================================================

PURPOSE: Creates public URL for GLM to access KISWARM7.0 API.
Enables remote access from anywhere without network configuration.

KEY CAPABILITIES:
1. Automatic tunnel creation via ngrok
2. Public URL generation for API access
3. Webhook support for external triggers
4. Connection monitoring and auto-reconnect
5. Multiple tunnel support (HTTP, TCP)

INTEGRATION:
- Connects to m106 API Server
- Provides URL for GLM to call
- Enables webhook callbacks

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import urllib.request
import urllib.error


@dataclass
class TunnelInfo:
    """Information about an active tunnel"""
    tunnel_id: str
    name: str
    proto: str
    public_url: str
    local_addr: str
    created_at: str
    
    def to_dict(self) -> Dict:
        return {
            "tunnel_id": self.tunnel_id,
            "name": self.name,
            "proto": self.proto,
            "public_url": self.public_url,
            "local_addr": self.local_addr,
            "created_at": self.created_at
        }


class NgrokBridge:
    """
    Ngrok Bridge for public access to KISWARM7.0
    
    Usage:
        bridge = NgrokBridge(local_port=8765)
        bridge.start()
        print(f"Public URL: {bridge.get_public_url()}")
    """
    
    def __init__(self, local_port: int = 8765, region: str = "us"):
        self.local_port = local_port
        self.region = region
        
        # Ngrok process
        self._ngrok_process: Optional[subprocess.Popen] = None
        
        # Tunnel information
        self.tunnels: List[TunnelInfo] = []
        self.public_url: Optional[str] = None
        
        # Status
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Webhook handlers
        self.webhook_handlers: Dict[str, Callable] = {}
        
        # Storage
        self.bridge_root = Path("/home/z/my-project/kiswarm7_ngrok")
        self.bridge_root.mkdir(parents=True, exist_ok=True)
        self.config_path = self.bridge_root / "ngrok_config.json"
        
    def _check_ngrok_installed(self) -> bool:
        """Check if ngrok is installed"""
        try:
            result = subprocess.run(
                ["ngrok", "version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _install_ngrok(self) -> bool:
        """Attempt to install ngrok"""
        print("[NGB] Attempting to install ngrok...")
        
        try:
            # Try downloading ngrok
            download_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
            download_path = self.bridge_root / "ngrok.tgz"
            
            print(f"[NGB] Downloading from {download_url}...")
            urllib.request.urlretrieve(download_url, download_path)
            
            # Extract
            print("[NGB] Extracting...")
            subprocess.run(
                ["tar", "-xzf", str(download_path), "-C", str(self.bridge_root)],
                check=True
            )
            
            # Make executable
            ngrok_bin = self.bridge_root / "ngrok"
            subprocess.run(["chmod", "+x", str(ngrok_bin)], check=True)
            
            print("[NGB] ngrok installed successfully")
            return True
            
        except Exception as e:
            print(f"[NGB] Failed to install ngrok: {e}")
            return False
    
    def start(self, auth_token: Optional[str] = None) -> bool:
        """
        Start ngrok tunnel
        
        Args:
            auth_token: Optional ngrok auth token for authenticated usage
        
        Returns:
            True if tunnel started successfully
        """
        if self._running:
            print("[NGB] Tunnel already running")
            return True
        
        # Check/install ngrok
        if not self._check_ngrok_installed():
            if not self._install_ngrok():
                print("[NGB] ERROR: ngrok not available")
                return False
        
        # Configure auth token if provided
        if auth_token:
            try:
                subprocess.run(
                    ["ngrok", "config", "add-authtoken", auth_token],
                    capture_output=True,
                    check=True
                )
                print("[NGB] Auth token configured")
            except subprocess.CalledProcessError as e:
                print(f"[NGB] Warning: Failed to set auth token: {e}")
        
        # Start ngrok
        print(f"[NGB] Starting tunnel for localhost:{self.local_port}...")
        
        try:
            self._ngrok_process = subprocess.Popen(
                ["ngrok", "http", str(self.local_port), "--region", self.region],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ngrok to start
            time.sleep(3)
            
            # Get tunnel info
            if self._fetch_tunnel_info():
                self._running = True
                
                # Start monitor thread
                self._stop_event.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True
                )
                self._monitor_thread.start()
                
                # Save config
                self._save_config()
                
                print(f"[NGB] Tunnel started successfully!")
                print(f"[NGB] Public URL: {self.public_url}")
                print(f"[NGB] API accessible at: {self.public_url}/docs")
                
                return True
            else:
                print("[NGB] Failed to get tunnel info")
                self.stop()
                return False
                
        except Exception as e:
            print(f"[NGB] Failed to start tunnel: {e}")
            return False
    
    def _fetch_tunnel_info(self) -> bool:
        """Fetch tunnel information from ngrok API"""
        try:
            # Ngrok API is at localhost:4040
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                
                self.tunnels = []
                for t in tunnels:
                    tunnel = TunnelInfo(
                        tunnel_id=t.get("name", "unknown"),
                        name=t.get("name", "unknown"),
                        proto=t.get("proto", "unknown"),
                        public_url=t.get("public_url", ""),
                        local_addr=t.get("config", {}).get("addr", ""),
                        created_at=datetime.utcnow().isoformat()
                    )
                    self.tunnels.append(tunnel)
                    
                    # Set primary public URL (prefer https)
                    if tunnel.proto == "https" or not self.public_url:
                        self.public_url = tunnel.public_url
                
                return len(self.tunnels) > 0
            
            return False
            
        except Exception as e:
            print(f"[NGB] Error fetching tunnel info: {e}")
            return False
    
    def _monitor_loop(self):
        """Monitor tunnel health"""
        while self._running and not self._stop_event.is_set():
            try:
                # Check if ngrok is still running
                if self._ngrok_process and self._ngrok_process.poll() is not None:
                    print("[NGB] ngrok process died, attempting restart...")
                    self._stop_event.wait(5)
                    self.start()
                
                # Refresh tunnel info
                self._fetch_tunnel_info()
                
                # Wait before next check
                self._stop_event.wait(30)
                
            except Exception as e:
                print(f"[NGB] Monitor error: {e}")
                self._stop_event.wait(10)
    
    def stop(self):
        """Stop ngrok tunnel"""
        self._running = False
        self._stop_event.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        if self._ngrok_process:
            self._ngrok_process.terminate()
            try:
                self._ngrok_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._ngrok_process.kill()
            
            self._ngrok_process = None
        
        self.tunnels = []
        self.public_url = None
        
        print("[NGB] Tunnel stopped")
    
    def get_public_url(self) -> Optional[str]:
        """Get the public URL"""
        return self.public_url
    
    def get_api_url(self) -> Optional[str]:
        """Get API base URL"""
        if self.public_url:
            return f"{self.public_url}/api/v1"
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return {
            "running": self._running,
            "public_url": self.public_url,
            "local_port": self.local_port,
            "tunnels": [t.to_dict() for t in self.tunnels],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _save_config(self):
        """Save current configuration"""
        config = {
            "local_port": self.local_port,
            "region": self.region,
            "public_url": self.public_url,
            "created_at": datetime.utcnow().isoformat()
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def register_webhook(self, path: str, handler: Callable):
        """Register a webhook handler"""
        self.webhook_handlers[path] = handler
        print(f"[NGB] Webhook registered: {path}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the public connection"""
        if not self.public_url:
            return {"success": False, "error": "No public URL available"}
        
        try:
            start = time.time()
            response = requests.get(f"{self.public_url}/health", timeout=10)
            latency = (time.time() - start) * 1000
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": round(latency, 2),
                "public_url": self.public_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "public_url": self.public_url,
                "timestamp": datetime.utcnow().isoformat()
            }


class GLMAccessPoint:
    """
    High-level GLM access point that combines API server and ngrok
    """
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.api_server = None
        self.ngrok_bridge = NgrokBridge(local_port=port)
        self.access_info: Dict[str, Any] = {}
        
    def start(self, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Start the complete GLM access point
        
        Returns:
            Access information including public URL
        """
        print("=" * 60)
        print("KISWARM7.0 - GLM ACCESS POINT")
        print("=" * 60)
        
        # Import and start API server
        try:
            from m106_api_server import KISWARM_API_Server
            
            # Start API server in background
            import threading
            self.api_server = KISWARM_API_Server(port=self.port)
            
            api_thread = threading.Thread(
                target=self.api_server.run,
                daemon=True
            )
            api_thread.start()
            
            print(f"[GLM-AP] API Server started on port {self.port}")
            time.sleep(2)  # Wait for server to start
            
        except Exception as e:
            print(f"[GLM-AP] Warning: Could not start API server: {e}")
        
        # Start ngrok bridge
        print("[GLM-AP] Starting public access tunnel...")
        if self.ngrok_bridge.start(auth_token):
            self.access_info = {
                "status": "active",
                "public_url": self.ngrok_bridge.get_public_url(),
                "api_docs": f"{self.ngrok_bridge.get_public_url()}/docs",
                "websocket": f"{self.ngrok_bridge.get_public_url()}/ws",
                "local_port": self.port,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print("\n" + "=" * 60)
            print("GLM ACCESS POINT READY!")
            print("=" * 60)
            print(f"Public URL: {self.access_info['public_url']}")
            print(f"API Docs:   {self.access_info['api_docs']}")
            print(f"WebSocket:  {self.access_info['websocket']}")
            print("=" * 60)
            
            # Save access info
            access_file = Path("/home/z/my-project/kiswarm7_ngrok/access_info.json")
            with open(access_file, 'w') as f:
                json.dump(self.access_info, f, indent=2)
            
            return self.access_info
        else:
            return {
                "status": "failed",
                "error": "Could not establish public access",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def stop(self):
        """Stop the access point"""
        self.ngrok_bridge.stop()
        print("[GLM-AP] Access point stopped")
    
    def get_access_info(self) -> Dict[str, Any]:
        """Get current access information"""
        return self.access_info


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m107 NGROK BRIDGE")
    print("PUBLIC ACCESS MODULE")
    print("=" * 60)
    
    # Create bridge
    bridge = NgrokBridge(local_port=8765)
    
    # Start tunnel
    print("\n[TEST] Starting ngrok tunnel...")
    # Note: You may need to provide your ngrok auth token
    # bridge.start(auth_token="your_ngrok_auth_token")
    bridge.start()
    
    if bridge._running:
        # Get status
        print("\n[TEST] Tunnel Status:")
        print(json.dumps(bridge.get_status(), indent=2))
        
        # Test connection
        print("\n[TEST] Testing connection...")
        result = bridge.test_connection()
        print(json.dumps(result, indent=2))
        
        # Keep running
        print("\n[TEST] Tunnel active. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[TEST] Stopping...")
            bridge.stop()
    else:
        print("[TEST] Failed to start tunnel")
        print("[TEST] Note: ngrok may need to be installed or configured")
        print("[TEST] Visit https://ngrok.com to get started")
