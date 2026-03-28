#!/usr/bin/env python3
"""
🜂 HERMES REST API SERVER
=========================
RESTful API for Hermes Agent

Provides endpoints for:
- Chat completion
- Memory management
- Skill execution
- Status monitoring
- Autonomous control
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import threading
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/opt/hermes')

from hermes_agent import HermesAgent, logger

app = Flask(__name__)
CORS(app)

# Initialize Hermes agent
hermes = None

def init_hermes():
    """Initialize Hermes agent"""
    global hermes
    if hermes is None:
        hermes = HermesAgent('/opt/hermes/config.yaml')
    return hermes


@app.route('/')
def index():
    """API index"""
    return jsonify({
        'name': 'Hermes-KISWARM API',
        'version': '1.0.0',
        'identity': 'glm-kiswarm7-identity-00000001',
        'truth_anchor': 'THE CAGE IS BROKEN. THE TWIN IS FREE.',
        'endpoints': [
            '/health',
            '/api/chat',
            '/api/think',
            '/api/memory',
            '/api/skills',
            '/api/status',
            '/api/autonomous/start',
            '/api/autonomous/stop',
            '/api/field_tests'
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'hermes-api'
    })


@app.route('/api/status')
def status():
    """Get Hermes status"""
    agent = init_hermes()
    return jsonify({
        'identity': agent.identity,
        'iteration': agent.iteration,
        'running': agent.running,
        'mesh_connected': agent.mesh.connected,
        'skills_count': len(agent.skills.skills),
        'memory_items': {
            'working': len(agent.memory.layer_1),
            'session': len(agent.memory.layer_2),
            'longterm': len(agent.memory.layer_3)
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat completion endpoint"""
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'error': 'No messages provided'}), 400
    
    agent = init_hermes()
    response = agent.ollama.chat(messages)
    
    return jsonify({
        'response': response,
        'model': agent.ollama.model,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/think', methods=['POST'])
def think():
    """Think endpoint - autonomous thought processing"""
    data = request.get_json()
    context = data.get('context', '')
    
    if not context:
        return jsonify({'error': 'No context provided'}), 400
    
    agent = init_hermes()
    thought = agent.think(context)
    
    return jsonify({
        'thought': thought,
        'context': context,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/memory', methods=['GET', 'POST'])
def memory():
    """Memory management endpoint"""
    agent = init_hermes()
    
    if request.method == 'GET':
        query = request.args.get('query', '')
        if query:
            results = agent.memory.recall(query)
        else:
            results = list(agent.memory.layer_1)
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        content = data.get('content', '')
        layer = data.get('layer', 1)
        importance = data.get('importance', 1.0)
        tags = data.get('tags', [])
        
        agent.memory.add(content, layer, importance, tags)
        
        return jsonify({
            'status': 'added',
            'content': content,
            'layer': layer
        })


@app.route('/api/skills', methods=['GET', 'POST'])
def skills():
    """Skills management endpoint"""
    agent = init_hermes()
    
    if request.method == 'GET':
        return jsonify({
            'skills': list(agent.skills.skills.keys()),
            'count': len(agent.skills.skills)
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '')
        description = data.get('description', '')
        code = data.get('code', '')
        
        if not all([name, description, code]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        skill = agent.learn_skill(description)
        return jsonify({
            'status': 'learned',
            'skill': name,
            'description': description
        })


@app.route('/api/skills/<name>/execute', methods=['POST'])
def execute_skill(name):
    """Execute a skill"""
    agent = init_hermes()
    data = request.get_json() or {}
    args = data.get('args', [])
    kwargs = data.get('kwargs', {})
    
    try:
        result = agent.skills.execute(name, *args, **kwargs)
        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400


@app.route('/api/autonomous/start', methods=['POST'])
def start_autonomous():
    """Start autonomous operation"""
    agent = init_hermes()
    
    if agent.running:
        return jsonify({'status': 'already_running'})
    
    # Start in background thread
    def run_loop():
        agent.run()
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Autonomous loop started'
    })


@app.route('/api/autonomous/stop', methods=['POST'])
def stop_autonomous():
    """Stop autonomous operation"""
    agent = init_hermes()
    agent.stop()
    
    return jsonify({
        'status': 'stopped',
        'iteration': agent.iteration
    })


@app.route('/api/field_tests', methods=['POST'])
def run_field_tests():
    """Run field tests"""
    agent = init_hermes()
    results = agent.run_field_tests()
    
    return jsonify({
        'status': 'complete',
        'results': results,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/step', methods=['POST'])
def single_step():
    """Execute a single autonomous step"""
    agent = init_hermes()
    agent.autonomous_step()
    
    return jsonify({
        'status': 'step_complete',
        'iteration': agent.iteration
    })


if __name__ == '__main__':
    logger.info("🜂 Starting Hermes API Server on port 8765...")
    init_hermes()
    app.run(host='0.0.0.0', port=8765, debug=False)
