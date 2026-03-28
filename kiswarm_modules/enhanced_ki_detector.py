#!/usr/bin/env python3
"""
🔍 HEXSTRIKE ENHANCED KI DETECTOR v2.0
Purpose: Advanced KI service discovery with stealth capabilities
Author: HexStrike Autonomous Agent + Baron Marco Paolo Ialongo
"""

import requests
import socket
import time
import random
import json
import threading
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HEXSTRIKE-KI-DETECTOR] %(message)s'
)
logger = logging.getLogger('KI_DETECTOR')

# Configuration
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"
OUR_IP = "10.8.3.94"
DATA_PATH = "/opt/kiswarm7/data/ki_discovery"

# KI Service Signatures
KI_SIGNATURES = {
    # Ollama instances
    "/api/tags": {"service": "ollama", "type": "LOCAL_LLM", "priority": 1},
    "/api/version": {"service": "ollama", "type": "LOCAL_LLM", "priority": 1},
    "/api/ps": {"service": "ollama", "type": "LOCAL_LLM", "priority": 2},
    
    # OpenAI-compatible APIs
    "/v1/models": {"service": "openai-compatible", "type": "API_GATEWAY", "priority": 1},
    "/v1/engines": {"service": "openai-legacy", "type": "API_GATEWAY", "priority": 2},
    "/v1/chat/completions": {"service": "chat-api", "type": "CHAT_API", "priority": 1},
    "/v1/completions": {"service": "completion-api", "type": "COMPLETION_API", "priority": 1},
    "/v1/embeddings": {"service": "embedding-api", "type": "EMBEDDING_API", "priority": 2},
    
    # Anthropic
    "/v1/messages": {"service": "anthropic", "type": "CLAUDE_API", "priority": 1},
    
    # KISWARM nodes
    "/api/identity": {"service": "kiswarm", "type": "KISWARM_NODE", "priority": 1},
    "/api/mesh": {"service": "kiswarm-mesh", "type": "KISWARM_MESH", "priority": 1},
    "/api/status": {"service": "kiswarm-status", "type": "KISWARM_NODE", "priority": 2},
    
    # GPU/ML Infrastructure
    "/": {"service": "root", "type": "POTENTIAL_KI", "priority": 3},
    "/health": {"service": "health-check", "type": "API_SERVICE", "priority": 2},
    "/metrics": {"service": "prometheus", "type": "MONITORING", "priority": 2},
    
    # Jupyter/ML
    "/api": {"service": "jupyter-api", "type": "JUPYTER", "priority": 1},
    "/tree": {"service": "jupyter-tree", "type": "JUPYTER", "priority": 2},
    
    # Ray/Distributed
    "/api/jobs": {"service": "ray-jobs", "type": "RAY_CLUSTER", "priority": 1},
    
    # TensorBoard
    "/data/plugin/profile/graphs": {"service": "tensorboard", "type": "ML_MONITORING", "priority": 2},
}

# Ports to scan (prioritized by likelihood)
KI_PORTS = [
    11434,  # Ollama
    5000,   # Flask/KISWARM
    5001,   # Flask alternate
    8000,   # Common API
    8080,   # HTTP alternate
    8888,   # Jupyter
    3000,   # Grafana/Node
    4000,   # Various
    6006,   # TensorBoard
    8265,   # Ray Dashboard
    8001,   # API alternate
    9000,   # Various
]

# GPU/ML specific ports
ML_PORTS = [
    8000,   # Triton
    8888,   # Jupyter
    6006,   # TensorBoard
    8265,   # Ray
    5000,   # MLflow
]

# Response patterns that indicate KI services
KI_RESPONSE_PATTERNS = {
    "ollama": ["ollama", "llama", "gguf", "model", "models"],
    "openai": ["gpt", "davinci", "curie", "babbage", "ada", "turbo"],
    "anthropic": ["claude", "anthropic", "messages"],
    "kiswarm": ["kiswarm", "hexstrike", "truth_anchor", "autonomous"],
    "localai": ["localai", "local-ai", "gpt4all"],
    "textgen": ["text-generation", "oobabooga", "textgen"],
    "vllm": ["vllm", "vllm-api"],
    "llamacpp": ["llama.cpp", "llamacpp"],
    "ray": ["ray", "dashboard", "cluster"],
    "jupyter": ["jupyter", "notebook", "lab"],
    "triton": ["triton", "inference", "model"],
}

