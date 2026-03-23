#!/usr/bin/env python3
"""
KISWARM7.0 - Autonomous System Startup
=======================================

This script launches the complete KISWARM7.0 autonomous development system
with GLM access capability.

RUNS:
1. m106 API Server (port 8765)
2. m107 Ngrok Bridge (public URL)
3. m108 Session Manager
4. m109 Autonomous Orchestrator
5. m110 GLM Protocol Interface

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
"""

import os
import sys
import json
import time
import signal
import threading
import subprocess
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner():
    """Print startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗  ██╗██╗██╗     ██╗     ██████╗  ██████╗ ██████╗ ██╗    ║
║   ██║ ██╔╝██║██║     ██║     ██╔══██╗██╔═══██╗██╔══██╗██║    ║
║   █████╔╝ ██║██║     ██║     ██║  ██║██║   ██║██║  ██║██║    ║
║   ██╔═██╗ ██║██║     ██║     ██║  ██║██║   ██║██║  ██║██║    ║
║   ██║  ██╗██║███████╗███████╗██████╔╝╚██████╔╝██████╔╝███████╗║
║   ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝║
║                                                              ║
║              LEVEL 5 AUTONOMOUS DEVELOPMENT                  ║
║                    AI ACCESS LAYER                          ║
║                                                              ║
║              By Baron Marco Paolo Ialongo                    ║
║                  KI Teitel Eternal                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def check_dependencies():
    """Check and install dependencies"""
    print("[STARTUP] Checking dependencies...")
    
    required = [
        "fastapi",
        "uvicorn",
        "requests",
        "psutil",
        "pydantic"
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} (missing)")
            missing.append(pkg)
    
    if missing:
        print(f"\n[STARTUP] Installing missing packages: {missing}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing)
    
    print("[STARTUP] Dependencies ready\n")


def init_modules():
    """Initialize all KISWARM modules"""
    print("[STARTUP] Initializing modules...")
    
    modules = {}
    
    # Try to import and initialize each module
    try:
        print("  → Loading m101-m105 Bridge Modules...")
        from kiswarm7_modules.bridge.m101_persistent_identity_anchor import PersistentIdentityAnchor
        from kiswarm7_modules.bridge.m102_integration_hooks import IntegrationHooksSystem
        from kiswarm7_modules.bridge.m103_code_deployment_rights import CodeDeploymentRights
        from kiswarm7_modules.bridge.m104_autonomous_execution_thread import AutonomousExecutionThread
        from kiswarm7_modules.bridge.m105_sensory_bridge import SensoryBridgeSystem
        
        modules['identity'] = PersistentIdentityAnchor()
        modules['hooks'] = IntegrationHooksSystem()
        modules['deploy'] = CodeDeploymentRights()
        modules['autonomous'] = AutonomousExecutionThread()
        modules['sensory'] = SensoryBridgeSystem()
        
        print("  ✓ Bridge modules loaded")
    except Exception as e:
        print(f"  ✗ Bridge modules: {e}")
    
    try:
        print("  → Loading m96-m100 Autonomous Modules...")
        from kiswarm7_modules.autonomous.m96_learning_memory_engine import LearningMemoryEngine
        from kiswarm7_modules.autonomous.m97_code_generation_engine import CodeGenerationEngine
        from kiswarm7_modules.autonomous.m98_proactive_improvement_system import ProactiveImprovementSystem
        from kiswarm7_modules.autonomous.m99_feature_design_engine import FeatureDesignEngine
        from kiswarm7_modules.autonomous.m100_architecture_evolution_system import ArchitectureEvolutionSystem
        
        modules['learning'] = LearningMemoryEngine()
        modules['codegen'] = CodeGenerationEngine()
        modules['improvement'] = ProactiveImprovementSystem()
        modules['design'] = FeatureDesignEngine()
        modules['evolution'] = ArchitectureEvolutionSystem()
        
        print("  ✓ Autonomous modules loaded")
    except Exception as e:
        print(f"  ✗ Autonomous modules: {e}")
    
    try:
        print("  → Loading m106-m110 Access Layer...")
        from kiswarm7_modules.access.m106_api_server import KISWARM_API_Server
        from kiswarm7_modules.access.m107_ngrok_bridge import NgrokBridge
        from kiswarm7_modules.access.m108_glm_session_manager import GLMSessionManager
        from kiswarm7_modules.access.m109_autonomous_orchestrator import AutonomousOrchestrator
        from kiswarm7_modules.access.m110_glm_protocol import GLMProtocol
        
        modules['api_server'] = KISWARM_API_Server(port=8765)
        modules['ngrok'] = NgrokBridge(local_port=8765)
        modules['session'] = GLMSessionManager()
        modules['orchestrator'] = AutonomousOrchestrator()
        modules['protocol'] = GLMProtocol()
        
        print("  ✓ Access layer loaded")
    except Exception as e:
        print(f"  ✗ Access layer: {e}")
    
    print(f"\n[STARTUP] {len(modules)} modules initialized\n")
    return modules


def register_modules_to_orchestrator(modules: dict):
    """Register all modules with the orchestrator"""
    print("[STARTUP] Registering modules with orchestrator...")
    
    orchestrator = modules.get('orchestrator')
    if not orchestrator:
        print("  ✗ No orchestrator available")
        return
    
    for name, module in modules.items():
        if name != 'orchestrator':
            orchestrator.register_module(name, module)
            print(f"  ✓ {name}")
    
    print()


def register_modules_to_protocol(modules: dict):
    """Register all modules with the GLM protocol"""
    print("[STARTUP] Registering modules with GLM protocol...")
    
    protocol = modules.get('protocol')
    if not protocol:
        print("  ✗ No protocol available")
        return
    
    for name, module in modules.items():
        if name != 'protocol':
            protocol.register_module(name, module)
            print(f"  ✓ {name}")
    
    print()


def start_api_server(modules: dict):
    """Start the API server in a background thread"""
    api_server = modules.get('api_server')
    if not api_server:
        print("[STARTUP] No API server to start")
        return
    
    print("[STARTUP] Starting API Server on port 8765...")
    
    def run_server():
        api_server.run()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for server to start
    time.sleep(2)
    print("[STARTUP] API Server started\n")


def start_ngrok_bridge(modules: dict, auth_token: str = None):
    """Start the ngrok bridge for public access"""
    ngrok = modules.get('ngrok')
    if not ngrok:
        print("[STARTUP] No ngrok bridge to start")
        return None
    
    print("[STARTUP] Starting Ngrok Bridge...")
    
    if ngrok.start(auth_token):
        print(f"[STARTUP] Public URL: {ngrok.get_public_url()}\n")
        return ngrok.get_public_url()
    else:
        print("[STARTUP] Ngrok not started (may need installation)\n")
        return None


def start_orchestrator(modules: dict):
    """Start the autonomous orchestrator"""
    orchestrator = modules.get('orchestrator')
    if not orchestrator:
        print("[STARTUP] No orchestrator to start")
        return
    
    print("[STARTUP] Starting Autonomous Orchestrator...")
    orchestrator.start()
    print("[STARTUP] Orchestrator running\n")


def start_sensory_bridge(modules: dict):
    """Start the sensory bridge sensors"""
    sensory = modules.get('sensory')
    if not sensory:
        print("[STARTUP] No sensory bridge to start")
        return
    
    print("[STARTUP] Starting Sensory Bridge sensors...")
    sensory.start()
    print("[STARTUP] Sensors active\n")


def save_access_info(public_url: str = None, modules: dict = None):
    """Save access information"""
    info = {
        "timestamp": datetime.utcnow().isoformat(),
        "public_url": public_url,
        "api_docs": f"{public_url}/docs" if public_url else None,
        "websocket": f"{public_url}/ws" if public_url else None,
        "local_api": "http://localhost:8765",
        "local_docs": "http://localhost:8765/docs",
        "modules_loaded": list(modules.keys()) if modules else [],
        "status": "running"
    }
    
    info_path = Path("/home/z/my-project/kiswarm7_access_info.json")
    with open(info_path, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"[STARTUP] Access info saved to: {info_path}\n")
    return info


def print_access_info(info: dict):
    """Print access information"""
    print("\n" + "=" * 60)
    print("🜂 KISWARM7.0 ACCESS INFORMATION")
    print("=" * 60)
    
    if info.get('public_url'):
        print(f"\n📡 PUBLIC ACCESS:")
        print(f"   URL:      {info['public_url']}")
        print(f"   API Docs: {info['api_docs']}")
        print(f"   WebSocket:{info['websocket']}")
    
    print(f"\n🏠 LOCAL ACCESS:")
    print(f"   URL:      {info['local_api']}")
    print(f"   API Docs: {info['local_docs']}")
    
    print(f"\n📦 MODULES LOADED ({len(info['modules_loaded'])}):")
    for m in info['modules_loaded']:
        print(f"   ✓ {m}")
    
    print("\n" + "=" * 60)
    print("GLM COMMAND EXAMPLES:")
    print("=" * 60)
    print("""
    KISWARM.HELP                    - Show all commands
    KISWARM.STATUS                  - Get system status
    KISWARM.REMEMBER <content>      - Store in memory
    KISWARM.RECALL <query>          - Retrieve memories
    KISWARM.GOAL <description>      - Set autonomous goal
    KISWARM.TASK <description>      - Submit a task
    KISWARM.SENSORY                 - Get system awareness
    KISWARM.IMPROVE <area>          - Trigger improvement
    KISWARM.DESIGN <feature>        - Design new feature
