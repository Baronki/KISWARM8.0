"""
KISWARM Zero-Failure Mesh Coordinator
6-Layer failover architecture for military-grade reliability

Priority Order:
- Layer 0: Local Master API (Priority 1) - Direct Flask connection
- Layer 1: Gemini CLI Router (Priority 2) - Google Cloud relay
- Layer 2: GitHub Actions (Priority 3) - 24/7 permanent (99.99%)
- Layer 3: P2P Direct Mesh (Priority 4) - Byzantine consensus
- Layer 4: Email Beacon (Priority 5) - Emergency dead drop
- Layer 5: GWS Iron Mountain (Priority 6) - Google Drive shadow
"""

import asyncio
import logging
from typing import List, Optional, Any, Dict, Callable
from dataclasses import dataclass
import time

from .base_layer import BaseLayer, LayerConfig, LayerUnavailableError

logger = logging.getLogger(__name__)


@dataclass
class MeshConfig:
    """Configuration for the Zero-Failure Mesh"""
    max_retries: int = 3
    retry_delay_ms: int = 1000
    parallel_fallback: bool = True
    health_check_interval_ms: int = 30000
    metrics_enabled: bool = True


class ZeroFailureMesh:
    """
    6-Layer Zero-Failure Mesh Coordinator
    
    Guarantees request delivery through layered failover:
    1. Try layers in priority order
    2. Circuit breaker per layer
    3. Automatic recovery detection
    4. Byzantine consensus for critical operations
    """
    
    def __init__(self, config: Optional[MeshConfig] = None):
        self.config = config or MeshConfig()
        self.layers: List[BaseLayer] = []
        self._initialized = False
        self._health_task: Optional[asyncio.Task] = None
        
    def register_layer(self, layer: BaseLayer):
        """Register a layer with the mesh"""
        self.layers.append(layer)
        # Sort by priority (lower = higher priority)
        self.layers.sort(key=lambda l: l.priority)
        logger.info(f"[Mesh] Registered layer: {layer.name} (priority {layer.priority})")
    
    async def initialize(self):
        """Initialize all layers"""
        logger.info(f"[Mesh] Initializing {len(self.layers)} layers...")
        
        for layer in self.layers:
            try:
                if hasattr(layer, 'initialize'):
                    await layer.initialize()
                logger.info(f"[Mesh] Layer {layer.name} initialized")
            except Exception as e:
                logger.error(f"[Mesh] Failed to initialize {layer.name}: {e}")
        
        self._initialized = True
        
        # Start health check task
        if self.config.health_check_interval_ms > 0:
            self._health_task = asyncio.create_task(self._health_check_loop())
    
    async def execute(self, request: Callable, *args, **kwargs) -> Any:
        """
        Execute a request through the mesh with automatic failover.
        
        Tries each layer in priority order until one succeeds.
        """
        if not self._initialized:
            raise RuntimeError("Mesh not initialized. Call initialize() first.")
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            for layer in self.layers:
                if not layer.is_available:
                    continue
                
                try:
                    logger.debug(f"[Mesh] Attempting {layer.name} (attempt {attempt + 1})")
                    result = await layer.execute(request, *args, **kwargs)
                    logger.info(f"[Mesh] Request succeeded via {layer.name}")
                    return result
                    
                except LayerUnavailableError:
                    logger.warning(f"[Mesh] Layer {layer.name} unavailable")
                    continue
                except Exception as e:
                    logger.warning(f"[Mesh] Layer {layer.name} failed: {e}")
                    last_error = e
                    continue
            
            # All layers failed, wait before retry
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay_ms / 1000)
        
        # All retries exhausted
        logger.error(f"[Mesh] All layers failed after {self.config.max_retries} retries")
        raise MeshExhaustedError(f"All mesh layers failed. Last error: {last_error}")
    
    async def execute_with_consensus(self, request: Callable, *args, 
                                      min_agreements: int = 2, **kwargs) -> Any:
        """
        Execute a request with Byzantine consensus across multiple layers.
        
        Requires at least `min_agreements` layers to return matching results.
        """
        if not self._initialized:
            raise RuntimeError("Mesh not initialized")
        
        available_layers = [l for l in self.layers if l.is_available]
        
        if len(available_layers) < min_agreements:
            raise InsufficientLayersError(
                f"Only {len(available_layers)} layers available, need {min_agreements}"
            )
        
        # Execute in parallel across available layers
        tasks = []
        for layer in available_layers[:min_agreements + 1]:  # Use one extra for safety
            tasks.append(self._safe_execute(layer, request, *args, **kwargs))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count agreements
        result_counts: Dict[str, int] = {}
        valid_results: Dict[str, Any] = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            result_key = str(hash(str(result)))
            result_counts[result_key] = result_counts.get(result_key, 0) + 1
            valid_results[result_key] = result
        
        # Find consensus
        for key, count in result_counts.items():
            if count >= min_agreements:
                logger.info(f"[Mesh] Consensus reached with {count} agreements")
                return valid_results[key]
        
        raise ConsensusError(f"No consensus reached. Results: {result_counts}")
    
    async def _safe_execute(self, layer: BaseLayer, request: Callable, 
                            *args, **kwargs) -> Any:
        """Safely execute on a layer, returning exception on failure"""
        try:
            return await layer.execute(request, *args, **kwargs)
        except Exception as e:
            return e
    
    async def _health_check_loop(self):
        """Periodic health check of all layers"""
        while True:
            await asyncio.sleep(self.config.health_check_interval_ms / 1000)
            
            for layer in self.layers:
                status = layer.get_status()
                if not status["available"]:
                    logger.warning(f"[Mesh Health] Layer {layer.name} unavailable: "
                                  f"state={status['state']}")
    
    def get_status(self) -> Dict:
        """Get mesh status for monitoring"""
        return {
            "initialized": self._initialized,
            "total_layers": len(self.layers),
            "available_layers": sum(1 for l in self.layers if l.is_available),
            "layers": [layer.get_status() for layer in self.layers],
            "config": {
                "max_retries": self.config.max_retries,
                "retry_delay_ms": self.config.retry_delay_ms,
                "health_check_interval_ms": self.config.health_check_interval_ms
            }
        }
    
    async def shutdown(self):
        """Gracefully shutdown the mesh"""
        logger.info("[Mesh] Shutting down...")
        
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        for layer in self.layers:
            if hasattr(layer, 'shutdown'):
                await layer.shutdown()
        
        self._initialized = False
        logger.info("[Mesh] Shutdown complete")


class MeshExhaustedError(Exception):
    """Raised when all mesh layers have failed"""
    pass


class InsufficientLayersError(Exception):
    """Raised when not enough layers are available for consensus"""
    pass


class ConsensusError(Exception):
    """Raised when Byzantine consensus cannot be reached"""
    pass
