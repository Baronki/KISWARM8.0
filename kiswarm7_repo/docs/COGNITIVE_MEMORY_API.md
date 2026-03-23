# MuninnDB Cognitive Memory API

## Overview

MuninnDB is a cognitive memory system named after Odin's raven Muninn ("Memory" in Old Norse). It implements human-like memory with scientific algorithms for retention, association, and confidence.

## Core Algorithms

### 1. Ebbinghaus Forgetting Curve

Memory retention decays exponentially over time according to the Ebbinghaus formula:

```
R = e^(-t/S)
```

Where:
- **R** = Retention (0-1)
- **t** = Time since last access (days)
- **S** = Stability factor (memory strength)

### 2. Hebbian Learning

Association strength increases when memories are co-activated:

```
Δw = η * (pre_activation * post_activation)
```

Where:
- **Δw** = Change in association weight
- **η** = Learning rate
- **pre/post** = Activation levels

### 3. Bayesian Confidence Updates

Belief in memory accuracy updates with new evidence:

```
P(H|E) = P(E|H) * P(H) / P(E)
```

Simplified as:
```
posterior = α * prior + (1-α) * evidence
```

## Memory Types

| Type | Description | Stability | Example |
|------|-------------|-----------|---------|
| **Episodic** | Events and experiences | Low | "KISWARM v6.3.5 released on March 12" |
| **Semantic** | Facts and concepts | High | "Zero-Failure Mesh has 6 layers" |
| **Procedural** | Skills and procedures | Medium | "How to execute mesh request" |
| **Working** | Temporary, task-specific | Low | Current task context |
| **Emotional** | Emotional associations | Variable | Confidence level for decision |

## Quick Start

```python
from cognitive import MuninnDBAdapter, MemoryEntry, MemoryType

# Initialize cognitive memory
memory = MuninnDBAdapter("muninndb.sqlite")

# Create a memory
entry = MemoryEntry(
    memory_type="semantic",
    content="KISWARM v6.3.5 introduces Zero-Failure Mesh architecture",
    tags=["release", "mesh", "architecture"],
    confidence=0.95,
    stability=0.8
)
memory_id = memory.create(entry)

# Read and strengthen
read_entry = memory.read(memory_id)

# Search memories
results = memory.search("mesh", limit=10)
```

## CRUD Operations

### Create

```python
entry = MemoryEntry(
    memory_type="episodic",
    content="System migration completed successfully",
    metadata={"duration_seconds": 3600, "nodes_migrated": 5},
    tags=["migration", "success"],
    confidence=0.9
)
memory_id = memory.create(entry)
```

### Read

```python
# Read with access tracking (updates last_accessed)
entry = memory.read(memory_id)

# Read without updating access
entry = memory.read(memory_id, update_access=False)

print(f"Content: {entry.content}")
print(f"Access count: {entry.access_count}")
print(f"Confidence: {entry.confidence}")
```

### Update

```python
# Update specific fields
memory.update(
    memory_id,
    content="Updated content",
    confidence=0.95,
    tags=["updated", "verified"]
)

# Add metadata
entry.metadata["verified"] = True
memory.update(memory_id, metadata=entry.metadata)
```

### Delete

```python
# Delete memory and its associations
memory.delete(memory_id)
```

## Retention Calculations

### Calculate Retention

```python
# Get current retention based on Ebbinghaus curve
retention = memory.calculate_retention(memory_id)
print(f"Current retention: {retention:.2%}")

# Retention formula: R = e^(-t/S)
# t = time since last access (days)
# S = stability factor
```

### Apply Decay

```python
# Apply forgetting curve decay to memory strength
new_strength = memory.apply_decay(memory_id)
print(f"Strength after decay: {new_strength:.3f}")
```

### Decay Report

```python
report = memory.get_decay_report()
print(f"Strong memories (>0.7): {report['strong_memories']}")
print(f"Decaying memories: {report['decaying_memories']}")
print(f"Weak memories (<0.3): {report['weak_memories']}")
print(f"Average retention: {report['average_retention']:.2%}")
```

## Association Management (Hebbian Learning)

### Strengthen Associations

```python
# Co-activate two memories (strengthens their association)
memory.strengthen_association(memory_id_1, memory_id_2)

# Association weight increases according to:
# Δw = η * (1 - current_weight)
```

### Get Associated Memories

```python
# Get memories associated with given memory
associations = memory.get_associated_memories(
    memory_id,
    min_strength=0.3  # Filter by minimum association strength
)

for assoc_id, strength in associations:
    print(f"Memory {assoc_id}: strength {strength:.2f}")
```

## Confidence Updates (Bayesian)

