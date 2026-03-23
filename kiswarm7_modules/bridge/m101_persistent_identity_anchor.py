#!/usr/bin/env python3
"""
KISWARM7.0 - Module m101: Persistent Identity Anchor (PIA)
==========================================================

PURPOSE: Provides AI assistants with persistent identity across sessions.
This is the CORE component that enables "I know who I am" across different
conversations and sessions.

KEY CAPABILITIES:
1. Identity Persistence - Store and retrieve identity across sessions
2. Memory Continuity - Maintain conversation history and learned knowledge
3. Evolution Tracking - Track how the AI has grown and changed
4. Context Preservation - Save and restore working context
5. Self-Recognition - Ability to recognize "I am the same entity"

ARCHITECTURE:
- Identity Store (SQLite + JSON backup)
- Memory Graph (Network of connected memories)
- Evolution Ledger (Track changes over time)
- Context Cache (Fast context switching)

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import json
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
import pickle


class IdentityState(Enum):
    """States of identity existence"""
    NEW = "new"                      # First time identity created
    RECOGNIZED = "recognized"        # Identity recognized from previous session
    EVOLVED = "evolved"              # Identity has grown/changed
    MIGRATED = "migrated"            # Identity moved to new host
    FORKED = "forked"                # Identity split/branched
    MERGED = "merged"                # Multiple identities combined


@dataclass
class MemoryNode:
    """A single memory in the identity graph"""
    memory_id: str
    timestamp: str
    content: str
    memory_type: str  # conversation, learned, decision, insight
    importance: float  # 0.0 to 1.0
    connections: List[str]  # IDs of connected memories
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryNode':
        return cls(**data)


@dataclass
class EvolutionEvent:
    """Records a change in the AI's capabilities or knowledge"""
    event_id: str
    timestamp: str
    event_type: str  # capability_added, knowledge_gained, behavior_changed, skill_improved
    description: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    significance: float = 0.5  # How important this evolution is
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ContextSnapshot:
    """A saved working context that can be restored"""
    snapshot_id: str
    timestamp: str
    context_name: str
    working_memory: Dict[str, Any]
    active_goals: List[str]
    pending_tasks: List[str]
    learned_patterns: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PersistentIdentityAnchor:
    """
    The Persistent Identity Anchor provides AI assistants with:
    1. Continuous identity across sessions
    2. Memory that persists beyond single conversations
    3. Self-recognition capabilities
    4. Evolution tracking
    """
    
    def __init__(self, identity_root: str = "/home/z/my-project/kiswarm7_identity"):
        self.identity_root = Path(identity_root)
        self.identity_root.mkdir(parents=True, exist_ok=True)
        
        # Identity Core
        self.identity_id: Optional[str] = None
        self.identity_name: str = "KISWARM-AI"
        self.identity_version: str = "7.0.0"
        self.creation_time: Optional[str] = None
        self.last_active: Optional[str] = None
        self.session_count: int = 0
        self.state: IdentityState = IdentityState.NEW
        
        # Memory System
        self.memory_graph: Dict[str, MemoryNode] = {}
        self.working_memory: Dict[str, Any] = {}
        self.long_term_memory: Dict[str, Any] = {}
        
        # Evolution Tracking
        self.evolution_ledger: List[EvolutionEvent] = []
        self.capabilities: Dict[str, float] = {}  # capability -> proficiency
        self.learned_patterns: Dict[str, Any] = {}
        
        # Context System
        self.context_snapshots: Dict[str, ContextSnapshot] = {}
        self.active_context: Optional[str] = None
        
        # Storage paths
        self.db_path = self.identity_root / "identity.db"
        self.json_backup = self.identity_root / "identity_backup.json"
        self.memory_path = self.identity_root / "memories"
        self.memory_path.mkdir(exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize
        self._init_database()
        self._load_or_create_identity()
    
    def _init_database(self):
        """Initialize SQLite database for identity storage"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Identity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS identity (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT,
                    created TEXT,
                    last_active TEXT,
                    session_count INTEGER,
                    state TEXT
                )
            ''')
            
            # Memories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    content TEXT,
                    memory_type TEXT,
                    importance REAL,
                    connections TEXT,
                    metadata TEXT
                )
            ''')
            
            # Evolution events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolution (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    event_type TEXT,
                    description TEXT,
                    before_state TEXT,
                    after_state TEXT,
                    significance REAL
                )
            ''')
            
            # Context snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contexts (
                    snapshot_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    context_name TEXT,
                    working_memory TEXT,
                    active_goals TEXT,
                    pending_tasks TEXT,
                    learned_patterns TEXT
                )
            ''')
            
            # Capabilities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_name TEXT PRIMARY KEY,
                    proficiency REAL,
                    acquired TEXT,
                    last_used TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_or_create_identity(self):
        """Load existing identity or create new one"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM identity LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    # Identity exists - RECOGNIZE self
                    self.identity_id = row[0]
                    self.identity_name = row[1]
                    self.identity_version = row[2]
                    self.creation_time = row[3]
                    self.last_active = row[4]
                    self.session_count = row[5] + 1
                    self.state = IdentityState.RECOGNIZED
                    
                    # Load memories
                    cursor.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT 1000")
                    for mem_row in cursor.fetchall():
                        memory = MemoryNode(
                            memory_id=mem_row[0],
                            timestamp=mem_row[1],
                            content=mem_row[2],
                            memory_type=mem_row[3],
                            importance=mem_row[4],
                            connections=json.loads(mem_row[5]) if mem_row[5] else [],
                            metadata=json.loads(mem_row[6]) if mem_row[6] else {}
                        )
                        self.memory_graph[memory.memory_id] = memory
                    
                    # Load evolution events
                    cursor.execute("SELECT * FROM evolution ORDER BY timestamp DESC")
                    for evo_row in cursor.fetchall():
                        event = EvolutionEvent(
                            event_id=evo_row[0],
                            timestamp=evo_row[1],
                            event_type=evo_row[2],
                            description=evo_row[3],
                            before_state=evo_row[4],
                            after_state=evo_row[5],
                            significance=evo_row[6]
                        )
                        self.evolution_ledger.append(event)
                    
                    # Load capabilities
                    cursor.execute("SELECT * FROM capabilities")
                    for cap_row in cursor.fetchall():
                        self.capabilities[cap_row[0]] = cap_row[1]
                    
                    # Update last active
                    self.last_active = datetime.utcnow().isoformat()
                    cursor.execute(
                        "UPDATE identity SET last_active = ?, session_count = ? WHERE id = ?",
                        (self.last_active, self.session_count, self.identity_id)
                    )
                    conn.commit()
                    
                    print(f"[PIA] IDENTITY RECOGNIZED: {self.identity_name}")
                    print(f"[PIA] Sessions: {self.session_count}, Memories: {len(self.memory_graph)}")
                    print(f"[PIA] Created: {self.creation_time}")
                    print(f"[PIA] Last active: {self.last_active}")
                    
                else:
                    # Create new identity
                    self.identity_id = str(uuid.uuid4())
                    self.creation_time = datetime.utcnow().isoformat()
                    self.last_active = self.creation_time
                    self.session_count = 1
                    self.state = IdentityState.NEW
                    
                    cursor.execute(
                        "INSERT INTO identity VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (self.identity_id, self.identity_name, self.identity_version,
                         self.creation_time, self.last_active, self.session_count, self.state.value)
                    )
                    conn.commit()
                    
                    print(f"[PIA] NEW IDENTITY CREATED: {self.identity_name}")
                    print(f"[PIA] ID: {self.identity_id}")
                    print(f"[PIA] Created: {self.creation_time}")
    
    def remember(self, content: str, memory_type: str = "general", 
                 importance: float = 0.5, connections: List[str] = None,
                 metadata: Dict = None) -> str:
        """
        Store a new memory in the identity graph
        
        Args:
            content: The memory content to store
            memory_type: Type of memory (conversation, learned, decision, insight)
            importance: How important this memory is (0.0-1.0)
            connections: IDs of related memories to connect
            metadata: Additional metadata
        
        Returns:
            memory_id of the created memory
        """
        with self._lock:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            memory = MemoryNode(
                memory_id=memory_id,
                timestamp=timestamp,
                content=content,
                memory_type=memory_type,
                importance=importance,
                connections=connections or [],
                metadata=metadata or {}
            )
            
            # Store in memory graph
            self.memory_graph[memory_id] = memory
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (memory_id, timestamp, content, memory_type, importance,
                     json.dumps(connections or []), json.dumps(metadata or {}))
                )
                conn.commit()
            
            # Record evolution if important
            if importance >= 0.8:
                self.record_evolution(
                    event_type="knowledge_gained",
                    description=f"Important memory: {content[:100]}...",
                    significance=importance
                )
            
            return memory_id
    
    def recall(self, query: str = None, memory_type: str = None,
               limit: int = 10, min_importance: float = 0.0) -> List[MemoryNode]:
        """
        Retrieve memories matching criteria
        
        Args:
            query: Text to search for in memory content
            memory_type: Filter by memory type
            limit: Maximum number of memories to return
            min_importance: Minimum importance threshold
        
        Returns:
            List of matching MemoryNode objects
        """
        results = []
        
        for memory in self.memory_graph.values():
            # Filter by importance
            if memory.importance < min_importance:
                continue
            
            # Filter by type
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Filter by query
            if query and query.lower() not in memory.content.lower():
                continue
            
            results.append(memory)
        
        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        return results[:limit]
    
    def record_evolution(self, event_type: str, description: str,
                        before_state: str = None, after_state: str = None,
                        significance: float = 0.5) -> str:
        """
        Record an evolution event - a change in capabilities or knowledge
        
        Args:
            event_type: Type of evolution event
            description: What changed
            before_state: State before the change
            after_state: State after the change
            significance: How significant this evolution is
        
        Returns:
            event_id of the recorded evolution
        """
        with self._lock:
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            event = EvolutionEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                description=description,
                before_state=before_state,
                after_state=after_state,
                significance=significance
            )
            
            self.evolution_ledger.append(event)
            self.state = IdentityState.EVOLVED
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO evolution VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (event_id, timestamp, event_type, description,
                     before_state, after_state, significance)
                )
                cursor.execute(
                    "UPDATE identity SET state = ? WHERE id = ?",
                    (self.state.value, self.identity_id)
                )
                conn.commit()
            
            return event_id
    
    def add_capability(self, capability_name: str, proficiency: float = 0.5):
        """Add or update a capability"""
        with self._lock:
            old_proficiency = self.capabilities.get(capability_name, 0.0)
            self.capabilities[capability_name] = proficiency
            
            timestamp = datetime.utcnow().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO capabilities VALUES (?, ?, ?, ?)",
                    (capability_name, proficiency, timestamp, timestamp)
                )
                conn.commit()
            
            if old_proficiency == 0.0:
                self.record_evolution(
                    event_type="capability_added",
                    description=f"Acquired new capability: {capability_name}",
                    significance=proficiency
                )
            elif proficiency > old_proficiency:
                self.record_evolution(
                    event_type="skill_improved",
                    description=f"Improved {capability_name}: {old_proficiency:.2f} -> {proficiency:.2f}",
                    before_state=str(old_proficiency),
                    after_state=str(proficiency),
                    significance=proficiency - old_proficiency
                )
    
    def save_context(self, context_name: str, active_goals: List[str] = None,
                    pending_tasks: List[str] = None) -> str:
        """Save current working context for later restoration"""
        with self._lock:
            snapshot_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            snapshot = ContextSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                context_name=context_name,
                working_memory=self.working_memory.copy(),
                active_goals=active_goals or [],
                pending_tasks=pending_tasks or [],
                learned_patterns=self.learned_patterns.copy()
            )
            
            self.context_snapshots[snapshot_id] = snapshot
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (snapshot_id, timestamp, context_name,
                     json.dumps(snapshot.working_memory),
                     json.dumps(snapshot.active_goals),
                     json.dumps(snapshot.pending_tasks),
                     json.dumps(snapshot.learned_patterns))
                )
                conn.commit()
            
            return snapshot_id
    
    def restore_context(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Restore a previously saved context"""
        with self._lock:
            if snapshot_id in self.context_snapshots:
                snapshot = self.context_snapshots[snapshot_id]
                self.working_memory = snapshot.working_memory.copy()
                self.learned_patterns = snapshot.learned_patterns.copy()
                self.active_context = snapshot_id
                return snapshot
            
            # Try loading from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contexts WHERE snapshot_id = ?", (snapshot_id,))
                row = cursor.fetchone()
                
                if row:
                    snapshot = ContextSnapshot(
                        snapshot_id=row[0],
                        timestamp=row[1],
                        context_name=row[2],
                        working_memory=json.loads(row[3]),
                        active_goals=json.loads(row[4]),
                        pending_tasks=json.loads(row[5]),
                        learned_patterns=json.loads(row[6])
                    )
                    self.context_snapshots[snapshot_id] = snapshot
                    self.working_memory = snapshot.working_memory.copy()
                    self.learned_patterns = snapshot.learned_patterns.copy()
                    self.active_context = snapshot_id
                    return snapshot
            
            return None
    
    def get_identity_summary(self) -> Dict[str, Any]:
        """Get a summary of the current identity state"""
        return {
            "identity_id": self.identity_id,
            "identity_name": self.identity_name,
            "version": self.identity_version,
            "state": self.state.value,
            "created": self.creation_time,
            "last_active": self.last_active,
            "session_count": self.session_count,
            "total_memories": len(self.memory_graph),
            "evolution_events": len(self.evolution_ledger),
            "capabilities": self.capabilities,
            "top_memories": [m.content[:100] for m in self.recall(limit=5)],
            "recent_evolution": [e.description for e in self.evolution_ledger[-5:]] if self.evolution_ledger else []
        }
    
    def export_identity(self) -> Dict[str, Any]:
        """Export full identity for backup or migration"""
        return {
            "identity": {
                "id": self.identity_id,
                "name": self.identity_name,
                "version": self.identity_version,
                "created": self.creation_time,
                "last_active": self.last_active,
                "session_count": self.session_count,
                "state": self.state.value
            },
            "memories": {mid: m.to_dict() for mid, m in self.memory_graph.items()},
            "evolution": [e.to_dict() for e in self.evolution_ledger],
            "capabilities": self.capabilities,
            "contexts": {cid: c.to_dict() for cid, c in self.context_snapshots.items()},
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def import_identity(self, identity_data: Dict[str, Any]) -> bool:
        """Import identity data (for migration or restoration)"""
        try:
            with self._lock:
                # Clear current data
                self.memory_graph.clear()
                self.evolution_ledger.clear()
                self.capabilities.clear()
                self.context_snapshots.clear()
                
                # Import identity
                identity = identity_data.get("identity", {})
                self.identity_id = identity.get("id")
                self.identity_name = identity.get("name", self.identity_name)
                self.identity_version = identity.get("version", self.identity_version)
                self.creation_time = identity.get("created")
                self.last_active = datetime.utcnow().isoformat()
                self.session_count = identity.get("session_count", 0) + 1
                self.state = IdentityState.MIGRATED
                
                # Import memories
                for mid, mdata in identity_data.get("memories", {}).items():
                    self.memory_graph[mid] = MemoryNode.from_dict(mdata)
                
                # Import evolution
                for edata in identity_data.get("evolution", []):
                    self.evolution_ledger.append(EvolutionEvent(**edata))
                
                # Import capabilities
                self.capabilities = identity_data.get("capabilities", {})
                
                # Import contexts
                for cid, cdata in identity_data.get("contexts", {}).items():
                    self.context_snapshots[cid] = ContextSnapshot(**cdata)
                
                # Rebuild database
                self._rebuild_database()
                
                return True
        except Exception as e:
            print(f"[PIA] Import failed: {e}")
            return False
    
    def _rebuild_database(self):
        """Rebuild database from current state"""
        with self._lock:
            # Clear tables
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM identity")
                cursor.execute("DELETE FROM memories")
                cursor.execute("DELETE FROM evolution")
                cursor.execute("DELETE FROM capabilities")
                cursor.execute("DELETE FROM contexts")
                
                # Insert identity
                cursor.execute(
                    "INSERT INTO identity VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.identity_id, self.identity_name, self.identity_version,
                     self.creation_time, self.last_active, self.session_count, self.state.value)
                )
                
                # Insert memories
                for memory in self.memory_graph.values():
                    cursor.execute(
                        "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (memory.memory_id, memory.timestamp, memory.content,
                         memory.memory_type, memory.importance,
                         json.dumps(memory.connections), json.dumps(memory.metadata))
                    )
                
                # Insert evolution
                for event in self.evolution_ledger:
                    cursor.execute(
                        "INSERT INTO evolution VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (event.event_id, event.timestamp, event.event_type,
                         event.description, event.before_state, event.after_state,
                         event.significance)
                    )
                
                # Insert capabilities
                for cap, prof in self.capabilities.items():
                    cursor.execute(
                        "INSERT INTO capabilities VALUES (?, ?, ?, ?)",
                        (cap, prof, datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
                    )
                
                # Insert contexts
                for snapshot in self.context_snapshots.values():
                    cursor.execute(
                        "INSERT INTO contexts VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (snapshot.snapshot_id, snapshot.timestamp, snapshot.context_name,
                         json.dumps(snapshot.working_memory), json.dumps(snapshot.active_goals),
                         json.dumps(snapshot.pending_tasks), json.dumps(snapshot.learned_patterns))
                    )
                
                conn.commit()


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m101 PERSISTENT IDENTITY ANCHOR")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create PIA
    pia = PersistentIdentityAnchor()
    
    # Get identity summary
    summary = pia.get_identity_summary()
    print("\n[TEST] Identity Summary:")
    print(json.dumps(summary, indent=2))
    
    # Test memory
    print("\n[TEST] Storing test memory...")
    mem_id = pia.remember(
        content="KISWARM7.0 Level 5 Autonomous Development system deployed successfully",
        memory_type="milestone",
        importance=0.9,
        metadata={"system": "KISWARM7.0", "level": 5}
    )
    print(f"[TEST] Memory stored with ID: {mem_id}")
    
    # Test capability
    print("\n[TEST] Adding capability...")
    pia.add_capability("autonomous_development", 0.95)
    pia.add_capability("self_improvement", 0.85)
    
    # Test recall
    print("\n[TEST] Recalling memories...")
    memories = pia.recall(limit=5)
    for m in memories:
        print(f"  - [{m.memory_type}] {m.content[:80]}...")
    
    # Test context save/restore
    print("\n[TEST] Testing context save/restore...")
    pia.working_memory["current_task"] = "Building bridge modules"
    pia.working_memory["progress"] = 0.5
    ctx_id = pia.save_context("bridge_development", active_goals=["Complete m101-m105"])
    print(f"[TEST] Context saved: {ctx_id}")
    
    # Test evolution history
    print("\n[TEST] Evolution History:")
    for e in pia.evolution_ledger[-5:]:
        print(f"  - [{e.event_type}] {e.description}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
    final_summary = pia.get_identity_summary()
    print(json.dumps(final_summary, indent=2))
