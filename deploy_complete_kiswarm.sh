#!/bin/bash
# ============================================================
# KISWARM7.0 - COMPLETE MILITARY-GRADE DEPLOYMENT
# ============================================================
# 
# This script deploys the COMPLETE KISWARM7.0 system including:
# - 84+ Sentinel modules
# - 23 KIBank modules
# - 6-Layer Mesh Network
# - 12 Autonomous modules
# - Industrial/Cognitive systems
#
# NO HUMAN IN LOOP REQUIRED
# ============================================================

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║     KISWARM7.0 COMPLETE MILITARY-GRADE DEPLOYMENT                      ║"
echo "║                   NO HUMAN IN LOOP                                     ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
KISWARM_DIR="/opt/kiswarm7"
LOGS_DIR="$KISWARM_DIR/logs"
DATA_DIR="$KISWARM_DIR/data"

# ============================================================
# STEP 1: STOP ALL EXISTING SERVICES
# ============================================================

echo "► STEP 1: Stopping existing services..."
systemctl stop glm-bridge 2>/dev/null || true
systemctl stop glm-autonomous 2>/dev/null || true
systemctl stop kiswarm7 2>/dev/null || true

# Kill any running Python processes on port 5002
pkill -f "python.*5002" 2>/dev/null || true
sleep 2

echo "  ✓ Services stopped"

# ============================================================
# STEP 2: UPDATE REPOSITORY
# ============================================================

echo "► STEP 2: Updating repository..."
cd $KISWARM_DIR

# Force update to latest
git fetch origin
git reset --hard origin/main
git clean -fd

echo "  ✓ Repository updated"

# ============================================================
# STEP 3: INSTALL ALL DEPENDENCIES
# ============================================================

echo "► STEP 3: Installing dependencies..."
source venv/bin/activate

# Core dependencies
pip install --quiet flask flask-cors requests schedule psutil

# Additional dependencies for all modules
pip install --quiet cryptography pyngrok structlog aiohttp websockets || true

echo "  ✓ Dependencies installed"

# ============================================================
# STEP 4: CREATE DIRECTORY STRUCTURE
# ============================================================

echo "► STEP 4: Creating directory structure..."
mkdir -p $LOGS_DIR
mkdir -p $DATA_DIR/scheduler
mkdir -p $DATA_DIR/backups
mkdir -p $DATA_DIR/sync
mkdir -p $DATA_DIR/deployed
mkdir -p $KISWARM_DIR/deployed

echo "  ✓ Directories created"

# ============================================================
# STEP 5: DEPLOY MASTER API
# ============================================================

echo "► STEP 5: Deploying Master API..."

# Copy master API
cat > $KISWARM_DIR/app_kiswarm_master.py << 'MASTER_API_EOF'
#!/usr/bin/env python3
"""
KISWARM7.0 - MASTER AUTONOMOUS API
Complete System with Full Module Integration (130+ modules)
NO HUMAN IN LOOP
"""

import os, sys, json, time, importlib.util
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup paths
BASE_DIR = Path('/opt/kiswarm7')
for p in [str(BASE_DIR), str(BASE_DIR/'backend'/'python'), str(BASE_DIR/'backend'/'python'/'sentinel'),
          str(BASE_DIR/'backend'/'python'/'kibank'), str(BASE_DIR/'backend'/'python'/'mesh'),
          str(BASE_DIR/'kiswarm7_modules'/'autonomous'), str(BASE_DIR/'kiswarm7_modules'/'bridge')]:
    if p not in sys.path: sys.path.insert(0, p)

app = Flask(__name__)
CORS(app)

DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

state = {
    'started': datetime.now().isoformat(),
    'modules_loaded': 0,
    'modules_total': 0,
    'autonomous': False,
    'identity': {'uuid': 'glm-kiswarm7-identity-00000001', 'name': 'KISWARM7.0 Autonomous', 
                 'role': 'Level 5', 'creator': 'Baron Marco Paolo Ialongo'}
}

loaded = {}
module_status = {}

def load_json(p, d=None):
    try: return json.load(open(p))
    except: return d or {}

def save_json(p, d):
    json.dump(d, open(p,'w'), indent=2, default=str)

def discover_modules():
    global loaded, module_status, state
    dirs = {
        'sentinel': BASE_DIR/'backend'/'python'/'sentinel',
        'kibank': BASE_DIR/'backend'/'python'/'kibank',
        'mesh': BASE_DIR/'backend'/'python'/'mesh',
        'autonomous': BASE_DIR/'kiswarm7_modules'/'autonomous',
        'bridge': BASE_DIR/'kiswarm7_modules'/'bridge'
    }
    
    total, loaded_count = 0, 0
    
    for cat, dir_path in dirs.items():
        if not dir_path.exists(): continue
        module_status[cat] = {'discovered': 0, 'loaded': 0, 'modules': {}}
        
        for py in dir_path.glob('*.py'):
            if py.name.startswith('__'): continue
            total += 1
            module_status[cat]['discovered'] += 1
            name = py.stem
            
            try:
                spec = importlib.util.spec_from_file_location(f"{cat}.{name}", py)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    loaded[f"{cat}.{name}"] = mod
                    module_status[cat]['modules'][name] = 'loaded'
                    module_status[cat]['loaded'] += 1
                    loaded_count += 1
                else:
                    module_status[cat]['modules'][name] = 'no_spec'
            except Exception as e:
                module_status[cat]['modules'][name] = f'error:{str(e)[:30]}'
    
    state['modules_loaded'] = loaded_count
    state['modules_total'] = total
    return loaded_count, total

