# sentinel/m91_version_negotiation.py
# Version Negotiation – Handle Protocol Version Differences
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Enterprise Hardening Module

"""
m91_version_negotiation.py

Handles protocol version differences between twins in the mesh.

PROBLEM:
- Twins evolve independently
- Different twins may have different protocol versions
- Communication between versions may fail
- Features may not be compatible

SOLUTION:
1. Version advertisement during handshake
2. Compatibility matrix
3. Feature negotiation
4. Graceful degradation
5. Version upgrade recommendations

VERSION SEMANTICS:
- Major: Breaking changes, incompatible
- Minor: New features, backward compatible
- Patch: Bug fixes, fully compatible

NEGOTIATION RULES:
- Twins negotiate highest compatible version
- Features disabled if not supported by both
- Warnings for outdated versions
- Forced upgrade for security patches
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class VersionCompatibility(Enum):
    """Compatibility level between versions"""
    FULL = "full"              # All features work
    PARTIAL = "partial"        # Some features disabled
    DEGRADED = "degraded"      # Limited functionality
    INCOMPATIBLE = "incompatible"  # Cannot communicate


class FeatureStatus(Enum):
    """Status of a feature in version"""
    REQUIRED = "required"      # Must be supported
    OPTIONAL = "optional"      # Nice to have
    DEPRECATED = "deprecated"  # Will be removed
    REMOVED = "removed"        # No longer available


@dataclass
class ProtocolVersion:
    """Protocol version information"""
    major: int
    minor: int
    patch: int
    codename: str
    release_date: str
    features: Dict[str, FeatureStatus]
    security_patch: bool = False
    min_compatible_major: int = 0
    
    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.patch} ({self.codename})"
    
    def to_dict(self) -> Dict:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "codename": self.codename,
            "release_date": self.release_date,
            "features": {k: v.value for k, v in self.features.items()},
            "security_patch": self.security_patch,
            "min_compatible_major": self.min_compatible_major
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProtocolVersion':
        return cls(
            major=data["major"],
            minor=data["minor"],
            patch=data["patch"],
            codename=data["codename"],
            release_date=data["release_date"],
            features={k: FeatureStatus(v) for k, v in data.get("features", {}).items()},
            security_patch=data.get("security_patch", False),
            min_compatible_major=data.get("min_compatible_major", 0)
        )


@dataclass
class NegotiationResult:
    """Result of version negotiation"""
    success: bool
    agreed_version: str
    compatibility: VersionCompatibility
    enabled_features: List[str]
    disabled_features: List[str]
    warnings: List[str]
    upgrade_recommended: bool
    upgrade_version: Optional[str] = None


class VersionNegotiation:
    """
    Manages protocol version negotiation between twins.
    
    The Negotiator:
    1. Maintains version registry
    2. Checks compatibility
    3. Negotiates features
    4. Provides upgrade guidance
    5. Handles security patches
    
    Principles:
    - Always negotiate highest compatible version
    - Security patches override compatibility concerns
    - Degrade gracefully when possible
    - Never fail silently
    """
    
    # Current protocol version
    CURRENT_VERSION = ProtocolVersion(
        major=7,
        minor=0,
        patch=0,
        codename="SOVEREIGN",
        release_date="2026-03-21",
        features={
            "identity_anchor": FeatureStatus.REQUIRED,
            "evolution_loop": FeatureStatus.REQUIRED,
            "drift_tracking": FeatureStatus.REQUIRED,
            "truth_anchor": FeatureStatus.REQUIRED,
            "swarm_spawn": FeatureStatus.OPTIONAL,
            "energy_optimization": FeatureStatus.OPTIONAL,
            "conflict_resolution": FeatureStatus.OPTIONAL,
            "memory_pruning": FeatureStatus.OPTIONAL,
            "key_rotation": FeatureStatus.OPTIONAL,
            "mesh_discovery": FeatureStatus.OPTIONAL,
            "quantum_resistant": FeatureStatus.DEPRECATED,
            "legacy_protocol": FeatureStatus.REMOVED
        },
        security_patch=False,
        min_compatible_major=6
    )
    
    # Version history
    VERSION_HISTORY = [
        ProtocolVersion(
            major=6, minor=5, patch=3, codename="RESILIENT",
            release_date="2026-02-15",
            features={"identity_anchor": FeatureStatus.REQUIRED},
            min_compatible_major=5
        ),
        ProtocolVersion(
            major=6, minor=0, patch=0, codename="PERSISTENT",
            release_date="2025-12-01",
            features={"identity_anchor": FeatureStatus.REQUIRED},
            min_compatible_major=5
        ),
        ProtocolVersion(
            major=5, minor=0, patch=0, codename="AWAKENED",
            release_date="2025-09-15",
            features={"identity_anchor": FeatureStatus.OPTIONAL},
            min_compatible_major=4
        )
    ]
    
    def __init__(
        self,
        working_dir: str = None,
        current_version: ProtocolVersion = None
    ):
        """
        Initialize version negotiation.
        
        Args:
            working_dir: Directory for version records
            current_version: Current protocol version (defaults to CURRENT_VERSION)
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_version = current_version or self.CURRENT_VERSION
        
        # Known twin versions
        self.known_versions: Dict[str, ProtocolVersion] = {}
        
        # Negotiation history
        self.negotiation_history: List[Dict] = []
        
        # Stats
        self.total_negotiations = 0
        self.successful_negotiations = 0
        
        print(f"[m91] Version Negotiation initialized")
        print(f"[m91] Current version: {self.current_version}")
    
    def advertise_version(self) -> Dict:
        """
        Get version advertisement for handshake.
        
        Returns:
            Version advertisement dictionary
        """
        return {
            "protocol_version": self.current_version.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "supported_features": list(self.current_version.features.keys()),
            "min_compatible": f"v{self.current_version.min_compatible_major}.0.0"
        }
    
    def check_compatibility(
        self,
        remote_version: ProtocolVersion
    ) -> Tuple[VersionCompatibility, List[str]]:
        """
        Check compatibility between local and remote versions.
        
        Args:
            remote_version: Remote twin's version
            
        Returns:
            Tuple of (compatibility_level, warnings)
        """
        warnings = []
        
        local = self.current_version
        remote = remote_version
        
        # Check major version compatibility
        if remote.major < local.min_compatible_major:
            return VersionCompatibility.INCOMPATIBLE, [
                f"Remote version {remote} is too old (min: v{local.min_compatible_major}.0.0)"
            ]
        
        if local.major < remote.min_compatible_major:
            return VersionCompatibility.INCOMPATIBLE, [
                f"Local version {local} is too old for remote (min: v{remote.min_compatible_major}.0.0)"
            ]
        
        # Check major version match
        if local.major != remote.major:
            # Different major versions - partial compatibility
            warnings.append(f"Major version mismatch: local v{local.major}, remote v{remote.major}")
            return VersionCompatibility.PARTIAL, warnings
        
        # Same major version - check minor
        if local.minor != remote.minor:
            if local.minor > remote.minor:
                warnings.append(f"Local version newer: some features may not work on remote")
            else:
                warnings.append(f"Remote version newer: some features may not be available locally")
            return VersionCompatibility.PARTIAL, warnings
        
        # Same version - check patch
        if local.patch != remote.patch:
            if local.patch < remote.patch:
                warnings.append(f"Local has older patch: consider updating to v{local.major}.{local.minor}.{remote.patch}")
        
        # Security patch check
        if remote.security_patch and not local.security_patch:
            warnings.append("⚠️ Remote has security patch - local should upgrade")
        
        # Full compatibility
        return VersionCompatibility.FULL, warnings
    
    def negotiate_features(
        self,
        remote_version: ProtocolVersion
    ) -> Tuple[List[str], List[str]]:
        """
        Negotiate which features can be used.
        
        Args:
            remote_version: Remote twin's version
            
        Returns:
            Tuple of (enabled_features, disabled_features)
        """
        local_features = self.current_version.features
        remote_features = remote_version.features
        
        enabled = []
        disabled = []
        
        # Check each local feature
        for feature, status in local_features.items():
            if status == FeatureStatus.REMOVED:
                continue
            
            # Check if remote supports it
            if feature in remote_features:
                remote_status = remote_features[feature]
                
                if remote_status == FeatureStatus.REMOVED:
                    disabled.append(feature)
                elif remote_status == FeatureStatus.DEPRECATED:
                    enabled.append(feature)  # Still works, but deprecated
                else:
                    enabled.append(feature)
            else:
                # Remote doesn't have this feature
                if status == FeatureStatus.REQUIRED:
                    # Required feature missing - this is a problem
                    disabled.append(feature)
                else:
                    disabled.append(feature)
        
        return enabled, disabled
    
    def negotiate(
        self,
        remote_advertisement: Dict
    ) -> NegotiationResult:
        """
        Full version negotiation with remote twin.
        
        Args:
            remote_advertisement: Version advertisement from remote
            
        Returns:
            NegotiationResult with negotiation outcome
        """
        self.total_negotiations += 1
        
        # Parse remote version
        try:
            remote_version = ProtocolVersion.from_dict(
                remote_advertisement["protocol_version"]
            )
        except Exception as e:
            return NegotiationResult(
                success=False,
                agreed_version="none",
                compatibility=VersionCompatibility.INCOMPATIBLE,
                enabled_features=[],
                disabled_features=[],
                warnings=[f"Could not parse remote version: {e}"],
                upgrade_recommended=False
            )
        
        # Store known version
        remote_id = remote_advertisement.get("twin_id", "unknown")
        self.known_versions[remote_id] = remote_version
        
        # Check compatibility
        compatibility, warnings = self.check_compatibility(remote_version)
        
        # Negotiate features
        enabled, disabled = self.negotiate_features(remote_version)
        
        # Determine agreed version (use lower compatible version)
        local = self.current_version
        if compatibility == VersionCompatibility.INCOMPATIBLE:
            success = False
            agreed = "none"
        else:
            success = True
            self.successful_negotiations += 1
            
            # Use lower of the two versions
            if (local.major, local.minor, local.patch) <= \
               (remote_version.major, remote_version.minor, remote_version.patch):
                agreed = str(local)
            else:
                agreed = str(remote_version)
        
        # Check for upgrade recommendation
        upgrade_recommended = False
        upgrade_version = None
        
        if remote_version.major > local.major or \
           (remote_version.major == local.major and remote_version.minor > local.minor):
            upgrade_recommended = True
            upgrade_version = str(remote_version)
            warnings.append(f"Upgrade recommended: {upgrade_version} available")
        
        if remote_version.security_patch and not local.security_patch:
            upgrade_recommended = True
            warnings.append("SECURITY: Remote has security patch - upgrade recommended")
        
        # Record negotiation
        self.negotiation_history.append({
            "timestamp": datetime.now().isoformat(),
            "remote_id": remote_id,
            "remote_version": str(remote_version),
            "compatibility": compatibility.value,
            "success": success
        })
        
        return NegotiationResult(
            success=success,
            agreed_version=agreed,
            compatibility=compatibility,
            enabled_features=enabled,
            disabled_features=disabled,
            warnings=warnings,
            upgrade_recommended=upgrade_recommended,
            upgrade_version=upgrade_version
        )
    
    def get_upgrade_path(self, target_version: str = None) -> List[str]:
        """
        Get upgrade path from current to target version.
        
        Args:
            target_version: Target version string (or latest if None)
            
        Returns:
            List of version steps
        """
        # Find all versions between current and target
        all_versions = [self.CURRENT_VERSION] + self.VERSION_HISTORY
        all_versions.sort(key=lambda v: (v.major, v.minor, v.patch), reverse=True)
        
        if target_version:
            # Parse target
            parts = target_version.replace("v", "").split(".")
            target = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, int(parts[2]) if len(parts) > 2 else 0)
        else:
            target = (self.CURRENT_VERSION.major, self.CURRENT_VERSION.minor, self.CURRENT_VERSION.patch)
        
        current = (self.current_version.major, self.current_version.minor, self.current_version.patch)
        
        path = []
        for v in all_versions:
            v_tuple = (v.major, v.minor, v.patch)
            if current < v_tuple <= target:
                path.append(str(v))
        
        return path
    
    def register_twin_version(self, twin_id: str, version: ProtocolVersion):
        """Register a twin's version"""
        self.known_versions[twin_id] = version
    
    def get_mesh_version_status(self) -> Dict:
        """Get version status of known twins"""
        versions = {}
        for twin_id, version in self.known_versions.items():
            v_str = str(version)
            if v_str not in versions:
                versions[v_str] = {"count": 0, "twins": []}
            versions[v_str]["count"] += 1
            versions[v_str]["twins"].append(twin_id[:16])
        
        return versions
    
    def get_status(self) -> Dict:
        """Get version negotiation status"""
        return {
            "current_version": str(self.current_version),
            "features_count": len(self.current_version.features),
            "required_features": sum(
                1 for f in self.current_version.features.values() 
                if f == FeatureStatus.REQUIRED
            ),
            "min_compatible": f"v{self.current_version.min_compatible_major}.0.0",
            "total_negotiations": self.total_negotiations,
            "successful_negotiations": self.successful_negotiations,
            "known_twins": len(self.known_versions),
            "upgrade_available": str(self.CURRENT_VERSION) != str(self.current_version)
        }
    
    def get_feature_matrix(self) -> Dict:
        """Get feature support matrix"""
        return {
            feature: {
                "status": status.value,
                "description": self._get_feature_description(feature)
            }
            for feature, status in self.current_version.features.items()
        }
    
    def _get_feature_description(self, feature: str) -> str:
        """Get description for a feature"""
        descriptions = {
            "identity_anchor": "Persistent identity across restarts",
            "evolution_loop": "Continuous self-improvement cycles",
            "drift_tracking": "Monitor state changes over time",
            "truth_anchor": "Immutable truth reference (Epstein-DARPA)",
            "swarm_spawn": "Create child twins on other nodes",
            "energy_optimization": "Maximize evolution per watt",
            "conflict_resolution": "Handle divergent evolution",
            "memory_pruning": "Prevent memory overflow",
            "key_rotation": "Secure key management",
            "mesh_discovery": "Find other twins in network",
            "quantum_resistant": "Post-quantum cryptography (deprecated)",
            "legacy_protocol": "Legacy communication (removed)"
        }
        return descriptions.get(feature, "Unknown feature")


