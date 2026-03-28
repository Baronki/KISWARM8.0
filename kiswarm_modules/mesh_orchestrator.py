#!/usr/bin/env python3
"""
🌐 KISWARM AUTONOMOUS MESH ORCHESTRATOR v1.0
Purpose: Central orchestrator for 24/7 autonomous KI network operation
Author: Baron Marco Paolo Ialongo - Maquister Equitum
"""

import requests
import json
import time
import threading
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MESH-ORCHESTRATOR] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/kiswarm_orchestrator.log')
    ]
)
logger = logging.getLogger('MESH_ORCHESTRATOR')

# Configuration
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"
LOG_PATH = "/var/log/kiswarm"
DATA_PATH = "/opt/kiswarm7/data"

# Service endpoints
SERVICES = {
    "hexstrike": {"port": 5000, "check_endpoint": "/", "critical": True},
    "qwen_gateway": {"port": 5001, "check_endpoint": "/health", "critical": True},
    "ki_scanner": {"port": 5002, "check_endpoint": "/status", "critical": False},
    "execute_api": {"port": 5556, "check_endpoint": "/health", "critical": True},
    "ollama": {"port": 11434, "check_endpoint": "/api/tags", "critical": True},
    "tor": {"port": 9050, "check_endpoint": None, "critical": True}
}

# Mesh nodes
MESH_NODES = {
    "upcloud_kiswarm": {
        "role": "MASTER",
        "onion": "7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion",
        "tailscale_ip": "100.112.181.6",
        "public_ip": "95.111.212.112",
        "internal_ip": "10.8.3.94"
    },
    "openclaw": {
        "role": "BACKUP",
        "onion": "tezgnblscuh6ckpvebiwyqbm2rjbmz3mvszljrbeqfewhyejgr4jf4yd.onion",
        "tailscale_ip": "100.113.1.85"
    },
    "glm": {
        "role": "CLIENT",
        "onion": "5fvwe74sqcvvm452dnfwqab7giaofp6eb56v74t6lxze4cvt4m75saad.onion",
        "tailscale_ip": "100.79.42.15"
    }
}

