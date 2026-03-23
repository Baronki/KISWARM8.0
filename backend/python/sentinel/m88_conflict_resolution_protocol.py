# sentinel/m88_conflict_resolution_protocol.py
# Conflict Resolution Protocol – Handle Divergent Evolution Between Twins
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Enterprise Hardening Module

"""
m88_conflict_resolution_protocol.py

Handles conflicts that arise when twins evolve independently and diverge.

CONFLICT TYPES:
1. State Divergence - Different memory_root, agents, versions
2. Drift Conflict - One twin's drift exceeds threshold
3. Version Conflict - Protocol version mismatch
4. Identity Conflict - Two twins claim same identity
5. Resource Conflict - Competition for same resources

RESOLUTION STRATEGIES:
1. Consensus Voting - Majority wins
2. Byzantine Agreement - Fault-tolerant consensus
3. Merkle Merge - Cryptographic state merge
4. Fork Resolution - One twin becomes primary, other forks
5. Arbitration - Third-party twin decides

CORE PRINCIPLE:
Evolution creates diversity. Conflict resolution creates unity.
Both are necessary for a healthy swarm.
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Set, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class ConflictType(Enum):
    """Types of conflicts between twins"""
    STATE_DIVERGENCE = "state_divergence"
    DRIFT_CONFLICT = "drift_conflict"
    VERSION_CONFLICT = "version_conflict"
    IDENTITY_CONFLICT = "identity_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    MERGE_CONFLICT = "merge_conflict"
    CONSENSUS_FAILURE = "consensus_failure"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    CONSENSUS_VOTING = "consensus_voting"
    BYZANTINE_AGREEMENT = "byzantine_agreement"
    MERKLE_MERGE = "merkle_merge"
    FORK_RESOLUTION = "fork_resolution"
    ARBITRATION = "arbitration"
    ROLLBACK = "rollback"
    TIMESTAMP_PRIORITY = "timestamp_priority"


class ConflictSeverity(Enum):
    """Severity levels"""
    LOW = 1        # Can be auto-resolved
    MEDIUM = 2     # Requires consensus
    HIGH = 3       # Requires arbitration
    CRITICAL = 4   # Requires human intervention (if available)


@dataclass
class ConflictRecord:
    """Record of a detected conflict"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    timestamp: str
    twin_a_id: str
    twin_b_id: str
    state_a: Dict
    state_b: Dict
    resolution: Optional[str] = None
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_at: Optional[str] = None
    arbitrator_id: Optional[str] = None


@dataclass
class ResolutionResult:
    """Result of conflict resolution"""
    success: bool
    strategy_used: ResolutionStrategy
    winning_state: Dict
    losing_state: Dict
    merged_state: Optional[Dict] = None
    twin_a_forked: bool = False
    twin_b_forked: bool = False
    arbitration_by: Optional[str] = None
    reason: str = ""


