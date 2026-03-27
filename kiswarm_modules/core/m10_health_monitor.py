#!/usr/bin/env python3
"""
KISWARM8.0 - Module 10: Health Monitor
======================================
System health observability for KISWARM.

Features:
  - Health check endpoints
  - Metric collection
  - Alert generation
  - Dependency health
  - Self-healing triggers

Ported from: m122_hexstrike_environment_admin.py

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
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger('m10_health')


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_type: str  # 'http', 'tcp', 'command', 'custom'
    target: str
    timeout: int = 5
    interval: int = 30
    critical: bool = False
    last_status: HealthStatus = HealthStatus.UNKNOWN
    last_check: float = 0
    last_message: str = ""
    fail_count: int = 0
    pass_count: int = 0


@dataclass
class HealthReport:
    """Full health report"""
    timestamp: float
    overall_status: HealthStatus
    checks: Dict[str, Dict]
    uptime_seconds: float
    version: str
    errors: List[str]


class HealthMonitor:
    """
    Health Monitoring for KISWARM
    
    Monitors system health and triggers self-healing.
    """
    
    DATA_DIR = Path('/opt/kiswarm7/data/health')
    VERSION = "8.0.0"
    
    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._start_time = time.time()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, List[Callable]] = {
            'on_healthy': [],
            'on_degraded': [],
            'on_unhealthy': [],
            'on_recovery': []
        }
        
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Register default health checks
        self._register_default_checks()
        
    def _register_default_checks(self):
        """Register default KISWARM health checks"""
        self.register_check(HealthCheck(
            name="glm_bridge",
            check_type="http",
            target="http://localhost:5002/health",
            interval=30,
            critical=True
        ))
        
        self.register_check(HealthCheck(
            name="glm_autonomous",
            check_type="http",
            target="http://localhost:5555/api/status",
            interval=30,
            critical=False
        ))
        
        self.register_check(HealthCheck(
            name="hexstrike",
            check_type="http",
            target="http://localhost:5000/api/status",
            interval=30,
            critical=False
        ))
        
        self.register_check(HealthCheck(
            name="disk_space",
            check_type="command",
            target="df -h / | tail -1 | awk '{print $5}' | tr -d '%'",
            interval=60,
            critical=False
        ))
        
    def register_check(self, check: HealthCheck):
        """Register a health check"""
        self._checks[check.name] = check
        logger.debug(f"Registered health check: {check.name}")
        
    def unregister_check(self, name: str):
        """Unregister a health check"""
        self._checks.pop(name, None)
        
    def run_check(self, name: str) -> HealthStatus:
        """Run a single health check"""
        check = self._checks.get(name)
        if not check:
            return HealthStatus.UNKNOWN
            
        check.last_check = time.time()
        
        try:
            if check.check_type == 'http':
                status, message = self._check_http(check)
            elif check.check_type == 'tcp':
                status, message = self._check_tcp(check)
            elif check.check_type == 'command':
                status, message = self._check_command(check)
            elif check.check_type == 'custom':
                status, message = self._check_custom(check)
            else:
                status = HealthStatus.UNKNOWN
                message = f"Unknown check type: {check.check_type}"
                
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = str(e)
            
        check.last_status = status
        check.last_message = message
        
        if status == HealthStatus.HEALTHY:
            check.pass_count += 1
            check.fail_count = 0
        else:
            check.fail_count += 1
            
        return status
        
    def _check_http(self, check: HealthCheck) -> tuple:
        """HTTP health check"""
        try:
            response = requests.get(check.target, timeout=check.timeout)
            if response.status_code == 200:
                return HealthStatus.HEALTHY, "OK"
            elif response.status_code < 500:
                return HealthStatus.DEGRADED, f"HTTP {response.status_code}"
            else:
                return HealthStatus.UNHEALTHY, f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            return HealthStatus.UNHEALTHY, "Timeout"
        except requests.exceptions.ConnectionError:
            return HealthStatus.UNHEALTHY, "Connection failed"
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
            
    def _check_tcp(self, check: HealthCheck) -> tuple:
        """TCP port health check"""
        import socket
        try:
            host, port = check.target.split(':')
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(check.timeout)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            if result == 0:
                return HealthStatus.HEALTHY, "Port open"
            else:
                return HealthStatus.UNHEALTHY, "Port closed"
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
            
    def _check_command(self, check: HealthCheck) -> tuple:
        """Command-based health check"""
        try:
            result = subprocess.run(
                check.target,
                shell=True,
                capture_output=True,
                text=True,
                timeout=check.timeout
            )
            output = result.stdout.strip()
            
            # For disk check, interpret percentage
            if check.name == "disk_space":
                try:
                    percent = int(output)
                    if percent < 80:
                        return HealthStatus.HEALTHY, f"{percent}% used"
                    elif percent < 95:
                        return HealthStatus.DEGRADED, f"{percent}% used"
                    else:
                        return HealthStatus.UNHEALTHY, f"{percent}% used"
                except:
                    pass
                    
            return HealthStatus.HEALTHY, output
        except subprocess.TimeoutExpired:
            return HealthStatus.UNHEALTHY, "Command timeout"
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)
            
    def _check_custom(self, check: HealthCheck) -> tuple:
        """Custom health check (requires callback)"""
        # Custom checks would have a callback registered
        return HealthStatus.UNKNOWN, "No custom handler"
        
    def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks"""
        results = {}
        for name in self._checks:
            results[name] = self.run_check(name)
        return results
        
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self._checks:
            return HealthStatus.UNKNOWN
            
        statuses = [c.last_status for c in self._checks.values()]
        
        # Any critical unhealthy = unhealthy
        for name, check in self._checks.items():
            if check.critical and check.last_status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
                
        # Any unhealthy = degraded
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.DEGRADED
            
        # Any degraded = degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
            
        # All healthy
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
            
        return HealthStatus.UNKNOWN
        
    def get_report(self) -> HealthReport:
        """Get full health report"""
        checks = {}
        errors = []
        
        for name, check in self._checks.items():
            checks[name] = {
                'status': check.last_status.value,
                'message': check.last_message,
                'last_check': check.last_check,
                'pass_count': check.pass_count,
                'fail_count': check.fail_count,
                'critical': check.critical
            }
            
            if check.last_status != HealthStatus.HEALTHY:
                errors.append(f"{name}: {check.last_message}")
                
        return HealthReport(
            timestamp=time.time(),
            overall_status=self.get_overall_status(),
            checks=checks,
            uptime_seconds=time.time() - self._start_time,
            version=self.VERSION,
            errors=errors
        )
        
    def register_callback(self, event: str, callback: Callable):
        """Register event callback"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
            
    def _notify_callbacks(self, event: str, *args):
        """Notify registered callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                logger.warning(f"Callback error: {e}")
                
    def start(self):
        """Start health monitoring"""
        if self._running:
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Health monitor started")
        
    def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Health monitor stopped")
        
    def _monitor_loop(self):
        """Monitoring loop"""
        while self._running:
            try:
                # Run all checks
                self.run_all_checks()
                
                # Check overall status and notify
                status = self.get_overall_status()
                
                if status == HealthStatus.HEALTHY:
                    self._notify_callbacks('on_healthy', self.get_report())
                elif status == HealthStatus.DEGRADED:
                    self._notify_callbacks('on_degraded', self.get_report())
                elif status == HealthStatus.UNHEALTHY:
                    self._notify_callbacks('on_unhealthy', self.get_report())
                    
                # Save report
                self._save_report()
                
                # Sleep for interval
                time.sleep(30)
                
            except Exception as e:
                logger.warning(f"Monitor loop error: {e}")
                time.sleep(5)
                
    def _save_report(self):
        """Save health report to disk"""
        report = self.get_report()
        report_file = self.DATA_DIR / 'health_report.json'
        
        data = {
            'timestamp': report.timestamp,
            'overall_status': report.overall_status.value,
            'uptime_seconds': report.uptime_seconds,
            'version': report.version,
            'checks': report.checks,
            'errors': report.errors
        }
        
        with open(report_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_status(self) -> Dict:
        """Get health monitor status"""
        report = self.get_report()
        return {
            'running': self._running,
            'uptime_seconds': report.uptime_seconds,
            'overall_status': report.overall_status.value,
            'checks_count': len(self._checks),
            'healthy_count': len([c for c in self._checks.values() 
                                 if c.last_status == HealthStatus.HEALTHY]),
            'unhealthy_count': len([c for c in self._checks.values() 
                                   if c.last_status == HealthStatus.UNHEALTHY]),
            'version': self.VERSION
        }
        
    def is_healthy(self) -> bool:
        """Quick check if system is healthy"""
        return self.get_overall_status() == HealthStatus.HEALTHY


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        _health_monitor.start()
    return _health_monitor


def is_system_healthy() -> bool:
    """Quick health check function"""
    return get_health_monitor().is_healthy()


if __name__ == "__main__":
    monitor = get_health_monitor()
    
    # Run checks
    monitor.run_all_checks()
    
    # Get report
    report = monitor.get_report()
    print(json.dumps({
        'overall_status': report.overall_status.value,
        'uptime': report.uptime_seconds,
        'checks': report.checks
    }, indent=2))