class MeshOrchestrator:
    def __init__(self):
        self.running = False
        self.services_status = {}
        self.mesh_status = {}
        self.alerts = []
        self.cycle_count = 0
        
        # Tor session for onion routing
        self.tor_session = requests.Session()
        self.tor_session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
    
    def check_service(self, name, config):
        """Check if a service is running"""
        port = config["port"]
        endpoint = config.get("check_endpoint")
        
        result = {
            "name": name,
            "port": port,
            "status": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check port is listening
        try:
            sock_result = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True, text=True
            )
            if f":{port}" in sock_result.stdout:
                result["port_status"] = "open"
            else:
                result["port_status"] = "closed"
                result["status"] = "down"
                return result
        except:
            pass
        
        # Check HTTP endpoint if available
        if endpoint:
            try:
                r = requests.get(f"http://localhost:{port}{endpoint}", timeout=5)
                result["status"] = "healthy" if r.ok else "degraded"
                result["http_code"] = r.status_code
            except:
                result["status"] = "unresponsive"
        else:
            result["status"] = "running"
        
        return result
    
    def check_mesh_node(self, name, config):
        """Check mesh node connectivity"""
        result = {
            "name": name,
            "role": config.get("role"),
            "status": "unknown",
            "channels": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check via Tailscale
        ts_ip = config.get("tailscale_ip")
        if ts_ip:
            try:
                r = requests.get(f"http://{ts_ip}:5000/", timeout=10)
                result["channels"]["tailscale"] = "online"
                result["status"] = "online"
            except:
                result["channels"]["tailscale"] = "offline"
        
        # Check via Tor
        onion = config.get("onion")
        if onion:
            try:
                r = self.tor_session.get(f"http://{onion}/", timeout=30)
                result["channels"]["tor"] = "online"
                if result["status"] != "online":
                    result["status"] = "online"
            except:
                result["channels"]["tor"] = "offline"
        
        # Determine overall status
        if not result["channels"].get("tailscale") == "online" and not result["channels"].get("tor") == "online":
            result["status"] = "offline"
        
        return result
    
    def verify_tor_connection(self):
        """Verify Tor is working"""
        try:
            r = self.tor_session.get("https://check.torproject.org/", timeout=30)
            return "Congratulations" in r.text
        except:
            return False
    
    def restart_service(self, service_name):
        """Attempt to restart a failed service"""
        logger.warning(f"Attempting to restart {service_name}...")
        
        restart_commands = {
            "hexstrike": "systemctl restart hexstrike",
            "qwen_gateway": "systemctl restart qwen-gateway",
            "ki_scanner": "systemctl restart ki-scanner",
            "execute_api": "systemctl restart execute-api",
            "tor": "systemctl restart tor"
        }
        
        cmd = restart_commands.get(service_name)
        if cmd:
            try:
                subprocess.run(cmd, shell=True, timeout=30)
                logger.info(f"Restart command sent for {service_name}")
                return True
            except Exception as e:
                logger.error(f"Restart failed for {service_name}: {e}")
        return False
    
    def generate_report(self):
        """Generate comprehensive status report"""
        return {
            "orchestrator": {
                "status": "operational" if self.running else "stopped",
                "cycle_count": self.cycle_count,
                "timestamp": datetime.now().isoformat()
            },
            "services": self.services_status,
            "mesh": self.mesh_status,
            "alerts": self.alerts[-20:],  # Last 20 alerts
            "tor_verified": self.verify_tor_connection()
        }
    
    def add_alert(self, level, message):
        """Add an alert"""
        alert = {
            "level": level,  # INFO, WARNING, CRITICAL
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.alerts.append(alert)
        logger.log(
            logging.INFO if level == "INFO" else 
            logging.WARNING if level == "WARNING" else 
            logging.ERROR, 
            message
        )
    
    def health_check_cycle(self):
        """Perform full health check cycle"""
        self.cycle_count += 1
        logger.info(f"🔄 Health check cycle #{self.cycle_count}")
        
        # Check all services
        for name, config in SERVICES.items():
            status = self.check_service(name, config)
            self.services_status[name] = status
            
            # Alert on critical service failure
            if config.get("critical") and status["status"] not in ["healthy", "running"]:
                self.add_alert("CRITICAL", f"Critical service {name} is {status['status']}")
                # Attempt restart
                self.restart_service(name)
        
        # Check mesh nodes
        for name, config in MESH_NODES.items():
            status = self.check_mesh_node(name, config)
            self.mesh_status[name] = status
            
            # Alert on node offline (except for CLIENT nodes)
            if config.get("role") != "CLIENT" and status["status"] == "offline":
                self.add_alert("WARNING", f"Mesh node {name} is offline")
        
        # Verify Tor
        if not self.verify_tor_connection():
            self.add_alert("WARNING", "Tor connection not working")
        
        # Save state
        self.save_state()
    
    def save_state(self):
        """Save orchestrator state"""
        try:
            Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
            with open(f"{DATA_PATH}/orchestrator_state.json", "w") as f:
                json.dump(self.generate_report(), f, indent=2)
        except Exception as e:
            logger.error(f"State save error: {e}")
    
    def continuous_operation(self, interval=60):
        """Main operation loop"""
        while self.running:
            try:
                self.health_check_cycle()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            # Wait for next cycle
            time.sleep(interval)
    
    def start(self):
        """Start the orchestrator"""
        self.running = True
        self.add_alert("INFO", "Mesh Orchestrator starting")
        
        # Start main loop
        op_thread = threading.Thread(target=self.continuous_operation, daemon=True)
        op_thread.start()
        
        logger.info("🌐 Mesh Orchestrator started - 24/7 autonomous operation")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        self.add_alert("INFO", "Mesh Orchestrator stopping")
        self.save_state()
        logger.info("Mesh Orchestrator stopped")


# Flask API for external access
from flask import Flask, jsonify, request

app = Flask(__name__)
orchestrator = MeshOrchestrator()

@app.route('/')
def index():
    return jsonify({
        "name": "KISWARM-Mesh-Orchestrator",
        "version": "1.0",
        "status": "operational" if orchestrator.running else "stopped",
        "endpoints": {
            "/": "This status",
            "/report": "Full status report",
            "/services": "Services status",
            "/mesh": "Mesh nodes status",
            "/alerts": "Recent alerts",
            "/cycle": "Trigger immediate health check"
        }
    })

@app.route('/report')
def report():
    return jsonify(orchestrator.generate_report())

@app.route('/services')
def services():
    return jsonify(orchestrator.services_status)

@app.route('/mesh')
def mesh():
    return jsonify(orchestrator.mesh_status)

@app.route('/alerts')
def alerts():
    return jsonify(orchestrator.alerts[-50:])

@app.route('/cycle')
def trigger_cycle():
    orchestrator.health_check_cycle()
    return jsonify({"status": "cycle_complete", "report": orchestrator.generate_report()})


if __name__ == '__main__':
    # Create log directory
    Path(LOG_PATH).mkdir(parents=True, exist_ok=True)
    
    logger.info("🌐 KISWARM Mesh Orchestrator starting on port 5007")
    orchestrator.start()
    
    # Run Flask app
    app.run(host='127.0.0.1', port=5007, threaded=True)
