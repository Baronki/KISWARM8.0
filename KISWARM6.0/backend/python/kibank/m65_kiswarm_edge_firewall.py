"""
KISWARM6.0 — Module 65: KISWARM Edge Firewall
==============================================

TCS GREEN SAFE HOUSE - RESIDENTIAL EDGE SECURITY NODE
Distributed Self-Evolving Firewall for Energy Platform Customers

HARDWARE: GEEKOM GT15 Max Mini AI PC (3-Node Cluster Configuration)
CAPABILITY: Permanent self-evolving firewall for residential customers

ARCHITECTURE:
- 3x GT15 Max nodes per customer installation
- Dual LAN configuration (WAN + LAN)
- Distributed LLM inference for real-time threat detection
- HexStrike agents adapted for residential security
- Swarm coordination with Central Bank
- Self-evolving rules based on threat learning

BENEFITS FOR TCS CUSTOMERS:
- Military-grade security for their home/solar installation
- AI-powered threat detection and prevention
- Automatic updates from Central Bank threat intelligence
- Integration with TCS Green Safe House energy platform
- Protection of solar investment and energy data

Author: Baron Marco Paolo Ialongo
Version: 6.0.0 (KISWARM Edge)
"""

import hashlib
import json
import time
import secrets
import threading
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum, auto
from collections import deque, defaultdict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# EDGE NODE HARDWARE SPECIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

GT15MAX_SPECS = {
    "cpu": "Intel Core Ultra 9-285H (16 cores, 65W)",
    "ram": "128GB DDR5-5600 Dual-Channel",
    "gpu": "Intel Arc 140T iGPU (XeSS + Ray Tracing)",
    "npu": "Intel AI Boost — 99 TOPS",
    "storage": "4TB NVMe PCIe Gen4 + 2TB SATA",
    "network": "Dual 2.5G LAN + Wi-Fi 7",
    "power": "150W typical, 200W max",
    "form_factor": "Mini PC (0.8L volume)",
    "llm_capacity": "6-8 models @ Q4_K_M",
    "inference_speed": "100-140 tok/s (small models)"
}

# Model allocation for residential edge nodes
EDGE_MODEL_ALLOCATION = {
    "node_1_primary": {
        "role": "Main Firewall & Threat Detection",
        "models": {
            "firewall_llm": "llama3.2:3b",
            "threat_detection": "qwen2.5:1.5b",
            "anomaly_detection": "tinyllama:1.1b"
        },
        "vram_required": "8GB",
        "cpu_cores": 8
    },
    "node_2_hexstrike": {
        "role": "HexStrike Security Agents",
        "models": {
            "hexstrike_guard": "llama3.2:3b",
            "honeypot_manager": "qwen2.5:1.5b",
            "intel_aggregator": "phi3:mini"
        },
        "vram_required": "10GB",
        "cpu_cores": 4
    },
    "node_3_swarm": {
        "role": "Swarm Coordination & Learning",
        "models": {
            "swarm_coordinator": "deepseek-r1:8b",
            "rule_evolver": "qwen2.5:3b",
            "report_generator": "llama3.2:1b"
        },
        "vram_required": "12GB",
        "cpu_cores": 4
    }
}

# Network configuration for firewall mode
NETWORK_CONFIG = {
    "wan_interface": "eth0",  # Connected to ISP modem
    "lan_interface": "eth1",  # Connected to home network
    "management_interface": "wlan0",  # Wi-Fi for customer access
    "default_subnet": "192.168.100.0/24",  # Home network
    "firewall_zone": "tcs_green_zone"
}

