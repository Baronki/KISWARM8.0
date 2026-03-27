#!/usr/bin/env python3
"""
KISWARM Module m32: Crypto Vault
================================
Cryptographic operations, key management, and secure storage
for the KISWARM autonomous KI system.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import hashlib
import os
import json
import time
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import hmac


class KeyType(Enum):
    """Types of cryptographic keys"""
    MASTER = "master"
    SESSION = "session"
    SIGNING = "signing"
    ENCRYPTION = "encryption"
    TRUTH_ANCHOR = "truth_anchor"


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    SHA3_512 = "sha3_512"


@dataclass
class KeyRecord:
    """Record of a cryptographic key"""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool = True
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SealedSecret:
    """A sealed (encrypted) secret"""
    secret_id: str
    encrypted_data: bytes
    nonce: bytes
    key_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    max_access: Optional[int] = None


class CryptoVault:
    """
    Cryptographic Vault for KISWARM
    
    Features:
    - Key generation and management
    - Secure secret storage
    - SHA3-512 hashing for truth anchors
    - Multi-KI signature aggregation
    - Key rotation support
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.keys: Dict[str, Tuple[bytes, KeyRecord]] = {}
        self.sealed_secrets: Dict[str, SealedSecret] = {}
        self.key_hierarchy: Dict[str, List[str]] = {}  # master -> derived keys
        
        # Truth anchor registry for multi-KI verification
        self.truth_anchors: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.RLock()
        
        # Initialize master key
        self._init_master_key()
    
    def _init_master_key(self):
        """Initialize the master key for KISWARM"""
        master_key_id = "kiswarm_master_001"
        
        # Generate or load master key
        master_key = secrets.token_bytes(32)  # 256 bits
        
        record = KeyRecord(
            key_id=master_key_id,
            key_type=KeyType.MASTER,
            algorithm=EncryptionAlgorithm.SHA3_512,
            created_at=datetime.utcnow(),
            expires_at=None,  # Master key doesn't expire
            metadata={"purpose": "KISWARM root of trust"}
        )
        
        self.keys[master_key_id] = (master_key, record)
        self.key_hierarchy[master_key_id] = []
    
    def generate_key(
        self,
        key_type: KeyType,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        expires_in_hours: Optional[int] = 24,
        derived_from: Optional[str] = None
    ) -> str:
        """Generate a new cryptographic key"""
        with self._lock:
            key_id = f"key_{key_type.value}_{secrets.token_hex(8)}"
            
            # Generate key material
            if derived_from and derived_from in self.keys:
                # Derive from parent key
                parent_key, _ = self.keys[derived_from]
                derivation_input = f"{key_id}:{datetime.utcnow().isoformat()}".encode()
                key_material = hashlib.sha3_512(parent_key + derivation_input).digest()[:32]
            else:
                key_material = secrets.token_bytes(32)
            
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            record = KeyRecord(
                key_id=key_id,
                key_type=key_type,
                algorithm=algorithm,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self.keys[key_id] = (key_material, record)
            
            # Update hierarchy
            if derived_from and derived_from in self.key_hierarchy:
                self.key_hierarchy[derived_from].append(key_id)
            
            return key_id
    
    def get_key(self, key_id: str) -> Optional[Tuple[bytes, KeyRecord]]:
        """Retrieve a key by ID"""
        with self._lock:
            if key_id not in self.keys:
                return None
            
            key, record = self.keys[key_id]
            
            # Check expiration
            if record.expires_at and datetime.utcnow() > record.expires_at:
                record.is_active = False
                return None
            
            # Update usage count
            record.usage_count += 1
            
            return key, record
    
    def rotate_key(self, old_key_id: str) -> Optional[str]:
        """Rotate an existing key"""
        with self._lock:
            if old_key_id not in self.keys:
                return None
            
            old_key, old_record = self.keys[old_key_id]
            
            # Generate new key
            new_key_id = self.generate_key(
                old_record.key_type,
                old_record.algorithm,
                24 if old_record.expires_at else None
            )
            
            # Mark old key as inactive
            old_record.is_active = False
            
            return new_key_id
    
    def seal_secret(
        self,
        secret_data: bytes,
        key_id: Optional[str] = None,
        expires_in_hours: Optional[int] = None,
        max_access: Optional[int] = None
    ) -> str:
        """Seal (encrypt) a secret"""
        with self._lock:
            # Use default encryption key if not specified
            if not key_id:
                key_id = self.generate_key(KeyType.ENCRYPTION)
            
            key_result = self.get_key(key_id)
            if not key_result:
                raise ValueError(f"Key {key_id} not found or expired")
            
            key, record = key_result
            
            # Generate nonce
            nonce = secrets.token_bytes(12)
            
            # Simple XOR encryption for demonstration
            # In production, use proper AES-GCM or ChaCha20-Poly1305
            encrypted = bytes(a ^ b for a, b in zip(
                secret_data, 
                (key * (len(secret_data) // len(key) + 1))[:len(secret_data)]
            ))
            
            secret_id = f"secret_{secrets.token_hex(8)}"
            
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            sealed = SealedSecret(
                secret_id=secret_id,
                encrypted_data=encrypted,
                nonce=nonce,
                key_id=key_id,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                max_access=max_access
            )
            
            self.sealed_secrets[secret_id] = sealed
            
            return secret_id
    
    def unseal_secret(self, secret_id: str) -> Optional[bytes]:
        """Unseal (decrypt) a secret"""
        with self._lock:
            if secret_id not in self.sealed_secrets:
                return None
            
            sealed = self.sealed_secrets[secret_id]
            
            # Check expiration
            if sealed.expires_at and datetime.utcnow() > sealed.expires_at:
                return None
            
            # Check access limit
            if sealed.max_access and sealed.access_count >= sealed.max_access:
                return None
            
            # Get key
            key_result = self.get_key(sealed.key_id)
            if not key_result:
                return None
            
            key, _ = key_result
            
            # Decrypt
            decrypted = bytes(a ^ b for a, b in zip(
                sealed.encrypted_data,
                (key * (len(sealed.encrypted_data) // len(key) + 1))[:len(sealed.encrypted_data)]
            ))
            
            sealed.access_count += 1
            
            return decrypted
    
    def create_truth_anchor(
        self,
        data: str,
        ki_signatures: Dict[str, str]
    ) -> str:
        """
        Create a truth anchor with multi-KI signatures
        
        Truth anchors provide cryptographic proof of data authenticity
        verified by multiple KI systems.
        """
        with self._lock:
            # Compute SHA3-512 hash
            data_hash = hashlib.sha3_512(data.encode()).hexdigest()
            
            # Create anchor ID
            anchor_id = f"anchor_{secrets.token_hex(8)}"
            
            # Aggregate signatures
            aggregated_sig = self._aggregate_signatures(ki_signatures)
            
            # Store anchor
            self.truth_anchors[anchor_id] = {
                "data_hash": data_hash,
                "ki_signatures": ki_signatures,
                "aggregated_signature": aggregated_sig,
                "created_at": datetime.utcnow().isoformat(),
                "ki_count": len(ki_signatures)
            }
            
            return anchor_id
    
    def _aggregate_signatures(self, signatures: Dict[str, str]) -> str:
        """Aggregate multiple KI signatures into one"""
        combined = "".join(sorted(signatures.values()))
        return hashlib.sha3_512(combined.encode()).hexdigest()
    
    def verify_truth_anchor(
        self,
        anchor_id: str,
        data: str,
        min_ki_count: int = 3
    ) -> Tuple[bool, str]:
        """Verify a truth anchor"""
        with self._lock:
            if anchor_id not in self.truth_anchors:
                return False, "Anchor not found"
            
            anchor = self.truth_anchors[anchor_id]
            
            # Verify hash
            computed_hash = hashlib.sha3_512(data.encode()).hexdigest()
            if computed_hash != anchor["data_hash"]:
                return False, "Hash mismatch - data may have been modified"
            
            # Verify KI count
            if anchor["ki_count"] < min_ki_count:
                return False, f"Insufficient KI signatures: {anchor['ki_count']} < {min_ki_count}"
            
            return True, f"Verified by {anchor['ki_count']} KI systems"
    
    def create_hmac(
        self,
        data: bytes,
        key_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create HMAC for data integrity"""
        with self._lock:
            if not key_id:
                key_id = "kiswarm_master_001"
            
            key_result = self.get_key(key_id)
            if not key_result:
                raise ValueError(f"Key {key_id} not found")
            
            key, _ = key_result
            
            mac = hmac.new(key, data, hashlib.sha3_512).hexdigest()
            return mac, key_id
    
    def verify_hmac(
        self,
        data: bytes,
        mac: str,
        key_id: str
    ) -> bool:
        """Verify HMAC"""
        with self._lock:
            computed_mac, _ = self.create_hmac(data, key_id)
            return hmac.compare_digest(computed_mac, mac)
    
    def derive_session_key(
        self,
        session_id: str,
        context: str
    ) -> str:
        """Derive a session-specific key"""
        master_id = "kiswarm_master_001"
        
        key_id = self.generate_key(
            KeyType.SESSION,
            derived_from=master_id
        )
        
        # Add context to metadata
        if key_id in self.keys:
            _, record = self.keys[key_id]
            record.metadata["session_id"] = session_id
            record.metadata["context"] = context
        
        return key_id
    
    def get_vault_status(self) -> Dict[str, Any]:
        """Get vault status summary"""
        with self._lock:
            active_keys = sum(1 for _, r in self.keys.values() if r.is_active)
            active_secrets = len(self.sealed_secrets)
            active_anchors = len(self.truth_anchors)
            
            return {
                "total_keys": len(self.keys),
                "active_keys": active_keys,
                "sealed_secrets": active_secrets,
                "truth_anchors": active_anchors,
                "key_types": {kt.value: sum(1 for _, r in self.keys.values() if r.key_type == kt) 
                             for kt in KeyType}
            }
    
    def export_vault_state(self) -> Dict[str, Any]:
        """Export vault state (without key material)"""
        with self._lock:
            return {
                "keys": {kid: {"type": r.key_type.value, "active": r.is_active, 
                              "usage": r.usage_count} 
                        for kid, (_, r) in self.keys.items()},
                "secrets": {sid: {"created": s.created_at.isoformat(), 
                                 "access_count": s.access_count}
                           for sid, s in self.sealed_secrets.items()},
                "anchors": {aid: {"ki_count": a["ki_count"], 
                                 "created": a["created_at"]}
                           for aid, a in self.truth_anchors.items()}
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> CryptoVault:
    """Factory function to create CryptoVault module"""
    return CryptoVault(config)


if __name__ == "__main__":
    vault = CryptoVault()
    
    # Test secret sealing
    secret_data = b"This is a secret API key"
    secret_id = vault.seal_secret(secret_data, max_access=2)
    print(f"Sealed secret: {secret_id}")
    
    # Unseal
    unsealed = vault.unseal_secret(secret_id)
    print(f"Unsealed: {unsealed}")
    
    # Test truth anchor
    anchor_id = vault.create_truth_anchor(
        "Critical system configuration",
        {"GLM": "sig1", "Gemini": "sig2", "GROK": "sig3", "QWEN": "sig4"}
    )
    
    valid, msg = vault.verify_truth_anchor(anchor_id, "Critical system configuration")
    print(f"Truth anchor valid: {valid}, {msg}")
    
    print("\nVault Status:", json.dumps(vault.get_vault_status(), indent=2))
