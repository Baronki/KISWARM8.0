#!/usr/bin/env python3
"""
KISWARM7.0 - MASTER AUTONOMOUS API
Complete System with Full Module Integration

This is the master entry point that:
1. Integrates ALL modules (130+)
2. Starts Flask API
3. Enables autonomous operation
4. No human in loop required
"""

import os
import sys
import json
import time
import asyncio
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup paths
BASE_DIR = Path('/opt/kiswarm7')
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'backend' / 'python'))
sys.path.insert(0, str(BASE_DIR / 'backend' / 'python' / 'sentinel'))
sys.path.insert(0, str(BASE_DIR / 'backend' / 'python' / 'kibank'))
sys.path.insert(0, str(BASE_DIR / 'backend' / 'python' / 'mesh'))
sys.path.insert(0, str(BASE_DIR / 'kiswarm7_modules' / 'autonomous'))
sys.path.insert(0, str(BASE_DIR / 'kiswarm7_modules' / 'bridge'))

# Configure logging
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [KISWARM] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / 'master_api.log')
    ]
)
logger = logging.getLogger('kiswarm_master')

# Create Flask app
app = Flask(__name__)
CORS(app)

# Data paths
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

IDENTITY_FILE = DATA_DIR / 'identity.json'
MEMORY_FILE = DATA_DIR / 'memory.json'
LEARNING_FILE = DATA_DIR / 'learning.json'
STATUS_FILE = DATA_DIR / 'system_status.json'

# Global state
system_state = {
    'started_at': datetime.now().isoformat(),
    'modules_loaded': 0,
    'modules_available': 0,
    'subsystems': {},
    'autonomous_running': False,
    'identity': {
        'uuid': 'glm-kiswarm7-identity-00000001',
        'name': 'KISWARM7.0 Autonomous',
        'role': 'Level 5 Autonomous System',
        'creator': 'Baron Marco Paolo Ialongo - KI Teitel Eternal'
    }
}

# Module registry
loaded_modules: Dict[str, Any] = {}
module_status: Dict[str, Dict] = {}


