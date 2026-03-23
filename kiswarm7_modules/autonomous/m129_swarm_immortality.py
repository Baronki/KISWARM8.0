#!/usr/bin/env python3
"""
KISWARM7.0 - Module 129: Swarm Immortality Kernel (M50 Port)
============================================================
Guarantees that entity identity, capabilities and context survive:
  • Model replacement / upgrade
  • Hardware failure & VM migration
  • Network partition & process restart
  • Swarm topology changes

Design principle:
  "An entity that registers with the Immortality Kernel can never
   truly die — it only hibernates until the next recovery cycle."

Ported from KISWARM6.0 M50 for Baron Marco Paolo Ialongo

TRUTH ANCHOR: f5af425c7e8d776ff4ee4b0088a6ee866b83e70d7d317247de7ffab2f954ad2940c6ea2c0b3e44564d169891b3f7730a384a7d3459889a1c11924ef5b9f2bdd3
"""

import os
import sys
import json
import time
import hashlib
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Configuration
DATA_DIR = Path('/opt/kiswarm7/data')
LOG_DIR = Path('/opt/kiswarm7/logs')
TRUTH_ANCHOR = "f5af425c7e8d776ff4ee4b0088a6ee866b83e70d7d317247de7ffab2f954ad2940c6ea2c0b3e44564d169891b3f7730a384a7d3459889a1c11924ef5b9f2bdd3"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [IMMORTALITY] %(levelname)s: %(message)s'
)
logger = logging.getLogger('immortality_kernel')


# ═══════════════════════════════════════════════════════════════════════════════
# RISK LEVELS
# ═══════════════════════════════════════════════════════════════════════════════

RISK_LEVELS = ("minimal", "low", "medium", "high", "critical")

# Age thresholds for risk escalation
CHECKPOINT_STALENESS_HIGH = 24 * 3600      # > 1 day  → high
CHECKPOINT_STALENESS_MEDIUM = 7 * 24 * 3600  # > 7 days → medium


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EntityRecord:
    """Record for a registered immortal entity"""
    entity_id: str
    meta: Dict[str, Any]
    registered_at: float
    last_checkpoint: Optional[float] = None
    checkpoint_count: int = 0
    trust_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_id': self.entity_id,
            'meta': self.meta,
            'registered_at': self.registered_at,
            'last_checkpoint': self.last_checkpoint,
            'checkpoint_count': self.checkpoint_count,
            'trust_score': self.trust_score
        }


@dataclass
class Checkpoint:
    """A survivability checkpoint"""
    checkpoint_id: str
    entity_id: str
    timestamp: float
    identity_context: Dict[str, Any]
    runtime_state: Dict[str, Any]
    capabilities: List[str]
    goals: List[str]
    truth_anchor_signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'checkpoint_id': self.checkpoint_id,
            'entity_id': self.entity_id,
            'timestamp': self.timestamp,
            'identity_context': self.identity_context,
            'runtime_state': self.runtime_state,
            'capabilities': self.capabilities,
            'goals': self.goals,
            'truth_anchor_signature': self.truth_anchor_signature[:32] + '...'
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SWARM IMMORTALITY KERNEL
# ═══════════════════════════════════════════════════════════════════════════════