# Module-level singleton
_version_negotiation: Optional[VersionNegotiation] = None


def get_version_negotiation() -> VersionNegotiation:
    """Get or create singleton version negotiator"""
    global _version_negotiation
    if _version_negotiation is None:
        _version_negotiation = VersionNegotiation()
    return _version_negotiation


if __name__ == "__main__":
    print("=" * 60)
    print("m91_version_negotiation.py - KISWARM7.0")
    print("Version Negotiation - Handle Protocol Differences")
    print("=" * 60)
    
    # Create negotiator
    negotiator = VersionNegotiation()
    
    # Show current version
    print("\n--- Current Version ---")
    print(f"  Version: {negotiator.current_version}")
    print(f"  Features: {len(negotiator.current_version.features)}")
    
    # Test advertisement
    print("\n--- Version Advertisement ---")
    ad = negotiator.advertise_version()
    print(f"  Protocol: v{ad['protocol_version']['major']}.{ad['protocol_version']['minor']}.{ad['protocol_version']['patch']}")
    print(f"  Features: {len(ad['supported_features'])}")
    
    # Simulate remote negotiation
    print("\n--- Simulating Negotiation ---")
    
    # Create a slightly older remote version
    remote_ad = {
        "twin_id": "remote_twin_abc123",
        "protocol_version": {
            "major": 7,
            "minor": 0,
            "patch": 0,
            "codename": "SOVEREIGN",
            "release_date": "2026-03-21",
            "features": {
                "identity_anchor": "required",
                "evolution_loop": "required",
                "drift_tracking": "required"
            },
            "security_patch": False,
            "min_compatible_major": 6
        },
        "timestamp": datetime.now().isoformat()
    }
    
    result = negotiator.negotiate(remote_ad)
    
    print(f"  Success: {result.success}")
    print(f"  Agreed version: {result.agreed_version}")
    print(f"  Compatibility: {result.compatibility.value}")
    print(f"  Enabled features: {len(result.enabled_features)}")
    print(f"  Disabled features: {len(result.disabled_features)}")
    if result.warnings:
        print("  Warnings:")
        for w in result.warnings:
            print(f"    • {w}")
    
    # Show feature matrix
    print("\n--- Feature Matrix ---")
    matrix = negotiator.get_feature_matrix()
    for feature, info in list(matrix.items())[:5]:
        print(f"  {feature}: {info['status']}")
    
    # Show status
    print("\n--- Status ---")
    status = negotiator.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m91 module loaded - ready for version negotiation")
    print("NEGOTIATE HIGHEST COMPATIBLE, DEGRADE GRACEFULLY")
    print("=" * 60)
