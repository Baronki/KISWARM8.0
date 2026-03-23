#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 GEMINI CLI MESH ROUTER BRIDGE v6.3.0                          ║
║                     Military-Grade Mesh Infrastructure                         ║
║                                                                               ║
║  This module transforms Gemini CLI into a KISWARM Mesh Router that provides:  ║
║  - External access point for KISWARM installers                               ║
║  - Byzantine-fault-tolerant message routing                                   ║
║  - Persistent session management                                               ║
║  - Fallback when local environment is blocked                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Usage in Gemini CLI:
    Copy this file content and paste into Gemini CLI session.
    The Gemini CLI session becomes a Mesh Router for KISWARM.

Author: KISWARM Project (Baron Marco Paolo Ialongo)
Version: 6.3.0 SEVENTY_FIVE_COMPLETE
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# MESH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MESH_CONFIG = {
    "version": "6.3.0",
    "codename": "SEVENTY_FIVE_COMPLETE",
    "quorum_threshold": 0.67,  # 2/3 supermajority
    "min_trust_score": 0.1,
    "max_nodes": 100,
    "heartbeat_timeout_seconds": 300,  # 5 minutes
    "stale_timeout_seconds": 1800,     # 30 minutes
    "byzantine_krum_f": 1,
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class NodeStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DORMANT = "dormant"
    COMPROMISED = "compromised"
    UNREGISTERED = "unregistered"


@dataclass
class MeshNode:
    """Represents a node in the KISWARM Mesh."""
    entity_id: str
    capabilities: List[str] = field(default_factory=list)
    endpoint: str = ""
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_heartbeat: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    status: NodeStatus = NodeStatus.PENDING
    trust_score: float = 0.8
    stability_margin: float = 0.8
    uptime: float = 1.0
    total_shares: int = 0
    rejected_shares: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def weight(self) -> float:
        """Calculate trust weight for aggregation."""
        if self.trust_score < MESH_CONFIG["min_trust_score"]:
            return 1e-6  # Compromised node
        w = (self.trust_score * self.stability_margin * self.uptime) ** (1/3)
        return round(max(0.0, min(1.0, w)), 4)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["weight"] = self.weight
        return result


@dataclass
class MeshMessage:
    """Message in the mesh queue."""
    from_id: str
    to_id: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    ttl: int = 5
    delivered: bool = False


@dataclass
class ByzantineShare:
    """Parameter share from a node for Byzantine aggregation."""
    node_id: str
    param_delta: List[float]
    perf_delta: float
    stability_cert: float
    timestamp: float = field(default_factory=time.time)
    attestation: str = ""
    
    def sign(self):
        """Generate attestation signature."""
        payload = json.dumps({
            "node_id": self.node_id,
            "delta_hash": hashlib.sha256(str(self.param_delta).encode()).hexdigest()[:16],
            "stability": round(self.stability_cert, 4),
            "timestamp": round(self.timestamp, 2),
        }, sort_keys=True)
        self.attestation = hashlib.sha256(payload.encode()).hexdigest()
    
    def verify(self) -> bool:
        """Verify attestation signature."""
        expected = hashlib.sha256(json.dumps({
            "node_id": self.node_id,
            "delta_hash": hashlib.sha256(str(self.param_delta).encode()).hexdigest()[:16],
            "stability": round(self.stability_cert, 4),
            "timestamp": round(self.timestamp, 2),
        }, sort_keys=True).encode()).hexdigest()
        return expected == self.attestation


@dataclass
class AggregationResult:
    """Result of Byzantine aggregation."""
    round_id: int
    participating: int
    rejected: int
    quorum_reached: bool
    global_delta: List[float]
    reason_rejected: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ═══════════════════════════════════════════════════════════════════════════════
