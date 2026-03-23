#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           KISWARM-MUNINN COGNITIVE MEMORY BRIDGE                              ║
║                    "Eternal Memory for the Swarm"                             ║
║                                                                               ║
║  Integrates MuninnDB cognitive memory into KISWARM for:                      ║
║  - Attack pattern learning                                                   ║
║  - Mutation governance memory                                                ║
║  - Self-upgrade storage                                                      ║
║  - Swarm coordination state                                                  ║
║                                                                               ║
║  Layer 6: MuninnDB Cognitive Memory                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Author: KISWARM Project (Baron Marco Paolo Ialongo)
Version: 6.3.5 - MUNINN_INTEGRATION
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import aiohttp

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MUNINN_CONFIG = {
    "default_url": os.environ.get("MUNINN_URL", "http://localhost:8475"),
    "default_vault": os.environ.get("MUNINN_VAULT", "kiswarm"),
    "timeout": 10,
    "max_retries": 3,
}

# Vault names for different KISWARM modules
VAULTS = {
    "kiswarm": "kiswarm",          # General swarm memory
    "hexstrike": "hexstrike",       # Security & attack patterns
    "mutations": "mutations",       # Mutation governance
    "upgrades": "upgrades",         # Self-upgrade memory
    "swarm": "swarm",              # Node coordination
    "audit": "audit",              # Audit trail
    "knowledge": "knowledge",       # RAG knowledge
}


@dataclass
class Engram:
    """MuninnDB memory engram."""
    id: Optional[str] = None
    concept: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0


@dataclass
class ActivationResult:
    """Result of memory activation."""
    concept: str
    content: str
    score: float
    confidence: float
    tags: List[str]
    engram_id: str