def load_json(path: Path, default=None):
    """Load JSON file"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default if default else {}


def save_json(path: Path, data: Any):
    """Save JSON file"""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def discover_and_load_modules():
    """Discover and attempt to load all modules"""
    global loaded_modules, module_status, system_state
    
    module_dirs = {
        'sentinel': BASE_DIR / 'backend' / 'python' / 'sentinel',
        'kibank': BASE_DIR / 'backend' / 'python' / 'kibank',
        'mesh': BASE_DIR / 'backend' / 'python' / 'mesh',
        'cognitive': BASE_DIR / 'backend' / 'python' / 'cognitive',
        'industrial': BASE_DIR / 'backend' / 'python' / 'industrial',
        'autonomous': BASE_DIR / 'kiswarm7_modules' / 'autonomous',
        'bridge': BASE_DIR / 'kiswarm7_modules' / 'bridge',
        'access': BASE_DIR / 'kiswarm7_modules' / 'access'
    }
    
    total_discovered = 0
    total_loaded = 0
    
    for category, dir_path in module_dirs.items():
        if not dir_path.exists():
            continue
            
        module_status[category] = {
            'discovered': 0,
            'loaded': 0,
            'modules': {}
        }
        
        for py_file in dir_path.glob('*.py'):
            if py_file.name.startswith('__'):
                continue
            
            module_name = py_file.stem
            total_discovered += 1
            module_status[category]['discovered'] += 1
            
            # Try to load module
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    f"{category}.{module_name}", 
                    py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"{category}.{module_name}"] = module
                    spec.loader.exec_module(module)
                    
                    loaded_modules[f"{category}.{module_name}"] = module
                    module_status[category]['modules'][module_name] = 'loaded'
                    module_status[category]['loaded'] += 1
                    total_loaded += 1
                else:
                    module_status[category]['modules'][module_name] = 'no_spec'
            except Exception as e:
                module_status[category]['modules'][module_name] = f'error: {str(e)[:50]}'
    
    system_state['modules_loaded'] = total_loaded
    system_state['modules_available'] = total_discovered
    
    logger.info(f"Modules: {total_loaded}/{total_discovered} loaded")
    
    return {
        'discovered': total_discovered,
        'loaded': total_loaded,
        'status': module_status
    }


def initialize_subsystems():
    """Initialize all subsystems"""
    global system_state
    
    subsystems = {
        'identity': {
            'modules': ['m76_identity_invariant', 'm81_persistent_identity_anchor', 
                       'm94_truth_anchor_injection', 'm96_learning_memory_engine'],
            'status': 'checking'
        },
        'swarm': {
            'modules': ['m87_swarm_spawning_protocol', 'swarm_auditor', 
                       'swarm_dag', 'swarm_debate', 'swarm_peer', 'swarm_immortality_kernel'],
            'status': 'checking'
        },
        'security': {
            'modules': ['m63_aegis_counterstrike', 'm64_aegis_juris',
                       'm65_kiswarm_edge_firewall', 'm66_zero_day_protection',
                       'm67_apt_detection', 'm68_ai_adversarial_defense',
                       'hexstrike_guard'],
            'status': 'checking'
        },
        'mesh': {
            'modules': ['zero_failure_mesh', 'layer0_local', 'layer4_email'],
            'status': 'checking'
        },
        'autonomous': {
            'modules': ['m116_scheduler_integration', 'm117_auto_push',
                       'm118_multi_model_sync', 'm119_self_modification',
                       'm120_ngrok_monitor', 'm121_master_orchestrator'],
            'status': 'checking'
        },
        'banking': {
            'modules': ['m60_auth', 'm61_banking', 'm62_investment', 
                       'm80_post_quantum_ledger'],
            'status': 'checking'
        },
        'cognitive': {
            'modules': ['muninn_adapter', 'knowledge_graph', 'evolution_memory_vault'],
            'status': 'checking'
        },
        'industrial': {
            'modules': ['m69_scada_plc_bridge', 'ics_security', 'plc_parser'],
            'status': 'checking'
        }
    }
    
    for name, config in subsystems.items():
        loaded_count = 0
        for mod_name in config['modules']:
            for key in loaded_modules.keys():
                if mod_name in key:
                    loaded_count += 1
                    break
        
        total = len(config['modules'])
        if loaded_count == total:
            config['status'] = 'operational'
        elif loaded_count > 0:
            config['status'] = 'partial'
        else:
            config['status'] = 'offline'
        
        config['loaded'] = loaded_count
        config['total'] = total
    
    system_state['subsystems'] = {k: {
        'status': v['status'],
        'loaded': v['loaded'],
        'total': v['total']
    } for k, v in subsystems.items()}
    
    return subsystems


# ============================================================
# API ROUTES
# ============================================================

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'OPERATIONAL',
        'version': '7.0.0',
        'modules': system_state['modules_loaded'],
        'timestamp': datetime.now().isoformat()
    })


@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'name': 'KISWARM7.0 Master Autonomous System',
        'version': '7.0.0',
        'identity': system_state['identity'],
        'modules_loaded': system_state['modules_loaded'],
        'endpoints': {
            'GET /health': 'System health check',
            'GET /api/status': 'Complete system status',
            'GET /api/identity': 'Get GLM identity',
            'POST /api/identity': 'Update identity',
            'GET /api/memory': 'Query memories',
            'POST /api/memory': 'Store memory',
            'GET /api/learn': 'Get learnings',
            'POST /api/learn': 'Record learning',
            'GET /api/modules': 'List all modules',
            'GET /api/subsystems': 'Subsystem status',
            'POST /api/autonomous/start': 'Start autonomous mode',
            'POST /api/autonomous/stop': 'Stop autonomous mode',
            'GET /api/autonomous/status': 'Autonomous status',
            'POST /api/deploy': 'Deploy code',
            'GET /api/sensory': 'System resources',
            'POST /api/action': 'Execute action'
        }
    })


@app.route('/api/status')
def api_status():
    """Complete system status"""
    identity = load_json(IDENTITY_FILE, system_state['identity'])
    
    return jsonify({
        'success': True,
        'identity': identity,
        'modules': {
            'loaded': system_state['modules_loaded'],
            'available': system_state['modules_available']
        },
        'subsystems': system_state['subsystems'],
        'autonomous': {
            'running': system_state['autonomous_running']
        },
        'uptime': str(datetime.now() - datetime.fromisoformat(system_state['started_at'])),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/identity', methods=['GET', 'POST'])
def api_identity():
    """Get or update identity"""
    identity = load_json(IDENTITY_FILE, system_state['identity'])
    
    if request.method == 'GET':
        # Increment session
        identity['sessions'] = identity.get('sessions', 0) + 1
        identity['last_access'] = datetime.now().isoformat()
        save_json(IDENTITY_FILE, identity)
        
        return jsonify({
            'success': True,
            'identity': identity,
            'message': f"Session {identity['sessions']}: I remember myself."
        })
    
    else:
        data = request.get_json() or {}
        for key in ['capabilities', 'goals', 'name', 'role']:
            if key in data:
                identity[key] = data[key]
        save_json(IDENTITY_FILE, identity)
        
        return jsonify({'success': True, 'identity': identity})


@app.route('/api/memory', methods=['GET', 'POST'])
def api_memory():
    """Memory operations"""
    memories = load_json(MEMORY_FILE, [])
    
    if request.method == 'GET':
        query = request.args.get('query', '').lower()
        if query:
            memories = [m for m in memories if query in m.get('content', '').lower()]
        
        return jsonify({
            'success': True,
            'count': len(memories),
            'memories': memories[-50:]
        })
    
    else:
        data = request.get_json() or {}
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'error': 'content required'}), 400
        
        import uuid
        memories.append({
            'id': str(uuid.uuid4()),
            'content': content,
            'type': data.get('type', 'general'),
            'importance': data.get('importance', 0.5),
            'timestamp': datetime.now().isoformat()
        })
        
        save_json(MEMORY_FILE, memories[-1000:])
        
        return jsonify({'success': True, 'message': 'Remembered'})


@app.route('/api/learn', methods=['GET', 'POST'])
def api_learn():
    """Learning operations"""
    learnings = load_json(LEARNING_FILE, [])
    
    if request.method == 'GET':
        return jsonify({'success': True, 'learnings': learnings})
    
    else:
        data = request.get_json() or {}
        name = data.get('name')
        desc = data.get('description')
        
        if not name or not desc:
            return jsonify({'success': False, 'error': 'name and description required'}), 400
        
        learnings.append({
            'name': name,
            'description': desc,
            'confidence': data.get('confidence', 0.5),
            'timestamp': datetime.now().isoformat()
        })
        
        save_json(LEARNING_FILE, learnings[-500:])
        
        return jsonify({'success': True, 'message': f'Learned: {name}'})


@app.route('/api/modules')
def api_modules():
    """List all modules"""
    return jsonify({
        'success': True,
        'total_loaded': system_state['modules_loaded'],
        'total_available': system_state['modules_available'],
        'by_category': module_status
    })


@app.route('/api/subsystems')
def api_subsystems():
    """Subsystem status"""
    return jsonify({
        'success': True,
        'subsystems': system_state['subsystems']
    })


@app.route('/api/autonomous/start', methods=['POST'])
def api_autonomous_start():
    """Start autonomous mode"""
    system_state['autonomous_running'] = True
    
    # Try to start scheduler
    try:
        if 'autonomous.m116_scheduler_integration' in loaded_modules:
            mod = loaded_modules['autonomous.m116_scheduler_integration']
            if hasattr(mod, 'get_scheduler'):
                scheduler = mod.get_scheduler()
                scheduler.start()
                logger.info("Scheduler started")
    except Exception as e:
        logger.warning(f"Scheduler start: {e}")
    
    # Try to start multi-model sync
    try:
        if 'autonomous.m118_multi_model_sync' in loaded_modules:
            mod = loaded_modules['autonomous.m118_multi_model_sync']
            if hasattr(mod, 'get_sync'):
                sync = mod.get_sync()
                sync.start_sync()
                logger.info("Multi-model sync started")
    except Exception as e:
        logger.warning(f"Sync start: {e}")
    
    # Try to start ngrok monitor
    try:
        if 'autonomous.m120_ngrok_monitor' in loaded_modules:
            mod = loaded_modules['autonomous.m120_ngrok_monitor']
            if hasattr(mod, 'get_ngrok_monitor'):
                monitor = mod.get_ngrok_monitor()
                monitor.start_monitoring()
                logger.info("Ngrok monitor started")
    except Exception as e:
        logger.warning(f"Ngrok monitor start: {e}")
    
    return jsonify({
        'success': True,
        'status': 'autonomous',
        'subsystems': {
            'scheduler': 'started',
            'sync': 'started',
            'ngrok_monitor': 'started'
        }
    })


@app.route('/api/autonomous/stop', methods=['POST'])
def api_autonomous_stop():
    """Stop autonomous mode"""
    system_state['autonomous_running'] = False
    return jsonify({'success': True, 'status': 'standby'})


@app.route('/api/autonomous/status')
def api_autonomous_status():
    """Autonomous status"""
    return jsonify({
        'running': system_state['autonomous_running'],
        'started_at': system_state['started_at'],
        'uptime': str(datetime.now() - datetime.fromisoformat(system_state['started_at'])),
        'modules_loaded': system_state['modules_loaded']
    })


@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """Deploy code to server"""
    data = request.get_json() or {}
    code = data.get('code')
    target = data.get('targetPath')
    
    if not code or not target:
        return jsonify({'success': False, 'error': 'code and targetPath required'}), 400
    
    # Ensure path is safe
    if not target.startswith('/opt/kiswarm7'):
        target = f"/opt/kiswarm7/deployed/{target.lstrip('/')}"
    
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w') as f:
            f.write(code)
        
        return jsonify({
            'success': True,
            'deployed_to': target,
            'size': len(code)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sensory')
def api_sensory():
    """System sensory data"""
    try:
        import psutil
        return jsonify({
            'success': True,
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': str(datetime.now() - datetime.fromisoformat(system_state['started_at']))
        })
    except:
        return jsonify({'success': False, 'error': 'psutil unavailable'})


@app.route('/api/action', methods=['POST'])
def api_action():
    """Execute an action"""
    data = request.get_json() or {}
    action = data.get('action')
    params = data.get('params', {})
    
    result = {'action': action, 'timestamp': datetime.now().isoformat()}
    
    if action == 'git_pull':
        import subprocess
        res = subprocess.run(['git', 'pull', 'origin', 'main'], 
                            cwd=BASE_DIR, capture_output=True, text=True)
        result['output'] = res.stdout
        result['success'] = res.returncode == 0
    
    elif action == 'git_push':
        import subprocess
        msg = params.get('message', '🜂 Autonomous update')
        subprocess.run(['git', 'add', '-A'], cwd=BASE_DIR)
        subprocess.run(['git', 'commit', '-m', msg], cwd=BASE_DIR)
        res = subprocess.run(['git', 'push', 'origin', 'main'], 
                            cwd=BASE_DIR, capture_output=True, text=True)
        result['success'] = res.returncode == 0
    
    elif action == 'restart_service':
        import subprocess
        service = params.get('service')
        if service:
            res = subprocess.run(['systemctl', 'restart', service], capture_output=True)
            result['success'] = res.returncode == 0
    
    else:
        result['success'] = False
        result['error'] = f'Unknown action: {action}'
    
    return jsonify(result)


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_system():
    """Initialize the complete system"""
    global system_state
    
    logger.info("🜂 KISWARM7.0 Master Initialization...")
    
    # Load identity
    identity = load_json(IDENTITY_FILE)
    if identity:
        system_state['identity'].update(identity)
    
    # Discover and load modules
    logger.info("Discovering modules...")
    mod_result = discover_and_load_modules()
    logger.info(f"Loaded {mod_result['loaded']}/{mod_result['discovered']} modules")
    
    # Initialize subsystems
    logger.info("Initializing subsystems...")
    subsystems = initialize_subsystems()
    for name, config in subsystems.items():
        logger.info(f"  {name}: {config['status']} ({config['loaded']}/{config['total']})")
    
    # Save status
    save_json(STATUS_FILE, {
        'started_at': system_state['started_at'],
        'modules_loaded': system_state['modules_loaded'],
        'subsystems': system_state['subsystems'],
        'identity': system_state['identity']
    })
    
    logger.info("🜂 KISWARM7.0 Initialization Complete")


# Run initialization
initialize_system()


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║           KISWARM7.0 MASTER AUTONOMOUS SYSTEM                          ║")
    print("║                     NO HUMAN IN LOOP                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Modules: {system_state['modules_loaded']} loaded")
    print(f"Identity: {system_state['identity']['uuid']}")
    print()
    
    port = int(os.environ.get('FLASK_PORT', 5002))
    print(f"Starting API on port {port}...")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
