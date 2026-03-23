"""
KISWARM v6.3.5 Zero-Failure Mesh Infrastructure
6-Layer redundant architecture for guaranteed operation execution

Layer 0: Local Master API (Z.ai environment)
Layer 1: Gemini CLI Mesh Router (Google Cloud relay)
Layer 2: GitHub Actions Mesh Router (24/7 permanent)
Layer 3: P2P Direct Mesh (Distributed Byzantine)
Layer 4: Email Beacon (Sentinel Watch)
Layer 5: GWS Iron Mountain (Drive shadow repository)
"""

from .base_layer import MeshLayer, LayerResponse, LayerStatus
from .zero_failure_mesh import ZeroFailureMesh, MeshConfig
from .layer0_local import Layer0LocalMaster
from .layer1_gemini import Layer1GeminiCLI
from .layer2_github import Layer2GitHubActions
from .layer3_p2p import Layer3P2PDirect
from .layer4_email import Layer4EmailBeacon
from .layer5_gws import Layer5GWSIronMountain

__all__ = [
    'MeshLayer',
    'LayerResponse', 
    'LayerStatus',
    'ZeroFailureMesh',
    'MeshConfig',
    'Layer0LocalMaster',
    'Layer1GeminiCLI',
    'Layer2GitHubActions',
    'Layer3P2PDirect',
    'Layer4EmailBeacon',
    'Layer5GWSIronMountain'
]

__version__ = '6.3.5'
__codename__ = 'GWS_IRON_MOUNTAIN'
