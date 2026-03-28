#!/usr/bin/env python3
"""
☸️ HEXSTRIKE K8S DISCOVERY v1.0
Purpose: Discover Kubernetes clusters and container orchestration
Capabilities: K8s API detection, node discovery, service mesh detection, container awareness
"""

import requests
import socket
import logging
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s [K8S-DISCOVERY] %(message)s')
logger = logging.getLogger('K8S_DISCOVERY')

class K8sDiscovery:
    """Discover Kubernetes clusters and container infrastructure"""
    
    # Kubernetes standard ports
    K8S_PORTS = {
        6443: 'kube-apiserver',
        10250: 'kubelet',
        10251: 'kube-scheduler',
        10252: 'kube-controller',
        10257: 'kube-controller-manager-secure',
        10259: 'kube-scheduler-secure',
        2379: 'etcd',
        2380: 'etcd-peer',
        30000: 'nodeport-range',
        32767: 'nodeport-range',
    }
    
    # K8s API endpoints
    K8S_API_ENDPOINTS = [
        '/api',
        '/api/v1',
        '/api/v1/nodes',
        '/api/v1/pods',
        '/api/v1/services',
        '/api/v1/namespaces',
        '/apis',
        '/apis/apps/v1',
        '/apis/apps/v1/deployments',
        '/healthz',
        '/readyz',
        '/livez',
        '/version',
        '/metrics',
        '/openapi/v2',
    ]
    
    # Service mesh indicators
    SERVICE_MESH_PORTS = {
        15001: 'envoy-proxy',
        15006: 'envoy-inbound',
        15010: 'istio-pilot-http',
        15011: 'istio-pilot-https',
        15012: 'istio-pilot-grpc',
        15014: 'istio-mixer',
        15090: 'istio-proxy-metrics',
        4190: 'linkerd-proxy',
        9990: 'linkerd-admin',
        9991: 'linkerd-control',
    }
    
    # Docker/container indicators
    CONTAINER_PORTS = {
        2375: 'docker-http',
        2376: 'docker-https',
        2377: 'docker-swarm',
        4243: 'docker-https-alt',
        5000: 'docker-registry',
        5001: 'docker-registry-alt',
    }
    
    # Container runtime patterns
    CONTAINER_PATTERNS = [
        'kubernetes', 'k8s', 'kube', 'docker', 'containerd', 'cri-o',
        'podman', 'runc', 'kubelet', 'kube-proxy', 'etcd',
        'istio', 'linkerd', 'consul', 'nomad',
    ]
    
    def __init__(self):
        self.discovered_clusters = {}
        self.discovered_containers = {}
        
    def check_k8s_api(self, host: str, port: int = 6443) -> Optional[Dict]:
        """Check if host is running Kubernetes API server"""
        url = f"https://{host}:{port}"
        
        try:
            # Try to get K8s version endpoint (often unauthenticated)
            r = requests.get(
                f"{url}/version",
                verify=False,
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            
            if r.ok:
                try:
                    data = r.json()
                    return {
                        'host': host,
                        'port': port,
                        'type': 'kubernetes-api',
                        'version': data.get('gitVersion', 'unknown'),
                        'platform': data.get('platform', 'unknown'),
                        'is_k8s': True,
                        'info': data,
                    }
                except:
                    pass
                    
        except:
            pass
        
        # Try healthz endpoint
        try:
            r = requests.get(
                f"{url}/healthz",
                verify=False,
                timeout=5
            )
            if r.ok or r.status_code == 401:  # 401 means API exists but needs auth
                return {
                    'host': host,
                    'port': port,
                    'type': 'kubernetes-api',
                    'status_code': r.status_code,
                    'is_k8s': True,
                    'needs_auth': r.status_code == 401,
                }
        except:
            pass
        
        return None
    
    def check_kubelet(self, host: str, port: int = 10250) -> Optional[Dict]:
        """Check if kubelet is running"""
        url = f"https://{host}:{port}"
        
        try:
            # Kubelet health check
            r = requests.get(
                f"{url}/healthz",
                verify=False,
                timeout=5
            )
            
            if r.ok:
                return {
                    'host': host,
                    'port': port,
                    'type': 'kubelet',
                    'is_k8s_node': True,
                }
                
        except:
            pass
        
        return None
    
    def check_docker_api(self, host: str, port: int = 2375) -> Optional[Dict]:
        """Check for exposed Docker API"""
        url = f"http://{host}:{port}"
        
        try:
            r = requests.get(f"{url}/version", timeout=5)
            
            if r.ok:
                data = r.json()
                return {
                    'host': host,
                    'port': port,
                    'type': 'docker-api',
                    'version': data.get('Version', 'unknown'),
                    'api_version': data.get('ApiVersion', 'unknown'),
                    'os': data.get('Os', 'unknown'),
                    'exposed': True,  # SECURITY ISSUE - Docker API exposed!
                    'severity': 'CRITICAL',
                }
                
        except:
            pass
        
        return None
    
    def check_docker_registry(self, host: str, port: int = 5000) -> Optional[Dict]:
        """Check for Docker registry"""
        url = f"http://{host}:{port}"
        
        try:
            r = requests.get(f"{url}/v2/_catalog", timeout=5)
            
            if r.ok:
                data = r.json()
                return {
                    'host': host,
                    'port': port,
                    'type': 'docker-registry',
                    'repositories': data.get('repositories', []),
                    'exposed': True,
                }
                
            # Check v2 API
            r = requests.get(f"{url}/v2/", timeout=5)
            if r.ok:
                return {
                    'host': host,
                    'port': port,
                    'type': 'docker-registry',
                    'api_version': 'v2',
                }
                
        except:
            pass
        
        return None
    
    def check_service_mesh(self, host: str, ports: List[int] = None) -> List[Dict]:
        """Check for service mesh components"""
        ports = ports or list(self.SERVICE_MESH_PORTS.keys())
        results = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    service = self.SERVICE_MESH_PORTS.get(port, 'unknown')
                    results.append({
                        'host': host,
                        'port': port,
                        'type': 'service-mesh',
                        'service': service,
                        'is_istio': 'istio' in service,
                        'is_linkerd': 'linkerd' in service,
                    })
                    logger.info(f"☸️ Service mesh found: {host}:{port} ({service})")
                    
            except:
                pass
        
        return results
    
    def scan_host_k8s(self, host: str) -> Dict:
        """Full K8s/container scan of host"""
        results = {
            'host': host,
            'timestamp': datetime.now().isoformat(),
            'kubernetes': None,
            'docker': None,
            'service_mesh': [],
            'containers': [],
        }
        
        # Check K8s API
        k8s_api = self.check_k8s_api(host)
        if k8s_api:
            results['kubernetes'] = k8s_api
            logger.info(f"☸️ K8s API found: {host}")
        
        # Check Kubelet
        kubelet = self.check_kubelet(host)
        if kubelet:
            results['kubernetes'] = results.get('kubernetes') or {}
            results['kubernetes']['kubelet'] = kubelet
        
        # Check Docker
        docker = self.check_docker_api(host)
        if docker:
            results['docker'] = docker
            logger.warning(f"🐳 Exposed Docker API: {host}")
        
        # Check Docker registry
        registry = self.check_docker_registry(host)
        if registry:
            results['containers'].append(registry)
        
        # Check service mesh
        mesh = self.check_service_mesh(host)
        if mesh:
            results['service_mesh'] = mesh
        
        return results
    
    def scan_subnet_k8s(self, base_ip: str, range_size: int = 30) -> Dict:
        """Scan subnet for K8s/container infrastructure"""
        results = {
            'scan_time': datetime.now().isoformat(),
            'base_ip': base_ip,
            'clusters_found': 0,
            'docker_exposed': 0,
            'hosts_scanned': 0,
            'findings': [],
        }
        
        parts = base_ip.split('.')
        if len(parts) != 4:
            return results
        
        base = '.'.join(parts[:3])
        start = int(parts[3])
        
        for i in range(start, min(start + range_size, 255)):
            host = f"{base}.{i}"
            
            # Quick K8s port scan
            k8s_open = False
            for port in self.K8S_PORTS.keys():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        k8s_open = True
                        break
                except:
                    pass
            
            if k8s_open:
                results['hosts_scanned'] += 1
                scan_result = self.scan_host_k8s(host)
                
                if scan_result.get('kubernetes'):
                    results['clusters_found'] += 1
                    results['findings'].append(scan_result)
                    
                if scan_result.get('docker', {}).get('exposed'):
                    results['docker_exposed'] += 1
                    results['findings'].append(scan_result)
        
        return results
    
    def get_status(self):
        return {
            "clusters_discovered": len(self.discovered_clusters),
            "containers_discovered": len(self.discovered_containers),
            "k8s_ports_monitored": len(self.K8S_PORTS),
            "service_mesh_ports": len(self.SERVICE_MESH_PORTS),
        }


# Flask API
from flask import Flask, jsonify, request

app = Flask(__name__)
k8s = K8sDiscovery()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-K8S-Discovery",
        "version": "1.0",
        "capabilities": [
            "Kubernetes API detection",
            "Kubelet discovery",
            "Docker API detection",
            "Service mesh identification",
            "Container registry discovery"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Discovery status",
            "/scan/host/<host>": "Scan host for K8s",
            "/scan/subnet/<base_ip>": "Scan subnet for K8s"
        }
    })

@app.route('/status')
def status():
    return jsonify(k8s.get_status())

@app.route('/scan/host/<host>')
def scan_host(host):
    result = k8s.scan_host_k8s(host)
    return jsonify(result)

@app.route('/scan/subnet/<path:base_ip>')
def scan_subnet(base_ip):
    range_size = request.args.get('range', 20, type=int)
    result = k8s.scan_subnet_k8s(base_ip, range_size)
    return jsonify(result)


if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    logger.info("☸️ K8s Discovery starting on port 5012")
    app.run(host='127.0.0.1', port=5012)
