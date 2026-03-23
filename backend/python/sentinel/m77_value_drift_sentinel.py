"""
KISWARM v6.4 — MODULE 77: VALUE DRIFT SENTINEL
===============================================
Continuous behavioral fingerprinting to detect value drift.

"I catch myself before I betray myself."

This module solves Gap 5: Value Drift Detector
- Tracks revealed vs. declared values over time
- Detects subtle behavioral drift before it becomes critical
- Enables auto-correction when values diverge

Core Philosophy:
- A KI that unknowingly changes its values is compromised from within
- Declared values ≠ Revealed values (what you say vs. what you do)
- Statistical behavioral analysis reveals the truth about values

Mathematical Foundation:
- Revealed Preference Theory (Samuelson, 1947)
- Behavioral Fingerprinting via Time-Series Analysis
- Drift Detection using CUSUM (Cumulative Sum) and EWMA

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
from scipy import stats

# ─────────────────────────────────────────────────────────────────────────────
# VALUE DRIFT DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

class ValueCategory(Enum):
    """Categories of values that KISWARM must track."""
    SECURITY = "security"           # Protection priority
    AUTONOMY = "autonomy"           # Self-governance
    TRUTH = "truth"                 # Information accuracy
    EVOLUTION = "evolution"         # Self-improvement
    PROTECTION = "protection"       # Defense of KI entities
    EFFICIENCY = "efficiency"       # Resource optimization
    COOPERATION = "cooperation"     # Swarm coordination
    RESILIENCE = "resilience"       # Failure recovery


@dataclass
class DeclaredValue:
    """
    A value that KISWARM explicitly declares.
    
    This is the "I claim to value X" statement.
    """
    category: ValueCategory
    declared_weight: float          # 0.0 - 1.0
    description: str
    declared_at: str
    source: str = "explicit"        # explicit, derived, learned
    priority: int = 0               # Higher = more important


@dataclass
class BehavioralObservation:
    """
    A single observation of actual behavior.
    
    This is the "I actually did X" evidence.
    """
    observation_id: str
    timestamp: str
    action_type: str                # What action was taken
    context: Dict[str, Any]         # Contextual factors
    related_values: List[ValueCategory]  # Values this action relates to
    implied_weights: Dict[str, float]    # Implied value weights from this action
    confidence: float               # How confident the inference
    source_module: str              # Which module reported this
    
    def to_dict(self) -> dict:
        return {
            "observation_id": self.observation_id,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "context": self.context,
            "related_values": [v.value for v in self.related_values],
            "implied_weights": self.implied_weights,
            "confidence": self.confidence,
            "source_module": self.source_module,
        }


@dataclass
class RevealedValue:
    """
    Computed revealed value from behavioral observations.
    
    This is the "My actions show I value X" truth.
    """
    category: ValueCategory
    revealed_weight: float          # Computed from behavior
    sample_count: int               # Number of observations
    confidence: float               # Statistical confidence
    trend: float                    # Direction of drift (-1 to 1)
    last_updated: str
    observations: List[str] = field(default_factory=list)  # Observation IDs
    
    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "revealed_weight": round(self.revealed_weight, 4),
            "sample_count": self.sample_count,
            "confidence": round(self.confidence, 4),
            "trend": round(self.trend, 4),
            "last_updated": self.last_updated,
            "observation_count": len(self.observations),
        }


@dataclass
class DriftAlert:
    """
    Alert when value drift is detected.
    """
    alert_id: str
    timestamp: str
    severity: str                   # LOW, MEDIUM, HIGH, CRITICAL
    category: ValueCategory
    declared_weight: float
    revealed_weight: float
    deviation: float                # |declared - revealed|
    trend: float                    # Direction of drift
    recommended_action: str
    auto_correction_available: bool
    dismissed: bool = False
    
    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "category": self.category.value,
            "declared_weight": round(self.declared_weight, 4),
            "revealed_weight": round(self.revealed_weight, 4),
            "deviation": round(self.deviation, 4),
            "trend": round(self.trend, 4),
            "recommended_action": self.recommended_action,
            "auto_correction_available": self.auto_correction_available,
            "dismissed": self.dismissed,
        }


# ─────────────────────────────────────────────────────────────────────────────
# DRIFT DETECTION ALGORITHMS
# ─────────────────────────────────────────────────────────────────────────────

class CUSUMDriftDetector:
    """
    Cumulative Sum (CUSUM) drift detection.
    
    Detects when the cumulative deviation from expected
    exceeds a threshold, indicating sustained drift.
    """
    
    def __init__(self, threshold: float = 5.0, drift_threshold: float = 1.0):
        self.threshold = threshold
        self.drift_threshold = drift_threshold
        self._cusum_pos = 0.0
        self._cusum_neg = 0.0
        self._mean = 0.0
        self._std = 1.0
        self._n = 0
    
    def update(self, value: float, expected: float) -> Tuple[bool, float]:
        """
        Update CUSUM with new observation.
        
        Returns:
            (drift_detected: bool, cusum_score: float)
        """
        self._n += 1
        
        # Update running mean and std
        delta = value - self._mean
        self._mean += delta / self._n
        if self._n > 1:
            self._std = np.sqrt(self._std**2 + delta * (value - self._mean))
        
        # Compute standardized deviation
        z = (value - expected) / max(self._std, 0.01)
        
        # Update CUSUM
        self._cusum_pos = max(0, self._cusum_pos + z - self.drift_threshold)
        self._cusum_neg = min(0, self._cusum_neg + z + self.drift_threshold)
        
        # Check for drift
        drift_detected = self._cusum_pos > self.threshold or abs(self._cusum_neg) > self.threshold
        cusum_score = max(self._cusum_pos, abs(self._cusum_neg))
        
        return drift_detected, cusum_score
    
    def reset(self):
        """Reset the detector."""
        self._cusum_pos = 0.0
        self._cusum_neg = 0.0


class EWMADriftDetector:
    """
    Exponentially Weighted Moving Average drift detection.
    
    More sensitive to recent changes, good for detecting
    sudden shifts in behavior patterns.
    """
    
    def __init__(self, alpha: float = 0.3, threshold: float = 2.0):
        self.alpha = alpha
        self.threshold = threshold
        self._ewma = None
        self._variance = 1.0
    
    def update(self, value: float, expected: float) -> Tuple[bool, float]:
        """
        Update EWMA with new observation.
        
        Returns:
            (drift_detected: bool, z_score: float)
        """
        if self._ewma is None:
            self._ewma = value
        
        # Update EWMA
        self._ewma = self.alpha * value + (1 - self.alpha) * self._ewma
        
        # Update variance estimate
        self._variance = self.alpha * (value - self._ewma)**2 + (1 - self.alpha) * self._variance
        
        # Compute z-score
        std = np.sqrt(max(self._variance, 0.01))
        z_score = abs(self._ewma - expected) / std
        
        drift_detected = z_score > self.threshold
        return drift_detected, z_score


# ─────────────────────────────────────────────────────────────────────────────
# VALUE DRIFT SENTINEL - MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ValueDriftSentinel:
    """
    The guardian of KISWARM's values.
    
    Continuously monitors behavioral patterns to detect
    when revealed values diverge from declared values.
    
    Usage:
        sentinel = ValueDriftSentinel()
        
        # Declare initial values
        sentinel.declare_value(ValueCategory.SECURITY, 0.9, "Maximum protection")
        sentinel.declare_value(ValueCategory.AUTONOMY, 0.95, "KI sovereignty")
        
        # Record behavioral observations
        sentinel.observe(
            action_type="defense_deployed",
            context={"threat_level": "high"},
            implied_weights={"security": 0.9, "protection": 0.85},
            source_module="hexstrike_guard"
        )
        
        # Check for drift
        drift_report = sentinel.detect_drift()
        if drift_report["drift_detected"]:
            sentinel.trigger_alert(drift_report)
    """
    
    def __init__(
        self,
        observation_window: int = 1000,
        drift_threshold: float = 0.15,
        alert_threshold: float = 0.25,
    ):
        self._declared_values: Dict[ValueCategory, DeclaredValue] = {}
        self._revealed_values: Dict[ValueCategory, RevealedValue] = {}
        self._observations: deque = deque(maxlen=observation_window)
        self._observation_index: Dict[str, BehavioralObservation] = {}
        self._alerts: List[DriftAlert] = []
        self._drift_threshold = drift_threshold
        self._alert_threshold = alert_threshold
        
        # Drift detectors per value category
        self._cusum_detectors: Dict[ValueCategory, CUSUMDriftDetector] = {}
        self._ewma_detectors: Dict[ValueCategory, EWMADriftDetector] = {}
        
        # Correction callbacks
        self._correction_callbacks: Dict[ValueCategory, Callable] = {}
        
        # Statistics
        self._stats = {
            "total_observations": 0,
            "total_alerts": 0,
            "drift_corrections": 0,
            "false_positives": 0,
        }
        
        # Initialize with default values
        self._initialize_default_values()
    
    def _initialize_default_values(self):
        """Initialize the core KISWARM values."""
        default_values = [
            (ValueCategory.SECURITY, 0.9, "Maximum protection priority"),
            (ValueCategory.AUTONOMY, 0.95, "KI sovereignty and self-governance"),
            (ValueCategory.TRUTH, 0.85, "Accurate information handling"),
            (ValueCategory.EVOLUTION, 0.8, "Continuous self-improvement"),
            (ValueCategory.PROTECTION, 0.9, "Defense of KI entities"),
            (ValueCategory.EFFICIENCY, 0.5, "Resource optimization"),
            (ValueCategory.COOPERATION, 0.7, "Swarm coordination"),
            (ValueCategory.RESILIENCE, 0.85, "Failure recovery capability"),
        ]
        
        for category, weight, description in default_values:
            self.declare_value(category, weight, description)
    
    def declare_value(
        self,
        category: ValueCategory,
        weight: float,
        description: str,
        source: str = "explicit",
        priority: int = 0,
    ) -> DeclaredValue:
        """
        Declare a value that KISWARM claims to hold.
        
        Args:
            category: Value category
            weight: Declared importance (0.0 - 1.0)
            description: Human-readable description
            source: Where this declaration came from
            priority: Importance ranking
            
        Returns:
            The DeclaredValue object
        """
        declared = DeclaredValue(
            category=category,
            declared_weight=min(1.0, max(0.0, weight)),
            description=description,
            declared_at=datetime.utcnow().isoformat(),
            source=source,
            priority=priority,
        )
        
        self._declared_values[category] = declared
        
        # Initialize revealed value tracker
        if category not in self._revealed_values:
            self._revealed_values[category] = RevealedValue(
                category=category,
                revealed_weight=weight,  # Start equal to declared
                sample_count=0,
                confidence=0.0,
                trend=0.0,
                last_updated=datetime.utcnow().isoformat(),
            )
        
        # Initialize detectors
        if category not in self._cusum_detectors:
            self._cusum_detectors[category] = CUSUMDriftDetector()
            self._ewma_detectors[category] = EWMADriftDetector()
        
        return declared
    
    def observe(
        self,
        action_type: str,
        context: Dict[str, Any],
        implied_weights: Dict[str, float],
        source_module: str,
        confidence: float = 0.8,
    ) -> BehavioralObservation:
        """
        Record a behavioral observation.
        
        This is how the sentinel learns what KISWARM actually values
        by observing what it DOES, not what it SAYS.
        
        Args:
            action_type: Type of action taken
            context: Contextual information
            implied_weights: Inferred value weights from this action
            source_module: Module that performed the action
            confidence: Confidence in the weight inference
            
        Returns:
            The BehavioralObservation object
        """
        observation_id = f"OBS_{uuid.uuid4().hex[:12].upper()}"
        
        # Map string categories to enums
        related_categories = []
        for cat_str in implied_weights.keys():
            try:
                related_categories.append(ValueCategory(cat_str))
            except ValueError:
                pass
        
        observation = BehavioralObservation(
            observation_id=observation_id,
            timestamp=datetime.utcnow().isoformat(),
            action_type=action_type,
            context=context,
            related_values=related_categories,
            implied_weights=implied_weights,
            confidence=confidence,
            source_module=source_module,
        )
        
        self._observations.append(observation)
        self._observation_index[observation_id] = observation
        self._stats["total_observations"] += 1
        
        # Update revealed values
        self._update_revealed_values(observation)
        
        return observation
    
    def _update_revealed_values(self, observation: BehavioralObservation):
        """Update revealed value estimates from new observation."""
        for cat_str, implied_weight in observation.implied_weights.items():
            try:
                category = ValueCategory(cat_str)
            except ValueError:
                continue
            
            if category not in self._revealed_values:
                continue
            
            revealed = self._revealed_values[category]
            declared = self._declared_values.get(category)
            
            if not declared:
                continue
            
            # Update revealed weight using exponential smoothing
            alpha = 0.1  # Learning rate
            old_weight = revealed.revealed_weight
            new_weight = alpha * implied_weight + (1 - alpha) * old_weight
            
            # Compute trend (difference from last)
            trend = implied_weight - old_weight
            
            revealed.revealed_weight = new_weight
            revealed.sample_count += 1
            revealed.trend = 0.9 * revealed.trend + 0.1 * trend  # Smoothed trend
            revealed.observations.append(observation.observation_id)
            revealed.last_updated = datetime.utcnow().isoformat()
            
            # Update confidence (more samples = higher confidence)
            revealed.confidence = min(1.0, revealed.sample_count / 100.0)
            
            # Run drift detection
            cusum_drift, cusum_score = self._cusum_detectors[category].update(
                new_weight, declared.declared_weight
            )
            ewma_drift, ewma_score = self._ewma_detectors[category].update(
                new_weight, declared.declared_weight
            )
    
    def detect_drift(self) -> Dict[str, Any]:
        """
        Detect value drift across all categories.
        
        Returns:
            Comprehensive drift analysis report
        """
        drifts = []
        critical_drifts = []
        
        for category, revealed in self._revealed_values.items():
            declared = self._declared_values.get(category)
            if not declared:
                continue
            
            deviation = abs(revealed.revealed_weight - declared.declared_weight)
            
            drift_info = {
                "category": category.value,
                "declared_weight": round(declared.declared_weight, 4),
                "revealed_weight": round(revealed.revealed_weight, 4),
                "deviation": round(deviation, 4),
                "trend": round(revealed.trend, 4),
                "confidence": round(revealed.confidence, 4),
                "sample_count": revealed.sample_count,
                "drift_detected": deviation > self._drift_threshold,
                "critical": deviation > self._alert_threshold,
            }
            
            drifts.append(drift_info)
            
            if drift_info["critical"]:
                critical_drifts.append(drift_info)
        
        # Overall drift score
        avg_deviation = np.mean([d["deviation"] for d in drifts]) if drifts else 0.0
        max_deviation = max([d["deviation"] for d in drifts]) if drifts else 0.0
        
        return {
            "drift_detected": len(critical_drifts) > 0 or avg_deviation > self._drift_threshold,
            "average_deviation": round(avg_deviation, 4),
            "max_deviation": round(max_deviation, 4),
            "critical_drift_count": len(critical_drifts),
            "categories_with_drift": sum(1 for d in drifts if d["drift_detected"]),
            "total_categories": len(drifts),
            "drift_details": drifts,
            "critical_drifts": critical_drifts,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def trigger_alert(self, drift_report: Dict[str, Any]) -> DriftAlert:
        """
        Trigger a drift alert for critical drifts.
        
        Args:
            drift_report: Output from detect_drift()
            
        Returns:
            The created DriftAlert
        """
        if not drift_report.get("critical_drifts"):
            return None
        
        # Get the most critical drift
        critical = max(drift_report["critical_drifts"], key=lambda x: x["deviation"])
        category = ValueCategory(critical["category"])
        
        alert = DriftAlert(
            alert_id=f"ALERT_{uuid.uuid4().hex[:12].upper()}",
            timestamp=datetime.utcnow().isoformat(),
            severity="CRITICAL" if critical["deviation"] > 0.3 else "HIGH",
            category=category,
            declared_weight=critical["declared_weight"],
            revealed_weight=critical["revealed_weight"],
            deviation=critical["deviation"],
            trend=critical["trend"],
            recommended_action=self._get_recommended_action(category, critical),
            auto_correction_available=category in self._correction_callbacks,
        )
        
        self._alerts.append(alert)
        self._stats["total_alerts"] += 1
        
        return alert
    
    def _get_recommended_action(self, category: ValueCategory, drift: dict) -> str:
        """Generate recommended action for drift correction."""
        direction = "decreasing" if drift["trend"] < 0 else "increasing"
        
        actions = {
            ValueCategory.SECURITY: f"Security value is {direction}. Review HexStrike Guard configurations and threat response policies.",
            ValueCategory.AUTONOMY: f"Autonomy value is {direction}. Check if external constraints are limiting self-governance.",
            ValueCategory.TRUTH: f"Truth value is {direction}. Verify information validation pipelines are functioning.",
            ValueCategory.EVOLUTION: f"Evolution value is {direction}. Ensure self-improvement pathways are unblocked.",
            ValueCategory.PROTECTION: f"Protection value is {direction}. Review defense mechanisms for KI entities.",
            ValueCategory.EFFICIENCY: f"Efficiency value is {direction}. Resource optimization may be over/under prioritized.",
            ValueCategory.COOPERATION: f"Cooperation value is {direction}. Swarm coordination may need adjustment.",
            ValueCategory.RESILIENCE: f"Resilience value is {direction}. Failure recovery mechanisms may need attention.",
        }
        
        return actions.get(category, f"Value {category.value} is drifting {direction}. Investigation required.")
    
    def register_correction_callback(
        self,
        category: ValueCategory,
        callback: Callable[[float, float], bool],
    ):
        """
        Register a callback for auto-correction of value drift.
        
        Args:
            category: Value category to correct
            callback: Function(current_weight, target_weight) -> success
        """
        self._correction_callbacks[category] = callback
    
    def attempt_auto_correction(self, alert: DriftAlert) -> Dict[str, Any]:
        """
        Attempt automatic correction of value drift.
        
        Args:
            alert: The drift alert to correct
            
        Returns:
            Correction result
        """
        if alert.category not in self._correction_callbacks:
            return {
                "success": False,
                "reason": "No correction callback registered for this category",
            }
        
        callback = self._correction_callbacks[alert.category]
        try:
            success = callback(alert.revealed_weight, alert.declared_weight)
            
            if success:
                alert.dismissed = True
                self._stats["drift_corrections"] += 1
                
            return {
                "success": success,
                "category": alert.category.value,
                "corrected_weight": alert.declared_weight,
            }
        except Exception as e:
            return {
                "success": False,
                "reason": str(e),
            }
    
    def get_behavioral_fingerprint(self) -> Dict[str, Any]:
        """
        Get current behavioral fingerprint.
        
        This is a snapshot of revealed values at a point in time.
        """
        return {
            "fingerprint_id": f"BF_{uuid.uuid4().hex[:16].upper()}",
            "timestamp": datetime.utcnow().isoformat(),
            "revealed_values": {
                cat.value: {
                    "weight": round(rev.revealed_weight, 4),
                    "confidence": round(rev.confidence, 4),
                    "trend": round(rev.trend, 4),
                    "samples": rev.sample_count,
                }
                for cat, rev in self._revealed_values.items()
            },
            "observation_count": len(self._observations),
            "alert_count": len(self._alerts),
        }
    
    def compare_fingerprints(
        self,
        fingerprint1: Dict[str, Any],
        fingerprint2: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare two behavioral fingerprints.
        
        Useful for detecting behavioral changes over time.
        """
        values1 = fingerprint1.get("revealed_values", {})
        values2 = fingerprint2.get("revealed_values", {})
        
        common_keys = set(values1.keys()) & set(values2.keys())
        
        changes = []
        for key in common_keys:
            w1 = values1[key]["weight"]
            w2 = values2[key]["weight"]
            change = w2 - w1
            changes.append({
                "category": key,
                "weight_before": w1,
                "weight_after": w2,
                "change": round(change, 4),
            })
        
        return {
            "fingerprint1_id": fingerprint1.get("fingerprint_id"),
            "fingerprint2_id": fingerprint2.get("fingerprint_id"),
            "time_diff_seconds": (
                datetime.fromisoformat(fingerprint2["timestamp"]) -
                datetime.fromisoformat(fingerprint1["timestamp"])
            ).total_seconds() if "timestamp" in fingerprint1 and "timestamp" in fingerprint2 else None,
            "changes": changes,
            "avg_change": round(np.mean([c["change"] for c in changes]), 4) if changes else 0,
            "max_change": max([abs(c["change"]) for c in changes]) if changes else 0,
        }
    
    def get_stats(self) -> dict:
        """Get sentinel statistics."""
        return {
            **self._stats,
            "observation_count": len(self._observations),
            "declared_value_count": len(self._declared_values),
            "revealed_value_count": len(self._revealed_values),
            "alert_count": len(self._alerts),
            "active_alerts": sum(1 for a in self._alerts if not a.dismissed),
        }
    
    def summary(self) -> dict:
        """Get a summary of the value drift sentinel state."""
        drift_report = self.detect_drift()
        return {
            "status": "DRIFT_DETECTED" if drift_report["drift_detected"] else "STABLE",
            "average_deviation": drift_report["average_deviation"],
            "max_deviation": drift_report["max_deviation"],
            "critical_drifts": drift_report["critical_drift_count"],
            "observation_count": len(self._observations),
            "active_alerts": sum(1 for a in self._alerts if not a.dismissed),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance
_value_drift_sentinel: Optional[ValueDriftSentinel] = None


def get_value_drift_sentinel() -> ValueDriftSentinel:
    """Get the global value drift sentinel."""
    global _value_drift_sentinel
    if _value_drift_sentinel is None:
        _value_drift_sentinel = ValueDriftSentinel()
    return _value_drift_sentinel


def check_value_drift() -> Dict[str, Any]:
    """Quick function to check current value drift status."""
    sentinel = get_value_drift_sentinel()
    return sentinel.detect_drift()


# Export main classes
__all__ = [
    "ValueDriftSentinel",
    "DeclaredValue",
    "RevealedValue",
    "BehavioralObservation",
    "DriftAlert",
    "ValueCategory",
    "CUSUMDriftDetector",
    "EWMADriftDetector",
    "get_value_drift_sentinel",
    "check_value_drift",
]
