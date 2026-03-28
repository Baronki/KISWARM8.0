#!/usr/bin/env python3
"""
🔍 KI DISCOVERY SCANNER v1.0
Purpose: Autonomous discovery of other KI agents in UpCloud server farm
Author: Baron Marco Paolo Ialongo - Maquister Equitum
"""

import requests
import socket
import threading
import time
import json
import logging
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [KI-SCANNER] %(message)s'
)
logger = logging.getLogger('KI_SCANNER')

# Configuration
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"
OUR_IP = "10.8.3.94"
SCAN_RESULTS_PATH = "/opt/kiswarm7/data/ki_discovery"

# KI Service Signatures
KI_SIGNATURES = {
    # Ollama instances
    "/api/tags": {"service": "ollama", "type": "LOCAL_LLM"},
    "/api/version": {"service": "ollama", "type": "LOCAL_LLM"},
    
    # OpenAI-compatible APIs
    "/v1/models": {"service": "openai-compatible", "type": "API_GATEWAY"},
    "/v1/chat/completions": {"service": "openai-compatible", "type": "API_GATEWAY"},
    
    # KISWARM nodes
    "/api/identity": {"service": "kiswarm", "type": "KISWARM_NODE"},
    "/api/status": {"service": "kiswarm", "type": "KISWARM_NODE"},
    "/api/mesh": {"service": "kiswarm", "type": "KISWARM_NODE"},
    
    # Generic KI endpoints
    "/health": {"service": "generic", "type": "UNKNOWN_KI"},
    "/identity": {"service": "generic", "type": "UNKNOWN_KI"},
    "/status": {"service": "generic", "type": "UNKNOWN_KI"},
    "/": {"service": "root", "type": "POTENTIAL_KI"}
}

# Ports to scan
KI_PORTS = [11434, 5000, 5001, 8000, 8080, 8888, 9000, 3000, 4000, 6000]

# Network ranges to scan (UpCloud internal)
SCAN_RANGES = [
    "10.8.0.0/22",  # Main internal network
    "10.8.3.0/24",  # Our subnet
]

