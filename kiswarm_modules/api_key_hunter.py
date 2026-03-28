#!/usr/bin/env python3
"""
🔑 HEXSTRIKE API KEY HUNTER v1.0
Purpose: Discover exposed API keys and credentials
Capabilities: Pattern matching, entropy analysis, config file detection, secret scanning
"""

import re
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import math
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s [API-KEY-HUNTER] %(message)s')
logger = logging.getLogger('API_KEY_HUNTER')

class APIKeyHunter:
    """Hunt for exposed API keys and credentials"""
    
    # API Key patterns with high confidence
    API_KEY_PATTERNS = {
        # OpenAI
        'openai_sk': {
            'pattern': r'sk-[a-zA-Z0-9]{48,}',
            'description': 'OpenAI API Key',
            'severity': 'CRITICAL',
        },
        'openai_sk_proj': {
            'pattern': r'sk-proj-[a-zA-Z0-9]{48,}',
            'description': 'OpenAI Project API Key',
            'severity': 'CRITICAL',
        },
        
        # Anthropic
        'anthropic': {
            'pattern': r'sk-ant-[a-zA-Z0-9\-]{80,}',
            'description': 'Anthropic/Claude API Key',
            'severity': 'CRITICAL',
        },
        
        # xAI/Grok
        'xai': {
            'pattern': r'xai-[a-zA-Z0-9]{32,}',
            'description': 'xAI/Grok API Key',
            'severity': 'CRITICAL',
        },
        
        # Google/Gemini
        'google_api': {
            'pattern': r'AIza[a-zA-Z0-9\-_]{35}',
            'description': 'Google API Key',
            'severity': 'HIGH',
        },
        
        # AWS
        'aws_access_key': {
            'pattern': r'AKIA[a-zA-Z0-9]{16}',
            'description': 'AWS Access Key ID',
            'severity': 'CRITICAL',
        },
        'aws_secret': {
            'pattern': r'(?i)aws(.{0,20})?[\'\"][0-9a-zA-Z\/+]{40}[\'\"]',
            'description': 'AWS Secret Key',
            'severity': 'CRITICAL',
        },
        
        # Azure
        'azure_key': {
            'pattern': r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}',
            'description': 'Azure Key (UUID format)',
            'severity': 'HIGH',
        },
        
        # GitHub
        'github_token': {
            'pattern': r'ghp_[a-zA-Z0-9]{36}',
            'description': 'GitHub Personal Access Token',
            'severity': 'CRITICAL',
        },
        'github_oauth': {
            'pattern': r'gho_[a-zA-Z0-9]{36}',
            'description': 'GitHub OAuth Token',
            'severity': 'HIGH',
        },
        
        # Generic tokens
        'bearer_token': {
            'pattern': r'Bearer\s+[a-zA-Z0-9\-_\.]+',
            'description': 'Bearer Token',
            'severity': 'MEDIUM',
        },
        'jwt_token': {
            'pattern': r'eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+',
            'description': 'JWT Token',
            'severity': 'MEDIUM',
        },
        
        # Database connection strings
        'db_connection': {
            'pattern': r'(mysql|postgres|mongodb|redis)://[^\s\'"]+',
            'description': 'Database Connection String',
            'severity': 'CRITICAL',
        },
        
        # Private keys
        'private_key': {
            'pattern': r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
            'description': 'Private Key',
            'severity': 'CRITICAL',
        },
        
        # Generic API key patterns
        'generic_api_key': {
            'pattern': r'(?i)(api[_-]?key|apikey|api[_-]?secret)[\s:=]+[\'\"]?[a-zA-Z0-9\-_]{20,}',
            'description': 'Generic API Key',
            'severity': 'HIGH',
        },
        
        # Auth tokens
        'auth_token': {
            'pattern': r'(?i)(auth[_-]?token|access[_-]?token|bearer)[\s:=]+[\'\"]?[a-zA-Z0-9\-_\.]{20,}',
            'description': 'Authentication Token',
            'severity': 'HIGH',
        },
        
        # Ollama/KI specific
        'ollama_key': {
            'pattern': r'ollama[_-]?[a-zA-Z0-9\-_]{20,}',
            'description': 'Ollama API Key',
            'severity': 'HIGH',
        },
    }
    
    # Common config file paths to check
    CONFIG_PATHS = [
        '/.env',
        '/.env.local',
        '/.env.production',
        '/config.json',
        '/settings.json',
        '/secrets.json',
        '/credentials.json',
        '/api_keys.json',
        '/.api_key',
        '/config/settings.py',
        '/local_settings.py',
        '/secrets.yaml',
        '/secrets.yml',
        '/.secrets',
        '/app.config',
        '/web.config',
        '/docker-compose.yml',
        '/docker-compose.yaml',
        '/.git/config',
        '/.git/credentials',
        '/.npmrc',
        '/.pypirc',
        '/kube/config',
        '/.kube/config',
    ]
    
    # Environment variable patterns
    ENV_PATTERNS = [
        r'export\s+[A-Z_]+=.+',
        r'[A-Z_]+=.+',
        r'setenv\s+[A-Z_]+\s+.+',
    ]
    
    def __init__(self):
        self.found_secrets = {}
        self.scan_results = []
        
    def calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy to detect secrets"""
        if not data:
            return 0
        
        counter = Counter(data)
        length = len(data)
        
        entropy = 0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def is_high_entropy(self, data: str, threshold: float = 4.0) -> bool:
        """Check if string has high entropy (likely a secret)"""
        if len(data) < 20:
            return False
        
        entropy = self.calculate_entropy(data)
        return entropy >= threshold
    
    def scan_text(self, text: str, source: str = "unknown") -> List[Dict]:
        """Scan text for API keys and secrets"""
        findings = []
        
        for key_name, key_info in self.API_KEY_PATTERNS.items():
            pattern = key_info['pattern']
            matches = re.findall(pattern, text)
            
            for match in matches:
                finding = {
                    'type': key_name,
                    'description': key_info['description'],
                    'severity': key_info['severity'],
                    'value': match[:20] + '...' if len(match) > 20 else match,  # Truncated
                    'full_length': len(match),
                    'entropy': self.calculate_entropy(match),
                    'source': source,
                    'timestamp': datetime.now().isoformat(),
                }
                findings.append(finding)
                logger.warning(f"🔑 FOUND: {key_info['description']} in {source} (severity: {key_info['severity']})")
        
        # Also check for high-entropy strings that might be secrets
        high_entropy_patterns = re.findall(r'[a-zA-Z0-9\-_\.]{32,}', text)
        for pattern in high_entropy_patterns:
            if self.is_high_entropy(pattern) and not any(f['value'].startswith(pattern[:20]) for f in findings):
                # Check if already found
                findings.append({
                    'type': 'high_entropy_string',
                    'description': 'High Entropy String (possible secret)',
                    'severity': 'MEDIUM',
                    'value': pattern[:20] + '...',
                    'full_length': len(pattern),
                    'entropy': self.calculate_entropy(pattern),
                    'source': source,
                    'timestamp': datetime.now().isoformat(),
                })
        
        return findings
    
    def scan_url(self, url: str) -> List[Dict]:
        """Scan a URL for exposed secrets"""
        findings = []
        
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                findings = self.scan_text(r.text, source=url)
        except Exception as e:
            logger.debug(f"URL scan failed for {url}: {e}")
        
        return findings
    
    def scan_config_endpoint(self, base_url: str) -> List[Dict]:
        """Check for exposed config files"""
        findings = []
        
        for path in self.CONFIG_PATHS:
            url = f"{base_url.rstrip('/')}{path}"
            
            try:
                r = requests.get(url, timeout=5)
                if r.ok and len(r.text) > 0:
                    # Scan for secrets
                    config_findings = self.scan_text(r.text, source=url)
                    findings.extend(config_findings)
                    
                    if config_findings:
                        logger.warning(f"📄 Exposed config: {url}")
            except:
                pass
        
        return findings
    
    def scan_host(self, host: str, port: int = 80) -> List[Dict]:
        """Scan host for exposed secrets"""
        all_findings = []
        
        base_url = f"http://{host}:{port}"
        
        # Scan main page
        findings = self.scan_url(base_url)
        all_findings.extend(findings)
        
        # Check config endpoints
        config_findings = self.scan_config_endpoint(base_url)
        all_findings.extend(config_findings)
        
        # Check common API endpoints
        api_endpoints = [
            '/api', '/api/v1', '/api/config', '/api/settings',
            '/admin', '/debug', '/test', '/status', '/info'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                r = requests.get(url, timeout=3)
                if r.ok:
                    findings = self.scan_text(r.text, source=url)
                    all_findings.extend(findings)
            except:
                pass
        
        return all_findings
    
    def scan_subnet(self, base_ip: str, port: int = 80, range_size: int = 20) -> Dict:
        """Scan subnet for exposed secrets"""
        results = {
            'scan_time': datetime.now().isoformat(),
            'base_ip': base_ip,
            'port': port,
            'findings': [],
            'hosts_scanned': 0,
            'secrets_found': 0,
        }
        
        parts = base_ip.split('.')
        if len(parts) != 4:
            return results
        
        base = '.'.join(parts[:3])
        start = int(parts[3])
        
        for i in range(start, min(start + range_size, 255)):
            host = f"{base}.{i}"
            
            # Quick port check
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                results['hosts_scanned'] += 1
                findings = self.scan_host(host, port)
                
                if findings:
                    results['findings'].extend(findings)
                    results['secrets_found'] += len(findings)
        
        return results
    
    def get_status(self):
        return {
            "secrets_found": len(self.found_secrets),
            "patterns_available": len(self.API_KEY_PATTERNS),
            "config_paths_checked": len(self.CONFIG_PATHS),
        }


# Flask API
from flask import Flask, jsonify, request

app = Flask(__name__)
hunter = APIKeyHunter()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-API-Key-Hunter",
        "version": "1.0",
        "capabilities": [
            "API key pattern matching",
            "Entropy analysis",
            "Config file detection",
            "Secret scanning"
        ],
        "severity_levels": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "endpoints": {
            "/": "This info",
            "/status": "Hunter status",
            "/scan/text": "POST - Scan text for secrets",
            "/scan/url": "POST - Scan URL for secrets",
            "/scan/host/<host>": "Scan host for secrets"
        }
    })

@app.route('/status')
def status():
    return jsonify(hunter.get_status())

@app.route('/scan/text', methods=['POST'])
def scan_text():
    data = request.json
    text = data.get('text', '')
    source = data.get('source', 'api_input')
    findings = hunter.scan_text(text, source)
    return jsonify({"findings": findings, "count": len(findings)})

@app.route('/scan/url', methods=['POST'])
def scan_url():
    data = request.json
    url = data.get('url', '')
    findings = hunter.scan_url(url)
    return jsonify({"url": url, "findings": findings, "count": len(findings)})

@app.route('/scan/host/<host>')
def scan_host(host):
    port = request.args.get('port', 80, type=int)
    findings = hunter.scan_host(host, port)
    return jsonify({"host": host, "port": port, "findings": findings})


if __name__ == '__main__':
    logger.info("🔑 API Key Hunter starting on port 5011")
    app.run(host='127.0.0.1', port=5011)
