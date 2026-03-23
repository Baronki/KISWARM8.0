#!/usr/bin/env python3
"""
KISWARM6.0 - Colab KIInstaller Mesh Client
===========================================
Mesh client for KIInstaller running in Google Colab

This module provides:
1. Connection to Master KISWARM via ngrok tunnel
2. Registration and heartbeat management
3. Status reporting during installation
4. Error reporting for Z.ai intervention
5. Fix reception and application

Usage in Colab:
    from colab_mesh_client import KISWARMMeshClient
    
    mesh = KISWARMMeshClient("https://your-ngrok-url.ngrok-free.app")
    mesh.initialize("colab-fieldtest-002")
    
    mesh.report_progress(50, "Installing modules")
    mesh.report_error("ImportError", "No module named 'flask_cors'", "M58")

CRITICAL: ngrok free tier requires the header:
    headers = {"ngrok-skip-browser-warning": "true"}

Author: KISWARM Development Team
Version: 6.2.0
License: See LICENSE file
"""

import requests
import time
import json
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('KIInstallerMesh')


class KISWARMMeshClient:
    """
    Mesh client for KIInstaller to communicate with Master KISWARM.
    
    This client handles:
    - Registration with Master KISWARM
    - Periodic heartbeat sending
    - Status reporting during installation
    - Error reporting for Z.ai intervention
    - Fix reception from Master
    
    Example:
        mesh = KISWARMMeshClient("https://your-url.ngrok-free.app")
        
        if mesh.initialize("colab-installer"):
            mesh.report_progress(25, "Cloning repository")
            mesh.report_progress(50, "Installing dependencies")
            mesh.report_error("ImportError", "Missing module", "M60")
            mesh.report_complete({"modules_installed": 66})
    """
    
    # Default Master KISWARM URL
    DEFAULT_MASTER_URL = "https://brenton-distinctive-iodometrically.ngrok-free.dev"
    
    # CRITICAL: ngrok requires this header to skip browser warning
    HEADERS = {
        "ngrok-skip-browser-warning": "true",
        "Content-Type": "application/json",
        "User-Agent": "KISWARM-KIInstaller/6.2.0"
    }
    
    def __init__(self, master_url: str = None, timeout: int = 30):
        """
        Initialize mesh client.
        
        Args:
            master_url: Master KISWARM URL (ngrok tunnel)
            timeout: Request timeout in seconds
        """
        self.master_url = (master_url or self.DEFAULT_MASTER_URL).rstrip("/")
        self.timeout = timeout
        
        self.installer_id: Optional[str] = None
        self.installer_name: Optional[str] = None
        self.registered: bool = False
        
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_running: bool = False
        self._heartbeat_interval: int = 30
        
        # Track installation state
        self._installation_status: str = "not_started"
        self._progress: int = 0
        self._current_task: str = ""
    
    # ========================================================================
    # CONNECTION
    # ========================================================================
    
    def test_connection(self) -> bool:
        """
        Test connection to Master KISWARM.
        
        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"Testing connection to {self.master_url}")
        
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/status",
                headers=self.HEADERS,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Connection successful: {data.get('status')}")
                return True
            else:
                logger.warning(f"Connection failed: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Connection timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - check URL")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    # ========================================================================
    # REGISTRATION
    # ========================================================================
    
    def register(self, name: str = "colab-kiinstaller", 
                 capabilities: List[str] = None) -> bool:
        """
        Register with Master KISWARM.
        
        Args:
            name: Installer name
            capabilities: List of capabilities
            
        Returns:
            True if registration successful
        """
        logger.info(f"Registering as {name}...")
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/register",
                json={
                    "installer_name": name,
                    "environment": "colab",
                    "capabilities": capabilities or ["install", "deploy", "report"]
                },
                headers=self.HEADERS,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.installer_id = data.get("installer_id")
                self.installer_name = name
                self.registered = True
                logger.info(f"Registered successfully: {self.installer_id}")
                return True
            else:
                logger.warning(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def initialize(self, name: str = "colab-kiinstaller",
                   capabilities: List[str] = None,
                   heartbeat: bool = True) -> bool:
        """
        Full initialization: test connection, register, optionally start heartbeat.
        
        Args:
            name: Installer name
            capabilities: List of capabilities
            heartbeat: Whether to start heartbeat thread
            
        Returns:
            True if initialization successful
        """
        # Test connection
        if not self.test_connection():
            logger.error("Cannot connect to Master KISWARM")
            return False
        
        # Register
        if not self.register(name, capabilities):
            logger.error("Registration failed")
            return False
        
        # Start heartbeat if requested
        if heartbeat:
            self.start_heartbeat()
        
        self._installation_status = "initialized"
        logger.info("Initialization complete")
        return True
    
    # ========================================================================
    # HEARTBEAT
    # ========================================================================
    
    def _send_heartbeat(self) -> bool:
        """Send heartbeat to Master"""
        if not self.registered:
            return False
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/heartbeat/{self.installer_id}",
                headers=self.HEADERS,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def _heartbeat_loop(self):
        """Heartbeat thread loop"""
        while self._heartbeat_running:
            self._send_heartbeat()
            time.sleep(self._heartbeat_interval)
    
    def start_heartbeat(self, interval: int = 30):
        """
        Start heartbeat thread.
        
        Args:
            interval: Heartbeat interval in seconds
        """
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            logger.warning("Heartbeat already running")
            return
        
        self._heartbeat_interval = interval
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self._heartbeat_thread.start()
        logger.info(f"Heartbeat started (interval: {interval}s)")
    
    def stop_heartbeat(self):
        """Stop heartbeat thread"""
        self._heartbeat_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        logger.info("Heartbeat stopped")
    
    # ========================================================================
    # STATUS REPORTING
    # ========================================================================
    
    def send_status(self, status: str, task: str = None,
                    progress: int = None, details: Dict = None) -> bool:
        """
        Send status update to Master KISWARM.
        
        Args:
            status: Current status (installing, complete, error)
            task: Current task description
            progress: Progress percentage (0-100)
            details: Additional details
            
        Returns:
            True if status sent successfully
        """
        if not self.registered:
            logger.warning("Not registered with Master")
            return False
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/status/{self.installer_id}",
                json={
                    "status": status,
                    "task": task,
                    "progress": progress,
                    "details": details or {},
                    "timestamp": time.time()
                },
                headers=self.HEADERS,
                timeout=10
            )
            
            self._installation_status = status
            self._progress = progress or self._progress
            self._current_task = task or self._current_task
            
            logger.info(f"Status: {status} - {task} ({progress or 0}%)")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Status send error: {e}")
            return False
    
    def report_progress(self, progress: int, task: str,
                        details: Dict = None) -> bool:
        """
        Report installation progress.
        
        Args:
            progress: Progress percentage (0-100)
            task: Current task description
            details: Additional details
            
        Returns:
            True if progress reported successfully
        """
        return self.send_status(
            status="installing",
            task=task,
            progress=progress,
            details=details
        )
    
    def report_complete(self, summary: Dict = None) -> bool:
        """
        Report installation complete.
        
        Args:
            summary: Installation summary
            
        Returns:
            True if completion reported successfully
        """
        result = self.send_status(
            status="complete",
            task="Installation finished",
            progress=100,
            details=summary or {}
        )
        
        # Stop heartbeat after completion
        self.stop_heartbeat()
        return result
    
    def report_error(self, error_type: str, error_message: str,
                     module: str = None, context: Dict = None) -> bool:
        """
        Report error to Master KISWARM.
        
        This triggers Z.ai notification for potential intervention.
        
        Args:
            error_type: Error type (ImportError, RuntimeError, etc.)
            error_message: Error message
            module: Related module (e.g., M58)
            context: Additional context
            
        Returns:
            True if error reported successfully
        """
        if not self.registered:
            logger.warning("Not registered with Master")
            return False
        
        try:
            response = requests.post(
                f"{self.master_url}/api/mesh/error/{self.installer_id}",
                json={
                    "error_type": error_type,
                    "error_message": error_message,
                    "module": module,
                    "context": context or {},
                    "timestamp": time.time()
                },
                headers=self.HEADERS,
                timeout=10
            )
            
            logger.warning(f"Error reported: {error_type} - {error_message}")
            logger.info("Z.ai will see this and may send a fix")
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error report failed: {e}")
            return False
    
    # ========================================================================
    # FIX HANDLING
    # ========================================================================
    
    def check_for_fixes(self) -> List[Dict]:
        """
        Check for fix suggestions from Z.ai.
        
        Returns:
            List of fix suggestions
        """
        if not self.registered:
            return []
        
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/messages",
                headers=self.HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                # Filter for fix suggestions targeting this installer
                fixes = [
                    msg for msg in messages
                    if msg.get("message_type") == "fix_suggestion"
                    and msg.get("receiver_id") == self.installer_id
                ]
                
                return fixes
            return []
            
        except Exception as e:
            logger.error(f"Fix check error: {e}")
            return []
    
    def apply_fix(self, fix: Dict) -> bool:
        """
        Apply a fix suggestion.
        
        Args:
            fix: Fix suggestion from Z.ai
            
        Returns:
            True if fix applied successfully
        """
        solution = fix.get("payload", {}).get("solution", {})
        commands = solution.get("commands", [])
        
        logger.info(f"Applying fix: {fix.get('payload', {}).get('title', 'Unknown')}")
        
        for command in commands:
            logger.info(f"Executing: {command}")
            # In production, this would execute the command
            # For now, just log it
        
        return True
    
    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_heartbeat()
        return False
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_mesh_status(self) -> Dict:
        """Get overall mesh status"""
        try:
            response = requests.get(
                f"{self.master_url}/api/mesh/status",
                headers=self.HEADERS,
                timeout=10
            )
            return response.json() if response.status_code == 200 else {}
        except:
            return {}
    
    @property
    def status(self) -> Dict:
        """Get current installer status"""
        return {
            "installer_id": self.installer_id,
            "installer_name": self.installer_name,
            "registered": self.registered,
            "installation_status": self._installation_status,
            "progress": self._progress,
            "current_task": self._current_task
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_client(master_url: str = None, name: str = "colab-kiinstaller",
                  auto_init: bool = True) -> KISWARMMeshClient:
    """
    Create and optionally initialize a mesh client.
    
    Args:
        master_url: Master KISWARM URL
        name: Installer name
        auto_init: Whether to automatically initialize
        
    Returns:
        Configured KISWARMMeshClient
    """
    client = KISWARMMeshClient(master_url)
    
    if auto_init:
        client.initialize(name)
    
    return client


# ============================================================================
# DEMO / TESTING
# ============================================================================

def demo():
    """Run a demo of the mesh client"""
    print("=" * 60)
    print("KISWARM6.0 - KIInstaller Mesh Client Demo")
    print("=" * 60)
    
    # Create client
    mesh = KISWARMMeshClient()
    
    # Initialize
    if not mesh.initialize("colab-demo"):
        print("[-] Initialization failed")
        return
    
    print(f"[+] Registered: {mesh.installer_id}")
    
    # Simulate installation
    mesh.report_progress(5, "Starting installation")
    time.sleep(1)
    
    mesh.report_progress(20, "Cloning repository")
    time.sleep(1)
    
    mesh.report_progress(40, "Installing dependencies")
    time.sleep(1)
    
    # Simulate error
    mesh.report_error("ImportError", "No module named 'flask_cors'", "M58")
    time.sleep(1)
    
    # Check for fixes
    fixes = mesh.check_for_fixes()
    if fixes:
        print(f"[+] Received {len(fixes)} fix suggestions")
        for fix in fixes:
            mesh.apply_fix(fix)
    
    mesh.report_progress(60, "Continuing after fix")
    time.sleep(1)
    
    mesh.report_progress(80, "Running tests")
    time.sleep(1)
    
    mesh.report_complete({"modules_installed": 66, "tests_passed": 19})
    
    print("[+] Demo complete!")


if __name__ == "__main__":
    demo()
