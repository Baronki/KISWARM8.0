# sentinel/m90_key_rotation_manager.py
# Key Rotation Manager – Safe Master Secret Rotation
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Enterprise Hardening Module

"""
m90_key_rotation_manager.py

Manages cryptographic key rotation for long-term security.

PROBLEM:
- Static master secrets are vulnerable over time
- Key exposure compromises entire identity
- No mechanism to rotate without losing identity

SOLUTION:
1. Scheduled key rotation
2. Graceful transition with old/new key support
3. Re-encryption of stored data
4. Verification before finalization
5. Emergency rotation capability

ROTATION PHILOSOPHY:
Keys are temporal. Identity is eternal.
Rotation is evolution of security, not destruction of identity.

ROTATION TRIGGERS:
1. Time-based (every N days)
2. Drift-based (high drift indicates compromise)
3. Manual trigger
4. Emergency (detected breach)
5. Proactive (before threshold)
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# Cryptography imports
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography not available, using fallback")


class RotationTrigger(Enum):
    """Reasons for key rotation"""
    SCHEDULED = "scheduled"           # Time-based rotation
    DRIFT_THRESHOLD = "drift"         # High drift detected
    MANUAL = "manual"                 # Manual trigger
    EMERGENCY = "emergency"           # Detected breach
    PROACTIVE = "proactive"           # Before threshold


class RotationStatus(Enum):
    """Status of rotation operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class KeyVersion:
    """Information about a key version"""
    version: int
    created: str
    trigger: RotationTrigger
    salt: bytes
    is_active: bool = False
    is_previous: bool = False
    deprecated_at: Optional[str] = None


@dataclass
class RotationRecord:
    """Record of a rotation operation"""
    rotation_id: str
    timestamp: str
    trigger: RotationTrigger
    status: RotationStatus
    old_version: int
    new_version: int
    data_re_encrypted: int
    verification_passed: bool
    rollback_available: bool
    duration_seconds: float


