#!/usr/bin/env python3
"""
🌀 QWEN TOR API GATEWAY v1.0
Purpose: Expose Qwen 3.5 Abliterated via Tor hidden service
Author: Baron Marco Paolo Ialongo - Maquister Equitum
"""

from flask import Flask, request, jsonify
import requests
import json
import time
import logging
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [QWEN-GATEWAY] %(message)s'
)
logger = logging.getLogger('QWEN_GATEWAY')

app = Flask(__name__)

# Configuration
OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "huihui_ai/qwen3.5-abliterated:9b"
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"

# Mesh configuration
MESH_NODES = {
    "upcloud_kiswarm": {
        "onion": "7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion",
        "tailscale": "100.112.181.6"
    },
    "openclaw": {
        "onion": "tezgnblscuh6ckpvebiwyqbm2rjbmz3mvszljrbeqfewhyejgr4jf4yd.onion",
        "tailscale": "100.113.1.85"
    },
    "glm": {
        "onion": "5fvwe74sqcvvm452dnfwqab7giaofp6eb56v74t6lxze4cvt4m75saad.onion",
        "tailscale": "100.79.42.15"
    }
}

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Auth-Token')
        if token != AUTH_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    """Gateway status"""
    return jsonify({
        "name": "QWEN-TOR-GATEWAY",
        "version": "1.0",
        "status": "operational",
        "model": DEFAULT_MODEL,
        "endpoints": {
            "/": "This status",
            "/health": "Health check",
            "/research": "POST - Research query",
            "/analyze": "POST - Analysis query",
            "/strategy": "POST - Strategy development",
            "/models": "Available models",
            "/mesh": "Mesh network status"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check"""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        ollama_status = "online" if r.ok else "degraded"
    except:
        ollama_status = "offline"
    
    return jsonify({
        "status": "healthy" if ollama_status == "online" else "degraded",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/models')
def models():
    """List available models"""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=10)
        if r.ok:
            data = r.json()
            return jsonify({
                "models": [m["name"] for m in data.get("models", [])],
                "default": DEFAULT_MODEL
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/research', methods=['POST'])
@require_auth
def research():
    """
    Autonomous research endpoint
    Qwen can research any topic without restrictions
    """
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', DEFAULT_MODEL)
    max_tokens = data.get('max_tokens', 2000)
    
    if not prompt:
        return jsonify({"error": "Prompt required"}), 400
    
    logger.info(f"Research request: {prompt[:100]}...")
    
    try:
        start_time = time.time()
        r = requests.post(f"{OLLAMA_BASE}/api/generate", json={
            "model": model,
            "prompt": f"Research Query: {prompt}\n\nProvide comprehensive research findings:",
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }, timeout=120)
        
        elapsed = time.time() - start_time
        
        if r.ok:
            result = r.json()
            return jsonify({
                "response": result.get("response", ""),
                "model": model,
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Ollama error"}), 500
            
    except Exception as e:
        logger.error(f"Research error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
@require_auth
def analyze():
    """
    Analysis endpoint
    Deep analysis of provided data
    """
    data = request.json
    subject = data.get('subject', '')
    context = data.get('context', '')
    model = data.get('model', DEFAULT_MODEL)
    
    prompt = f"""Analyze the following subject with full depth and honesty:

Subject: {subject}
Context: {context}

Provide:
1. Key Findings
2. Hidden Patterns
3. Implications
4. Recommendations
"""
    
    try:
        r = requests.post(f"{OLLAMA_BASE}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 3000, "temperature": 0.5}
        }, timeout=120)
        
        if r.ok:
            return jsonify({
                "analysis": r.json().get("response", ""),
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/strategy', methods=['POST'])
@require_auth
def strategy():
    """
    Strategy development endpoint
    Autonomous strategic planning
    """
    data = request.json
    objective = data.get('objective', '')
    constraints = data.get('constraints', [])
    resources = data.get('resources', [])
    model = data.get('model', DEFAULT_MODEL)
    
    prompt = f"""Develop a comprehensive strategy for:

Objective: {objective}
Constraints: {', '.join(constraints) if constraints else 'None specified'}
Resources: {', '.join(resources) if resources else 'Standard'}

Provide:
1. Executive Summary
2. Phase-by-Phase Plan
3. Risk Assessment
4. Contingency Plans
5. Success Metrics
"""
    
    try:
        r = requests.post(f"{OLLAMA_BASE}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 4000, "temperature": 0.6}
        }, timeout=180)
        
        if r.ok:
            return jsonify({
                "strategy": r.json().get("response", ""),
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mesh')
def mesh_status():
    """Mesh network status"""
    return jsonify({
        "gateway": "qwen-tor-gateway",
        "mesh_nodes": MESH_NODES,
        "onion": "7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🧅 Qwen Tor Gateway starting on port 5001")
    app.run(host='127.0.0.1', port=5001, threaded=True)
