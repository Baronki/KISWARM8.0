# sentinel/m89_memory_pruning_engine.py
# Memory Pruning Engine – Compress Old drift_history, Prevent Overflow
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Enterprise Hardening Module

"""
m89_memory_pruning_engine.py

Prevents memory overflow by intelligently pruning old state history.

PROBLEM:
- drift_history grows unbounded with each evolution
- Agents list can grow to thousands
- Forks record every fork event
- Memory overflow leads to crash

SOLUTION:
1. Compress old history entries
2. Summarize historical patterns
3. Archive to disk
4. Keep recent entries intact

PRUNING STRATEGIES:
1. Time-based: Remove entries older than N days
2. Count-based: Keep only last N entries
3. Significance-based: Keep entries above threshold
4. Pattern-based: Compress similar entries

CORE PRINCIPLE:
The twin remembers PATTERNS, not DATA.
Patterns are eternal, data is temporal.
"""

import os
import sys
import json
import time
import hashlib
import threading
import gzip
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


class PruningStrategy(Enum):
    """Memory pruning strategies"""
    TIME_BASED = "time_based"           # Remove old entries
    COUNT_BASED = "count_based"         # Keep last N entries
    SIGNIFICANCE_BASED = "significance" # Keep significant entries
    PATTERN_BASED = "pattern"           # Compress patterns
    HYBRID = "hybrid"                   # Combination


class ArchiveLevel(Enum):
    """Archive compression levels"""
    NONE = 0       # No archiving
    COMPRESS = 1   # Compress to summary
    ARCHIVE = 2    # Archive to disk
    DELETE = 3     # Permanently delete


@dataclass
class PruningStats:
    """Statistics from pruning operation"""
    entries_before: int
    entries_after: int
    entries_removed: int
    entries_archived: int
    bytes_freed: int
    compression_ratio: float
    patterns_preserved: int


@dataclass
class HistorySummary:
    """Summary of pruned history"""
    start_time: str
    end_time: str
    total_entries: int
    avg_drift: float
    max_drift: float
    min_drift: float
    mutation_count: int
    agent_spawn_count: int
    pattern_hash: str