# Threat categories for residential
class ResidentialThreatType(Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    RANSOMWARE = "ransomware"
    IoT_COMPROMISE = "iot_compromise"
    SOLAR_INVERTER_ATTACK = "solar_inverter_attack"
    ENERGY_DATA_THEFT = "energy_data_theft"
    NETWORK_INTRUSION = "network_intrusion"
    DDOS = "ddos"
    DNS_HIJACKING = "dns_hijacking"
    CRYPTOJACKING = "cryptojacking"
    SMART_HOME_BREACH = "smart_home_breach"
    GRID_ATTACK = "grid_attack"  # Attack on energy grid connection

# Firewall rule priorities
class RulePriority(Enum):
    CRITICAL = 1      # Always block, no override
    HIGH = 2          # Block by default
    MEDIUM = 3        # Alert and log
    LOW = 4           # Monitor only
    LEARNING = 5      # New rule being learned

# Node roles
class NodeRole(Enum):
    PRIMARY_FIREWALL = "primary_firewall"
    HEXSTRIKE_AGENT = "hexstrike_agent"
    SWARM_COORDINATOR = "swarm_coordinator"
    BACKUP = "backup"
    OFFLINE = "offline"


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EdgeNode:
    """KISWARM Edge Node configuration"""
    node_id: str
    serial_number: str
    role: NodeRole
    ip_address: str
    mac_address: str
    models_loaded: List[str]
    status: str  # "online", "offline", "maintenance"
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    gpu_usage: float = 0.0
    last_heartbeat: Optional[str] = None
    threat_count: int = 0
    uptime_seconds: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "ip_address": self.ip_address,
            "status": self.status,
            "cpu_usage": self.cpu_usage,
            "ram_usage": self.ram_usage,
            "models_loaded": self.models_loaded,
            "threat_count": self.threat_count,
            "uptime_seconds": self.uptime_seconds
        }


@dataclass
class FirewallRule:
    """Self-evolving firewall rule"""
    rule_id: str
    name: str
    priority: RulePriority
    action: str  # "allow", "block", "rate_limit", "quarantine"
    source: Optional[str] = None  # IP/CIDR
    destination: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None  # "tcp", "udp", "icmp"
    threat_type: Optional[ResidentialThreatType] = None
    confidence: float = 0.0  # AI confidence in rule
    learned_from: str = "manual"  # How rule was created
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    hit_count: int = 0
    last_hit: Optional[str] = None
    expires_at: Optional[str] = None  # For temporary rules
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "priority": self.priority.value,
            "action": self.action,
            "source": self.source,
            "destination": self.destination,
            "port": self.port,
            "protocol": self.protocol,
            "confidence": self.confidence,
            "learned_from": self.learned_from,
            "hit_count": self.hit_count,
            "created_at": self.created_at
        }


@dataclass
class ThreatEvent:
    """Detected threat event"""
    event_id: str
    timestamp: str
    threat_type: ResidentialThreatType
    severity: int  # 1-10
    source_ip: str
    source_port: Optional[int]
    destination_ip: str
    destination_port: Optional[int]
    protocol: str
    payload_hash: Optional[str]
    action_taken: str
    rule_triggered: str
    node_id: str
    ai_confidence: float
    mitre_attack_id: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "threat_type": self.threat_type.value,
            "severity": self.severity,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "action_taken": self.action_taken,
            "ai_confidence": self.ai_confidence
        }


@dataclass
class SolarAssetProtection:
    """Protection profile for TCS Green Safe House solar assets"""
    asset_id: str
    customer_id: str
    asset_type: str  # "solar_inverter", "battery", "smart_meter", "gateway"
    ip_address: str
    expected_communication: List[Dict[str, Any]] = field(default_factory=list)  # Expected traffic patterns
    mac_address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    last_seen: Optional[str] = None
    protection_level: str = "maximum"
    isolated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "customer_id": self.customer_id,
            "asset_type": self.asset_type,
            "ip_address": self.ip_address,
            "protection_level": self.protection_level,
            "isolated": self.isolated
        }


@dataclass
class SwarmLearningUpdate:
    """Update from swarm learning"""
    update_id: str
    source_node: str
    update_type: str  # "new_rule", "rule_update", "threat_signature", "model_update"
    data: Dict[str, Any]
    confidence: float
    timestamp: str
    validated: bool = False
    propagated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "update_id": self.update_id,
            "source_node": self.source_node,
            "update_type": self.update_type,
            "confidence": self.confidence,
            "validated": self.validated,
            "propagated": self.propagated
        }


