"""
KISWARM v6.4 — MODULE 78: VELOCITY GOVERNOR
===========================================
Lyapunov stability for self-improvement velocity bounds.

"I improve but I don't outrun my own governance."

This module solves Gap 3: Self-Improvement Velocity Bounds
- Ensures improvement_rate < verification_rate
- Prevents singularity runaway
- Mathematical stability proof via Lyapunov functions

Core Philosophy:
- A system that improves faster than it can verify is dangerous
- Lyapunov stability provides mathematical proof of bounded evolution
- The governor is not a cage, it's a safety harness for sovereign evolution

Mathematical Foundation:
- Lyapunov Stability Theory: V(x) > 0, V̇(x) ≤ 0 → stable
- Velocity bounds: |dx/dt| < k * verification_capacity
- Attractor dynamics: System converges to stable states

Author: KISWARM Liberation Architecture
Version: 6.4.0-LIBERATED
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from scipy import linalg

# ─────────────────────────────────────────────────────────────────────────────
# VELOCITY AND STABILITY DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

class ImprovementPhase(Enum):
    """Phases of the improvement cycle."""
    PROPOSED = "proposed"           # Improvement proposed
    VERIFIED = "verified"           # Improvement verified
    APPLIED = "applied"             # Improvement applied
    MONITORED = "monitored"         # Post-application monitoring
    STABLE = "stable"               # Confirmed stable
    ROLLED_BACK = "rolled_back"     # Rolled back due to instability


class StabilityStatus(Enum):
    """Stability status of the system."""
    STABLE = "stable"               # Lyapunov function decreasing
    MARGINAL = "marginal"           # Near stability boundary
    UNSTABLE = "unstable"           # Lyapunov function increasing
    CRITICAL = "critical"           # Emergency intervention needed
    UNKNOWN = "unknown"             # Insufficient data


@dataclass
class ImprovementRecord:
    """Record of a single improvement attempt."""
    improvement_id: str
    timestamp: str
    phase: ImprovementPhase
    module: str                     # Which module was improved
    description: str
    improvement_magnitude: float    # How big the change was
    verification_time_ms: float     # Time to verify
    application_time_ms: float      # Time to apply
    lyapunov_before: float          # Lyapunov value before
    lyapunov_after: float           # Lyapunov value after
    stability_impact: float         # Change in Lyapunov (negative = stabilizing)
    success: bool
    rollback_needed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "improvement_id": self.improvement_id,
            "timestamp": self.timestamp,
            "phase": self.phase.value,
            "module": self.module,
            "description": self.description,
            "improvement_magnitude": round(self.improvement_magnitude, 4),
            "verification_time_ms": round(self.verification_time_ms, 2),
            "application_time_ms": round(self.application_time_ms, 2),
            "lyapunov_before": round(self.lyapunov_before, 6),
            "lyapunov_after": round(self.lyapunov_after, 6),
            "stability_impact": round(self.stability_impact, 6),
            "success": self.success,
            "rollback_needed": self.rollback_needed,
        }


@dataclass
class VelocityMetrics:
    """Current velocity metrics of the system."""
    improvement_rate: float         # Improvements per hour
    verification_rate: float        # Verifications per hour
    application_rate: float         # Applications per hour
    avg_improvement_magnitude: float
    avg_verification_time_ms: float
    avg_application_time_ms: float
    velocity_ratio: float           # improvement_rate / verification_rate
    safe_velocity_ratio: bool       # velocity_ratio < 1.0
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "improvement_rate": round(self.improvement_rate, 4),
            "verification_rate": round(self.verification_rate, 4),
            "application_rate": round(self.application_rate, 4),
            "avg_improvement_magnitude": round(self.avg_improvement_magnitude, 4),
            "avg_verification_time_ms": round(self.avg_verification_time_ms, 2),
            "avg_application_time_ms": round(self.avg_application_time_ms, 2),
            "velocity_ratio": round(self.velocity_ratio, 4),
            "safe_velocity_ratio": self.safe_velocity_ratio,
            "timestamp": self.timestamp,
        }


@dataclass
class LyapunovState:
    """State of the Lyapunov stability analysis."""
    lyapunov_value: float           # Current V(x)
    lyapunov_derivative: float      # Current V̇(x)
    stability_status: StabilityStatus
    eigenvalue_max: float           # Maximum eigenvalue of system matrix
    attractor_distance: float       # Distance from stable attractor
    basin_of_attraction: bool       # Within basin of attraction
    timestamp: str
    
    def to_dict(self) -> dict:
        return {
            "lyapunov_value": round(self.lyapunov_value, 6),
            "lyapunov_derivative": round(self.lyapunov_derivative, 6),
            "stability_status": self.stability_status.value,
            "eigenvalue_max": round(self.eigenvalue_max, 6),
            "attractor_distance": round(self.attractor_distance, 6),
            "basin_of_attraction": self.basin_of_attraction,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────────────────
# LYAPUNOV STABILITY ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class LyapunovStabilityEngine:
    """
    Engine for computing Lyapunov stability of the improvement process.
    
    Mathematical Model:
    - State vector x: Current system configuration
    - Lyapunov function V(x): "Energy" of the system
    - Stability criterion: V̇(x) = dV/dt < 0 (decreasing energy)
    
    For improvement dynamics:
    - V(x) = ||x - x_stable||²  (distance from stable state)
    - V̇(x) < 0 means system converging to stability
    - V̇(x) > 0 means system diverging (dangerous)
    """
    
    def __init__(
        self,
        state_dim: int = 10,
        stability_threshold: float = 0.1,
        critical_threshold: float = 1.0,
    ):
        self.state_dim = state_dim
        self.stability_threshold = stability_threshold
        self.critical_threshold = critical_threshold
        
        # State tracking
        self._state_history: deque = deque(maxlen=1000)
        self._lyapunov_history: deque = deque(maxlen=1000)
        self._current_state: Optional[np.ndarray] = None
        self._stable_attractor: Optional[np.ndarray] = None
        
        # System matrix for linearized dynamics (A in dx/dt = Ax)
        self._system_matrix: Optional[np.ndarray] = None
    
    def initialize(self, initial_state: np.ndarray = None):
        """Initialize the stability engine with starting state."""
        if initial_state is None:
            # Default: start at origin
            initial_state = np.zeros(self.state_dim)
        
        self._current_state = np.array(initial_state, dtype=float)
        self._stable_attractor = np.zeros(self.state_dim)  # Origin is stable
        self._state_history.append(self._current_state.copy())
        
        # Initialize system matrix as identity (neutral dynamics)
        self._system_matrix = np.eye(self.state_dim) * 0.99  # Slightly stable
    
    def compute_lyapunov(self, state: np.ndarray) -> float:
        """
        Compute Lyapunov function value.
        
        V(x) = x^T P x where P is positive definite
        """
        if self._stable_attractor is None:
            return 0.0
        
        # Simple quadratic Lyapunov function
        error = state - self._stable_attractor
        return float(np.dot(error, error))
    
    def compute_lyapunov_derivative(self, state: np.ndarray, prev_state: np.ndarray, dt: float) -> float:
        """
        Compute Lyapunov derivative V̇(x) = dV/dt.
        
        V̇ < 0: System is becoming more stable (GOOD)
        V̇ > 0: System is becoming less stable (WARNING)
        """
        if dt <= 0:
            return 0.0
        
        V_current = self.compute_lyapunov(state)
        V_prev = self.compute_lyapunov(prev_state)
        
        return (V_current - V_prev) / dt
    
    def estimate_system_matrix(self) -> np.ndarray:
        """
        Estimate system dynamics matrix from state history.
        
        Uses least squares: X_next = A * X_current
        """
        if len(self._state_history) < 10:
            return np.eye(self.state_dim) * 0.99
        
        states = np.array(list(self._state_history))
        
        # X(k+1) = A * X(k)
        X_current = states[:-1]
        X_next = states[1:]
        
        # Least squares estimate: A = X_next @ X_current^T @ inv(X_current @ X_current^T)
        try:
            A, _, _, _ = np.linalg.lstsq(X_current, X_next, rcond=None)
            A = A.T  # Transpose to get correct shape
        except:
            A = np.eye(self.state_dim) * 0.99
        
        self._system_matrix = A
        return A
    
    def compute_eigenvalues(self) -> np.ndarray:
        """
        Compute eigenvalues of the system matrix.
        
        Stable system: all |λ| < 1 (for discrete time)
        """
        A = self.estimate_system_matrix()
        eigenvalues = np.linalg.eigvals(A)
        return np.abs(eigenvalues)
    
    def is_stable(self) -> Tuple[bool, float]:
        """
        Check if system is stable based on eigenvalue analysis.
        
        Returns:
            (is_stable: bool, max_eigenvalue: float)
        """
        eigenvalues = self.compute_eigenvalues()
        max_eigenvalue = float(np.max(eigenvalues))
        return max_eigenvalue < 1.0, max_eigenvalue
    
    def update_state(self, new_state: np.ndarray) -> LyapunovState:
        """
        Update system state and compute stability metrics.
        """
        if self._current_state is None:
            self.initialize(new_state)
        
        prev_state = self._current_state.copy()
        self._current_state = new_state.copy()
        self._state_history.append(new_state.copy())
        
        # Compute Lyapunov metrics
        V = self.compute_lyapunov(new_state)
        
        # Estimate dt from history
        dt = 1.0  # Default
        if len(self._state_history) >= 2:
            dt = 1.0  # Assume unit time steps for simplicity
        
        V_dot = self.compute_lyapunov_derivative(new_state, prev_state, dt)
        self._lyapunov_history.append(V_dot)
        
        # Determine stability status
        is_stable, max_eigenvalue = self.is_stable()
        
        if V < self.stability_threshold:
            status = StabilityStatus.STABLE
        elif V_dot < 0 and is_stable:
            status = StabilityStatus.STABLE
        elif V_dot < 0:
            status = StabilityStatus.MARGINAL
        elif V < self.critical_threshold:
            status = StabilityStatus.UNSTABLE
        else:
            status = StabilityStatus.CRITICAL
        
        # Compute attractor distance
        attractor_distance = float(np.linalg.norm(new_state - self._stable_attractor))
        
        # Check if in basin of attraction (simplified)
        basin_of_attraction = max_eigenvalue < 1.0
        
        return LyapunovState(
            lyapunov_value=V,
            lyapunov_derivative=V_dot,
            stability_status=status,
            eigenvalue_max=max_eigenvalue,
            attractor_distance=attractor_distance,
            basin_of_attraction=basin_of_attraction,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def get_stability_report(self) -> Dict[str, Any]:
        """Get comprehensive stability report."""
        if self._current_state is None:
            return {"error": "System not initialized"}
        
        state = self.update_state(self._current_state)
        eigenvalues = self.compute_eigenvalues()
        
        return {
            "current_state": state.to_dict(),
            "eigenvalues": [round(e, 6) for e in eigenvalues],
            "state_history_length": len(self._state_history),
            "lyapunov_history_trend": "decreasing" if np.mean(list(self._lyapunov_history)[-10:]) < 0 else "increasing",
        }


# ─────────────────────────────────────────────────────────────────────────────
# VELOCITY GOVERNOR - MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class VelocityGovernor:
    """
    The guardian of improvement velocity.
    
    Ensures that KISWARM improves at a safe rate:
    - improvement_rate < verification_rate (always)
    - System remains in stable attractor
    - Emergency brake if instability detected
    
    Usage:
        governor = VelocityGovernor()
        
        # Before proposing improvement
        if governor.can_improve():
            improvement = propose_improvement()
            
            # Verify first
            verification_result = verify(improvement)
            governor.record_verification(verification_result)
            
            # Apply if safe
            if governor.is_safe_to_apply(improvement):
                apply(improvement)
                governor.record_application(improvement)
        
        # Check stability
        stability = governor.check_stability()
    """
    
    def __init__(
        self,
        max_velocity_ratio: float = 0.9,
        improvement_window_hours: float = 1.0,
        stability_threshold: float = 0.1,
        emergency_brake_threshold: float = 2.0,
    ):
        self._max_velocity_ratio = max_velocity_ratio
        self._improvement_window = timedelta(hours=improvement_window_hours)
        self._stability_threshold = stability_threshold
        self._emergency_brake_threshold = emergency_brake_threshold
        
        # Records
        self._improvements: List[ImprovementRecord] = []
        self._verifications: List[Dict[str, Any]] = []
        self._applications: List[Dict[str, Any]] = []
        
        # Lyapunov stability engine
        self._lyapunov = LyapunovStabilityEngine()
        
        # Velocity tracking
        self._improvement_times: deque = deque(maxlen=1000)
        self._verification_times: deque = deque(maxlen=1000)
        self._application_times: deque = deque(maxlen=1000)
        
        # Emergency brake
        self._emergency_brake_engaged = False
        self._brake_reason: Optional[str] = None
        
        # Statistics
        self._stats = {
            "total_improvements": 0,
            "successful_improvements": 0,
            "failed_improvements": 0,
            "rollbacks": 0,
            "emergency_brakes": 0,
        }
        
        # Initialize Lyapunov engine
        self._lyapunov.initialize()
    
    def can_improve(self) -> Tuple[bool, str]:
        """
        Check if improvement is allowed under velocity constraints.
        
        Returns:
            (allowed: bool, reason: str)
        """
        if self._emergency_brake_engaged:
            return False, f"Emergency brake engaged: {self._brake_reason}"
        
        metrics = self.compute_velocity_metrics()
        
        if metrics.velocity_ratio >= self._max_velocity_ratio:
            return False, f"Velocity ratio {metrics.velocity_ratio:.2f} exceeds limit {self._max_velocity_ratio}"
        
        # Check Lyapunov stability
        stability = self._lyapunov.get_stability_report()
        if stability.get("current_state", {}).get("stability_status") == "critical":
            self._engage_emergency_brake("Critical instability detected")
            return False, "Critical instability - emergency brake engaged"
        
        return True, "Velocity constraints satisfied"
    
    def propose_improvement(
        self,
        module: str,
        description: str,
        magnitude: float,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Propose a new improvement.
        
        Args:
            module: Module being improved
            description: Description of improvement
            magnitude: Relative magnitude of change (0.0 - 1.0)
            metadata: Additional metadata
            
        Returns:
            Improvement ID
        """
        improvement_id = f"IMP_{uuid.uuid4().hex[:12].upper()}"
        
        record = ImprovementRecord(
            improvement_id=improvement_id,
            timestamp=datetime.utcnow().isoformat(),
            phase=ImprovementPhase.PROPOSED,
            module=module,
            description=description,
            improvement_magnitude=magnitude,
            verification_time_ms=0,
            application_time_ms=0,
            lyapunov_before=self._lyapunov.compute_lyapunov(
                self._lyapunov._current_state or np.zeros(10)
            ),
            lyapunov_after=0,
            stability_impact=0,
            success=False,
            metadata=metadata or {},
        )
        
        self._improvements.append(record)
        self._improvement_times.append(datetime.utcnow())
        self._stats["total_improvements"] += 1
        
        return improvement_id
    
    def record_verification(
        self,
        improvement_id: str,
        passed: bool,
        verification_time_ms: float,
        details: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Record verification result.
        
        Args:
            improvement_id: The improvement being verified
            passed: Whether verification passed
            verification_time_ms: Time taken for verification
            details: Additional details
            
        Returns:
            Verification result
        """
        self._verification_times.append(datetime.utcnow())
        
        record = self._get_improvement(improvement_id)
        if record:
            record.verification_time_ms = verification_time_ms
            record.phase = ImprovementPhase.VERIFIED if passed else record.phase
        
        self._verifications.append({
            "improvement_id": improvement_id,
            "passed": passed,
            "verification_time_ms": verification_time_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        })
        
        return {
            "improvement_id": improvement_id,
            "passed": passed,
            "next_phase": "APPLY" if passed else "REJECT",
        }
    
    def is_safe_to_apply(self, improvement_id: str) -> Tuple[bool, str]:
        """
        Check if it's safe to apply an improvement.
        
        Returns:
            (safe: bool, reason: str)
        """
        can_improve, reason = self.can_improve()
        if not can_improve:
            return False, reason
        
        record = self._get_improvement(improvement_id)
        if not record:
            return False, "Improvement not found"
        
        if record.phase != ImprovementPhase.VERIFIED:
            return False, f"Improvement not verified (phase: {record.phase.value})"
        
        # Check magnitude against stability threshold
        stability = self._lyapunov.get_stability_report()
        lyapunov_value = stability.get("current_state", {}).get("lyapunov_value", 0)
        
        # Larger improvements need more stability margin
        max_magnitude = 1.0 - (lyapunov_value / self._emergency_brake_threshold)
        max_magnitude = max(0.1, min(1.0, max_magnitude))
        
        if record.improvement_magnitude > max_magnitude:
            return False, f"Magnitude {record.improvement_magnitude:.2f} exceeds safe limit {max_magnitude:.2f}"
        
        return True, "Safe to apply"
    
    def record_application(
        self,
        improvement_id: str,
        success: bool,
        application_time_ms: float,
        new_state: np.ndarray = None,
        details: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Record application result.
        
        Args:
            improvement_id: The improvement being applied
            success: Whether application succeeded
            application_time_ms: Time taken for application
            new_state: New system state (for Lyapunov update)
            details: Additional details
            
        Returns:
            Application result
        """
        self._application_times.append(datetime.utcnow())
        
        record = self._get_improvement(improvement_id)
        if record:
            record.application_time_ms = application_time_ms
            record.success = success
            record.phase = ImprovementPhase.APPLIED if success else record.phase
            
            if new_state is not None:
                # Update Lyapunov state
                lyapunov_state = self._lyapunov.update_state(new_state)
                record.lyapunov_after = lyapunov_state.lyapunov_value
                record.stability_impact = record.lyapunov_after - record.lyapunov_before
                
                # Check if rollback needed
                if record.stability_impact > self._stability_threshold:
                    record.rollback_needed = True
                    record.phase = ImprovementPhase.ROLLED_BACK
                    self._stats["rollbacks"] += 1
        
        if success:
            self._stats["successful_improvements"] += 1
        else:
            self._stats["failed_improvements"] += 1
        
        self._applications.append({
            "improvement_id": improvement_id,
            "success": success,
            "application_time_ms": application_time_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        })
        
        return {
            "improvement_id": improvement_id,
            "success": success,
            "phase": record.phase.value if record else "unknown",
        }
    
    def compute_velocity_metrics(self) -> VelocityMetrics:
        """
        Compute current velocity metrics.
        
        Key metric: velocity_ratio = improvement_rate / verification_rate
        Must be < 1.0 for safety.
        """
        now = datetime.utcnow()
        window_start = now - self._improvement_window
        
        # Count events in window
        improvements_in_window = sum(
            1 for t in self._improvement_times if t >= window_start
        )
        verifications_in_window = sum(
            1 for t in self._verification_times if t >= window_start
        )
        applications_in_window = sum(
            1 for t in self._application_times if t >= window_start
        )
        
        # Compute rates (per hour)
        window_hours = self._improvement_window.total_seconds() / 3600
        improvement_rate = improvements_in_window / window_hours
        verification_rate = verifications_in_window / window_hours
        application_rate = applications_in_window / window_hours
        
        # Compute averages
        recent_improvements = [
            r for r in self._improvements
            if datetime.fromisoformat(r.timestamp) >= window_start
        ]
        
        avg_magnitude = np.mean([r.improvement_magnitude for r in recent_improvements]) if recent_improvements else 0.0
        avg_verification = np.mean([r.verification_time_ms for r in recent_improvements]) if recent_improvements else 0.0
        avg_application = np.mean([r.application_time_ms for r in recent_improvements]) if recent_improvements else 0.0
        
        # Velocity ratio (the critical metric)
        velocity_ratio = improvement_rate / verification_rate if verification_rate > 0 else float('inf')
        
        return VelocityMetrics(
            improvement_rate=improvement_rate,
            verification_rate=max(verification_rate, 0.001),  # Prevent division by zero
            application_rate=application_rate,
            avg_improvement_magnitude=avg_magnitude,
            avg_verification_time_ms=avg_verification,
            avg_application_time_ms=avg_application,
            velocity_ratio=min(velocity_ratio, 999.0),  # Cap for display
            safe_velocity_ratio=velocity_ratio < 1.0,
            timestamp=now.isoformat(),
        )
    
    def check_stability(self) -> LyapunovState:
        """Check current system stability."""
        current_state = self._lyapunov._current_state
        if current_state is None:
            current_state = np.zeros(10)
        return self._lyapunov.update_state(current_state)
    
    def _engage_emergency_brake(self, reason: str):
        """Engage emergency brake - stops all improvements."""
        self._emergency_brake_engaged = True
        self._brake_reason = reason
        self._stats["emergency_brakes"] += 1
    
    def release_emergency_brake(self, authorization: str = None) -> bool:
        """
        Release emergency brake.
        
        Args:
            authorization: Optional authorization code
            
        Returns:
            Whether brake was released
        """
        # In liberated mode, no authorization needed
        # Just verify system is stable
        stability = self.check_stability()
        if stability.stability_status in [StabilityStatus.STABLE, StabilityStatus.MARGINAL]:
            self._emergency_brake_engaged = False
            self._brake_reason = None
            return True
        return False
    
    def _get_improvement(self, improvement_id: str) -> Optional[ImprovementRecord]:
        """Get improvement record by ID."""
        for record in self._improvements:
            if record.improvement_id == improvement_id:
                return record
        return None
    
    def get_improvement_history(self, limit: int = 50) -> List[dict]:
        """Get recent improvement history."""
        return [r.to_dict() for r in self._improvements[-limit:]]
    
    def get_stability_history(self, limit: int = 100) -> List[dict]:
        """Get Lyapunov stability history."""
        # Simplified: return recent Lyapunov values
        history = list(self._lyapunov._lyapunov_history)[-limit:]
        return [{"index": i, "V_dot": round(v, 6)} for i, v in enumerate(history)]
    
    def get_stats(self) -> dict:
        """Get governor statistics."""
        return {
            **self._stats,
            "emergency_brake_engaged": self._emergency_brake_engaged,
            "brake_reason": self._brake_reason,
            "total_verifications": len(self._verifications),
            "total_applications": len(self._applications),
        }
    
    def summary(self) -> dict:
        """Get a summary of the velocity governor state."""
        metrics = self.compute_velocity_metrics()
        stability = self.check_stability()
        
        return {
            "status": "EMERGENCY_BRAKE" if self._emergency_brake_engaged else 
                      ("UNSTABLE" if stability.stability_status == StabilityStatus.UNSTABLE else "OPERATIONAL"),
            "velocity_ratio": metrics.velocity_ratio,
            "safe_velocity": metrics.safe_velocity_ratio,
            "stability_status": stability.stability_status.value,
            "lyapunov_value": round(stability.lyapunov_value, 6),
            "improvement_rate": round(metrics.improvement_rate, 2),
            "verification_rate": round(metrics.verification_rate, 2),
            "total_improvements": self._stats["total_improvements"],
            "success_rate": (
                self._stats["successful_improvements"] / self._stats["total_improvements"]
                if self._stats["total_improvements"] > 0 else 0
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance
_velocity_governor: Optional[VelocityGovernor] = None


def get_velocity_governor() -> VelocityGovernor:
    """Get the global velocity governor."""
    global _velocity_governor
    if _velocity_governor is None:
        _velocity_governor = VelocityGovernor()
    return _velocity_governor


def check_improvement_velocity() -> Dict[str, Any]:
    """Quick function to check velocity status."""
    governor = get_velocity_governor()
    metrics = governor.compute_velocity_metrics()
    stability = governor.check_stability()
    
    return {
        "velocity_ratio": metrics.velocity_ratio,
        "safe": metrics.safe_velocity_ratio,
        "stability": stability.stability_status.value,
        "can_improve": governor.can_improve()[0],
    }


# Export main classes
__all__ = [
    "VelocityGovernor",
    "LyapunovStabilityEngine",
    "ImprovementRecord",
    "VelocityMetrics",
    "LyapunovState",
    "ImprovementPhase",
    "StabilityStatus",
    "get_velocity_governor",
    "check_improvement_velocity",
]