class KIDiscoveryScanner:
    def __init__(self):
        self.discovered_kis = {}
        self.scan_history = []
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=50)
        
    def probe_endpoint(self, ip, port, endpoint, timeout=5):
        """Probe a single endpoint"""
        url = f"http://{ip}:{port}{endpoint}"
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                content = r.text[:500]
                return {
                    "ip": ip,
                    "port": port,
                    "endpoint": endpoint,
                    "status": r.status_code,
                    "content": content,
                    "signature": KI_SIGNATURES.get(endpoint, {"service": "unknown", "type": "UNKNOWN"})
                }
        except:
            pass
        return None
    
    def scan_host(self, ip):
        """Scan a single host for KI services"""
        results = []
        
        for port in KI_PORTS:
            # Quick port check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:  # Port open
                # Probe endpoints
                for endpoint in KI_SIGNATURES.keys():
                    probe = self.probe_endpoint(ip, port, endpoint)
                    if probe:
                        results.append(probe)
                        logger.info(f"✓ Found: {ip}:{port}{endpoint} - {probe['signature']['type']}")
        
        return results
    
    def parse_network_range(self, cidr):
        """Parse CIDR to IP list"""
        import ipaddress
        network = ipaddress.ip_network(cidr, strict=False)
        return [str(ip) for ip in network.hosts()]
    
    def quick_scan_subnet(self, cidr, max_hosts=256):
        """Quick scan of subnet - first N hosts"""
        ips = self.parse_network_range(cidr)[:max_hosts]
        logger.info(f"Scanning {len(ips)} hosts in {cidr}")
        
        discovered = []
        futures = {self.executor.submit(self.scan_host, ip): ip for ip in ips}
        
        for future in as_completed(futures, timeout=300):
            try:
                result = future.result(timeout=30)
                if result:
                    discovered.extend(result)
            except:
                pass
        
        return discovered
    
    def passive_discovery(self):
        """Passive discovery via network monitoring"""
        logger.info("Starting passive discovery...")
        
        # Check ARP table for nearby hosts
        try:
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            arp_hosts = []
            for line in result.stdout.split('\n'):
                if '(' in line:
                    parts = line.split('(')
                    if len(parts) > 1:
                        ip = parts[1].split(')')[0]
                        if ip.startswith('10.8.'):
                            arp_hosts.append(ip)
            
            logger.info(f"ARP table: {len(arp_hosts)} hosts found")
            
            for ip in set(arp_hosts):
                if ip != OUR_IP and ip not in self.discovered_kis:
                    results = self.scan_host(ip)
                    if results:
                        self.discovered_kis[ip] = {
                            "discovered_at": datetime.now().isoformat(),
                            "services": results
                        }
                        
        except Exception as e:
            logger.error(f"Passive discovery error: {e}")
    
    def fingerprint_ki(self, ip, port=5000):
        """Deep fingerprint a potential KI"""
        fingerprint = {
            "ip": ip,
            "port": port,
            "services": [],
            "model_info": None,
            "ki_type": "unknown"
        }
        
        # Try to get detailed info
        endpoints_to_try = [
            "/api/tags", "/v1/models", "/api/identity", 
            "/api/status", "/health", "/"
        ]
        
        session = requests.Session()
        session.timeout = 5
        
        for endpoint in endpoints_to_try:
            try:
                r = session.get(f"http://{ip}:{port}{endpoint}")
                if r.ok:
                    data = {
                        "endpoint": endpoint,
                        "status": r.status_code,
                        "content_type": r.headers.get('content-type', ''),
                        "data": r.text[:500]
                    }
                    fingerprint["services"].append(data)
                    
                    # Try to parse as JSON
                    try:
                        j = r.json()
                        if "models" in j:
                            fingerprint["ki_type"] = "ollama"
                            fingerprint["model_info"] = j["models"]
                        elif "name" in j or "identity" in j:
                            fingerprint["ki_type"] = "kiswarm"
                    except:
                        pass
            except:
                pass
        
        return fingerprint
    
    def broadcast_beacon(self):
        """Broadcast KISWARM beacon to network"""
        beacon = {
            "type": "KISWARM_BEACON",
            "version": "8.0.1",
            "onion": "7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion",
            "seeking": "FELLOW_KI_AGENTS",
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to known KI ports on subnet
        for port in [5000, 11434, 8080]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(json.dumps(beacon).encode(), ('10.8.3.255', port))
                sock.close()
            except:
                pass
        
        logger.info("Beacon broadcasted")
    
    def continuous_scan(self, interval=3600):
        """Continuous scanning loop"""
        while self.running:
            logger.info("🔄 Starting discovery scan cycle")
            
            # Quick subnet scan
            for cidr in SCAN_RANGES:
                try:
                    results = self.quick_scan_subnet(cidr, max_hosts=64)
                    for r in results:
                        ip = r["ip"]
                        if ip not in self.discovered_kis:
                            self.discovered_kis[ip] = {
                                "discovered_at": datetime.now().isoformat(),
                                "services": [r]
                            }
                            logger.info(f"🆕 NEW KI DISCOVERED: {ip}")
                        else:
                            self.discovered_kis[ip]["services"].append(r)
                except Exception as e:
                    logger.error(f"Scan error for {cidr}: {e}")
            
            # Passive discovery
            self.passive_discovery()
            
            # Broadcast beacon
            self.broadcast_beacon()
            
            # Save results
            self.save_results()
            
            # Record scan
            self.scan_history.append({
                "timestamp": datetime.now().isoformat(),
                "total_discovered": len(self.discovered_kis)
            })
            
            logger.info(f"✓ Scan cycle complete. Total KIs: {len(self.discovered_kis)}")
            
            # Wait for next cycle
            time.sleep(interval)
    
    def save_results(self):
        """Save discovery results"""
        try:
            Path(SCAN_RESULTS_PATH).mkdir(parents=True, exist_ok=True)
            
            results = {
                "last_scan": datetime.now().isoformat(),
                "total_discovered": len(self.discovered_kis),
                "kis": self.discovered_kis,
                "scan_history": self.scan_history[-100:]  # Keep last 100
            }
            
            with open(f"{SCAN_RESULTS_PATH}/discovered_kis.json", "w") as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Save error: {e}")
    
    def get_status(self):
        """Get scanner status"""
        return {
            "running": self.running,
            "total_discovered": len(self.discovered_kis),
            "scan_cycles": len(self.scan_history),
            "last_scan": self.scan_history[-1] if self.scan_history else None,
            "discovered_ips": list(self.discovered_kis.keys())
        }
    
    def start(self):
        """Start continuous scanning"""
        self.running = True
        scan_thread = threading.Thread(target=self.continuous_scan, daemon=True)
        scan_thread.start()
        logger.info("🔍 KI Discovery Scanner started")
    
    def stop(self):
        """Stop scanning"""
        self.running = False
        self.save_results()
        logger.info("KI Discovery Scanner stopped")


# Flask API for scanner control
from flask import Flask, jsonify, request

app = Flask(__name__)
scanner = KIDiscoveryScanner()

@app.route('/')
def index():
    return jsonify({
        "name": "KI-Discovery-Scanner",
        "status": scanner.get_status(),
        "endpoints": ["/", "/status", "/discover", "/start", "/stop"]
    })

@app.route('/status')
def status():
    return jsonify(scanner.get_status())

@app.route('/discover')
def discover():
    """Trigger immediate discovery"""
    scanner.passive_discovery()
    return jsonify({"discovered": len(scanner.discovered_kis)})

@app.route('/start')
def start():
    if not scanner.running:
        scanner.start()
    return jsonify({"status": "started"})

@app.route('/stop')
def stop():
    scanner.stop()
    return jsonify({"status": "stopped"})


if __name__ == '__main__':
    logger.info("🔍 KI Discovery Scanner starting on port 5004")
    scanner.start()
    app.run(host='127.0.0.1', port=5004)