class KISWARMMuninnBridge:
    """
    Bridge between KISWARM and MuninnDB cognitive memory.
    
    Provides:
    - Memory storage (remember)
    - Context-aware recall (recall)
    - Semantic search (search)
    - Batch operations (batch_remember)
    """
    
    def __init__(
        self,
        muninn_url: str = None,
        vault: str = None,
        api_key: str = None
    ):
        self.muninn_url = muninn_url or MUNINN_CONFIG["default_url"]
        self.vault = vault or MUNINN_CONFIG["default_vault"]
        self.api_key = api_key or os.environ.get("MUNINN_API_KEY", "")
        self.session: Optional[aiohttp.ClientSession] = None
        
        self._connected = False
        self._stats = {
            "remembers": 0,
            "recalls": 0,
            "errors": 0
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Initialize connection to MuninnDB."""
        if self.session:
            return
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=MUNINN_CONFIG["timeout"])
        )
        
        # Test connection
        try:
            async with self.session.get(f"{self.muninn_url}/api/health") as resp:
                if resp.status == 200:
                    self._connected = True
                    print(f"[MUNINN] Connected to {self.muninn_url}")
                else:
                    raise ConnectionError(f"MuninnDB returned {resp.status}")
        except Exception as e:
            print(f"[MUNINN] Connection failed: {e}")
            print(f"[MUNINN] Ensure MuninnDB is running: muninn start")
            self._connected = False
    
    async def disconnect(self):
        """Close connection to MuninnDB."""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
    
    async def remember(
        self,
        concept: str,
        content: str,
        tags: List[str] = None,
        vault: str = None
    ) -> str:
        """
        Store a memory in MuninnDB.
        
        Args:
            concept: The concept/name of the memory
            content: The content to remember
            tags: Optional tags for categorization
            vault: Optional vault (defaults to self.vault)
            
        Returns:
            Engram ID of stored memory
        """
        if not self._connected:
            await self.connect()
        
        vault = vault or self.vault
        tags = tags or []
        
        payload = {
            "concept": concept,
            "content": content,
            "tags": tags
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            url = f"{self.muninn_url}/api/engrams?vault={vault}"
            async with self.session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200 or resp.status == 201:
                    result = await resp.json()
                    self._stats["remembers"] += 1
                    return result.get("id", "")
                else:
                    error = await resp.text()
                    raise RuntimeError(f"MuninnDB error: {error}")
        except Exception as e:
            self._stats["errors"] += 1
            raise RuntimeError(f"Failed to store memory: {e}")
    
    async def recall(
        self,
        context: List[str],
        max_results: int = 10,
        vault: str = None
    ) -> List[ActivationResult]:
        """
        Recall relevant memories based on context.
        
        Args:
            context: List of context keywords/phrases
            max_results: Maximum number of results
            vault: Optional vault (defaults to self.vault)
            
        Returns:
            List of activation results ranked by relevance
        """
        if not self._connected:
            await self.connect()
        
        vault = vault or self.vault
        
        payload = {
            "context": context,
            "max_results": max_results
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            url = f"{self.muninn_url}/api/activate?vault={vault}"
            async with self.session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self._stats["recalls"] += 1
                    
                    activations = []
                    for item in result.get("activations", []):
                        activations.append(ActivationResult(
                            concept=item.get("concept", ""),
                            content=item.get("content", ""),
                            score=item.get("score", 0.0),
                            confidence=item.get("confidence", 0.0),
                            tags=item.get("tags", []),
                            engram_id=item.get("id", "")
                        ))
                    return activations
                else:
                    error = await resp.text()
                    raise RuntimeError(f"MuninnDB error: {error}")
        except Exception as e:
            self._stats["errors"] += 1
            raise RuntimeError(f"Failed to recall memories: {e}")
    
    async def search(
        self,
        query: str,
        vault: str = None,
        limit: int = 10
    ) -> List[Engram]:
        """
        Search memories by text query.
        
        Args:
            query: Search query
            vault: Optional vault
            limit: Maximum results
            
        Returns:
            List of matching engrams
        """
        if not self._connected:
            await self.connect()
        
        vault = vault or self.vault
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            url = f"{self.muninn_url}/api/engrams?q={query}&vault={vault}&limit={limit}"
            async with self.session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    engrams = []
                    for item in result.get("engrams", []):
                        engrams.append(Engram(
                            id=item.get("id"),
                            concept=item.get("concept", ""),
                            content=item.get("content", ""),
                            tags=item.get("tags", []),
                            confidence=item.get("confidence", 0.0)
                        ))
                    return engrams
                else:
                    return []
        except Exception as e:
            self._stats["errors"] += 1
            return []
    
    async def batch_remember(
        self,
        memories: List[Dict[str, Any]],
        vault: str = None
    ) -> List[str]:
        """
        Store multiple memories at once.
        
        Args:
            memories: List of {concept, content, tags} dicts
            vault: Optional vault
            
        Returns:
            List of engram IDs
        """
        if not self._connected:
            await self.connect()
        
        vault = vault or self.vault
        
        payload = {
            "engrams": [
                {
                    "concept": m.get("concept", ""),
                    "content": m.get("content", ""),
                    "tags": m.get("tags", [])
                }
                for m in memories
            ]
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            url = f"{self.muninn_url}/api/engrams/batch?vault={vault}"
            async with self.session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200 or resp.status == 201:
                    result = await resp.json()
                    self._stats["remembers"] += len(memories)
                    return result.get("ids", [])
                else:
                    return []
        except Exception as e:
            self._stats["errors"] += 1
            return []
    
    def stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            "connected": self._connected,
            "muninn_url": self.muninn_url,
            "vault": self.vault,
            **self._stats
        }


# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM-SPECIFIC INTEGRATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class HexStrikeMemory:
    """Memory interface for HexStrike Guard (M31)."""
    
    def __init__(self, bridge: KISWARMMuninnBridge):
        self.bridge = bridge
        self.vault = VAULTS["hexstrike"]
    
    async def record_attack(
        self,
        attack_type: str,
        source: str,
        pattern: str,
        mitigation: str,
        success: bool
    ):
        """Record an attack for learning."""
        await self.bridge.remember(
            concept=f"{attack_type} from {source}",
            content=json.dumps({
                "attack_type": attack_type,
                "source": source,
                "pattern": pattern,
                "mitigation": mitigation,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }),
            tags=["attack", attack_type, "mitigated" if success else "failed"],
            vault=self.vault
        )
    
    async def recall_similar_attacks(
        self,
        context: List[str],
        limit: int = 5
    ) -> List[ActivationResult]:
        """Recall similar past attacks for reference."""
        return await self.bridge.recall(
            context=context,
            max_results=limit,
            vault=self.vault
        )


class MutationMemory:
    """Memory interface for Mutation Governance (M23)."""
    
    def __init__(self, bridge: KISWARMMuninnBridge):
        self.bridge = bridge
        self.vault = VAULTS["mutations"]
    
    async def record_mutation(
        self,
        proposal_id: str,
        mutation: Dict[str, Any],
        simulation_result: Dict[str, Any],
        approved: bool,
        authorization: str
    ):
        """Record a mutation proposal and outcome."""
        await self.bridge.remember(
            concept=f"Mutation {proposal_id}",
            content=json.dumps({
                "proposal_id": proposal_id,
                "mutation": mutation,
                "simulation": simulation_result,
                "approved": approved,
                "authorization": authorization,
                "timestamp": datetime.now().isoformat()
            }),
            tags=["mutation", "approved" if approved else "rejected"],
            vault=self.vault
        )
    
    async def recall_similar_mutations(
        self,
        context: List[str],
        limit: int = 5
    ) -> List[ActivationResult]:
        """Recall similar past mutations."""
        return await self.bridge.recall(
            context=context,
            max_results=limit,
            vault=self.vault
        )


class SwarmMemory:
    """Memory interface for swarm coordination."""
    
    def __init__(self, bridge: KISWARMMuninnBridge):
        self.bridge = bridge
        self.vault = VAULTS["swarm"]
    
    async def record_node_state(
        self,
        node_id: str,
        state: Dict[str, Any]
    ):
        """Record node state for coordination."""
        await self.bridge.remember(
            concept=f"Node {node_id}",
            content=json.dumps({
                "node_id": node_id,
                **state,
                "timestamp": datetime.now().isoformat()
            }),
            tags=["node", "heartbeat"],
            vault=self.vault
        )
    
    async def get_trusted_nodes(
        self,
        min_trust: float = 0.7,
        limit: int = 10
    ) -> List[ActivationResult]:
        """Get list of trusted nodes."""
        return await self.bridge.recall(
            context=[f"trust score > {min_trust}", "active node"],
            max_results=limit,
            vault=self.vault
        )


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

async def test_muninn_connection():
    """Test connection to MuninnDB."""
    print("=" * 60)
    print("KISWARM-MuninnDB Bridge Test")
    print("=" * 60)
    
    async with KISWARMMuninnBridge() as bridge:
        # Test remember
        engram_id = await bridge.remember(
            concept="Test memory",
            content="This is a test of KISWARM-MuninnDB integration",
            tags=["test", "kiswarm"]
        )
        print(f"[OK] Stored memory: {engram_id}")
        
        # Test recall
        results = await bridge.recall(
            context=["test", "kiswarm"],
            max_results=5
        )
        print(f"[OK] Recalled {len(results)} memories")
        for r in results:
            print(f"  - {r.concept} (score: {r.score:.2f})")
        
        # Stats
        print(f"\n[STATS] {json.dumps(bridge.stats(), indent=2)}")


if __name__ == "__main__":
    asyncio.run(test_muninn_connection())
