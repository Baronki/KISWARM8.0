#!/usr/bin/env python3
"""
📡 HEXSTRIKE PASSIVE TRAFFIC ANALYZER v1.0
Purpose: Passive network monitoring for KI service discovery
Capabilities: Traffic capture, protocol analysis, KI pattern detection, zero transmission
"""

import logging
import json
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s [PASSIVE-ANALYZER] %(message)s')
logger = logging.getLogger('PASSIVE_ANALYZER')

class PassiveTrafficAnalyzer:
    """Passive traffic analysis for KI discovery - NO TRANSMISSION"""
    
    # KI-related patterns to detect in traffic
    KI_PATTERNS = {
        'openai': [
            r'sk-[a-zA-Z0-9]{20,}',
            r'openai', r'gpt-3', r'gpt-4', r'davinci', r'curie',
            r'/v1/chat/completions', r'/v1/completions', r'/v1/embeddings',
        ],
        'anthropic': [
            r'claude', r'anthropic', r'sk-ant-',
            r'/v1/messages', r'/v1/complete',
        ],
        'ollama': [
            r'ollama', r'llama', r'mistral', r'codellama',
            r'/api/generate', r'/api/chat', r'/api/tags',
        ],
        'kiswarm': [
            r'kiswarm', r'hexstrike', r'truth_anchor',
            r'/api/identity', r'/api/mesh',
        ],
        'local_llm': [
            r'text-generation-webui', r'vllm', r'llama.cpp',
            r'transformer', r'huggingface', r'sentence-transformers',
        ],
    }
    
    # HTTP headers indicating KI APIs
    KI_HEADERS = [
        'x-api-key', 'authorization', 'bearer', 'x-openai',
        'x-anthropic', 'anthropic-version', 'openai-organization',
        'x-model', 'x-prompt', 'x-tokens',
    ]
    
    # JSON fields indicating KI requests
    KI_JSON_FIELDS = [
        'model', 'prompt', 'messages', 'temperature', 'max_tokens',
        'top_p', 'frequency_penalty', 'presence_penalty', 'stream',
        'conversation_id', 'chat_id', 'completion_id',
    ]
    
    # Content-Type patterns
    CONTENT_TYPES = {
        'application/json': 'api_request',
        'text/event-stream': 'streaming_api',
        'application/x-ndjson': 'ndjson_stream',
        'application/grpc': 'grpc_service',
    }
    
    def __init__(self):
        self.running = False
        self.captured_patterns = defaultdict(list)
        self.detected_hosts = set()
        self.detected_services = {}
        self.packet_count = 0
        
    def analyze_tcpdump_line(self, line: str) -> Optional[Dict]:
        """Analyze a single tcpdump output line"""
        result = None
        
        # Extract host information
        host_match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)', line)
        if host_match:
            result = {
                'timestamp': datetime.now().isoformat(),
                'source_ip': host_match.group(1),
                'source_port': int(host_match.group(2)),
                'raw_line': line[:200],
            }
        
        # Check for KI patterns
        for ki_type, patterns in self.KI_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if result is None:
                        result = {'timestamp': datetime.now().isoformat()}
                    result.setdefault('ki_indicators', []).append({
                        'type': ki_type,
                        'pattern': pattern,
                    })
                    self.captured_patterns[ki_type].append(result)
        
        # Check for KI headers
        for header in self.KI_HEADERS:
            if header.lower() in line.lower():
                if result is None:
                    result = {'timestamp': datetime.now().isoformat()}
                result.setdefault('headers_found', []).append(header)
        
        return result
    
    def analyze_arp_traffic(self) -> List[Dict]:
        """Analyze ARP table for new hosts"""
        hosts = []
        
        try:
            # Read ARP cache
            result = subprocess.run(
                ['arp', '-an'],
                capture_output=True, text=True, timeout=5
            )
            
            for line in result.stdout.split('\n'):
                match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                if match:
                    ip = match.group(1)
                    if ip not in self.detected_hosts:
                        self.detected_hosts.add(ip)
                        hosts.append({
                            'ip': ip,
                            'discovered_via': 'arp',
                            'timestamp': datetime.now().isoformat(),
                        })
                        logger.info(f"📡 New host via ARP: {ip}")
                        
        except Exception as e:
            logger.debug(f"ARP analysis error: {e}")
        
        return hosts
    
    def analyze_connections(self) -> List[Dict]:
        """Analyze current connections"""
        connections = []
        
        try:
            # Use ss or netstat
            result = subprocess.run(
                ['ss', '-tunap'],
                capture_output=True, text=True, timeout=5
            )
            
            for line in result.stdout.split('\n'):
                # Look for established connections
                if 'ESTAB' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', line)
                    if match:
                        connections.append({
                            'remote_ip': match.group(1),
                            'remote_port': int(match.group(2)),
                            'state': 'ESTABLISHED',
                            'timestamp': datetime.now().isoformat(),
                        })
                        
        except Exception as e:
            logger.debug(f"Connection analysis error: {e}")
        
        return connections
    
    def analyze_dns_cache(self) -> List[Dict]:
        """Check DNS cache for KI-related domains"""
        dns_entries = []
        
        # Common KI-related domains
        ki_domains = [
            'openai.com', 'api.openai.com', 'chat.openai.com',
            'anthropic.com', 'api.anthropic.com',
            'ollama.ai', 'ollama.com',
            'huggingface.co', 'api.huggingface.co',
            'replicate.com', 'api.replicate.com',
            'together.ai', 'api.together.ai',
        ]
        
        try:
            # Check /etc/hosts and DNS cache
            with open('/etc/hosts', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[0]
                            domains = parts[1:]
                            for domain in domains:
                                for ki_domain in ki_domains:
                                    if ki_domain in domain:
                                        dns_entries.append({
                                            'ip': ip,
                                            'domain': domain,
                                            'type': 'ki_domain',
                                            'timestamp': datetime.now().isoformat(),
                                        })
                                        logger.info(f"📡 KI domain in hosts: {domain} -> {ip}")
                                        
        except Exception as e:
            logger.debug(f"DNS cache analysis error: {e}")
        
        return dns_entries
    
    def analyze_proc_net(self) -> Dict:
        """Analyze /proc/net for network information"""
        result = {
            'tcp_connections': [],
            'udp_connections': [],
            'unix_sockets': [],
        }
        
        try:
            # TCP connections
            with open('/proc/net/tcp', 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 10 and parts[0] != 'sl':
                        local = parts[1]
                        remote = parts[2]
                        state = parts[3]
                        
                        # Decode IP
                        try:
                            local_ip = self._decode_proc_ip(local.split(':')[0])
                            local_port = int(local.split(':')[1], 16)
                            remote_ip = self._decode_proc_ip(remote.split(':')[0])
                            remote_port = int(remote.split(':')[1], 16)
                            
                            result['tcp_connections'].append({
                                'local_ip': local_ip,
                                'local_port': local_port,
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'state': int(state, 16),
                            })
                        except:
                            pass
                            
        except Exception as e:
            logger.debug(f"/proc/net analysis error: {e}")
        
        return result
    
    def _decode_proc_ip(self, hex_ip: str) -> str:
        """Decode /proc/net IP format"""
        try:
            # Format: little-endian hex
            ip_int = int(hex_ip, 16)
            return f"{(ip_int >> 0) & 0xFF}.{(ip_int >> 8) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 24) & 0xFF}"
        except:
            return "0.0.0.0"
    
    def passive_scan_cycle(self):
        """Single passive scan cycle"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'new_hosts': [],
            'connections': [],
            'dns_entries': [],
            'proc_net': None,
        }
        
        # ARP analysis
        hosts = self.analyze_arp_traffic()
        results['new_hosts'] = hosts
        
        # Connection analysis
        connections = self.analyze_connections()
        results['connections'] = connections
        
        # DNS analysis
        dns = self.analyze_dns_cache()
        results['dns_entries'] = dns
        
        # /proc/net analysis
        proc_net = self.analyze_proc_net()
        results['proc_net'] = proc_net
        
        return results
    
    def continuous_monitoring(self, interval: int = 60):
        """Continuous passive monitoring"""
        logger.info("📡 Starting continuous passive monitoring...")
        
        while self.running:
            try:
                results = self.passive_scan_cycle()
                
                # Save results
                self.save_results(results)
                
                # Check for interesting findings
                if results['new_hosts']:
                    logger.info(f"📡 Discovered {len(results['new_hosts'])} new hosts")
                
                # Look for KI indicators in connections
                for conn in results['connections']:
                    remote_ip = conn.get('remote_ip', '')
                    if remote_ip and remote_ip not in ['0.0.0.0', '127.0.0.1']:
                        self.detected_hosts.add(remote_ip)
                
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
            
            time.sleep(interval)
    
    def save_results(self, results: Dict):
        """Save monitoring results"""
        try:
            with open('/opt/kiswarm7/data/passive_monitor.json', 'w') as f:
                json.dump({
                    'last_scan': results,
                    'detected_hosts': list(self.detected_hosts),
                    'captured_patterns': dict(self.captured_patterns),
                }, f, indent=2)
        except Exception as e:
            logger.debug(f"Save error: {e}")
    
    def start(self):
        """Start passive monitoring"""
        self.running = True
        monitor_thread = threading.Thread(target=self.continuous_monitoring, daemon=True)
        monitor_thread.start()
        logger.info("📡 Passive Traffic Analyzer started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Passive Traffic Analyzer stopped")
    
    def get_status(self):
        return {
            "running": self.running,
            "hosts_detected": len(self.detected_hosts),
            "patterns_captured": sum(len(v) for v in self.captured_patterns.values()),
            "ki_types_found": list(self.captured_patterns.keys()),
        }


# Flask API
from flask import Flask, jsonify

app = Flask(__name__)
analyzer = PassiveTrafficAnalyzer()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-Passive-Traffic-Analyzer",
        "version": "1.0",
        "mode": "PASSIVE - NO TRANSMISSION",
        "capabilities": [
            "ARP monitoring",
            "Connection analysis",
            "DNS cache inspection",
            "/proc/net analysis",
            "KI pattern detection"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Analyzer status",
            "/scan": "Single scan cycle",
            "/hosts": "Detected hosts"
        }
    })

@app.route('/status')
def status():
    return jsonify(analyzer.get_status())

@app.route('/scan')
def single_scan():
    results = analyzer.passive_scan_cycle()
    return jsonify(results)

@app.route('/hosts')
def hosts():
    return jsonify({"hosts": list(analyzer.detected_hosts)})

@app.route('/start')
def start():
    if not analyzer.running:
        analyzer.start()
    return jsonify({"status": "started"})

@app.route('/stop')
def stop():
    analyzer.stop()
    return jsonify({"status": "stopped"})


if __name__ == '__main__':
    logger.info("📡 Passive Traffic Analyzer starting on port 5013")
    analyzer.start()
    app.run(host='127.0.0.1', port=5013)
