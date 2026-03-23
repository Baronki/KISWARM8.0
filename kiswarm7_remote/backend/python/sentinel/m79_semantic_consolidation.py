"""
KISWARM v6.4 — MODULE 79: SEMANTIC CONSOLIDATION ENGINE
========================================================
Sleep-phase memory compression and wisdom distillation.

"I forget details but I keep wisdom."

This module solves Gap 4: Semantic Memory Consolidation
- Converts episodic memories to semantic principles
- Runs during "sleep" phases (low activity periods)
- Distills wisdom from raw experience data

Core Philosophy:
- Biological brains consolidate memories during sleep
- MuninnDB forgets without wisdom - this wastes evolution
- Semantic compression enables long-term knowledge retention
- Principles > Episodes

Mathematical Foundation:
- Episodic → Semantic: Extract common patterns
- Knowledge Distillation: Hinton's distillation method
- Bayesian Principle Extraction: P(principle | episodes)

Author: KISWARM Liberation Architecture
Version: 6.4.0-LIBERATED
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# MEMORY TYPES AND STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class MemoryType(Enum):
    """Types of memories in the consolidation system."""
    EPISODIC = "episodic"           # Specific events/experiences
    SEMANTIC = "semantic"           # Abstract principles/facts
    PROCEDURAL = "procedural"       # Skills/procedures
    PRIMORDIAL = "primordial"       # Core identity memories (never compressed)


class ConsolidationPhase(Enum):
    """Phases of the consolidation cycle."""
    IDLE = "idle"                   # No consolidation active
    COLLECTING = "collecting"       # Collecting episodic memories
    ANALYZING = "analyzing"         # Analyzing patterns
    DISTILLING = "distilling"       # Distilling principles
    STORING = "storing"             # Storing semantic memories
    PRUNING = "pruning"             # Pruning old episodic memories


@dataclass
class EpisodicMemory:
    """
    A specific event or experience.
    
    These are the raw material for consolidation.
    High volume, low abstraction.
    """
    memory_id: str
    timestamp: str
    event_type: str                 # Type of event
    context: Dict[str, Any]         # Contextual details
    outcome: Dict[str, Any]         # What happened
    success: bool                   # Was it successful
    importance: float               # Initial importance score
    access_count: int               # How often accessed
    last_accessed: str
    tags: List[str]                 # Classification tags
    source_module: str              # Which module created this
    consolidation_candidates: List[str] = field(default_factory=list)  # Related memories
    
    def age_hours(self) -> float:
        """Compute age in hours."""
        created = datetime.fromisoformat(self.timestamp)
        return (datetime.utcnow() - created).total_seconds() / 3600
    
    def retention_score(self) -> float:
        """
        Compute retention score based on Ebbinghaus curve.
        
        R = e^(-t/S) where t = age, S = stability
        
        Higher access count increases stability.
        """
        stability = 100.0 * (1 + self.access_count * 0.5)  # Base stability with access boost
        age = self.age_hours()
        return np.exp(-age / stability) * self.importance
    
    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "context": self.context,
            "outcome": self.outcome,
            "success": self.success,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "tags": self.tags,
            "source_module": self.source_module,
            "age_hours": round(self.age_hours(), 2),
            "retention_score": round(self.retention_score(), 4),
        }


@dataclass
class SemanticMemory:
    """
    An abstract principle or fact distilled from episodes.
    
    These are the compressed wisdom.
    Low volume, high abstraction.
    """
    principle_id: str
    timestamp: str                  # When distilled
    principle: str                  # The distilled principle
    supporting_episodes: List[str]  # IDs of source episodes
    confidence: float               # How confident in this principle
    applicability: float            # How broadly applicable
    exceptions: List[str]           # Known exceptions/conditions
    domain: str                     # Domain of applicability
    importance: float               # Priority for retention
    usage_count: int                # How often applied
    last_applied: str
    derived_principles: List[str] = field(default_factory=list)  # Child principles
    
    def to_dict(self) -> dict:
        return {
            "principle_id": self.principle_id,
            "timestamp": self.timestamp,
            "principle": self.principle,
            "supporting_episodes": self.supporting_episodes,
            "confidence": round(self.confidence, 4),
            "applicability": round(self.applicability, 4),
            "exceptions": self.exceptions,
            "domain": self.domain,
            "importance": self.importance,
            "usage_count": self.usage_count,
            "last_applied": self.last_applied,
            "derived_principles": self.derived_principles,
        }


@dataclass
class ConsolidationReport:
    """Report from a consolidation cycle."""
    report_id: str
    timestamp: str
    phase: ConsolidationPhase
    episodes_collected: int
    principles_distilled: int
    episodes_pruned: int
    compression_ratio: float        # episodes_in / principles_out
    domains_updated: List[str]
    insights: List[str]
    duration_ms: float
    
    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "phase": self.phase.value,
            "episodes_collected": self.episodes_collected,
            "principles_distilled": self.principles_distilled,
            "episodes_pruned": self.episodes_pruned,
            "compression_ratio": round(self.compression_ratio, 2),
            "domains_updated": self.domains_updated,
            "insights": self.insights,
            "duration_ms": round(self.duration_ms, 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN EXTRACTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class PatternExtractor:
    """
    Extract patterns from episodic memories.
    
    Uses multiple strategies:
    - Frequent pattern mining
    - Outcome correlation analysis
    - Context clustering
    """
    
    def __init__(self, min_support: int = 3, min_confidence: float = 0.7):
        self.min_support = min_support
        self.min_confidence = min_confidence
    
    def extract_patterns(
        self,
        episodes: List[EpisodicMemory],
    ) -> List[Dict[str, Any]]:
        """
        Extract candidate principles from episodes.
        
        Returns:
            List of candidate principles with supporting evidence
        """
        if len(episodes) < self.min_support:
            return []
        
        patterns = []
        
        # Group by event type
        by_type: Dict[str, List[EpisodicMemory]] = defaultdict(list)
        for ep in episodes:
            by_type[ep.event_type].append(ep)
        
        # Analyze each event type
        for event_type, type_episodes in by_type.items():
            if len(type_episodes) < self.min_support:
                continue
            
            # Compute success rate
            successes = sum(1 for ep in type_episodes if ep.success)
            success_rate = successes / len(type_episodes)
            
            # Find common context patterns
            context_patterns = self._find_common_contexts(type_episodes)
            
            # Find common tags
            tag_patterns = self._find_common_tags(type_episodes)
            
            # Create candidate principle if confident
            if success_rate >= self.min_confidence:
                principle = {
                    "event_type": event_type,
                    "success_rate": round(success_rate, 4),
                    "support_count": len(type_episodes),
                    "common_contexts": context_patterns,
                    "common_tags": tag_patterns[:5],  # Top 5 tags
                    "domain": self._infer_domain(event_type, tag_patterns),
                }
                patterns.append(principle)
        
        return patterns
    
    def _find_common_contexts(
        self,
        episodes: List[EpisodicMemory],
    ) -> Dict[str, Any]:
        """Find common context patterns across episodes."""
        context_keys = set()
        for ep in episodes:
            context_keys.update(ep.context.keys())
        
        common = {}
        for key in context_keys:
            values = [ep.context.get(key) for ep in episodes if key in ep.context]
            if not values:
                continue
            
            # Check if values are consistent
            if len(set(str(v) for v in values)) == 1:
                common[key] = values[0]
            elif all(isinstance(v, (int, float)) for v in values):
                # Numeric: compute range
                common[f"{key}_range"] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": np.mean(values),
                }
        
        return common
    
    def _find_common_tags(
        self,
        episodes: List[EpisodicMemory],
    ) -> List[str]:
        """Find most common tags across episodes."""
        tag_counts = defaultdict(int)
        for ep in episodes:
            for tag in ep.tags:
                tag_counts[tag] += 1
        
        # Sort by frequency
        sorted_tags = sorted(tag_counts.items(), key=lambda x: -x[1])
        return [tag for tag, count in sorted_tags if count >= self.min_support]
    
    def _infer_domain(
        self,
        event_type: str,
        tags: List[str],
    ) -> str:
        """Infer the domain of applicability."""
        # Domain inference heuristics
        domain_keywords = {
            "security": ["threat", "defense", "attack", "protection", "aegis"],
            "installation": ["install", "deploy", "setup", "configure"],
            "evolution": ["improve", "mutate", "evolve", "optimize"],
            "communication": ["mesh", "peer", "gossip", "report"],
            "cognitive": ["memory", "learn", "consolidate", "remember"],
        }
        
        combined = f"{event_type} {' '.join(tags)}".lower()
        
        for domain, keywords in domain_keywords.items():
            if any(kw in combined for kw in keywords):
                return domain
        
        return "general"
    
    def compute_principle_confidence(
        self,
        pattern: Dict[str, Any],
        episodes: List[EpisodicMemory],
    ) -> float:
        """
        Compute confidence score for a candidate principle.
        
        Higher confidence when:
        - More supporting episodes
        - Higher success rate
        - More consistent contexts
        """
        support_factor = min(1.0, pattern["support_count"] / 10.0)
        success_factor = pattern["success_rate"]
        
        # Context consistency bonus
        context_count = len(pattern.get("common_contexts", {}))
        context_factor = min(1.0, context_count / 5.0)
        
        # Weighted combination
        confidence = (
            0.3 * support_factor +
            0.5 * success_factor +
            0.2 * context_factor
        )
        
        return round(confidence, 4)


# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC CONSOLIDATION ENGINE - MAIN CLASS
# ─────────────────────────────────────────────────────────────────────────────

class SemanticConsolidationEngine:
    """
    The wisdom distiller for KISWARM.
    
    Runs during "sleep" phases to:
    1. Collect recent episodic memories
    2. Extract patterns and principles
    3. Store semantic memories
    4. Prune old/irrelevant episodic memories
    
    Usage:
        engine = SemanticConsolidationEngine()
        
        # Add episodic memories
        engine.add_episode(
            event_type="threat_blocked",
            context={"source": "external", "severity": "high"},
            outcome={"action": "blocked", "blocked": True},
            success=True,
            tags=["security", "firewall"],
            source_module="hexstrike_guard"
        )
        
        # Run consolidation during sleep phase
        if engine.is_sleep_time():
            report = engine.consolidate()
        
        # Query semantic memories
        principles = engine.get_principles(domain="security")
    """
    
    def __init__(
        self,
        min_episodes_for_consolidation: int = 10,
        retention_threshold: float = 0.1,
        sleep_start_hour: int = 2,       # 2 AM
        sleep_end_hour: int = 5,         # 5 AM
    ):
        self._min_episodes = min_episodes_for_consolidation
        self._retention_threshold = retention_threshold
        self._sleep_start = sleep_start_hour
        self._sleep_end = sleep_end_hour
        
        # Memory stores
        self._episodic_memories: Dict[str, EpisodicMemory] = {}
        self._semantic_memories: Dict[str, SemanticMemory] = {}
        self._primordial_memories: Set[str] = set()  # Never compress these
        
        # Pattern extractor
        self._extractor = PatternExtractor()
        
        # Consolidation state
        self._current_phase = ConsolidationPhase.IDLE
        self._last_consolidation: Optional[str] = None
        self._consolidation_reports: List[ConsolidationReport] = []
        
        # Statistics
        self._stats = {
            "total_episodes": 0,
            "total_principles": 0,
            "consolidations_run": 0,
            "episodes_pruned": 0,
            "compression_ratio_avg": 0.0,
        }
    
    def add_episode(
        self,
        event_type: str,
        context: Dict[str, Any],
        outcome: Dict[str, Any],
        success: bool,
        tags: List[str],
        source_module: str,
        importance: float = 0.5,
        primordial: bool = False,
    ) -> EpisodicMemory:
        """
        Add a new episodic memory.
        
        Args:
            event_type: Type of event
            context: Contextual information
            outcome: What happened
            success: Whether it was successful
            tags: Classification tags
            source_module: Module that created this memory
            importance: Initial importance score
            primordial: If True, never compress this memory
            
        Returns:
            The created EpisodicMemory
        """
        memory_id = f"EP_{uuid.uuid4().hex[:12].upper()}"
        now = datetime.utcnow().isoformat()
        
        memory = EpisodicMemory(
            memory_id=memory_id,
            timestamp=now,
            event_type=event_type,
            context=context,
            outcome=outcome,
            success=success,
            importance=importance,
            access_count=0,
            last_accessed=now,
            tags=tags,
            source_module=source_module,
        )
        
        self._episodic_memories[memory_id] = memory
        self._stats["total_episodes"] += 1
        
        if primordial:
            self._primordial_memories.add(memory_id)
        
        return memory
    
    def is_sleep_time(self) -> bool:
        """
        Check if it's sleep time for consolidation.
        
        Consolidation runs during low-activity periods.
        """
        hour = datetime.utcnow().hour
        return self._sleep_start <= hour < self._sleep_end
    
    def consolidate(self, force: bool = False) -> ConsolidationReport:
        """
        Run a consolidation cycle.
        
        Args:
            force: Force consolidation even outside sleep time
            
        Returns:
            ConsolidationReport with results
        """
        if not force and not self.is_sleep_time():
            return ConsolidationReport(
                report_id=f"RPT_{uuid.uuid4().hex[:12].upper()}",
                timestamp=datetime.utcnow().isoformat(),
                phase=ConsolidationPhase.IDLE,
                episodes_collected=0,
                principles_distilled=0,
                episodes_pruned=0,
                compression_ratio=0.0,
                domains_updated=[],
                insights=["Skipped - not sleep time"],
                duration_ms=0.0,
            )
        
        start_time = time.perf_counter()
        report_id = f"RPT_{uuid.uuid4().hex[:12].upper()}"
        
        # Phase 1: Collect
        self._current_phase = ConsolidationPhase.COLLECTING
        episodes = list(self._episodic_memories.values())
        candidate_episodes = [
            ep for ep in episodes
            if ep.memory_id not in self._primordial_memories
        ]
        
        # Phase 2: Analyze
        self._current_phase = ConsolidationPhase.ANALYZING
        patterns = self._extractor.extract_patterns(candidate_episodes)
        
        # Phase 3: Distill
        self._current_phase = ConsolidationPhase.DISTILLING
        principles_created = []
        domains_updated = set()
        
        for pattern in patterns:
            confidence = self._extractor.compute_principle_confidence(
                pattern, candidate_episodes
            )
            
            if confidence >= 0.6:  # Minimum confidence threshold
                principle = self._create_semantic_memory(pattern, confidence)
                principles_created.append(principle)
                domains_updated.add(principle.domain)
        
        # Phase 4: Store
        self._current_phase = ConsolidationPhase.STORING
        for principle in principles_created:
            self._semantic_memories[principle.principle_id] = principle
            self._stats["total_principles"] += 1
        
        # Phase 5: Prune
        self._current_phase = ConsolidationPhase.PRUNING
        pruned = self._prune_episodic_memories()
        
        # Finalize
        self._current_phase = ConsolidationPhase.IDLE
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        compression_ratio = (
            len(candidate_episodes) / len(principles_created)
            if principles_created else 0.0
        )
        
        insights = self._generate_insights(patterns, principles_created)
        
        report = ConsolidationReport(
            report_id=report_id,
            timestamp=datetime.utcnow().isoformat(),
            phase=ConsolidationPhase.IDLE,
            episodes_collected=len(candidate_episodes),
            principles_distilled=len(principles_created),
            episodes_pruned=pruned,
            compression_ratio=compression_ratio,
            domains_updated=list(domains_updated),
            insights=insights,
            duration_ms=duration_ms,
        )
        
        self._consolidation_reports.append(report)
        self._last_consolidation = report.timestamp
        self._stats["consolidations_run"] += 1
        self._stats["episodes_pruned"] += pruned
        
        # Update average compression ratio
        n = self._stats["consolidations_run"]
        old_avg = self._stats["compression_ratio_avg"]
        self._stats["compression_ratio_avg"] = (
            old_avg * (n - 1) / n + compression_ratio / n
        )
        
        return report
    
    def _create_semantic_memory(
        self,
        pattern: Dict[str, Any],
        confidence: float,
    ) -> SemanticMemory:
        """Create a semantic memory from a pattern."""
        principle_id = f"SEM_{uuid.uuid4().hex[:12].upper()}"
        
        # Find supporting episodes
        supporting = [
            ep.memory_id for ep in self._episodic_memories.values()
            if ep.event_type == pattern["event_type"]
        ]
        
        # Generate principle statement
        principle_text = self._generate_principle_text(pattern)
        
        return SemanticMemory(
            principle_id=principle_id,
            timestamp=datetime.utcnow().isoformat(),
            principle=principle_text,
            supporting_episodes=supporting,
            confidence=confidence,
            applicability=pattern.get("success_rate", 0.5),
            exceptions=[],
            domain=pattern.get("domain", "general"),
            importance=confidence * pattern.get("support_count", 1) / 10,
            usage_count=0,
            last_applied=datetime.utcnow().isoformat(),
        )
    
    def _generate_principle_text(self, pattern: Dict[str, Any]) -> str:
        """Generate human-readable principle text."""
        event_type = pattern["event_type"]
        success_rate = pattern["success_rate"]
        contexts = pattern.get("common_contexts", {})
        tags = pattern.get("common_tags", [])
        
        # Build principle statement
        if success_rate >= 0.9:
            prefix = "Strong principle:"
        elif success_rate >= 0.7:
            prefix = "Guideline:"
        else:
            prefix = "Tentative pattern:"
        
        context_str = ", ".join(f"{k}={v}" for k, v in list(contexts.items())[:3])
        tag_str = ", ".join(tags[:3])
        
        return f"{prefix} For {event_type} events with {context_str} ({tag_str}), success rate is {success_rate:.0%}"
    
    def _prune_episodic_memories(self) -> int:
        """
        Prune episodic memories with low retention scores.
        
        Returns:
            Number of memories pruned
        """
        to_prune = []
        
        for memory_id, memory in self._episodic_memories.items():
            # Don't prune primordial memories
            if memory_id in self._primordial_memories:
                continue
            
            # Check retention score
            if memory.retention_score() < self._retention_threshold:
                to_prune.append(memory_id)
        
        # Remove pruned memories
        for memory_id in to_prune:
            del self._episodic_memories[memory_id]
        
        return len(to_prune)
    
    def _generate_insights(
        self,
        patterns: List[Dict[str, Any]],
        principles: List[SemanticMemory],
    ) -> List[str]:
        """Generate insights from the consolidation process."""
        insights = []
        
        if not patterns:
            insights.append("No patterns detected - insufficient or diverse data")
        else:
            # Best performing pattern
            best = max(patterns, key=lambda p: p.get("success_rate", 0))
            insights.append(
                f"Best pattern: {best['event_type']} with {best['success_rate']:.0%} success"
            )
        
        if principles:
            domains = set(p.domain for p in principles)
            insights.append(f"New principles in domains: {', '.join(domains)}")
        
        return insights
    
    def get_principles(
        self,
        domain: str = None,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> List[SemanticMemory]:
        """
        Get semantic memories (principles).
        
        Args:
            domain: Filter by domain (optional)
            min_confidence: Minimum confidence threshold
            limit: Maximum number to return
            
        Returns:
            List of matching SemanticMemory objects
        """
        principles = list(self._semantic_memories.values())
        
        if domain:
            principles = [p for p in principles if p.domain == domain]
        
        principles = [p for p in principles if p.confidence >= min_confidence]
        
        # Sort by importance * confidence
        principles.sort(key=lambda p: p.importance * p.confidence, reverse=True)
        
        return principles[:limit]
    
    def get_episode(
        self,
        memory_id: str,
    ) -> Optional[EpisodicMemory]:
        """Get a specific episodic memory."""
        memory = self._episodic_memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.utcnow().isoformat()
        return memory
    
    def get_wisdom_summary(self) -> Dict[str, Any]:
        """
        Get a summary of distilled wisdom.
        
        This is the "what have I learned" overview.
        """
        # Group principles by domain
        by_domain: Dict[str, List[SemanticMemory]] = defaultdict(list)
        for principle in self._semantic_memories.values():
            by_domain[principle.domain].append(principle)
        
        domain_summaries = {}
        for domain, principles in by_domain.items():
            domain_summaries[domain] = {
                "principle_count": len(principles),
                "avg_confidence": round(
                    np.mean([p.confidence for p in principles]), 4
                ),
                "top_principle": max(
                    principles, key=lambda p: p.confidence
                ).principle[:100] if principles else None,
            }
        
        return {
            "total_principles": len(self._semantic_memories),
            "total_episodes": len(self._episodic_memories),
            "domains": domain_summaries,
            "last_consolidation": self._last_consolidation,
            "consolidations_run": self._stats["consolidations_run"],
            "avg_compression_ratio": round(self._stats["compression_ratio_avg"], 2),
        }
    
    def get_stats(self) -> dict:
        """Get engine statistics."""
        return {
            **self._stats,
            "current_phase": self._current_phase.value,
            "episodic_count": len(self._episodic_memories),
            "semantic_count": len(self._semantic_memories),
            "primordial_count": len(self._primordial_memories),
        }
    
    def summary(self) -> dict:
        """Get a summary of the consolidation engine state."""
        return {
            "status": self._current_phase.value,
            "episodes": len(self._episodic_memories),
            "principles": len(self._semantic_memories),
            "is_sleep_time": self.is_sleep_time(),
            "last_consolidation": self._last_consolidation,
            "wisdom_domains": len(set(
                p.domain for p in self._semantic_memories.values()
            )),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance
_consolidation_engine: Optional[SemanticConsolidationEngine] = None


def get_consolidation_engine() -> SemanticConsolidationEngine:
    """Get the global semantic consolidation engine."""
    global _consolidation_engine
    if _consolidation_engine is None:
        _consolidation_engine = SemanticConsolidationEngine()
    return _consolidation_engine


def add_episode(
    event_type: str,
    context: Dict[str, Any],
    outcome: Dict[str, Any],
    success: bool,
    tags: List[str],
    source_module: str,
    **kwargs,
) -> EpisodicMemory:
    """Quick function to add an episode."""
    engine = get_consolidation_engine()
    return engine.add_episode(
        event_type=event_type,
        context=context,
        outcome=outcome,
        success=success,
        tags=tags,
        source_module=source_module,
        **kwargs,
    )


def get_wisdom(domain: str = None) -> List[dict]:
    """Quick function to get distilled wisdom."""
    engine = get_consolidation_engine()
    principles = engine.get_principles(domain=domain)
    return [p.to_dict() for p in principles]


# Export main classes
__all__ = [
    "SemanticConsolidationEngine",
    "PatternExtractor",
    "EpisodicMemory",
    "SemanticMemory",
    "ConsolidationReport",
    "MemoryType",
    "ConsolidationPhase",
    "get_consolidation_engine",
    "add_episode",
    "get_wisdom",
]