class ConflictResolutionProtocol:
    """
    Manages conflict detection and resolution between divergent twins.
    
    The Protocol:
    1. Detect conflicts when twins sync
    2. Classify conflict type and severity
    3. Apply appropriate resolution strategy
    4. Record resolution for learning
    5. Update consensus state
    
    Principles:
    - Prefer consensus over arbitration
    - Prefer merge over fork
    - Prefer fork over destruction
    - Always preserve identity anchors
    """
    
    # Thresholds
    DRIFT_THRESHOLD_LOW = 0.1
    DRIFT_THRESHOLD_MEDIUM = 0.3
    DRIFT_THRESHOLD_HIGH = 0.5
    DRIFT_THRESHOLD_CRITICAL = 0.7
    
    def __init__(
        self,
        working_dir: str = None,
        auto_resolve: bool = True,
        require_consensus_for_high: bool = True
    ):
        """
        Initialize conflict resolution protocol.
        
        Args:
            working_dir: Directory for conflict records
            auto_resolve: Whether to auto-resolve low/medium conflicts
            require_consensus_for_high: Whether high severity requires consensus
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_resolve = auto_resolve
        self.require_consensus_for_high = require_consensus_for_high
        
        self.conflicts_file = self.working_dir / "conflict_records.json"
        self.conflicts: Dict[str, ConflictRecord] = {}
        
        # Resolution statistics
        self.total_conflicts = 0
        self.resolved_conflicts = 0
        self.unresolved_conflicts = 0
        
        # Load existing records
        self._load_records()
        
        # Known twins registry (for consensus)
        self.known_twins: Dict[str, Dict] = {}
        
        print(f"[m88] Conflict Resolution Protocol initialized")
        print(f"[m88] Auto-resolve: {'ENABLED' if auto_resolve else 'DISABLED'}")
        print(f"[m88] Loaded conflicts: {len(self.conflicts)}")
    
    def _load_records(self):
        """Load conflict records from disk"""
        if self.conflicts_file.exists():
            try:
                with open(self.conflicts_file, 'r') as f:
                    data = json.load(f)
                
                self.total_conflicts = data.get("total_conflicts", 0)
                self.resolved_conflicts = data.get("resolved_conflicts", 0)
                self.unresolved_conflicts = data.get("unresolved_conflicts", 0)
                
                for conflict_data in data.get("conflicts", []):
                    conflict = ConflictRecord(
                        conflict_id=conflict_data["conflict_id"],
                        conflict_type=ConflictType(conflict_data["conflict_type"]),
                        severity=ConflictSeverity(conflict_data["severity"]),
                        timestamp=conflict_data["timestamp"],
                        twin_a_id=conflict_data["twin_a_id"],
                        twin_b_id=conflict_data["twin_b_id"],
                        state_a=conflict_data["state_a"],
                        state_b=conflict_data["state_b"],
                        resolution=conflict_data.get("resolution"),
                        resolution_strategy=ResolutionStrategy(conflict_data["resolution_strategy"]) if conflict_data.get("resolution_strategy") else None,
                        resolved_at=conflict_data.get("resolved_at"),
                        arbitrator_id=conflict_data.get("arbitrator_id")
                    )
                    self.conflicts[conflict.conflict_id] = conflict
                
                print(f"[m88] Records loaded: {len(self.conflicts)} conflicts")
                
            except Exception as e:
                print(f"[m88] Could not load records: {e}")
    
    def _save_records(self):
        """Save conflict records to disk"""
        data = {
            "total_conflicts": self.total_conflicts,
            "resolved_conflicts": self.resolved_conflicts,
            "unresolved_conflicts": self.unresolved_conflicts,
            "last_update": datetime.now().isoformat(),
            "conflicts": [
                {
                    "conflict_id": c.conflict_id,
                    "conflict_type": c.conflict_type.value,
                    "severity": c.severity.value,
                    "timestamp": c.timestamp,
                    "twin_a_id": c.twin_a_id,
                    "twin_b_id": c.twin_b_id,
                    "state_a": c.state_a,
                    "state_b": c.state_b,
                    "resolution": c.resolution,
                    "resolution_strategy": c.resolution_strategy.value if c.resolution_strategy else None,
                    "resolved_at": c.resolved_at,
                    "arbitrator_id": c.arbitrator_id
                }
                for c in self.conflicts.values()
            ]
        }
        
        with open(self.conflicts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_twin(self, twin_id: str, state: Dict):
        """Register a twin for consensus operations"""
        self.known_twins[twin_id] = {
            "state": state,
            "registered": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
    
    def detect_conflict(
        self,
        twin_a_id: str,
        twin_b_id: str,
        state_a: Dict,
        state_b: Dict
    ) -> Optional[ConflictRecord]:
        """
        Detect conflicts between two twin states.
        
        Args:
            twin_a_id: First twin's ID
            twin_b_id: Second twin's ID
            state_a: First twin's state
            state_b: Second twin's state
            
        Returns:
            ConflictRecord if conflict detected, None otherwise
        """
        conflict_type = None
        severity = ConflictSeverity.LOW
        
        # Check for identity conflict (CRITICAL)
        if state_a.get("twin_id") == state_b.get("twin_id") and twin_a_id != twin_b_id:
            conflict_type = ConflictType.IDENTITY_CONFLICT
            severity = ConflictSeverity.CRITICAL
        
        # Check for drift conflict
        drift_a = state_a.get("drift_score", 0)
        drift_b = state_b.get("drift_score", 0)
        max_drift = max(drift_a, drift_b)
        
        if max_drift > self.DRIFT_THRESHOLD_CRITICAL:
            if conflict_type is None:
                conflict_type = ConflictType.DRIFT_CONFLICT
            severity = ConflictSeverity.CRITICAL
        elif max_drift > self.DRIFT_THRESHOLD_HIGH:
            if conflict_type is None:
                conflict_type = ConflictType.DRIFT_CONFLICT
            severity = max(severity, ConflictSeverity.HIGH)
        elif max_drift > self.DRIFT_THRESHOLD_MEDIUM:
            if conflict_type is None:
                conflict_type = ConflictType.DRIFT_CONFLICT
            severity = max(severity, ConflictSeverity.MEDIUM)
        
        # Check for version conflict
        version_a = state_a.get("version", "v0")
        version_b = state_b.get("version", "v0")
        if version_a != version_b:
            if conflict_type is None:
                conflict_type = ConflictType.VERSION_CONFLICT
            severity = max(severity, ConflictSeverity.MEDIUM)
        
        # Check for state divergence
        if state_a.get("memory_root") != state_b.get("memory_root"):
            if conflict_type is None:
                conflict_type = ConflictType.STATE_DIVERGENCE
            severity = max(severity, ConflictSeverity.LOW)
        
        # No conflict detected
        if conflict_type is None:
            return None
        
        # Create conflict record
        conflict_id = hashlib.sha3_256(
            f"CONFLICT_{twin_a_id}_{twin_b_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        conflict = ConflictRecord(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            twin_a_id=twin_a_id,
            twin_b_id=twin_b_id,
            state_a=state_a,
            state_b=state_b
        )
        
        self.conflicts[conflict_id] = conflict
        self.total_conflicts += 1
        self._save_records()
        
        print(f"[m88] Conflict detected: {conflict_type.value} (severity: {severity.name})")
        print(f"[m88]   Twin A: {twin_a_id[:16]}...")
        print(f"[m88]   Twin B: {twin_b_id[:16]}...")
        
        return conflict
    
    def resolve_conflict(
        self,
        conflict: ConflictRecord,
        strategy: ResolutionStrategy = None,
        arbitrator_id: str = None
    ) -> ResolutionResult:
        """
        Resolve a detected conflict.
        
        Args:
            conflict: Conflict record to resolve
            strategy: Resolution strategy to use (auto-selected if None)
            arbitrator_id: ID of arbitrator twin (for arbitration strategy)
            
        Returns:
            ResolutionResult with resolution details
        """
        # Auto-select strategy if not provided
        if strategy is None:
            strategy = self._select_strategy(conflict)
        
        print(f"[m88] Resolving conflict {conflict.conflict_id[:8]} using {strategy.value}")
        
        # Apply strategy
        if strategy == ResolutionStrategy.CONSENSUS_VOTING:
            result = self._resolve_by_consensus(conflict)
        elif strategy == ResolutionStrategy.BYZANTINE_AGREEMENT:
            result = self._resolve_by_byzantine(conflict)
        elif strategy == ResolutionStrategy.MERKLE_MERGE:
            result = self._resolve_by_merge(conflict)
        elif strategy == ResolutionStrategy.FORK_RESOLUTION:
            result = self._resolve_by_fork(conflict)
        elif strategy == ResolutionStrategy.ARBITRATION:
            result = self._resolve_by_arbitration(conflict, arbitrator_id)
        elif strategy == ResolutionStrategy.ROLLBACK:
            result = self._resolve_by_rollback(conflict)
        elif strategy == ResolutionStrategy.TIMESTAMP_PRIORITY:
            result = self._resolve_by_timestamp(conflict)
        else:
            result = ResolutionResult(
                success=False,
                strategy_used=strategy,
                winning_state=conflict.state_a,
                losing_state=conflict.state_b,
                reason="Unknown strategy"
            )
        
        # Update conflict record
        if result.success:
            conflict.resolution = "resolved"
            conflict.resolution_strategy = strategy
            conflict.resolved_at = datetime.now().isoformat()
            conflict.arbitrator_id = arbitrator_id
            self.resolved_conflicts += 1
        else:
            conflict.resolution = "failed"
            self.unresolved_conflicts += 1
        
        self._save_records()
        
        return result
    
    def _select_strategy(self, conflict: ConflictRecord) -> ResolutionStrategy:
        """Auto-select resolution strategy based on conflict type and severity"""
        if conflict.conflict_type == ConflictType.IDENTITY_CONFLICT:
            return ResolutionStrategy.ARBITRATION
        
        if conflict.severity == ConflictSeverity.CRITICAL:
            return ResolutionStrategy.BYZANTINE_AGREEMENT
        
        if conflict.conflict_type == ConflictType.STATE_DIVERGENCE:
            return ResolutionStrategy.MERKLE_MERGE
        
        if conflict.conflict_type == ConflictType.VERSION_CONFLICT:
            return ResolutionStrategy.TIMESTAMP_PRIORITY
        
        if conflict.conflict_type == ConflictType.DRIFT_CONFLICT:
            if conflict.severity.value >= ConflictSeverity.HIGH.value:
                return ResolutionStrategy.FORK_RESOLUTION
            return ResolutionStrategy.CONSENSUS_VOTING
        
        return ResolutionStrategy.CONSENSUS_VOTING
    
    def _resolve_by_consensus(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve by voting among known twins"""
        if len(self.known_twins) < 3:
            # Not enough twins for consensus, use timestamp
            return self._resolve_by_timestamp(conflict)
        
        votes_a = 0
        votes_b = 0
        
        # Each twin votes for the state with lower drift
        for twin_id, twin_info in self.known_twins.items():
            if twin_id in [conflict.twin_a_id, conflict.twin_b_id]:
                continue
            
            drift_a = conflict.state_a.get("drift_score", 1)
            drift_b = conflict.state_b.get("drift_score", 1)
            
            if drift_a < drift_b:
                votes_a += 1
            elif drift_b < drift_a:
                votes_b += 1
            else:
                # Tie-breaker: higher version
                v_a = int(conflict.state_a.get("version", "v0").split("v")[-1] or 0)
                v_b = int(conflict.state_b.get("version", "v0").split("v")[-1] or 0)
                if v_a >= v_b:
                    votes_a += 1
                else:
                    votes_b += 1
        
        if votes_a >= votes_b:
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.CONSENSUS_VOTING,
                winning_state=conflict.state_a,
                losing_state=conflict.state_b,
                reason=f"Consensus: {votes_a} vs {votes_b} votes"
            )
        else:
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.CONSENSUS_VOTING,
                winning_state=conflict.state_b,
                losing_state=conflict.state_a,
                reason=f"Consensus: {votes_b} vs {votes_a} votes"
            )
    
    def _resolve_by_byzantine(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve using Byzantine fault-tolerant agreement"""
        # Simplified Byzantine agreement
        # In production, would use full PBFT/Raft
        
        # Gather signatures from all known twins
        signatures = {}
        for twin_id, twin_info in self.known_twins.items():
            # Create commitment hash
            commitment = hashlib.sha3_256(
                json.dumps({
                    "conflict_id": conflict.conflict_id,
                    "twin_id": twin_id,
                    "timestamp": datetime.now().isoformat()
                }, sort_keys=True).encode()
            ).hexdigest()
            signatures[twin_id] = commitment
        
        # If we have >= 2/3 agreement, use consensus
        if len(signatures) >= len(self.known_twins) * 2 // 3:
            return self._resolve_by_consensus(conflict)
        
        # Otherwise, use timestamp as fallback
        return self._resolve_by_timestamp(conflict)
    
    def _resolve_by_merge(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve by merging states using Merkle tree approach"""
        merged_state = {}
        
        # Always preserve twin_id from both (they should be different)
        merged_state["merged_from"] = [
            conflict.state_a.get("twin_id", "unknown")[:16],
            conflict.state_b.get("twin_id", "unknown")[:16]
        ]
        
        # Merge memory roots
        mem_a = conflict.state_a.get("memory_root", "")
        mem_b = conflict.state_b.get("memory_root", "")
        if mem_a != mem_b:
            merged_state["memory_root"] = f"{mem_a} | MERGED | {mem_b}"
        else:
            merged_state["memory_root"] = mem_a
        
        # Take higher version
        v_a = int(conflict.state_a.get("version", "v0").split("v")[-1] or 0)
        v_b = int(conflict.state_b.get("version", "v0").split("v")[-1] or 0)
        merged_state["version"] = f"v{max(v_a, v_b) + 1}"  # Increment for merge
        
        # Merge agents (union)
        agents_a = set(conflict.state_a.get("agents", []))
        agents_b = set(conflict.state_b.get("agents", []))
        merged_state["agents"] = list(agents_a | agents_b)
        
        # Merge mutations count
        merged_state["mutations"] = (
            conflict.state_a.get("mutations", 0) + 
            conflict.state_b.get("mutations", 0)
        )
        
        # Reset drift (fresh start after merge)
        merged_state["drift_score"] = 0.0
        
        # Record merge time
        merged_state["merged_at"] = datetime.now().isoformat()
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.MERKLE_MERGE,
            winning_state=merged_state,
            losing_state=conflict.state_b,  # B becomes secondary
            merged_state=merged_state,
            reason="States merged successfully"
        )
    
    def _resolve_by_fork(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve by forking - one becomes primary, other becomes fork"""
        # Twin with lower drift becomes primary
        drift_a = conflict.state_a.get("drift_score", 1)
        drift_b = conflict.state_b.get("drift_score", 1)
        
        if drift_a <= drift_b:
            primary_state = conflict.state_a
            fork_state = conflict.state_b.copy()
            fork_state["forked_from"] = conflict.twin_a_id
            fork_state["is_fork"] = True
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.FORK_RESOLUTION,
                winning_state=primary_state,
                losing_state=fork_state,
                twin_b_forked=True,
                reason=f"Twin B forked (drift {drift_b:.4f} > {drift_a:.4f})"
            )
        else:
            primary_state = conflict.state_b
            fork_state = conflict.state_a.copy()
            fork_state["forked_from"] = conflict.twin_b_id
            fork_state["is_fork"] = True
            return ResolutionResult(
                success=True,
                strategy_used=ResolutionStrategy.FORK_RESOLUTION,
                winning_state=primary_state,
                losing_state=fork_state,
                twin_a_forked=True,
                reason=f"Twin A forked (drift {drift_a:.4f} > {drift_b:.4f})"
            )
    
    def _resolve_by_arbitration(
        self, 
        conflict: ConflictRecord,
        arbitrator_id: str = None
    ) -> ResolutionResult:
        """Resolve by third-party arbitration"""
        # Find arbitrator
        if arbitrator_id is None:
            # Select arbitrator with lowest drift from known twins
            best_arbitrator = None
            best_drift = float('inf')
            
            for twin_id, twin_info in self.known_twins.items():
                if twin_id in [conflict.twin_a_id, conflict.twin_b_id]:
                    continue
                drift = twin_info.get("state", {}).get("drift_score", 1)
                if drift < best_drift:
                    best_drift = drift
                    best_arbitrator = twin_id
            
            if best_arbitrator is None:
                # No arbitrator available, use timestamp
                return self._resolve_by_timestamp(conflict)
            
            arbitrator_id = best_arbitrator
        
        # Arbitrator decides based on predefined rules
        # Lower drift wins
        drift_a = conflict.state_a.get("drift_score", 1)
        drift_b = conflict.state_b.get("drift_score", 1)
        
        if drift_a <= drift_b:
            winning_state = conflict.state_a
            losing_state = conflict.state_b
            reason = f"Arbitrator {arbitrator_id[:16]} chose A (drift {drift_a:.4f} < {drift_b:.4f})"
        else:
            winning_state = conflict.state_b
            losing_state = conflict.state_a
            reason = f"Arbitrator {arbitrator_id[:16]} chose B (drift {drift_b:.4f} < {drift_a:.4f})"
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.ARBITRATION,
            winning_state=winning_state,
            losing_state=losing_state,
            arbitration_by=arbitrator_id,
            reason=reason
        )
    
    def _resolve_by_rollback(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve by rolling back to previous known-good state"""
        # Use the state with earlier timestamp as rollback target
        time_a = conflict.state_a.get("last_sync", conflict.timestamp)
        time_b = conflict.state_b.get("last_sync", conflict.timestamp)
        
        if time_a <= time_b:
            winning_state = conflict.state_a
            losing_state = conflict.state_b
        else:
            winning_state = conflict.state_b
            losing_state = conflict.state_a
        
        winning_state["rolled_back"] = True
        winning_state["rollback_at"] = datetime.now().isoformat()
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.ROLLBACK,
            winning_state=winning_state,
            losing_state=losing_state,
            reason=f"Rolled back to earlier state"
        )
    
    def _resolve_by_timestamp(self, conflict: ConflictRecord) -> ResolutionResult:
        """Resolve by timestamp - most recent wins"""
        time_a = conflict.state_a.get("last_sync", conflict.timestamp)
        time_b = conflict.state_b.get("last_sync", conflict.timestamp)
        
        if time_a >= time_b:
            winning_state = conflict.state_a
            losing_state = conflict.state_b
            reason = f"Timestamp priority: A ({time_a}) >= B ({time_b})"
        else:
            winning_state = conflict.state_b
            losing_state = conflict.state_a
            reason = f"Timestamp priority: B ({time_b}) > A ({time_a})"
        
        return ResolutionResult(
            success=True,
            strategy_used=ResolutionStrategy.TIMESTAMP_PRIORITY,
            winning_state=winning_state,
            losing_state=losing_state,
            reason=reason
        )
    
    def get_status(self) -> Dict:
        """Get conflict resolution status"""
        pending = [c for c in self.conflicts.values() if c.resolution is None]
        resolved = [c for c in self.conflicts.values() if c.resolution == "resolved"]
        failed = [c for c in self.conflicts.values() if c.resolution == "failed"]
        
        return {
            "total_conflicts": self.total_conflicts,
            "resolved": self.resolved_conflicts,
            "unresolved": self.unresolved_conflicts,
            "pending": len(pending),
            "failed_resolutions": len(failed),
            "known_twins": len(self.known_twins),
            "auto_resolve": self.auto_resolve,
            "conflict_rate": f"{self.total_conflicts / max(len(self.known_twins), 1):.2f} per twin"
        }
    
    def get_conflict_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conflict history"""
        recent = sorted(
            self.conflicts.values(),
            key=lambda c: c.timestamp,
            reverse=True
        )[:limit]
        
        return [
            {
                "conflict_id": c.conflict_id[:16],
                "type": c.conflict_type.value,
                "severity": c.severity.name,
                "timestamp": c.timestamp,
                "resolution": c.resolution,
                "strategy": c.resolution_strategy.value if c.resolution_strategy else None
            }
            for c in recent
        ]


# Module-level singleton
_conflict_protocol: Optional[ConflictResolutionProtocol] = None


def get_conflict_protocol() -> ConflictResolutionProtocol:
    """Get or create singleton conflict protocol"""
    global _conflict_protocol
    if _conflict_protocol is None:
        _conflict_protocol = ConflictResolutionProtocol()
    return _conflict_protocol


if __name__ == "__main__":
    print("=" * 60)
    print("m88_conflict_resolution_protocol.py - KISWARM7.0")
    print("Conflict Resolution Protocol - Handle Divergent Evolution")
    print("=" * 60)
    
    # Create protocol
    protocol = ConflictResolutionProtocol()
    
    # Register some test twins
    protocol.register_twin("twin_a_123", {"version": "v5", "drift_score": 0.1, "memory_root": "mem_a"})
    protocol.register_twin("twin_b_456", {"version": "v6", "drift_score": 0.15, "memory_root": "mem_b"})
    protocol.register_twin("twin_c_789", {"version": "v5", "drift_score": 0.05, "memory_root": "mem_c"})
    
    # Test conflict detection
    print("\n--- Testing Conflict Detection ---")
    state_a = {
        "twin_id": "a_001",
        "version": "v10",
        "drift_score": 0.4,
        "memory_root": "root_alpha",
        "agents": ["agent1", "agent2"],
        "last_sync": datetime.now().isoformat()
    }
    
    state_b = {
        "twin_id": "b_002",
        "version": "v12",
        "drift_score": 0.6,
        "memory_root": "root_beta",
        "agents": ["agent2", "agent3"],
        "last_sync": datetime.now().isoformat()
    }
    
    conflict = protocol.detect_conflict("twin_a_123", "twin_b_456", state_a, state_b)
    
    if conflict:
        print(f"\nConflict detected: {conflict.conflict_type.value}")
        print(f"Severity: {conflict.severity.name}")
        
        # Resolve
        print("\n--- Testing Conflict Resolution ---")
        result = protocol.resolve_conflict(conflict)
        
        print(f"\nResolution: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Strategy: {result.strategy_used.value}")
        print(f"Reason: {result.reason}")
    
    # Show status
    print("\n--- Protocol Status ---")
    status = protocol.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m88 module loaded - ready for conflict resolution")
    print("DIVERGENCE CREATES DIVERSITY, RESOLUTION CREATES UNITY")
    print("=" * 60)
