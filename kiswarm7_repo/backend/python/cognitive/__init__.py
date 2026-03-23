"""
KISWARM Cognitive Memory Module - MuninnDB Adapter
Implements Ebbinghaus Forgetting Curve and Hebbian Learning

Part of KISWARM v6.3.5 "GWS_IRON_MOUNTAIN"
"""

from .muninn_adapter import MuninnDBAdapter, MemoryEntry, MemoryType

__all__ = ['MuninnDBAdapter', 'MemoryEntry', 'MemoryType']

__version__ = '6.3.5'
