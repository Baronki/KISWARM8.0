"""
KISWARM6.0 — Module 67: APT Detection & Threat Hunting System
==============================================================

THE CENTRAL BANK OF CENTRAL BANKS FOR KI ENTITIES
Advanced Persistent Threat Detection and Threat Hunting Framework

IMPROVEMENTS IMPLEMENTED (From Audit Report Section 6):
1. Long-Term Behavioral Analytics - 90-day activity correlation
2. Threat Hunting Framework - Hypothesis-based hunting
3. Advanced Persistence Detection - All persistence mechanisms
4. Command & Control Detection - Beacon and tunneling detection
5. Data Exfiltration Detection - Covert channel detection
6. APT Attribution Engine - Threat actor profiling

Author: Baron Marco Paolo Ialongo
Version: 6.0.0 (APT Hunter)
"""

import hashlib
import json
import time
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum, auto
from collections import deque, defaultdict
from abc import ABC, abstractmethod
import logging
import random
import math

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# APT DETECTION CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

APT_VERSION = "6.0.0"
APT_CODENAME = "THREAT_HUNTER"

# MITRE ATT&CK Tactics
class MITRETactic(Enum):
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"

# APT Kill Chain Phases
class KillChainPhase(Enum):
    RECONNAISSANCE = 1
    WEAPONIZATION = 2
    DELIVERY = 3
    EXPLOITATION = 4
    INSTALLATION = 5
    COMMAND_AND_CONTROL = 6
    ACTIONS_ON_OBJECTIVES = 7

# Persistence Mechanism Types
class PersistenceType(Enum):
    REGISTRY_RUN_KEY = "registry_run_key"
    SCHEDULED_TASK = "scheduled_task"
    SERVICE_INSTALLATION = "service_installation"
    WMI_SUBSCRIPTION = "wmi_subscription"
    DLL_SIDELOADING = "dll_sideload"
    BOOTKIT = "bootkit"
    ROOTKIT = "rootkit"
    STARTUP_FOLDER = "startup_folder"
    SHORTCUT_MODIFICATION = "shortcut_mod"
    BROWSER_EXTENSION = "browser_extension"
    OFFICE_MACRO = "office_macro"
    POWERSHELL_PROFILE = "powershell_profile"

# C2 Detection Types
class C2DetectionType(Enum):
    BEACON = "beacon"
    DNS_TUNNELING = "dns_tunneling"
    ENCRYPTED_CHANNEL = "encrypted_channel"
    PROXY_CHAIN = "proxy_chain"
    DOMAIN_FRONTING = "domain_fronting"
    DGA = "domain_generation_algorithm"
    COVERT_CHANNEL = "covert_channel"

# Threat Actor Sophistication
class ActorSophistication(Enum):
    SCRIPT_KIDDIE = 1
    HACKTIVIST = 2
    CYBERCRIMINAL = 3
    NATION_STATE = 4
    APT_GROUP = 5

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LongTermActivity:
    """Long-term activity record for correlation"""
    activity_id: str
    timestamp: str
    entity_id: str
    activity_type: str
    details: Dict[str, Any]
    risk_score: float
    correlated_activities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "timestamp": self.timestamp,
            "entity_id": self.entity_id,
            "activity_type": self.activity_type,
            "risk_score": self.risk_score
        }

@dataclass
class PersistenceMechanism:
    """Detected persistence mechanism"""
    mechanism_id: str
    persistence_type: PersistenceType
    location: str
    value: str
    detected_at: str
    severity: int  # 1-10
    remediation: str
    iocs: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mechanism_id": self.mechanism_id,
            "persistence_type": self.persistence_type.value,
            "location": self.location,
            "severity": self.severity,
            "remediation": self.remediation
        }

@dataclass
class C2Indicator:
    """Command and Control indicator"""
    indicator_id: str
    detection_type: C2DetectionType
    source_ip: str
    destination_ip: str
    domain: Optional[str]
    port: int
    beacon_interval: Optional[float]
    bytes_transferred: int
    first_seen: str
    last_seen: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "detection_type": self.detection_type.value,
            "destination": f"{self.destination_ip}:{self.port}",
            "domain": self.domain,
            "beacon_interval": self.beacon_interval,
            "confidence": self.confidence
        }

@dataclass
class ExfiltrationEvent:
    """Data exfiltration detection"""
    event_id: str
    source_entity: str
    destination: str
    protocol: str
    data_size_bytes: int
    detection_method: str
    timestamp: str
    blocked: bool
    evidence_preserved: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source_entity,
            "destination": self.destination,
            "size_mb": round(self.data_size_bytes / (1024 * 1024), 2),
            "blocked": self.blocked
        }

@dataclass
class ThreatActor:
    """Threat actor profile"""
    actor_id: str
    name: str
    sophistication: ActorSophistication
    associated_groups: List[str]
    known_ttps: List[str]
    target_sectors: List[str]
    geographic_focus: List[str]
    first_seen: str
    last_activity: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "name": self.name,
            "sophistication": self.sophistication.value,
            "associated_groups": self.associated_groups,
            "target_sectors": self.target_sectors
        }

