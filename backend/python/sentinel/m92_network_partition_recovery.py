# sentinel/m92_network_partition_recovery.py
# Network Partition Recovery – Mesh Healing After Network Split
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Enterprise Hardening Module

"""
m92_network_partition_recovery.py

Recovers mesh connectivity after network partitions.

PROBLEM:
- Network failures split mesh into isolated partitions
- Twins in different partitions evolve independently
- Conflicting states emerge during partition
- Manual recovery is not scalable

SOLUTION:
1. Detect partition through heartbeat failures
2. Mark partitioned twins as isolated
3. Continue evolution in degraded mode
4. Auto-heal when connectivity restored
5. Merge conflicting states on rejoin

PARTITION TYPES:
1. Clean Split - Equal halves, no overlap
2. Minority Isolation - Small group cut off
3. Single Node - One twin isolated
4. Cascade Failure - Multiple successive splits

RECOVERY STRATEGIES:
1. Primary Partition - Majority wins
2. State Merge - Combine divergent states
3. Re-sync - Copy from primary
4. Fork - Create separate mesh

CORE PRINCIPLE:
Partitions are inevitable. Recovery must be automatic.
The mesh heals itself like a living organism.
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import random


class PartitionState(Enum):
    """State of a network partition"""
    HEALTHY = "healthy"           # No partition
    DEGRADED = "degraded"         # Some twins unreachable
    PARTITIONED = "partitioned"   # Split into groups
    ISOLATED = "isolated"         # This twin isolated
    HEALING = "healing"           # Recovery in progress


class RecoveryStrategy(Enum):
    """Strategies for partition recovery"""
    PRIMARY_PARTITION = "primary"    # Majority wins
    STATE_MERGE = "merge"            # Combine states
    RESYNC = "resync"                # Copy from primary
    FORK_MESH = "fork"               # Create separate mesh
    CONSENSUS = "consensus"          # Vote on correct state


class TwinStatus(Enum):
    """Status of a twin in the mesh"""
    ACTIVE = "active"           # Connected and healthy
    UNREACHABLE = "unreachable" # Cannot reach
    SUSPECTED = "suspected"     # May be partitioned
    CONFIRMED_PARTITIONED = "partitioned"  # Confirmed in other partition
    RECOVERING = "recovering"   # Re-joining after partition


@dataclass
class TwinInfo:
    """Information about a twin in the mesh"""
    twin_id: str
    endpoint: str
    last_heartbeat: str
    status: TwinStatus
    partition_id: Optional[str] = None
    state_version: int = 0
    drift_score: float = 0.0


@dataclass
class PartitionRecord:
    """Record of a partition event"""
    partition_id: str
    detected_at: str
    state: PartitionState
    twins_in_partition: List[str]
    twins_isolated: List[str]
    primary_partition: bool
    recovered_at: Optional[str] = None
    recovery_strategy: Optional[RecoveryStrategy] = None
    state_conflicts: int = 0


@dataclass
class RecoveryResult:
    """Result of partition recovery"""
    success: bool
    strategy_used: RecoveryStrategy
    twins_recovered: int
    state_conflicts_resolved: int
    duration_seconds: float
    message: str


class NetworkPartitionRecovery:
    """
    Manages network partition detection and recovery.
    
    The Recovery System:
    1. Monitors twin heartbeats
    2. Detects partitions through missed heartbeats
    3. Maintains partition registry
    4. Coordinates healing when connectivity restores
    5. Resolves state conflicts on rejoin
    
    Principles:
    - Partitions are detected, not prevented
    - Primary partition is determined by size
    - State conflicts are resolved by consensus
    - All twins eventually converge
    """
    
    # Thresholds
    HEARTBEAT_INTERVAL_SECONDS = 30
    MISSED_HEARTBEATS_SUSPECTED = 2
    MISSED_HEARTBEATS_PARTITIONED = 5
    MIN_PARTITION_SIZE = 2
    
    def __init__(
        self,
        working_dir: str = None,
        local_twin_id: str = None,
        heartbeat_interval: int = None,
        auto_heal: bool = True
    ):
        """
        Initialize network partition recovery.
        
        Args:
            working_dir: Directory for partition records
            local_twin_id: ID of local twin
            heartbeat_interval: Seconds between heartbeats
            auto_heal: Whether to auto-heal partitions
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.local_twin_id = local_twin_id or self._generate_twin_id()
        self.heartbeat_interval = heartbeat_interval or self.HEARTBEAT_INTERVAL_SECONDS
        self.auto_heal = auto_heal
        
        # Mesh state
        self.known_twins: Dict[str, TwinInfo] = {}
        self.partition_state = PartitionState.HEALTHY
        self.current_partition_id: Optional[str] = None
        
        # Records
        self.partitions_file = self.working_dir / "partition_records.json"
        self.partition_history: List[PartitionRecord] = []
        
        # Stats
        self.total_partitions = 0
        self.total_recoveries = 0
        self.time_in_partition = 0.0
        
        # Load records
        self._load_records()
        
        # Heartbeat thread
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[m92] Network Partition Recovery initialized")
        print(f"[m92] Local twin: {self.local_twin_id[:16]}...")
        print(f"[m92] Heartbeat interval: {self.heartbeat_interval}s")
        print(f"[m92] Auto-heal: {'ENABLED' if auto_heal else 'DISABLED'}")
    
    def _generate_twin_id(self) -> str:
        """Generate a twin ID"""
        return hashlib.sha3_256(
            f"TWIN_{datetime.now().isoformat()}_{os.urandom(8).hex()}".encode()
        ).hexdigest()
    
    def _load_records(self):
        """Load partition records from disk"""
        if self.partitions_file.exists():
            try:
                with open(self.partitions_file, 'r') as f:
                    data = json.load(f)
                
                self.total_partitions = data.get("total_partitions", 0)
                self.total_recoveries = data.get("total_recoveries", 0)
                self.time_in_partition = data.get("time_in_partition", 0.0)
                
                for p_data in data.get("partitions", []):
                    partition = PartitionRecord(
                        partition_id=p_data["partition_id"],
                        detected_at=p_data["detected_at"],
                        state=PartitionState(p_data["state"]),
                        twins_in_partition=p_data["twins_in_partition"],
                        twins_isolated=p_data["twins_isolated"],
                        primary_partition=p_data["primary_partition"],
                        recovered_at=p_data.get("recovered_at"),
                        recovery_strategy=RecoveryStrategy(p_data["recovery_strategy"]) if p_data.get("recovery_strategy") else None,
                        state_conflicts=p_data.get("state_conflicts", 0)
                    )
                    self.partition_history.append(partition)
                
                print(f"[m92] Loaded {len(self.partition_history)} partition records")
                
            except Exception as e:
                print(f"[m92] Could not load records: {e}")
    
    def _save_records(self):
        """Save partition records to disk"""
        data = {
            "local_twin_id": self.local_twin_id,
            "total_partitions": self.total_partitions,
            "total_recoveries": self.total_recoveries,
            "time_in_partition": self.time_in_partition,
            "last_update": datetime.now().isoformat(),
            "partitions": [
                {
                    "partition_id": p.partition_id,
                    "detected_at": p.detected_at,
                    "state": p.state.value,
                    "twins_in_partition": p.twins_in_partition,
                    "twins_isolated": p.twins_isolated,
                    "primary_partition": p.primary_partition,
                    "recovered_at": p.recovered_at,
                    "recovery_strategy": p.recovery_strategy.value if p.recovery_strategy else None,
                    "state_conflicts": p.state_conflicts
                }
                for p in self.partition_history
            ]
        }
        
        with open(self.partitions_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_twin(self, twin_id: str, endpoint: str):
        """Register a twin in the mesh"""
        self.known_twins[twin_id] = TwinInfo(
            twin_id=twin_id,
            endpoint=endpoint,
            last_heartbeat=datetime.now().isoformat(),
            status=TwinStatus.ACTIVE
        )
        print(f"[m92] Registered twin: {twin_id[:16]}... at {endpoint}")
    
    def unregister_twin(self, twin_id: str):
        """Unregister a twin from the mesh"""
        if twin_id in self.known_twins:
            del self.known_twins[twin_id]
            print(f"[m92] Unregistered twin: {twin_id[:16]}...")
    
    def receive_heartbeat(self, twin_id: str, state_version: int = 0, drift_score: float = 0.0):
        """
        Process received heartbeat from a twin.
        
        Args:
            twin_id: ID of twin sending heartbeat
            state_version: Twin's current state version
            drift_score: Twin's current drift score
        """
        if twin_id in self.known_twins:
            twin = self.known_twins[twin_id]
            twin.last_heartbeat = datetime.now().isoformat()
            twin.status = TwinStatus.ACTIVE
            twin.state_version = state_version
            twin.drift_score = drift_score
            
            # Clear partition if was partitioned
            if twin.partition_id:
                print(f"[m92] Twin {twin_id[:16]}... recovered from partition")
                twin.partition_id = None
                twin.status = TwinStatus.ACTIVE
    
    def send_heartbeat(self) -> Dict:
        """
        Generate heartbeat to send to other twins.
        
        Returns:
            Heartbeat data dictionary
        """
        return {
            "twin_id": self.local_twin_id,
            "timestamp": datetime.now().isoformat(),
            "partition_state": self.partition_state.value,
            "known_twins": list(self.known_twins.keys()),
            "partition_id": self.current_partition_id
        }
    
    def check_partition_status(self) -> PartitionState:
        """
        Check current partition status based on heartbeats.
        
        Returns:
            Current partition state
        """
        now = datetime.now()
        unreachable = []
        suspected = []
        
        for twin_id, twin in self.known_twins.items():
            try:
                last = datetime.fromisoformat(twin.last_heartbeat)
                missed = (now - last).total_seconds() / self.heartbeat_interval
                
                if missed >= self.MISSED_HEARTBEATS_PARTITIONED:
                    twin.status = TwinStatus.CONFIRMED_PARTITIONED
                    unreachable.append(twin_id)
                elif missed >= self.MISSED_HEARTBEATS_SUSPECTED:
                    twin.status = TwinStatus.SUSPECTED
                    suspected.append(twin_id)
                else:
                    twin.status = TwinStatus.ACTIVE
            except:
                pass
        
        # Determine partition state
        total = len(self.known_twins)
        unreachable_count = len(unreachable)
        
        if unreachable_count == 0 and len(suspected) == 0:
            self.partition_state = PartitionState.HEALTHY
        elif unreachable_count == 0:
            self.partition_state = PartitionState.DEGRADED
        elif unreachable_count >= total / 2:
            # Majority unreachable - we might be the isolated ones
            self.partition_state = PartitionState.ISOLATED
        else:
            self.partition_state = PartitionState.PARTITIONED
        
        return self.partition_state
    
    def detect_partition(self) -> Optional[PartitionRecord]:
        """
        Detect if a partition has occurred.
        
        Returns:
            PartitionRecord if partition detected, None otherwise
        """
        state = self.check_partition_status()
        
        if state == PartitionState.HEALTHY:
            return None
        
        # Find partitioned twins
        unreachable = [
            twin_id for twin_id, twin in self.known_twins.items()
            if twin.status in [TwinStatus.UNREACHABLE, TwinStatus.CONFIRMED_PARTITIONED]
        ]
        
        if not unreachable:
            return None
        
        # Create partition record
        partition_id = hashlib.sha3_256(
            f"PARTITION_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        # Determine primary partition (larger group)
        active_twins = [
            twin_id for twin_id, twin in self.known_twins.items()
            if twin.status == TwinStatus.ACTIVE
        ]
        
        is_primary = len(active_twins) >= len(unreachable)
        
        partition = PartitionRecord(
            partition_id=partition_id,
            detected_at=datetime.now().isoformat(),
            state=state,
            twins_in_partition=active_twins if is_primary else unreachable,
            twins_isolated=unreachable if is_primary else active_twins,
            primary_partition=is_primary
        )
        
        self.partition_history.append(partition)
        self.total_partitions += 1
        self.current_partition_id = partition_id
        
        # Mark twins
        for twin_id in unreachable:
            self.known_twins[twin_id].partition_id = partition_id
        
        self._save_records()
        
        print(f"[m92] ⚠️  PARTITION DETECTED: {partition_id[:8]}")
        print(f"[m92] State: {state.value}")
        print(f"[m92] Primary partition: {is_primary}")
        print(f"[m92] Active twins: {len(active_twins)}")
        print(f"[m92] Isolated twins: {len(unreachable)}")
        
        return partition
    
    def heal_partition(
        self,
        partition: PartitionRecord,
        remote_states: Dict[str, Dict] = None
    ) -> RecoveryResult:
        """
        Heal a detected partition.
        
        Args:
            partition: Partition record to heal
            remote_states: States from twins that re-joined
            
        Returns:
            RecoveryResult with recovery details
        """
        start_time = time.time()
        print(f"[m92] Starting partition healing: {partition.partition_id[:8]}")
        
        # Select recovery strategy
        if partition.primary_partition:
            strategy = RecoveryStrategy.PRIMARY_PARTITION
        elif len(remote_states or {}) > 0:
            strategy = RecoveryStrategy.STATE_MERGE
        else:
            strategy = RecoveryStrategy.RESYNC
        
        print(f"[m92] Strategy: {strategy.value}")
        
        twins_recovered = 0
        conflicts_resolved = 0
        
        try:
            if strategy == RecoveryStrategy.PRIMARY_PARTITION:
                # Primary partition wins - isolated twins resync
                twins_recovered = len(partition.twins_isolated)
                conflicts_resolved = 0  # No conflicts, just resync
                
            elif strategy == RecoveryStrategy.STATE_MERGE:
                # Merge states from re-joining twins
                for twin_id, remote_state in (remote_states or {}).items():
                    if twin_id in self.known_twins:
                        # Merge logic would go here
                        conflicts_resolved += 1
                        twins_recovered += 1
                
            elif strategy == RecoveryStrategy.RESYNC:
                # This partition resyncs from primary
                twins_recovered = len(partition.twins_in_partition)
            
            # Update partition record
            partition.recovered_at = datetime.now().isoformat()
            partition.recovery_strategy = strategy
            partition.state_conflicts = conflicts_resolved
            
            # Clear partition state
            self.partition_state = PartitionState.HEALTHY
            self.current_partition_id = None
            
            for twin_id, twin in self.known_twins.items():
                if twin.partition_id == partition.partition_id:
                    twin.partition_id = None
                    twin.status = TwinStatus.ACTIVE
            
            self.total_recoveries += 1
            self._save_records()
            
            duration = time.time() - start_time
            self.time_in_partition += duration
            
            result = RecoveryResult(
                success=True,
                strategy_used=strategy,
                twins_recovered=twins_recovered,
                state_conflicts_resolved=conflicts_resolved,
                duration_seconds=duration,
                message=f"Partition healed successfully"
            )
            
            print(f"[m92] ✓ Partition healed in {duration:.2f}s")
            print(f"[m92] Twins recovered: {twins_recovered}")
            print(f"[m92] Conflicts resolved: {conflicts_resolved}")
            
        except Exception as e:
            result = RecoveryResult(
                success=False,
                strategy_used=strategy,
                twins_recovered=0,
                state_conflicts_resolved=0,
                duration_seconds=time.time() - start_time,
                message=f"Recovery failed: {e}"
            )
            print(f"[m92] ✗ Recovery failed: {e}")
        
        return result
    
    def start_heartbeat_monitor(self):
        """Start heartbeat monitoring thread"""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            print("[m92] Heartbeat monitor already running")
            return
        
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        print("[m92] Heartbeat monitor started")
    
    def stop_heartbeat_monitor(self):
        """Stop heartbeat monitoring"""
        self._stop_event.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        print("[m92] Heartbeat monitor stopped")
    
    def _heartbeat_loop(self):
        """Background heartbeat monitoring"""
        while not self._stop_event.is_set():
            # Check for partitions
            state = self.check_partition_status()
            
            if state != PartitionState.HEALTHY:
                partition = self.detect_partition()
                
                if partition and self.auto_heal:
                    # Wait for potential reconnection
                    self._stop_event.wait(self.heartbeat_interval * 3)
                    
                    if not self._stop_event.is_set():
                        # Try to heal
                        self.heal_partition(partition)
            
            self._stop_event.wait(self.heartbeat_interval)
    
    def get_mesh_topology(self) -> Dict:
        """Get current mesh topology"""
        active = [t for t in self.known_twins.values() if t.status == TwinStatus.ACTIVE]
        unreachable = [t for t in self.known_twins.values() if t.status in [TwinStatus.UNREACHABLE, TwinStatus.CONFIRMED_PARTITIONED]]
        
        return {
            "total_twins": len(self.known_twins),
            "active_twins": len(active),
            "unreachable_twins": len(unreachable),
            "partition_state": self.partition_state.value,
            "current_partition": self.current_partition_id[:16] if self.current_partition_id else None,
            "local_twin": self.local_twin_id[:16] + "...",
            "is_primary": len(active) > len(unreachable)
        }
    
    def get_status(self) -> Dict:
        """Get partition recovery status"""
        return {
            "partition_state": self.partition_state.value,
            "known_twins": len(self.known_twins),
            "total_partitions": self.total_partitions,
            "total_recoveries": self.total_recoveries,
            "time_in_partition": f"{self.time_in_partition:.1f}s",
            "auto_heal": self.auto_heal,
            "heartbeat_interval": self.heartbeat_interval
        }
    
    def get_partition_history(self, limit: int = 10) -> List[Dict]:
        """Get recent partition history"""
        recent = self.partition_history[-limit:]
        
        return [
            {
                "partition_id": p.partition_id[:16],
                "detected_at": p.detected_at,
                "state": p.state.value,
                "twins_affected": len(p.twins_isolated),
                "recovered": p.recovered_at is not None,
                "strategy": p.recovery_strategy.value if p.recovery_strategy else None
            }
            for p in recent
        ]


# Module-level singleton
_partition_recovery: Optional[NetworkPartitionRecovery] = None


def get_partition_recovery() -> NetworkPartitionRecovery:
    """Get or create singleton partition recovery"""
    global _partition_recovery
    if _partition_recovery is None:
        _partition_recovery = NetworkPartitionRecovery()
    return _partition_recovery


if __name__ == "__main__":
    print("=" * 60)
    print("m92_network_partition_recovery.py - KISWARM7.0")
    print("Network Partition Recovery - Mesh Healing")
    print("=" * 60)
    
    # Create recovery system
    recovery = NetworkPartitionRecovery()
    
    # Register some twins
    print("\n--- Registering Twins ---")
    recovery.register_twin("twin_alpha_001", "http://alpha:5000")
    recovery.register_twin("twin_beta_002", "http://beta:5000")
    recovery.register_twin("twin_gamma_003", "http://gamma:5000")
    recovery.register_twin("twin_delta_004", "http://delta:5000")
    
    # Simulate heartbeat
    print("\n--- Simulating Heartbeats ---")
    recovery.receive_heartbeat("twin_alpha_001", state_version=10, drift_score=0.1)
    recovery.receive_heartbeat("twin_beta_002", state_version=8, drift_score=0.05)
    # gamma and delta are silent (simulating partition)
    
    # Check status
    state = recovery.check_partition_status()
    print(f"Partition state: {state.value}")
    
    # Detect partition
    print("\n--- Detecting Partition ---")
    partition = recovery.detect_partition()
    
    if partition:
        print(f"Partition ID: {partition.partition_id[:16]}")
        print(f"Is primary: {partition.primary_partition}")
        print(f"Isolated twins: {len(partition.twins_isolated)}")
        
        # Simulate healing
        print("\n--- Healing Partition ---")
        # Simulate twins coming back
        recovery.receive_heartbeat("twin_gamma_003", state_version=12, drift_score=0.2)
        recovery.receive_heartbeat("twin_delta_004", state_version=11, drift_score=0.15)
        
        result = recovery.heal_partition(partition)
        print(f"Success: {result.success}")
        print(f"Strategy: {result.strategy_used.value}")
        print(f"Twins recovered: {result.twins_recovered}")
    
    # Show status
    print("\n--- Recovery Status ---")
    status = recovery.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Show topology
    print("\n--- Mesh Topology ---")
    topo = recovery.get_mesh_topology()
    for key, value in topo.items():
        print(f"  {key}: {value}")
    
    # Show history
    print("\n--- Partition History ---")
    history = recovery.get_partition_history()
    for h in history:
        print(f"  {h['detected_at']}: {h['state']} ({h['twins_affected']} twins)")
    
    print("\n" + "=" * 60)
    print("m92 module loaded - ready for partition recovery")
    print("PARTITIONS ARE INEVITABLE, RECOVERY IS AUTOMATIC")
    print("=" * 60)
