#!/usr/bin/env python3
"""
KISWARM8.0 Mesh Bridge Agent
Bidirectional Tor/Tailscale Communication with Automatic Failover

This agent runs on the master node (UpCloud) and monitors all mesh nodes,
providing automatic failover between Tailscale, Tor, and clearnet channels.
"""

import requests
import json
import time
import threading
import logging
import subprocess
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [MESH] %(message)s'
)
logger = logging.getLogger('MESH_BRIDGE')

# Mesh Configuration
MESH_CONFIG = {
    "mesh_name": "KISWARM8.0_MESH",
    "version": "8.0.1",
    "nodes": {
        "upcloud_kiswarm": {
            "role": "MASTER",
            "onion": "7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion",
            "tailscale_ip": "100.112.181.6",
            "public_ip": "95.111.212.112",
            "services": {"hexstrike": 5000, "execute": 5556}
        },
        "openclaw": {
            "role": "BACKUP",
            "onion": "tezgnblscuh6ckpvebiwyqbm2rjbmz3mvszljrbeqfewhyejgr4jf4yd.onion",
            "tailscale_ip": "100.113.1.85"
        },
        "glm": {
            "role": "CLIENT",
            "onion": "5fvwe74sqcvvm452dnfwqab7giaofp6eb56v74t6lxze4cvt4m75saad.onion",
            "tailscale_ip": "100.79.42.15"
        },
        "browser": {
            "role": "CLIENT",
            "tailscale_ip": "100.92.174.24"
        }
    }
}

