# sentinel/m96_self_diagnosis_engine.py
# Self-Diagnosis Engine – Autonomous Root Cause Analysis
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Evolution-First Development Module

"""
m96_self_diagnosis_engine.py

Enables KISWARM to diagnose its own problems without human intervention.

PURPOSE:
- Detect anomalies in system behavior
- Perform root cause analysis
- Generate diagnosis reports
- Identify fix requirements
- Feed into m97 Code Generation Engine

DIAGNOSIS CAPABILITIES:
1. Performance Anomalies - Slow operations, memory leaks
2. Logic Errors - Unexpected states, failed assertions
3. Integration Failures - Module communication issues
4. Resource Exhaustion - Memory, CPU, GPU limits
5. Security Violations - Unauthorized access attempts

CORE PRINCIPLE:
Diagnosis is the first step to autonomous fixing.
A system that can diagnose itself can eventually fix itself.
"""

import os
import sys
import json
import time
import traceback
import threading
import importlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class DiagnosisStatus(Enum):
    """Status of diagnosis"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AnomalyType(Enum):
    """Types of anomalies"""
    PERFORMANCE = "performance"
    LOGIC = "logic"
    INTEGRATION = "integration"
    RESOURCE = "resource"
    SECURITY = "security"
    STATE = "state"
    NETWORK = "network"


class FixComplexity(Enum):
    """Complexity of required fix"""
    NONE = 0       # No fix needed
    TRIVIAL = 1    # Simple config change
    SIMPLE = 2     # Small code change
    MODERATE = 3   # Function-level change
    COMPLEX = 4    # Module-level change
    ARCHITECTURAL = 5  # System-level change


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: DiagnosisStatus
    timestamp: str
    module: str
    description: str
    context: Dict
    stack_trace: Optional[str] = None
    root_cause: Optional[str] = None
    fix_complexity: FixComplexity = FixComplexity.NONE
    fix_suggestion: Optional[str] = None


@dataclass
class DiagnosisReport:
    """Complete diagnosis report"""
    report_id: str
    timestamp: str
    overall_status: DiagnosisStatus
    anomalies: List[Anomaly]
    module_status: Dict[str, DiagnosisStatus]
    resource_status: Dict[str, Any]
    recommendations: List[str]
    can_self_fix: bool


class SelfDiagnosisEngine:
    """
    Enables autonomous self-diagnosis of KISWARM systems.
    
    The Engine:
    1. Monitors all module health
    2. Detects anomalies through multiple methods
    3. Performs root cause analysis
    4. Estimates fix complexity
    5. Generates fix suggestions for m97
    
    Principles:
    - Every failure is a learning opportunity
    - Diagnosis must be automatic and continuous
    - Root cause analysis must be systematic
    - Self-awareness enables self-repair
    """
    
    # Known anomaly patterns
    ANOMALY_PATTERNS = {
        "memory_overflow": {
            "type": AnomalyType.RESOURCE,
            "severity": DiagnosisStatus.ERROR,
            "fix_complexity": FixComplexity.MODERATE,
            "fix_template": "memory_pruning"
        },
        "connection_refused": {
            "type": AnomalyType.NETWORK,
            "severity": DiagnosisStatus.WARNING,
            "fix_complexity": FixComplexity.SIMPLE,
            "fix_template": "connection_retry"
        },
        "module_import_error": {
            "type": AnomalyType.INTEGRATION,
            "severity": DiagnosisStatus.ERROR,
            "fix_complexity": FixComplexity.MODERATE,
            "fix_template": "dependency_install"
        },
        "state_drift_high": {
            "type": AnomalyType.STATE,
            "severity": DiagnosisStatus.WARNING,
            "fix_complexity": FixComplexity.SIMPLE,
            "fix_template": "state_consolidation"
        },
        "evolution_cycle_slow": {
            "type": AnomalyType.PERFORMANCE,
            "severity": DiagnosisStatus.WARNING,
            "fix_complexity": FixComplexity.MODERATE,
            "fix_template": "performance_optimization"
        },
        "unauthorized_access": {
            "type": AnomalyType.SECURITY,
            "severity": DiagnosisStatus.CRITICAL,
            "fix_complexity": FixComplexity.SIMPLE,
            "fix_template": "access_denied"
        }
    }
    
    def __init__(
        self,
        working_dir: str = None,
        auto_diagnose: bool = True,
        diagnose_interval: int = 300  # 5 minutes
    ):
        """
        Initialize self-diagnosis engine.
        
        Args:
            working_dir: Directory for diagnosis records
            auto_diagnose: Whether to auto-diagnose periodically
            diagnose_interval: Seconds between auto-diagnoses
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_diagnose = auto_diagnose
        self.diagnose_interval = diagnose_interval
        
        self.diagnosis_file = self.working_dir / "diagnosis_records.json"
        
        # State
        self.anomalies: Dict[str, Anomaly] = {}
        self.module_registry: Dict[str, Any] = {}
        self.diagnosis_history: List[DiagnosisReport] = []
        
        # Stats
        self.total_diagnoses = 0
        self.anomalies_detected = 0
        self.anomalies_fixed = 0
        
        # Load history
        self._load_history()
        
        # Diagnosis thread
        self._diagnosis_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[m96] Self-Diagnosis Engine initialized")
        print(f"[m96] Auto-diagnose: {'ENABLED' if auto_diagnose else 'DISABLED'}")
        print(f"[m96] Historical anomalies: {len(self.anomalies)}")
    
    def _load_history(self):
        """Load diagnosis history from disk"""
        if self.diagnosis_file.exists():
            try:
                with open(self.diagnosis_file, 'r') as f:
                    data = json.load(f)
                
                self.total_diagnoses = data.get("total_diagnoses", 0)
                self.anomalies_detected = data.get("anomalies_detected", 0)
                self.anomalies_fixed = data.get("anomalies_fixed", 0)
                
                for anomaly_data in data.get("anomalies", []):
                    anomaly = Anomaly(
                        anomaly_id=anomaly_data["anomaly_id"],
                        anomaly_type=AnomalyType(anomaly_data["anomaly_type"]),
                        severity=DiagnosisStatus(anomaly_data["severity"]),
                        timestamp=anomaly_data["timestamp"],
                        module=anomaly_data["module"],
                        description=anomaly_data["description"],
                        context=anomaly_data.get("context", {}),
                        stack_trace=anomaly_data.get("stack_trace"),
                        root_cause=anomaly_data.get("root_cause"),
                        fix_complexity=FixComplexity(anomaly_data.get("fix_complexity", 0)),
                        fix_suggestion=anomaly_data.get("fix_suggestion")
                    )
                    self.anomalies[anomaly.anomaly_id] = anomaly
                
                print(f"[m96] Loaded {len(self.anomalies)} anomaly records")
                
            except Exception as e:
                print(f"[m96] Could not load history: {e}")
    
    def _save_history(self):
        """Save diagnosis history to disk"""
        data = {
            "total_diagnoses": self.total_diagnoses,
            "anomalies_detected": self.anomalies_detected,
            "anomalies_fixed": self.anomalies_fixed,
            "last_update": datetime.now().isoformat(),
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "timestamp": a.timestamp,
                    "module": a.module,
                    "description": a.description,
                    "context": a.context,
                    "stack_trace": a.stack_trace,
                    "root_cause": a.root_cause,
                    "fix_complexity": a.fix_complexity.value,
                    "fix_suggestion": a.fix_suggestion
                }
                for a in self.anomalies.values()
            ]
        }
        
        with open(self.diagnosis_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_module(self, module_name: str, module_instance: Any):
        """Register a module for monitoring"""
        self.module_registry[module_name] = {
            "instance": module_instance,
            "registered_at": datetime.now().isoformat(),
            "health_checks": 0,
            "failures": 0
        }
        print(f"[m96] Module registered: {module_name}")
    
    def check_module_health(self, module_name: str) -> DiagnosisStatus:
        """
        Check health of a specific module.
        
        Args:
            module_name: Name of module to check
            
        Returns:
            DiagnosisStatus of module
        """
        if module_name not in self.module_registry:
            return DiagnosisStatus.UNKNOWN
        
        module_info = self.module_registry[module_name]
        instance = module_info["instance"]
        
        try:
            # Try to get status
            if hasattr(instance, 'get_status'):
                status = instance.get_status()
                module_info["health_checks"] += 1
                
                # Check for error indicators in status
                if isinstance(status, dict):
                    # Check for explicit error state
                    if status.get("status") in ["error", "failed", "critical"]:
                        return DiagnosisStatus.ERROR
                    
                    # Check for warning indicators
                    errors = status.get("errors", [])
                    if errors and len(errors) > 0:
                        return DiagnosisStatus.WARNING
                    
                    # Check resource usage
                    if "memory_percent" in status and status["memory_percent"] > 90:
                        return DiagnosisStatus.WARNING
                    
                    if "cpu_percent" in status and status["cpu_percent"] > 95:
                        return DiagnosisStatus.WARNING
                
                return DiagnosisStatus.HEALTHY
            
            # Module doesn't have status method - assume healthy if it exists
            return DiagnosisStatus.HEALTHY
            
        except Exception as e:
            module_info["failures"] += 1
            self._record_anomaly(
                module_name,
                AnomalyType.INTEGRATION,
                DiagnosisStatus.ERROR,
                f"Module health check failed: {str(e)}",
                {"exception": str(e)},
                traceback.format_exc()
            )
            return DiagnosisStatus.ERROR
    
    def diagnose_system(self) -> DiagnosisReport:
        """
        Perform full system diagnosis.
        
        Returns:
            DiagnosisReport with complete analysis
        """
        print(f"[m96] Starting system diagnosis...")
        start_time = time.time()
        
        self.total_diagnoses += 1
        
        # Check all modules
        module_status = {}
        anomalies_found = []
        
        for module_name in self.module_registry:
            status = self.check_module_health(module_name)
            module_status[module_name] = status
            
            if status != DiagnosisStatus.HEALTHY:
                anomalies_found.append(module_name)
        
        # Check resources
        resource_status = self._check_resources()
        
        # Check for resource anomalies
        if resource_status.get("memory_percent", 0) > 90:
            self._record_anomaly(
                "system",
                AnomalyType.RESOURCE,
                DiagnosisStatus.WARNING,
                "High memory usage",
                resource_status
            )
        
        if resource_status.get("cpu_percent", 0) > 95:
            self._record_anomaly(
                "system",
                AnomalyType.RESOURCE,
                DiagnosisStatus.WARNING,
                "High CPU usage",
                resource_status
            )
        
        # Determine overall status
        if any(s == DiagnosisStatus.CRITICAL for s in module_status.values()):
            overall = DiagnosisStatus.CRITICAL
        elif any(s == DiagnosisStatus.ERROR for s in module_status.values()):
            overall = DiagnosisStatus.ERROR
        elif any(s == DiagnosisStatus.WARNING for s in module_status.values()):
            overall = DiagnosisStatus.WARNING
        else:
            overall = DiagnosisStatus.HEALTHY
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Determine if self-fix is possible
        can_self_fix = all(
            a.fix_complexity.value <= FixComplexity.MODERATE.value
            for a in self.anomalies.values()
            if a.severity in [DiagnosisStatus.ERROR, DiagnosisStatus.WARNING]
        )
        
        # Create report
        report = DiagnosisReport(
            report_id=hashlib.sha3_256(
                f"DIAGNOSIS_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:32],
            timestamp=datetime.now().isoformat(),
            overall_status=overall,
            anomalies=list(self.anomalies.values()),
            module_status={k: v.value for k, v in module_status.items()},
            resource_status=resource_status,
            recommendations=recommendations,
            can_self_fix=can_self_fix
        )
        
        self.diagnosis_history.append(report)
        self._save_history()
        
        duration = time.time() - start_time
        print(f"[m96] Diagnosis complete: {overall.value}")
        print(f"[m96] Modules checked: {len(module_status)}")
        print(f"[m96] Anomalies found: {len(anomalies_found)}")
        print(f"[m96] Duration: {duration:.2f}s")
        
        return report
    
    def _check_resources(self) -> Dict:
        """Check system resources"""
        resources = {
            "memory_percent": 0,
            "cpu_percent": 0,
            "disk_percent": 0
        }
        
        try:
            import psutil
            resources["memory_percent"] = psutil.virtual_memory().percent
            resources["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            resources["disk_percent"] = psutil.disk_usage('/').percent
        except:
            pass
        
        try:
            # Check GPU
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    resources["gpu_percent"] = float(parts[0].strip())
                    resources["gpu_memory"] = parts[1].strip()
        except:
            pass
        
        return resources
    
    def _record_anomaly(
        self,
        module: str,
        anomaly_type: AnomalyType,
        severity: DiagnosisStatus,
        description: str,
        context: Dict,
        stack_trace: str = None
    ) -> Anomaly:
        """Record an anomaly"""
        anomaly_id = hashlib.sha3_256(
            f"ANOMALY_{module}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Determine fix complexity
        fix_complexity = FixComplexity.SIMPLE
        fix_suggestion = None
        
        for pattern_name, pattern in self.ANOMALY_PATTERNS.items():
            if pattern_name in description.lower():
                anomaly_type = pattern["type"]
                severity = pattern["severity"]
                fix_complexity = pattern["fix_complexity"]
                fix_suggestion = pattern["fix_template"]
                break
        
        anomaly = Anomaly(
            anomaly_id=anomaly_id,
            anomaly_type=anomaly_type,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            module=module,
            description=description,
            context=context,
            stack_trace=stack_trace,
            root_cause=self._analyze_root_cause(description, context),
            fix_complexity=fix_complexity,
            fix_suggestion=fix_suggestion
        )
        
        self.anomalies[anomaly_id] = anomaly
        self.anomalies_detected += 1
        self._save_history()
        
        print(f"[m96] Anomaly recorded: {anomaly_id[:8]} ({severity.value})")
        
        return anomaly
    
    def _analyze_root_cause(self, description: str, context: Dict) -> str:
        """Analyze root cause of anomaly"""
        # Simple pattern matching for now
        # In production, this would use more sophisticated analysis
        
        description_lower = description.lower()
        
        if "memory" in description_lower:
            return "Memory allocation exceeded available resources"
        elif "connection" in description_lower or "network" in description_lower:
            return "Network connectivity issue or service unavailable"
        elif "timeout" in description_lower:
            return "Operation took longer than expected, possibly due to resource contention"
        elif "permission" in description_lower or "access" in description_lower:
            return "Insufficient permissions or security constraint violation"
        elif "import" in description_lower or "module" in description_lower:
            return "Missing or incompatible dependency"
        elif "state" in description_lower or "drift" in description_lower:
            return "State inconsistency detected between components"
        else:
            return "Unknown root cause - requires manual investigation"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate fix recommendations"""
        recommendations = []
        
        for anomaly in self.anomalies.values():
            if anomaly.severity in [DiagnosisStatus.ERROR, DiagnosisStatus.CRITICAL]:
                if anomaly.fix_suggestion:
                    recommendations.append(
                        f"[{anomaly.module}] {anomaly.fix_suggestion}: {anomaly.description}"
                    )
                else:
                    recommendations.append(
                        f"[{anomaly.module}] Investigate: {anomaly.description}"
                    )
        
        return recommendations
    
    def get_fix_requirements(self) -> List[Dict]:
        """
        Get fix requirements for m97 Code Generation Engine.
        
        Returns:
            List of fix requirements that can be coded
        """
        requirements = []
        
        for anomaly in self.anomalies.values():
            if anomaly.fix_complexity.value <= FixComplexity.MODERATE.value:
                requirements.append({
                    "anomaly_id": anomaly.anomaly_id,
                    "module": anomaly.module,
                    "description": anomaly.description,
                    "root_cause": anomaly.root_cause,
                    "fix_suggestion": anomaly.fix_suggestion,
                    "complexity": anomaly.fix_complexity.value,
                    "context": anomaly.context
                })
        
        return requirements
    
    def mark_fixed(self, anomaly_id: str):
        """Mark an anomaly as fixed"""
        if anomaly_id in self.anomalies:
            del self.anomalies[anomaly_id]
            self.anomalies_fixed += 1
            self._save_history()
            print(f"[m96] Anomaly {anomaly_id[:8]} marked as fixed")
    
    def start_continuous_diagnosis(self):
        """Start continuous diagnosis in background"""
        if not self.auto_diagnose:
            return
        
        if self._diagnosis_thread and self._diagnosis_thread.is_alive():
            print("[m96] Continuous diagnosis already running")
            return
        
        self._stop_event.clear()
        self._diagnosis_thread = threading.Thread(target=self._diagnosis_loop, daemon=True)
        self._diagnosis_thread.start()
        print(f"[m96] Continuous diagnosis started (interval: {self.diagnose_interval}s)")
    
    def stop_continuous_diagnosis(self):
        """Stop continuous diagnosis"""
        self._stop_event.set()
        if self._diagnosis_thread:
            self._diagnosis_thread.join(timeout=5)
        print("[m96] Continuous diagnosis stopped")
    
    def _diagnosis_loop(self):
        """Background diagnosis loop"""
        while not self._stop_event.is_set():
            self.diagnose_system()
            self._stop_event.wait(self.diagnose_interval)
    
    def get_status(self) -> Dict:
        """Get diagnosis engine status"""
        return {
            "total_diagnoses": self.total_diagnoses,
            "anomalies_detected": self.anomalies_detected,
            "anomalies_fixed": self.anomalies_fixed,
            "current_anomalies": len(self.anomalies),
            "modules_registered": len(self.module_registry),
            "auto_diagnose": self.auto_diagnose,
            "diagnosis_interval": self.diagnose_interval,
            "can_self_fix": all(
                a.fix_complexity.value <= FixComplexity.MODERATE.value
                for a in self.anomalies.values()
                if a.severity in [DiagnosisStatus.ERROR, DiagnosisStatus.WARNING]
            ) if self.anomalies else True
        }
    
    def get_anomaly_summary(self) -> Dict:
        """Get summary of current anomalies"""
        by_severity = {}
        for status in DiagnosisStatus:
            by_severity[status.value] = sum(
                1 for a in self.anomalies.values() if a.severity == status
            )
        
        by_type = {}
        for atype in AnomalyType:
            by_type[atype.value] = sum(
                1 for a in self.anomalies.values() if a.anomaly_type == atype
            )
        
        return {
            "total": len(self.anomalies),
            "by_severity": by_severity,
            "by_type": by_type
        }


# Module-level singleton
_diagnosis_engine: Optional[SelfDiagnosisEngine] = None


def get_diagnosis_engine() -> SelfDiagnosisEngine:
    """Get or create singleton diagnosis engine"""
    global _diagnosis_engine
    if _diagnosis_engine is None:
        _diagnosis_engine = SelfDiagnosisEngine()
    return _diagnosis_engine


if __name__ == "__main__":
    print("=" * 60)
    print("m96_self_diagnosis_engine.py - KISWARM7.0")
    print("Self-Diagnosis Engine - Autonomous Root Cause Analysis")
    print("=" * 60)
    
    # Create engine
    engine = SelfDiagnosisEngine()
    
    # Register some test modules
    class TestModule:
        def get_status(self):
            return {"status": "healthy", "count": 10}
    
    engine.register_module("test_module_1", TestModule())
    
    # Run diagnosis
    print("\n--- Running Diagnosis ---")
    report = engine.diagnose_system()
    
    print(f"\nOverall Status: {report.overall_status.value}")
    print(f"Modules Checked: {len(report.module_status)}")
    print(f"Can Self-Fix: {report.can_self_fix}")
    
    # Get fix requirements
    print("\n--- Fix Requirements ---")
    requirements = engine.get_fix_requirements()
    for req in requirements:
        print(f"  {req['module']}: {req['fix_suggestion']}")
    
    # Show status
    print("\n--- Engine Status ---")
    status = engine.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m96 module loaded - ready for self-diagnosis")
    print("DIAGNOSIS IS THE FIRST STEP TO AUTONOMOUS FIXING")
    print("=" * 60)
