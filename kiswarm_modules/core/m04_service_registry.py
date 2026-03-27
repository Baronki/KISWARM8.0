#!/usr/bin/env python3
"""
KISWARM8.0 - Module 04: Service Registry
========================================
Service discovery and health tracking for KISWARM.

Features:
  - Service registration and discovery
  - Health check monitoring
  - Load balancing decisions
  - Service versioning
  - Dependency tracking

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import json
import time
import logging
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random

logger = logging.getLogger('m04_service_registry')


class ServiceStatus(str, Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """Service endpoint definition"""
    host: str
    port: int
    protocol: str = "http"
    path: str = ""
    
    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"


@dataclass
class ServiceInstance:
    """Registered service instance"""
    service_id: str
    service_name: str
    version: str
    endpoint: ServiceEndpoint
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: float = 0
    check_count: int = 0
    fail_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    registered_at: float = field(default_factory=time.time)
    health_endpoint: str = "/health"
    check_interval: int = 30  # seconds
    timeout: int = 5


class ServiceRegistry:
    """
    Service Registry for KISWARM
    
    Tracks all services, their health, and dependencies.
    Enables service discovery and load balancing.
    """
    
    HEALTH_CHECK_INTERVAL = 30  # seconds
    MAX_FAILURES = 3
    RETRY_DELAY = 60  # seconds before retrying unhealthy service
    
    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or Path('/opt/kiswarm7/data/service_registry.json')
        
        self._services: Dict[str, ServiceInstance] = {}
        self._service_types: Dict[str, List[str]] = {}  # name -> [ids]
        self._lock = threading.RLock()
        self._running = False
        self._health_thread: Optional[threading.Thread] = None
        
        # Load existing registry
        self._load_registry()
        
        # Register built-in services
        self._register_builtin_services()
        
    def _register_builtin_services(self):
        """Register KISWARM built-in services"""
        builtins = [
            ServiceInstance(
                service_id="glm-bridge-primary",
                service_name="glm-bridge",
                version="8.0.0",
                endpoint=ServiceEndpoint(host="localhost", port=5002),
                health_endpoint="/health",
                dependencies=[],
                metadata={'description': 'GLM Bridge API - Memory, Learning, Identity'}
            ),
            ServiceInstance(
                service_id="glm-autonomous-primary",
                service_name="glm-autonomous",
                version="8.0.0",
                endpoint=ServiceEndpoint(host="localhost", port=5555),
                health_endpoint="/api/status",
                dependencies=["glm-bridge"],
                metadata={'description': 'GLM Autonomous Access - Command Execution'}
            ),
            ServiceInstance(
                service_id="hexstrike-primary",
                service_name="hexstrike",
                version="8.0.0",
                endpoint=ServiceEndpoint(host="localhost", port=5000),
                health_endpoint="/api/status",
                dependencies=[],
                metadata={'description': 'HEXSTRIKE - Multi-KI Network'}
            )
        ]
        
        for svc in builtins:
            if svc.service_id not in self._services:
                self._services[svc.service_id] = svc
                self._add_to_type_index(svc)
                
    def _add_to_type_index(self, service: ServiceInstance):
        """Add service to type index"""
        if service.service_name not in self._service_types:
            self._service_types[service.service_name] = []
        if service.service_id not in self._service_types[service.service_name]:
            self._service_types[service.service_name].append(service.service_id)
            
    def register(self, service: ServiceInstance) -> bool:
        """Register a new service instance"""
        with self._lock:
            self._services[service.service_id] = service
            self._add_to_type_index(service)
            self._save_registry()
            
        logger.info(f"Registered service: {service.service_name} ({service.service_id})")
        return True
        
    def deregister(self, service_id: str) -> bool:
        """Deregister a service instance"""
        with self._lock:
            if service_id in self._services:
                service = self._services[service_id]
                self._service_types[service.service_name].remove(service_id)
                del self._services[service_id]
                self._save_registry()
                logger.info(f"Deregistered service: {service_id}")
                return True
        return False
        
    def get(self, service_id: str) -> Optional[ServiceInstance]:
        """Get a service by ID"""
        return self._services.get(service_id)
        
    def get_by_name(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of a service by name"""
        with self._lock:
            ids = self._service_types.get(service_name, [])
            return [self._services[i] for i in ids if i in self._services]
            
    def get_healthy(self, service_name: str) -> List[ServiceInstance]:
        """Get healthy instances of a service"""
        services = self.get_by_name(service_name)
        return [s for s in services if s.status == ServiceStatus.HEALTHY]
        
    def get_endpoint(self, service_name: str, load_balance: bool = True) -> Optional[ServiceEndpoint]:
        """Get an endpoint for a service (with optional load balancing)"""
        healthy = self.get_healthy(service_name)
        if not healthy:
            return None
            
        if load_balance:
            # Simple round-robin / random selection
            service = random.choice(healthy)
        else:
            service = healthy[0]
            
        return service.endpoint
        
    def check_health(self, service_id: str) -> ServiceStatus:
        """Check health of a specific service"""
        service = self._services.get(service_id)
        if not service:
            return ServiceStatus.UNKNOWN
            
        try:
            url = f"{service.endpoint.url}{service.health_endpoint}"
            response = requests.get(url, timeout=service.timeout)
            
            service.check_count += 1
            service.last_check = time.time()
            
            if response.status_code == 200:
                service.fail_count = 0
                service.status = ServiceStatus.HEALTHY
            else:
                service.fail_count += 1
                if service.fail_count >= self.MAX_FAILURES:
                    service.status = ServiceStatus.UNHEALTHY
                else:
                    service.status = ServiceStatus.DEGRADED
                    
        except Exception as e:
            service.fail_count += 1
            service.last_check = time.time()
            
            if service.fail_count >= self.MAX_FAILURES:
                service.status = ServiceStatus.UNHEALTHY
            else:
                service.status = ServiceStatus.DEGRADED
                
            logger.debug(f"Health check failed for {service_id}: {e}")
            
        return service.status
        
    def check_all(self) -> Dict[str, ServiceStatus]:
        """Check health of all registered services"""
        results = {}
        with self._lock:
            for service_id in list(self._services.keys()):
                results[service_id] = self.check_health(service_id)
        return results
        
    def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            self.check_all()
            time.sleep(self.HEALTH_CHECK_INTERVAL)
            
    def start(self):
        """Start health monitoring"""
        if self._running:
            return
        self._running = True
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()
        logger.info("Service registry health monitoring started")
        
    def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5)
        logger.info("Service registry stopped")
        
    def _load_registry(self):
        """Load registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                for svc_data in data.get('services', []):
                    endpoint = ServiceEndpoint(**svc_data['endpoint'])
                    service = ServiceInstance(
                        service_id=svc_data['service_id'],
                        service_name=svc_data['service_name'],
                        version=svc_data['version'],
                        endpoint=endpoint,
                        status=ServiceStatus(svc_data.get('status', 'unknown')),
                        metadata=svc_data.get('metadata', {}),
                        dependencies=svc_data.get('dependencies', []),
                        health_endpoint=svc_data.get('health_endpoint', '/health')
                    )
                    self._services[service.service_id] = service
                    self._add_to_type_index(service)
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
                
    def _save_registry(self):
        """Save registry to file"""
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'services': [
                {
                    'service_id': s.service_id,
                    'service_name': s.service_name,
                    'version': s.version,
                    'endpoint': {
                        'host': s.endpoint.host,
                        'port': s.endpoint.port,
                        'protocol': s.endpoint.protocol,
                        'path': s.endpoint.path
                    },
                    'status': s.status.value,
                    'metadata': s.metadata,
                    'dependencies': s.dependencies,
                    'health_endpoint': s.health_endpoint
                }
                for s in self._services.values()
            ],
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_dependencies(self, service_id: str) -> List[str]:
        """Get dependencies for a service"""
        service = self._services.get(service_id)
        return service.dependencies if service else []
        
    def get_dependents(self, service_id: str) -> List[str]:
        """Get services that depend on this service"""
        return [
            s.service_id 
            for s in self._services.values() 
            if service_id in s.dependencies
        ]
        
    def get_status(self) -> Dict:
        """Get registry status"""
        with self._lock:
            return {
                'running': self._running,
                'total_services': len(self._services),
                'service_types': dict(self._service_types),
                'health_summary': {
                    'healthy': len([s for s in self._services.values() if s.status == ServiceStatus.HEALTHY]),
                    'degraded': len([s for s in self._services.values() if s.status == ServiceStatus.DEGRADED]),
                    'unhealthy': len([s for s in self._services.values() if s.status == ServiceStatus.UNHEALTHY]),
                    'unknown': len([s for s in self._services.values() if s.status == ServiceStatus.UNKNOWN])
                },
                'services': {
                    s.service_id: {
                        'name': s.service_name,
                        'status': s.status.value,
                        'endpoint': s.endpoint.url
                    }
                    for s in self._services.values()
                }
            }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the service registry singleton"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
        _service_registry.start()
    return _service_registry


if __name__ == "__main__":
    registry = get_service_registry()
    print(json.dumps(registry.get_status(), indent=2))