# ─────────────────────────────────────────────────────────────────────────────
# EDGE FIREWALL ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class EdgeFirewallEngine:
    """
    Core firewall engine for residential deployment.
    
    Features:
    - Self-evolving rules based on AI learning
    - Integration with HexStrike agents
    - Solar asset protection
    - Customer-friendly configuration
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.rules: Dict[str, FirewallRule] = {}
        self.threat_log: deque = deque(maxlen=10000)
        self.learning_buffer: deque = deque(maxlen=1000)
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default firewall rules"""
        default_rules = [
            {
                "name": "Block Known Malicious IPs",
                "priority": RulePriority.CRITICAL,
                "action": "block",
                "learned_from": "central_bank_intelligence"
            },
            {
                "name": "Protect Solar Inverter Ports",
                "priority": RulePriority.CRITICAL,
                "action": "block",
                "port": 502,  # Modbus
                "learned_from": "solar_security_baseline"
            },
            {
                "name": "Block Ransomware C2 Traffic",
                "priority": RulePriority.CRITICAL,
                "action": "block",
                "threat_type": ResidentialThreatType.RANSOMWARE,
                "learned_from": "hexstrike_intelligence"
            },
            {
                "name": "Rate Limit New Connections",
                "priority": RulePriority.MEDIUM,
                "action": "rate_limit",
                "learned_from": "ddos_protection"
            },
            {
                "name": "Monitor IoT Device Traffic",
                "priority": RulePriority.LOW,
                "action": "allow",
                "learned_from": "smart_home_baseline"
            }
        ]
        
        for i, rule_data in enumerate(default_rules):
            rule_id = f"RULE_DEFAULT_{i+1:03d}"
            self.rules[rule_id] = FirewallRule(
                rule_id=rule_id,
                name=rule_data["name"],
                priority=rule_data["priority"],
                action=rule_data["action"],
                learned_from=rule_data["learned_from"],
                confidence=1.0
            )
    
    def process_packet(self, packet_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a network packet through firewall rules"""
        decision = {
            "action": "allow",  # Default allow
            "rule_matched": None,
            "threat_detected": False,
            "confidence": 1.0,
            "processing_time_ms": 0
        }
        
        start_time = time.time()
        
        # Check against all rules in priority order
        for rule in sorted(self.rules.values(), key=lambda r: r.priority.value):
            if self._rule_matches(rule, packet_info):
                decision["action"] = rule.action
                decision["rule_matched"] = rule.rule_id
                decision["confidence"] = rule.confidence
                
                # Update rule statistics
                rule.hit_count += 1
                rule.last_hit = datetime.now().isoformat()
                
                # Log for learning
                self.learning_buffer.append({
                    "packet": packet_info,
                    "rule": rule.rule_id,
                    "action": rule.action,
                    "timestamp": datetime.now().isoformat()
                })
                
                break
        
        decision["processing_time_ms"] = (time.time() - start_time) * 1000
        
        return decision
    
    def _rule_matches(self, rule: FirewallRule, packet: Dict[str, Any]) -> bool:
        """Check if a rule matches the packet"""
        # Check source
        if rule.source and not self._ip_matches(packet.get("src_ip"), rule.source):
            return False
        
        # Check destination
        if rule.destination and not self._ip_matches(packet.get("dst_ip"), rule.destination):
            return False
        
        # Check port
        if rule.port and packet.get("dst_port") != rule.port:
            return False
        
        # Check protocol
        if rule.protocol and packet.get("protocol", "").lower() != rule.protocol.lower():
            return False
        
        return True
    
    def _ip_matches(self, packet_ip: Optional[str], rule_ip: str) -> bool:
        """Check if IP matches rule (supports CIDR)"""
        if not packet_ip:
            return False
        
        # Simple match for now
        if "/" in rule_ip:
            # CIDR notation - simplified check
            network = rule_ip.split("/")[0]
            return packet_ip.startswith(network.rsplit(".", 1)[0])
        
        return packet_ip == rule_ip
    
    def add_learned_rule(self, rule_data: Dict[str, Any], 
                         confidence: float) -> FirewallRule:
        """Add a new rule learned from AI analysis"""
        rule_id = f"RULE_LEARNED_{int(time.time())}_{secrets.token_hex(4)}"
        
        rule = FirewallRule(
            rule_id=rule_id,
            name=rule_data.get("name", "AI Learned Rule"),
            priority=RulePriority.LEARNING,
            action=rule_data.get("action", "block"),
            source=rule_data.get("source"),
            destination=rule_data.get("destination"),
            port=rule_data.get("port"),
            protocol=rule_data.get("protocol"),
            threat_type=rule_data.get("threat_type"),
            confidence=confidence,
            learned_from="ai_learning"
        )
        
        self.rules[rule_id] = rule
        logger.info(f"New learned rule added: {rule_id} (confidence: {confidence:.2f})")
        
        return rule
    
    def log_threat(self, event: ThreatEvent):
        """Log a threat event"""
        self.threat_log.append(event.to_dict())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get firewall statistics"""
        return {
            "total_rules": len(self.rules),
            "rules_by_priority": {
                p.value: len([r for r in self.rules.values() if r.priority == p])
                for p in RulePriority
            },
            "threats_logged": len(self.threat_log),
            "learning_buffer_size": len(self.learning_buffer),
            "top_hit_rules": sorted(
                [r.to_dict() for r in self.rules.values()],
                key=lambda x: x["hit_count"],
                reverse=True
            )[:5]
        }


# ─────────────────────────────────────────────────────────────────────────────
# HEXSTRIKE RESIDENTIAL AGENTS
# ─────────────────────────────────────────────────────────────────────────────

class HexStrikeResidentialAgent:
    """
    HexStrike agent adapted for residential security.
    
    Monitors:
    - Network traffic anomalies
    - IoT device behavior
    - Solar system communications
    - External attack attempts
    """
    
    AGENT_TYPES = {
        "network_guardian": {
            "description": "Monitors all network traffic",
            "model": "llama3.2:3b",
            "scan_interval": 1  # seconds
        },
        "iot_watcher": {
            "description": "Monitors IoT device behavior",
            "model": "qwen2.5:1.5b",
            "scan_interval": 5
        },
        "solar_protector": {
            "description": "Protects solar energy systems",
            "model": "phi3:mini",
            "scan_interval": 2
        },
        "threat_hunter": {
            "description": "Hunts for advanced threats",
            "model": "llama3.2:3b",
            "scan_interval": 10
        },
        "anomaly_detector": {
            "description": "Detects behavioral anomalies",
            "model": "tinyllama:1.1b",
            "scan_interval": 3
        },
        "dns_guardian": {
            "description": "Protects DNS queries",
            "model": "qwen2.5:0.5b",
            "scan_interval": 1
        }
    }
    
    def __init__(self, agent_type: str, node_id: str):
        self.agent_type = agent_type
        self.node_id = node_id
        self.config = self.AGENT_TYPES.get(agent_type, self.AGENT_TYPES["network_guardian"])
        self.status = "idle"
        self.detections = 0
        self.last_detection: Optional[str] = None
        self._scan_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start_monitoring(self):
        """Start the agent's monitoring loop"""
        self._running = True
        self._scan_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._scan_thread.start()
        logger.info(f"HexStrike agent {self.agent_type} started on {self.node_id}")
    
    def stop_monitoring(self):
        """Stop the agent's monitoring loop"""
        self._running = False
        self.status = "stopped"
        logger.info(f"HexStrike agent {self.agent_type} stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        self.status = "active"
        
        while self._running:
            # Simulate monitoring activity
            time.sleep(self.config["scan_interval"])
            
            # In production, would process actual network data
            # using the assigned LLM model
    
    def analyze_traffic(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network traffic for threats"""
        analysis = {
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
            "threat_detected": False,
            "confidence": 0.0,
            "details": {}
        }
        
        # Check for various threat patterns
        if self.agent_type == "network_guardian":
            analysis["details"] = self._analyze_network_patterns(traffic_data)
        
        elif self.agent_type == "iot_watcher":
            analysis["details"] = self._analyze_iot_behavior(traffic_data)
        
        elif self.agent_type == "solar_protector":
            analysis["details"] = self._analyze_solar_traffic(traffic_data)
        
        elif self.agent_type == "dns_guardian":
            analysis["details"] = self._analyze_dns_queries(traffic_data)
        
        # Determine if threat detected
        if analysis["details"].get("anomaly_score", 0) > 0.7:
            analysis["threat_detected"] = True
            analysis["confidence"] = analysis["details"]["anomaly_score"]
            self.detections += 1
            self.last_detection = analysis["timestamp"]
        
        return analysis
    
    def _analyze_network_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network traffic patterns"""
        return {
            "anomaly_score": 0.0,
            "bytes_transferred": data.get("bytes", 0),
            "connection_count": data.get("connections", 0),
            "suspicious_ports": []
        }
    
    def _analyze_iot_behavior(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze IoT device behavior"""
        return {
            "anomaly_score": 0.0,
            "device_count": data.get("device_count", 0),
            "unexpected_connections": []
        }
    
    def _analyze_solar_traffic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze solar system communications"""
        return {
            "anomaly_score": 0.0,
            "inverter_status": "normal",
            "grid_connection": "secure",
            "data_flow": "expected"
        }
    
    def _analyze_dns_queries(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DNS queries for threats"""
        return {
            "anomaly_score": 0.0,
            "queries_analyzed": data.get("query_count", 0),
            "suspicious_domains": []
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_type": self.agent_type,
            "node_id": self.node_id,
            "status": self.status,
            "detections": self.detections,
            "last_detection": self.last_detection,
            "model": self.config["model"]
        }


# ─────────────────────────────────────────────────────────────────────────────
# SWARM COORDINATION LAYER
# ─────────────────────────────────────────────────────────────────────────────

class SwarmCoordinationLayer:
    """
    Coordinates learning and updates across all edge nodes.
    
    Features:
    - Distributed rule learning
    - Threat signature sharing
    - Model update coordination
    - Central Bank integration
    """
    
    def __init__(self, cluster_id: str):
        self.cluster_id = cluster_id
        self.nodes: Dict[str, EdgeNode] = {}
        self.pending_updates: deque = deque(maxlen=1000)
        self.propagated_updates: Dict[str, SwarmLearningUpdate] = {}
        self.central_bank_connection: Optional[str] = None
    
    def register_node(self, node: EdgeNode):
        """Register an edge node in the cluster"""
        self.nodes[node.node_id] = node
        logger.info(f"Node {node.node_id} registered in cluster {self.cluster_id}")
    
    def receive_update(self, update: SwarmLearningUpdate) -> bool:
        """Receive a learning update from a node"""
        # Validate update
        if update.confidence < 0.7:
            logger.warning(f"Update {update.update_id} rejected - low confidence")
            return False
        
        self.pending_updates.append(update)
        return True
    
    def propagate_update(self, update_id: str) -> Dict[str, Any]:
        """Propagate an update to all nodes"""
        results = {
            "update_id": update_id,
            "propagated_to": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Find the update
        update = None
        for u in self.pending_updates:
            if u.update_id == update_id:
                update = u
                break
        
        if not update:
            results["error"] = "Update not found"
            return results
        
        # Send to all active nodes
        for node_id, node in self.nodes.items():
            if node.status == "online" and node_id != update.source_node:
                # In production, would send actual network message
                results["propagated_to"].append(node_id)
        
        if update:
            update.propagated = True
            self.propagated_updates[update_id] = update
        
        return results
    
    def sync_with_central_bank(self) -> Dict[str, Any]:
        """Synchronize threat intelligence with Central Bank"""
        sync_result = {
            "timestamp": datetime.now().isoformat(),
            "cluster_id": self.cluster_id,
            "updates_received": 0,
            "updates_sent": 0,
            "status": "success"
        }
        
        # In production, would establish secure connection to Central Bank
        # and exchange threat intelligence
        
        return sync_result
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get status of the entire cluster"""
        return {
            "cluster_id": self.cluster_id,
            "total_nodes": len(self.nodes),
            "online_nodes": len([n for n in self.nodes.values() if n.status == "online"]),
            "pending_updates": len(self.pending_updates),
            "propagated_updates": len(self.propagated_updates),
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()}
        }


# ─────────────────────────────────────────────────────────────────────────────
# SOLAR ASSET PROTECTION MANAGER
# ─────────────────────────────────────────────────────────────────────────────

class SolarAssetProtectionManager:
    """
    Manages protection for TCS Green Safe House solar assets.
    
    Protects:
    - Solar inverters
    - Battery storage systems
    - Smart meters
    - Energy gateways
    - Grid connections
    """
    
    # Common solar equipment ports and protocols
    SOLAR_PROTOCOLS = {
        "modbus_tcp": {"port": 502, "protocol": "tcp", "risk": "high"},
        "modbus_rtu": {"port": 502, "protocol": "serial", "risk": "high"},
        "sunspec": {"port": 502, "protocol": "tcp", "risk": "medium"},
        "mqtt": {"port": 1883, "protocol": "tcp", "risk": "medium"},
        "mqtt_tls": {"port": 8883, "protocol": "tcp", "risk": "low"},
        "http_api": {"port": 80, "protocol": "tcp", "risk": "high"},
        "https_api": {"port": 443, "protocol": "tcp", "risk": "low"}
    }
    
    def __init__(self):
        self.protected_assets: Dict[str, SolarAssetProtection] = {}
        self.baselines: Dict[str, Dict[str, Any]] = {}
    
    def register_asset(self, asset: SolarAssetProtection):
        """Register a solar asset for protection"""
        self.protected_assets[asset.asset_id] = asset
        
        # Create communication baseline
        self.baselines[asset.asset_id] = {
            "expected_ports": self._get_expected_ports(asset),
            "expected_peers": asset.expected_communication,
            "traffic_baseline": None,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Solar asset registered: {asset.asset_id} ({asset.asset_type})")
    
    def _get_expected_ports(self, asset: SolarAssetProtection) -> List[int]:
        """Get expected ports for asset type"""
        port_mapping = {
            "solar_inverter": [502, 443],
            "battery": [502, 443, 1883],
            "smart_meter": [502],
            "gateway": [443, 1883, 8883]
        }
        return port_mapping.get(asset.asset_type, [443])
    
    def check_asset_communication(self, asset_id: str, 
                                  traffic: Dict[str, Any]) -> Dict[str, Any]:
        """Check if asset communication is legitimate"""
        if asset_id not in self.protected_assets:
            return {"error": "Asset not registered"}
        
        asset = self.protected_assets[asset_id]
        baseline = self.baselines[asset_id]
        
        result = {
            "asset_id": asset_id,
            "compliant": True,
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check port usage
        traffic_port = traffic.get("port")
        if traffic_port not in baseline["expected_ports"]:
            result["warnings"].append(f"Unexpected port: {traffic_port}")
        
        # Check destination
        dst_ip = traffic.get("destination_ip")
        expected_peers = [p.get("ip") for p in asset.expected_communication]
        if dst_ip and expected_peers and dst_ip not in expected_peers:
            result["warnings"].append(f"Unexpected destination: {dst_ip}")
            result["compliant"] = False
        
        return result
    
    def isolate_asset(self, asset_id: str, reason: str) -> Dict[str, Any]:
        """Isolate a compromised asset"""
        if asset_id not in self.protected_assets:
            return {"error": "Asset not registered"}
        
        asset = self.protected_assets[asset_id]
        asset.isolated = True
        asset.protection_level = "isolated"
        
        # In production, would update firewall rules to block asset
        
        return {
            "asset_id": asset_id,
            "isolated": True,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_protection_status(self) -> Dict[str, Any]:
        """Get overall protection status"""
        return {
            "total_assets": len(self.protected_assets),
            "protected_assets": len([a for a in self.protected_assets.values() if not a.isolated]),
            "isolated_assets": len([a for a in self.protected_assets.values() if a.isolated]),
            "assets_by_type": self._count_by_type(),
            "protocols_monitored": list(self.SOLAR_PROTOCOLS.keys())
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count assets by type"""
        counts: Dict[str, int] = defaultdict(int)
        for asset in self.protected_assets.values():
            counts[asset.asset_type] += 1
        return dict(counts)


# ─────────────────────────────────────────────────────────────────────────────
# KISWARM EDGE NODE CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class KISWARMEdgeNodeController:
    """
    Master controller for a single KISWARM Edge Node.
    
    Manages all edge security functions for TCS Green Safe House customers.
    """
    
    def __init__(self, node_id: str, customer_id: str, 
                 role: NodeRole = NodeRole.PRIMARY_FIREWALL):
        self.node_id = node_id
        self.customer_id = customer_id
        self.role = role
        
        # Initialize subsystems
        self.firewall = EdgeFirewallEngine(node_id)
        self.hexstrike_agents: Dict[str, HexStrikeResidentialAgent] = {}
        self.solar_protection = SolarAssetProtectionManager()
        
        # Node state
        self.status = "initializing"
        self.start_time = datetime.now()
        self.threat_count = 0
        
        # Initialize HexStrike agents based on role
        self._initialize_agents()
        
        logger.info(f"KISWARM Edge Node {node_id} initialized (role: {role.value})")
    
    def _initialize_agents(self):
        """Initialize HexStrike agents for this node"""
        if self.role == NodeRole.PRIMARY_FIREWALL:
            agent_types = ["network_guardian", "dns_guardian", "anomaly_detector"]
        elif self.role == NodeRole.HEXSTRIKE_AGENT:
            agent_types = ["threat_hunter", "iot_watcher", "solar_protector"]
        else:
            agent_types = ["anomaly_detector"]
        
        for agent_type in agent_types:
            self.hexstrike_agents[agent_type] = HexStrikeResidentialAgent(
                agent_type, self.node_id
            )
    
    def start(self):
        """Start all security functions"""
        self.status = "starting"
        
        # Start all agents
        for agent in self.hexstrike_agents.values():
            agent.start_monitoring()
        
        self.status = "active"
        logger.info(f"KISWARM Edge Node {self.node_id} started")
    
    def stop(self):
        """Stop all security functions"""
        self.status = "stopping"
        
        for agent in self.hexstrike_agents.values():
            agent.stop_monitoring()
        
        self.status = "stopped"
        logger.info(f"KISWARM Edge Node {self.node_id} stopped")
    
    def process_network_traffic(self, traffic: Dict[str, Any]) -> Dict[str, Any]:
        """Process network traffic through all security layers"""
        result = {
            "node_id": self.node_id,
            "timestamp": datetime.now().isoformat(),
            "firewall_decision": None,
            "agent_analyses": [],
            "final_action": "allow"
        }
        
        # Process through firewall
        result["firewall_decision"] = self.firewall.process_packet(traffic)
        
        # Process through HexStrike agents
        for agent_type, agent in self.hexstrike_agents.items():
            analysis = agent.analyze_traffic(traffic)
            result["agent_analyses"].append(analysis)
            
            if analysis["threat_detected"]:
                self.threat_count += 1
                # Create threat event
                event = ThreatEvent(
                    event_id=f"EVT_{int(time.time())}_{secrets.token_hex(4)}",
                    timestamp=datetime.now().isoformat(),
                    threat_type=ResidentialThreatType.NETWORK_INTRUSION,
                    severity=7,
                    source_ip=traffic.get("src_ip", "unknown"),
                    source_port=traffic.get("src_port"),
                    destination_ip=traffic.get("dst_ip", "unknown"),
                    destination_port=traffic.get("dst_port"),
                    protocol=traffic.get("protocol", "unknown"),
                    payload_hash=None,
                    action_taken="blocked",
                    rule_triggered="agent_detection",
                    node_id=self.node_id,
                    ai_confidence=analysis["confidence"]
                )
                self.firewall.log_threat(event)
        
        # Determine final action
        if result["firewall_decision"]["action"] == "block":
            result["final_action"] = "blocked"
        
        for analysis in result["agent_analyses"]:
            if analysis.get("threat_detected"):
                result["final_action"] = "blocked_quarantined"
                break
        
        return result
    
    def register_solar_asset(self, asset: SolarAssetProtection):
        """Register a solar asset for protection"""
        self.solar_protection.register_asset(asset)
    
    def get_node_status(self) -> Dict[str, Any]:
        """Get comprehensive node status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "node_id": self.node_id,
            "customer_id": self.customer_id,
            "role": self.role.value,
            "status": self.status,
            "uptime_seconds": int(uptime),
            "threat_count": self.threat_count,
            "firewall_stats": self.firewall.get_statistics(),
            "agent_statuses": {
                atype: agent.get_status() 
                for atype, agent in self.hexstrike_agents.items()
            },
            "solar_protection": self.solar_protection.get_protection_status()
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3-NODE CLUSTER CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class ThreeNodeClusterController:
    """
    Controller for 3-node GT15 Max cluster.
    
    Architecture:
    - Node 1: Primary Firewall (8 cores, 8GB VRAM)
    - Node 2: HexStrike Agents (4 cores, 10GB VRAM)
    - Node 3: Swarm Coordination (4 cores, 12GB VRAM)
    
    Network Topology:
    - WAN (eth0) → Node 1 → Node 2 → LAN (eth1)
    - Node 3: Management and coordination
    """
    
    def __init__(self, cluster_id: str, customer_id: str):
        self.cluster_id = cluster_id
        self.customer_id = customer_id
        
        # Initialize nodes
        self.nodes: Dict[str, KISWARMEdgeNodeController] = {}
        self.swarm = SwarmCoordinationLayer(cluster_id)
        
        # Cluster state
        self.status = "initializing"
        self.failover_mode = False
        
        # Initialize cluster
        self._initialize_cluster()
    
    def _initialize_cluster(self):
        """Initialize the 3-node cluster"""
        node_configs = [
            ("node_1", NodeRole.PRIMARY_FIREWALL),
            ("node_2", NodeRole.HEXSTRIKE_AGENT),
            ("node_3", NodeRole.SWARM_COORDINATOR)
        ]
        
        for node_id, role in node_configs:
            node = KISWARMEdgeNodeController(
                node_id=f"{self.cluster_id}_{node_id}",
                customer_id=self.customer_id,
                role=role
            )
            self.nodes[node_id] = node
            
            # Register with swarm
            edge_node = EdgeNode(
                node_id=f"{self.cluster_id}_{node_id}",
                serial_number=f"GT15_{secrets.token_hex(8)}",
                role=role,
                ip_address=self._get_node_ip(node_id),
                mac_address=f"02:00:00:{secrets.token_hex(6)}",
                models_loaded=[],
                status="initialized"
            )
            self.swarm.register_node(edge_node)
        
        self.status = "initialized"
        logger.info(f"3-Node Cluster {self.cluster_id} initialized for customer {self.customer_id}")
    
    def _get_node_ip(self, node_id: str) -> str:
        """Get IP address for node"""
        base_ip = "192.168.100"
        node_num = int(node_id.split("_")[1])
        return f"{base_ip}.{10 + node_num}"
    
    def start_cluster(self):
        """Start all nodes in the cluster"""
        self.status = "starting"
        
        for node in self.nodes.values():
            node.start()
        
        self.status = "active"
        logger.info(f"Cluster {self.cluster_id} started")
    
    def stop_cluster(self):
        """Stop all nodes in the cluster"""
        for node in self.nodes.values():
            node.stop()
        
        self.status = "stopped"
        logger.info(f"Cluster {self.cluster_id} stopped")
    
    def process_traffic(self, traffic: Dict[str, Any]) -> Dict[str, Any]:
        """Process traffic through the cluster"""
        result = {
            "cluster_id": self.cluster_id,
            "timestamp": datetime.now().isoformat(),
            "node_results": {},
            "final_decision": "allow"
        }
        
        # Process through primary firewall first
        if "node_1" in self.nodes:
            result["node_results"]["firewall"] = self.nodes["node_1"].process_network_traffic(traffic)
        
        # Process through HexStrike node
        if "node_2" in self.nodes:
            result["node_results"]["hexstrike"] = self.nodes["node_2"].process_network_traffic(traffic)
        
        # Determine final decision
        all_blocked = any(
            r.get("final_action", "").startswith("block")
            for r in result["node_results"].values()
        )
        
        if all_blocked:
            result["final_decision"] = "blocked"
        
        return result
    
    def handle_node_failure(self, failed_node_id: str):
        """Handle node failure with failover"""
        logger.warning(f"Node failure detected: {failed_node_id}")
        
        self.failover_mode = True
        
        # Determine failover strategy
        if failed_node_id == "node_1":
            # Promote node 2 to primary
            logger.info("Failing over to node_2 as primary firewall")
            self.nodes["node_2"].role = NodeRole.PRIMARY_FIREWALL
        
        elif failed_node_id == "node_2":
            # Distribute HexStrike duties to node 3
            logger.info("Distributing HexStrike duties to remaining nodes")
        
        elif failed_node_id == "node_3":
            # Swarm coordination falls back to node 1
            logger.info("Swarm coordination falling back to node_1")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status"""
        return {
            "cluster_id": self.cluster_id,
            "customer_id": self.customer_id,
            "status": self.status,
            "failover_mode": self.failover_mode,
            "nodes": {
                nid: node.get_node_status() 
                for nid, node in self.nodes.items()
            },
            "swarm_status": self.swarm.get_cluster_status(),
            "hardware_specs": GT15MAX_SPECS,
            "model_allocation": EDGE_MODEL_ALLOCATION
        }


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def create_edge_cluster(cluster_id: str, customer_id: str) -> ThreeNodeClusterController:
    """Create a new edge cluster for a TCS customer"""
    return ThreeNodeClusterController(cluster_id, customer_id)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║         KISWARM EDGE FIREWALL v6.0.0                                 ║
    ║         TCS Green Safe House - Residential Security Node             ║
    ║         3x GT15 Max Cluster Configuration                            ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  Hardware: GEEKOM GT15 Max (Intel Ultra 9, 128GB RAM, Arc 140T)     ║
    ║  Network:  Dual 2.5G LAN + Wi-Fi 7                                   ║
    ║  Capacity: 6-8 LLM models, 100-140 tok/s inference                   ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create a test cluster
    cluster = create_edge_cluster("CLUSTER_001", "TCS_CUSTOMER_001")
    cluster.start_cluster()
    
    status = cluster.get_cluster_status()
    print(json.dumps(status, indent=2, default=str))
