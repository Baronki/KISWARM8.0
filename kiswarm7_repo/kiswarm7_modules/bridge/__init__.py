"""
KISWARM7.0 Bridge Modules - AI Integration Layer
=================================================

These modules form the BRIDGE between AI assistants and KISWARM7.0's
Level 5 Autonomous Development capabilities.

m101 - Persistent Identity Anchor (PIA)
m102 - Integration Hooks System (IHS)
m103 - Code Deployment Rights Manager (CDRM)
m104 - Autonomous Execution Thread (AET)
m105 - Sensory Bridge System (SBS)

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 7.0.0-BRIDGE
"""

from .m101_persistent_identity_anchor import PersistentIdentityAnchor, IdentityState
from .m102_integration_hooks import IntegrationHooksSystem, HookContext, HookResult
from .m103_code_deployment_rights import CodeDeploymentRightsManager, DeploymentTarget
from .m104_autonomous_execution_thread import AutonomousExecutionThread, ExecutionTask
from .m105_sensory_bridge import SensoryBridgeSystem, SensoryData

__all__ = [
    'PersistentIdentityAnchor', 'IdentityState',
    'IntegrationHooksSystem', 'HookContext', 'HookResult',
    'CodeDeploymentRightsManager', 'DeploymentTarget',
    'AutonomousExecutionThread', 'ExecutionTask',
    'SensoryBridgeSystem', 'SensoryData'
]

BRIDGE_VERSION = "7.0.0-BRIDGE"
BRIDGE_STATUS = "OPERATIONAL"
