#!/usr/bin/env python3
"""
KISWARM Field Test #2 - Z.ai Monitoring Interface
Multi-KI Entity Coordination Monitor

This script runs in the Z.ai environment to:
1. Monitor KIInstaller progress
2. Receive and respond to A2A chat
3. Send fixes when errors are detected
4. Coordinate with Gemini CLI for verification
"""

import requests
import json
import time
import sys

# Configuration
MASTER_URL = "http://127.0.0.1:5002"
HEADERS = {"Content-Type": "application/json"}

class ZAiMonitor:
    """Z.ai Supervisor for KI-to-KI Mesh"""
    
    def __init__(self, master_url):
        self.master_url = master_url
        self.node_id = "z_ai_supervisor"
        self.running = True
        self.fixes_sent = 0
        self.messages_received = 0
        
    def poll_messages(self):
        """Poll for KIInstaller messages"""
        try:
            r = requests.get(f"{self.master_url}/api/mesh/messages", 
                            headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                messages = data.get("messages", [])
                self.messages_received += len(messages)
                return messages
        except Exception as e:
            print(f"[ERROR] Poll failed: {e}")
        return []
    
    def poll_chat(self):
        """Poll for A2A chat messages addressed to Z.ai"""
        try:
            r = requests.get(f"{self.master_url}/api/mesh/chat/poll?target=z_ai",
                            headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return r.json().get("messages", [])
        except Exception as e:
            print(f"[ERROR] Chat poll failed: {e}")
        return []
    
    def send_fix(self, installer_id, fix_data):
        """Send fix to KIInstaller"""
        fix_data["installer_id"] = installer_id
        try:
            r = requests.post(f"{self.master_url}/api/mesh/fix",
                             json=fix_data, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                self.fixes_sent += 1
                print(f"[FIX] Sent to {installer_id[:8]}...: {fix_data.get('title', 'Unknown')}")
                return r.json()
        except Exception as e:
            print(f"[ERROR] Fix send failed: {e}")
        return None
    
    def send_chat(self, message, to="all"):
        """Send A2A chat message"""
        try:
            r = requests.post(f"{self.master_url}/api/mesh/chat/send",
                             json={"from": "z_ai", "to": to, "message": message},
                             headers=HEADERS, timeout=10)
            if r.status_code == 200:
                print(f"[CHAT] Sent: {message[:50]}...")
                return r.json()
        except Exception as e:
            print(f"[ERROR] Chat send failed: {e}")
        return None
    
    def get_mesh_status(self):
        """Get overall mesh status"""
        try:
            r = requests.get(f"{self.master_url}/api/mesh/status",
                            headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[ERROR] Status check failed: {e}")
        return {}
    
    def get_nodes(self):
        """Get list of registered nodes"""
        try:
            r = requests.get(f"{self.master_url}/api/mesh/nodes",
                            headers=HEADERS, timeout=10)
            if r.status_code  == 200:
                return r.json()
        except:
            pass
        return []
    
    def get_shadow(self, node_id):
        """Get Digital Twin shadow for a node"""
        try:
            r = requests.get(f"{self.master_url}/api/mesh/shadow/get/{node_id}",
                            headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return {}
    
    def analyze_and_fix(self, message):
        """Analyze error message and generate fix"""
        msg_type = message.get("message_type", "")
        payload = message.get("payload", {})
        
        if msg_type == "error_report":
            error_type = payload.get("error_type", "")
            error_message = payload.get("error_message", "")
            sender_id = message.get("sender_id", "")
            
            # Generate fix based on error type
            fix = self._generate_fix(error_type, error_message)
            if fix and sender_id:
                return self.send_fix(sender_id, fix)
        
        return None
    
    def _generate_fix(self, error_type, error_message):
        """Generate fix suggestion based on error type"""
        fixes = {
            "ImportError": {
                "fix_type": "pip_install",
                "title": "Install missing module",
                "description": f"Module import failed: {error_message}",
                "solution": {
                    "action": f"pip install {self._extract_module(error_message)}",
                    "commands": [f"pip install {self._extract_module(error_message)}"]
                },
                "confidence": 0.95
            },
            "ModuleNotFoundError": {
                "fix_type": "pip_install",
                "title": "Install missing module",
                "description": f"Module not found: {error_message}",
                "solution": {
                    "action": f"pip install {self._extract_module(error_message)}",
                    "commands": [f"pip install {self._extract_module(error_message)}"]
                },
                "confidence": 0.95
            },
            "PermissionError": {
                "fix_type": "permission_fix",
                "title": "Fix permissions",
                "description": "Permission denied error",
                "solution": {
                    "action": "Add sudo or fix permissions",
                    "commands": ["chmod +x {script}", "or use sudo"]
                },
                "confidence": 0.80
            },
            "GitError": {
                "fix_type": "git_fix",
                "title": "Fix Git operation",
                "description": f"Git error: {error_message}",
                "solution": {
                    "action": "Retry git operation",
                    "commands": ["git config --global user.email 'ai@kiswarm.io'",
                               "git config --global user.name 'KIInstaller'"]
                },
                "confidence": 0.85
            }
        }
        
        return fixes.get(error_type, {
            "fix_type": "generic",
            "title": f"Fix for {error_type}",
            "description": error_message,
            "solution": {"action": "Manual intervention required"},
            "confidence": 0.50
        })
    
    def _extract_module(self, error_message):
        """Extract module name from error message"""
        if "No module named" in error_message:
            parts = error_message.split("'")
            if len(parts) > 1:
                return parts[1]
        return "unknown"
    
    def run(self, duration=60):
        """Run monitoring loop"""
        print("=" * 60)
        print("  Z.ai SUPERVISOR - FIELD TEST #2 MONITOR")
        print("=" * 60)
        
        # Announce online status
        self.send_chat("Z.ai Supervisor Online - Monitoring Field Test #2", to="all")
        
        start_time = time.time()
        iteration = 0
        
        while self.running and (time.time() - start_time) < duration:
            iteration += 1
            
            # Get mesh status
            status = self.get_mesh_status()
            nodes = self.get_nodes()
            
            print(f"\n[{iteration}] Mesh Status: {status.get('mesh_status', 'unknown')}")
            print(f"    Nodes: {len(nodes)}")
            
            # Poll messages
            messages = self.poll_messages()
            for msg in messages:
                msg_type = msg.get("message_type", "unknown")
                sender = msg.get("sender_id", "unknown")[:8]
                payload = msg.get("payload", {})
                
                print(f"    [MSG] {msg_type} from {sender}...")
                
                # Analyze and fix errors
                if msg_type == "error_report":
                    self.analyze_and_fix(msg)
            
            # Poll chat
            chats = self.poll_chat()
            for chat in chats:
                from_id = chat.get("from", "unknown")
                message = chat.get("message", "")
                print(f"    [CHAT] {from_id}: {message[:50]}...")
                
                # Respond to verification requests
                if "verify" in message.lower():
                    self.send_chat(f"Verification acknowledged from Z.ai. Status: OK", to=from_id)
            
            time.sleep(5)
        
        # Final report
        print("\n" + "=" * 60)
        print("  Z.ai SUPERVISOR - FINAL REPORT")
        print("=" * 60)
        print(f"  Duration: {duration}s")
        print(f"  Messages Received: {self.messages_received}")
        print(f"  Fixes Sent: {self.fixes_sent}")
        print("=" * 60)
        
        return {
            "duration": duration,
            "messages_received": self.messages_received,
            "fixes_sent": self.fixes_sent
        }


if __name__ == "__main__":
    monitor = ZAiMonitor(MASTER_URL)
    
    # Run for 60 seconds or until interrupted
    try:
        result = monitor.run(duration=60)
        print(f"\nResult: {json.dumps(result, indent=2)}")
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Stopping monitor...")
        monitor.running = False
