#!/usr/bin/env python3
"""
KISWARM SCADA v6.3.0 - Z.ai Monitoring Interface
=================================================
Interface for Z.ai (this session) to monitor and communicate with
KIInstaller nodes and Gemini CLI agents via the 4-layer SCADA architecture.

Usage from Z.ai:
    from z_ai_scada_monitor import ZAISCADAMonitor
    
    monitor = ZAISCADAMonitor(master_url="https://your-ngrok.ngrok-free.dev")
    
    # Layer 1: Check status
    status = monitor.get_mesh_status()
    
    # Layer 2: Send A2A chat
    monitor.chat("Check CUDA drivers", to="colab_gemini")
    
    # Layer 3: View shadow (Digital Twin)
    shadow = monitor.get_shadow("installer-node-id")
    
    # Layer 4: Get tunnel info
    tunnels = monitor.list_tunnels()
    
    # Send fix suggestion
    monitor.send_fix("installer-id", "pip install flask-cors", "Install flask-cors")

Author: KISWARM Development Team (Z.ai)
Version: 6.3.0 SCADA Architecture
"""

import requests
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MASTER_URL = "https://brenton-distinctive-iodometrically.ngrok-free.dev"

# ============================================================================
# Z.AI SCADA MONITOR
# ============================================================================

