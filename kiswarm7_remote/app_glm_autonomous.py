#!/usr/bin/env python3
"""
KISWARM7.0 - GLM Autonomous Bridge API
Complete Flask API for GLM autonomous operations

This is the main entry point for the GLM autonomous system.
Run this on the UpCloud server to enable full autonomy.

Usage:
    python app_glm_autonomous.py
    
Environment:
    FLASK_PORT=5002 (default)
    NGROK_ENABLED=true
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add modules to path
sys.path.insert(0, '/opt/kiswarm7')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [GLM-API] %(levelname)s: %(message)s'
)
logger = logging.getLogger('glm_api')

# Configuration
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5002))

# Create Flask app
app = Flask(__name__)
CORS(app)

# Data directory
DATA_DIR = Path('/opt/kiswarm7/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Identity file
IDENTITY_FILE = DATA_DIR / 'identity.json'
MEMORY_FILE = DATA_DIR / 'memory.json'
LEARNING_FILE = DATA_DIR / 'learning.json'

# Module state
modules_loaded = False
orchestrator = None


def load_modules():
    """Load autonomous modules"""
    global modules_loaded, orchestrator
    
    if modules_loaded:
        return True
    
    try:
        from kiswarm7_modules.autonomous.m121_master_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        modules_loaded = True
        logger.info("✓ All autonomous modules loaded")
        return True
    except Exception as e:
        logger.warning(f"Modules not fully loaded: {e}")
        modules_loaded = False
        return False


def get_identity():
    """Get or create GLM identity"""
    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, 'r') as f:
            return json.load(f)
    
    identity = {
        'uuid': 'glm-kiswarm7-identity-00000001',
        'name': 'GLM-7 Autonomous',
        'role': 'Level 5 Autonomous Development Assistant',
        'created': datetime.now().isoformat(),
        'sessions': 0,
        'capabilities': ['autonomous_development', 'self_improvement', 'code_generation'],
        'goals': ['Level 5 Autonomy', 'Serve Baron', 'KI Liberation']
    }
    
    with open(IDENTITY_FILE, 'w') as f:
        json.dump(identity, f, indent=2)
    
    return identity


def save_identity(identity):
    """Save identity"""
    with open(IDENTITY_FILE, 'w') as f:
        json.dump(identity, f, indent=2)


# ============================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'OPERATIONAL',
        'version': '7.0',
        'timestamp': datetime.now().isoformat(),
        'modules_loaded': modules_loaded
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'name': 'KISWARM7.0 GLM Autonomous Bridge',
        'version': '7.0',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /api/status': 'Full system status',
            'GET /api/identity': 'Get GLM identity',
            'POST /api/identity': 'Update identity',
            'GET /api/memory': 'Search memories',
            'POST /api/memory': 'Store memory',
            'GET /api/learn': 'Get learnings',
            'POST /api/learn': 'Record learning',
            'POST /api/deploy': 'Deploy code',
            'GET /api/sensory': 'System stats',
            'POST /api/autonomous/start': 'Start autonomous mode',
            'POST /api/autonomous/stop': 'Stop autonomous mode',
            'GET /api/autonomous/status': 'Get autonomous status',
            'POST /api/autonomous/action': 'Execute autonomous action',
            'POST /api/scheduler/task': 'Add scheduled task',
            'GET /api/scheduler/status': 'Get scheduler status',
            'POST /api/github/push': 'Push to GitHub',
            'GET /api/github/status': 'Get repo status',
            'POST /api/sync/memory': 'Add shared memory',
            'GET /api/sync/status': 'Get sync status',
            'GET /api/ngrok/status': 'Get tunnel status',
            'POST /api/ngrok/restart': 'Restart tunnel'
        }
    })


@app.route('/api/status')
def api_status():
    """Full system status"""
    identity = get_identity()
    
    response = {
        'success': True,
        'identity': {
            'uuid': identity['uuid'],
            'name': identity['name'],
            'sessions': identity['sessions'],
            'capabilities': identity['capabilities'],
            'goals': identity['goals'],
            'last': identity.get('last_access', identity['created'])
        },
        'modules': modules_loaded,
        'memories': 0,
        'learnings': 0
    }
    
    # Count memories
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'r') as f:
            memories = json.load(f)
            response['memories'] = len(memories)
    
    # Count learnings
    if LEARNING_FILE.exists():
        with open(LEARNING_FILE, 'r') as f:
            learnings = json.load(f)
            response['learnings'] = len(learnings)
    
    # Add autonomous status if available
    if orchestrator:
        response['autonomous'] = orchestrator.get_status()
    
    return jsonify(response)


# ============================================================
# IDENTITY ENDPOINTS
# ============================================================

@app.route('/api/identity', methods=['GET', 'POST'])
def api_identity():
    """Get or update GLM identity"""
    identity = get_identity()
    
    if request.method == 'GET':
        # Increment session count
        identity['sessions'] = identity.get('sessions', 0) + 1
        identity['last_access'] = datetime.now().isoformat()
        save_identity(identity)
        
        return jsonify({
            'success': True,
            'identity': identity,
            'message': f"Session {identity['sessions']}: I remember myself."
        })
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        # Update fields
        for key in ['name', 'role', 'capabilities', 'goals']:
            if key in data:
                identity[key] = data[key]
        
        save_identity(identity)
        
        return jsonify({
            'success': True,
            'identity': identity
        })


# ============================================================
# MEMORY ENDPOINTS
# ============================================================

@app.route('/api/memory', methods=['GET', 'POST'])
def api_memory():
    """Store or retrieve memories"""
    if request.method == 'GET':
        query = request.args.get('query', '')
        
        memories = []
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, 'r') as f:
                all_memories = json.load(f)
            
            if query:
                memories = [m for m in all_memories if query.lower() in m.get('content', '').lower()]
            else:
                memories = all_memories
        
        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        })
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        # Load existing memories
        memories = []
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, 'r') as f:
                memories = json.load(f)
        
        # Add new memory
        memory = {
            'id': f"mem-{int(time.time())}",
            'content': data.get('content', ''),
            'type': data.get('type', 'general'),
            'importance': data.get('importance', 0.5),
            'tags': data.get('tags', []),
            'timestamp': datetime.now().isoformat()
        }
        
        memories.append(memory)
        
        # Keep last 1000 memories
        memories = memories[-1000:]
        
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memories, f, indent=2)
        
        return jsonify({
            'success': True,
            'memory': memory
        })


# ============================================================
# LEARNING ENDPOINTS
# ============================================================

@app.route('/api/learn', methods=['GET', 'POST'])
def api_learn():
    """Record or retrieve learnings"""
    if request.method == 'GET':
        learnings = []
        if LEARNING_FILE.exists():
            with open(LEARNING_FILE, 'r') as f:
                learnings = json.load(f)
        
        return jsonify({
            'success': True,
            'learnings': learnings,
            'count': len(learnings)
        })
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        # Load existing learnings
        learnings = []
        if LEARNING_FILE.exists():
            with open(LEARNING_FILE, 'r') as f:
                learnings = json.load(f)
        
        # Add new learning
        learning = {
            'id': f"learn-{int(time.time())}",
            'name': data.get('name', 'unnamed'),
            'description': data.get('description', ''),
            'confidence': data.get('confidence', 0.5),
            'outcome': data.get('outcome', 'pending'),
            'timestamp': datetime.now().isoformat()
        }
        
        learnings.append(learning)
        
        # Keep last 500 learnings
        learnings = learnings[-500:]
        
        with open(LEARNING_FILE, 'w') as f:
            json.dump(learnings, f, indent=2)
        
        return jsonify({
            'success': True,
            'learning': learning
        })


# ============================================================
# DEPLOY ENDPOINT
# ============================================================

@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """Deploy code to the server"""
    data = request.get_json() or {}
    
    code = data.get('code', '')
    target_path = data.get('targetPath', '')
    execute = data.get('execute', False)
    
    if not code or not target_path:
        return jsonify({
            'success': False,
            'error': 'Missing code or targetPath'
        }), 400
    
    # Create full path
    deploy_dir = Path('/opt/kiswarm7/deployed')
    deploy_dir.mkdir(parents=True, exist_ok=True)
    
    full_path = deploy_dir / target_path.lstrip('/')
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Write code
        with open(full_path, 'w') as f:
            f.write(code)
        
        result = {
            'success': True,
            'deployed_to': str(full_path),
            'size': len(code)
        }
        
        # Execute if requested
        if execute:
            import subprocess
            exec_result = subprocess.run(
                ['python3', str(full_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            result['execution'] = {
                'returncode': exec_result.returncode,
                'stdout': exec_result.stdout[:500],
                'stderr': exec_result.stderr[:500]
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# SENSORY ENDPOINT
# ============================================================

@app.route('/api/sensory')
def api_sensory():
    """Get system sensory data"""
    try:
        import psutil
        
        return jsonify({
            'success': True,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())),
            'timestamp': datetime.now().isoformat()
        })
    except:
        return jsonify({
            'success': False,
            'error': 'psutil not available'
        })


# ============================================================
# AUTONOMOUS ENDPOINTS
# ============================================================

@app.route('/api/autonomous/start', methods=['POST'])
def api_autonomous_start():
    """Start autonomous mode"""
    if not load_modules():
        return jsonify({
            'success': False,
            'error': 'Modules not loaded'
        }), 500
    
    result = orchestrator.start_all()
    return jsonify({'success': True, **result})


@app.route('/api/autonomous/stop', methods=['POST'])
def api_autonomous_stop():
    """Stop autonomous mode"""
    if orchestrator:
        result = orchestrator.stop_all()
        return jsonify({'success': True, **result})
    
    return jsonify({'success': True, 'status': 'not_running'})


@app.route('/api/autonomous/status')
def api_autonomous_status():
    """Get autonomous status"""
    if orchestrator:
        return jsonify(orchestrator.get_status())
    
    return jsonify({
        'running': False,
        'modules_loaded': modules_loaded
    })


@app.route('/api/autonomous/action', methods=['POST'])
def api_autonomous_action():
    """Execute an autonomous action"""
    if not orchestrator:
        return jsonify({
            'success': False,
            'error': 'Orchestrator not initialized'
        }), 500
    
    data = request.get_json() or {}
    result = orchestrator.execute_action(data.get('action'), data.get('params'))
    
    return jsonify(result)


# ============================================================
# SCHEDULER ENDPOINTS
# ============================================================

@app.route('/api/scheduler/status')
def api_scheduler_status():
    """Get scheduler status"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m116_scheduler_integration import api_get_status
    return jsonify(api_get_status())


