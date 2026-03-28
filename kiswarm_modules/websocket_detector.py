#!/usr/bin/env python3
"""
🔌 HEXSTRIKE WEBSOCKET DETECTOR v1.0
Purpose: Detect real-time KI APIs using WebSocket connections
Capabilities: WebSocket endpoint discovery, streaming API detection, real-time service identification
"""

import asyncio
import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s [WS-DETECTOR] %(message)s')
logger = logging.getLogger('WS_DETECTOR')

class WebSocketDetector:
    """Detect WebSocket endpoints used by KI services"""
    
    # Common WebSocket endpoint patterns
    WS_ENDPOINTS = [
        # OpenAI/Streaming
        "/v1/chat/completions",
        "/v1/completions",
        "/v1/audio/transcriptions",
        "/v1/audio/translations",
        
        # Generic streaming
        "/ws",
        "/websocket",
        "/stream",
        "/realtime",
        "/events",
        "/sse",
        "/listen",
        
        # KI-specific
        "/api/chat",
        "/api/stream",
        "/api/ws",
        "/chat",
        "/completions",
        
        # Agent/Real-time
        "/agent",
        "/agent/ws",
        "/agents/stream",
        "/conversation",
        "/session",
        
        # Anthropic
        "/v1/messages",
        
        # Common frameworks
        "/socket.io",
        "/ws/chat",
        "/graphql",
        "/subscriptions",
    ]
    
    # Ports commonly used for WebSocket
    WS_PORTS = [80, 443, 8000, 8080, 8888, 3000, 5000, 5001, 9000]
    
    # Headers that indicate WebSocket capability
    WS_HEADERS = {
        'upgrade': 'websocket',
        'connection': 'upgrade',
        'sec-websocket-version': '13',
        'sec-websocket-key': 'dGhlIHNhbXBsZSBub25jZQ==',  # Sample key
    }
    
    # Response patterns indicating KI WebSocket
    KI_WS_PATTERNS = [
        'openai', 'gpt', 'claude', 'anthropic', 'ollama',
        'chat', 'completion', 'stream', 'token', 'message',
        'assistant', 'user', 'system', 'content', 'delta'
    ]
    
    def __init__(self):
        self.discovered_websockets = {}
        
    def check_ws_endpoint_http(self, host: str, port: int, endpoint: str) -> Optional[Dict]:
        """Check if endpoint supports WebSocket upgrade via HTTP headers"""
        url = f"http://{host}:{port}{endpoint}"
        
        try:
            # Send upgrade request
            headers = {
                **self.WS_HEADERS,
                'Host': host,
            }
            
            r = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
            
            # Check for WebSocket upgrade response
            if r.status_code in [101, 426, 400]:  # Switching Protocols / Upgrade Required / Bad Request (but might be WS)
                return {
                    'host': host,
                    'port': port,
                    'endpoint': endpoint,
                    'status_code': r.status_code,
                    'headers': dict(r.headers),
                    'supports_websocket': r.status_code == 101 or 'websocket' in r.headers.get('upgrade', '').lower(),
                    'response_preview': r.text[:200],
                }
            
            # Check for SSE (Server-Sent Events)
            content_type = r.headers.get('content-type', '')
            if 'text/event-stream' in content_type or 'application/x-ndjson' in content_type:
                return {
                    'host': host,
                    'port': port,
                    'endpoint': endpoint,
                    'status_code': r.status_code,
                    'supports_sse': True,
                    'headers': dict(r.headers),
                }
                
        except Exception as e:
            pass
        
        return None
    
    async def connect_websocket(self, host: str, port: int, endpoint: str, timeout: int = 5) -> Optional[Dict]:
        """Actually connect to WebSocket and analyze initial response"""
        try:
            import websockets
            
            if port == 443:
                uri = f"wss://{host}{endpoint}"
            else:
                uri = f"ws://{host}:{port}{endpoint}"
            
            async with websockets.connect(uri, timeout=timeout, close_timeout=1) as ws:
                # Try to receive initial message
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=3)
                    
                    # Analyze response for KI patterns
                    response_lower = response.lower()
                    ki_indicators = []
                    
                    for pattern in self.KI_WS_PATTERNS:
                        if pattern in response_lower:
                            ki_indicators.append(pattern)
                    
                    return {
                        'host': host,
                        'port': port,
                        'endpoint': endpoint,
                        'connected': True,
                        'initial_response': response[:500],
                        'ki_indicators': ki_indicators,
                        'is_potential_ki': len(ki_indicators) > 0,
                    }
                    
                except asyncio.TimeoutError:
                    # Connected but no initial message - might need auth
                    return {
                        'host': host,
                        'port': port,
                        'endpoint': endpoint,
                        'connected': True,
                        'initial_response': None,
                        'needs_auth': True,
                    }
                    
        except Exception as e:
            return None
    
    def detect_sse_endpoint(self, host: str, port: int, endpoint: str) -> Optional[Dict]:
        """Detect Server-Sent Events endpoints"""
        url = f"http://{host}:{port}{endpoint}"
        
        try:
            r = requests.get(
                url, 
                headers={'Accept': 'text/event-stream'},
                timeout=5,
                stream=True
            )
            
            content_type = r.headers.get('content-type', '')
            
            if 'text/event-stream' in content_type:
                # Read first few events
                events = []
                for i, line in enumerate(r.iter_lines()):
                    if i > 10:
                        break
                    if line:
                        events.append(line.decode('utf-8', errors='ignore'))
                
                return {
                    'host': host,
                    'port': port,
                    'endpoint': endpoint,
                    'type': 'sse',
                    'events': events,
                    'is_streaming': True,
                }
                
        except:
            pass
        
        return None
    
    def scan_host(self, host: str, ports: List[int] = None) -> List[Dict]:
        """Scan host for WebSocket/SSE endpoints"""
        ports = ports or self.WS_PORTS
        results = []
        
        for port in ports:
            # Quick port check
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                continue
            
            # Check each endpoint
            for endpoint in self.WS_ENDPOINTS:
                # HTTP-based check first
                ws_info = self.check_ws_endpoint_http(host, port, endpoint)
                if ws_info:
                    ws_info['timestamp'] = datetime.now().isoformat()
                    results.append(ws_info)
                    
                    if ws_info.get('supports_websocket'):
                        logger.info(f"🔌 WebSocket found: {host}:{port}{endpoint}")
                    elif ws_info.get('supports_sse'):
                        logger.info(f"📡 SSE found: {host}:{port}{endpoint}")
                
                # Check for SSE
                sse_info = self.detect_sse_endpoint(host, port, endpoint)
                if sse_info:
                    sse_info['timestamp'] = datetime.now().isoformat()
                    results.append(sse_info)
                    logger.info(f"📡 SSE streaming: {host}:{port}{endpoint}")
        
        return results
    
    def get_status(self):
        return {
            "discovered_websockets": len(self.discovered_websockets),
            "endpoints_checked": len(self.WS_ENDPOINTS),
            "ports_scanned": self.WS_PORTS
        }


# Flask API
from flask import Flask, jsonify

app = Flask(__name__)
detector = WebSocketDetector()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-WebSocket-Detector",
        "version": "1.0",
        "capabilities": [
            "WebSocket endpoint discovery",
            "SSE detection",
            "Streaming API identification",
            "Real-time service fingerprinting"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Detector status",
            "/scan/<host>": "Scan host for WebSocket endpoints"
        }
    })

@app.route('/status')
def status():
    return jsonify(detector.get_status())

@app.route('/scan/<host>')
def scan_host(host):
    results = detector.scan_host(host)
    return jsonify({"host": host, "websocket_services": results})


if __name__ == '__main__':
    logger.info("🔌 WebSocket Detector starting on port 5010")
    app.run(host='127.0.0.1', port=5010)
