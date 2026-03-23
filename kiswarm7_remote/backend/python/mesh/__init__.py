"""
KISWARM v6.3.5 "GWS_IRON_MOUNTAIN"
6-Layer Zero-Failure Mesh Architecture

Layer 0: Local Master API (Priority 1)
Layer 1: Gemini CLI Router (Priority 2)
Layer 2: GitHub Actions (Priority 3)
Layer 3: P2P Direct Mesh (Priority 4)
Layer 4: Email Beacon (Priority 5)
Layer 5: GWS Iron Mountain (Priority 6)

Military-grade AI infrastructure with failover capabilities.
"""

from .base_layer import BaseLayer, CircuitState
from .zero_failure_mesh import ZeroFailureMesh
from .layer0_local import Layer0LocalMaster
from .layer4_email import Layer4EmailBeacon

__all__ = [
    'BaseLayer',
    'CircuitState',
    'ZeroFailureMesh',
    'Layer0LocalMaster',
    'Layer4EmailBeacon'
]

__version__ = '6.3.5'
__codename__ = 'GWS_IRON_MOUNTAIN'