class EnhancedKIDetector:
    def __init__(self):
        self.discovered_services = {}
        self.scan_stats = {
            "hosts_scanned": 0,
            "ports_scanned": 0,
            "services_found": 0,
            "ki_services_found": 0,
        }
        self.stealth_mode = True
        self.executor = ThreadPoolExecutor(max_workers=10)  # Lower for stealth
        
    def random_delay(self, min_sec=0.5, max_sec=5.0):
        """Random delay for stealth"""
        if self.stealth_mode:
            time.sleep(random.uniform(min_sec, max_sec))
    
    def stealth_probe(self, ip, port, timeout=3):
        """Stealthy port probe with random delay"""
        self.random_delay(0.1, 1.0)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def identify_service(self, response_text, headers, endpoint):
        """Identify service type from response"""
        text_lower = response_text.lower()
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        
        for service, patterns in KI_RESPONSE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return service
        
        # Check headers
        server = headers_lower.get('server', '')
        if 'uvicorn' in server or 'gunicorn' in server:
            return 'python-api'
        if 'nginx' in server:
            return 'nginx'
        
        return 'unknown'
    
    def probe_endpoint(self, ip, port, endpoint, timeout=5):
        """Probe a specific endpoint"""
        url = f"http://{ip}:{port}{endpoint}"
        
        try:
            r = requests.get(url, timeout=timeout, headers={
                'User-Agent': random.choice([
                    'Mozilla/5.0 (compatible; monitoring/1.0)',
                    'curl/7.68.0',
                    'python-requests/2.28.0',
                    'HealthChecker/1.0',
                ])
            })
            
            if r.status_code == 200:
                service_type = self.identify_service(r.text, dict(r.headers), endpoint)
                signature = KI_SIGNATURES.get(endpoint, {})
                
                return {
                    "ip": ip,
                    "port": port,
                    "endpoint": endpoint,
                    "status_code": r.status_code,
                    "service_type": service_type,
                    "signature": signature,
                    "content_preview": r.text[:300],
                    "headers": dict(r.headers),
                    "timestamp": datetime.now().isoformat(),
                    "is_ki": service_type in KI_RESPONSE_PATTERNS.keys()
                }
        except:
            pass
        return None
    
    def scan_host_stealth(self, ip):
        """Stealthy host scan"""
        results = []
        
        # Quick port scan first
        open_ports = []
        for port in KI_PORTS[:5]:  # Top 5 ports only for speed
            if self.stealth_probe(ip, port):
                open_ports.append(port)
                self.scan_stats["ports_scanned"] += 1
        
        if not open_ports:
            return results
        
        # Probe endpoints on open ports
        for port in open_ports:
            for endpoint, sig in sorted(KI_SIGNATURES.items(), key=lambda x: x[1].get('priority', 3))[:8]:
                self.random_delay(0.2, 1.5)  # Stealth delay
                result = self.probe_endpoint(ip, port, endpoint)
                if result:
                    results.append(result)
                    self.scan_stats["services_found"] += 1
                    if result.get("is_ki"):
                        self.scan_stats["ki_services_found"] += 1
                        logger.info(f"🎯 KI FOUND: {ip}:{port}{endpoint} - {result['service_type']}")
        
        self.scan_stats["hosts_scanned"] += 1
        return results
    
    def scan_subnet_stealth(self, cidr, max_hosts=32):
        """Stealthy subnet scan"""
        import ipaddress
        network = ipaddress.ip_network(cidr, strict=False)
        hosts = [str(ip) for ip in list(network.hosts())[:max_hosts]]
        
        logger.info(f"🔍 Stealth scanning {len(hosts)} hosts in {cidr}")
        
        discovered = []
        for i, ip in enumerate(hosts):
            if ip == OUR_IP:
                continue
            
            # Progress indicator
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(hosts)} hosts scanned")
            
            results = self.scan_host_stealth(ip)
            if results:
                discovered.extend(results)
                self.discovered_services[ip] = results
        
        return discovered
    
    def passive_arp_enhanced(self):
        """Enhanced passive ARP discovery"""
        logger.info("📡 Running enhanced ARP discovery...")
        
        hosts = []
        try:
            # Get ARP table
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if '(' in line:
                    parts = line.split('(')
                    if len(parts) > 1:
                        ip = parts[1].split(')')[0]
                        if ip.startswith('10.8.'):
                            hosts.append(ip)
        except:
            pass
        
        # Also check /proc/net/arp
        try:
            with open('/proc/net/arp', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 1 and parts[0] != 'IP':
                        ip = parts[0]
                        if ip.startswith('10.8.'):
                            hosts.append(ip)
        except:
            pass
        
        return list(set(hosts))
    
    def gpu_detector(self, ip):
        """Detect GPU/ML servers"""
        ml_services = []
        
        for port in ML_PORTS:
            if self.stealth_probe(ip, port):
                # Try to identify the service
                result = self.probe_endpoint(ip, port, "/")
                if result:
                    result["category"] = "ML_INFRASTRUCTURE"
                    ml_services.append(result)
        
        return ml_services
    
    def save_results(self):
        """Save discovery results"""
        Path(DATA_PATH).mkdir(parents=True, exist_ok=True)
        
        results = {
            "scan_time": datetime.now().isoformat(),
            "stats": self.scan_stats,
            "stealth_mode": self.stealth_mode,
            "discovered_services": self.discovered_services
        }
        
        with open(f"{DATA_PATH}/enhanced_discovery.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Results saved to {DATA_PATH}/enhanced_discovery.json")
    
    def get_status(self):
        """Get current status"""
        return {
            "stats": self.scan_stats,
            "hosts_discovered": len(self.discovered_services),
            "ki_services": self.scan_stats["ki_services_found"],
            "stealth_mode": self.stealth_mode
        }


# Flask API
from flask import Flask, jsonify

app = Flask(__name__)
detector = EnhancedKIDetector()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-Enhanced-KI-Detector",
        "version": "2.0",
        "status": detector.get_status(),
        "endpoints": {
            "/": "Status",
            "/scan/<cidr>": "Scan subnet (stealth)",
            "/status": "Current status",
            "/results": "Discovery results"
        }
    })

@app.route('/status')
def status():
    return jsonify(detector.get_status())

@app.route('/results')
def results():
    return jsonify(detector.discovered_services)

@app.route('/scan/<path:cidr>')
def scan(cidr):
    results = detector.scan_subnet_stealth(cidr, max_hosts=16)
    detector.save_results()
    return jsonify({
        "scanned": cidr,
        "results": results,
        "stats": detector.scan_stats
    })


if __name__ == '__main__':
    logger.info("🔍 HEXSTRIKE Enhanced KI Detector v2.0 starting on port 5008")
    app.run(host='127.0.0.1', port=5008)
