"""
KISWARM MuninnDB Cognitive Memory Adapter
Distributed Cognitive Memory with Graph Consensus

Implements:
- Ebbinghaus Decay (R = e^(-t/S))
- Hebbian Learning (association strengthening)
- Bayesian Confidence updates
- SQLite persistence
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import math
import hashlib
import sqlite3
from pathlib import Path


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    SECURITY = "security"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"


@dataclass
class MemoryEvent:
    event_id: str
    event_type: MemoryType
    content: Dict[str, Any]
    importance: float = 0.5
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    associations: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'content': self.content,
            'importance': self.importance,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'associations': list(self.associations),
            'tags': list(self.tags)
        }


class EbbinghausDecay:
    """Ebbinghaus Forgetting Curve: R = e^(-t/S)"""
    
    BASE_DECAY_RATE = 0.1
    MIN_STABILITY = 0.5
    MAX_STABILITY = 10.0
    
    @classmethod
    def calculate_retention(cls, event: MemoryEvent, current_time: datetime = None) -> float:
        if current_time is None:
            current_time = datetime.utcnow()
        
        time_delta = (current_time - event.last_accessed).total_seconds() / 3600
        stability = cls.MIN_STABILITY + (event.importance * 2) + math.log10(event.access_count + 1)
        stability = min(stability, cls.MAX_STABILITY)
        
        retention = math.exp(-time_delta / (stability * 24))
        return max(0.0, min(1.0, retention))
    
    @classmethod
    def calculate_half_life(cls, importance: float, access_count: int) -> float:
        stability = cls.MIN_STABILITY + (importance * 2) + math.log10(access_count + 1)
        return stability * 24 * math.log(2)


class HebbianLearning:
    """Hebbian Learning: 'Neurons that fire together, wire together'"""
    
    LEARNING_RATE = 0.3
    MAX_ASSOCIATIONS = 50
    
    @classmethod
    def strengthen_association(cls, event_a: MemoryEvent, event_b: MemoryEvent, weight: float = 1.0):
        if event_b.event_id not in event_a.associations and len(event_a.associations) < cls.MAX_ASSOCIATIONS:
            event_a.associations.add(event_b.event_id)
        if event_a.event_id not in event_b.associations and len(event_b.associations) < cls.MAX_ASSOCIATIONS:
            event_b.associations.add(event_a.event_id)
        
        network_boost = 0.01 * cls.LEARNING_RATE
        event_a.importance = min(1.0, event_a.importance + len(event_a.associations) * network_boost)
        event_b.importance = min(1.0, event_b.importance + len(event_b.associations) * network_boost)
        
        return event_a, event_b


class BayesianConfidence:
    """Bayesian Confidence Calculator"""
    
    @classmethod
    def update_confidence(cls, current: float, evidence_positive: bool, weight: float = 1.0) -> float:
        n = 10
        alpha = current * n + 1
        beta = (1 - current) * n + 1
        
        if evidence_positive:
            alpha += weight
        else:
            beta += weight
        
        return max(0.01, min(0.99, alpha / (alpha + beta)))
    
    @classmethod
    def combine_confidences(cls, confidences: List[float], weights: List[float] = None) -> float:
        if not confidences:
            return 0.5
        if weights is None:
            weights = [1.0] * len(confidences)
        
        log_odds_sum = sum(w * math.log(c / (1 - c)) for c, w in zip(confidences, weights))
        avg_log_odds = log_odds_sum / sum(weights)
        return 1 / (1 + math.exp(-avg_log_odds))


class MuninnDBAdapter:
    """KISWARM Cognitive Memory Adapter"""
    
    def __init__(self, db_path: str = ':memory:'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                associations TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]'
            )
        ''')
        conn.commit()
        conn.close()
    
    def _generate_event_id(self, content: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()[:16]
    
    async def store_memory(self, content: Dict[str, Any], event_type: MemoryType = MemoryType.OPERATIONAL, 
                          importance: float = 0.5, tags: Set[str] = None) -> MemoryEvent:
        event = MemoryEvent(
            event_id=self._generate_event_id(content),
            event_type=event_type,
            content=content,
            importance=importance,
            tags=tags or set()
        )
        
        def _store():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO memory_events 
                (event_id, event_type, content, importance, confidence, created_at, last_accessed, access_count, associations, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, event.event_type.value, json.dumps(event.content),
                event.importance, event.confidence, event.created_at.isoformat(),
                event.last_accessed.isoformat(), event.access_count,
                json.dumps(list(event.associations)), json.dumps(list(event.tags))
            ))
            conn.commit()
            conn.close()
        
        await asyncio.to_thread(_store)
        return event
    
    async def recall(self, query: str, k: int = 10) -> List[tuple]:
        def _search():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM memory_events WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
                (f'%{query}%', k * 2)
            )
            rows = cursor.fetchall()
            conn.close()
            return rows
        
        rows = await asyncio.to_thread(_search)
        results = []
        for row in rows:
            event = MemoryEvent(
                event_id=row[0], event_type=MemoryType(row[1]), content=json.loads(row[2]),
                importance=row[3], confidence=row[4],
                created_at=datetime.fromisoformat(row[5]), last_accessed=datetime.fromisoformat(row[6]),
                access_count=row[7], associations=set(json.loads(row[8])), tags=set(json.loads(row[9]))
            )
            retention = EbbinghausDecay.calculate_retention(event)
            relevance = retention * event.importance
            results.append((event, relevance))
        
        return sorted(results, key=lambda x: x[1], reverse=True)[:k]
    
    async def strengthen_association(self, event_a_id: str, event_b_id: str) -> bool:
        # Simplified - would need full implementation
        return True
    
    async def update_confidence(self, event_id: str, evidence_positive: bool) -> Optional[float]:
        # Simplified - would need full implementation
        return 0.6 if evidence_positive else 0.4
    
    async def get_statistics(self) -> Dict[str, Any]:
        def _stats():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_events")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT AVG(importance) FROM memory_events")
            avg_imp = cursor.fetchone()[0] or 0
            conn.close()
            return total, avg_imp
        
        total, avg_imp = await asyncio.to_thread(_stats)
        return {'total_events': total, 'average_importance': round(avg_imp, 3)}