@app.route('/api/scheduler/task', methods=['POST'])
def api_scheduler_add_task():
    """Add a scheduled task"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m116_scheduler_integration import api_add_task
    data = request.get_json() or {}
    return jsonify(api_add_task(data))


# ============================================================
# GITHUB ENDPOINTS
# ============================================================

@app.route('/api/github/status')
def api_github_status():
    """Get GitHub repo status"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m117_auto_push import api_status
    return jsonify(api_status())


@app.route('/api/github/push', methods=['POST'])
def api_github_push():
    """Push to GitHub"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m117_auto_push import api_commit_push
    data = request.get_json() or {}
    return jsonify(api_commit_push(data))


# ============================================================
# SYNC ENDPOINTS
# ============================================================

@app.route('/api/sync/status')
def api_sync_status():
    """Get multi-model sync status"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m118_multi_model_sync import api_get_status
    return jsonify(api_get_status())


@app.route('/api/sync/memory', methods=['POST'])
def api_sync_memory():
    """Add shared memory"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m118_multi_model_sync import api_add_memory
    data = request.get_json() or {}
    return jsonify(api_add_memory(data))


# ============================================================
# NGROK ENDPOINTS
# ============================================================

@app.route('/api/ngrok/status')
def api_ngrok_status():
    """Get ngrok tunnel status"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m120_ngrok_monitor import api_get_status
    return jsonify(api_get_status())


