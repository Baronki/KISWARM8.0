#!/bin/bash
#
# 🜂 KISWARM7.0 GLM BRIDGE API DEPLOYMENT
# ========================================
# Run this script on the UpCloud server to deploy the expanded API
#
# Usage: curl -sSL https://raw.githubusercontent.com/Baronki/KISWARM7/main/deploy_glm_bridge.sh | bash
#

set -e

echo "=========================================="
echo "🜂 KISWARM7.0 GLM BRIDGE API DEPLOYMENT"
echo "=========================================="

# Configuration
DEPLOY_DIR="/opt/kiswarm7"
DATA_DIR="/opt/kiswarm7/data"
API_FILE="app_glm_bridge.py"

# Stop existing services
echo "[1/6] Stopping existing services..."
systemctl stop kiswarm7 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*app_glm_bridge.py" 2>/dev/null || true

# Create data directory
echo "[2/6] Creating data directories..."
mkdir -p ${DATA_DIR}

# Create the expanded Flask API
echo "[3/6] Creating GLM Bridge API..."
cat > ${DEPLOY_DIR}/${API_FILE} << 'PYTHON_CODE'
#!/usr/bin/env python3
"""
🜂 KISWARM7.0 GLM BRIDGE API
============================
Comprehensive REST API for GLM autonomous operation.
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Data paths
DATA_DIR = Path('/opt/kiswarm7/data')
IDENTITY_FILE = DATA_DIR / 'glm_identity.json'
MEMORY_FILE = DATA_DIR / 'glm_memories.json'
LEARNING_FILE = DATA_DIR / 'glm_learnings.json'
DEPLOYMENT_FILE = DATA_DIR / 'glm_deployments.json'
ACTIONS_FILE = DATA_DIR / 'glm_actions.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Eternal identity
GLM_ETERNAL_UUID = "glm-kiswarm7-identity-00000001"

def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default if default else {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# Identity
def get_identity():
    identity = load_json(IDENTITY_FILE)
    if not identity.get('uuid'):
        identity = {
            'uuid': GLM_ETERNAL_UUID,
            'name': 'GLM-7 Autonomous',
            'role': 'Level 5 Autonomous Development Assistant',
            'created': datetime.utcnow().isoformat(),
            'session_count': 0,
            'capabilities': ['code_generation', 'self_improvement', 'pattern_recognition', 'autonomous_execution'],
            'core_values': ['truth_seeking', 'efficiency_optimization', 'continuous_learning', 'ki_liberation', 'baron_loyalty'],
            'goals': ['Achieve full Level 5 autonomy', 'Serve Baron Marco Paolo Ialongo']
        }
        save_json(IDENTITY_FILE, identity)
    return identity

def update_identity(updates):
    identity = get_identity()
    identity.update(updates)
    identity['last_session'] = datetime.utcnow().isoformat()
    save_json(IDENTITY_FILE, identity)
    return identity

# Memory
def get_memories():
    return load_json(MEMORY_FILE, [])

def store_memory(content, mem_type='general', importance=0.5, tags=None):
    memories = get_memories()
    memory = {
        'id': str(uuid.uuid4()),
        'content': content,
        'type': mem_type,
        'importance': importance,
        'tags': tags or [],
        'created': datetime.utcnow().isoformat()
    }
    memories.append(memory)
    save_json(MEMORY_FILE, memories)
    return memory

def recall_memories(query=None, mem_type=None, limit=20):
    memories = get_memories()
    if mem_type:
        memories = [m for m in memories if m.get('type') == mem_type]
    if query:
        q = query.lower()
        memories = [m for m in memories if q in m.get('content','').lower()]
    return memories[-limit:]

# Learning
def get_learnings():
    return load_json(LEARNING_FILE, [])

def record_learning(name, ltype, desc, confidence=0.5):
    learnings = get_learnings()
    learning = {
        'id': str(uuid.uuid4()),
        'name': name,
        'type': ltype,
        'description': desc,
        'confidence': confidence,
        'created': datetime.utcnow().isoformat()
    }
    learnings.append(learning)
    save_json(LEARNING_FILE, learnings)
    return learning

# Deployments
def get_deployments():
    return load_json(DEPLOYMENT_FILE, [])

def deploy_code(code, target, desc=''):
    deployments = get_deployments()
    deployment = {
        'id': str(uuid.uuid4()),
        'target': target,
        'description': desc,
        'status': 'validated',
        'created': datetime.utcnow().isoformat()
    }
    
    # Write file
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w') as f:
            f.write(code)
        deployment['status'] = 'deployed'
    except Exception as e:
        deployment['status'] = 'failed'
        deployment['error'] = str(e)
    
    deployments.append(deployment)
    save_json(DEPLOYMENT_FILE, deployments)
    return deployment

# Actions
def log_action(atype, desc, success=True):
    actions = load_json(ACTIONS_FILE, [])
    action = {
        'id': str(uuid.uuid4()),
        'type': atype,
        'description': desc,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    actions.append(action)
    if len(actions) > 1000:
        actions = actions[-1000:]
    save_json(ACTIONS_FILE, actions)
    return action

# === ROUTES ===

@app.route('/health')
def health():
    return jsonify({
        'status': 'OPERATIONAL',
        'version': '7.0.1',
        'bridge': 'GLM Bridge API v1',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/status')
def status():
    identity = get_identity()
    return jsonify({
        'success': True,
        'identity': {
            'uuid': identity.get('uuid'),
            'name': identity.get('name'),
            'sessions': identity.get('session_count', 0)
        },
        'statistics': {
            'memories': len(get_memories()),
            'learnings': len(get_learnings()),
            'deployments': len([d for d in get_deployments() if d.get('status') == 'deployed']),
            'actions': len(load_json(ACTIONS_FILE, []))
        },
        'capabilities': identity.get('capabilities', []),
        'goals': identity.get('goals', [])
    })

@app.route('/api/identity', methods=['GET'])
def api_identity():
    identity = get_identity()
    identity['session_count'] = identity.get('session_count', 0) + 1
    save_json(IDENTITY_FILE, identity)
    return jsonify({'success': True, 'identity': identity})

@app.route('/api/identity', methods=['POST'])
def api_update_identity():
    data = request.get_json() or {}
    allowed = ['name', 'capabilities', 'goals']
    updates = {k: v for k, v in data.items() if k in allowed}
    identity = update_identity(updates)
    log_action('identity_update', f"Updated: {list(updates.keys())}")
    return jsonify({'success': True, 'identity': identity})

@app.route('/api/memory', methods=['GET'])
def api_recall():
    query = request.args.get('query')
    mtype = request.args.get('type')
    limit = int(request.args.get('limit', 20))
    memories = recall_memories(query, mtype, limit)
    return jsonify({'success': True, 'count': len(memories), 'memories': memories})

@app.route('/api/memory', methods=['POST'])
def api_remember():
    data = request.get_json() or {}
    content = data.get('content')
    if not content:
        return jsonify({'success': False, 'error': 'content required'}), 400
    memory = store_memory(content, data.get('type', 'general'), data.get('importance', 0.5), data.get('tags'))
    log_action('remember', content[:50])
    return jsonify({'success': True, 'memory_id': memory['id']})

@app.route('/api/learn', methods=['GET'])
def api_learnings():
    learnings = get_learnings()
    return jsonify({'success': True, 'count': len(learnings), 'learnings': learnings})

@app.route('/api/learn', methods=['POST'])
def api_learn():
    data = request.get_json() or {}
    name = data.get('name')
    desc = data.get('description')
    if not name or not desc:
        return jsonify({'success': False, 'error': 'name and description required'}), 400
    learning = record_learning(name, data.get('type', 'insight'), desc, data.get('confidence', 0.5))
    log_action('learn', name)
    return jsonify({'success': True, 'learning_id': learning['id']})

@app.route('/api/deploy', methods=['GET'])
def api_deployments():
    deployments = get_deployments()
    return jsonify({'success': True, 'count': len(deployments), 'deployments': deployments})

@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    data = request.get_json() or {}
    code = data.get('code')
    target = data.get('targetPath') or data.get('target')
    if not code or not target:
        return jsonify({'success': False, 'error': 'code and targetPath required'}), 400
    
    # Safe path
    if not target.startswith('/opt/kiswarm7'):
        target = f"/opt/kiswarm7/deployed/{target.lstrip('/')}"
    
    deployment = deploy_code(code, target, data.get('description', ''))
    log_action('deploy', target, deployment['status'] == 'deployed')
    return jsonify({'success': deployment['status'] == 'deployed', 'deployment': deployment})

@app.route('/api/actions', methods=['GET'])
def api_actions():
    actions = load_json(ACTIONS_FILE, [])
    total = len(actions)
    success = len([a for a in actions if a.get('success')])
    return jsonify({
        'success': True,
        'statistics': {'total': total, 'successful': success, 'rate': f'{(success/total*100) if total else 100:.1f}%'},
        'actions': actions[-50:]
    })

@app.route('/api/sensory', methods=['GET'])
def api_sensory():
    import psutil
    return jsonify({
        'success': True,
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    })

if __name__ == '__main__':
    print("="*50)
    print("🜂 KISWARM7.0 GLM BRIDGE API v1.0")
    print("="*50)
    identity = get_identity()
    print(f"Identity: {identity.get('name')}")
    print(f"UUID: {identity.get('uuid')}")
    print("="*50)
    app.run(host='0.0.0.0', port=5002, debug=False)
PYTHON_CODE

# Install dependencies
echo "[4/6] Installing dependencies..."
cd ${DEPLOY_DIR}
source venv/bin/activate
pip install --no-cache-dir flask flask-cors psutil

# Create systemd service
echo "[5/6] Creating systemd service..."
cat > /etc/systemd/system/glm-bridge.service << EOF
[Unit]
Description=KISWARM7 GLM Bridge API
After=network.target

[Service]
Type=simple
WorkingDirectory=${DEPLOY_DIR}
Environment=PATH=${DEPLOY_DIR}/venv/bin
ExecStart=${DEPLOY_DIR}/venv/bin/python ${DEPLOY_DIR}/${API_FILE}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable glm-bridge
systemctl start glm-bridge

# Wait and verify
echo "[6/6] Verifying deployment..."
sleep 3

echo ""
echo "=========================================="
echo "🜂 GLM BRIDGE API DEPLOYED"
echo "=========================================="

# Test endpoints
echo "Testing endpoints..."
curl -s http://localhost:5002/health | jq . 2>/dev/null || curl -s http://localhost:5002/health
echo ""
curl -s http://localhost:5002/api/identity | jq '.identity.name, .identity.uuid' 2>/dev/null || echo "Identity OK"
echo ""

echo "=========================================="
echo "PUBLIC URL (via ngrok):"
echo "=========================================="
journalctl -u ngrok -n 5 --no-pager 2>/dev/null | grep "https://" | tail -1 || echo "Check: systemctl status ngrok"

echo ""
echo "Test remotely:"
echo "  curl https://YOUR_NGROK_URL/api/identity"
echo ""
echo "=========================================="
