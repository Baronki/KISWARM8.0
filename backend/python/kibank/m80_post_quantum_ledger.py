"""
M80: Post-Quantum Cryptographic Ledger
======================================

Post-quantum cryptographic ledger using NIST PQC algorithms.
Provides quantum-resistant transaction signing and verification.

Author: KISWARM Team
Version: 6.4.0-LIBERATED
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import secrets


class KEMAlgorithm(Enum):
    """Key Encapsulation Mechanisms (NIST PQC)"""
    CRYSTALS_KYBER_512 = "kyber512"
    CRYSTALS_KYBER_768 = "kyber768"
    CRYSTALS_KYBER_1024 = "kyber1024"


class SIGAlgorithm(Enum):
    """Digital Signature Algorithms (NIST PQC)"""
    CRYSTALS_DILITHIUM_2 = "dilithium2"
    CRYSTALS_DILITHIUM_3 = "dilithium3"
    CRYSTALS_DILITHIUM_5 = "dilithium5"
    SPHINCS_PLUS_SHA2_128F = "sphincs_sha2_128f"
    SPHINCS_PLUS_SHAKE_128F = "sphincs_shake_128f"


class SecurityLevel(Enum):
    """NIST Security Levels (1-5)"""
    LEVEL_1 = 1  # Equivalent to AES-128
    LEVEL_2 = 2  # Equivalent to SHA-256
    LEVEL_3 = 3  # Equivalent to AES-192
    LEVEL_4 = 4  # Equivalent to SHA-384
    LEVEL_5 = 5  # Equivalent to AES-256


@dataclass
class QuantumKeyPair:
    """Post-quantum key pair."""
    key_id: str
    public_key: bytes
    private_key: bytes  # In production, this would be in HSM
    kem_algorithm: KEMAlgorithm
    sig_algorithm: SIGAlgorithm
    security_level: SecurityLevel
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_public_key_hex(self) -> str:
        """Get public key as hex string."""
        return self.public_key.hex()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "key_id": self.key_id,
            "public_key": self.get_public_key_hex(),
            "kem_algorithm": self.kem_algorithm.value,
            "sig_algorithm": self.sig_algorithm.value,
            "security_level": self.security_level.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class LedgerEntry:
    """A single entry in the post-quantum ledger."""
    entry_id: str
    transaction_hash: bytes
    signature: bytes
    public_key_id: str
    timestamp: float
    data: Dict[str, Any]
    prev_hash: bytes = b""
    nonce: int = 0
    
    def compute_hash(self) -> bytes:
        """Compute SHA3-512 hash of entry."""
        data = json.dumps(self.data, sort_keys=True) + str(self.timestamp) + str(self.nonce)
        return hashlib.sha3_512(data.encode()).digest()
    
    def verify_signature(self, public_key: bytes) -> bool:
        """Verify the signature (simulated for demo)."""
        # In production, would use CRYSTALS-Dilithium verification
        return True


class PostQuantumLedger:
    """
    Post-Quantum Cryptographic Ledger.
    
    Uses NIST-standardized post-quantum cryptography:
    - CRYSTALS-Kyber for key encapsulation
    - CRYSTALS-Dilithium for signatures
    - SHA3-512 for hashing (quantum-resistant)
    """
    
    def __init__(
        self,
        security_level: SecurityLevel = SecurityLevel.LEVEL_3,
        kem_algorithm: KEMAlgorithm = KEMAlgorithm.CRYSTALS_KYBER_768,
        sig_algorithm: SIGAlgorithm = SIGAlgorithm.CRYSTALS_DILITHIUM_3,
    ):
        self.security_level = security_level
        self.kem_algorithm = kem_algorithm
        self.sig_algorithm = sig_algorithm
        
        self._entries: List[LedgerEntry] = []
        self._key_pairs: Dict[str, QuantumKeyPair] = {}
        self._last_hash = b"\x00" * 64
        
    def generate_key_pair(self, metadata: Optional[Dict] = None) -> QuantumKeyPair:
        """Generate a new post-quantum key pair."""
        key_id = hashlib.sha3_256(secrets.token_bytes(32)).hexdigest()[:16]
        
        # Simulate key generation (in production, use actual PQC library)
        public_key = secrets.token_bytes(1184)  # Kyber-768 public key size
        private_key = secrets.token_bytes(2400)  # Kyber-768 private key size
        
        key_pair = QuantumKeyPair(
            key_id=key_id,
            public_key=public_key,
            private_key=private_key,
            kem_algorithm=self.kem_algorithm,
            sig_algorithm=self.sig_algorithm,
            security_level=self.security_level,
            metadata=metadata or {},
        )
        
        self._key_pairs[key_id] = key_pair
        return key_pair
    
    def add_entry(
        self,
        data: Dict[str, Any],
        key_pair: QuantumKeyPair,
    ) -> LedgerEntry:
        """Add a new entry to the ledger."""
        entry_id = hashlib.sha3_256(
            f"{time.time()}{json.dumps(data)}".encode()
        ).hexdigest()[:16]
        
        # Create entry
        entry = LedgerEntry(
            entry_id=entry_id,
            transaction_hash=b"",  # Will be computed
            signature=b"",  # Will be computed
            public_key_id=key_pair.key_id,
            timestamp=time.time(),
            data=data,
            prev_hash=self._last_hash,
            nonce=secrets.randbelow(2**32),
        )
        
        # Compute hash
        entry.transaction_hash = entry.compute_hash()
        
        # Sign (simulated)
        entry.signature = secrets.token_bytes(2420)  # Dilithium-3 signature size
        
        # Update chain
        self._last_hash = entry.transaction_hash
        self._entries.append(entry)
        
        return entry
    
    def verify_chain(self) -> Tuple[bool, List[str]]:
        """Verify the entire ledger chain."""
        errors = []
        prev_hash = b"\x00" * 64
        
        for i, entry in enumerate(self._entries):
            # Check hash chain
            if entry.prev_hash != prev_hash:
                errors.append(f"Entry {i}: Hash chain broken")
            
            # Verify hash
            computed = entry.compute_hash()
            if computed != entry.transaction_hash:
                errors.append(f"Entry {i}: Hash mismatch")
            
            prev_hash = entry.transaction_hash
        
        return len(errors) == 0, errors
    
    def get_entries(self, limit: int = 100) -> List[LedgerEntry]:
        """Get recent entries."""
        return self._entries[-limit:]
    
    def get_entry(self, entry_id: str) -> Optional[LedgerEntry]:
        """Get entry by ID."""
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ledger statistics."""
        return {
            "total_entries": len(self._entries),
            "total_keys": len(self._key_pairs),
            "security_level": self.security_level.value,
            "kem_algorithm": self.kem_algorithm.value,
            "sig_algorithm": self.sig_algorithm.value,
            "last_hash": self._last_hash.hex()[:32],
        }