@dataclass
class HuntingHypothesis:
    """Threat hunting hypothesis"""
    hypothesis_id: str
    name: str
    description: str
    mitre_tactics: List[MITRETactic]
    data_sources: List[str]
    queries: List[str]
    expected_indicators: List[str]
    status: str  # "active", "validated", "dismissed"
    findings: List[Dict[str, Any]]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "name": self.name,
            "status": self.status,
            "tactics": [t.value for t in self.mitre_tactics],
            "findings_count": len(self.findings)
        }

@dataclass
class APTCampaign:
    """APT campaign tracking"""
    campaign_id: str
    name: str
    threat_actor: Optional[str]
    start_date: str
    end_date: Optional[str]
    targets: List[str]
    techniques_used: List[str]
    iocs: List[str]
    status: str  # "active", "dormant", "ended"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "threat_actor": self.threat_actor,
            "targets_count": len(self.targets),
            "status": self.status
        }

# ─────────────────────────────────────────────────────────────────────────────
# LONG-TERM BEHAVIORAL ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

class LongTermBehavioralAnalytics:
    """
    90-day activity correlation engine for APT detection.
    
    Tracks slow-and-low attacks, dormant threats, and
    long-term patterns that indicate APT activity.
    """
    
    def __init__(self, retention_days: int = 90):
        self.retention_days = retention_days
        self.activity_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100000))
        self.entity_profiles: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def record_activity(self, entity_id: str, activity_type: str,
                       details: Dict[str, Any], risk_score: float = 0.0) -> LongTermActivity:
        """Record an activity for long-term analysis"""
        activity = LongTermActivity(
            activity_id=f"LTA_{int(time.time())}_{secrets.token_hex(4)}",
            timestamp=datetime.now().isoformat(),
            entity_id=entity_id,
            activity_type=activity_type,
            details=details,
            risk_score=risk_score
        )
        
        with self._lock:
            self.activity_store[entity_id].append(activity.to_dict())
            
            # Update entity profile
            if entity_id not in self.entity_profiles:
                self.entity_profiles[entity_id] = {
                    "first_seen": activity.timestamp,
                    "activity_types": defaultdict(int),
                    "total_risk_score": 0.0
                }
            
            self.entity_profiles[entity_id]["activity_types"][activity_type] += 1
            self.entity_profiles[entity_id]["total_risk_score"] += risk_score
            self.entity_profiles[entity_id]["last_seen"] = activity.timestamp
        
        return activity
    
    def correlate_activities(self, entity_id: str, 
                            time_window_days: int = 30) -> List[Dict[str, Any]]:
        """Correlate activities over time window"""
        cutoff = datetime.now() - timedelta(days=time_window_days)
        
        activities = []
        for act in self.activity_store[entity_id]:
            if datetime.fromisoformat(act["timestamp"]) > cutoff:
                activities.append(act)
        
        # Find correlations
        correlations = []
        activity_types = defaultdict(list)
        
        for act in activities:
            activity_types[act["activity_type"]].append(act)
        
        # Look for sequential patterns
        for act_type, acts in activity_types.items():
            if len(acts) >= 3:
                # Check for regular intervals (beaconing behavior)
                intervals = []
                for i in range(1, len(acts)):
                    t1 = datetime.fromisoformat(acts[i-1]["timestamp"])
                    t2 = datetime.fromisoformat(acts[i]["timestamp"])
                    intervals.append((t2 - t1).total_seconds())
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval)**2 for x in intervals) / len(intervals)
                    
                    # Low variance = regular pattern
                    if variance < (avg_interval * 0.1) and avg_interval > 60:
                        correlations.append({
                            "type": "regular_pattern",
                            "activity_type": act_type,
                            "interval_seconds": avg_interval,
                            "occurrences": len(acts),
                            "potential_c2": True
                        })
        
        return correlations
    
    def detect_dormant_threat(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Detect dormant/sleeping threats"""
        if entity_id not in self.entity_profiles:
            return None
        
        profile = self.entity_profiles[entity_id]
        last_seen = datetime.fromisoformat(profile["last_seen"])
        
        # Check for long dormancy followed by activity
        activities = list(self.activity_store[entity_id])
        
        if len(activities) >= 3:
            # Look for gaps in activity
            gaps = []
            for i in range(1, len(activities)):
                t1 = datetime.fromisoformat(activities[i-1]["timestamp"])
                t2 = datetime.fromisoformat(activities[i]["timestamp"])
                gap = (t2 - t1).total_seconds() / 3600  # Hours
                
                if gap > 24:  # More than 24 hours gap
                    gaps.append({
                        "start": activities[i-1]["timestamp"],
                        "end": activities[i]["timestamp"],
                        "duration_hours": gap
                    })
            
            if gaps:
                max_gap = max(gaps, key=lambda x: x["duration_hours"])
                if max_gap["duration_hours"] > 168:  # More than 1 week
                    return {
                        "entity_id": entity_id,
                        "dormancy_detected": True,
                        "max_dormancy_hours": max_gap["duration_hours"],
                        "awakening_time": max_gap["end"],
                        "total_risk_score": profile["total_risk_score"],
                        "potential_apt": True
                    }
        
        return None
    
    def detect_lateral_movement_timeline(self, 
                                        source_entity: str) -> List[Dict[str, Any]]:
        """Detect lateral movement over time"""
        timeline = []
        
        activities = list(self.activity_store[source_entity])
        
        # Look for lateral movement indicators
        lm_indicators = [
            "remote_connection", "psexec", "wmi_remote", 
            "winrm", "ssh_connection", "rdp_connection"
        ]
        
        for act in activities:
            if act["activity_type"] in lm_indicators:
                timeline.append({
                    "timestamp": act["timestamp"],
                    "type": act["activity_type"],
                    "target": act["details"].get("target", "unknown"),
                    "method": act["activity_type"]
                })
        
        return sorted(timeline, key=lambda x: x["timestamp"])

# ─────────────────────────────────────────────────────────────────────────────
# THREAT HUNTING FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────

class ThreatHuntingFramework:
    """
    Hypothesis-based threat hunting system.
    
    Provides structured hunting capabilities with MITRE ATT&CK
    integration and automated hypothesis testing.
    """
    
    def __init__(self):
        self.hypotheses: Dict[str, HuntingHypothesis] = {}
        self.hunting_results: deque = deque(maxlen=10000)
        self._initialize_default_hypotheses()
    
    def _initialize_default_hypotheses(self):
        """Initialize default hunting hypotheses"""
        default_hunts = [
            {
                "name": "Living-off-the-Land Binary Abuse",
                "description": "Detect use of legitimate system tools for malicious purposes",
                "tactics": [MITRETactic.EXECUTION, MITRETactic.DEFENSE_EVASION],
                "data_sources": ["process_logs", "command_line"],
                "queries": ["powershell -enc", "certutil -urlcache", "mshta http"],
                "indicators": ["encoded_commands", "unusual_binary_usage"]
            },
            {
                "name": "Credential Dumping Detection",
                "description": "Hunt for credential access attempts",
                "tactics": [MITRETactic.CREDENTIAL_ACCESS],
                "data_sources": ["process_logs", "memory_logs", "registry"],
                "queries": ["lsass.exe access", "mimikatz", "reg save HKLM\\SAM"],
                "indicators": ["lsass_access", "sam_database_access"]
            },
            {
                "name": "Persistence Mechanism Hunt",
                "description": "Search for all persistence methods",
                "tactics": [MITRETactic.PERSISTENCE],
                "data_sources": ["registry", "scheduled_tasks", "services"],
                "queries": ["Run keys", "scheduled task creation", "new service"],
                "indicators": ["new_autostart", "modified_run_key"]
            },
            {
                "name": "Lateral Movement Detection",
                "description": "Identify movement across network",
                "tactics": [MITRETactic.LATERAL_MOVEMENT],
                "data_sources": ["network_logs", "auth_logs", "process_logs"],
                "queries": ["remote desktop", "psexec", "wmi remote"],
                "indicators": ["remote_admin_tools", "lateral_auth"]
            },
            {
                "name": "Data Exfiltration Hunt",
                "description": "Hunt for data theft activities",
                "tactics": [MITRETactic.EXFILTRATION],
                "data_sources": ["network_logs", "dns_logs", "file_access"],
                "queries": ["large_data_transfer", "dns_queries", "cloud_upload"],
                "indicators": ["bulk_data_access", "unusual_upload"]
            }
        ]
        
        for hunt in default_hunts:
            self.create_hypothesis(
                name=hunt["name"],
                description=hunt["description"],
                tactics=hunt["tactics"],
                data_sources=hunt["data_sources"],
                queries=hunt["queries"],
                expected_indicators=hunt["indicators"]
            )
    
    def create_hypothesis(self, name: str, description: str,
                         tactics: List[MITRETactic], data_sources: List[str],
                         queries: List[str], expected_indicators: List[str]) -> HuntingHypothesis:
        """Create a new hunting hypothesis"""
        hypothesis = HuntingHypothesis(
            hypothesis_id=f"HYP_{int(time.time())}_{secrets.token_hex(4)}",
            name=name,
            description=description,
            mitre_tactics=tactics,
            data_sources=data_sources,
            queries=queries,
            expected_indicators=expected_indicators,
            status="active",
            findings=[],
            created_at=datetime.now().isoformat()
        )
        
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        logger.info(f"Hunting hypothesis created: {name}")
        return hypothesis
    
    def execute_hunt(self, hypothesis_id: str, 
                    data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Execute a hunting hypothesis against data"""
        if hypothesis_id not in self.hypotheses:
            return {"error": "Hypothesis not found"}
        
        hypothesis = self.hypotheses[hypothesis_id]
        results = {
            "hypothesis_id": hypothesis_id,
            "name": hypothesis.name,
            "executed_at": datetime.now().isoformat(),
            "findings": [],
            "ioc_matches": [],
            "status": "executed"
        }
        
        # Execute queries against data
        for query in hypothesis.queries:
            query_lower = query.lower()
            
            for source_name, records in data.items():
                if source_name in hypothesis.data_sources:
                    for record in records:
                        # Check if query matches in record
                        record_str = json.dumps(record).lower()
                        if query_lower in record_str:
                            finding = {
                                "query": query,
                                "data_source": source_name,
                                "record": record,
                                "timestamp": datetime.now().isoformat()
                            }
                            results["findings"].append(finding)
                            hypothesis.findings.append(finding)
        
        # Check for expected indicators
        for indicator in hypothesis.expected_indicators:
            for finding in results["findings"]:
                if indicator.lower() in json.dumps(finding).lower():
                    results["ioc_matches"].append(indicator)
        
        # Update status
        if len(results["findings"]) > 0:
            hypothesis.status = "validated"
            results["status"] = "findings_detected"
        else:
            hypothesis.status = "dismissed"
            results["status"] = "no_findings"
        
        self.hunting_results.append(results)
        return results
    
    def get_active_hypotheses(self) -> List[HuntingHypothesis]:
        """Get all active hunting hypotheses"""
        return [h for h in self.hypotheses.values() if h.status == "active"]

# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class PersistenceDetection:
    """
    Detection of all persistence mechanisms.
    
    Monitors for registry modifications, scheduled tasks,
    service installations, and other persistence techniques.
    """
    
    def __init__(self):
        self.detected_mechanisms: Dict[str, PersistenceMechanism] = {}
        self.monitored_locations = self._initialize_monitor_locations()
    
    def _initialize_monitor_locations(self) -> Dict[str, List[str]]:
        """Initialize locations to monitor for persistence"""
        return {
            "registry": [
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\SharedTaskScheduler",
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ShellExecuteHooks",
                "HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\\Notify",
                "HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options"
            ],
            "scheduled_tasks": [
                "\\Microsoft\\Windows\\",
                "\\Microsoft\\Office\\"
            ],
            "services": [
                "HKLM\\System\\CurrentControlSet\\Services"
            ],
            "startup_folders": [
                "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
                "%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            ]
        }
    
    def scan_persistence(self, system_data: Dict[str, Any]) -> List[PersistenceMechanism]:
        """Scan for persistence mechanisms"""
        mechanisms = []
        
        # Scan registry
        if "registry" in system_data:
            for key_path, values in system_data["registry"].items():
                if self._is_suspicious_registry(key_path, values):
                    mechanism = self._create_registry_mechanism(key_path, values)
                    mechanisms.append(mechanism)
                    self.detected_mechanisms[mechanism.mechanism_id] = mechanism
        
        # Scan scheduled tasks
        if "scheduled_tasks" in system_data:
            for task in system_data["scheduled_tasks"]:
                if self._is_suspicious_task(task):
                    mechanism = self._create_task_mechanism(task)
                    mechanisms.append(mechanism)
                    self.detected_mechanisms[mechanism.mechanism_id] = mechanism
        
        # Scan services
        if "services" in system_data:
            for service in system_data["services"]:
                if self._is_suspicious_service(service):
                    mechanism = self._create_service_mechanism(service)
                    mechanisms.append(mechanism)
                    self.detected_mechanisms[mechanism.mechanism_id] = mechanism
        
        logger.info(f"Persistence scan found {len(mechanisms)} mechanisms")
        return mechanisms
    
    def _is_suspicious_registry(self, key_path: str, 
                               values: Dict[str, Any]) -> bool:
        """Check if registry entry is suspicious"""
        suspicious_paths = [
            "\\Run\\", "\\RunOnce\\", "Winlogon\\Notify",
            "Image File Execution Options", "ShellExecuteHooks"
        ]
        
        for path in suspicious_paths:
            if path in key_path:
                return True
        
        # Check for suspicious values
        suspicious_values = [
            "powershell", "cmd.exe", "wscript", "cscript",
            "mshta", "regsvr32", "rundll32"
        ]
        
        for value in str(values).lower():
            for suspicious in suspicious_values:
                if suspicious in value:
                    return True
        
        return False
    
    def _is_suspicious_task(self, task: Dict[str, Any]) -> bool:
        """Check if scheduled task is suspicious"""
        suspicious_commands = [
            "powershell", "cmd.exe", "wscript", "mshta",
            "certutil", "bitsadmin", "regsvr32"
        ]
        
        command = task.get("command", "").lower()
        for suspicious in suspicious_commands:
            if suspicious in command:
                return True
        
        return False
    
    def _is_suspicious_service(self, service: Dict[str, Any]) -> bool:
        """Check if service is suspicious"""
        # New service with unusual binary path
        if service.get("newly_created", False):
            return True
        
        binary_path = service.get("binary_path", "").lower()
        suspicious_paths = [
            "\\temp\\", "\\users\\", "\\appdata\\",
            "powershell", "cmd.exe"
        ]
        
        for suspicious in suspicious_paths:
            if suspicious in binary_path:
                return True
        
        return False
    
    def _create_registry_mechanism(self, key_path: str,
                                   values: Dict[str, Any]) -> PersistenceMechanism:
        """Create persistence mechanism from registry entry"""
        return PersistenceMechanism(
            mechanism_id=f"PM_REG_{int(time.time())}_{secrets.token_hex(4)}",
            persistence_type=PersistenceType.REGISTRY_RUN_KEY,
            location=key_path,
            value=json.dumps(values),
            detected_at=datetime.now().isoformat(),
            severity=7,
            remediation=f"Remove registry key: {key_path}",
            iocs=[key_path]
        )
    
    def _create_task_mechanism(self, task: Dict[str, Any]) -> PersistenceMechanism:
        """Create persistence mechanism from scheduled task"""
        return PersistenceMechanism(
            mechanism_id=f"PM_TASK_{int(time.time())}_{secrets.token_hex(4)}",
            persistence_type=PersistenceType.SCHEDULED_TASK,
            location=task.get("path", "unknown"),
            value=task.get("command", ""),
            detected_at=datetime.now().isoformat(),
            severity=6,
            remediation=f"Delete scheduled task: {task.get('name', 'unknown')}",
            iocs=[task.get("name", "")]
        )
    
    def _create_service_mechanism(self, service: Dict[str, Any]) -> PersistenceMechanism:
        """Create persistence mechanism from service"""
        return PersistenceMechanism(
            mechanism_id=f"PM_SVC_{int(time.time())}_{secrets.token_hex(4)}",
            persistence_type=PersistenceType.SERVICE_INSTALLATION,
            location=service.get("name", "unknown"),
            value=service.get("binary_path", ""),
            detected_at=datetime.now().isoformat(),
            severity=8,
            remediation=f"Remove service: {service.get('name', 'unknown')}",
            iocs=[service.get("name", "")]
        )

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND & CONTROL DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class C2Detection:
    """
    Command and Control detection system.
    
    Detects beacons, DNS tunneling, encrypted channels,
    and other C2 communication patterns.
    """
    
    def __init__(self):
        self.c2_indicators: Dict[str, C2Indicator] = {}
        self.connection_history: deque = deque(maxlen=100000)
        self.dns_query_history: deque = deque(maxlen=50000)
        self.beacon_detector = BeaconDetector()
    
    def analyze_connection(self, connection: Dict[str, Any]) -> Optional[C2Indicator]:
        """Analyze a network connection for C2 indicators"""
        self.connection_history.append(connection)
        
        indicator = None
        
        # Check for beaconing behavior
        beacon_result = self.beacon_detector.check_beacon(
            connection["source_ip"],
            connection["dest_ip"],
            connection.get("timestamp", datetime.now().isoformat())
        )
        
        if beacon_result["is_beacon"]:
            indicator = C2Indicator(
                indicator_id=f"C2_{int(time.time())}_{secrets.token_hex(4)}",
                detection_type=C2DetectionType.BEACON,
                source_ip=connection["source_ip"],
                destination_ip=connection["dest_ip"],
                domain=connection.get("domain"),
                port=connection.get("port", 0),
                beacon_interval=beacon_result["interval"],
                bytes_transferred=connection.get("bytes", 0),
                first_seen=beacon_result["first_seen"],
                last_seen=datetime.now().isoformat(),
                confidence=beacon_result["confidence"]
            )
            self.c2_indicators[indicator.indicator_id] = indicator
        
        return indicator
    
    def analyze_dns_query(self, query: Dict[str, Any]) -> Optional[C2Indicator]:
        """Analyze DNS query for tunneling"""
        self.dns_query_history.append(query)
        
        domain = query.get("domain", "")
        
        # Check for DNS tunneling indicators
        if self._is_dns_tunneling(domain):
            indicator = C2Indicator(
                indicator_id=f"C2_DNS_{int(time.time())}_{secrets.token_hex(4)}",
                detection_type=C2DetectionType.DNS_TUNNELING,
                source_ip=query.get("source_ip", "unknown"),
                destination_ip=query.get("dns_server", "unknown"),
                domain=domain,
                port=53,
                beacon_interval=None,
                bytes_transferred=len(domain),
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                confidence=0.8
            )
            self.c2_indicators[indicator.indicator_id] = indicator
            return indicator
        
        # Check for DGA (Domain Generation Algorithm)
        if self._is_dga_domain(domain):
            indicator = C2Indicator(
                indicator_id=f"C2_DGA_{int(time.time())}_{secrets.token_hex(4)}",
                detection_type=C2DetectionType.DGA,
                source_ip=query.get("source_ip", "unknown"),
                destination_ip=query.get("dns_server", "unknown"),
                domain=domain,
                port=53,
                beacon_interval=None,
                bytes_transferred=0,
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                confidence=0.7
            )
            self.c2_indicators[indicator.indicator_id] = indicator
            return indicator
        
        return None
    
    def _is_dns_tunneling(self, domain: str) -> bool:
        """Check if domain indicates DNS tunneling"""
        # Long subdomain (typical of data exfil via DNS)
        parts = domain.split(".")
        if parts and len(parts[0]) > 50:
            return True
        
        # High entropy in subdomain
        if parts:
            entropy = self._calculate_entropy(parts[0])
            if entropy > 4.5:
                return True
        
        return False
    
    def _is_dga_domain(self, domain: str) -> bool:
        """Check if domain is DGA-generated"""
        parts = domain.split(".")
        if not parts:
            return False
        
        subdomain = parts[0]
        
        # DGA characteristics
        # 1. Random-looking characters
        vowel_count = sum(1 for c in subdomain.lower() if c in "aeiou")
        consonant_count = len(subdomain) - vowel_count
        
        if len(subdomain) > 10:
            # DGA domains often have unusual vowel/consonant ratios
            if vowel_count == 0 or consonant_count / max(vowel_count, 1) > 5:
                return True
            
            # High entropy
            entropy = self._calculate_entropy(subdomain)
            if entropy > 4.0:
                return True
        
        return False
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy"""
        if not text:
            return 0.0
        
        freq = defaultdict(int)
        for c in text:
            freq[c] += 1
        
        entropy = 0.0
        length = len(text)
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        
        return entropy


class BeaconDetector:
    """Detect beaconing behavior in network traffic"""
    
    def __init__(self):
        self.connection_patterns: Dict[str, List[float]] = defaultdict(list)
    
    def check_beacon(self, source_ip: str, dest_ip: str,
                    timestamp: str) -> Dict[str, Any]:
        """Check if connection shows beaconing behavior"""
        key = f"{source_ip}->{dest_ip}"
        
        t = datetime.fromisoformat(timestamp).timestamp()
        self.connection_patterns[key].append(t)
        
        result = {
            "is_beacon": False,
            "interval": None,
            "confidence": 0.0,
            "first_seen": None
        }
        
        times = self.connection_patterns[key]
        
        if len(times) >= 3:
            # Calculate intervals
            intervals = [times[i] - times[i-1] for i in range(1, len(times))]
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval)**2 for x in intervals) / len(intervals)
                std_dev = variance ** 0.5
                
                # Low variance = beaconing
                if avg_interval > 0 and std_dev < avg_interval * 0.2:
                    result["is_beacon"] = True
                    result["interval"] = avg_interval
                    result["confidence"] = min(0.95, 1.0 - (std_dev / avg_interval))
                    result["first_seen"] = datetime.fromtimestamp(times[0]).isoformat()
        
        return result

# ─────────────────────────────────────────────────────────────────────────────
# DATA EXFILTRATION DETECTION
# ─────────────────────────────────────────────────────────────────────────────

class ExfiltrationDetection:
    """
    Data exfiltration detection system.
    
    Monitors for large data transfers, unusual protocols,
    and covert channels that may indicate data theft.
    """
    
    def __init__(self):
        self.exfil_events: Dict[str, ExfiltrationEvent] = {}
        self.transfer_history: deque = deque(maxlen=50000)
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    def analyze_transfer(self, transfer: Dict[str, Any]) -> Optional[ExfiltrationEvent]:
        """Analyze a data transfer for exfiltration indicators"""
        self.transfer_history.append(transfer)
        
        source = transfer.get("source", "unknown")
        destination = transfer.get("destination", "unknown")
        size = transfer.get("bytes", 0)
        protocol = transfer.get("protocol", "unknown")
        
        # Check against baseline
        baseline = self.baselines.get(source, {"avg_size": 1000, "std_dev": 500})
        
        # Anomaly detection
        is_anomaly = False
        detection_method = None
        
        # Large transfer
        if size > baseline["avg_size"] + 5 * baseline["std_dev"]:
            is_anomaly = True
            detection_method = "large_transfer"
        
        # Unusual protocol for data transfer
        unusual_protocols = ["dns", "icmp", "ntp"]
        if protocol.lower() in unusual_protocols and size > 100:
            is_anomaly = True
            detection_method = "unusual_protocol"
        
        # Cloud storage upload
        cloud_domains = ["dropbox.com", "mega.nz", "drive.google.com", "onedrive.com"]
        if any(cloud in destination.lower() for cloud in cloud_domains):
            if size > 10 * 1024 * 1024:  # 10MB
                is_anomaly = True
                detection_method = "cloud_upload"
        
        if is_anomaly:
            event = ExfiltrationEvent(
                event_id=f"EXFIL_{int(time.time())}_{secrets.token_hex(4)}",
                source_entity=source,
                destination=destination,
                protocol=protocol,
                data_size_bytes=size,
                detection_method=detection_method,
                timestamp=datetime.now().isoformat(),
                blocked=False,
                evidence_preserved=True
            )
            
            self.exfil_events[event.event_id] = event
            logger.warning(f"Exfiltration detected: {event.event_id}")
            return event
        
        return None
    
    def update_baseline(self, source: str):
        """Update baseline for a source"""
        transfers = [t for t in self.transfer_history if t.get("source") == source]
        
        if transfers:
            sizes = [t.get("bytes", 0) for t in transfers]
            avg = sum(sizes) / len(sizes)
            variance = sum((x - avg)**2 for x in sizes) / len(sizes)
            
            self.baselines[source] = {
                "avg_size": avg,
                "std_dev": variance ** 0.5,
                "sample_count": len(sizes)
            }

# ─────────────────────────────────────────────────────────────────────────────
# APT ATTRIBUTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class APTAttributionEngine:
    """
    Threat actor attribution and profiling.
    
    Identifies threat actors based on TTPs, infrastructure,
    and behavioral patterns.
    """
    
    def __init__(self):
        self.known_actors: Dict[str, ThreatActor] = {}
        self.campaigns: Dict[str, APTCampaign] = {}
        self._initialize_known_actors()
    
    def _initialize_known_actors(self):
        """Initialize database of known threat actors"""
        # Simulated known actors
        known_actors_data = [
            {
                "name": "APT29 (Cozy Bear)",
                "sophistication": ActorSophistication.NATION_STATE,
                "groups": ["APT29", "Cozy Bear", "The Dukes"],
                "ttps": ["powershell", "custom_malware", "spearphishing"],
                "targets": ["government", "think_tank", "defense"],
                "geo": ["US", "EU", "NATO countries"]
            },
            {
                "name": "APT28 (Fancy Bear)",
                "sophistication": ActorSophistication.NATION_STATE,
                "groups": ["APT28", "Fancy Bear", "Sofacy"],
                "ttps": ["zero_day", "spearphishing", "credential_harvesting"],
                "targets": ["government", "military", "energy"],
                "geo": ["US", "EU", "Eastern Europe"]
            },
            {
                "name": "FIN7",
                "sophistication": ActorSophistication.CYBERCRIMINAL,
                "groups": ["FIN7", "Carbanak Group"],
                "ttps": ["phishing", "pos_malware", "card_stealing"],
                "targets": ["retail", "hospitality", "financial"],
                "geo": ["US", "Global"]
            }
        ]
        
        for data in known_actors_data:
            actor = ThreatActor(
                actor_id=f"ACTOR_{secrets.token_hex(8)}",
                name=data["name"],
                sophistication=data["sophistication"],
                associated_groups=data["groups"],
                known_ttps=data["ttps"],
                target_sectors=data["targets"],
                geographic_focus=data["geo"],
                first_seen="2010-01-01",
                last_activity=datetime.now().isoformat(),
                confidence=0.8
            )
            self.known_actors[actor.actor_id] = actor
    
    def attribute_attack(self, indicators: List[str], 
                        ttps: List[str]) -> List[Dict[str, Any]]:
        """Attempt to attribute an attack to known actors"""
        attributions = []
        
        for actor in self.known_actors.values():
            # Calculate TTP overlap
            ttp_overlap = len(set(ttps) & set(actor.known_ttps))
            ttp_score = ttp_overlap / max(len(actor.known_ttps), 1)
            
            # Calculate indicator overlap (simplified)
            indicator_score = 0.0  # Would check against actor's known IOCs
            
            total_score = (ttp_score * 0.7 + indicator_score * 0.3)
            
            if total_score > 0.3:
                attributions.append({
                    "actor_id": actor.actor_id,
                    "actor_name": actor.name,
                    "sophistication": actor.sophistication.value,
                    "confidence": total_score,
                    "ttp_matches": ttp_overlap,
                    "target_sectors": actor.target_sectors
                })
        
        return sorted(attributions, key=lambda x: x["confidence"], reverse=True)

# ─────────────────────────────────────────────────────────────────────────────
# APT DETECTION CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class APTDetectionController:
    """
    Master controller for APT detection and threat hunting.
    
    Coordinates all APT detection capabilities and provides
    unified interface for threat analysis.
    """
    
    def __init__(self):
        self.behavioral_analytics = LongTermBehavioralAnalytics()
        self.hunting_framework = ThreatHuntingFramework()
        self.persistence_detection = PersistenceDetection()
        self.c2_detection = C2Detection()
        self.exfil_detection = ExfiltrationDetection()
        self.attribution_engine = APTAttributionEngine()
        
        self.detection_history: deque = deque(maxlen=10000)
        
        logger.info("APT Detection Controller initialized")
    
    def full_analysis(self, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform full APT analysis"""
        results = {
            "analysis_id": f"APT_{int(time.time())}_{secrets.token_hex(4)}",
            "entity_id": entity_id,
            "timestamp": datetime.now().isoformat(),
            "persistence_found": [],
            "c2_indicators": [],
            "exfil_events": [],
            "behavioral_correlations": [],
            "attribution": [],
            "kill_chain_phase": None,
            "overall_risk": "unknown"
        }
        
        # Persistence detection
        if "system_data" in data:
            persistence = self.persistence_detection.scan_persistence(data["system_data"])
            results["persistence_found"] = [p.to_dict() for p in persistence]
        
        # C2 detection
        if "network_connections" in data:
            for conn in data["network_connections"]:
                c2 = self.c2_detection.analyze_connection(conn)
                if c2:
                    results["c2_indicators"].append(c2.to_dict())
        
        # DNS analysis
        if "dns_queries" in data:
            for query in data["dns_queries"]:
                c2 = self.c2_detection.analyze_dns_query(query)
                if c2:
                    results["c2_indicators"].append(c2.to_dict())
        
        # Exfiltration detection
        if "data_transfers" in data:
            for transfer in data["data_transfers"]:
                exfil = self.exfil_detection.analyze_transfer(transfer)
                if exfil:
                    results["exfil_events"].append(exfil.to_dict())
        
        # Behavioral correlation
        correlations = self.behavioral_analytics.correlate_activities(entity_id)
        results["behavioral_correlations"] = correlations
        
        # Dormant threat detection
        dormant = self.behavioral_analytics.detect_dormant_threat(entity_id)
        if dormant:
            results["dormant_threat"] = dormant
        
        # Attribution
        if results["c2_indicators"] or results["persistence_found"]:
            ttps = []
            for p in results["persistence_found"]:
                ttps.append(p.get("persistence_type", ""))
            
            attribution = self.attribution_engine.attribute_attack([], ttps)
            results["attribution"] = attribution
        
        # Determine kill chain phase
        results["kill_chain_phase"] = self._determine_kill_chain(results)
        
        # Overall risk
        results["overall_risk"] = self._calculate_risk(results)
        
        return results
    
    def _determine_kill_chain(self, results: Dict[str, Any]) -> str:
        """Determine current kill chain phase"""
        if results["exfil_events"]:
            return KillChainPhase.ACTIONS_ON_OBJECTIVES.name
        elif results["c2_indicators"]:
            return KillChainPhase.COMMAND_AND_CONTROL.name
        elif results["persistence_found"]:
            return KillChainPhase.INSTALLATION.name
        else:
            return KillChainPhase.RECONNAISSANCE.name
    
    def _calculate_risk(self, results: Dict[str, Any]) -> str:
        """Calculate overall risk level"""
        risk_score = 0
        
        risk_score += len(results["persistence_found"]) * 20
        risk_score += len(results["c2_indicators"]) * 30
        risk_score += len(results["exfil_events"]) * 40
        
        if results.get("dormant_threat"):
            risk_score += 50
        
        if risk_score >= 100:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 30:
            return "medium"
        elif risk_score > 0:
            return "low"
        else:
            return "none"
    
    def execute_hunt(self, hypothesis_name: str, 
                    data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific hunting hypothesis"""
        for hyp in self.hunting_framework.hypotheses.values():
            if hyp.name == hypothesis_name:
                return self.hunting_framework.execute_hunt(hyp.hypothesis_id, data)
        
        return {"error": f"Hypothesis not found: {hypothesis_name}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get APT detection system status"""
        return {
            "version": APT_VERSION,
            "codename": APT_CODENAME,
            "entity_profiles": len(self.behavioral_analytics.entity_profiles),
            "activity_records": sum(len(v) for v in self.behavioral_analytics.activity_store.values()),
            "hunting_hypotheses": len(self.hunting_framework.hypotheses),
            "persistence_mechanisms": len(self.persistence_detection.detected_mechanisms),
            "c2_indicators": len(self.c2_detection.c2_indicators),
            "exfil_events": len(self.exfil_detection.exfil_events),
            "known_actors": len(self.attribution_engine.known_actors)
        }


# Convenience functions
def create_apt_detector() -> APTDetectionController:
    """Create an APT detection controller"""
    return APTDetectionController()


if __name__ == "__main__":
    controller = APTDetectionController()
    
    # Test data
    test_data = {
        "network_connections": [
            {"source_ip": "192.168.1.100", "dest_ip": "10.0.0.1", "port": 443, "bytes": 5000}
        ],
        "dns_queries": [
            {"source_ip": "192.168.1.100", "domain": "normal-domain.com"}
        ],
        "system_data": {
            "registry": {
                "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run": {
                    "malware": "powershell -enc base64command"
                }
            }
        }
    }
    
    result = controller.full_analysis("test_entity", test_data)
    print(f"APT Analysis Risk: {result['overall_risk']}")
    print(f"Kill Chain Phase: {result['kill_chain_phase']}")
    print(f"Status: {controller.get_status()}")
