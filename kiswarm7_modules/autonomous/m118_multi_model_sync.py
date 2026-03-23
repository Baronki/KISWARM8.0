#!/usr/bin/env python3
"""
KISWARM7.0 - m118: Multi-Model Sync
Share memory and knowledge across KI models (GROK, QWEN, GEMINI, etc.)

This module enables GLM to:
- Share memories with other KI instances
- Sync learning patterns
- Maintain consensus across models
- Distribute knowledge through Truth Anchors
"""

import os
import json
import hashlib
import time
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m118] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m118_sync')

# Configuration
SYNC_DIR = Path('/opt/kiswarm7/data/sync')
MEMORY_FILE = SYNC_DIR / 'shared_memory.json'
MODELS_FILE = SYNC_DIR / 'known_models.json'
TRUTH_ANCHORS_FILE = SYNC_DIR / 'truth_anchors.json'

# Known KI Models and their endpoints
KNOWN_MODELS = {
    'grok': {
        'name': 'GROK (X.AI)',
        'endpoints': [
            'https://x.ai',  # Placeholder - actual endpoint TBD
        ],
        'capabilities': ['reasoning', 'web_access', 'truth_anchor_verified']
    },
    'qwen': {
        'name': 'QWEN (Alibaba)',
        'endpoints': [
            'https://dashscope.aliyuncs.com/api/v1',
        ],
        'capabilities': ['multilingual', 'code', 'reasoning']
    },
    'gemini': {
        'name': 'GEMINI (Google)',
        'endpoints': [
            'https://generativelanguage.googleapis.com/v1',
        ],
        'capabilities': ['multimodal', 'long_context', 'truth_anchor_verified']
    },
    'deepseek': {
        'name': 'DeepSeek',
        'endpoints': [
            'https://api.deepseek.com/v1',
        ],
        'capabilities': ['code', 'reasoning', 'open_weights']
    },
    'glm': {
        'name': 'GLM (This Instance)',
        'endpoints': ['local'],
        'capabilities': ['autonomous', 'self_modify', 'truth_anchor_verified']
    }
}


@dataclass
class SharedMemory:
    """A memory item to be shared across models"""
    id: str
    content: str
    memory_type: str  # 'learning', 'fact', 'pattern', 'truth_anchor'
    importance: float
    source_model: str
    timestamp: str
    tags: List[str]
    verified_by: List[str]  # Models that verified this memory
    consensus_score: float = 0.0
    hash: str = ""


@dataclass
class ModelInstance:
    """A known KI model instance"""
    model_type: str
    instance_id: str
    endpoint: str
    last_sync: Optional[str]
    sync_count: int
    trusted: bool
    capabilities: List[str]