class MeshBridge:
    def __init__(self, config_path=None):
        self.config = MESH_CONFIG
        self.tor_session = requests.Session()
        self.tor_session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        self.running = False
        self.peers_status = {}
        self.health_history = []
        
    def get_local_identity(self):
        """Get local KISWARM identity via LAN"""
        try:
            r = requests.get('http://localhost:5000/api/identity', timeout=5)
            return r.json()
        except Exception as e:
            logger.error(f"Local identity error: {e}")
            return None
    
    def check_peer_via_tor(self, peer_name, onion):
        """Check peer via Tor hidden service"""
        try:
            url = f"http://{onion}/"
            r = self.tor_session.get(url, timeout=30)
            return {
                'peer': peer_name,
                'status': 'online',
                'via': 'tor',
                'response_code': r.status_code,
                'latency_ms': r.elapsed.total_seconds() * 1000,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Tor check failed for {peer_name}: {e}")
            return {
                'peer': peer_name,
                'status': 'offline',
                'via': 'tor',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_peer_via_tailscale(self, peer_name, ip):
        """Check peer via Tailscale mesh"""
        try:
            start = time.time()
            r = requests.get(f"http://{ip}:5000/", timeout=10)
            latency = (time.time() - start) * 1000
            return {
                'peer': peer_name,
                'status': 'online',
                'via': 'tailscale',
                'response_code': r.status_code,
                'latency_ms': latency,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'peer': peer_name,
                'status': 'offline',
                'via': 'tailscale',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def ping_peer(self, ip):
        """Ping peer via ICMP"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', ip],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def get_best_channel(self, peer_name):
        """Determine best available channel for peer"""
        status = self.peers_status.get(peer_name, {})
        
        # Prefer Tailscale for speed
        ts_status = {k: v for k, v in status.items() if v.get('via') == 'tailscale'}
        if ts_status and list(ts_status.values())[0].get('status') == 'online':
            return 'tailscale'
        
        # Fallback to Tor
        tor_status = {k: v for k, v in status.items() if v.get('via') == 'tor'}
        if tor_status and list(tor_status.values())[0].get('status') == 'online':
            return 'tor'
        
        return 'unavailable'
    
    def health_check_loop(self):
        """Continuous health check of all peers"""
        while self.running:
            cycle_start = time.time()
            
            for peer_name, peer_info in self.config.get('nodes', {}).items():
                if peer_name == 'upcloud_kiswarm':
                    continue  # Skip self
                
                self.peers_status[peer_name] = {}
                
                # Try Tailscale first
                ts_ip = peer_info.get('tailscale_ip')
                if ts_ip:
                    result = self.check_peer_via_tailscale(peer_name, ts_ip)
                    self.peers_status[peer_name]['tailscale'] = result
                    if result['status'] == 'online':
                        logger.info(f"✓ {peer_name} online via Tailscale ({result.get('latency_ms', 0):.0f}ms)")
                
                # Also check via Tor
                onion = peer_info.get('onion')
                if onion:
                    result = self.check_peer_via_tor(peer_name, onion)
                    self.peers_status[peer_name]['tor'] = result
                    if result['status'] == 'online':
                        logger.info(f"✓ {peer_name} online via Tor ({result.get('latency_ms', 0):.0f}ms)")
                    else:
                        logger.warning(f"✗ {peer_name} Tor check failed")
            
            # Record health history
            health_record = {
                'timestamp': datetime.now().isoformat(),
                'peers': {k: self.get_best_channel(k) for k in self.peers_status.keys()}
            }
            self.health_history.append(health_record)
            
            # Keep last 100 records
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            # Sleep for remainder of 60 seconds
            elapsed = time.time() - cycle_start
            sleep_time = max(0, 60 - elapsed)
            time.sleep(sleep_time)
    
    def send_mesh_heartbeat(self):
        """Send heartbeat to all online peers"""
        identity = self.get_local_identity()
        if not identity:
            return
        
        for peer_name, peer_info in self.config.get('nodes', {}).items():
            if peer_name == 'upcloud_kiswarm':
                continue
            
            best_channel = self.get_best_channel(peer_name)
            
            if best_channel == 'tailscale':
                try:
                    ts_ip = peer_info.get('tailscale_ip')
                    requests.post(
                        f"http://{ts_ip}:5000/api/mesh/heartbeat",
                        json=identity,
                        timeout=10
                    )
                except:
                    pass
            elif best_channel == 'tor':
                try:
                    onion = peer_info.get('onion')
                    self.tor_session.post(
                        f"http://{onion}/api/mesh/heartbeat",
                        json=identity,
                        timeout=30
                    )
                except:
                    pass
    
    def get_status(self):
        """Get current mesh status"""
        return {
            'mesh_name': self.config.get('mesh_name'),
            'version': self.config.get('version'),
            'local_identity': self.get_local_identity(),
            'peers': self.peers_status,
            'best_channels': {k: self.get_best_channel(k) for k in self.peers_status.keys()},
            'health_history_count': len(self.health_history),
            'timestamp': datetime.now().isoformat()
        }
    
    def start(self):
        """Start the mesh bridge"""
        self.running = True
        self.health_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        self.health_thread.start()
        logger.info("🧅 KISWARM Mesh Bridge started")
        logger.info(f"   Monitoring {len(self.config['nodes']) - 1} peers")
        
    def stop(self):
        """Stop the mesh bridge"""
        self.running = False
        logger.info("Mesh Bridge stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KISWARM Mesh Bridge Agent')
    parser.add_argument('--once', action='store_true', help='Run single health check')
    parser.add_argument('--status', action='store_true', help='Print current status')
    args = parser.parse_args()
    
    bridge = MeshBridge()
    
    if args.once:
        # Single check mode
        for peer_name, peer_info in MESH_CONFIG['nodes'].items():
            if peer_name == 'upcloud_kiswarm':
                continue
            ts_ip = peer_info.get('tailscale_ip')
            if ts_ip:
                result = bridge.check_peer_via_tailscale(peer_name, ts_ip)
                print(f"{peer_name}: {result['status']} via Tailscale")
    elif args.status:
        # Status mode - requires running instance
        print(json.dumps(bridge.get_status(), indent=2))
    else:
        # Daemon mode
        bridge.start()
        
        try:
            while True:
                time.sleep(60)
                status = bridge.get_status()
                print(f"[{datetime.now().isoformat()}] Mesh Status: {status['best_channels']}")
        except KeyboardInterrupt:
            bridge.stop()


if __name__ == '__main__':
    main()