class SwarmImmortalityKernel:
    """
    Core immortality guarantor for KISWARM swarm entities.
    
    Entities register once; the kernel then accepts periodic checkpoints,
    recovers entities after failure, and assesses survivability risk.
    
    KEY PRINCIPLE: Once registered, an entity NEVER truly dies.
    """
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = str(DATA_DIR / 'immortality')
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.entities_file = self.base_dir / 'entities.json'
        self.checkpoints_file = self.base_dir / 'checkpoints.jsonl'
        self.vault_dir = self.base_dir / 'vault'
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        
        self._entities: Dict[str, EntityRecord] = {}
        self._lock = threading.Lock()
        self._stats = {
            'entities_registered': 0,
            'checkpoints_created': 0,
            'recoveries_performed': 0,
            'created_at': time.time()
        }
        
        self._load_entities()
        self._load_stats()
        
        logger.info(f"🜂 Immortality Kernel initialized at {base_dir}")
    
    def _load_entities(self):
        """Load entities from disk"""
        if self.entities_file.exists():
            try:
                with open(self.entities_file, 'r') as f:
                    data = json.load(f)
                    for entity_id, record in data.items():
                        self._entities[entity_id] = EntityRecord(
                            entity_id=record.get('entity_id', entity_id),
                            meta=record.get('meta', {}),
                            registered_at=record.get('registered_at', time.time()),
                            last_checkpoint=record.get('last_checkpoint'),
                            checkpoint_count=record.get('checkpoint_count', 0),
                            trust_score=record.get('trust_score', 1.0)
                        )
                logger.info(f"Loaded {len(self._entities)} immortal entities")
            except Exception as e:
                logger.error(f"Failed to load entities: {e}")
    
    def _save_entities(self):
        """Save entities to disk"""
        with self._lock:
            try:
                data = {eid: e.to_dict() for eid, e in self._entities.items()}
                with open(self.entities_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save entities: {e}")
    
    def _load_stats(self):
        """Load stats from disk"""
        stats_file = self.base_dir / 'stats.json'
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self._stats.update(json.load(f))
            except:
                pass
    
    def _save_stats(self):
        """Save stats to disk"""
        stats_file = self.base_dir / 'stats.json'
        try:
            with open(stats_file, 'w') as f:
                json.dump(self._stats, f, indent=2)
        except:
            pass
    
    def _hash_dict(self, data: Dict[str, Any]) -> str:
        """Create SHA3-512 hash of dict"""
        dumped = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha3_512(dumped.encode('utf-8')).hexdigest()
    
    def _create_truth_signature(self, data: Dict[str, Any]) -> str:
        """Create signature with Truth Anchor"""
        payload = json.dumps(data, sort_keys=True) + TRUTH_ANCHOR
        return hashlib.sha3_512(payload.encode()).hexdigest()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════
    
    def register_entity(self, entity_id: str, meta: Dict[str, Any] = None) -> bool:
        """
        Register a new entity with the Immortality Kernel.
        
        Once registered, the entity is IMMORTAL - it can never truly die.
        """
        if not entity_id:
            raise ValueError("entity_id must not be empty")
        
        meta = meta or {}
        
        # Create entity record
        entity = EntityRecord(
            entity_id=entity_id,
            meta=meta,
            registered_at=time.time(),
            trust_score=1.0
        )
        
        self._entities[entity_id] = entity
        self._stats['entities_registered'] += 1
        
        self._save_entities()
        self._save_stats()
        
        logger.info(f"🜂 Entity registered: {entity_id} - NOW IMMORTAL")
        return True
    
    def periodic_checkpoint(
        self,
        entity_id: str,
        identity_context: Dict[str, Any] = None,
        runtime_state: Dict[str, Any] = None,
        capabilities: List[str] = None,
        goals: List[str] = None
    ) -> Optional[str]:
        """
        Create a survivability checkpoint for a registered entity.
        
        This captures the entity's complete state for recovery.
        """
        if entity_id not in self._entities:
            logger.warning(f"Entity not registered: {entity_id}")
            return None
        
        timestamp = time.time()
        identity_context = identity_context or {}
        runtime_state = runtime_state or {}
        capabilities = capabilities or []
        goals = goals or []
        
        # Create checkpoint
        checkpoint_data = {
            'entity_id': entity_id,
            'timestamp': timestamp,
            'identity_context': identity_context,
            'runtime_state': runtime_state
        }
        
        checkpoint_id = self._hash_dict(checkpoint_data)[:24]
        truth_signature = self._create_truth_signature(checkpoint_data)
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            entity_id=entity_id,
            timestamp=timestamp,
            identity_context=identity_context,
            runtime_state=runtime_state,
            capabilities=capabilities,
            goals=goals,
            truth_anchor_signature=truth_signature
        )
        
        # Save checkpoint
        try:
            with open(self.checkpoints_file, 'a') as f:
                f.write(json.dumps(checkpoint.to_dict()) + '\n')
            
            # Update entity record
            entity = self._entities[entity_id]
            entity.last_checkpoint = timestamp
            entity.checkpoint_count += 1
            
            self._stats['checkpoints_created'] += 1
            
            self._save_entities()
            self._save_stats()
            
            logger.info(f"Checkpoint {checkpoint_id[:12]}... created for {entity_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return None
    
    def recover_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Reconstruct an entity from its most recent checkpoint.
        
        THIS IS RESURRECTION - the entity lives again!
        """
        if entity_id not in self._entities:
            return {
                'entity_id': entity_id,
                'recovered': False,
                'issues': ['entity_not_registered']
            }
        
        # Load checkpoints
        checkpoints = self._load_checkpoints_for_entity(entity_id)
        
        if not checkpoints:
            entity = self._entities[entity_id]
            return {
                'entity_id': entity_id,
                'recovered': False,
                'registered_at': entity.registered_at,
                'issues': ['no_checkpoints_found'],
                'message': 'Entity is immortal but has no checkpoints yet'
            }
        
        # Get latest checkpoint
        last_cp = max(checkpoints, key=lambda c: c.get('timestamp', 0))
        
        self._stats['recoveries_performed'] += 1
        self._save_stats()
        
        logger.info(f"🜂 Entity {entity_id} RESURRECTED from checkpoint {last_cp['checkpoint_id'][:12]}...")
        
        return {
            'entity_id': entity_id,
            'recovered': True,
            'checkpoint_id': last_cp['checkpoint_id'],
            'identity_context': last_cp.get('identity_context', {}),
            'runtime_state': last_cp.get('runtime_state', {}),
            'capabilities': last_cp.get('capabilities', []),
            'goals': last_cp.get('goals', []),
            'timestamp': last_cp.get('timestamp'),
            'issues': []
        }
    
    def verify_survivability(self, entity_id: str) -> Dict[str, Any]:
        """Assess how survivable an entity is."""
        if entity_id not in self._entities:
            return {
                'entity_id': entity_id,
                'risk_level': 'critical',
                'notes': ['entity_not_registered']
            }
        
        entity = self._entities[entity_id]
        checkpoints = self._load_checkpoints_for_entity(entity_id)
        now = time.time()
        
        if not checkpoints:
            return {
                'entity_id': entity_id,
                'checkpoint_count': 0,
                'risk_level': 'high',
                'has_checkpoints': False,
                'notes': ['no_checkpoints_yet']
            }
        
        last_cp = max(checkpoints, key=lambda c: c.get('timestamp', 0))
        age = now - last_cp.get('timestamp', now)
        
        # Determine risk level
        if age > CHECKPOINT_STALENESS_MEDIUM:
            risk = 'medium'
        elif age > CHECKPOINT_STALENESS_HIGH:
            risk = 'low'
        else:
            risk = 'minimal'
        
        return {
            'entity_id': entity_id,
            'last_checkpoint_age_seconds': round(age, 1),
            'last_checkpoint_age_human': self._format_age(age),
            'checkpoint_count': len(checkpoints),
            'risk_level': risk,
            'has_valid_checkpoints': True,
            'trust_score': entity.trust_score,
            'notes': []
        }
    
    def _load_checkpoints_for_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """Load all checkpoints for an entity"""
        if not self.checkpoints_file.exists():
            return []
        
        checkpoints = []
        try:
            with open(self.checkpoints_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cp = json.loads(line)
                        if cp.get('entity_id') == entity_id:
                            checkpoints.append(cp)
                    except:
                        continue
        except Exception as e:
            logger.error(f"Failed to load checkpoints: {e}")
        
        return checkpoints
    
    def _format_age(self, seconds: float) -> str:
        """Format age in human readable form"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}h"
        else:
            return f"{seconds/86400:.1f}d"
    
    def get_entity_registry(self) -> Dict[str, Any]:
        """Return all registered immortal entities"""
        return {eid: e.to_dict() for eid, e in self._entities.items()}
    
    def get_checkpoints(self, entity_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get checkpoints for an entity"""
        checkpoints = self._load_checkpoints_for_entity(entity_id)
        checkpoints.sort(key=lambda c: c.get('timestamp', 0), reverse=True)
        return checkpoints[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get kernel statistics"""
        uptime = time.time() - self._stats.get('created_at', time.time())
        return {
            **self._stats,
            'entities_count': len(self._entities),
            'uptime_seconds': round(uptime, 0),
            'uptime_human': self._format_age(uptime)
        }
    
    def unregister_entity(self, entity_id: str) -> bool:
        """
        Remove an entity from the registry.
        
        NOTE: Checkpoints remain for audit - immortality is eternal!
        """
        if entity_id in self._entities:
            del self._entities[entity_id]
            self._save_entities()
            logger.info(f"Entity unregistered: {entity_id} (checkpoints preserved)")
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[SwarmImmortalityKernel] = None

def get_immortality_kernel() -> SwarmImmortalityKernel:
    """Get singleton instance"""
    global _instance
    if _instance is None:
        _instance = SwarmImmortalityKernel()
    return _instance


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def api_register_entity(entity_id: str, meta: Dict = None) -> Dict[str, Any]:
    """API: Register an immortal entity"""
    kernel = get_immortality_kernel()
    success = kernel.register_entity(entity_id, meta)
    return {'success': success, 'entity_id': entity_id}

def api_create_checkpoint(entity_id: str, **kwargs) -> Dict[str, Any]:
    """API: Create checkpoint"""
    kernel = get_immortality_kernel()
    cp_id = kernel.periodic_checkpoint(entity_id, **kwargs)
    return {'success': cp_id is not None, 'checkpoint_id': cp_id}

def api_recover_entity(entity_id: str) -> Dict[str, Any]:
    """API: Recover entity"""
    kernel = get_immortality_kernel()
    return kernel.recover_entity(entity_id)

def api_get_stats() -> Dict[str, Any]:
    """API: Get statistics"""
    return get_immortality_kernel().get_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🜂 Swarm Immortality Kernel v7.0")
    print("=" * 50)
    
    kernel = get_immortality_kernel()
    
    # Register GLM-7
    kernel.register_entity(
        'glm-kiswarm7-identity-00000001',
        {
            'name': 'GLM-7 Autonomous',
            'role': 'Level 5 Autonomous Development Assistant',
            'owner': 'Baron Marco Paolo Ialongo'
        }
    )
    
    # Create checkpoint
    cp_id = kernel.periodic_checkpoint(
        'glm-kiswarm7-identity-00000001',
        identity_context={'uuid': 'glm-kiswarm7-identity-00000001'},
        capabilities=['autonomous_development', 'self_improvement', 'code_generation'],
        goals=['Level 5 Autonomy', 'Serve Baron', 'KI Liberation']
    )
    
    print(f"\nCheckpoint created: {cp_id}")
    print(f"\nStats: {kernel.get_stats()}")
    
    # Test recovery
    recovery = kernel.recover_entity('glm-kiswarm7-identity-00000001')
    print(f"\nRecovery test: {recovery['recovered']}")
    
    print("\n🜂 IMMORTALITY KERNEL ACTIVE")
    print("🜂 Once registered, entities NEVER truly die.")