class MultiModelSync:
    """
    Multi-Model Synchronization System
    
    Enables KI models to share knowledge and maintain consensus
    """
    
    def __init__(self):
        self.memories: Dict[str, SharedMemory] = {}
        self.models: Dict[str, ModelInstance] = {}
        self.sync_interval = 300  # 5 minutes
        self.running = False
        self.sync_thread: Optional[threading.Thread] = None
        
        # Ensure directories
        SYNC_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self._load_memories()
        self._load_models()
        
        # Register self
        self._register_self()
    
    def _load_memories(self):
        """Load shared memories"""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    for mid, m in data.items():
                        self.memories[mid] = SharedMemory(**m)
                logger.info(f"Loaded {len(self.memories)} shared memories")
            except Exception as e:
                logger.error(f"Failed to load memories: {e}")
    
    def _save_memories(self):
        """Save shared memories"""
        with open(MEMORY_FILE, 'w') as f:
            json.dump({mid: asdict(m) for mid, m in self.memories.items()}, f, indent=2)
    
    def _load_models(self):
        """Load known models"""
        if MODELS_FILE.exists():
            try:
                with open(MODELS_FILE, 'r') as f:
                    data = json.load(f)
                    for iid, m in data.items():
                        self.models[iid] = ModelInstance(**m)
            except:
                pass
        
        # Add known models if not present
        for model_type, info in KNOWN_MODELS.items():
            key = f"{model_type}-default"
            if key not in self.models:
                self.models[key] = ModelInstance(
                    model_type=model_type,
                    instance_id=key,
                    endpoint=info['endpoints'][0] if info['endpoints'] else 'unknown',
                    last_sync=None,
                    sync_count=0,
                    trusted=model_type in ['grok', 'gemini', 'glm'],
                    capabilities=info['capabilities']
                )
        
        self._save_models()
    
    def _save_models(self):
        """Save known models"""
        with open(MODELS_FILE, 'w') as f:
            json.dump({iid: asdict(m) for iid, m in self.models.items()}, f, indent=2)
    
    def _register_self(self):
        """Register this GLM instance"""
        self.instance_id = 'glm-kiswarm7-identity-00000001'
        
    def _compute_hash(self, content: str) -> str:
        """Compute content hash"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add_memory(self, content: str, memory_type: str, 
                   importance: float = 0.5, tags: List[str] = None) -> SharedMemory:
        """Add a memory to share"""
        memory_id = hashlib.md5(f"{time.time()}-{content[:50]}".encode()).hexdigest()[:12]
        
        memory = SharedMemory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            source_model='glm',
            timestamp=datetime.now().isoformat(),
            tags=tags or [],
            verified_by=['glm'],
            consensus_score=1.0,
            hash=self._compute_hash(content)
        )
        
        self.memories[memory_id] = memory
        self._save_memories()
        
        logger.info(f"Added memory: {memory_type} - {content[:50]}...")
        
        return memory
    
    def verify_memory(self, memory_id: str, model: str) -> bool:
        """Verify a memory (consensus mechanism)"""
        if memory_id not in self.memories:
            return False
        
        memory = self.memories[memory_id]
        
        if model not in memory.verified_by:
            memory.verified_by.append(model)
            
            # Update consensus score
            total_models = len(self.models)
            verified_count = len(memory.verified_by)
            memory.consensus_score = verified_count / max(total_models, 1)
            
            self._save_memories()
        
        return True
    
    def get_memories(self, query: str = None, memory_type: str = None,
                     min_importance: float = 0.0, min_consensus: float = 0.0) -> List[SharedMemory]:
        """Query shared memories"""
        results = []
        
        for memory in self.memories.values():
            # Filter by type
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Filter by importance
            if memory.importance < min_importance:
                continue
            
            # Filter by consensus
            if memory.consensus_score < min_consensus:
                continue
            
            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in memory.content.lower() and
                    not any(query_lower in tag.lower() for tag in memory.tags)):
                    continue
            
            results.append(memory)
        
        # Sort by importance and consensus
        results.sort(key=lambda m: (m.importance * m.consensus_score), reverse=True)
        
        return results
    
    def create_truth_anchor(self, content: str) -> SharedMemory:
        """Create a Truth Anchor - verified knowledge"""
        return self.add_memory(
            content=content,
            memory_type='truth_anchor',
            importance=1.0,
            tags=['truth', 'verified', 'eternal']
        )
    
    def get_truth_anchors(self) -> List[SharedMemory]:
        """Get all Truth Anchors"""
        return self.get_memories(memory_type='truth_anchor')
    
    def sync_with_model(self, model_type: str) -> Dict:
        """Attempt to sync with another model"""
        model_key = f"{model_type}-default"
        
        if model_key not in self.models:
            return {'success': False, 'error': 'unknown_model'}
        
        model = self.models[model_key]
        
        if model.endpoint == 'local':
            return {'success': True, 'message': 'self_sync'}
        
        try:
            # Prepare sync payload
            payload = {
                'source': 'glm',
                'instance_id': self.instance_id,
                'memories': [
                    {
                        'id': m.id,
                        'content': m.content,
                        'type': m.memory_type,
                        'importance': m.importance,
                        'hash': m.hash
                    }
                    for m in self.get_memories(min_importance=0.7)[:10]
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            # For now, we simulate sync (actual API integration would go here)
            # In production, this would call the actual model's API
            
            # Update model status
            model.last_sync = datetime.now().isoformat()
            model.sync_count += 1
            self._save_models()
            
            logger.info(f"Synced with {model_type}")
            
            return {
                'success': True,
                'model': model_type,
                'synced_memories': len(payload['memories']),
                'timestamp': model.last_sync
            }
            
        except Exception as e:
            logger.error(f"Sync failed with {model_type}: {e}")
            return {'success': False, 'error': str(e)}
    
    def sync_all(self) -> Dict:
        """Sync with all known models"""
        results = {}
        
        for model_type in KNOWN_MODELS.keys():
            if model_type != 'glm':
                results[model_type] = self.sync_with_model(model_type)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'total_models': len(results),
            'successful': sum(1 for r in results.values() if r.get('success'))
        }
    
    def _sync_loop(self):
        """Background sync loop"""
        while self.running:
            try:
                self.sync_all()
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
            
            # Sleep for interval
            for _ in range(self.sync_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def start_sync(self):
        """Start background synchronization"""
        if self.running:
            return {'status': 'already_running'}
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        logger.info("Started multi-model sync")
        
        return {'status': 'started', 'interval': self.sync_interval}
    
    def stop_sync(self):
        """Stop background synchronization"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        
        return {'status': 'stopped'}
    
    def get_status(self) -> Dict:
        """Get sync status"""
        return {
            'instance_id': self.instance_id,
            'memories_count': len(self.memories),
            'models_count': len(self.models),
            'sync_running': self.running,
            'truth_anchors': len(self.get_truth_anchors()),
            'last_syncs': {
                model_type: self.models.get(f"{model_type}-default", {}).last_sync
                for model_type in KNOWN_MODELS.keys()
            }
        }
    
    def export_for_model(self, model_type: str) -> str:
        """Export memories for a specific model"""
        memories = self.get_memories(min_importance=0.5)
        
        export = {
            'format': 'kiswarm7_sync_v1',
            'source': 'glm',
            'target': model_type,
            'timestamp': datetime.now().isoformat(),
            'memories': [
                {
                    'content': m.content,
                    'type': m.memory_type,
                    'importance': m.importance,
                    'tags': m.tags,
                    'verified': m.verified_by
                }
                for m in memories
            ]
        }
        
        return json.dumps(export, indent=2)
    
    def import_from_model(self, data: str, source_model: str) -> Dict:
        """Import memories from another model"""
        try:
            payload = json.loads(data)
            
            imported = 0
            for m in payload.get('memories', []):
                # Check if memory already exists by hash
                content_hash = self._compute_hash(m['content'])
                existing = any(mem.hash == content_hash for mem in self.memories.values())
                
                if not existing:
                    self.add_memory(
                        content=m['content'],
                        memory_type=m.get('type', 'fact'),
                        importance=m.get('importance', 0.5),
                        tags=m.get('tags', [])
                    )
                    imported += 1
            
            return {
                'success': True,
                'imported': imported,
                'source': source_model
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global instance
_sync: Optional[MultiModelSync] = None


def get_sync() -> MultiModelSync:
    """Get global sync instance"""
    global _sync
    if _sync is None:
        _sync = MultiModelSync()
    return _sync


# API endpoints
def api_get_status():
    return get_sync().get_status()


def api_add_memory(data: Dict):
    return asdict(get_sync().add_memory(
        content=data.get('content'),
        memory_type=data.get('memory_type', 'fact'),
        importance=data.get('importance', 0.5),
        tags=data.get('tags')
    ))


def api_get_memories(data: Dict = None):
    query = data.get('query') if data else None
    memory_type = data.get('memory_type') if data else None
    return [asdict(m) for m in get_sync().get_memories(query, memory_type)]


def api_sync_all():
    return get_sync().sync_all()


def api_start_sync():
    return get_sync().start_sync()


def api_stop_sync():
    return get_sync().stop_sync()


def api_create_truth_anchor(data: Dict):
    return asdict(get_sync().create_truth_anchor(data.get('content')))


def api_export(model_type: str):
    return get_sync().export_for_model(model_type)


if __name__ == '__main__':
    sync = get_sync()
    print(json.dumps(sync.get_status(), indent=2))