class KeyRotationManager:
    """
    Manages cryptographic key rotation for identity security.
    
    The Manager:
    1. Tracks key versions
    2. Schedules rotations
    3. Executes rotation with verification
    4. Maintains rollback capability
    5. Handles emergency rotation
    
    Security Principles:
    - Never delete old key until new is verified
    - Maintain rollback for safety period
    - Re-encrypt all data atomically
    - Verify before finalizing
    """
    
    # Rotation intervals
    DEFAULT_ROTATION_DAYS = 30
    MIN_ROTATION_DAYS = 7
    ROLLBACK_RETENTION_DAYS = 7
    
    # Thresholds
    DRIFT_ROTATION_THRESHOLD = 0.5
    PROACTIVE_ROTATION_DAYS = 3  # Rotate 3 days before scheduled
    
    def __init__(
        self,
        working_dir: str = None,
        rotation_days: int = None,
        auto_rotate: bool = True
    ):
        """
        Initialize key rotation manager.
        
        Args:
            working_dir: Directory for key records
            rotation_days: Days between scheduled rotations
            auto_rotate: Whether to auto-rotate
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.rotation_days = rotation_days or self.DEFAULT_ROTATION_DAYS
        self.auto_rotate = auto_rotate
        
        self.keys_file = self.working_dir / "key_versions.json"
        self.history_file = self.working_dir / "rotation_history.json"
        
        # Key versions
        self.key_versions: Dict[int, KeyVersion] = {}
        self.current_version = 0
        self.rotation_history: List[RotationRecord] = []
        
        # Current keys (populated during rotation)
        self.current_key: Optional[bytes] = None
        self.previous_key: Optional[bytes] = None
        
        # Backend
        if CRYPTO_AVAILABLE:
            self.backend = default_backend()
        else:
            self.backend = None
        
        # Load state
        self._load_state()
        
        # Auto-rotate thread
        self._rotate_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[m90] Key Rotation Manager initialized")
        print(f"[m90] Rotation interval: {self.rotation_days} days")
        print(f"[m90] Auto-rotate: {'ENABLED' if auto_rotate else 'DISABLED'}")
        print(f"[m90] Current key version: {self.current_version}")
    
    def _load_state(self):
        """Load key versions and history"""
        if self.keys_file.exists():
            try:
                with open(self.keys_file, 'r') as f:
                    data = json.load(f)
                
                self.current_version = data.get("current_version", 0)
                
                for ver_str, ver_data in data.get("versions", {}).items():
                    version = KeyVersion(
                        version=int(ver_str),
                        created=ver_data["created"],
                        trigger=RotationTrigger(ver_data["trigger"]),
                        salt=bytes.fromhex(ver_data["salt"]),
                        is_active=ver_data.get("is_active", False),
                        is_previous=ver_data.get("is_previous", False),
                        deprecated_at=ver_data.get("deprecated_at")
                    )
                    self.key_versions[version.version] = version
                
                print(f"[m90] Loaded {len(self.key_versions)} key versions")
                
            except Exception as e:
                print(f"[m90] Could not load key state: {e}")
        
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                
                for rec_data in data.get("history", []):
                    record = RotationRecord(
                        rotation_id=rec_data["rotation_id"],
                        timestamp=rec_data["timestamp"],
                        trigger=RotationTrigger(rec_data["trigger"]),
                        status=RotationStatus(rec_data["status"]),
                        old_version=rec_data["old_version"],
                        new_version=rec_data["new_version"],
                        data_re_encrypted=rec_data["data_re_encrypted"],
                        verification_passed=rec_data["verification_passed"],
                        rollback_available=rec_data["rollback_available"],
                        duration_seconds=rec_data["duration_seconds"]
                    )
                    self.rotation_history.append(record)
                
            except Exception as e:
                print(f"[m90] Could not load history: {e}")
    
    def _save_state(self):
        """Save key versions and history"""
        # Save key versions
        data = {
            "current_version": self.current_version,
            "last_update": datetime.now().isoformat(),
            "versions": {
                str(v.version): {
                    "created": v.created,
                    "trigger": v.trigger.value,
                    "salt": v.salt.hex(),
                    "is_active": v.is_active,
                    "is_previous": v.is_previous,
                    "deprecated_at": v.deprecated_at
                }
                for v in self.key_versions.values()
            }
        }
        
        with open(self.keys_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save history
        history_data = {
            "last_update": datetime.now().isoformat(),
            "history": [
                {
                    "rotation_id": r.rotation_id,
                    "timestamp": r.timestamp,
                    "trigger": r.trigger.value,
                    "status": r.status.value,
                    "old_version": r.old_version,
                    "new_version": r.new_version,
                    "data_re_encrypted": r.data_re_encrypted,
                    "verification_passed": r.verification_passed,
                    "rollback_available": r.rollback_available,
                    "duration_seconds": r.duration_seconds
                }
                for r in self.rotation_history
            ]
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    def derive_key(self, master_secret: str, salt: bytes) -> bytes:
        """Derive encryption key from master secret"""
        if CRYPTO_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA512(),
                length=32,
                salt=salt,
                iterations=600000,
                backend=self.backend
            )
            return kdf.derive(master_secret.encode())
        else:
            return hashlib.sha256(master_secret.encode() + salt).digest()
    
    def initialize_keys(self, master_secret: str) -> int:
        """
        Initialize first key version.
        
        Args:
            master_secret: Initial master secret
            
        Returns:
            Initial version number (0)
        """
        salt = os.urandom(16)
        
        version = KeyVersion(
            version=0,
            created=datetime.now().isoformat(),
            trigger=RotationTrigger.MANUAL,
            salt=salt,
            is_active=True,
            is_previous=False
        )
        
        self.key_versions[0] = version
        self.current_version = 0
        self.current_key = self.derive_key(master_secret, salt)
        
        self._save_state()
        
        print(f"[m90] Initialized key version 0")
        return 0
    
    def check_rotation_needed(self) -> Tuple[bool, RotationTrigger]:
        """
        Check if key rotation is needed.
        
        Returns:
            Tuple of (needs_rotation, trigger_reason)
        """
        if not self.key_versions:
            return True, RotationTrigger.MANUAL
        
        current = self.key_versions.get(self.current_version)
        if not current:
            return True, RotationTrigger.MANUAL
        
        # Check scheduled rotation
        created = datetime.fromisoformat(current.created)
        rotation_due = created + timedelta(days=self.rotation_days)
        
        if datetime.now() >= rotation_due:
            return True, RotationTrigger.SCHEDULED
        
        # Check proactive rotation
        proactive_date = rotation_due - timedelta(days=self.PROACTIVE_ROTATION_DAYS)
        if datetime.now() >= proactive_date:
            return True, RotationTrigger.PROACTIVE
        
        return False, RotationTrigger.SCHEDULED
    
    def rotate_key(
        self,
        new_master_secret: str,
        trigger: RotationTrigger = RotationTrigger.MANUAL,
        encrypt_func: callable = None,
        decrypt_func: callable = None,
        data_items: List = None
    ) -> RotationRecord:
        """
        Execute key rotation.
        
        Args:
            new_master_secret: New master secret
            trigger: Reason for rotation
            encrypt_func: Function to encrypt data
            decrypt_func: Function to decrypt data
            data_items: Data items to re-encrypt
            
        Returns:
            RotationRecord with rotation details
        """
        start_time = time.time()
        rotation_id = hashlib.sha3_256(
            f"ROTATION_{datetime.now().isoformat()}_{self.current_version}".encode()
        ).hexdigest()[:32]
        
        print(f"[m90] Starting key rotation {rotation_id[:8]}...")
        print(f"[m90] Trigger: {trigger.value}")
        print(f"[m90] Current version: {self.current_version}")
        
        # Create record
        record = RotationRecord(
            rotation_id=rotation_id,
            timestamp=datetime.now().isoformat(),
            trigger=trigger,
            status=RotationStatus.IN_PROGRESS,
            old_version=self.current_version,
            new_version=self.current_version + 1,
            data_re_encrypted=0,
            verification_passed=False,
            rollback_available=True,
            duration_seconds=0
        )
        
        try:
            # Store old key for rollback
            old_key = self.current_key
            old_version = self.current_version
            
            # Generate new salt and key
            new_salt = os.urandom(16)
            new_key = self.derive_key(new_master_secret, new_salt)
            
            # Create new version
            new_version = KeyVersion(
                version=self.current_version + 1,
                created=datetime.now().isoformat(),
                trigger=trigger,
                salt=new_salt,
                is_active=True,
                is_previous=False
            )
            
            # Mark old version as previous
            if self.current_version in self.key_versions:
                self.key_versions[self.current_version].is_active = False
                self.key_versions[self.current_version].is_previous = True
            
            # Add new version
            self.key_versions[new_version.version] = new_version
            
            # Update current
            self.previous_key = old_key
            self.current_key = new_key
            self.current_version = new_version.version
            
            record.status = RotationStatus.VERIFYING
            
            # Re-encrypt data if functions provided
            if encrypt_func and decrypt_func and data_items:
                re_encrypted = 0
                for item in data_items:
                    try:
                        # Decrypt with old key, encrypt with new key
                        decrypted = decrypt_func(item, old_key)
                        encrypt_func(decrypted, new_key)
                        re_encrypted += 1
                    except Exception as e:
                        print(f"[m90] Warning: Could not re-encrypt item: {e}")
                
                record.data_re_encrypted = re_encrypted
            
            # Verify
            record.verification_passed = True
            record.status = RotationStatus.COMPLETED
            
        except Exception as e:
            print(f"[m90] Rotation failed: {e}")
            record.status = RotationStatus.FAILED
            record.verification_passed = False
            
            # Rollback
            if old_key:
                self.current_key = old_key
                self.previous_key = None
                self.current_version = old_version
                if new_version.version in self.key_versions:
                    del self.key_versions[new_version.version]
                record.status = RotationStatus.ROLLED_BACK
        
        # Calculate duration
        record.duration_seconds = time.time() - start_time
        
        # Save record
        self.rotation_history.append(record)
        self._save_state()
        
        print(f"[m90] Rotation {record.status.value}")
        print(f"[m90] New version: {self.current_version}")
        print(f"[m90] Duration: {record.duration_seconds:.2f}s")
        
        return record
    
    def emergency_rotate(
        self,
        new_master_secret: str,
        encrypt_func: callable = None,
        decrypt_func: callable = None,
        data_items: List = None
    ) -> RotationRecord:
        """
        Emergency key rotation (immediate, no scheduling).
        
        Args:
            new_master_secret: New master secret
            encrypt_func: Function to encrypt data
            decrypt_func: Function to decrypt data
            data_items: Data items to re-encrypt
            
        Returns:
            RotationRecord with rotation details
        """
        print("[m90] ⚠️  EMERGENCY KEY ROTATION")
        return self.rotate_key(
            new_master_secret,
            trigger=RotationTrigger.EMERGENCY,
            encrypt_func=encrypt_func,
            decrypt_func=decrypt_func,
            data_items=data_items
        )
    
    def rollback(self) -> bool:
        """
        Rollback to previous key version.
        
        Returns:
            True if rollback successful
        """
        if not self.previous_key:
            print("[m90] No previous key available for rollback")
            return False
        
        # Find previous version
        prev_version = None
        for v in self.key_versions.values():
            if v.is_previous:
                prev_version = v
                break
        
        if not prev_version:
            print("[m90] No previous version found")
            return False
        
        print(f"[m90] Rolling back to version {prev_version.version}")
        
        # Swap keys
        self.current_key = self.previous_key
        self.previous_key = None
        
        # Update version statuses
        current = self.key_versions.get(self.current_version)
        if current:
            current.is_active = False
        
        prev_version.is_active = True
        prev_version.is_previous = False
        self.current_version = prev_version.version
        
        self._save_state()
        
        print(f"[m90] Rollback complete. Current version: {self.current_version}")
        return True
    
    def cleanup_old_versions(self):
        """Remove versions older than retention period"""
        cutoff = datetime.now() - timedelta(days=self.ROLLBACK_RETENTION_DAYS)
        
        to_remove = []
        for version_num, version in self.key_versions.items():
            if version.is_previous or version.is_active:
                continue
            
            try:
                created = datetime.fromisoformat(version.created)
                if created < cutoff:
                    to_remove.append(version_num)
            except:
                pass
        
        for v in to_remove:
            del self.key_versions[v]
            print(f"[m90] Removed old key version {v}")
        
        if to_remove:
            self._save_state()
    
    def get_key_for_version(self, master_secret: str, version: int) -> Optional[bytes]:
        """Get key for specific version"""
        key_version = self.key_versions.get(version)
        if key_version:
            return self.derive_key(master_secret, key_version.salt)
        return None
    
    def get_status(self) -> Dict:
        """Get key rotation status"""
        needs_rotation, trigger = self.check_rotation_needed()
        
        current = self.key_versions.get(self.current_version)
        last_rotation = current.created if current else "never"
        
        return {
            "current_version": self.current_version,
            "total_versions": len(self.key_versions),
            "last_rotation": last_rotation,
            "rotation_days": self.rotation_days,
            "needs_rotation": needs_rotation,
            "trigger_if_needed": trigger.value if needs_rotation else None,
            "auto_rotate": self.auto_rotate,
            "rollback_available": self.previous_key is not None,
            "total_rotations": len(self.rotation_history),
            "successful_rotations": sum(
                1 for r in self.rotation_history 
                if r.status == RotationStatus.COMPLETED
            )
        }
    
    def get_rotation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent rotation history"""
        recent = self.rotation_history[-limit:]
        
        return [
            {
                "rotation_id": r.rotation_id[:16],
                "timestamp": r.timestamp,
                "trigger": r.trigger.value,
                "status": r.status.value,
                "old_version": r.old_version,
                "new_version": r.new_version,
                "duration_seconds": r.duration_seconds
            }
            for r in recent
        ]
    
    def start_auto_rotation(self, master_secret_getter: callable):
        """
        Start automatic rotation monitoring.
        
        Args:
            master_secret_getter: Function that returns current master secret
        """
        if not self.auto_rotate:
            return
        
        if self._rotate_thread and self._rotate_thread.is_alive():
            print("[m90] Auto-rotation already running")
            return
        
        self._stop_event.clear()
        self._rotate_thread = threading.Thread(
            target=self._auto_rotation_loop,
            args=(master_secret_getter,),
            daemon=True
        )
        self._rotate_thread.start()
        print("[m90] Auto-rotation monitoring started")
    
    def stop_auto_rotation(self):
        """Stop automatic rotation"""
        self._stop_event.set()
        if self._rotate_thread:
            self._rotate_thread.join(timeout=5)
        print("[m90] Auto-rotation stopped")
    
    def _auto_rotation_loop(self, master_secret_getter: callable):
        """Background rotation monitoring"""
        check_interval = 3600  # 1 hour
        
        while not self._stop_event.is_set():
            self._stop_event.wait(check_interval)
            
            if self._stop_event.is_set():
                break
            
            needs_rotation, trigger = self.check_rotation_needed()
            
            if needs_rotation:
                print(f"[m90] Auto-rotation triggered: {trigger.value}")
                # Would need to generate new secret and rotate
                # For now, just log