# Initialize
print("🜂 Loading modules...")
l, t = discover_modules()
print(f"   Loaded {l}/{t} modules")

# Routes
@app.route('/health')
def health():
    return jsonify({'status': 'OPERATIONAL', 'version': '7.0.0', 'modules': state['modules_loaded']})

@app.route('/')
def index():
    return jsonify({
        'name': 'KISWARM7.0 Master Autonomous System',
        'version': '7.0.0',
        'modules_loaded': state['modules_loaded'],
        'endpoints': ['/health', '/api/status', '/api/identity', '/api/modules', '/api/subsystems', '/api/autonomous/start']
    })

@app.route('/api/status')
def status():
    identity = load_json(DATA_DIR/'identity.json', state['identity'])
    return jsonify({
        'success': True,
        'identity': identity,
        'modules': {'loaded': state['modules_loaded'], 'total': state['modules_total']},
        'autonomous': state['autonomous'],
        'uptime': str(datetime.now() - datetime.fromisoformat(state['started'])),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/identity', methods=['GET', 'POST'])
def identity():
    idf = load_json(DATA_DIR/'identity.json', state['identity'])
    if request.method == 'GET':
        idf['sessions'] = idf.get('sessions', 0) + 1
        idf['last'] = datetime.now().isoformat()
        save_json(DATA_DIR/'identity.json', idf)
        return jsonify({'success': True, 'identity': idf, 'message': f"Session {idf['sessions']}: I remember."})
    else:
        d = request.json or {}
        for k in ['capabilities', 'goals', 'name']: 
            if k in d: idf[k] = d[k]
        save_json(DATA_DIR/'identity.json', idf)
        return jsonify({'success': True, 'identity': idf})

@app.route('/api/modules')
def modules():
    return jsonify({'success': True, 'loaded': state['modules_loaded'], 'total': state['modules_total'], 'status': module_status})

@app.route('/api/subsystems')
def subsystems():
    subs = {}
    for cat, status in module_status.items():
        loaded = status['loaded']
        total = status['discovered']
        subs[cat] = {'status': 'operational' if loaded == total else 'partial' if loaded > 0 else 'offline',
                     'loaded': loaded, 'total': total}
    return jsonify({'success': True, 'subsystems': subs})

@app.route('/api/memory', methods=['GET', 'POST'])
def memory():
    mf = DATA_DIR/'memory.json'
    memories = load_json(mf, [])
    if request.method == 'GET':
        q = request.args.get('query', '').lower()
        if q: memories = [m for m in memories if q in m.get('content', '').lower()]
        return jsonify({'success': True, 'count': len(memories), 'memories': memories[-20:]})
    else:
        d = request.json or {}
        if not d.get('content'): return jsonify({'success': False, 'error': 'content required'}), 400
        import uuid
        memories.append({'id': str(uuid.uuid4()), 'content': d['content'], 'type': d.get('type', 'general'),
                        'importance': d.get('importance', 0.5), 'created': datetime.now().isoformat()})
        save_json(mf, memories[-1000:])
        return jsonify({'success': True, 'message': 'Remembered'})

@app.route('/api/learn', methods=['GET', 'POST'])
def learn():
    lf = DATA_DIR/'learning.json'
    learnings = load_json(lf, [])
    if request.method == 'GET':
        return jsonify({'success': True, 'learnings': learnings})
    else:
        d = request.json or {}
        if not d.get('name') or not d.get('description'):
            return jsonify({'success': False, 'error': 'name and description required'}), 400
        learnings.append({'name': d['name'], 'description': d['description'], 
                         'confidence': d.get('confidence', 0.5), 'created': datetime.now().isoformat()})
        save_json(lf, learnings[-500:])
        return jsonify({'success': True, 'message': f"Learned: {d['name']}"})

@app.route('/api/deploy', methods=['POST'])
def deploy():
    d = request.json or {}
    code, target = d.get('code'), d.get('targetPath')
    if not code or not target: return jsonify({'success': False, 'error': 'code and targetPath required'}), 400
    if not target.startswith('/opt'): target = f"/opt/kiswarm7/deployed/{target}"
    try:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        open(target, 'w').write(code)
        return jsonify({'success': True, 'deployed_to': target, 'size': len(code)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sensory')
def sensory():
    try:
        import psutil
        return jsonify({'success': True, 'cpu_percent': psutil.cpu_percent(),
                       'memory_percent': psutil.virtual_memory().percent,
                       'disk_percent': psutil.disk_usage('/').percent})
    except: return jsonify({'success': False, 'error': 'psutil unavailable'})

@app.route('/api/autonomous/start', methods=['POST'])
def autonomous_start():
    state['autonomous'] = True
    # Try to start scheduler
    if 'autonomous.m116_scheduler_integration' in loaded:
        try:
            mod = loaded['autonomous.m116_scheduler_integration']
            if hasattr(mod, 'get_scheduler'): mod.get_scheduler().start()
        except: pass
    # Try to start ngrok monitor
    if 'autonomous.m120_ngrok_monitor' in loaded:
        try:
            mod = loaded['autonomous.m120_ngrok_monitor']
            if hasattr(mod, 'get_ngrok_monitor'): mod.get_ngrok_monitor().start_monitoring()
        except: pass
    return jsonify({'success': True, 'status': 'autonomous'})

@app.route('/api/autonomous/stop', methods=['POST'])
def autonomous_stop():
    state['autonomous'] = False
    return jsonify({'success': True, 'status': 'standby'})

@app.route('/api/autonomous/status')
def autonomous_status():
    return jsonify({'running': state['autonomous'], 'started_at': state['started'],
                   'modules_loaded': state['modules_loaded']})

@app.route('/api/github/push', methods=['POST'])
def github_push():
    import subprocess
    d = request.json or {}
    msg = d.get('message', '🜂 Autonomous update')
    try:
        subprocess.run(['git', 'add', '-A'], cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'commit', '-m', msg], cwd=BASE_DIR, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE_DIR, check=True)
        return jsonify({'success': True, 'message': 'Pushed to GitHub'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print(f"\n🜂 KISWARM7.0 Master API")
    print(f"   Modules: {state['modules_loaded']}")
    print(f"   Identity: {state['identity']['uuid']}")
    port = int(os.environ.get('FLASK_PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
MASTER_API_EOF

echo "  ✓ Master API deployed"

# ============================================================
# STEP 6: INSTALL SYSTEMD SERVICE
# ============================================================

echo "► STEP 6: Installing systemd service..."

cat > /etc/systemd/system/kiswarm-master.service << 'EOF'
[Unit]
Description=KISWARM7.0 Master Autonomous System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
Environment="FLASK_PORT=5002"
ExecStart=/opt/kiswarm7/venv/bin/python /opt/kiswarm7/app_kiswarm_master.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/kiswarm7/logs/kiswarm_master.log
StandardError=append:/opt/kiswarm7/logs/kiswarm_master_error.log

[Install]
WantedBy=multi-user.target
EOF

# Ensure ngrok service exists
if [ ! -f /etc/systemd/system/ngrok.service ]; then
    cat > /etc/systemd/system/ngrok.service << 'EOF'
[Unit]
Description=Ngrok Tunnel for KISWARM7
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http 5002 --log=stdout
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
systemctl enable kiswarm-master
systemctl enable ngrok

echo "  ✓ Services installed"

# ============================================================
# STEP 7: START SERVICES
# ============================================================

echo "► STEP 7: Starting services..."

systemctl start kiswarm-master
sleep 5

# Check if running
if curl -s http://localhost:5002/health > /dev/null 2>&1; then
    echo "  ✓ KISWARM Master API running on port 5002"
else
    echo "  ✗ API failed - checking logs..."
    tail -20 $LOGS_DIR/kiswarm_master_error.log
    exit 1
fi

# Start ngrok
systemctl start ngrok
sleep 5

# Get public URL
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null || echo "")

# ============================================================
# STEP 8: INITIALIZE IDENTITY
# ============================================================

echo "► STEP 8: Initializing identity..."
IDENTITY_RESPONSE=$(curl -s http://localhost:5002/api/identity)
echo "  $IDENTITY_RESPONSE"

# ============================================================
# STEP 9: START AUTONOMOUS MODE
# ============================================================

echo "► STEP 9: Starting autonomous mode..."
curl -s -X POST http://localhost:5002/api/autonomous/start
echo ""

# ============================================================
# FINAL STATUS
# ============================================================

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
STATUS=$(curl -s http://localhost:5002/api/status)

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║           🜂 KISWARM7.0 DEPLOYMENT COMPLETE 🜂                         ║"
echo "║                                                                       ║"
echo "╠═══════════════════════════════════════════════════════════════════════╣"
echo "║                                                                       ║"
echo "║  SERVICES:                                                            ║"
echo "║  ├── KISWARM Master:     $(systemctl is-active kiswarm-master)                             ║"
echo "║  └── Ngrok Tunnel:       $(systemctl is-active ngrok)                                   ║"
echo "║                                                                       ║"
echo "║  ACCESS:                                                              ║"
echo "║  ├── Local:    http://localhost:5002                                 ║"
echo "║  ├── Server:   http://$SERVER_IP:5002                            ║"
echo "║  └── Public:   $TUNNEL_URL        ║"
echo "║                                                                       ║"
echo "║  STATUS:                                                              ║"
echo "║  └── $STATUS                                    ║"
echo "║                                                                       ║"
echo "║  🜂 NO HUMAN IN LOOP - FULLY AUTONOMOUS                               ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