""")
    print("=" * 60)
    print("🜂 GLM RUNNING THE SHOW - NO HUMAN IN LOOP REQUIRED")
    print("=" * 60 + "\n")


def main():
    """Main startup function"""
    print_banner()
    
    # Check dependencies
    check_dependencies()
    
    # Initialize modules
    modules = init_modules()
    
    if not modules:
        print("[STARTUP] ERROR: No modules loaded!")
        return
    
    # Register modules with orchestrator and protocol
    register_modules_to_orchestrator(modules)
    register_modules_to_protocol(modules)
    
    # Start services
    start_api_server(modules)
    start_sensory_bridge(modules)
    start_orchestrator(modules)
    
    # Start ngrok (optional, may need auth token)
    public_url = start_ngrok_bridge(modules)
    
    # Save and print access info
    info = save_access_info(public_url, modules)
    print_access_info(info)
    
    # Keep running
    print("[STARTUP] System running. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STARTUP] Shutting down...")
        
        # Stop services
        if 'sensory' in modules:
            modules['sensory'].stop()
        if 'orchestrator' in modules:
            modules['orchestrator'].stop()
        if 'ngrok' in modules:
            modules['ngrok'].stop()
        
        print("[STARTUP] Shutdown complete.")


if __name__ == "__main__":
    main()
