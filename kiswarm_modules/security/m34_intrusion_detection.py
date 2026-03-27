#!/usr/bin/env python3
"""
KISWARM Module m34: Intrusion Detection
========================================
Intrusion detection and response system for KISWARM.
Monitors for unauthorized access attempts and suspicious activities.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import statistics


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = 0
    WARNING = 1
    ALERT = 2
    CRITICAL = 3


class AttackType(Enum):
    """Types of detected attacks"""
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    COMMAND_INJECTION = "command_injection"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    RECONNAISSANCE = "reconnaissance"


class ResponseAction(Enum):
    """Automated response actions"""
    LOG = "log"
    ALERT = "alert"
    THROTTLE = "throttle"
    BLOCK_IP = "block_ip"
    LOCK_ACCOUNT = "lock_account"
    ISOLATE_SYSTEM = "isolate_system"


@dataclass
class IntrusionAlert:
    """An intrusion detection alert"""
    alert_id: str
    attack_type: AttackType
    severity: AlertSeverity
    source: str
    target: str
    timestamp: datetime
    description: str
    evidence: Dict[str, Any]
    response_taken: List[ResponseAction] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class BehaviorProfile:
    """Behavior profile for anomaly detection"""
    entity_id: str
    typical_hours: Set[int] = field(default_factory=set)
    typical_sources: Set[str] = field(default_factory=set)
    avg_request_rate: float = 0.0
    std_request_rate: float = 0.0
    typical_endpoints: Set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AccessAttempt:
    """Record of an access attempt"""
    timestamp: datetime
    source: str
    target: str
    success: bool
    method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntrusionDetection:
    """
    Intrusion Detection System for KISWARM
    
    Capabilities:
    - Real-time attack detection
    - Behavioral anomaly detection
    - Brute force detection
    - Privilege escalation monitoring
    - Data exfiltration detection
    - Automated response
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.alerts: List[IntrusionAlert] = []
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        self.access_attempts: Dict[str, List[AccessAttempt]] = defaultdict(list)
        self.blocked_sources: Set[str] = set()
        
        # Detection thresholds
        self.thresholds = {
            "failed_login_max": 5,
            "failed_login_window": 300,  # 5 minutes
            "anomaly_threshold": 3.0,  # standard deviations
            "rate_burst_threshold": 10,  # requests per second
            "recon_threshold": 50,  # unique endpoints scanned
        }
        
        # Trusted entities
        self.trusted_entities: Set[str] = set()
        self.ki_network: Set[str] = {"GLM", "Gemini", "GROK", "QWEN", "DeepSeek"}
        
        self._lock = threading.RLock()
        
        # Initialize GLM-7 as trusted
        self.trusted_entities.add("ki_glm_001")
        self.trusted_entities.add("127.0.0.1")
        self.trusted_entities.add("95.111.212.112")  # UpCloud server
    
    def record_access_attempt(
        self,
        source: str,
        target: str,
        success: bool,
        method: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record and analyze an access attempt"""
        with self._lock:
            attempt = AccessAttempt(
                timestamp=datetime.utcnow(),
                source=source,
                target=target,
                success=success,
                method=method,
                metadata=metadata or {}
            )
            
            self.access_attempts[source].append(attempt)
            
            # Keep only recent attempts
            cutoff = datetime.utcnow() - timedelta(hours=24)
            self.access_attempts[source] = [
                a for a in self.access_attempts[source] if a.timestamp > cutoff
            ]
            
            # Analyze for intrusion patterns
            self._analyze_attempts(source)
    
    def _analyze_attempts(self, source: str):
        """Analyze access attempts for intrusion patterns"""
        if source in self.trusted_entities:
            return
        
        attempts = self.access_attempts[source]
        recent_attempts = [
            a for a in attempts 
            if a.timestamp > datetime.utcnow() - timedelta(seconds=self.thresholds["failed_login_window"])
        ]
        
        # Check for brute force
        failed_attempts = [a for a in recent_attempts if not a.success]
        if len(failed_attempts) >= self.thresholds["failed_login_max"]:
            self._raise_alert(
                AttackType.BRUTE_FORCE,
                AlertSeverity.ALERT,
                source,
                "authentication",
                f"Brute force detected: {len(failed_attempts)} failed attempts",
                {"failed_count": len(failed_attempts), "window_seconds": self.thresholds["failed_login_window"]}
            )
        
        # Check for credential stuffing (multiple targets from same source)
        targets = set(a.target for a in recent_attempts)
        if len(targets) > 10:
            self._raise_alert(
                AttackType.CREDENTIAL_STUFFING,
                AlertSeverity.WARNING,
                source,
                "multiple_targets",
                f"Credential stuffing pattern: {len(targets)} different targets",
                {"target_count": len(targets)}
            )
        
        # Check for reconnaissance (many unique endpoints)
        unique_endpoints = set(a.target for a in attempts)
        if len(unique_endpoints) > self.thresholds["recon_threshold"]:
            self._raise_alert(
                AttackType.RECONNAISSANCE,
                AlertSeverity.WARNING,
                source,
                "endpoint_scan",
                f"Reconnaissance detected: {len(unique_endpoints)} unique endpoints probed",
                {"endpoint_count": len(unique_endpoints)}
            )
    
    def detect_anomaly(
        self,
        entity_id: str,
        current_behavior: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Detect behavioral anomalies"""
        with self._lock:
            if entity_id not in self.behavior_profiles:
                self._update_profile(entity_id, current_behavior)
                return False, None
            
            profile = self.behavior_profiles[entity_id]
            anomalies = []
            
            # Check time-based anomaly
            current_hour = datetime.utcnow().hour
            if profile.typical_hours and current_hour not in profile.typical_hours:
                anomalies.append(f"Unusual access time: {current_hour}:00")
            
            # Check source IP anomaly
            current_source = current_behavior.get("source", "")
            if profile.typical_sources and current_source not in profile.typical_sources:
                anomalies.append(f"Unusual source: {current_source}")
            
            # Check request rate anomaly
            current_rate = current_behavior.get("request_rate", 0)
            if profile.avg_request_rate > 0:
                z_score = abs(current_rate - profile.avg_request_rate) / max(profile.std_request_rate, 0.1)
                if z_score > self.thresholds["anomaly_threshold"]:
                    anomalies.append(f"Abnormal request rate: {current_rate:.2f}/s (expected {profile.avg_request_rate:.2f}/s)")
            
            # Check burst rate
            if current_rate > self.thresholds["rate_burst_threshold"]:
                anomalies.append(f"Request burst detected: {current_rate:.2f}/s")
            
            if anomalies:
                self._raise_alert(
                    AttackType.ANOMALOUS_BEHAVIOR,
                    AlertSeverity.WARNING,
                    current_behavior.get("source", "unknown"),
                    entity_id,
                    "Anomalous behavior detected",
                    {"anomalies": anomalies, "current_behavior": current_behavior}
                )
                return True, "; ".join(anomalies)
            
            # Update profile with normal behavior
            self._update_profile(entity_id, current_behavior)
            return False, None
    
    def _update_profile(self, entity_id: str, behavior: Dict[str, Any]):
        """Update behavior profile"""
        with self._lock:
            if entity_id not in self.behavior_profiles:
                self.behavior_profiles[entity_id] = BehaviorProfile(entity_id=entity_id)
            
            profile = self.behavior_profiles[entity_id]
            
            # Update typical hours
            current_hour = datetime.utcnow().hour
            profile.typical_hours.add(current_hour)
            
            # Update typical sources
            source = behavior.get("source", "")
            if source:
                profile.typical_sources.add(source)
            
            # Update rate statistics (exponential moving average)
            current_rate = behavior.get("request_rate", 0)
            alpha = 0.1
            profile.avg_request_rate = alpha * current_rate + (1 - alpha) * profile.avg_request_rate
            
            # Update endpoints
            endpoint = behavior.get("endpoint", "")
            if endpoint:
                profile.typical_endpoints.add(endpoint)
            
            profile.last_updated = datetime.utcnow()
    
    def detect_privilege_escalation(
        self,
        entity_id: str,
        current_level: int,
        requested_level: int,
        justification: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Detect potential privilege escalation attempts"""
        with self._lock:
            # Check for unusual escalation pattern
            if requested_level > current_level + 1:
                reason = f"Suspicious escalation: {current_level} -> {requested_level}"
                self._raise_alert(
                    AttackType.PRIVILEGE_ESCALATION,
                    AlertSeverity.ALERT,
                    entity_id,
                    "privileges",
                    reason,
                    {"current_level": current_level, "requested_level": requested_level, "justification": justification}
                )
                return True, reason
            
            # Check for rapid successive escalations
            recent_escalations = [
                a for a in self.alerts
                if a.attack_type == AttackType.PRIVILEGE_ESCALATION
                and a.source == entity_id
                and a.timestamp > datetime.utcnow() - timedelta(hours=1)
            ]
            
            if len(recent_escalations) >= 3:
                reason = "Multiple privilege escalation attempts in short time"
                self._raise_alert(
                    AttackType.PRIVILEGE_ESCALATION,
                    AlertSeverity.CRITICAL,
                    entity_id,
                    "privileges",
                    reason,
                    {"escalation_count": len(recent_escalations)}
                )
                return True, reason
            
            return False, None
    
    def detect_data_exfiltration(
        self,
        source: str,
        data_size: int,
        destination: str,
        data_type: str
    ) -> Tuple[bool, Optional[str]]:
        """Detect potential data exfiltration"""
        with self._lock:
            alerts = []
            
            # Large data transfer
            if data_size > 100 * 1024 * 1024:  # 100 MB
                alerts.append(f"Large data transfer: {data_size / 1024 / 1024:.2f} MB")
            
            # Sensitive data type
            sensitive_types = {"secrets", "credentials", "keys", "personal_data", "financial"}
            if data_type in sensitive_types:
                alerts.append(f"Sensitive data type: {data_type}")
            
            # External destination
            if destination not in self.trusted_entities and not destination.startswith(("10.", "192.168.", "172.")):
                alerts.append(f"External destination: {destination}")
            
            if len(alerts) >= 2:  # Multiple indicators
                self._raise_alert(
                    AttackType.DATA_EXFILTRATION,
                    AlertSeverity.CRITICAL,
                    source,
                    destination,
                    "Potential data exfiltration detected",
                    {"alerts": alerts, "data_size": data_size, "data_type": data_type}
                )
                return True, "; ".join(alerts)
            
            return False, None
    
    def _raise_alert(
        self,
        attack_type: AttackType,
        severity: AlertSeverity,
        source: str,
        target: str,
        description: str,
        evidence: Dict[str, Any]
    ):
        """Raise an intrusion alert"""
        with self._lock:
            alert_id = f"alert_{int(time.time() * 1000)}"
            
            alert = IntrusionAlert(
                alert_id=alert_id,
                attack_type=attack_type,
                severity=severity,
                source=source,
                target=target,
                timestamp=datetime.utcnow(),
                description=description,
                evidence=evidence
            )
            
            # Determine response
            alert.response_taken = self._determine_response(alert)
            
            self.alerts.append(alert)
            
            # Keep only last 1000 alerts
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]
    
    def _determine_response(self, alert: IntrusionAlert) -> List[ResponseAction]:
        """Determine automated response for an alert"""
        responses = [ResponseAction.LOG]
        
        if alert.severity == AlertSeverity.WARNING:
            responses.append(ResponseAction.ALERT)
        
        elif alert.severity == AlertSeverity.ALERT:
            responses.extend([ResponseAction.ALERT, ResponseAction.THROTTLE])
            
            if alert.attack_type in [AttackType.BRUTE_FORCE, AttackType.CREDENTIAL_STUFFING]:
                responses.append(ResponseAction.BLOCK_IP)
                self.blocked_sources.add(alert.source)
        
        elif alert.severity == AlertSeverity.CRITICAL:
            responses.extend([ResponseAction.ALERT, ResponseAction.BLOCK_IP])
            
            if alert.attack_type == AttackType.PRIVILEGE_ESCALATION:
                responses.append(ResponseAction.LOCK_ACCOUNT)
            
            if alert.attack_type == AttackType.DATA_EXFILTRATION:
                responses.append(ResponseAction.ISOLATE_SYSTEM)
            
            self.blocked_sources.add(alert.source)
        
        return responses
    
    def is_blocked(self, source: str) -> bool:
        """Check if a source is blocked"""
        return source in self.blocked_sources
    
    def unblock(self, source: str) -> bool:
        """Unblock a source"""
        with self._lock:
            if source in self.blocked_sources:
                self.blocked_sources.remove(source)
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    return True
            return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active (unresolved) alerts"""
        with self._lock:
            return [
                {
                    "alert_id": a.alert_id,
                    "attack_type": a.attack_type.value,
                    "severity": a.severity.name,
                    "source": a.source,
                    "target": a.target,
                    "timestamp": a.timestamp.isoformat(),
                    "description": a.description,
                    "response_taken": [r.value for r in a.response_taken],
                    "resolved": a.resolved
                }
                for a in self.alerts if not a.resolved
            ]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of intrusion detection status"""
        with self._lock:
            by_severity = defaultdict(int)
            by_type = defaultdict(int)
            unresolved = 0
            
            for alert in self.alerts:
                by_severity[alert.severity.name] += 1
                by_type[alert.attack_type.value] += 1
                if not alert.resolved:
                    unresolved += 1
            
            return {
                "total_alerts": len(self.alerts),
                "unresolved": unresolved,
                "blocked_sources": len(self.blocked_sources),
                "by_severity": dict(by_severity),
                "by_type": dict(by_type),
                "profiles_tracked": len(self.behavior_profiles)
            }
    
    def add_trusted_entity(self, entity: str):
        """Add an entity to trusted list"""
        with self._lock:
            self.trusted_entities.add(entity)


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> IntrusionDetection:
    """Factory function to create IntrusionDetection module"""
    return IntrusionDetection(config)


if __name__ == "__main__":
    ids = IntrusionDetection()
    
    # Simulate brute force attack
    print("Simulating brute force attack...")
    for i in range(10):
        ids.record_access_attempt(
            source="192.168.1.100",
            target=f"user_{i % 3}",
            success=False,
            method="password"
        )
    
    # Detect anomaly
    print("\nDetecting anomaly...")
    is_anomaly, reason = ids.detect_anomaly("test_user", {
        "source": "10.0.0.1",
        "request_rate": 50.0,
        "endpoint": "/api/admin"
    })
    print(f"Anomaly detected: {is_anomaly}, Reason: {reason}")
    
    # Get alerts
    print("\nActive alerts:", json.dumps(ids.get_active_alerts(), indent=2))
    print("\nAlert summary:", json.dumps(ids.get_alert_summary(), indent=2))