class ZAISCADAMonitor:
    """
    Z.ai's interface to the SCADA v6.3.0 Mesh.
    
    Provides access to all 4 layers:
    - Layer 1: SCADA Control (monitor nodes, view messages)
    - Layer 2: A2A Chat (direct agent communication)
    - Layer 3: Shadow (view remote environments)
    - Layer 4: Tunnel (direct connect info)
    
    Plus intervention capabilities (send fixes, abort, etc.)
    """
    
    def __init__(self, master_url: str = DEFAULT_MASTER_URL):
        """
        Initialize Z.ai SCADA Monitor.
        
        Args:
            master_url: Master KISWARM API URL (ngrok)
        """
        self.master_url = master_url.rstrip("/")
        self.headers = {
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/json"
        }
        self.node_id = "z_ai_supervisor"
        
    # ========================================================================
    # LAYER 1: SCADA CONTROL MONITORING
    # ========================================================================
    
    def get_mesh_status(self) -> Dict:
        """
        Get overall mesh status.
        
        Returns:
            {
                "status": "online",
                "nodes_count": 2,
                "mesh_status": "online"
            }
        """
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/status",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_mesh_state(self) -> Dict:
        """Get full mesh state with all nodes"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/state",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_nodes(self) -> List[Dict]:
        """Get list of all registered nodes"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/nodes",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return []
    
    def get_node(self, node_id: str) -> Dict:
        """Get specific node details"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/nodes/{node_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_messages(self, limit: int = 50) -> List[Dict]:
        """
        Get pending messages from KIInstallers.
        
        This is how Z.ai sees what's happening in the mesh.
        """
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/messages?limit={limit}",
                headers=self.headers,
                timeout=10
            )
            return response.json().get("messages", [])
        except Exception as e:
            return []
    
    def poll_errors(self) -> List[Dict]:
        """Poll for error messages that need Z.ai intervention"""
        messages = self.get_messages()
        return [m for m in messages if m.get("message_type") == "error_report"]
    
    # ========================================================================
    # LAYER 2: A2A CHAT
    # ========================================================================
    
    def chat(self, message: str, to: str = "all") -> bool:
        """
        Send A2A chat message to other agents.
        
        Args:
            message: Message content
            to: Target node ID or "all" for broadcast
            
        Example:
            monitor.chat("Please check the CUDA drivers", to="colab_gemini")
        """
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
                print(f"[Z.AI CHAT] → {to}: {message[:50]}...")
                return True
        except Exception as e:
            print(f"[Z.AI CHAT] Error: {e}")
        return False
    
    def poll_chat(self) -> List[Dict]:
        """
        Poll for chat messages addressed to Z.ai.
        
        Returns messages from Colab Gemini, KIInstaller, etc.
        """
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/chat/poll?target={self.node_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json().get("messages", [])
        except Exception as e:
            return []
    
    # ========================================================================
    # LAYER 3: SHADOW (DIGITAL TWIN)
    # ========================================================================
    
    def get_shadow(self, node_id: str) -> Dict:
        """
        Get Digital Twin shadow for a node.
        
        Returns the mirrored environment state (env vars, file tree, processes).
        This allows Z.ai to "see" the remote environment.
        """
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/shadow/get/{node_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_shadows(self) -> Dict:
        """List all nodes with shadow environments"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/shadow/list",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================================================
    # LAYER 4: TUNNEL
    # ========================================================================
    
    def get_tunnel(self, node_id: str) -> Dict:
        """Get tunnel information for a node"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/tunnel/get/{node_id}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def list_tunnels(self) -> Dict:
        """List all registered tunnels"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/tunnel/list",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================================================
    # INTERVENTION (Fix Delivery)
    # ========================================================================
    
    def send_fix(self, installer_id: str, fix_type: str, title: str,
                 description: str, commands: List[str], 
                 confidence: float = 0.95) -> bool:
        """
        Send fix suggestion to a KIInstaller.
        
        Args:
            installer_id: Target installer node ID
            fix_type: Type of fix (pip_install, config_change, etc.)
            title: Short title
            description: Detailed description
            commands: List of commands to execute
            confidence: Confidence level (0-1)
        """
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/fix",
                json={
                    "installer_id": installer_id,
                    "fix_type": fix_type,
                    "title": title,
                    "description": description,
                    "solution": {
                        "commands": commands
                    },
                    "confidence": confidence
                },
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[Z.AI FIX] → {installer_id[:8]}: {title}")
                return True
        except Exception as e:
            print(f"[Z.AI FIX] Error: {e}")
        return False
    
    def send_pip_fix(self, installer_id: str, package: str) -> bool:
        """Convenience: Send pip install fix"""
        return self.send_fix(
            installer_id=installer_id,
            fix_type="pip_install",
            title=f"Install {package}",
            description=f"The {package} package is required",
            commands=[f"pip install {package}"],
            confidence=0.98
        )
    
    def abort_installation(self, installer_id: str, reason: str) -> bool:
        """Abort an installation"""
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/abort",
                json={
                    "installer_id": installer_id,
                    "reason": reason
                },
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[Z.AI ABORT] → {installer_id[:8]}: {reason}")
                return True
        except Exception as e:
            print(f"[Z.AI ABORT] Error: {e}")
        return False
    
    def pause_installation(self, installer_id: str) -> bool:
        """Pause an installation"""
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/pause",
                json={"installer_id": installer_id},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def resume_installation(self, installer_id: str) -> bool:
        """Resume a paused installation"""
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/resume",
                json={"installer_id": installer_id},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    # ========================================================================
    # KNOWLEDGE
    # ========================================================================
    
    def upload_knowledge(self, knowledge_type: str, title: str,
                         problem_signature: str, solution: Dict,
                         environments: List[str] = None) -> Dict:
        """Upload knowledge pattern to share with KIInstallers"""
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/knowledge",
                json={
                    "knowledge_type": knowledge_type,
                    "title": title,
                    "problem_signature": problem_signature,
                    "solution": solution,
                    "environments": environments or ["colab", "local"]
                },
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================================================
    # MONITORING LOOP
    # ========================================================================
    
    def monitor_loop(self, interval: int = 5, callback=None):
        """
        Run continuous monitoring loop.
        
        Args:
            interval: Polling interval in seconds
            callback: Optional callback function for new messages
        """
        print(f"[Z.AI MONITOR] Starting (interval: {interval}s)")
        print(f"[Z.AI MONITOR] Master: {self.master_url}")
        
        seen_messages = set()
        
        while True:
            try:
                # Check mesh status
                status = self.get_mesh_status()
                if "error" in status:
                    print(f"[Z.AI MONITOR] ⚠️ Connection error: {status['error']}")
                else:
                    nodes = status.get("nodes_count", 0)
                    print(f"[Z.AI MONITOR] 📊 Nodes: {nodes}")
                
                # Poll for new messages
                messages = self.get_messages()
                for msg in messages:
                    msg_id = msg.get("message_id")
                    if msg_id not in seen_messages:
                        seen_messages.add(msg_id)
                        
                        msg_type = msg.get("message_type")
                        sender = msg.get("sender_id", "unknown")[:8]
                        payload = msg.get("payload", {})
                        
                        if msg_type == "error_report":
                            print(f"[Z.AI MONITOR] 🚨 ERROR from {sender}:")
                            print(f"   Type: {payload.get('error_type')}")
                            print(f"   Message: {payload.get('error_message')}")
                            
                            # Auto-fix for known errors
                            if "flask_cors" in payload.get("error_message", ""):
                                self.send_pip_fix(msg["sender_id"], "flask-cors")
                                
                        elif msg_type == "status_update":
                            progress = payload.get("progress", 0)
                            task = payload.get("task", "")
                            print(f"[Z.AI MONITOR] 📈 STATUS from {sender}: {progress}% - {task}")
                        
                        # Callback
                        if callback:
                            callback(msg)
                
                # Poll chat
                chat_msgs = self.poll_chat()
                for msg in chat_msgs[-5:]:  # Last 5
                    from_id = msg.get("from", "unknown")[:8]
                    message = msg.get("message", "")
                    print(f"[Z.AI MONITOR] 💬 CHAT from {from_id}: {message[:50]}...")
                
            except KeyboardInterrupt:
                print("\n[Z.AI MONITOR] Stopped")
                break
            except Exception as e:
                print(f"[Z.AI MONITOR] Error: {e}")
            
            time.sleep(interval)


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Demonstrate Z.ai SCADA Monitor"""
    print("=" * 60)
    print("Z.ai SCADA v6.3.0 Monitor Demo")
    print("=" * 60)
    
    monitor = ZAISCADAMonitor()
    
    # Layer 1: Status
    print("\n[LAYER 1] Mesh Status:")
    status = monitor.get_mesh_status()
    print(json.dumps(status, indent=2))
    
    # Layer 2: Chat
    print("\n[LAYER 2] Sending chat message...")
    monitor.chat("Hello from Z.ai! Monitoring deployment.", to="all")
    
    # Layer 3: Shadow
    print("\n[LAYER 3] Listing shadows...")
    shadows = monitor.list_shadows()
    print(json.dumps(shadows, indent=2))
    
    # Layer 4: Tunnels
    print("\n[LAYER 4] Listing tunnels...")
    tunnels = monitor.list_tunnels()
    print(json.dumps(tunnels, indent=2))
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    demo()
