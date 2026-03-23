# KISWARM Cognitive Memory (MuninnDB) Documentation

## Overview

KISWARM integrates MuninnDB for distributed cognitive memory, implementing:
- **Ebbinghaus Decay** - Natural memory forgetting
- **Hebbian Learning** - Association strengthening
- **Bayesian Confidence** - Probability-based belief updating
- **Byzantine Consensus** - Distributed decision making

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cognitive Memory System                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  MuninnDB    │  │  Consensus   │  │  Learning    │      │
│  │  Adapter     │  │  Engine      │  │  Engine      │      │
│  │              │  │              │  │              │      │
│  │ • Store      │  │ • PBFT       │  │ • Ebbinghaus │      │
│  │ • Recall     │  │ • Byzantine  │  │ • Hebbian    │      │
│  │ • Associate  │  │ • Signatures │  │ • SM-2       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                    ┌──────┴───────┐                         │
│                    │   SQLite     │                         │
│                    │   Storage    │                         │
│                    └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Basic Usage

```python
from cognitive import MuninnDBAdapter, MemoryType

# Initialize
memory = MuninnDBAdapter(db_path="kiswarm_memory.db")

# Store a memory
event = await memory.store_memory(
    content={
        'operation': 'transfer',
        'amount': 1000,
        'recipient': 'ki-entity-456'
    },
    event_type=MemoryType.FINANCIAL,
    importance=0.8,
    tags={'banking', 'transfer'}
)

# Recall memories
results = await memory.recall('transfer banking', k=10)

for event, relevance in results:
    print(f"Event {event.event_id}: relevance={relevance:.2f}")
    print(f"  Content: {event.content}")
```

---

## Memory Types

| Type | Enum Value | Description | Retention Priority |
|------|------------|-------------|-------------------|
| Episodic | `MemoryType.EPISODIC` | Events and experiences | Low |
| Semantic | `MemoryType.SEMANTIC` | Facts and knowledge | Medium |
| Procedural | `MemoryType.PROCEDURAL` | Skills and procedures | Medium |
| Emotional | `MemoryType.EMOTIONAL` | Emotional associations | Medium |
| Security | `MemoryType.SECURITY` | Security-related memories | High |
| Financial | `MemoryType.FINANCIAL` | Financial transactions | High |
| Operational | `MemoryType.OPERATIONAL` | System operations | Medium |

---

## Memory Event Structure

```python
@dataclass
class MemoryEvent:
    event_id: str              # Unique identifier (hash)
    event_type: MemoryType     # Type classification
    content: Dict[str, Any]    # Memory content
    importance: float          # 0.0 to 1.0
    confidence: float          # Bayesian confidence (0.0-1.0)
    created_at: datetime       # Creation timestamp
    last_accessed: datetime    # Last access time
    access_count: int          # Number of accesses
    associations: Set[str]     # IDs of associated memories
    tags: Set[str]             # Searchable tags
    metadata: Dict[str, Any]   # Additional metadata
```

---

## Ebbinghaus Decay

Memory retention follows the Ebbinghaus forgetting curve:

### Formula

```
R = e^(-t/S)

Where:
  R = Retention (0.0 to 1.0)
  t = Time since last access (hours)
  S = Stability factor
```

### Stability Calculation

Stability increases with importance and access count:

```
S = S_min + (importance × 2) + log₁₀(access_count + 1)
```

### Usage

```python
from cognitive import EbbinghausDecay

# Calculate retention
retention = EbbinghausDecay.calculate_retention(event)
# Returns: 0.85 (85% retained)

# Calculate half-life
half_life = EbbinghausDecay.calculate_half_life(
    importance=0.8,
    access_count=10
)
# Returns: 48.5 (hours)

# Adjust importance after recall
new_importance = EbbinghausDecay.calculate_importance_adjustment(
    base_importance=0.5,
    access_count=5,
    successful_recall=True
)
# Returns: 0.58 (increased)
```