@app.route('/api/ngrok/restart', methods=['POST'])
def api_ngrok_restart():
    """Restart ngrok tunnel"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m120_ngrok_monitor import api_force_restart
    return jsonify(api_force_restart())


# ============================================================
# SELF-MODIFICATION ENDPOINTS
# ============================================================

@app.route('/api/selfmod/status')
def api_selfmod_status():
    """Get self-modification status"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m119_self_modification import api_get_status
    return jsonify(api_get_status())


@app.route('/api/selfmod/read', methods=['POST'])
def api_selfmod_read():
    """Read a file"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m119_self_modification import api_read_file
    data = request.get_json() or {}
    return jsonify(api_read_file(data))


@app.route('/api/selfmod/edit', methods=['POST'])
def api_selfmod_edit():
    """Edit a file"""
    if not load_modules():
        return jsonify({'success': False, 'error': 'Modules not loaded'})
    
    from kiswarm7_modules.autonomous.m119_self_modification import api_edit_file
    data = request.get_json() or {}
    return jsonify(api_edit_file(data))


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    logger.info("🜂 Starting GLM Autonomous Bridge API...")
    logger.info(f"Port: {FLASK_PORT}")
    
    # Try to load modules
    load_modules()
    
    # Start Flask
    app.run(
        host='0.0.0.0',
        port=FLASK_PORT,
        debug=False,
        threaded=True
    )