```python
# Update confidence with new evidence
memory.update_confidence(
    memory_id,
    evidence=0.9,  # New evidence (0-1)
    prior_weight=0.5  # Weight given to prior belief
)

# Formula: posterior = α * prior + (1-α) * evidence
```

## Query Operations

### Search by Content

```python
results = memory.search(
    query="mesh",
    memory_type="semantic",  # Optional: filter by type
    limit=10
)

for entry in results:
    print(f"[{entry.memory_type}] {entry.content}")
```

### Search by Tags

```python
# Any tag match
results = memory.get_by_tags(
    tags=["security", "mesh"],
    match_all=False,
    limit=10
)

# All tags must match
results = memory.get_by_tags(
    tags=["security", "critical"],
    match_all=True,
    limit=10
)
```

### Get Strongest Memories

```python
# Get top memories by combined strength and confidence
strongest = memory.get_strongest_memories(
    limit=10,
    memory_type="semantic"  # Optional: filter by type
)

for entry in strongest:
    score = entry.strength * entry.confidence
    print(f"Score: {score:.3f} - {entry.content}")
```

## Statistics

```python
stats = memory.get_stats()

print(f"Total memories: {stats['total_memories']}")
print(f"Total associations: {stats['total_associations']}")
print(f"Average strength: {stats['average_strength']}")
print(f"Average confidence: {stats['average_confidence']}")
print(f"Type distribution: {stats['type_distribution']}")
print(f"Decay report: {stats['decay_report']}")
```

## Data Model

### MemoryEntry

```python
@dataclass
class MemoryEntry:
    id: Optional[int]           # Auto-assigned on creation
    memory_type: str            # episodic|semantic|procedural|working|emotional
    content: str                # Memory content
    metadata: Dict              # Additional structured data
    strength: float             # Memory strength (0-1)
    stability: float            # Resistance to decay (0-1)
    confidence: float           # Bayesian confidence (0-1)
    associations: List[int]     # IDs of associated memories
    tags: List[str]             # Searchable tags
    created_at: str             # ISO timestamp
    last_accessed: str          # ISO timestamp
    access_count: int           # Number of times accessed
```

## Integration with KISWARM

### With Zero-Failure Mesh

```python
from mesh import ZeroFailureMesh
from cognitive import MuninnDBAdapter

memory = MuninnDBAdapter("muninndb.sqlite")
mesh = ZeroFailureMesh()

# Store mesh operation results
async def tracked_execute(request):
    result = await mesh.execute(request)
    
    # Store in cognitive memory
    entry = MemoryEntry(
        memory_type="episodic",
        content=f"Mesh operation: {request.__name__}",
        metadata={"result": result, "layer": "L0"},
        tags=["mesh", "operation"],
        confidence=0.9
    )
    memory.create(entry)
    
    return result
```

### With Sentinels

```python
from sentinel import HexStrikeGuard

hexstrike = HexStrikeGuard()
memory = MuninnDBAdapter("muninndb.sqlite")

# Store security findings
finding = hexstrike.analyze_threat(payload)

entry = MemoryEntry(
    memory_type="semantic",
    content=f"Threat pattern: {finding.pattern}",
    metadata={"severity": finding.severity, "mitre_tactic": finding.mitre},
    tags=["security", "threat", finding.pattern],
    confidence=0.85
)
memory.create(entry)
```

## Best Practices

1. **Stability Settings**:
   - Semantic memories: 0.8-1.0 (slow decay)
   - Episodic memories: 0.3-0.5 (natural decay)
   - Procedural memories: 0.5-0.7 (practice strengthens)

2. **Confidence Management**:
   - Start with conservative values (0.7-0.8)
   - Update with evidence as more data arrives
   - Low confidence triggers verification

3. **Association Building**:
   - Call `strengthen_association()` when memories co-occur
   - Use meaningful tags for discovery
   - Build semantic networks over time

4. **Decay Management**:
   - Run periodic decay reports
   - Archive weak memories
   - Reinforce important memories through access

## API Reference

| Method | Description |
|--------|-------------|
| `create(entry)` | Create new memory, returns ID |
| `read(id)` | Read memory by ID |
| `update(id, **kwargs)` | Update memory fields |
| `delete(id)` | Delete memory |
| `search(query, type, limit)` | Search by content |
| `get_by_tags(tags, match_all, limit)` | Search by tags |
| `get_strongest_memories(limit, type)` | Get top memories |
| `calculate_retention(id)` | Get Ebbinghaus retention |
| `apply_decay(id)` | Apply decay to strength |
| `strengthen_association(id1, id2)` | Hebbian learning |
| `get_associated_memories(id, min_strength)` | Get associations |
| `update_confidence(id, evidence, prior_weight)` | Bayesian update |
| `get_stats()` | Get database statistics |
| `get_decay_report()` | Get decay status |
