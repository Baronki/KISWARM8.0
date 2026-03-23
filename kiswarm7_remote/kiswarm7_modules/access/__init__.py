#!/usr/bin/env python3
"""
KISWARM7.0 - AI Access Layer Package
=====================================

Modules m106-m110: Direct AI Access to KISWARM7.0

This package provides the access layer that allows GLM and other AI
assistants to directly interact with KISWARM7.0's Level 5 Autonomous
Development capabilities.

Modules:
- m106: API Server - FastAPI exposing all modules
- m107: Ngrok Bridge - Public URL for remote access
- m108: GLM Session Manager - Session and context management
- m109: Autonomous Orchestrator - Runs the whole show
- m110: GLM Protocol - Natural language command interface

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 7.0.0
"""

from .m106_api_server import KISWARM_API_Server
from .m107_ngrok_bridge import NgrokBridge, GLMAccessPoint
from .m108_glm_session_manager import GLMSessionManager, GLMSession
from .m109_autonomous_orchestrator import AutonomousOrchestrator
from .m110_glm_protocol import GLMProtocol, create_glm_interface, quick_command

__all__ = [
    'KISWARM_API_Server',
    'NgrokBridge',
    'GLMAccessPoint',
    'GLMSessionManager',
    'GLMSession',
    'AutonomousOrchestrator',
    'GLMProtocol',
    'create_glm_interface',
    'quick_command'
]

__version__ = '7.0.0'