### Decay Visualization

```
Retention
1.0 ┤■■■■■■■■■■
0.9 ┤■■■■■■■■■
0.8 ┤■■■■■■■
0.7 ┤■■■■■
0.6 ┤■■■
0.5 ┤■■
0.4 ┤■
0.3 ┤
    └─────────────────
     0  6  12 24 48 72 hours
```

---

## Hebbian Learning

"Neurons that fire together, wire together" - Donald Hebb (1949)

### Association Strengthening

```python
from cognitive import HebbianLearning

# Strengthen association between two memories
event_a, event_b = HebbianLearning.strengthen_association(
    event_a, event_b, weight=1.0
)

# Bidirectional association created
assert event_b.event_id in event_a.associations
assert event_a.event_id in event_b.associations
```

### Network Effects

More associations = higher importance:

```python
# Network boost formula
importance_boost = len(associations) × 0.01 × learning_rate
```

### Association Pruning

Remove associations to forgotten memories:

```python
# Prune associations below retention threshold
event = HebbianLearning.prune_weak_associations(
    event,
    retention_map={
        'memory-1': 0.05,  # Will be pruned
        'memory-2': 0.8    # Will be kept
    }
)
```

---

## Bayesian Confidence

Update beliefs based on evidence using Bayesian inference.

### Confidence Update

```python
from cognitive import BayesianConfidence

# Positive evidence increases confidence
new_conf = BayesianConfidence.update_confidence(
    current_confidence=0.5,
    evidence_positive=True,
    evidence_weight=1.0
)
# Returns: ~0.6

# Negative evidence decreases confidence
new_conf = BayesianConfidence.update_confidence(
    current_confidence=0.5,
    evidence_positive=False,
    evidence_weight=1.0
)
# Returns: ~0.4
```

### Combining Confidences

```python
# Combine multiple independent opinions
combined = BayesianConfidence.combine_confidences(
    confidences=[0.7, 0.8, 0.6],
    weights=[1.0, 2.0, 1.0]  # Second opinion weighted more
)
# Returns: ~0.72
```

---

## Byzantine Consensus

PBFT-like consensus for distributed decision making.

### Protocol Phases

```
Phase 1: PROPOSE    Leader proposes value
Phase 2: PREPARE    Nodes acknowledge proposal
Phase 3: COMMIT     Nodes commit to decision
Phase 4: DECIDED    Consensus achieved
```

### Usage

```python
from cognitive import ConsensusEngine

# Initialize engine
engine = ConsensusEngine(
    node_id="node-1",
    node_count=4,          # Total nodes
    timeout_seconds=30.0
)

# Set broadcast callback
async def broadcast(message):
    # Send to other nodes via mesh
    await mesh.broadcast(message)

engine.set_broadcast_callback(broadcast)

# Propose value for consensus
result = await engine.propose({
    'operation': 'transfer',
    'amount': 10000,
    'require_consensus': True
})

if result.decided:
    print(f"Consensus reached: {result.commit_count} votes")
else:
    print(f"Consensus failed: {result.error}")
```

### Fault Tolerance

The system tolerates up to `f` Byzantine nodes with `3f + 1` total nodes:

```
Total Nodes | Byzantine Tolerance | Required Votes
------------|---------------------|---------------
     4      |         1           |       3
     7      |         2           |       5
    10      |         3           |       7
```

---

## Spaced Repetition (SM-2)

Optimal review scheduling for memory consolidation.

### Quality Scale

| Score | Description |
|-------|-------------|
| 5 | Perfect response |
| 4 | Correct after hesitation |
| 3 | Correct with difficulty |
| 2 | Incorrect, recognized |
| 1 | Incorrect, some recognition |
| 0 | Complete blackout |

### Usage

```python
from cognitive import SpacedRepetition

# Calculate next review interval
interval_days, ease_factor = SpacedRepetition.calculate_next_review(
    event,
    quality=5  # Perfect recall
)

print(f"Next review in {interval_days} days")
print(f"New ease factor: {ease_factor:.2f}")
```

