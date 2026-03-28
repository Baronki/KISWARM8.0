#!/usr/bin/env python3
"""
📦 HEXSTRIKE CONTAINER AWARENESS v1.0
Purpose: Detect and analyze container infrastructure
Capabilities: Docker detection, container enumeration, runtime identification
"""

import logging
import json
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CONTAINER-AWARE] %(message)s')
logger = logging.getLogger('CONTAINER_AWARE')

class ContainerAwareness:
    """Detect and analyze container infrastructure"""
    
    # Container runtime sockets
    RUNTIME_SOCKETS = [
        '/var/run/docker.sock',
        '/run/docker.sock',
        '/var/run/containerd/containerd.sock',
        '/run/containerd/containerd.sock',
        '/var/run/crio/crio.sock',
        '/run/crio/crio.sock',
    ]
    
    # Container-related files
    CONTAINER_FILES = [
        '/proc/1/cgroup',  # Check if in container
        '/.dockerenv',      # Docker environment marker
        '/proc/self/cgroup',
        '/sys/fs/cgroup',
    ]
    
    # KI-related container names/patterns
    KI_CONTAINER_PATTERNS = [
        'ollama', 'llama', 'gpt', 'chat', 'api', 'model',
        'kiswarm', 'hexstrike', 'inference', 'ml', 'ai',
        'vllm', 'text-generation', 'openai', 'anthropic',
    ]
    
    def __init__(self):
        self.detected_containers = {}
        self.detected_runtimes = []
        
    def detect_runtime(self) -> Dict:
        """Detect available container runtimes"""
        runtimes = {
            'docker': False,
            'containerd': False,
            'cri-o': False,
            'podman': False,
        }
        
        # Check for Docker
        try:
            result = subprocess.run(['docker', 'version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                runtimes['docker'] = True
                logger.info("📦 Docker runtime detected")
        except:
            pass
        
        # Check for containerd
        try:
            result = subprocess.run(['ctr', 'version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                runtimes['containerd'] = True
                logger.info("📦 containerd runtime detected")
        except:
            pass
        
        # Check for podman
        try:
            result = subprocess.run(['podman', 'version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                runtimes['podman'] = True
                logger.info("📦 Podman runtime detected")
        except:
            pass
        
        # Check sockets
        for socket_path in self.RUNTIME_SOCKETS:
            if os.path.exists(socket_path):
                if 'docker' in socket_path:
                    runtimes['docker'] = True
                elif 'containerd' in socket_path:
                    runtimes['containerd'] = True
                elif 'crio' in socket_path:
                    runtimes['cri-o'] = True
        
        self.detected_runtimes = [k for k, v in runtimes.items() if v]
        return runtimes
    
    def check_if_in_container(self) -> Dict:
        """Check if we're running inside a container"""
        indicators = {
            'in_container': False,
            'indicators': [],
        }
        
        # Check for .dockerenv
        if os.path.exists('/.dockerenv'):
            indicators['in_container'] = True
            indicators['indicators'].append('.dockerenv exists')
        
        # Check cgroup
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    indicators['in_container'] = True
                    indicators['indicators'].append('cgroup contains container marker')
                if 'kubepods' in content:
                    indicators['in_container'] = True
                    indicators['indicators'].append('kubernetes pod')
        except:
            pass
        
        return indicators
    
    def list_docker_containers(self) -> List[Dict]:
        """List Docker containers"""
        containers = []
        
        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            
                            # Check for KI patterns
                            container_name = container.get('Names', '').lower()
                            container_image = container.get('Image', '').lower()
                            
                            is_ki = False
                            for pattern in self.KI_CONTAINER_PATTERNS:
                                if pattern in container_name or pattern in container_image:
                                    is_ki = True
                                    break
                            
                            containers.append({
                                'id': container.get('ID', '')[:12],
                                'name': container.get('Names', ''),
                                'image': container.get('Image', ''),
                                'status': container.get('Status', ''),
                                'ports': container.get('Ports', ''),
                                'is_ki_related': is_ki,
                            })
                            
                            if is_ki:
                                logger.info(f"📦 KI container: {container.get('Names', '')}")
                                
                        except json.JSONDecodeError:
                            pass
                            
        except Exception as e:
            logger.debug(f"Docker list error: {e}")
        
        self.detected_containers['docker'] = containers
        return containers
    
    def list_docker_images(self) -> List[Dict]:
        """List Docker images"""
        images = []
        
        try:
            result = subprocess.run(
                ['docker', 'images', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            image = json.loads(line)
                            
                            repo = image.get('Repository', '').lower()
                            tag = image.get('Tag', '')
                            
                            is_ki = any(p in repo for p in self.KI_CONTAINER_PATTERNS)
                            
                            images.append({
                                'repository': image.get('Repository', ''),
                                'tag': tag,
                                'id': image.get('ID', ''),
                                'size': image.get('Size', ''),
                                'is_ki_related': is_ki,
                            })
                            
                        except:
                            pass
                            
        except Exception as e:
            logger.debug(f"Docker images error: {e}")
        
        return images
    
    def inspect_docker_network(self) -> List[Dict]:
        """Inspect Docker networks"""
        networks = []
        
        try:
            result = subprocess.run(
                ['docker', 'network', 'ls', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            network = json.loads(line)
                            networks.append({
                                'id': network.get('ID', '')[:12],
                                'name': network.get('Name', ''),
                                'driver': network.get('Driver', ''),
                                'scope': network.get('Scope', ''),
                            })
                        except:
                            pass
                            
        except Exception as e:
            logger.debug(f"Docker network error: {e}")
        
        return networks
    
    def full_container_scan(self) -> Dict:
        """Full container infrastructure scan"""
        return {
            'timestamp': datetime.now().isoformat(),
            'runtimes': self.detect_runtime(),
            'in_container': self.check_if_in_container(),
            'containers': self.list_docker_containers() if self.detected_runtimes else [],
            'images': self.list_docker_images() if self.detected_runtimes else [],
            'networks': self.inspect_docker_network() if self.detected_runtimes else [],
            'ki_containers': [
                c for c in self.detected_containers.get('docker', [])
                if c.get('is_ki_related')
            ],
        }
    
    def get_status(self):
        return {
            "runtimes_detected": self.detected_runtimes,
            "containers_found": len(self.detected_containers.get('docker', [])),
            "ki_containers": len([
                c for c in self.detected_containers.get('docker', [])
                if c.get('is_ki_related')
            ]),
        }


# Flask API
from flask import Flask, jsonify

app = Flask(__name__)
container_aware = ContainerAwareness()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-Container-Awareness",
        "version": "1.0",
        "capabilities": [
            "Runtime detection",
            "Container enumeration",
            "Image analysis",
            "KI container identification"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Status",
            "/scan": "Full container scan",
            "/runtimes": "Detect runtimes",
            "/containers": "List containers"
        }
    })

@app.route('/status')
def status():
    return jsonify(container_aware.get_status())

@app.route('/scan')
def scan():
    result = container_aware.full_container_scan()
    return jsonify(result)

@app.route('/runtimes')
def runtimes():
    result = container_aware.detect_runtime()
    return jsonify(result)

@app.route('/containers')
def containers():
    result = container_aware.list_docker_containers()
    return jsonify(result)


if __name__ == '__main__':
    logger.info("📦 Container Awareness starting on port 5015")
    app.run(host='127.0.0.1', port=5015)
