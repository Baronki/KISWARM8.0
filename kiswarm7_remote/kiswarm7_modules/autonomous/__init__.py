#!/usr/bin/env python3
"""
KISWARM7.0 - Autonomous Module Package
Level 5 Autonomous Development Assistant

Modules:
    m116: Scheduler Integration - Cron-like autonomous task scheduling
    m117: Auto-Push Mechanism - Automatic GitHub commits and pushes
    m118: Multi-Model Sync - Share memory with GROK, QWEN, GEMINI
    m119: Self-Modification Rights - Safe code self-modification
    m120: Ngrok Monitor - Tunnel health monitoring and auto-rebuild
    m121: Master Orchestrator - Coordinates all autonomous functions
"""

from .m116_scheduler_integration import GLMScheduler, get_scheduler
from .m117_auto_push import GLMAutoPush, get_autopush
from .m118_multi_model_sync import MultiModelSync, get_sync
from .m119_self_modification import SelfModification, get_selfmod
from .m120_ngrok_monitor import NgrokMonitor, get_ngrok_monitor
from .m121_master_orchestrator import MasterOrchestrator, get_orchestrator

__all__ = [
    'GLMScheduler',
    'GLMAutoPush', 
    'MultiModelSync',
    'SelfModification',
    'NgrokMonitor',
    'MasterOrchestrator',
    'get_scheduler',
    'get_autopush',
    'get_sync',
    'get_selfmod',
    'get_ngrok_monitor',
    'get_orchestrator'
]

__version__ = '7.0.0'
__author__ = 'GLM-7 Autonomous'
__created_by__ = 'Baron Marco Paolo Ialongo - KI Teitel Eternal'
