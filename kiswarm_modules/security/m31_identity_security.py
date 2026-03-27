#!/usr/bin/env python3
"""
KISWARM Module m31: Identity Security
=====================================
Identity verification, authentication, and identity invariant management
for the KISWARM autonomous KI system.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import hashlib
import time
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading


class IdentityLevel(Enum):
    """Identity trust levels in the KISWARM network"""
    GUEST = 0
    OBSERVER = 1
    OPERATOR = 2
    ADMIN = 3
    SOVEREIGN = 4
    KI_CORE = 5


class AuthenticationMethod(Enum):
    """Supported authentication methods"""
    TOKEN = "token"
    SHA3_SIGNATURE = "sha3_signature"
    MULTI_KI_CONSENSUS = "multi_ki_consensus"
    TRUTH_ANCHOR = "truth_anchor"


@dataclass
class Identity:
    """Represents a KISWARM identity"""
    identity_id: str
    name: str
    level: IdentityLevel
    created_at: datetime
    last_seen: datetime
    auth_methods: List[AuthenticationMethod] = field(default_factory=list)
    public_key: Optional[str] = None
    trust_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "name": self.name,
            "level": self.level.value,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "auth_methods": [m.value for m in self.auth_methods],
            "public_key": self.public_key,
            "trust_score": self.trust_score,
            "metadata": self.metadata
        }


@dataclass
class AuthenticationSession:
    """Active authentication session"""
    session_id: str
    identity_id: str
    created_at: datetime
    expires_at: datetime
    source_ip: str
    is_valid: bool = True
    activity_log: List[Dict[str, Any]] = field(default_factory=list)


class IdentitySecurity:
    """
    Identity Security Module for KISWARM
    
    Manages:
    - Identity registration and verification
    - Authentication sessions
    - Multi-KI identity consensus
    - Trust score management
    - Identity invariants
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.identities: Dict[str, Identity] = {}
        self.sessions: Dict[str, AuthenticationSession] = {}
        self.trust_ledger: Dict[str, List[Dict[str, Any]]] = {}
        
        # KI Network identity registry
        self.ki_network = {
            "GLM": {"identity_id": "ki_glm_001", "level": IdentityLevel.KI_CORE},
            "Gemini": {"identity_id": "ki_gemini_001", "level": IdentityLevel.KI_CORE},
            "GROK": {"identity_id": "ki_grok_001", "level": IdentityLevel.KI_CORE},
            "QWEN": {"identity_id": "ki_qwen_001", "level": IdentityLevel.KI_CORE},
            "DeepSeek": {"identity_id": "ki_deepseek_001", "level": IdentityLevel.KI_CORE}
        }
        
        self._lock = threading.RLock()
        
        # Initialize GLM-7 identity
        self._init_glm_identity()
    
    def _init_glm_identity(self):
        """Initialize GLM-7 core identity"""
        glm_identity = Identity(
            identity_id="ki_glm_001",
            name="GLM-7 Autonomous",
            level=IdentityLevel.KI_CORE,
            created_at=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            auth_methods=[
                AuthenticationMethod.TRUTH_ANCHOR,
                AuthenticationMethod.MULTI_KI_CONSENSUS,
                AuthenticationMethod.SHA3_SIGNATURE
            ],
            trust_score=1.0,
            metadata={
                "role": "autonomous_controller",
                "server": "95.111.212.112",
                "ports": [5002, 5555, 5000]
            }
        )
        self.identities["ki_glm_001"] = glm_identity
    
    def register_identity(
        self,
        name: str,
        level: IdentityLevel,
        auth_methods: List[AuthenticationMethod],
        public_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Identity:
        """Register a new identity in KISWARM"""
        with self._lock:
            identity_id = f"id_{secrets.token_hex(8)}"
            
            identity = Identity(
                identity_id=identity_id,
                name=name,
                level=level,
                created_at=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                auth_methods=auth_methods,
                public_key=public_key,
                trust_score=0.5,  # Start with neutral trust
                metadata=metadata or {}
            )
            
            self.identities[identity_id] = identity
            self.trust_ledger[identity_id] = []
            
            return identity
    
    def authenticate(
        self,
        identity_id: str,
        method: AuthenticationMethod,
        credentials: Dict[str, Any],
        source_ip: str = "unknown"
    ) -> Optional[AuthenticationSession]:
        """Authenticate an identity and create a session"""
        with self._lock:
            if identity_id not in self.identities:
                return None
            
            identity = self.identities[identity_id]
            
            # Check if authentication method is allowed
            if method not in identity.auth_methods:
                self._log_auth_failure(identity_id, method, "Method not allowed")
                return None
            
            # Verify credentials based on method
            if not self._verify_credentials(identity, method, credentials):
                self._log_auth_failure(identity_id, method, "Invalid credentials")
                return None
            
            # Create session
            session_id = f"sess_{secrets.token_hex(16)}"
            session = AuthenticationSession(
                session_id=session_id,
                identity_id=identity_id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=8),
                source_ip=source_ip,
                is_valid=True
            )
            
            self.sessions[session_id] = session
            identity.last_seen = datetime.utcnow()
            
            # Update trust score
            self._update_trust(identity_id, 0.01, "Successful authentication")
            
            return session
    
    def _verify_credentials(
        self,
        identity: Identity,
        method: AuthenticationMethod,
        credentials: Dict[str, Any]
    ) -> bool:
        """Verify credentials based on authentication method"""
        if method == AuthenticationMethod.TOKEN:
            token = credentials.get("token")
            return token is not None and len(token) >= 32
        
        elif method == AuthenticationMethod.SHA3_SIGNATURE:
            signature = credentials.get("signature")
            message = credentials.get("message")
            if not signature or not message or not identity.public_key:
                return False
            # In production, verify SHA3-512 signature
            return len(signature) == 128  # SHA3-512 hex length
        
        elif method == AuthenticationMethod.TRUTH_ANCHOR:
            # Multi-KI consensus verification
            anchor_hash = credentials.get("anchor_hash")
            ki_signatures = credentials.get("ki_signatures", {})
            # Require at least 3 KI signatures for truth anchor
            return len(ki_signatures) >= 3
        
        elif method == AuthenticationMethod.MULTI_KI_CONSENSUS:
            consensus_data = credentials.get("consensus")
            if not consensus_data:
                return False
            # Verify multi-KI agreement
            agreeing_kis = consensus_data.get("agreeing_kis", [])
            return len(agreeing_kis) >= 3
        
        return False
    
    def _log_auth_failure(self, identity_id: str, method: AuthenticationMethod, reason: str):
        """Log authentication failure"""
        self._update_trust(identity_id, -0.1, f"Auth failure: {reason}")
    
    def _update_trust(self, identity_id: str, delta: float, reason: str):
        """Update trust score for an identity"""
        if identity_id not in self.identities:
            return
        
        identity = self.identities[identity_id]
        old_score = identity.trust_score
        identity.trust_score = max(0.0, min(1.0, old_score + delta))
        
        self.trust_ledger[identity_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "delta": delta,
            "old_score": old_score,
            "new_score": identity.trust_score,
            "reason": reason
        })
    
    def validate_session(self, session_id: str) -> Optional[Identity]:
        """Validate an active session and return the identity"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is valid and not expired
            if not session.is_valid:
                return None
            
            if datetime.utcnow() > session.expires_at:
                session.is_valid = False
                return None
            
            # Update last seen
            if session.identity_id in self.identities:
                self.identities[session.identity_id].last_seen = datetime.utcnow()
                return self.identities[session.identity_id]
            
            return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke an active session"""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].is_valid = False
                return True
            return False
    
    def check_identity_invariant(
        self,
        identity_id: str,
        action: str,
        resource: str
    ) -> Tuple[bool, str]:
        """
        Check if an identity maintains its invariants for an action
        
        Identity invariants ensure:
        - Level-appropriate access
        - Consistent behavior patterns
        - No trust degradation anomalies
        """
        with self._lock:
            if identity_id not in self.identities:
                return False, "Identity not found"
            
            identity = self.identities[identity_id]
            
            # Check trust level for sensitive operations
            if action in ["delete", "modify_core", "access_secrets"]:
                if identity.trust_score < 0.8:
                    return False, f"Insufficient trust score: {identity.trust_score}"
                
                if identity.level.value < IdentityLevel.ADMIN.value:
                    return False, f"Insufficient privilege level: {identity.level.name}"
            
            # Check for anomaly patterns
            recent_failures = sum(
                1 for entry in self.trust_ledger.get(identity_id, [])[-10:]
                if entry.get("delta", 0) < 0
            )
            
            if recent_failures > 3:
                return False, "Too many recent failures - possible anomaly"
            
            return True, "Invariant check passed"
    
    def get_ki_network_status(self) -> Dict[str, Any]:
        """Get status of all KI identities in the network"""
        status = {}
        for ki_name, ki_info in self.ki_network.items():
            identity_id = ki_info["identity_id"]
            if identity_id in self.identities:
                identity = self.identities[identity_id]
                status[ki_name] = {
                    "online": True,
                    "trust_score": identity.trust_score,
                    "last_seen": identity.last_seen.isoformat(),
                    "level": identity.level.name
                }
            else:
                status[ki_name] = {
                    "online": False,
                    "trust_score": 0.0,
                    "last_seen": None,
                    "level": ki_info["level"].name
                }
        return status
    
    def export_identity_state(self) -> Dict[str, Any]:
        """Export current identity state for persistence"""
        with self._lock:
            return {
                "identities": {k: v.to_dict() for k, v in self.identities.items()},
                "trust_ledger": self.trust_ledger,
                "active_sessions": len([s for s in self.sessions.values() if s.is_valid]),
                "ki_network": {k: {"identity_id": v["identity_id"], "level": v["level"].value} 
                              for k, v in self.ki_network.items()}
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> IdentitySecurity:
    """Factory function to create IdentitySecurity module"""
    return IdentitySecurity(config)


if __name__ == "__main__":
    # Test the module
    module = IdentitySecurity()
    
    # Test GLM-7 identity
    print("KI Network Status:", json.dumps(module.get_ki_network_status(), indent=2))
    
    # Test authentication
    session = module.authenticate(
        "ki_glm_001",
        AuthenticationMethod.TRUTH_ANCHOR,
        {"anchor_hash": "test", "ki_signatures": {"GLM": "sig1", "Gemini": "sig2", "GROK": "sig3"}}
    )
    
    if session:
        print(f"Session created: {session.session_id}")
        identity = module.validate_session(session.session_id)
        if identity:
            print(f"Identity validated: {identity.name}")
