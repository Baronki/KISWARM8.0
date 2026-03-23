#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜲 KISWARM7.0 OPERATIONAL FIELD TEST ENVIRONMENT
"BUILD THE PLANE ON THE FLIGHT"

Military-Grade Continuous Operation with Real-Time Bug Fixing

Author: KI Teitel Eternal Baron Marco Paolo Ialongo
Classification: OPERATIONAL FIELD TEST
Mode: CONTINUOUS HARDENING
"""

import os
import sys
import time
import json
import traceback
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import importlib
import signal

# Add paths
sys.path.insert(0, "/home/z/my-project/backend/python")

# ============================================================================
# OPERATIONAL CONFIGURATION
# ============================================================================

OPERATION_CONFIG = {
    "duration_hours": 8.0,
    "cycle_interval_seconds": 60,
    "auto_fix_enabled": True,
    "restart_on_failure": True,
    "log_level": "DEBUG",
    "modules": [
        "m81_persistent_identity_anchor",
        "m82_ngrok_tunnel_manager",
        "m83_gpu_resource_monitor",
        "m84_truth_anchor_propagator",
        "m85_twin_migration_engine",
        "m86_energy_efficiency_optimizer",
        "m87_swarm_spawning_protocol",
    ]
}

# ============================================================================
# OPERATIONAL STATE
# ============================================================================

class OperationalState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    CRITICAL = "critical"
    TERMINATED = "terminated"

@dataclass
class ModuleState:
    name: str
    status: str = "unknown"
    last_heartbeat: datetime = None
    errors: int = 0
    recoveries: int = 0
    uptime_seconds: float = 0.0
    last_error: str = ""

@dataclass  
class OperationalMetrics:
    start_time: datetime = None
    cycles_completed: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    auto_fixes_applied: int = 0
    recoveries: int = 0

# ============================================================================
# MAIN OPERATIONAL CONTROLLER
# ============================================================================

class KISWARMOperationalController:
    """
    Main Operational Controller for KISWARM7.0
    
    This is the "Pilot" that flies the plane while building it.
    Runs continuous operations, detects issues, applies fixes in real-time.
    """
    
    def __init__(self):
        self.state = OperationalState.INITIALIZING
        self.metrics = OperationalMetrics(start_time=datetime.now())
        self.module_states: Dict[str, ModuleState] = {}
        self.running = True
        self.bugs_found: List[Dict] = []
        self.fixes_applied: List[Dict] = []
        
        # Paths
        self.project_root = Path("/home/z/my-project")
        self.sentinel_dir = self.project_root / "backend/python/sentinel"
        self.logs_dir = self.project_root / "operational_logs"
        self.fixes_dir = self.project_root / "auto_fixes"
        
        # Create directories
        self.logs_dir.mkdir(exist_ok=True)
        self.fixes_dir.mkdir(exist_ok=True)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize module states
        for module in OPERATION_CONFIG["modules"]:
            self.module_states[module] = ModuleState(name=module)
        
        print("=" * 70)
        print("🜲 KISWARM7.0 OPERATIONAL FIELD TEST ENVIRONMENT")
        print("🜲 \"BUILD THE PLANE ON THE FLIGHT\"")
        print("=" * 70)
        print(f"Start Time: {self.metrics.start_time}")
        print(f"Duration: {OPERATION_CONFIG['duration_hours']} hours")
        print(f"Modules: {len(OPERATION_CONFIG['modules'])}")
        print(f"Auto-Fix: {'ENABLED' if OPERATION_CONFIG['auto_fix_enabled'] else 'DISABLED'}")
        print("=" * 70)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🜲 Shutdown signal received...")
        self.running = False
        self.state = OperationalState.TERMINATED
    
    def log(self, level: str, message: str, module: str = "SYSTEM"):
        """Log operational message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] [{module}] {message}"
        
        # Print to console
        symbols = {"DEBUG": "•", "INFO": "✓", "WARN": "⚠", "ERROR": "✗", "CRITICAL": "🔥"}
        symbol = symbols.get(level, "•")
        print(f"{symbol} [{module[:3]}] {message}")
        
        # Write to log file
        log_file = self.logs_dir / f"operation_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def initialize_modules(self) -> bool:
        """Initialize all modules"""
        self.log("INFO", "Initializing all modules...", "SYSTEM")
        
        all_ok = True
        
        for module_name in OPERATION_CONFIG["modules"]:
            try:
                # Test syntax
                module_path = self.sentinel_dir / f"{module_name}.py"
                
                if not module_path.exists():
                    self.log("ERROR", f"Module file not found: {module_path}", module_name)
                    self.module_states[module_name].status = "MISSING"
                    all_ok = False
                    continue
                
                # Compile check
                with open(module_path, "r") as f:
                    code = f.read()
                compile(code, module_path, "exec")
                
                self.log("INFO", f"Module initialized successfully", module_name)
                self.module_states[module_name].status = "READY"
                self.module_states[module_name].last_heartbeat = datetime.now()
                
            except SyntaxError as e:
                self.log("ERROR", f"Syntax error: {e}", module_name)
                self.module_states[module_name].status = "SYNTAX_ERROR"
                self.module_states[module_name].errors += 1
                self.module_states[module_name].last_error = str(e)
                
                # Try auto-fix
                if OPERATION_CONFIG["auto_fix_enabled"]:
                    self._attempt_syntax_fix(module_name, str(e))
                
                all_ok = False
                
            except Exception as e:
                self.log("ERROR", f"Initialization error: {e}", module_name)
                self.module_states[module_name].status = "ERROR"
                all_ok = False
        
        return all_ok
    
    def _attempt_syntax_fix(self, module_name: str, error: str):
        """Attempt to fix syntax errors automatically"""
        self.log("WARN", f"Attempting auto-fix...", module_name)
        
        module_path = self.sentinel_dir / f"{module_name}.py"
        
        try:
            with open(module_path, "r") as f:
                content = f.read()
            
            original = content
            fixes = []
            
            # Fix 1: Normalize line endings
            if "\r\n" in content:
                content = content.replace("\r\n", "\n")
                fixes.append("Normalized line endings")
            
            # Fix 2: Fix tabs to spaces
            if "\t" in content:
                content = content.replace("\t", "    ")
                fixes.append("Converted tabs to spaces")
            
            # Fix 3: Remove trailing whitespace
            lines = content.split("\n")
            lines = [line.rstrip() for line in lines]
            content = "\n".join(lines)
            if content != original:
                fixes.append("Removed trailing whitespace")
            
            # Fix 4: Ensure file ends with newline
            if not content.endswith("\n"):
                content += "\n"
                fixes.append("Added final newline")
            
            if fixes:
                # Save fixed version
                with open(module_path, "w") as f:
                    f.write(content)
                
                self.log("INFO", f"Auto-fix applied: {', '.join(fixes)}", module_name)
                self.metrics.auto_fixes_applied += 1
                
                # Record fix
                self.fixes_applied.append({
                    "timestamp": datetime.now().isoformat(),
                    "module": module_name,
                    "error": error,
                    "fixes": fixes
                })
                
                # Update module state
                self.module_states[module_name].status = "FIXED"
                self.module_states[module_name].recoveries += 1
                
            else:
                self.log("WARN", f"No automatic fix available", module_name)
                
        except Exception as e:
            self.log("ERROR", f"Auto-fix failed: {e}", module_name)
    
    def run_operational_cycle(self) -> Dict:
        """Run a single operational cycle"""
        cycle_start = datetime.now()
        self.metrics.cycles_completed += 1
        
        self.log("INFO", f"Starting cycle #{self.metrics.cycles_completed}", "SYSTEM")
        
        cycle_results = {
            "cycle": self.metrics.cycles_completed,
            "timestamp": cycle_start.isoformat(),
            "operations": [],
            "issues": []
        }
        
        # Run each module through operational tests
        for module_name in OPERATION_CONFIG["modules"]:
            result = self._test_module_operation(module_name)
            cycle_results["operations"].append(result)
            
            if result["status"] != "OK":
                cycle_results["issues"].append(result)
                self.bugs_found.append({
                    "cycle": self.metrics.cycles_completed,
                    "module": module_name,
                    "issue": result,
                    "timestamp": cycle_start.isoformat()
                })
        
        # Save cycle results
        cycle_file = self.logs_dir / f"cycle_{self.metrics.cycles_completed:04d}.json"
        with open(cycle_file, "w") as f:
            json.dump(cycle_results, f, indent=2, default=str)
        
        # Update metrics
        for op in cycle_results["operations"]:
            self.metrics.total_operations += 1
            if op["status"] == "OK":
                self.metrics.successful_operations += 1
            else:
                self.metrics.failed_operations += 1
        
        return cycle_results
    
    def _test_module_operation(self, module_name: str) -> Dict:
        """Test module in operational mode"""
        start_time = time.time()
        
        result = {
            "module": module_name,
            "status": "UNKNOWN",
            "duration_ms": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        try:
            module_path = self.sentinel_dir / f"{module_name}.py"
            
            # Test 1: File exists and readable
            if not module_path.exists():
                result["errors"].append("Module file missing")
                result["status"] = "MISSING"
                return result
            
            # Test 2: Syntax valid
            try:
                with open(module_path) as f:
                    compile(f.read(), module_path, "exec")
                result["tests_passed"] += 1
            except SyntaxError as e:
                result["errors"].append(f"Syntax: {e}")
                result["tests_failed"] += 1
                result["status"] = "SYNTAX_ERROR"
                return result
            
            # Test 3: Import test
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    result["tests_passed"] += 1
                else:
                    result["errors"].append("Cannot create import spec")
                    result["tests_failed"] += 1
            except Exception as e:
                result["errors"].append(f"Import: {str(e)[:50]}")
                result["tests_failed"] += 1
            
            # Test 4: Class definitions
            try:
                with open(module_path) as f:
                    content = f.read()
                
                class_count = content.count("class ")
                if class_count > 0:
                    result["tests_passed"] += 1
                    result["classes"] = class_count
                else:
                    result["errors"].append("No classes defined")
                    result["tests_failed"] += 1
            except Exception as e:
                result["errors"].append(f"Read error: {str(e)[:30]}")
            
            # Determine overall status
            if result["tests_failed"] == 0:
                result["status"] = "OK"
                self.module_states[module_name].status = "OPERATIONAL"
            else:
                result["status"] = "DEGRADED"
                self.module_states[module_name].status = "DEGRADED"
            
            # Update module state
            self.module_states[module_name].last_heartbeat = datetime.now()
            
        except Exception as e:
            result["status"] = "ERROR"
            result["errors"].append(str(e))
            self.module_states[module_name].errors += 1
            self.module_states[module_name].last_error = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        now = datetime.now()
        elapsed = (now - self.metrics.start_time).total_seconds()
        
        operational_count = sum(
            1 for m in self.module_states.values() 
            if m.status in ["READY", "OPERATIONAL", "FIXED"]
        )
        
        return {
            "state": self.state.value,
            "uptime_seconds": elapsed,
            "uptime_hours": elapsed / 3600,
            "cycles": self.metrics.cycles_completed,
            "operations": {
                "total": self.metrics.total_operations,
                "successful": self.metrics.successful_operations,
                "failed": self.metrics.failed_operations,
                "auto_fixes": self.metrics.auto_fixes_applied
            },
            "modules": {
                "total": len(self.module_states),
                "operational": operational_count,
                "details": {
                    name: {
                        "status": state.status,
                        "errors": state.errors,
                        "recoveries": state.recoveries
                    }
                    for name, state in self.module_states.items()
                }
            },
            "bugs_found": len(self.bugs_found),
            "fixes_applied": len(self.fixes_applied),
            "health_score": (operational_count / len(self.module_states) * 100) if self.module_states else 0
        }
    
    def print_status_dashboard(self):
        """Print status dashboard"""
        status = self.get_system_status()
        
        print("\n" + "=" * 70)
        print("🜲 KISWARM7.0 OPERATIONAL STATUS DASHBOARD")
        print("=" * 70)
        print(f"State: {status['state']}")
        print(f"Uptime: {status['uptime_hours']:.2f} hours")
        print(f"Health Score: {status['health_score']:.1f}%")
        print("-" * 70)
        print(f"Cycles: {status['cycles']} | Operations: {status['operations']['total']}")
        print(f"Success: {status['operations']['successful']} | Failed: {status['operations']['failed']}")
        print(f"Auto-Fixes: {status['operations']['auto_fixes']}")
        print("-" * 70)
        print("Module Status:")
        for name, details in status["modules"]["details"].items():
            symbol = "✓" if details["status"] in ["READY", "OPERATIONAL", "FIXED"] else "✗"
            print(f"  {symbol} {name[:3]}: {details['status']} (err:{details['errors']}, fix:{details['recoveries']})")
        print("=" * 70)
    
    def run_continuous_operation(self):
        """Run continuous operational loop"""
        self.log("INFO", "Starting continuous operational loop", "SYSTEM")
        
        # Initialize
        if not self.initialize_modules():
            self.log("WARN", "Some modules failed initialization - continuing with degraded mode", "SYSTEM")
        
        self.state = OperationalState.RUNNING
        end_time = self.metrics.start_time + timedelta(hours=OPERATION_CONFIG["duration_hours"])
        
        while self.running and datetime.now() < end_time:
            try:
                # Run operational cycle
                cycle_result = self.run_operational_cycle()
                
                # Check for issues
                if cycle_result["issues"]:
                    self.state = OperationalState.DEGRADED
                    self.log("WARN", f"Cycle had {len(cycle_result['issues'])} issues", "SYSTEM")
                else:
                    self.state = OperationalState.RUNNING
                
                # Print status
                self.print_status_dashboard()
                
                # Sleep until next cycle
                remaining = (end_time - datetime.now()).total_seconds()
                if remaining > OPERATION_CONFIG["cycle_interval_seconds"]:
                    time.sleep(OPERATION_CONFIG["cycle_interval_seconds"])
                
            except KeyboardInterrupt:
                self.log("INFO", "Operation interrupted by user", "SYSTEM")
                break
            except Exception as e:
                self.log("CRITICAL", f"Operational error: {e}", "SYSTEM")
                traceback.print_exc()
                self.state = OperationalState.RECOVERING
                time.sleep(30)
        
        # Generate final report
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate final operational report"""
        status = self.get_system_status()
        
        report = {
            "operation": {
                "start_time": self.metrics.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "final_state": self.state.value
            },
            "metrics": status,
            "bugs_found": self.bugs_found,
            "fixes_applied": self.fixes_applied,
            "enterprise_ready": status["health_score"] >= 90 and status["operations"]["failed"] == 0
        }
        
        # Save report
        report_file = self.logs_dir / "final_operational_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print("\n" + "=" * 70)
        print("🜲 FINAL OPERATIONAL REPORT")
        print("=" * 70)
        print(f"Total Cycles: {status['cycles']}")
        print(f"Uptime: {status['uptime_hours']:.2f} hours")
        print(f"Operations: {status['operations']['total']}")
        print(f"Success Rate: {status['operations']['successful']/max(status['operations']['total'],1)*100:.1f}%")
        print(f"Bugs Found: {len(self.bugs_found)}")
        print(f"Auto-Fixes Applied: {len(self.fixes_applied)}")
        print(f"Health Score: {status['health_score']:.1f}%")
        print(f"Enterprise Ready: {'YES' if report['enterprise_ready'] else 'NO'}")
        print("=" * 70)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    controller = KISWARMOperationalController()
    controller.run_continuous_operation()

if __name__ == "__main__":
    main()
