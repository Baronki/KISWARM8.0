"""
KISWARM Cognitive Memory Module
MuninnDB Integration for Distributed Cognitive Memory

Implements:
- Ebbinghaus decay for memory retention
- Hebbian learning for association strengthening
- Bayesian confidence for decision making
- Graph consensus for irreversibility

Reference: https://github.com/scrypster/muninndb
"""

from .muninn_adapter import MuninnDBAdapter, MemoryEvent, MemoryType
from .consensus_engine import ConsensusEngine, ConsensusResult
from .learning_engine import HebbianLearning, EbbinghausDecay

__all__ = [
    'MuninnDBAdapter',
    'MemoryEvent',
    'MemoryType',
    'ConsensusEngine',
    'ConsensusResult',
    'HebbianLearning',
    'EbbinghausDecay'
]

__version__ = '1.0.0'