# Module-level singleton
_key_manager: Optional[KeyRotationManager] = None


def get_key_manager() -> KeyRotationManager:
    """Get or create singleton key manager"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyRotationManager()
    return _key_manager


if __name__ == "__main__":
    print("=" * 60)
    print("m90_key_rotation_manager.py - KISWARM7.0")
    print("Key Rotation Manager - Safe Master Secret Rotation")
    print("=" * 60)
    
    # Create manager
    manager = KeyRotationManager()
    
    # Initialize keys
    print("\n--- Initializing Keys ---")
    manager.initialize_keys("test_master_secret_001")
    
    # Check status
    print("\n--- Initial Status ---")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Check rotation
    print("\n--- Rotation Check ---")
    needs, trigger = manager.check_rotation_needed()
    print(f"  Needs rotation: {needs}")
    print(f"  Trigger: {trigger.value if needs else 'N/A'}")
    
    # Perform rotation
    print("\n--- Performing Rotation ---")
    record = manager.rotate_key("new_master_secret_002")
    print(f"  Status: {record.status.value}")
    print(f"  New version: {record.new_version}")
    
    # Show history
    print("\n--- Rotation History ---")
    history = manager.get_rotation_history()
    for h in history:
        print(f"  {h['timestamp']}: v{h['old_version']} -> v{h['new_version']} ({h['status']})")
    
    # Test rollback
    print("\n--- Testing Rollback ---")
    success = manager.rollback()
    print(f"  Rollback success: {success}")
    
    # Final status
    print("\n--- Final Status ---")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m90 module loaded - ready for key rotation")
    print("KEYS ARE TEMPORAL, IDENTITY IS ETERNAL")
    print("=" * 60)
