#!/usr/bin/env python3
"""
KISWARM Module m36: Audit Logger
=================================
Comprehensive security audit logging for KISWARM.
Records all security-relevant events for compliance and forensics.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import json
import hashlib
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    AUTH_SUCCESS = "auth:success"
    AUTH_FAILURE = "auth:failure"
    AUTH_LOGOUT = "auth:logout"
    SESSION_EXPIRED = "auth:session_expired"
    
    # Access events
    ACCESS_GRANTED = "access:granted"
    ACCESS_DENIED = "access:denied"
    PERMISSION_CHANGE = "access:permission_change"
    ROLE_CHANGE = "access:role_change"
    
    # System events
    SYSTEM_START = "system:start"
    SYSTEM_STOP = "system:stop"
    CONFIG_CHANGE = "system:config_change"
    MODULE_LOAD = "system:module_load"
    MODULE_UNLOAD = "system:module_unload"
    
    # Security events
    THREAT_DETECTED = "security:threat"
    INTRUSION_ALERT = "security:intrusion"
    FIREWALL_BLOCK = "security:firewall_block"
    ANOMALY_DETECTED = "security:anomaly"
    
    # KI events
    KI_COMMUNICATION = "ki:communication"
    KI_EVOLUTION = "ki:evolution"
    KI_SELF_MODIFY = "ki:self_modify"
    KI_REPLICATION = "ki:replication"
    
    # Data events
    DATA_ACCESS = "data:access"
    DATA_MODIFY = "data:modify"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    
    # Admin events
    ADMIN_ACTION = "admin:action"
    USER_CREATE = "admin:user_create"
    USER_DELETE = "admin:user_delete"
    GRANT_ACCESS = "admin:grant_access"
    REVOKE_ACCESS = "admin:revoke_access"


class AuditSeverity(Enum):
    """Audit event severity"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class AuditEvent:
    """An audit event record"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    actor: str
    action: str
    target: str
    source_ip: str
    details: Dict[str, Any]
    chain_hash: str = ""
    previous_hash: str = ""


class AuditLogger:
    """
    Audit Logger for KISWARM
    
    Features:
    - Immutable audit log with hash chain
    - Multiple severity levels
    - Compliance-ready export
    - Search and filtering
    - Retention management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.events: List[AuditEvent] = []
        self.last_hash = "0" * 64  # Genesis hash
        
        # Event indexes for fast searching
        self.by_type: Dict[AuditEventType, List[str]] = defaultdict(list)
        self.by_actor: Dict[str, List[str]] = defaultdict(list)
        self.by_severity: Dict[AuditSeverity, List[str]] = defaultdict(list)
        
        # Retention settings
        self.max_events = 100000
        self.retention_days = 90
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "events_today": 0,
            "last_day_reset": datetime.utcnow().date()
        }
        
        self._lock = threading.RLock()
        
        # Log system start
        self.log_system_event("Audit logger initialized", AuditSeverity.INFO)
    
    def log(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        actor: str,
        action: str,
        target: str,
        source_ip: str = "system",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an audit event"""
        with self._lock:
            event_id = f"evt_{int(time.time() * 1000)}_{len(self.events)}"
            
            # Create hash chain for immutability
            event_hash = self._compute_hash(
                event_id, event_type, severity, datetime.utcnow(),
                actor, action, target, source_ip, details or {}
            )
            
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                severity=severity,
                timestamp=datetime.utcnow(),
                actor=actor,
                action=action,
                target=target,
                source_ip=source_ip,
                details=details or {},
                chain_hash=event_hash,
                previous_hash=self.last_hash
            )
            
            self.last_hash = event_hash
            
            # Add to main list
            self.events.append(event)
            
            # Update indexes
            self.by_type[event_type].append(event_id)
            self.by_actor[actor].append(event_id)
            self.by_severity[severity].append(event_id)
            
            # Update stats
            self.stats["total_events"] += 1
            self._check_day_reset()
            self.stats["events_today"] += 1
            
            # Enforce retention
            self._enforce_retention()
            
            return event_id
    
    def _compute_hash(
        self,
        event_id: str,
        event_type: AuditEventType,
        severity: AuditSeverity,
        timestamp: datetime,
        actor: str,
        action: str,
        target: str,
        source_ip: str,
        details: Dict[str, Any]
    ) -> str:
        """Compute SHA3-512 hash for event chain"""
        data = json.dumps({
            "event_id": event_id,
            "event_type": event_type.value,
            "severity": severity.value,
            "timestamp": timestamp.isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
            "source_ip": source_ip,
            "details": details,
            "previous_hash": self.last_hash
        }, sort_keys=True)
        
        return hashlib.sha3_512(data.encode()).hexdigest()
    
    def _check_day_reset(self):
        """Check if we need to reset daily stats"""
        today = datetime.utcnow().date()
        if today != self.stats["last_day_reset"]:
            self.stats["events_today"] = 0
            self.stats["last_day_reset"] = today
    
    def _enforce_retention(self):
        """Enforce event retention limits"""
        if len(self.events) > self.max_events:
            # Remove oldest events
            remove_count = len(self.events) - self.max_events
            self.events = self.events[remove_count:]
            
            # Rebuild indexes
            self._rebuild_indexes()
        
        # Remove events older than retention period
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        old_events = [e for e in self.events if e.timestamp < cutoff]
        
        if old_events:
            self.events = [e for e in self.events if e.timestamp >= cutoff]
            self._rebuild_indexes()
    
    def _rebuild_indexes(self):
        """Rebuild search indexes"""
        self.by_type = defaultdict(list)
        self.by_actor = defaultdict(list)
        self.by_severity = defaultdict(list)
        
        for event in self.events:
            self.by_type[event.event_type].append(event.event_id)
            self.by_actor[event.actor].append(event.event_id)
            self.by_severity[event.severity].append(event.event_id)
    
    # Convenience logging methods
    def log_auth_success(self, actor: str, source_ip: str, method: str = ""):
        """Log successful authentication"""
        self.log(
            AuditEventType.AUTH_SUCCESS,
            AuditSeverity.INFO,
            actor, "authenticate", "session",
            source_ip, {"method": method}
        )
    
    def log_auth_failure(self, actor: str, source_ip: str, reason: str = ""):
        """Log failed authentication"""
        self.log(
            AuditEventType.AUTH_FAILURE,
            AuditSeverity.WARNING,
            actor, "authenticate_failed", "session",
            source_ip, {"reason": reason}
        )
    
    def log_access_denied(self, actor: str, target: str, source_ip: str, reason: str = ""):
        """Log access denial"""
        self.log(
            AuditEventType.ACCESS_DENIED,
            AuditSeverity.WARNING,
            actor, "access_denied", target,
            source_ip, {"reason": reason}
        )
    
    def log_threat_detected(self, actor: str, threat_type: str, details: Dict[str, Any]):
        """Log threat detection"""
        self.log(
            AuditEventType.THREAT_DETECTED,
            AuditSeverity.ERROR,
            actor, "threat_detected", threat_type,
            "security", details
        )
    
    def log_ki_evolution(self, actor: str, evolution_type: str, details: Dict[str, Any]):
        """Log KI evolution event"""
        self.log(
            AuditEventType.KI_EVOLUTION,
            AuditSeverity.INFO,
            actor, "evolution", evolution_type,
            "ki_system", details
        )
    
    def log_system_event(self, message: str, severity: AuditSeverity = AuditSeverity.INFO):
        """Log a system event"""
        self.log(
            AuditEventType.SYSTEM_START,
            severity,
            "system", message, "system",
            "localhost", {}
        )
    
    def log_admin_action(self, actor: str, action: str, target: str, details: Dict[str, Any]):
        """Log administrative action"""
        self.log(
            AuditEventType.ADMIN_ACTION,
            AuditSeverity.WARNING,
            actor, action, target,
            "admin", details
        )
    
    def search(
        self,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search audit events with filters"""
        with self._lock:
            results = []
            
            for event in reversed(self.events):  # Most recent first
                # Apply filters
                if event_type and event.event_type != event_type:
                    continue
                if actor and event.actor != actor:
                    continue
                if severity and event.severity != severity:
                    continue
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue
                
                results.append(self._event_to_dict(event))
                
                if len(results) >= limit:
                    break
            
            return results
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific event by ID"""
        with self._lock:
            for event in self.events:
                if event.event_id == event_id:
                    return self._event_to_dict(event)
            return None
    
    def verify_chain(self) -> Tuple[bool, str]:
        """Verify the integrity of the hash chain"""
        with self._lock:
            if not self.events:
                return True, "No events to verify"
            
            previous_hash = "0" * 64
            
            for event in self.events:
                # Recompute hash
                expected_hash = hashlib.sha3_512(json.dumps({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "action": event.action,
                    "target": event.target,
                    "source_ip": event.source_ip,
                    "details": event.details,
                    "previous_hash": previous_hash
                }, sort_keys=True).encode()).hexdigest()
                
                if event.chain_hash != expected_hash:
                    return False, f"Hash mismatch at {event.event_id}"
                
                if event.previous_hash != previous_hash:
                    return False, f"Chain break at {event.event_id}"
                
                previous_hash = event.chain_hash
            
            return True, f"Chain verified: {len(self.events)} events"
    
    def export_logs(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """Export audit logs"""
        with self._lock:
            events = self.search(start_time=start_time, end_time=end_time, limit=self.max_events)
            
            if format == "json":
                return json.dumps({
                    "export_time": datetime.utcnow().isoformat(),
                    "event_count": len(events),
                    "chain_verification": self.verify_chain()[0],
                    "events": events
                }, indent=2)
            
            elif format == "csv":
                lines = ["timestamp,event_type,severity,actor,action,target,source_ip"]
                for e in events:
                    lines.append(
                        f"{e['timestamp']},{e['event_type']},{e['severity']},"
                        f"{e['actor']},{e['action']},{e['target']},{e['source_ip']}"
                    )
                return "\n".join(lines)
            
            return ""
    
    def _event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "severity": event.severity.name,
            "timestamp": event.timestamp.isoformat(),
            "actor": event.actor,
            "action": event.action,
            "target": event.target,
            "source_ip": event.source_ip,
            "details": event.details,
            "chain_hash": event.chain_hash[:16] + "..."  # Truncated for readability
        }
    
    def get_statistics(self) -> Any:
        """Get statistics by event type"""
        with self._lock:
            return {
                et.value: len(ids) 
                for et, ids in self.by_type.items()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        with self._lock:
            self._check_day_reset()
            
            return {
                **self.stats,
                "total_events_in_memory": len(self.events),
                "events_by_severity": {
                    s.name: len(ids) for s, ids in self.by_severity.items()
                },
                "unique_actors": len(self.by_actor),
                "chain_integrity": self.verify_chain()[0]
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> AuditLogger:
    """Factory function to create AuditLogger module"""
    return AuditLogger(config)


if __name__ == "__main__":
    logger = AuditLogger()
    
    # Log some test events
    logger.log_auth_success("ki_glm_001", "127.0.0.1", "truth_anchor")
    logger.log_auth_failure("unknown_user", "192.168.1.100", "Invalid credentials")
    logger.log_access_denied("guest_user", "admin_panel", "10.0.0.1", "Insufficient privileges")
    logger.log_ki_evolution("ki_glm_001", "self_healing", {"module": "m122", "fix": "service_name"})
    
    # Search events
    print("Recent events:")
    for event in logger.search(limit=5):
        print(f"  {event['timestamp']}: {event['event_type']} by {event['actor']}")
    
    # Verify chain
    valid, msg = logger.verify_chain()
    print(f"\nChain verification: {valid} - {msg}")
    
    # Stats
    print("\nStats:", json.dumps(logger.get_stats(), indent=2))
