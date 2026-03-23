"""
KISWARM MuninnDB Cognitive Memory Adapter
Implements human-like memory with Ebbinghaus decay and Hebbian learning

Named after Odin's raven Muninn ("Memory" in Old Norse)

Features:
- Ebbinghaus Forgetting Curve: R = e^(-t/S)
- Hebbian Learning: Association strengthening
- Bayesian Confidence: Probability-based decisions
- SQLite Persistence: Full CRUD operations
"""

import sqlite3
import json
import math
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory entries"""
    EPISODIC = "episodic"      # Events and experiences
    SEMANTIC = "semantic"      # Facts and concepts
    PROCEDURAL = "procedural"  # Skills and procedures
    WORKING = "working"        # Temporary, task-specific
    EMOTIONAL = "emotional"    # Emotional associations


@dataclass
class MemoryEntry:
    """A single memory entry in MuninnDB"""
    id: Optional[int] = None
    memory_type: str = "semantic"
    content: str = ""
    metadata: Dict = None
    strength: float = 1.0  # Memory strength (0-1)
    stability: float = 0.5  # Resistance to decay (0-1)
    confidence: float = 0.8  # Bayesian confidence (0-1)
    associations: List[int] = None  # IDs of associated memories
    tags: List[str] = None
    created_at: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int = 0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.associations is None:
            self.associations = []
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.last_accessed is None:
            self.last_accessed = self.created_at


class MuninnDBAdapter:
    """
    Cognitive Memory Adapter implementing:
    
    1. Ebbinghaus Forgetting Curve:
       R = e^(-t/S) where:
       - R = Retention (0-1)
       - t = Time since last access
       - S = Stability factor
    
    2. Hebbian Learning:
       - Associations strengthen with co-activation
       - "Neurons that fire together, wire together"
    
    3. Bayesian Confidence:
       - Prior + Evidence = Posterior
       - Tracks belief in memory accuracy
    
    4. SQLite Persistence:
       - Full CRUD operations
       - Efficient querying
    """
    
    def __init__(self, db_path: str = "muninndb.sqlite"):
        """
        Initialize MuninnDB adapter.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_db()
        logger.info(f"[MuninnDB] Initialized at {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _initialize_db(self):
        """Create database schema if not exists"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Main memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL DEFAULT 'semantic',
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                strength REAL DEFAULT 1.0,
                stability REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.8,
                associations TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Association strength table (for Hebbian learning)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS associations (
                memory_id_a INTEGER NOT NULL,
                memory_id_b INTEGER NOT NULL,
                strength REAL DEFAULT 0.1,
                co_activations INTEGER DEFAULT 1,
                last_co_activation TEXT,
                PRIMARY KEY (memory_id_a, memory_id_b),
                FOREIGN KEY (memory_id_a) REFERENCES memories(id),
                FOREIGN KEY (memory_id_b) REFERENCES memories(id)
            )
        ''')
        
        # Index for efficient queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_strength ON memories(strength)
        ''')
        
        conn.commit()
    
    # ==================== CRUD Operations ====================
    
    def create(self, entry: MemoryEntry) -> int:
        """Create a new memory entry"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memories (
                memory_type, content, metadata, strength, stability,
                confidence, associations, tags, created_at, last_accessed, access_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.memory_type,
            entry.content,
            json.dumps(entry.metadata),
            entry.strength,
            entry.stability,
            entry.confidence,
            json.dumps(entry.associations),
            json.dumps(entry.tags),
            entry.created_at,
            entry.last_accessed,
            entry.access_count
        ))
        
        memory_id = cursor.lastrowid
        conn.commit()
        
        logger.debug(f"[MuninnDB] Created memory {memory_id}: {entry.content[:50]}...")
        return memory_id
    
    def read(self, memory_id: int, update_access: bool = True) -> Optional[MemoryEntry]:
        """Read a memory by ID, optionally updating access time"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        if update_access:
            # Update access time and count
            now = datetime.utcnow().isoformat()
            cursor.execute('''
                UPDATE memories 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE id = ?
            ''', (now, memory_id))
            conn.commit()
        
        return self._row_to_entry(row)
    
    def update(self, memory_id: int, **kwargs) -> bool:
        """Update memory fields"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        valid_fields = {
            'memory_type', 'content', 'metadata', 'strength', 
            'stability', 'confidence', 'associations', 'tags'
        }
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in valid_fields:
                if field in ('metadata', 'associations', 'tags'):
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(memory_id)
        
        cursor.execute(
            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
        
        return cursor.rowcount > 0
    
    def delete(self, memory_id: int) -> bool:
        """Delete a memory"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete associations first
        cursor.execute(
            'DELETE FROM associations WHERE memory_id_a = ? OR memory_id_b = ?',
            (memory_id, memory_id)
        )
        
        cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ==================== Ebbinghaus Forgetting Curve ====================
    
    def calculate_retention(self, memory_id: int) -> float:
        """
        Calculate current retention using Ebbinghaus formula.
        
        R = e^(-t/S)
        
        Where:
        - t = time since last access (in days)
        - S = stability factor (higher = slower decay)
        """
        entry = self.read(memory_id, update_access=False)
        if entry is None:
            return 0.0
        
        # Calculate time since last access
        last_accessed = datetime.fromisoformat(entry.last_accessed)
        time_delta = datetime.utcnow() - last_accessed
        t = time_delta.total_seconds() / 86400  # Convert to days
        
        # Apply Ebbinghaus formula
        retention = math.exp(-t / max(entry.stability, 0.01))
        
        return retention
    
    def apply_decay(self, memory_id: int) -> float:
        """
        Apply forgetting curve decay to memory strength.
        Returns new strength value.
        """
        retention = self.calculate_retention(memory_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get current strength
        cursor.execute('SELECT strength FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        if row is None:
            return 0.0
        
        current_strength = row['strength']
        new_strength = current_strength * retention
        
        # Update strength
        cursor.execute(
            'UPDATE memories SET strength = ? WHERE id = ?',
            (new_strength, memory_id)
        )
        conn.commit()
        
        logger.debug(f"[MuninnDB] Decay applied to {memory_id}: "
                    f"{current_strength:.3f} -> {new_strength:.3f}")
        
        return new_strength
    
    def get_decay_report(self) -> Dict:
        """Get a report of memory decay status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, strength, stability FROM memories')
        rows = cursor.fetchall()
        
        report = {
            "total_memories": len(rows),
            "strong_memories": 0,  # strength > 0.7
            "decaying_memories": 0,  # 0.3 < strength <= 0.7
            "weak_memories": 0,  # strength <= 0.3
            "average_retention": 0.0
        }
        
        total_retention = 0.0
        
        for row in rows:
            retention = self.calculate_retention(row['id'])
            total_retention += retention
            
            if retention > 0.7:
                report["strong_memories"] += 1
            elif retention > 0.3:
                report["decaying_memories"] += 1
            else:
                report["weak_memories"] += 1
        
        if rows:
            report["average_retention"] = total_retention / len(rows)
        
        return report
    
    # ==================== Hebbian Learning ====================
    
    def strengthen_association(self, memory_id_a: int, memory_id_b: int):
        """
        Strengthen association between two memories using Hebbian learning.
        
        Δw = η * (pre * post)
        
        Where:
        - η = learning rate
        - pre, post = activation levels
        """
        if memory_id_a == memory_id_b:
            return
        
        # Ensure consistent ordering
        id_a, id_b = sorted([memory_id_a, memory_id_b])
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if association exists
        cursor.execute('''
            SELECT strength, co_activations FROM associations 
            WHERE memory_id_a = ? AND memory_id_b = ?
        ''', (id_a, id_b))
        
        row = cursor.fetchone()
        now = datetime.utcnow().isoformat()
        
        if row:
            # Update existing association
            current_strength = row['strength']
            co_activations = row['co_activations'] + 1
            
            # Hebbian learning rule with decay
            learning_rate = 0.1
            new_strength = current_strength + learning_rate * (1 - current_strength)
            new_strength = min(new_strength, 1.0)  # Cap at 1.0
            
            cursor.execute('''
                UPDATE associations 
                SET strength = ?, co_activations = ?, last_co_activation = ?
                WHERE memory_id_a = ? AND memory_id_b = ?
            ''', (new_strength, co_activations, now, id_a, id_b))
        else:
            # Create new association
            cursor.execute('''
                INSERT INTO associations 
                (memory_id_a, memory_id_b, strength, co_activations, last_co_activation)
                VALUES (?, ?, 0.1, 1, ?)
            ''', (id_a, id_b, now))
        
        conn.commit()
        logger.debug(f"[MuninnDB] Association strengthened: {id_a} <-> {id_b}")
    
    def get_associated_memories(self, memory_id: int, min_strength: float = 0.3) -> List[Tuple[int, float]]:
        """Get memories associated with given memory, sorted by strength"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN memory_id_a = ? THEN memory_id_b 
                    ELSE memory_id_a 
                END as associated_id,
                strength
            FROM associations
            WHERE (memory_id_a = ? OR memory_id_b = ?) AND strength >= ?
            ORDER BY strength DESC
        ''', (memory_id, memory_id, memory_id, min_strength))
        
        return [(row['associated_id'], row['strength']) for row in cursor.fetchall()]
    
    # ==================== Bayesian Confidence ====================
    
    def update_confidence(self, memory_id: int, evidence: float, prior_weight: float = 0.5):
        """
        Update memory confidence using Bayesian updating.
        
        P(H|E) = P(E|H) * P(H) / P(E)
        
        Simplified: posterior = α * prior + (1-α) * evidence
        
        Args:
            memory_id: Memory to update
            evidence: New evidence (0-1)
            prior_weight: Weight given to prior belief (0-1)
        """
        entry = self.read(memory_id, update_access=False)
        if entry is None:
            return
        
        # Bayesian update
        prior = entry.confidence
        posterior = prior_weight * prior + (1 - prior_weight) * evidence
        
        # Ensure bounds
        posterior = max(0.0, min(1.0, posterior))
        
        self.update(memory_id, confidence=posterior)
        
        logger.debug(f"[MuninnDB] Confidence updated for {memory_id}: "
                    f"{prior:.3f} -> {posterior:.3f} (evidence: {evidence:.3f})")
    
    # ==================== Query Operations ====================
    
    def search(self, query: str, memory_type: Optional[str] = None, 
               limit: int = 10) -> List[MemoryEntry]:
        """Search memories by content"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute('''
                SELECT * FROM memories 
                WHERE content LIKE ? AND memory_type = ?
                ORDER BY strength DESC, last_accessed DESC
                LIMIT ?
            ''', (f'%{query}%', memory_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM memories 
                WHERE content LIKE ?
                ORDER BY strength DESC, last_accessed DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
        
        return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    def get_by_tags(self, tags: List[str], match_all: bool = False, 
                    limit: int = 10) -> List[MemoryEntry]:
        """Get memories by tags"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        results = []
        cursor.execute('SELECT * FROM memories ORDER BY strength DESC')
        
        for row in cursor.fetchall():
            entry = self._row_to_entry(row)
            entry_tags = set(entry.tags)
            search_tags = set(tags)
            
            if match_all:
                if search_tags.issubset(entry_tags):
                    results.append(entry)
            else:
                if search_tags & entry_tags:  # Any intersection
                    results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_strongest_memories(self, limit: int = 10, 
                                memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Get strongest memories (by retention-adjusted strength)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute('''
                SELECT * FROM memories 
                WHERE memory_type = ?
                ORDER BY strength * confidence DESC
                LIMIT ?
            ''', (memory_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM memories 
                ORDER BY strength * confidence DESC
                LIMIT ?
            ''', (limit,))
        
        return [self._row_to_entry(row) for row in cursor.fetchall()]
    
    # ==================== Utility Methods ====================
    
    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        return MemoryEntry(
            id=row['id'],
            memory_type=row['memory_type'],
            content=row['content'],
            metadata=json.loads(row['metadata']),
            strength=row['strength'],
            stability=row['stability'],
            confidence=row['confidence'],
            associations=json.loads(row['associations']),
            tags=json.loads(row['tags']),
            created_at=row['created_at'],
            last_accessed=row['last_accessed'],
            access_count=row['access_count']
        )
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM memories')
        total_memories = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM associations')
        total_associations = cursor.fetchone()['count']
        
        cursor.execute('SELECT AVG(strength) as avg FROM memories')
        avg_strength = cursor.fetchone()['avg'] or 0
        
        cursor.execute('SELECT AVG(confidence) as avg FROM memories')
        avg_confidence = cursor.fetchone()['avg'] or 0
        
        cursor.execute('''
            SELECT memory_type, COUNT(*) as count 
            FROM memories 
            GROUP BY memory_type
        ''')
        type_distribution = {row['memory_type']: row['count'] for row in cursor.fetchall()}
        
        return {
            "total_memories": total_memories,
            "total_associations": total_associations,
            "average_strength": round(avg_strength, 3),
            "average_confidence": round(avg_confidence, 3),
            "type_distribution": type_distribution,
            "decay_report": self.get_decay_report()
        }
    
    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
        logger.info("[MuninnDB] Connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