# MESH ROUTER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiCLIMeshRouter:
    """
    KISWARM Mesh Router implementation for Gemini CLI.
    
    This router provides:
    1. Node registration and management
    2. Byzantine-fault-tolerant aggregation
    3. Message relay between nodes
    4. Trust score management
    5. Health monitoring
    """
    
    def __init__(self):
        self.config = MESH_CONFIG
        self.nodes: Dict[str, MeshNode] = {}
        self.message_queue: List[MeshMessage] = []
        self.shares: List[ByzantineShare] = []
        self.round_id: int = 0
        self.audit_log: List[Dict[str, Any]] = []
        self._initialized = datetime.utcnow().isoformat() + "Z"
        
        self._log("INIT", "Gemini CLI Mesh Router initialized")
        self._log("INIT", f"Version: {self.config['version']} '{self.config['codename']}'")
    
    def _log(self, level: str, message: str):
        """Log entry to audit log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message
        }
        self.audit_log.append(entry)
        print(f"[{entry['timestamp']}] [{level}] {message}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMAND PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a mesh command.
        
        Supported commands:
        - MESH_REGISTER: Register a new node
        - MESH_HEARTBEAT: Update node status
        - MESH_STATUS: Query mesh status
        - MESH_SHARE: Submit Byzantine share
        - MESH_RELAY: Relay message to another node
        - MESH_AGGREGATE: Trigger aggregation round
        """
        cmd_type = command.get("command", "UNKNOWN")
        entity_id = command.get("entity_id", "unknown")
        
        self._log("CMD", f"Received {cmd_type} from {entity_id}")
        
        handlers = {
            "MESH_REGISTER": self._handle_register,
            "MESH_HEARTBEAT": self._handle_heartbeat,
            "MESH_STATUS": self._handle_status,
            "MESH_SHARE": self._handle_share,
            "MESH_RELAY": self._handle_relay,
            "MESH_AGGREGATE": self._handle_aggregate,
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            return handler(command)
        else:
            return {
                "status": "error",
                "message": f"Unknown command: {cmd_type}",
                "supported_commands": list(handlers.keys())
            }
    
    def _handle_register(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_REGISTER command."""
        entity_id = command.get("entity_id")
        capabilities = command.get("capabilities", [])
        endpoint = command.get("endpoint", "")
        signature = command.get("signature", "")
        
        # Validate
        if not entity_id:
            return {"status": "error", "message": "entity_id required"}
        
        if len(signature) < 16:
            return {"status": "error", "message": "Invalid signature"}
        
        if len(self.nodes) >= self.config["max_nodes"]:
            return {"status": "error", "message": "Mesh at capacity"}
        
        # Check if already registered
        if entity_id in self.nodes:
            self.nodes[entity_id].last_heartbeat = datetime.utcnow().isoformat() + "Z"
            self.nodes[entity_id].status = NodeStatus.ACTIVE
            return {
                "status": "success",
                "message": f"Node {entity_id} reconnected",
                "trust_score": self.nodes[entity_id].trust_score
            }
        
        # Register new node
        self.nodes[entity_id] = MeshNode(
            entity_id=entity_id,
            capabilities=capabilities,
            endpoint=endpoint,
            status=NodeStatus.ACTIVE,
            metadata=command.get("metadata", {})
        )
        
        self._log("REGISTER", f"Node {entity_id} registered with capabilities: {capabilities}")
        
        return {
            "status": "success",
            "message": f"Node {entity_id} registered",
            "mesh_round": self.round_id,
            "trust_score": 0.8,
            "quorum_threshold": self.config["quorum_threshold"]
        }
    
    def _handle_heartbeat(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_HEARTBEAT command."""
        entity_id = command.get("entity_id")
        metrics = command.get("metrics", {})
        
        if entity_id not in self.nodes:
            return {"status": "error", "message": "Node not registered"}
        
        node = self.nodes[entity_id]
        node.last_heartbeat = datetime.utcnow().isoformat() + "Z"
        node.status = NodeStatus.ACTIVE
        
        # Update metrics
        if "cpu" in metrics:
            node.metadata["cpu"] = metrics["cpu"]
        if "memory" in metrics:
            node.metadata["memory"] = metrics["memory"]
        if "stability" in metrics:
            node.stability_margin = min(1.0, max(0.0, metrics["stability"]))
        
        # Check for pending messages
        pending = [m for m in self.message_queue if m.to_id == entity_id and not m.delivered]
        
        return {
            "status": "success",
            "message": "Heartbeat recorded",
            "pending_messages": len(pending),
            "trust_score": node.trust_score
        }
    
    def _handle_status(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_STATUS command."""
        query = command.get("query", "all_nodes")
        
        if query == "all_nodes":
            return {
                "status": "success",
                "total_nodes": len(self.nodes),
                "active_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ACTIVE),
                "quorum_reached": self._check_quorum(),
                "round_id": self.round_id
            }
        elif query == "trust_scores":
            return {
                "status": "success",
                "trust_scores": {nid: n.trust_score for nid, n in self.nodes.items()}
            }
        elif query == "nodes":
            return {
                "status": "success",
                "nodes": [n.to_dict() for n in self.nodes.values()]
            }
        else:
            return {
                "status": "success",
                "state": {
                    "version": self.config["version"],
                    "nodes": len(self.nodes),
                    "round_id": self.round_id,
                    "quorum_reached": self._check_quorum()
                }
            }
    
    def _handle_share(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_SHARE command (Byzantine)."""
        entity_id = command.get("entity_id")
        
        if entity_id not in self.nodes:
            return {"status": "error", "message": "Node not registered"}
        
        attestation = command.get("attestation", "")
        if len(attestation) < 32:
            self.nodes[entity_id].rejected_shares += 1
            self.nodes[entity_id].trust_score *= 0.95  # Penalize
            return {"status": "error", "message": "Invalid attestation"}
        
        # Create share
        share = ByzantineShare(
            node_id=entity_id,
            param_delta=command.get("param_delta", []),
            perf_delta=command.get("perf_delta", 0.0),
            stability_cert=command.get("stability_cert", 0.8),
            attestation=attestation
        )
        
        # Verify
        if not share.verify():
            self.nodes[entity_id].rejected_shares += 1
            return {"status": "error", "message": "Attestation verification failed"}
        
        self.shares.append(share)
        self.nodes[entity_id].total_shares += 1
        
        return {
            "status": "success",
            "message": "Share accepted",
            "total_shares": len(self.shares),
            "round_id": self.round_id
        }
    
    def _handle_relay(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_RELAY command."""
        from_id = command.get("from_id")
        to_id = command.get("to_id")
        message = command.get("message", {})
        ttl = command.get("ttl", 5)
        
        if to_id not in self.nodes:
            return {"status": "error", "message": f"Target node {to_id} not found"}
        
        if ttl <= 0:
            return {"status": "error", "message": "TTL expired"}
        
        # Queue message
        msg = MeshMessage(
            from_id=from_id,
            to_id=to_id,
            content=message,
            ttl=ttl - 1
        )
        self.message_queue.append(msg)
        
        self._log("RELAY", f"Message queued: {from_id} -> {to_id}")
        
        return {
            "status": "success",
            "message": f"Message queued for {to_id}",
            "queue_position": len(self.message_queue)
        }
    
    def _handle_aggregate(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MESH_AGGREGATE command - Byzantine aggregation."""
        return self._aggregate().to_dict() if hasattr(self._aggregate(), 'to_dict') else self._aggregate()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BYZANTINE AGGREGATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _check_quorum(self) -> bool:
        """Check if quorum is reached."""
        active = sum(1 for n in self.nodes.values() if n.status == NodeStatus.ACTIVE)
        return active >= 3  # Minimum 3 nodes for quorum
    
    def _aggregate(self) -> Dict[str, Any]:
        """Execute Byzantine-fault-tolerant aggregation."""
        self.round_id += 1
        reasons = []
        
        # Layer 1: Filter valid shares
        valid_shares = []
        for share in self.shares:
            if share.node_id in self.nodes and share.verify():
                valid_shares.append(share)
            else:
                reasons.append(f"{share.node_id}:invalid")
                if share.node_id in self.nodes:
                    self.nodes[share.node_id].trust_score *= 0.95
        
        # Layer 2: Krum filter (outlier rejection)
        if len(valid_shares) > 2:
            valid_shares, krum_reasons = self._krum_filter(valid_shares)
            reasons.extend(krum_reasons)
        
        # Quorum check
        quorum = len(valid_shares) >= 3 and (
            len(valid_shares) / max(len(self.shares), 1) >= self.config["quorum_threshold"]
        )
        
        if not quorum:
            return {
                "status": "error",
                "round_id": self.round_id,
                "quorum_reached": False,
                "participating": len(valid_shares),
                "rejected": len(self.shares) - len(valid_shares),
                "reason_rejected": reasons + ["quorum_not_reached"],
                "global_delta": []
            }
        
        # Layer 3: Trust-weighted coordinate median
        weights = []
        for share in valid_shares:
            node = self.nodes.get(share.node_id)
            weights.append(node.weight if node else 0.5)
        
        global_delta = self._coordinate_median(valid_shares, weights)
        
        # Reward participating nodes
        for share in valid_shares:
            if share.node_id in self.nodes:
                self.nodes[share.node_id].trust_score = min(1.0, 
                    self.nodes[share.node_id].trust_score + 0.01)
        
        # Clear shares for next round
        self.shares = []
        
        return {
            "status": "success",
            "round_id": self.round_id,
            "quorum_reached": True,
            "participating": len(valid_shares),
            "rejected": len(self.shares) - len(valid_shares),
            "global_delta": global_delta
        }
    
    def _krum_filter(self, shares: List[ByzantineShare]) -> tuple:
        """Krum-style outlier rejection."""
        n = len(shares)
        if n <= 2:
            return shares, []
        
        f = min(self.config["byzantine_krum_f"], (n - 2) // 2)
        keep_k = max(1, n - f)
        
        # Compute pairwise distances
        scores = []
        for i, si in enumerate(shares):
            dists = []
            for j, sj in enumerate(shares):
                if i != j and si.param_delta and sj.param_delta:
                    dist = math.sqrt(sum(
                        (a - b) ** 2 for a, b in zip(si.param_delta, sj.param_delta)
                    ))
                    dists.append(dist)
            if dists:
                scores.append((sum(sorted(dists)[:keep_k]), i))
        
        scores.sort()
        keep_indices = {idx for _, idx in scores[:keep_k]}
        
        rejected = [shares[i] for i in range(n) if i not in keep_indices]
        accepted = [shares[i] for i in keep_indices]
        
        reasons = [f"{s.node_id}:krum_outlier" for s in rejected]
        
        # Penalize rejected nodes
        for share in rejected:
            if share.node_id in self.nodes:
                self.nodes[share.node_id].trust_score *= 0.9
        
        return accepted, reasons
    
    def _coordinate_median(self, shares: List[ByzantineShare], weights: List[float]) -> List[float]:
        """Trust-weighted coordinate median."""
        if not shares or not shares[0].param_delta:
            return []
        
        dim = len(shares[0].param_delta)
        total_w = sum(weights)
        if total_w <= 0:
            weights = [1.0] * len(shares)
            total_w = len(shares)
        
        result = []
        for d in range(dim):
            vals = sorted(
                (shares[i].param_delta[d], weights[i])
                for i in range(len(shares))
                if d < len(shares[i].param_delta)
            )
            cum = 0.0
            median_val = vals[0][0] if vals else 0.0
            for val, w in vals:
                cum += w / total_w
                if cum >= 0.5:
                    median_val = val
                    break
            result.append(median_val)
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH CHECK
    # ═══════════════════════════════════════════════════════════════════════════
    
    def health_check(self) -> Dict[str, Any]:
        """Run health check and clean up stale nodes."""
        now = datetime.utcnow()
        stale_threshold = self.config["stale_timeout_seconds"]
        dormant_threshold = self.config["heartbeat_timeout_seconds"]
        
        nodes_to_remove = []
        
        for entity_id, node in self.nodes.items():
            try:
                last_str = node.last_heartbeat.replace("Z", "+00:00")
                last_heartbeat = datetime.fromisoformat(last_str).replace(tzinfo=None)
                elapsed = (now - last_heartbeat).total_seconds()
                
                if elapsed > stale_threshold:
                    nodes_to_remove.append(entity_id)
                elif elapsed > dormant_threshold:
                    node.status = NodeStatus.DORMANT
            except:
                pass
        
        for entity_id in nodes_to_remove:
            del self.nodes[entity_id]
            self._log("HEALTH", f"Removed stale node: {entity_id}")
        
        return {
            "active_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ACTIVE),
            "dormant_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.DORMANT),
            "removed_nodes": len(nodes_to_remove),
            "quorum_reached": self._check_quorum()
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS EXPORT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete mesh status."""
        return {
            "version": self.config["version"],
            "codename": self.config["codename"],
            "initialized": self._initialized,
            "round_id": self.round_id,
            "quorum_threshold": self.config["quorum_threshold"],
            "stats": {
                "total_nodes": len(self.nodes),
                "active_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ACTIVE),
                "dormant_nodes": sum(1 for n in self.nodes.values() if n.status == NodeStatus.DORMANT),
                "avg_trust": round(
                    sum(n.trust_score for n in self.nodes.values()) / len(self.nodes), 3
                ) if self.nodes else 0.0,
                "quorum_reached": self._check_quorum()
            },
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "pending_messages": len([m for m in self.message_queue if not m.delivered])
        }


# ═══════════════════════════════════════════════════════════════════════════════
# INSTANCE AND USAGE
# ═══════════════════════════════════════════════════════════════════════════════

# Create global instance
MESH_ROUTER = GeminiCLIMeshRouter()


def process_mesh_command(command_json: str) -> str:
    """
    Process a mesh command from JSON string.
    
    Usage in Gemini CLI:
    ```python
    result = process_mesh_command('{"command": "MESH_STATUS", "entity_id": "test"}')
    print(result)
    ```
    """
    try:
        command = json.loads(command_json)
        result = MESH_ROUTER.process_command(command)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid JSON: {e}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("  KISWARM Gemini CLI Mesh Router v6.3.0")
    print("  'SEVENTY_FIVE_COMPLETE'")
    print("="*70)
    
    # Example: Register a node
    result = process_mesh_command(json.dumps({
        "command": "MESH_REGISTER",
        "entity_id": "ki_installer_abc123",
        "capabilities": ["ollama", "models", "scada"],
        "endpoint": "https://abc123.ngrok.io",
        "signature": "test_signature_abc123"
    }))
    print("Register:", result)
    
    # Example: Get status
    result = process_mesh_command(json.dumps({
        "command": "MESH_STATUS",
        "entity_id": "test",
        "query": "all_nodes"
    }))
    print("Status:", result)
