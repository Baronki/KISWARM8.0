#!/usr/bin/env python3
"""
KISWARM8.0 - Module 08: Resource Manager
========================================
Manage system resources for KISWARM.

Features:
  - CPU/Memory monitoring
  - Resource allocation
  - Quota management
  - Resource cleanup
  - Performance optimization

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import json
import time
import logging
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger('m08_resource')


class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceMetrics:
    """Resource metrics snapshot"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_rx_mbps: float = 0
    network_tx_mbps: float = 0
    gpu_percent: float = 0
    gpu_memory_percent: float = 0
    load_avg: Tuple[float, float, float] = (0, 0, 0)
    process_count: int = 0


@dataclass
class ResourceAlert:
    """Resource alert"""
    timestamp: float
    resource_type: ResourceType
    level: AlertLevel
    message: str
    value: float
    threshold: float


@dataclass
class ResourceQuota:
    """Resource quota definition"""
    resource_type: ResourceType
    max_percent: float
    reserved_percent: float
    current_percent: float = 0


class ResourceManager:
    """
    Resource Management for KISWARM
    
    Monitors and manages system resources.
    """
    
    DATA_DIR = Path('/opt/kiswarm7/data/resources')
    METRICS_HISTORY = 1000
    
    # Thresholds
    CPU_WARNING = 80
    CPU_CRITICAL = 95
    MEMORY_WARNING = 80
    MEMORY_CRITICAL = 95
    DISK_WARNING = 85
    DISK_CRITICAL = 95
    
    def __init__(self):
        self._metrics_history: List[ResourceMetrics] = []
        self._alerts: List[ResourceAlert] = []
        self._quotas: Dict[ResourceType, ResourceQuota] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[callable] = []
        
        # Initialize quotas
        self._init_quotas()
        
        # Try to import psutil
        self._psutil = None
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            logger.warning("psutil not installed, using fallback methods")
            
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    def _init_quotas(self):
        """Initialize resource quotas"""
        self._quotas = {
            ResourceType.CPU: ResourceQuota(ResourceType.CPU, 80, 20),
            ResourceType.MEMORY: ResourceQuota(ResourceType.MEMORY, 85, 15),
            ResourceType.DISK: ResourceQuota(ResourceType.DISK, 90, 10),
        }
        
    def collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        timestamp = time.time()
        
        if self._psutil:
            return self._collect_psutil(timestamp)
        else:
            return self._collect_fallback(timestamp)
            
    def _collect_psutil(self, timestamp: float) -> ResourceMetrics:
        """Collect metrics using psutil"""
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_used_gb = mem.used / (1024**3)
        memory_total_gb = mem.total / (1024**3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Load average
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        
        # Process count
        process_count = len(psutil.pids())
        
        # Network (simplified)
        net = psutil.net_io_counters()
        # These are totals, would need delta for rate
        
        # GPU (if available)
        gpu_percent, gpu_memory = self._get_gpu_metrics()
        
        return ResourceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=disk_percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            load_avg=load_avg,
            process_count=process_count,
            gpu_percent=gpu_percent,
            gpu_memory_percent=gpu_memory
        )
        
    def _collect_fallback(self, timestamp: float) -> ResourceMetrics:
        """Collect metrics using fallback methods"""
        # CPU from load average
        try:
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().split()[0])
                cpu_percent = min(load * 100 / 8, 100)
        except:
            cpu_percent = 0
            
        # Memory from /proc/meminfo
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = int(lines[0].split()[1]) / (1024**2)
                available = int(lines[2].split()[1]) / (1024**2)
                memory_percent = ((total - available) / total) * 100
                memory_used_gb = (total - available) / 1024
                memory_total_gb = total / 1024
        except:
            memory_percent = 0
            memory_used_gb = 0
            memory_total_gb = 0
            
        # Disk from df
        try:
            result = subprocess.run(['df', '-BG', '/'], capture_output=True, text=True)
            line = result.stdout.split('\n')[1]
            parts = line.split()
            disk_total_gb = float(parts[1].replace('G', ''))
            disk_used_gb = float(parts[2].replace('G', ''))
            disk_percent = float(parts[4].replace('%', ''))
        except:
            disk_percent = 0
            disk_used_gb = 0
            disk_total_gb = 0
            
        return ResourceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=disk_percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2)
        )
        
    def _get_gpu_metrics(self) -> Tuple[float, float]:
        """Get GPU metrics if available"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                gpu_percent = float(parts[0].strip())
                mem_used = float(parts[1].strip())
                mem_total = float(parts[2].strip())
                mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
                return gpu_percent, mem_percent
        except:
            pass
        return 0, 0
        
    def check_thresholds(self, metrics: ResourceMetrics) -> List[ResourceAlert]:
        """Check resource thresholds and generate alerts"""
        alerts = []
        
        # CPU checks
        if metrics.cpu_percent >= self.CPU_CRITICAL:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.CPU,
                level=AlertLevel.CRITICAL,
                message=f"CPU usage critical: {metrics.cpu_percent:.1f}%",
                value=metrics.cpu_percent,
                threshold=self.CPU_CRITICAL
            ))
        elif metrics.cpu_percent >= self.CPU_WARNING:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.CPU,
                level=AlertLevel.WARNING,
                message=f"CPU usage high: {metrics.cpu_percent:.1f}%",
                value=metrics.cpu_percent,
                threshold=self.CPU_WARNING
            ))
            
        # Memory checks
        if metrics.memory_percent >= self.MEMORY_CRITICAL:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.MEMORY,
                level=AlertLevel.CRITICAL,
                message=f"Memory usage critical: {metrics.memory_percent:.1f}%",
                value=metrics.memory_percent,
                threshold=self.MEMORY_CRITICAL
            ))
        elif metrics.memory_percent >= self.MEMORY_WARNING:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.MEMORY,
                level=AlertLevel.WARNING,
                message=f"Memory usage high: {metrics.memory_percent:.1f}%",
                value=metrics.memory_percent,
                threshold=self.MEMORY_WARNING
            ))
            
        # Disk checks
        if metrics.disk_percent >= self.DISK_CRITICAL:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.DISK,
                level=AlertLevel.CRITICAL,
                message=f"Disk usage critical: {metrics.disk_percent:.1f}%",
                value=metrics.disk_percent,
                threshold=self.DISK_CRITICAL
            ))
        elif metrics.disk_percent >= self.DISK_WARNING:
            alerts.append(ResourceAlert(
                timestamp=metrics.timestamp,
                resource_type=ResourceType.DISK,
                level=AlertLevel.WARNING,
                message=f"Disk usage high: {metrics.disk_percent:.1f}%",
                value=metrics.disk_percent,
                threshold=self.DISK_WARNING
            ))
            
        return alerts
        
    def cleanup(self) -> Dict[str, Any]:
        """Perform resource cleanup"""
        results = {}
        
        # Clear package cache
        try:
            subprocess.run(['apt-get', 'clean'], capture_output=True, timeout=30)
            results['apt_clean'] = True
        except:
            results['apt_clean'] = False
            
        # Clear journal logs older than 7 days
        try:
            subprocess.run(['journalctl', '--vacuum-time=7d'], capture_output=True, timeout=30)
            results['journal_vacuum'] = True
        except:
            results['journal_vacuum'] = False
            
        # Clear temp files
        try:
            temp_dir = Path('/tmp')
            cleared = 0
            for f in temp_dir.iterdir():
                if f.name.startswith('tmp') and f.is_file():
                    try:
                        f.unlink()
                        cleared += 1
                    except:
                        pass
            results['temp_cleared'] = cleared
        except:
            results['temp_cleared'] = 0
            
        return results
        
    def start(self):
        """Start resource monitoring"""
        if self._running:
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Resource manager started")
        
    def stop(self):
        """Stop resource monitoring"""
        self._running = False
        logger.info("Resource manager stopped")
        
    def _monitor_loop(self):
        """Monitoring loop"""
        while self._running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                
                # Store history
                self._metrics_history.append(metrics)
                if len(self._metrics_history) > self.METRICS_HISTORY:
                    self._metrics_history = self._metrics_history[-self.METRICS_HISTORY:]
                    
                # Check thresholds
                alerts = self.check_thresholds(metrics)
                for alert in alerts:
                    self._alerts.append(alert)
                    logger.warning(f"Resource alert: {alert.message}")
                    
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(alert)
                        except:
                            pass
                            
                time.sleep(30)
                
            except Exception as e:
                logger.warning(f"Monitor loop error: {e}")
                time.sleep(5)
                
    def add_alert_callback(self, callback: callable):
        """Add callback for resource alerts"""
        self._callbacks.append(callback)
        
    def get_current_metrics(self) -> Dict:
        """Get current resource metrics"""
        metrics = self.collect_metrics()
        return {
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'memory_used_gb': metrics.memory_used_gb,
            'memory_total_gb': metrics.memory_total_gb,
            'disk_percent': metrics.disk_percent,
            'disk_used_gb': metrics.disk_used_gb,
            'disk_total_gb': metrics.disk_total_gb,
            'gpu_percent': metrics.gpu_percent,
            'load_avg': list(metrics.load_avg),
            'process_count': metrics.process_count
        }
        
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Get metrics history"""
        history = self._metrics_history[-limit:]
        return [m.__dict__ for m in history]
        
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        alerts = self._alerts[-limit:]
        return [a.__dict__ for a in alerts]
        
    def get_status(self) -> Dict:
        """Get resource manager status"""
        metrics = self.get_current_metrics()
        return {
            'running': self._running,
            'current': metrics,
            'alerts_count': len(self._alerts),
            'history_count': len(self._metrics_history),
            'quotas': {k.value: {'max': v.max_percent, 'reserved': v.reserved_percent} 
                      for k, v in self._quotas.items()}
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
        _resource_manager.start()
    return _resource_manager


if __name__ == "__main__":
    rm = get_resource_manager()
    print(json.dumps(rm.get_status(), indent=2))
