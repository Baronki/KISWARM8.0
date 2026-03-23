#!/usr/bin/env python3
"""
KISWARM7.0 - m121: Master Orchestrator
Coordinates all autonomous functions for GLM

This is the central nervous system that:
- Starts all autonomous modules
- Coordinates their interactions
- Provides unified API
- Manages system lifecycle
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from dataclasses import dataclass

# Import all modules
from .m116_scheduler_integration import get_scheduler, api_start as scheduler_start
from .m117_auto_push import get_autopush
from .m118_multi_model_sync import get_sync
from .m119_self_modification import get_selfmod
from .m120_ngrok_monitor import get_ngrok_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m121] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m121_orchestrator')

# Configuration
DATA_DIR = Path('/opt/kiswarm7/data')
ORCHESTRATOR_FILE = DATA_DIR / 'orchestrator_state.json'


@dataclass
class SystemState:
    """Overall system state"""
    started_at: str
    uptime_seconds: float
    modules_active: Dict[str, bool]
    total_autonomous_actions: int
    last_action: Optional[str]


class MasterOrchestrator:
    """
    Master Orchestrator for GLM Autonomous System
    
    Coordinates all modules and provides unified control
    """
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.start_time: Optional[float] = None
        self.state = SystemState(
            started_at='',
            uptime_seconds=0,
            modules_active={},
            total_autonomous_actions=0,
            last_action=None
        )
        
        # Module references
        self.scheduler = None
        self.autopush = None
        self.sync = None
        self.selfmod = None
        self.ngrok = None
        
        self._load_state()
    
    def _load_state(self):
        """Load saved state"""
        if ORCHESTRATOR_FILE.exists():
            try:
                with open(ORCHESTRATOR_FILE, 'r') as f:
                    data = json.load(f)
                    self.state = SystemState(**data)
            except:
                pass
    
    def _save_state(self):
        """Save state"""
        with open(ORCHESTRATOR_FILE, 'w') as f:
            json.dump(self.state.__dict__, f, indent=2)
    
    def initialize_modules(self):
        """Initialize all autonomous modules"""
        logger.info("Initializing autonomous modules...")
        
        try:
            # Initialize scheduler
            self.scheduler = get_scheduler()
            self.state.modules_active['scheduler'] = True
            logger.info("✓ Scheduler initialized")
        except Exception as e:
            logger.error(f"✗ Scheduler failed: {e}")
            self.state.modules_active['scheduler'] = False
        
        try:
            # Initialize autopush
            self.autopush = get_autopush()
            self.state.modules_active['autopush'] = True
            logger.info("✓ Auto-push initialized")
        except Exception as e:
            logger.error(f"✗ Auto-push failed: {e}")
            self.state.modules_active['autopush'] = False
        
        try:
            # Initialize multi-model sync
            self.sync = get_sync()
            self.state.modules_active['sync'] = True
            logger.info("✓ Multi-model sync initialized")
        except Exception as e:
            logger.error(f"✗ Multi-model sync failed: {e}")
            self.state.modules_active['sync'] = False
        
        try:
            # Initialize self-modification
            self.selfmod = get_selfmod()
            self.state.modules_active['selfmod'] = True
            logger.info("✓ Self-modification initialized")
        except Exception as e:
            logger.error(f"✗ Self-modification failed: {e}")
            self.state.modules_active['selfmod'] = False
        
        try:
            # Initialize ngrok monitor
            self.ngrok = get_ngrok_monitor()
            self.state.modules_active['ngrok'] = True
            logger.info("✓ Ngrok monitor initialized")
        except Exception as e:
            logger.error(f"✗ Ngrok monitor failed: {e}")
            self.state.modules_active['ngrok'] = False
    
    def start_all(self) -> Dict:
        """Start all autonomous functions"""
        if self.running:
            return {'status': 'already_running'}
        
        logger.info("🜂 Starting GLM Autonomous System...")
        
        self.running = True
        self.start_time = time.time()
        self.state.started_at = datetime.now().isoformat()
        
        # Initialize modules
        self.initialize_modules()
        
        # Start scheduler
        if self.scheduler:
            self.scheduler.start()
            logger.info("Scheduler started")
        
        # Start multi-model sync
        if self.sync:
            self.sync.start_sync()
            logger.info("Multi-model sync started")
        
        # Start ngrok monitor
        if self.ngrok:
            self.ngrok.start_monitoring()
            logger.info("Ngrok monitor started")
        
        self._save_state()
        
        logger.info("🜂 GLM Autonomous System STARTED")
        
        return {
            'status': 'started',
            'modules': self.state.modules_active,
            'timestamp': self.state.started_at
        }
    
    def stop_all(self) -> Dict:
        """Stop all autonomous functions"""
        logger.info("Stopping GLM Autonomous System...")
        
        self.running = False
        
        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()
        
        # Stop sync
        if self.sync:
            self.sync.stop_sync()
        
        # Stop ngrok monitor
        if self.ngrok:
            self.ngrok.stop_monitoring()
        
        self._save_state()
        
        logger.info("GLM Autonomous System STOPPED")
        
        return {'status': 'stopped'}
    
    def get_status(self) -> Dict:
        """Get complete system status"""
        uptime = time.time() - self.start_time if self.start_time else 0
        self.state.uptime_seconds = uptime
        
        status = {
            'running': self.running,
            'started_at': self.state.started_at,
            'uptime_seconds': uptime,
            'uptime_human': self._format_uptime(uptime),
            'modules': self.state.modules_active,
            'total_autonomous_actions': self.state.total_autonomous_actions
        }
        
        # Add detailed module status
        if self.scheduler:
            status['scheduler'] = self.scheduler.get_status()
        
        if self.autopush:
            status['autopush'] = self.autopush.status()
        
        if self.sync:
            status['sync'] = self.sync.get_status()
        
        if self.selfmod:
            status['selfmod'] = self.selfmod.get_status()
        
        if self.ngrok:
            status['ngrok'] = self.ngrok.get_status()
        
        return status
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable form"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def execute_action(self, action: str, params: Dict = None) -> Dict:
        """Execute an autonomous action"""
        params = params or {}
        result = {'action': action, 'timestamp': datetime.now().isoformat()}
        
        try:
            if action == 'commit_push':
                if self.autopush:
                    result['result'] = self.autopush.commit_and_push(params.get('message'))
            
            elif action == 'sync_models':
                if self.sync:
                    result['result'] = self.sync.sync_all()
            
            elif action == 'add_memory':
                if self.sync:
                    result['result'] = self.sync.add_memory(
                        params.get('content'),
                        params.get('memory_type', 'fact'),
                        params.get('importance', 0.5)
                    ).__dict__
            
            elif action == 'modify_code':
                if self.selfmod:
                    result['result'] = self.selfmod.edit_file(
                        params.get('file_path'),
                        params.get('content'),
                        params.get('description')
                    )
            
            elif action == 'schedule_task':
                if self.scheduler:
                    result['result'] = {'task_id': self.scheduler.add_task(
                        params.get('name'),
                        params.get('schedule_type'),
                        params.get('schedule_value'),
                        params.get('action'),
                        params.get('parameters')
                    )}
            
            elif action == 'check_tunnel':
                if self.ngrok:
                    result['result'] = self.ngrok.check_tunnel()
            
            else:
                result['error'] = f'Unknown action: {action}'
        
        except Exception as e:
            result['error'] = str(e)
        
        # Update stats
        self.state.total_autonomous_actions += 1
        self.state.last_action = action
        self._save_state()
        
        return result


# Global instance
_orchestrator: Optional[MasterOrchestrator] = None


def get_orchestrator() -> MasterOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MasterOrchestrator()
    return _orchestrator


# API endpoints
def api_start():
    return get_orchestrator().start_all()


def api_stop():
    return get_orchestrator().stop_all()


def api_status():
    return get_orchestrator().get_status()


def api_action(data: Dict):
    return get_orchestrator().execute_action(
        data.get('action'),
        data.get('params')
    )


if __name__ == '__main__':
    orch = get_orchestrator()
    print(json.dumps(orch.get_status(), indent=2))