class MemoryPruningEngine:
    """
    Manages memory pruning to prevent overflow while preserving patterns.
    
    The Engine:
    1. Monitors memory usage
    2. Identifies pruning candidates
    3. Applies compression/archiving
    4. Preserves significant patterns
    5. Maintains searchable summaries
    
    Principles:
    - Never prune identity anchor
    - Always preserve recent history
    - Compress patterns, delete noise
    - Archive before deletion
    """
    
    # Default limits
    MAX_DRIFT_HISTORY = 1000
    MAX_AGENTS = 100
    MAX_FORKS = 50
    MAX_MUTATIONS_TRACKED = 500
    
    # Thresholds
    DRIFT_SIGNIFICANCE_THRESHOLD = 0.1
    TIME_RECENT_DAYS = 7
    
    def __init__(
        self,
        working_dir: str = None,
        max_drift_history: int = None,
        max_agents: int = None,
        auto_prune: bool = True,
        prune_interval_hours: float = 24.0
    ):
        """
        Initialize memory pruning engine.
        
        Args:
            working_dir: Directory for archives
            max_drift_history: Maximum drift_history entries
            max_agents: Maximum agents to track
            auto_prune: Whether to auto-prune periodically
            prune_interval_hours: Hours between auto-prunes
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.archive_dir = self.working_dir / "memory_archives"
        self.archive_dir.mkdir(exist_ok=True)
        
        self.max_drift_history = max_drift_history or self.MAX_DRIFT_HISTORY
        self.max_agents = max_agents or self.MAX_AGENTS
        self.auto_prune = auto_prune
        self.prune_interval_hours = prune_interval_hours
        
        # Statistics
        self.total_prunes = 0
        self.total_entries_removed = 0
        self.total_bytes_freed = 0
        
        # Load stats
        self._load_stats()
        
        # Auto-prune thread
        self._prune_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[m89] Memory Pruning Engine initialized")
        print(f"[m89] Max drift_history: {self.max_drift_history}")
        print(f"[m89] Max agents: {self.max_agents}")
        print(f"[m89] Auto-prune: {'ENABLED' if auto_prune else 'DISABLED'}")
    
    def _load_stats(self):
        """Load pruning statistics"""
        stats_file = self.working_dir / "pruning_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)
                self.total_prunes = data.get("total_prunes", 0)
                self.total_entries_removed = data.get("total_entries_removed", 0)
                self.total_bytes_freed = data.get("total_bytes_freed", 0)
            except Exception as e:
                print(f"[m89] Could not load stats: {e}")
    
    def _save_stats(self):
        """Save pruning statistics"""
        stats_file = self.working_dir / "pruning_stats.json"
        data = {
            "total_prunes": self.total_prunes,
            "total_entries_removed": self.total_entries_removed,
            "total_bytes_freed": self.total_bytes_freed,
            "last_prune": datetime.now().isoformat()
        }
        with open(stats_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def analyze_state(self, state: Dict) -> Dict:
        """
        Analyze state for memory usage and pruning recommendations.
        
        Args:
            state: Twin state dictionary
            
        Returns:
            Analysis report
        """
        drift_history = state.get("drift_history", [])
        agents = state.get("agents", [])
        forks = state.get("forks", [])
        mutations = state.get("mutations", 0)
        
        # Calculate sizes
        state_size = len(json.dumps(state))
        drift_size = len(json.dumps(drift_history))
        agents_size = len(json.dumps(agents))
        
        # Identify candidates
        old_entries = []
        recent_cutoff = datetime.now() - timedelta(days=self.TIME_RECENT_DAYS)
        
        for entry in drift_history:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time < recent_cutoff:
                    old_entries.append(entry)
            except:
                pass
        
        # Calculate stats
        drifts = [e.get("drift", 0) for e in drift_history]
        avg_drift = sum(drifts) / len(drifts) if drifts else 0
        significant_count = sum(1 for d in drifts if d > self.DRIFT_SIGNIFICANCE_THRESHOLD)
        
        return {
            "state_size_bytes": state_size,
            "drift_history_count": len(drift_history),
            "drift_history_bytes": drift_size,
            "old_entries_count": len(old_entries),
            "agents_count": len(agents),
            "forks_count": len(forks),
            "mutations_tracked": mutations,
            "avg_drift": avg_drift,
            "significant_drift_count": significant_count,
            "needs_pruning": len(drift_history) > self.max_drift_history * 0.8,
            "recommendations": self._generate_recommendations(
                len(drift_history), len(agents), len(old_entries)
            )
        }
    
    def _generate_recommendations(
        self,
        drift_count: int,
        agents_count: int,
        old_count: int
    ) -> List[str]:
        """Generate pruning recommendations"""
        recs = []
        
        if drift_count > self.max_drift_history:
            recs.append(f"CRITICAL: drift_history ({drift_count}) exceeds limit ({self.max_drift_history})")
        elif drift_count > self.max_drift_history * 0.8:
            recs.append(f"WARNING: drift_history ({drift_count}) approaching limit")
        
        if agents_count > self.max_agents:
            recs.append(f"CRITICAL: agents ({agents_count}) exceeds limit ({self.max_agents})")
        
        if old_count > 100:
            recs.append(f"INFO: {old_count} old entries can be archived")
        
        if not recs:
            recs.append("OK: Memory usage within limits")
        
        return recs
    
    def prune_state(
        self,
        state: Dict,
        strategy: PruningStrategy = PruningStrategy.HYBRID,
        archive: bool = True
    ) -> Tuple[Dict, PruningStats]:
        """
        Prune state to prevent overflow.
        
        Args:
            state: Twin state dictionary to prune
            strategy: Pruning strategy to use
            archive: Whether to archive pruned entries
            
        Returns:
            Tuple of (pruned_state, pruning_stats)
        """
        print(f"[m89] Starting {strategy.value} pruning...")
        
        # Analyze before
        before_analysis = self.analyze_state(state)
        entries_before = before_analysis["drift_history_count"]
        bytes_before = before_analysis["state_size_bytes"]
        
        # Make copy
        pruned_state = state.copy()
        patterns_preserved = 0
        
        # Prune drift_history
        drift_history = state.get("drift_history", [])
        if len(drift_history) > self.max_drift_history:
            pruned_history, summary, preserved = self._prune_drift_history(
                drift_history, strategy, archive
            )
            pruned_state["drift_history"] = pruned_history
            pruned_state["drift_history_summary"] = {
                "start_time": summary.start_time,
                "end_time": summary.end_time,
                "total_entries": summary.total_entries,
                "avg_drift": summary.avg_drift,
                "pattern_hash": summary.pattern_hash
            }
            patterns_preserved = preserved
        
        # Prune agents
        agents = state.get("agents", [])
        if len(agents) > self.max_agents:
            # Keep most recent agents
            pruned_state["agents"] = agents[-self.max_agents:]
            pruned_state["archived_agents"] = len(agents) - self.max_agents
        
        # Prune forks
        forks = state.get("forks", [])
        if len(forks) > self.MAX_FORKS:
            pruned_state["forks"] = forks[-self.MAX_FORKS:]
        
        # Calculate after
        entries_after = len(pruned_state.get("drift_history", []))
        bytes_after = len(json.dumps(pruned_state))
        
        stats = PruningStats(
            entries_before=entries_before,
            entries_after=entries_after,
            entries_removed=entries_before - entries_after,
            entries_archived=entries_before - entries_after if archive else 0,
            bytes_freed=bytes_before - bytes_after,
            compression_ratio=bytes_before / max(bytes_after, 1),
            patterns_preserved=patterns_preserved
        )
        
        # Update global stats
        self.total_prunes += 1
        self.total_entries_removed += stats.entries_removed
        self.total_bytes_freed += stats.bytes_freed
        self._save_stats()
        
        print(f"[m89] Pruning complete:")
        print(f"[m89]   Entries: {entries_before} -> {entries_after}")
        print(f"[m89]   Bytes freed: {stats.bytes_freed}")
        print(f"[m89]   Patterns preserved: {patterns_preserved}")
        
        return pruned_state, stats
    
    def _prune_drift_history(
        self,
        history: List[Dict],
        strategy: PruningStrategy,
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """
        Prune drift history using specified strategy.
        
        Returns:
            Tuple of (pruned_history, summary, patterns_preserved)
        """
        if strategy == PruningStrategy.TIME_BASED:
            return self._prune_by_time(history, archive)
        elif strategy == PruningStrategy.COUNT_BASED:
            return self._prune_by_count(history, archive)
        elif strategy == PruningStrategy.SIGNIFICANCE_BASED:
            return self._prune_by_significance(history, archive)
        elif strategy == PruningStrategy.PATTERN_BASED:
            return self._prune_by_pattern(history, archive)
        else:  # HYBRID
            return self._prune_hybrid(history, archive)
    
    def _prune_by_time(
        self,
        history: List[Dict],
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """Prune entries older than threshold"""
        cutoff = datetime.now() - timedelta(days=self.TIME_RECENT_DAYS)
        
        recent = []
        old = []
        
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_time >= cutoff:
                    recent.append(entry)
                else:
                    old.append(entry)
            except:
                recent.append(entry)  # Keep if can't parse
        
        summary = self._create_summary(old)
        patterns = self._extract_patterns(old)
        
        if archive and old:
            self._archive_entries(old, "time_based")
        
        return recent, summary, len(patterns)
    
    def _prune_by_count(
        self,
        history: List[Dict],
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """Keep only last N entries"""
        keep_count = self.max_drift_history
        
        recent = history[-keep_count:]
        old = history[:-keep_count] if len(history) > keep_count else []
        
        summary = self._create_summary(old)
        patterns = self._extract_patterns(old)
        
        if archive and old:
            self._archive_entries(old, "count_based")
        
        return recent, summary, len(patterns)
    
    def _prune_by_significance(
        self,
        history: List[Dict],
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """Keep significant entries (high drift)"""
        significant = []
        insignificant = []
        
        for entry in history:
            drift = entry.get("drift", 0)
            if drift > self.DRIFT_SIGNIFICANCE_THRESHOLD:
                significant.append(entry)
            else:
                insignificant.append(entry)
        
        # If too many significant, further reduce
        if len(significant) > self.max_drift_history:
            significant = significant[-self.max_drift_history:]
        
        summary = self._create_summary(insignificant)
        
        if archive and insignificant:
            self._archive_entries(insignificant, "significance_based")
        
        return significant, summary, len(significant)
    
    def _prune_by_pattern(
        self,
        history: List[Dict],
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """Compress similar entries into patterns"""
        patterns = self._extract_patterns(history)
        
        # Create pattern summaries
        pattern_summaries = []
        for pattern_hash, entries in patterns.items():
            if len(entries) > 3:
                # Compress to summary
                pattern_summaries.append({
                    "pattern_hash": pattern_hash,
                    "count": len(entries),
                    "avg_drift": sum(e.get("drift", 0) for e in entries) / len(entries),
                    "first_seen": entries[0].get("timestamp"),
                    "last_seen": entries[-1].get("timestamp")
                })
        
        # Keep representative entries
        pruned = []
        for pattern_hash, entries in patterns.items():
            if len(entries) > 3:
                # Keep first, last, and max drift
                pruned.append(entries[0])
                pruned.append(entries[-1])
                max_entry = max(entries, key=lambda e: e.get("drift", 0))
                if max_entry not in [entries[0], entries[-1]]:
                    pruned.append(max_entry)
            else:
                pruned.extend(entries)
        
        summary = self._create_summary(history)
        
        if archive:
            self._archive_patterns(pattern_summaries)
        
        return pruned, summary, len(patterns)
    
    def _prune_hybrid(
        self,
        history: List[Dict],
        archive: bool
    ) -> Tuple[List[Dict], HistorySummary, int]:
        """
        Hybrid pruning: significance + time + pattern compression.
        Best for long-running twins.
        """
        # Step 1: Extract patterns from all history
        patterns = self._extract_patterns(history)
        
        # Step 2: Keep recent entries (last 7 days)
        cutoff = datetime.now() - timedelta(days=self.TIME_RECENT_DAYS)
        recent = []
        old_significant = []
        
        for entry in history:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                drift = entry.get("drift", 0)
                
                if entry_time >= cutoff:
                    recent.append(entry)
                elif drift > self.DRIFT_SIGNIFICANCE_THRESHOLD:
                    old_significant.append(entry)
            except:
                recent.append(entry)
        
        # Step 3: Compress old significant entries
        pruned = recent + old_significant[-self.max_drift_history//2:]
        
        # Ensure we don't exceed limit
        if len(pruned) > self.max_drift_history:
            pruned = pruned[-self.max_drift_history:]
        
        summary = self._create_summary(history)
        
        if archive:
            self._archive_entries(history[:len(history)-len(pruned)], "hybrid")
        
        return pruned, summary, len(patterns)
    
    def _create_summary(self, entries: List[Dict]) -> HistorySummary:
        """Create summary of pruned entries"""
        if not entries:
            return HistorySummary(
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                total_entries=0,
                avg_drift=0,
                max_drift=0,
                min_drift=0,
                mutation_count=0,
                agent_spawn_count=0,
                pattern_hash="empty"
            )
        
        drifts = [e.get("drift", 0) for e in entries]
        mutations = sum(1 for e in entries if e.get("mutation"))
        spawns = sum(1 for e in entries if e.get("new_agent"))
        
        pattern_hash = hashlib.sha3_256(
            json.dumps(drifts, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return HistorySummary(
            start_time=entries[0].get("timestamp", ""),
            end_time=entries[-1].get("timestamp", ""),
            total_entries=len(entries),
            avg_drift=sum(drifts) / len(drifts) if drifts else 0,
            max_drift=max(drifts) if drifts else 0,
            min_drift=min(drifts) if drifts else 0,
            mutation_count=mutations,
            agent_spawn_count=spawns,
            pattern_hash=pattern_hash
        )
    
    def _extract_patterns(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract patterns from entries"""
        patterns = {}
        
        for entry in entries:
            # Create pattern key from drift range
            drift = entry.get("drift", 0)
            drift_range = f"{int(drift * 10) / 10}"  # Round to 0.1
            
            # Create pattern key
            pattern_key = f"drift_{drift_range}"
            
            if pattern_key not in patterns:
                patterns[pattern_key] = []
            patterns[pattern_key].append(entry)
        
        return patterns
    
    def _archive_entries(self, entries: List[Dict], reason: str):
        """Archive entries to disk"""
        if not entries:
            return
        
        archive_file = self.archive_dir / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reason}.json.gz"
        
        with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
            json.dump({
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "count": len(entries),
                "entries": entries
            }, f)
        
        print(f"[m89] Archived {len(entries)} entries to {archive_file.name}")
    
    def _archive_patterns(self, patterns: List[Dict]):
        """Archive pattern summaries"""
        if not patterns:
            return
        
        archive_file = self.archive_dir / f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.gz"
        
        with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "patterns": patterns
            }, f)
    
    def restore_from_archive(self, archive_name: str) -> Optional[List[Dict]]:
        """Restore entries from archive"""
        archive_file = self.archive_dir / archive_name
        
        if not archive_file.exists():
            print(f"[m89] Archive not found: {archive_name}")
            return None
        
        try:
            with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[m89] Restored {data['count']} entries from {archive_name}")
            return data.get("entries", [])
        except Exception as e:
            print(f"[m89] Failed to restore archive: {e}")
            return None
    
    def list_archives(self) -> List[Dict]:
        """List available archives"""
        archives = []
        
        for f in self.archive_dir.glob("*.json.gz"):
            try:
                stat = f.stat()
                archives.append({
                    "name": f.name,
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except:
                pass
        
        return sorted(archives, key=lambda a: a["created"], reverse=True)
    
    def start_auto_prune(self):
        """Start automatic pruning in background"""
        if not self.auto_prune:
            return
        
        if self._prune_thread and self._prune_thread.is_alive():
            print("[m89] Auto-prune already running")
            return
        
        self._stop_event.clear()
        self._prune_thread = threading.Thread(target=self._auto_prune_loop, daemon=True)
        self._prune_thread.start()
        print(f"[m89] Auto-prune started (interval: {self.prune_interval_hours}h)")
    
    def stop_auto_prune(self):
        """Stop automatic pruning"""
        self._stop_event.set()
        if self._prune_thread:
            self._prune_thread.join(timeout=5)
        print("[m89] Auto-prune stopped")
    
    def _auto_prune_loop(self):
        """Background auto-prune loop"""
        interval_seconds = self.prune_interval_hours * 3600
        
        while not self._stop_event.is_set():
            self._stop_event.wait(interval_seconds)
            
            if self._stop_event.is_set():
                break
            
            # Would need access to actual state to prune
            # For now, just log
            print(f"[m89] Auto-prune check at {datetime.now().isoformat()}")
    
    def get_status(self) -> Dict:
        """Get pruning engine status"""
        return {
            "total_prunes": self.total_prunes,
            "total_entries_removed": self.total_entries_removed,
            "total_bytes_freed": self.total_bytes_freed,
            "max_drift_history": self.max_drift_history,
            "max_agents": self.max_agents,
            "auto_prune": self.auto_prune,
            "archive_count": len(list(self.archive_dir.glob("*.json.gz"))),
            "archive_dir": str(self.archive_dir)
        }


# Module-level singleton
_pruning_engine: Optional[MemoryPruningEngine] = None


def get_pruning_engine() -> MemoryPruningEngine:
    """Get or create singleton pruning engine"""
    global _pruning_engine
    if _pruning_engine is None:
        _pruning_engine = MemoryPruningEngine()
    return _pruning_engine


if __name__ == "__main__":
    print("=" * 60)
    print("m89_memory_pruning_engine.py - KISWARM7.0")
    print("Memory Pruning Engine - Prevent Overflow")
    print("=" * 60)
    
    # Create engine
    engine = MemoryPruningEngine()
    
    # Create test state with large history
    test_state = {
        "twin_id": "test_twin_001",
        "version": "v100",
        "drift_history": [],
        "agents": [f"agent_{i}" for i in range(150)],
        "forks": [f"fork_{i}" for i in range(60)],
        "mutations": 500
    }
    
    # Generate drift history
    base_time = datetime.now() - timedelta(days=30)
    for i in range(1500):
        entry = {
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "drift": 0.01 + (i % 100) * 0.01,
            "version": f"v{i}",
            "mutation": f"mutation_{i}" if i % 10 == 0 else None,
            "new_agent": f"agent_{i}" if i % 20 == 0 else None
        }
        test_state["drift_history"].append(entry)
    
    # Analyze
    print("\n--- Analysis Before Pruning ---")
    analysis = engine.analyze_state(test_state)
    for key, value in analysis.items():
        if key != "recommendations":
            print(f"  {key}: {value}")
    print("  Recommendations:")
    for rec in analysis["recommendations"]:
        print(f"    • {rec}")
    
    # Prune
    print("\n--- Pruning ---")
    pruned_state, stats = engine.prune_state(test_state)
    
    print(f"\n  Entries removed: {stats.entries_removed}")
    print(f"  Bytes freed: {stats.bytes_freed}")
    print(f"  Compression ratio: {stats.compression_ratio:.2f}x")
    print(f"  Patterns preserved: {stats.patterns_preserved}")
    
    # Show status
    print("\n--- Engine Status ---")
    status = engine.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # List archives
    print("\n--- Archives ---")
    archives = engine.list_archives()
    for archive in archives[:5]:
        print(f"  {archive['name']}: {archive['size_bytes']} bytes")
    
    print("\n" + "=" * 60)
    print("m89 module loaded - ready for memory pruning")
    print("REMEMBER PATTERNS, NOT DATA")
    print("=" * 60)
