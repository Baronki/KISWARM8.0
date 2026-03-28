#!/usr/bin/env python3
"""
🔐 HEXSTRIKE TLS ANALYZER v1.0
Purpose: Certificate analysis and HTTPS service detection
Capabilities: TLS fingerprinting, certificate analysis, SNI extraction, self-signed cert detection
"""

import socket
import ssl
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [TLS-ANALYZER] %(message)s')
logger = logging.getLogger('TLS_ANALYZER')

class TLSAnalyzer:
    """Advanced TLS/SSL analysis for KI service discovery"""
    
    # Ports commonly used for HTTPS APIs
    HTTPS_PORTS = [443, 8443, 9443, 5001, 8000, 8080, 8888, 9000]
    
    # KI-related certificate patterns
    KI_CERT_PATTERNS = [
        'ollama', 'openai', 'anthropic', 'claude', 'kiswarm', 'hexstrike',
        'llama', 'gpt', 'ai', 'ml', 'model', 'inference', 'api'
    ]
    
    # Self-signed certificate indicators (common for internal KIs)
    SELF_SIGNED_INDICATORS = [
        'localhost', 'internal', 'self-signed', 'untrusted'
    ]
    
    def __init__(self):
        self.discovered_tls_services = {}
        
    def get_certificate(self, host: str, port: int, timeout: int = 5) -> Optional[Dict]:
        """Extract TLS certificate information"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Accept self-signed
            
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_dict = ssock.getpeercert()
                    
                    # Get TLS version and cipher
                    tls_version = ssock.version()
                    cipher = ssock.cipher()
                    
                    # Decode certificate
                    from cryptography import x509
                    from cryptography.hazmat.backends import default_backend
                    
                    cert_obj = x509.load_der_x509_certificate(cert, default_backend())
                    
                    return {
                        'host': host,
                        'port': port,
                        'tls_version': tls_version,
                        'cipher': cipher[0] if cipher else None,
                        'cipher_strength': cipher[1] if cipher else None,
                        'subject': cert_dict.get('subject', []),
                        'issuer': cert_dict.get('issuer', []),
                        'version': cert_obj.version.name if hasattr(cert_obj.version, 'name') else str(cert_obj.version),
                        'serial_number': str(cert_obj.serial_number),
                        'not_before': cert_obj.not_valid_before.isoformat() if hasattr(cert_obj, 'not_valid_before') else None,
                        'not_after': cert_obj.not_valid_after.isoformat() if hasattr(cert_obj, 'not_valid_after') else None,
                        'is_self_signed': self._check_self_signed(cert_dict),
                        'sans': self._get_sans(cert_obj),
                        'public_key_type': cert_obj.public_key().__class__.__name__,
                        'signature_algorithm': cert_obj.signature_algorithm_oid._name,
                    }
        except Exception as e:
            logger.debug(f"Certificate extraction failed for {host}:{port} - {e}")
            return None
    
    def _check_self_signed(self, cert_dict: Dict) -> bool:
        """Check if certificate is self-signed"""
        if not cert_dict:
            return True
        
        subject = cert_dict.get('subject', ())
        issuer = cert_dict.get('issuer', ())
        
        # Self-signed if subject == issuer
        if subject == issuer:
            return True
            
        return False
    
    def _get_sans(self, cert_obj) -> List[str]:
        """Extract Subject Alternative Names"""
        try:
            from cryptography.x509 import ExtensionOID
            san_ext = cert_obj.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            return [str(name.value) for name in san_ext.value]
        except:
            return []
    
    def analyze_for_ki(self, cert_info: Dict) -> Dict:
        """Analyze certificate for KI service indicators"""
        analysis = {
            'is_potential_ki': False,
            'confidence': 0,
            'indicators': [],
            'internal_service': False,
        }
        
        # Check subject/issuer for KI patterns
        for field in ['subject', 'issuer']:
            for item in cert_info.get(field, []):
                for _, value in item if isinstance(item, tuple) else [('', item)]:
                    value_str = str(value).lower()
                    for pattern in self.KI_CERT_PATTERNS:
                        if pattern in value_str:
                            analysis['is_potential_ki'] = True
                            analysis['confidence'] += 20
                            analysis['indicators'].append(f'{field}_contains_{pattern}')
        
        # Check SANs for KI patterns
        for san in cert_info.get('sans', []):
            san_lower = san.lower()
            for pattern in self.KI_CERT_PATTERNS:
                if pattern in san_lower:
                    analysis['is_potential_ki'] = True
                    analysis['confidence'] += 15
                    analysis['indicators'].append(f'san_contains_{pattern}')
            
            # Check for internal indicators
            if any(ind in san_lower for ind in ['internal', 'local', 'private', '10.', '192.168.', '172.']):
                analysis['internal_service'] = True
                analysis['confidence'] += 10
        
        # Self-signed often indicates internal/development KI
        if cert_info.get('is_self_signed'):
            analysis['indicators'].append('self_signed')
            analysis['internal_service'] = True
            analysis['confidence'] += 15
        
        # Cap confidence at 100
        analysis['confidence'] = min(100, analysis['confidence'])
        
        return analysis
    
    def tls_fingerprint(self, host: str, port: int) -> Optional[Dict]:
        """Generate JA3-style TLS fingerprint"""
        try:
            # Use openssl for fingerprinting
            result = subprocess.run(
                ['openssl', 's_client', '-connect', f'{host}:{port}', '-servername', host],
                capture_output=True, text=True, timeout=10,
                input=''
            )
            
            output = result.stdout + result.stderr
            
            # Extract cipher suite
            cipher_match = None
            for line in output.split('\n'):
                if 'Cipher' in line and ':' in line:
                    cipher_match = line.split(':')[1].strip()
                    break
            
            return {
                'host': host,
                'port': port,
                'cipher_suite': cipher_match,
                'fingerprint_method': 'openssl'
            }
        except Exception as e:
            logger.debug(f"TLS fingerprint failed: {e}")
            return None
    
    def scan_host(self, host: str, ports: List[int] = None) -> List[Dict]:
        """Scan host for TLS services"""
        ports = ports or self.HTTPS_PORTS
        results = []
        
        for port in ports:
            cert_info = self.get_certificate(host, port)
            if cert_info:
                analysis = self.analyze_for_ki(cert_info)
                
                result = {
                    **cert_info,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(result)
                
                if analysis['is_potential_ki']:
                    logger.info(f"🎯 Potential KI TLS service: {host}:{port} (confidence: {analysis['confidence']}%)")
                    logger.info(f"   Indicators: {analysis['indicators']}")
        
        return results
    
    def quick_scan_subnet(self, base_ip: str, port: int = 443, range_size: int = 20) -> List[Dict]:
        """Quick scan of subnet for TLS services"""
        results = []
        
        # Parse base IP
        parts = base_ip.split('.')
        if len(parts) != 4:
            return results
        
        base = '.'.join(parts[:3])
        start = int(parts[3])
        
        for i in range(start, min(start + range_size, 255)):
            host = f"{base}.{i}"
            
            # Quick port check first
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    cert_info = self.get_certificate(host, port)
                    if cert_info:
                        analysis = self.analyze_for_ki(cert_info)
                        results.append({**cert_info, 'analysis': analysis})
            except:
                pass
        
        return results


# Flask API
from flask import Flask, jsonify, request

app = Flask(__name__)
analyzer = TLSAnalyzer()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-TLS-Analyzer",
        "version": "1.0",
        "capabilities": [
            "Certificate extraction",
            "Self-signed detection",
            "KI pattern analysis",
            "TLS fingerprinting",
            "SAN extraction"
        ],
        "endpoints": {
            "/": "This info",
            "/analyze/<host>/<int:port>": "Analyze TLS service",
            "/scan/<host>": "Scan host for TLS services"
        }
    })

@app.route('/analyze/<host>/<int:port>')
def analyze(host, port):
    cert_info = analyzer.get_certificate(host, port)
    if cert_info:
        analysis = analyzer.analyze_for_ki(cert_info)
        return jsonify({**cert_info, 'analysis': analysis})
    return jsonify({"error": "Could not retrieve certificate"}), 404

@app.route('/scan/<host>')
def scan_host(host):
    results = analyzer.scan_host(host)
    return jsonify({"host": host, "tls_services": results})


if __name__ == '__main__':
    logger.info("🔐 TLS Analyzer starting on port 5009")
    app.run(host='127.0.0.1', port=5009)
