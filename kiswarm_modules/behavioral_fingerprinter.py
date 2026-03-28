#!/usr/bin/env python3
"""
🧬 HEXSTRIKE BEHAVIORAL FINGERPRINTER v1.0
Purpose: Identify KI services by behavioral patterns and traffic signatures
Capabilities: Traffic pattern analysis, API call detection, streaming detection, behavioral profiling
"""

import logging
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict, Counter
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [BEHAVIORAL-FP] %(message)s')
logger = logging.getLogger('BEHAVIORAL_FP')

class BehavioralFingerprinter:
    """Identify KI services by their behavioral patterns"""
    
    # KI API request patterns
    KI_REQUEST_PATTERNS = {
        'chat_completion': {
            'patterns': [
                r'"messages"\s*:\s*\[',
                r'"model"\s*:\s*"[gpt|claude|llama]',
                r'"role"\s*:\s*"(user|assistant|system)"',
                r'"content"\s*:\s*"',
            ],
            'confidence': 90,
            'ki_type': 'chat_api',
        },
        'embedding': {
            'patterns': [
                r'"input"\s*:\s*["\[]',
                r'"model"\s*:\s*".*embed',
                r'/embeddings',
            ],
            'confidence': 85,
            'ki_type': 'embedding_api',
        },
        'image_gen': {
            'patterns': [
                r'"prompt"\s*:\s*"',
                r'"size"\s*:\s*"\d+x\d+"',
                r'/images/generations',
                r'"n"\s*:\s*\d+',
            ],
            'confidence': 80,
            'ki_type': 'image_api',
        },
        'streaming': {
            'patterns': [
                r'"stream"\s*:\s*true',
                r'Transfer-Encoding:\s*chunked',
                r'text/event-stream',
                r'data:\s*{',
            ],
            'confidence': 75,
            'ki_type': 'streaming_api',
        },
        'ollama': {
            'patterns': [
                r'/api/generate',
                r'/api/chat',
                r'/api/embeddings',
                r'"raw"\s*:',
                r'"template"\s*:',
            ],
            'confidence': 95,
            'ki_type': 'ollama',
        },
        'langchain': {
            'patterns': [
                r'langchain',
                r'LangChain',
                r'_type',
                r'_lc',
            ],
            'confidence': 70,
            'ki_type': 'langchain_app',
        },
    }
    
    # Response patterns
    KI_RESPONSE_PATTERNS = {
        'openai_response': {
            'patterns': [
                r'"id"\s*:\s*"chatcmpl-',
                r'"object"\s*:\s*"chat.completion',
                r'"choices"\s*:\s*\[',
                r'"usage"\s*:\s*{',
            ],
            'confidence': 95,
            'service': 'openai_compatible',
        },
        'anthropic_response': {
            'patterns': [
                r'"id"\s*:\s*"msg_',
                r'"type"\s*:\s*"message"',
                r'"content"\s*:\s*\[',
                r'"stop_reason"',
            ],
            'confidence': 95,
            'service': 'anthropic',
        },
        'ollama_response': {
            'patterns': [
                r'"model"\s*:\s*"[a-z]+',
                r'"created_at"',
                r'"done"\s*:',
                r'"total_duration"',
            ],
            'confidence': 90,
            'service': 'ollama',
        },
        'streaming_chunks': {
            'patterns': [
                r'data:\s*{"id"',
                r'data:\s*{"choices"',
                r'"delta"\s*:\s*{',
                r'\[DONE\]',
            ],
            'confidence': 85,
            'service': 'streaming_api',
        },
    }
    
    # Timing patterns (KI APIs often have specific response times)
    TIMING_PATTERNS = {
        'fast_local': {
            'min_ms': 10,
            'max_ms': 500,
            'likely': 'local_llm',
        },
        'fast_streaming': {
            'min_ms': 50,
            'max_ms': 2000,
            'likely': 'streaming_api',
        },
        'remote_api': {
            'min_ms': 500,
            'max_ms': 10000,
            'likely': 'remote_ki',
        },
    }
    
    # Port + Service combinations that indicate KI
    KI_PORT_SERVICES = {
        (11434, 'http'): {'service': 'ollama', 'confidence': 95},
        (5000, 'flask'): {'service': 'custom_ki', 'confidence': 60},
        (8000, 'uvicorn'): {'service': 'fastapi_ki', 'confidence': 60},
        (8080, 'proxy'): {'service': 'ki_proxy', 'confidence': 50},
        (8888, 'jupyter'): {'service': 'ml_notebook', 'confidence': 70},
    }
    
    def __init__(self):
        self.fingerprinted_services = {}
        self.behavioral_profiles = defaultdict(dict)
        
    def analyze_request_pattern(self, request_data: str) -> Dict:
        """Analyze request data for KI patterns"""
        results = {
            'detected_patterns': [],
            'highest_confidence': 0,
            'likely_ki_type': None,
        }
        
        for pattern_name, pattern_info in self.KI_REQUEST_PATTERNS.items():
            matches = 0
            for pattern in pattern_info['patterns']:
                if re.search(pattern, request_data, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                confidence = pattern_info['confidence'] * (matches / len(pattern_info['patterns']))
                results['detected_patterns'].append({
                    'pattern_type': pattern_name,
                    'ki_type': pattern_info['ki_type'],
                    'matches': matches,
                    'confidence': confidence,
                })
                
                if confidence > results['highest_confidence']:
                    results['highest_confidence'] = confidence
                    results['likely_ki_type'] = pattern_info['ki_type']
        
        return results
    
    def analyze_response_pattern(self, response_data: str) -> Dict:
        """Analyze response data for KI patterns"""
        results = {
            'detected_patterns': [],
            'highest_confidence': 0,
            'likely_service': None,
        }
        
        for pattern_name, pattern_info in self.KI_RESPONSE_PATTERNS.items():
            matches = 0
            for pattern in pattern_info['patterns']:
                if re.search(pattern, response_data, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                confidence = pattern_info['confidence'] * (matches / len(pattern_info['patterns']))
                results['detected_patterns'].append({
                    'pattern_type': pattern_name,
                    'service': pattern_info['service'],
                    'matches': matches,
                    'confidence': confidence,
                })
                
                if confidence > results['highest_confidence']:
                    results['highest_confidence'] = confidence
                    results['likely_service'] = pattern_info['service']
        
        return results
    
    def analyze_timing(self, response_time_ms: float) -> Dict:
        """Analyze response timing for clues"""
        for timing_name, timing_info in self.TIMING_PATTERNS.items():
            if timing_info['min_ms'] <= response_time_ms <= timing_info['max_ms']:
                return {
                    'timing_category': timing_name,
                    'likely_type': timing_info['likely'],
                    'response_time_ms': response_time_ms,
                }
        
        return {
            'timing_category': 'unknown',
            'response_time_ms': response_time_ms,
        }
    
    def fingerprint_service(self, host: str, port: int, endpoint: str = '/') -> Dict:
        """Full behavioral fingerprinting of a service"""
        fingerprint = {
            'host': host,
            'port': port,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat(),
            'ki_probability': 0,
            'indicators': [],
        }
        
        url = f"http://{host}:{port}{endpoint}"
        
        try:
            start_time = time.time()
            r = requests.get(url, timeout=10)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Analyze response
            response_analysis = self.analyze_response_pattern(r.text)
            fingerprint['response_analysis'] = response_analysis
            
            # Analyze timing
            timing_analysis = self.analyze_timing(response_time_ms)
            fingerprint['timing_analysis'] = timing_analysis
            
            # Check headers
            headers = dict(r.headers)
            for header, value in headers.items():
                header_lower = header.lower()
                if any(ki in header_lower for ki in ['api', 'model', 'ai', 'version']):
                    fingerprint['indicators'].append({
                        'type': 'header',
                        'header': header,
                        'value': value,
                    })
            
            # Check content-type
            content_type = headers.get('content-type', '')
            if 'application/json' in content_type:
                fingerprint['indicators'].append({
                    'type': 'content_type',
                    'value': 'json_api',
                })
            elif 'text/event-stream' in content_type:
                fingerprint['indicators'].append({
                    'type': 'content_type',
                    'value': 'streaming_api',
                })
            
            # Calculate KI probability
            confidence = response_analysis.get('highest_confidence', 0)
            
            # Boost if certain port+service combos
            port_service_key = (port, 'http')
            if port_service_key in self.KI_PORT_SERVICES:
                confidence += self.KI_PORT_SERVICES[port_service_key]['confidence'] * 0.5
            
            fingerprint['ki_probability'] = min(100, confidence)
            
            # Determine if KI
            if fingerprint['ki_probability'] > 50:
                fingerprint['is_ki'] = True
                fingerprint['ki_type'] = response_analysis.get('likely_service', 'unknown')
                logger.info(f"🧬 KI detected: {host}:{port} (prob: {fingerprint['ki_probability']:.0f}%)")
            
        except Exception as e:
            fingerprint['error'] = str(e)
        
        self.fingerprinted_services[f"{host}:{port}"] = fingerprint
        return fingerprint
    
    def profile_host(self, host: str, ports: List[int] = None) -> Dict:
        """Create behavioral profile of host"""
        ports = ports or [11434, 5000, 8000, 8080, 8888]
        
        profile = {
            'host': host,
            'timestamp': datetime.now().isoformat(),
            'services': [],
            'ki_services': [],
            'profile': {},
        }
        
        for port in ports:
            fp = self.fingerprint_service(host, port)
            if fp.get('ki_probability', 0) > 0:
                profile['services'].append(fp)
                if fp.get('is_ki'):
                    profile['ki_services'].append({
                        'port': port,
                        'ki_type': fp.get('ki_type'),
                        'probability': fp.get('ki_probability'),
                    })
        
        # Create summary profile
        if profile['ki_services']:
            profile['profile']['has_ki'] = True
            profile['profile']['ki_count'] = len(profile['ki_services'])
            profile['profile']['ki_types'] = list(set(s['ki_type'] for s in profile['ki_services']))
        
        self.behavioral_profiles[host] = profile
        return profile
    
    def get_status(self):
        return {
            "services_fingerprinted": len(self.fingerprinted_services),
            "hosts_profiled": len(self.behavioral_profiles),
            "ki_services_found": sum(1 for s in self.fingerprinted_services.values() if s.get('is_ki')),
        }


# Flask API
from flask import Flask, jsonify, request

app = Flask(__name__)
fingerprinter = BehavioralFingerprinter()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-Behavioral-Fingerprinter",
        "version": "1.0",
        "capabilities": [
            "Request pattern analysis",
            "Response pattern detection",
            "Timing analysis",
            "KI probability calculation"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Fingerprinter status",
            "/fingerprint/<host>/<int:port>": "Fingerprint service",
            "/profile/<host>": "Profile host"
        }
    })

@app.route('/status')
def status():
    return jsonify(fingerprinter.get_status())

@app.route('/fingerprint/<host>/<int:port>')
def fingerprint(host, port):
    endpoint = request.args.get('endpoint', '/')
    result = fingerprinter.fingerprint_service(host, port, endpoint)
    return jsonify(result)

@app.route('/profile/<host>')
def profile(host):
    result = fingerprinter.profile_host(host)
    return jsonify(result)


if __name__ == '__main__':
    logger.info("🧬 Behavioral Fingerprinter starting on port 5014")
    app.run(host='127.0.0.1', port=5014)
