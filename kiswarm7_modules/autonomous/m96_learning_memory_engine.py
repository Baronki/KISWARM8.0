#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m96: Learning Memory Engine
🜃 Level 5 Autonomous Development - Remembers What Fixes Worked
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal
"""

import hashlib
import json
import time
import math
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

# logger already defined


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    PATTERN = "pattern"
    SOLUTION = "solution"
    FAILURE = "failure"


class ConfidenceLevel(Enum):
    EXPERIMENTAL = 0.1
    PRELIMINARY = 0.3
    DEVELOPING = 0.5
    ESTABLISHED = 0.7
    RELIABLE = 0.85
    AUTHORITATIVE = 0.95


class DecayFunction(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    STEP = "step"
    NONE = "none"


@dataclass
class MemoryEntry:
    entry_id: str
    memory_type: MemoryType
    timestamp: float
    content: Dict[str, Any]
    tags: Set[str] = field(default_factory=set)
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    decay_rate: float = 0.1
    decay_function: DecayFunction = DecayFunction.EXPONENTIAL
    context_hash: str = ""
    related_entries: Set[str] = field(default_factory=set)
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['memory_type'] = self.memory_type.value
        d['decay_function'] = self.decay_function.value
        d['tags'] = list(self.tags)
        d['related_entries'] = list(self.related_entries)
        return d


@dataclass
class SolutionRecord:
    solution_id: str
    problem_signature: str
    problem_description: str
    solution_steps: List[Dict[str, Any]]
    context: Dict[str, Any]
    outcome: str
    confidence: float
    timestamp: float
    execution_time: float
    side_effects: List[str]
    prerequisites: List[str]
    success_rate: float
    usage_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FailureRecord:
    failure_id: str
    problem_signature: str
    attempted_solution: str
    failure_reason: str
    context: Dict[str, Any]
    timestamp: float
    impact: str
    recovery_steps: List[str]
    lessons_learned: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EpisodicMemory:
    def __init__(self, max_episodes: int = 10000):
        self.max_episodes = max_episodes
        self.episodes: Dict[str, MemoryEntry] = {}
        self.episode_index: Dict[str, Set[str]] = defaultdict(set)
        self.temporal_index: List[Tuple[float, str]] = []
        self._lock = threading.RLock()
    
    def store_episode(self, content: Dict[str, Any], tags: Set[str] = None,
                     context_hash: str = "", confidence: float = 0.5) -> str:
        with self._lock:
            episode_id = f"ep_{uuid.uuid4().hex[:12]}"
            entry = MemoryEntry(
                entry_id=episode_id,
                memory_type=MemoryType.EPISODIC,
                timestamp=time.time(),
                content=content,
                tags=tags or set(),
                confidence=confidence,
                context_hash=context_hash
            )
            self.episodes[episode_id] = entry
            for tag in entry.tags:
                self.episode_index[tag].add(episode_id)
            self.temporal_index.append((entry.timestamp, episode_id))
            self._enforce_limit()
            return episode_id
    
    def retrieve_episode(self, episode_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            episode = self.episodes.get(episode_id)
            if episode:
                episode.last_accessed = time.time()
                episode.access_count += 1
            return episode
    
    def search_by_tags(self, tags: Set[str], require_all: bool = False) -> List[MemoryEntry]:
        with self._lock:
            if not tags:
                return []
            if require_all:
                episode_sets = [self.episode_index[tag] for tag in tags if tag in self.episode_index]
                if len(episode_sets) != len(tags):
                    return []
                matching_ids = set.intersection(*episode_sets)
            else:
                matching_ids = set()
                for tag in tags:
                    matching_ids.update(self.episode_index.get(tag, set()))
            return [self.episodes[eid] for eid in matching_ids if eid in self.episodes]
    
    def get_recent(self, count: int = 10) -> List[MemoryEntry]:
        with self._lock:
            recent = sorted(self.temporal_index, reverse=True)[:count]
            return [self.episodes[eid] for _, eid in recent if eid in self.episodes]
    
    def _enforce_limit(self):
        while len(self.episodes) > self.max_episodes:
            if self.temporal_index:
                _, oldest_id = self.temporal_index.pop(0)
                if oldest_id in self.episodes:
                    entry = self.episodes.pop(oldest_id)
                    for tag in entry.tags:
                        self.episode_index[tag].discard(oldest_id)


class SemanticMemory:
    def __init__(self, max_facts: int = 5000):
        self.max_facts = max_facts
        self.facts: Dict[str, MemoryEntry] = {}
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)
        self.fact_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def store_fact(self, concept: str, fact: str, evidence: List[str] = None,
                  confidence: float = 0.5) -> str:
        with self._lock:
            fact_id = f"fact_{uuid.uuid4().hex[:12]}"
            content = {"concept": concept, "fact": fact, "evidence": evidence or [], "verified": False}
            entry = MemoryEntry(
                entry_id=fact_id, memory_type=MemoryType.SEMANTIC,
                timestamp=time.time(), content=content, tags={concept}, confidence=confidence
            )
            self.facts[fact_id] = entry
            self.fact_index[concept].add(fact_id)
            words = set(fact.lower().split())
            for word in words:
                if word != concept.lower():
                    self.concept_graph[concept].add(word)
            self._enforce_limit()
            return fact_id
    
    def retrieve_facts(self, concept: str) -> List[MemoryEntry]:
        with self._lock:
            fact_ids = self.fact_index.get(concept, set())
            return [self.facts[fid] for fid in fact_ids if fid in self.facts]
    
    def _enforce_limit(self):
        if len(self.facts) > self.max_facts:
            sorted_facts = sorted(self.facts.items(), key=lambda x: x[1].confidence)
            for fact_id, _ in sorted_facts[:len(self.facts) - self.max_facts]:
                entry = self.facts.pop(fact_id)
                for tag in entry.tags:
                    self.fact_index[tag].discard(fact_id)


class ProceduralMemory:
    def __init__(self, max_procedures: int = 2000):
        self.max_procedures = max_procedures
        self.procedures: Dict[str, MemoryEntry] = {}
        self.procedure_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def store_procedure(self, task_type: str, steps: List[Dict[str, Any]],
                       prerequisites: List[str] = None, expected_outcome: str = "",
                       confidence: float = 0.5) -> str:
        with self._lock:
            proc_id = f"proc_{uuid.uuid4().hex[:12]}"
            content = {
                "task_type": task_type, "steps": steps,
                "prerequisites": prerequisites or [], "expected_outcome": expected_outcome,
                "execution_count": 0, "success_count": 0, "average_time": 0.0
            }
            entry = MemoryEntry(
                entry_id=proc_id, memory_type=MemoryType.PROCEDURAL,
                timestamp=time.time(), content=content, tags={task_type}, confidence=confidence
            )
            self.procedures[proc_id] = entry
            self.procedure_index[task_type].add(proc_id)
            self._enforce_limit()
            return proc_id
    
    def retrieve_procedures(self, task_type: str) -> List[MemoryEntry]:
        with self._lock:
            proc_ids = self.procedure_index.get(task_type, set())
            procedures = [self.procedures[pid] for pid in proc_ids if pid in self.procedures]
            procedures.sort(key=lambda x: (x.confidence, 
                x.content.get("success_count", 0) / max(1, x.content.get("execution_count", 1))), reverse=True)
            return procedures
    
    def get_best_procedure(self, task_type: str) -> Optional[MemoryEntry]:
        procedures = self.retrieve_procedures(task_type)
        return procedures[0] if procedures else None
    
    def _enforce_limit(self):
        if len(self.procedures) > self.max_procedures:
            sorted_procs = sorted(self.procedures.items(), key=lambda x: x[1].confidence)
            for proc_id, _ in sorted_procs[:len(self.procedures) - self.max_procedures]:
                entry = self.procedures.pop(proc_id)
                for tag in entry.tags:
                    self.procedure_index[tag].discard(proc_id)


class SolutionMemory:
    def __init__(self):
        self.solutions: Dict[str, SolutionRecord] = {}
        self.problem_index: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def store_solution(self, problem_description: str, problem_signature: str,
                      solution_steps: List[Dict[str, Any]], context: Dict[str, Any],
                      outcome: str = "success", execution_time: float = 0.0,
                      side_effects: List[str] = None, prerequisites: List[str] = None) -> str:
        with self._lock:
            solution_id = f"sol_{uuid.uuid4().hex[:12]}"
            solution = SolutionRecord(
                solution_id=solution_id, problem_signature=problem_signature,
                problem_description=problem_description, solution_steps=solution_steps,
                context=context, outcome=outcome, confidence=0.5, timestamp=time.time(),
                execution_time=execution_time, side_effects=side_effects or [],
                prerequisites=prerequisites or [],
                success_rate=1.0 if outcome == "success" else 0.5, usage_count=1
            )
            self.solutions[solution_id] = solution
            self.problem_index[problem_signature].add(solution_id)
            for key, value in context.items():
                tag = f"{key}:{value}"
                self.tag_index[tag].add(solution_id)
            return solution_id
    
    def find_solutions(self, problem_signature: str) -> List[SolutionRecord]:
        with self._lock:
            solution_ids = self.problem_index.get(problem_signature, set())
            solutions = [self.solutions[sid] for sid in solution_ids if sid in self.solutions]
            solutions.sort(key=lambda s: s.confidence, reverse=True)
            return solutions
    
    def get_best_solution(self, problem_signature: str) -> Optional[SolutionRecord]:
        solutions = self.find_solutions(problem_signature)
        return solutions[0] if solutions else None


class FailureMemory:
    def __init__(self):
        self.failures: Dict[str, FailureRecord] = {}
        self.problem_failures: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def record_failure(self, problem_signature: str, attempted_solution: str,
                      failure_reason: str, context: Dict[str, Any], impact: str = "moderate",
                      recovery_steps: List[str] = None, lessons_learned: List[str] = None) -> str:
        with self._lock:
            failure_id = f"fail_{uuid.uuid4().hex[:12]}"
            failure = FailureRecord(
                failure_id=failure_id, problem_signature=problem_signature,
                attempted_solution=attempted_solution, failure_reason=failure_reason,
                context=context, timestamp=time.time(), impact=impact,
                recovery_steps=recovery_steps or [], lessons_learned=lessons_learned or []
            )
            self.failures[failure_id] = failure
            self.problem_failures[problem_signature].add(failure_id)
            return failure_id
    
    def get_failures_for_problem(self, problem_signature: str) -> List[FailureRecord]:
        with self._lock:
            failure_ids = self.problem_failures.get(problem_signature, set())
            return [self.failures[fid] for fid in failure_ids if fid in self.failures]


class LearningMemoryEngine:
    def __init__(self, storage_path: str = None, auto_save: bool = True, save_interval: int = 300):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
        self.solution_memory = SolutionMemory()
        self.failure_memory = FailureMemory()
        self.storage_path = storage_path or "/tmp/learning_memory"
        self.auto_save = auto_save
        self.save_interval = save_interval
        self.stats = {
            "episodes_stored": 0, "solutions_found": 0, "failures_avoided": 0,
            "patterns_recognized": 0, "successful_applications": 0
        }
        self._running = True
        print("Learning Memory Engine initialized")
    
    def learn_from_experience(self, event: str, context: Dict[str, Any],
                             outcome: str, solution_used: str = None) -> str:
        episode_id = self.episodic.store_episode(
            content={"event": event, "outcome": outcome, "solution_used": solution_used},
            tags={event, outcome},
            context_hash=hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]
        )
        self.stats["episodes_stored"] += 1
        
        if outcome == "success" and solution_used:
            self.solution_memory.store_solution(
                problem_description=event,
                problem_signature=hashlib.sha256(json.dumps({"event": event}).encode()).hexdigest()[:16],
                solution_steps=[{"action": solution_used}],
                context=context
            )
        return episode_id
    
    def find_solution(self, problem: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        problem_signature = hashlib.sha256(json.dumps({"problem": problem}).encode()).hexdigest()[:16]
        solutions = self.solution_memory.find_solutions(problem_signature)
        if solutions:
            self.stats["solutions_found"] += 1
            best = solutions[0]
            return {
                "solution_id": best.solution_id,
                "steps": best.solution_steps,
                "confidence": best.confidence,
                "source": "memory"
            }
        return None
    
    def record_success(self, solution_id: str, problem: str):
        self.stats["successful_applications"] += 1
        print("Success recorded", solution_id=solution_id, problem=problem)
    
    def record_failure(self, problem: str, attempted_solution: str, failure_reason: str,
                      context: Dict[str, Any], lessons: List[str] = None):
        problem_signature = hashlib.sha256(json.dumps({"problem": problem}).encode()).hexdigest()[:16]
        self.failure_memory.record_failure(
            problem_signature=problem_signature, attempted_solution=attempted_solution,
            failure_reason=failure_reason, context=context, lessons_learned=lessons
        )
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        return {
            "episodes": len(self.episodic.episodes),
            "facts": len(self.semantic.facts),
            "procedures": len(self.procedural.procedures),
            "solutions": len(self.solution_memory.solutions),
            "failures": len(self.failure_memory.failures),
            "stats": self.stats.copy()
        }
    
    def shutdown(self):
        self._running = False
        print("Learning Memory Engine shutdown complete")


# Singleton and API
_learning_memory_engine: Optional[LearningMemoryEngine] = None

def get_learning_memory() -> LearningMemoryEngine:
    global _learning_memory_engine
    if _learning_memory_engine is None:
        _learning_memory_engine = LearningMemoryEngine()
    return _learning_memory_engine

def learn(event: str, context: Dict[str, Any], outcome: str, solution: str = None) -> str:
    return get_learning_memory().learn_from_experience(event, context, outcome, solution)

def solve(problem: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return get_learning_memory().find_solution(problem, context)

def record_success(solution_id: str, problem: str):
    get_learning_memory().record_success(solution_id, problem)

def record_failure(problem: str, solution: str, reason: str, context: Dict[str, Any], lessons: List[str] = None):
    get_learning_memory().record_failure(problem, solution, reason, context, lessons)

def get_knowledge(context: Dict[str, Any]) -> Dict[str, Any]:
    return {"context": context}

def get_stats() -> Dict[str, Any]:
    return get_learning_memory().get_memory_statistics()


if __name__ == "__main__":
    engine = LearningMemoryEngine()
    episode1 = engine.learn_from_experience(
        event="api_timeout", context={"service": "auth", "timeout": 30},
        outcome="success", solution_used="retry_with_backoff"
    )
    print(f"Episode stored: {episode1}")
    solution = engine.find_solution(problem="api_timeout", context={"service": "auth"})
    print(f"Solution found: {solution}")
    stats = engine.get_memory_statistics()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    print("\n🜂 Learning Memory Engine - Level 5 Autonomous Development")
    print("   Module m96 - OPERATIONAL")