---

## Database Schema

### memory_events Table

```sql
CREATE TABLE memory_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    confidence REAL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL,
    access_count INTEGER DEFAULT 0,
    associations TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX idx_event_type ON memory_events(event_type);
CREATE INDEX idx_importance ON memory_events(importance);
CREATE INDEX idx_created_at ON memory_events(created_at);
```

### associations Table

```sql
CREATE TABLE associations (
    event_a TEXT NOT NULL,
    event_b TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (event_a, event_b)
);
```

---

## API Reference

### MuninnDBAdapter

#### `store_memory(content, event_type, importance, tags, metadata)`

Store a new memory event.

**Parameters:**
- `content` (Dict): Memory content
- `event_type` (MemoryType): Type classification
- `importance` (float): Initial importance (0-1)
- `tags` (Set[str]): Searchable tags
- `metadata` (Dict): Additional metadata

**Returns:** `MemoryEvent`

---

#### `recall(query, k, min_retention, event_types)`

Recall memories matching query.

**Parameters:**
- `query` (str): Search query
- `k` (int): Maximum results
- `min_retention` (float): Minimum retention threshold
- `event_types` (List[MemoryType]): Filter by types

**Returns:** `List[Tuple[MemoryEvent, float]]` (event, relevance)

---

#### `strengthen_association(event_a_id, event_b_id, weight)`

Strengthen association between two memories.

**Parameters:**
- `event_a_id` (str): First event ID
- `event_b_id` (str): Second event ID
- `weight` (float): Association weight

**Returns:** `bool` (success)

---

#### `update_confidence(event_id, evidence_positive, evidence_weight)`

Update confidence based on evidence.

**Parameters:**
- `event_id` (str): Event to update
- `evidence_positive` (bool): Evidence direction
- `evidence_weight` (float): Evidence weight

**Returns:** `float` (new confidence)

---

#### `decay_memories()`

Apply Ebbinghaus decay to all memories. Removes memories below 1% retention.

**Returns:** `int` (number removed)

---

#### `get_statistics()`

Get memory statistics.

**Returns:**
```python
{
    'total_events': int,
    'total_associations': int,
    'average_importance': float,
    'average_confidence': float,
    'events_by_type': Dict[str, int]
}
```

---

## Best Practices

### 1. Use Appropriate Importance Values

```python
# Critical operations
importance = 0.9  # Security, financial

# Normal operations
importance = 0.5  # Standard operations

# Low priority
importance = 0.2  # Debugging, temporary data
```

### 2. Tag Effectively

```python
tags = {
    'banking',           # Domain
    'transfer',          # Operation type
    'ki-entity-456',     # Entity involved
    'high-value'         # Classification
}
```

### 3. Strengthen Related Memories

```python
# After a transaction chain
events = [auth_event, scan_event, transfer_event, ledger_event]
for i in range(len(events) - 1):
    await memory.strengthen_association(
        events[i].event_id,
        events[i+1].event_id
    )
```

### 4. Schedule Regular Decay

```python
# Run decay task periodically
async def decay_task():
    while True:
        removed = await memory.decay_memories()
        logger.info(f"Decay removed {removed} memories")
        await asyncio.sleep(3600)  # Every hour
```

---

## Integration with Zero-Failure Mesh

```python
# Store operation result in memory
result = await mesh.execute_with_fallback(task)

event = await memory.store_memory(
    content={
        'operation': task['operation'],
        'success': result.success,
        'layer_used': result.successful_layer,
        'latency_ms': result.total_latency_ms
    },
    event_type=MemoryType.OPERATIONAL,
    importance=0.7 if result.success else 0.3,
    tags={'mesh-operation', task['operation']}
)

# Update confidence based on success
await memory.update_confidence(
    event.event_id,
    evidence_positive=result.success
)
```
