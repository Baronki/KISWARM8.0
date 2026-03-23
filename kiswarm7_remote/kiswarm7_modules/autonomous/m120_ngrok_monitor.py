#!/usr/bin/env python3
"""
KISWARM7.0 - m120: Ngrok Tunnel Monitor & Auto-Rebuild
Monitors and automatically rebuilds ngrok tunnel on failure

This module:
- Monitors ngrok tunnel health
- Auto-restarts on failure
- Reports public URL changes
- Maintains tunnel persistence
"""

import os
import json
import time
import subprocess
import threading
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import socket

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m120] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m120_ngrok')

# Configuration
DATA_DIR = Path('/opt/kiswarm7/data')
TUNNEL_FILE = DATA_DIR / 'tunnel_status.json'
NGROK_API = 'http://localhost:4040'
FLASK_PORT = 5002


@dataclass
class TunnelStatus:
    """Current tunnel status"""
    active: bool
    public_url: Optional[str]
    local_addr: str
    started_at: Optional[str]
    last_check: str
    restart_count: int
    last_error: Optional[str]


class NgrokMonitor:
    """
    Ngrok Tunnel Monitor
    
    Ensures tunnel stays active and auto-recovers
    """
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.check_interval = 30  # seconds
        
        self.status = TunnelStatus(
            active=False,
            public_url=None,
            local_addr=f'localhost:{FLASK_PORT}',
            started_at=None,
            last_check=datetime.now().isoformat(),
            restart_count=0,
            last_error=None
        )
        
        self._load_status()
    
    def _load_status(self):
        """Load saved status"""
        if TUNNEL_FILE.exists():
            try:
                with open(TUNNEL_FILE, 'r') as f:
                    data = json.load(f)
                    self.status = TunnelStatus(**data)
            except:
                pass
    
    def _save_status(self):
        """Save status"""
        with open(TUNNEL_FILE, 'w') as f:
            json.dump(asdict(self.status), f, indent=2)
    
    def _check_flask_running(self) -> bool:
        """Check if Flask is running on the expected port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', FLASK_PORT))
            sock.close()
            return result == 0
        except:
            return False
    
    def _check_ngrok_api(self) -> Dict:
        """Check ngrok API for tunnel status"""
        try:
            response = requests.get(f'{NGROK_API}/api/tunnels', timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                
                if tunnels:
                    tunnel = tunnels[0]
                    return {
                        'active': True,
                        'public_url': tunnel.get('public_url'),
                        'proto': tunnel.get('proto'),
                        'name': tunnel.get('name')
                    }
            
            return {'active': False, 'error': 'No tunnels found'}
            
        except requests.exceptions.ConnectionError:
            return {'active': False, 'error': 'Ngrok API not responding'}
        except Exception as e:
            return {'active': False, 'error': str(e)}
    
    def _start_ngrok(self) -> Dict:
        """Start ngrok tunnel"""
        try:
            # Check if ngrok is already running
            result = subprocess.run(
                ['pgrep', '-f', 'ngrok'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Already running, check if tunnel is active
                api_result = self._check_ngrok_api()
                if api_result.get('active'):
                    return {'started': False, 'reason': 'already_running'}
                else:
                    # Kill and restart
                    subprocess.run(['pkill', '-f', 'ngrok'], check=False)
                    time.sleep(2)
            
            # Start ngrok
            subprocess.Popen(
                ['ngrok', 'http', str(FLASK_PORT), '--log=stdout'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for tunnel to establish
            time.sleep(5)
            
            # Verify it started
            for _ in range(10):
                api_result = self._check_ngrok_api()
                if api_result.get('active'):
                    return {
                        'started': True,
                        'public_url': api_result.get('public_url')
                    }
                time.sleep(1)
            
            return {'started': False, 'error': 'Tunnel failed to establish'}
            
        except Exception as e:
            return {'started': False, 'error': str(e)}
    
    def _restart_ngrok(self) -> Dict:
        """Restart ngrok tunnel"""
        logger.info("Restarting ngrok tunnel...")
        
        # Kill existing ngrok
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
        time.sleep(2)
        
        # Start fresh
        result = self._start_ngrok()
        
        if result.get('started'):
            self.status.restart_count += 1
            self.status.last_error = None
            logger.info(f"Ngrok restarted. Public URL: {result.get('public_url')}")
        else:
            self.status.last_error = result.get('error')
            logger.error(f"Ngrok restart failed: {result.get('error')}")
        
        self._save_status()
        return result
    
    def check_tunnel(self) -> Dict:
        """Check tunnel status and restart if needed"""
        self.status.last_check = datetime.now().isoformat()
        
        # Check Flask first
        flask_running = self._check_flask_running()
        
        if not flask_running:
            self.status.active = False
            self.status.last_error = 'Flask not running'
            self._save_status()
            
            return {
                'active': False,
                'error': 'Flask not running',
                'action': 'start_flask'
            }
        
        # Check ngrok
        ngrok_status = self._check_ngrok_api()
        
        if ngrok_status.get('active'):
            self.status.active = True
            self.status.public_url = ngrok_status.get('public_url')
            self.status.last_error = None
            self._save_status()
            
            return {
                'active': True,
                'public_url': self.status.public_url
            }
        
        # Tunnel not active, try to restart
        logger.warning("Tunnel inactive, attempting restart...")
        restart_result = self._restart_ngrok()
        
        if restart_result.get('started'):
            self.status.active = True
            self.status.public_url = restart_result.get('public_url')
            self._save_status()
            
            return {
                'active': True,
                'public_url': self.status.public_url,
                'restarted': True
            }
        
        self.status.active = False
        self._save_status()
        
        return {
            'active': False,
            'error': restart_result.get('error'),
            'restart_count': self.status.restart_count
        }
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        logger.info("Ngrok monitor started")
        
        while self.running:
            try:
                self.check_tunnel()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            # Sleep in small intervals to respond to stop quickly
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info("Ngrok monitor stopped")
    
    def start_monitoring(self) -> Dict:
        """Start background monitoring"""
        if self.running:
            return {'status': 'already_running'}
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        return {
            'status': 'started',
            'check_interval': self.check_interval
        }
    
    def stop_monitoring(self) -> Dict:
        """Stop background monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        return {'status': 'stopped'}
    
    def get_status(self) -> Dict:
        """Get current tunnel status"""
        # Do a fresh check
        status = self.check_tunnel()
        
        return {
            **asdict(self.status),
            'current_check': status,
            'monitor_running': self.running
        }
    
    def get_public_url(self) -> Optional[str]:
        """Get current public URL"""
        ngrok_status = self._check_ngrok_api()
        return ngrok_status.get('public_url')
    
    def force_restart(self) -> Dict:
        """Force a tunnel restart"""
        return self._restart_ngrok()


# Global instance
_ngrok_monitor: Optional[NgrokMonitor] = None


def get_ngrok_monitor() -> NgrokMonitor:
    """Get global ngrok monitor instance"""
    global _ngrok_monitor
    if _ngrok_monitor is None:
        _ngrok_monitor = NgrokMonitor()
    return _ngrok_monitor


# API endpoints
def api_get_status():
    return get_ngrok_monitor().get_status()


def api_check_tunnel():
    return get_ngrok_monitor().check_tunnel()


def api_start_monitoring():
    return get_ngrok_monitor().start_monitoring()


def api_stop_monitoring():
    return get_ngrok_monitor().stop_monitoring()


def api_force_restart():
    return get_ngrok_monitor().force_restart()


def api_get_url():
    url = get_ngrok_monitor().get_public_url()
    return {'public_url': url, 'active': url is not None}


if __name__ == '__main__':
    monitor = get_ngrok_monitor()
    print(json.dumps(monitor.get_status(), indent=2))
