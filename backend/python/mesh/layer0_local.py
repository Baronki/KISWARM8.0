"""
KISWARM Mesh Layer 0: Local Master API
Direct Flask connection for primary operations

Priority: 1 (Highest)
Latency: <10ms
Reliability: 99.9% (local)
"""

import asyncio
import aiohttp
from typing import Any, Callable, Optional
import logging

from .base_layer import BaseLayer, LayerConfig

logger = logging.getLogger(__name__)


class Layer0LocalMaster(BaseLayer):
    """
    Layer 0: Direct connection to local Flask Master API
    
    Primary layer for all KISWARM operations when locally available.
    Lowest latency, highest reliability for local deployments.
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        config = LayerConfig(
            name="local_master",
            priority=0,  # Highest priority
            timeout_ms=10000,
            failure_threshold=3,
            recovery_timeout_ms=30000
        )
        super().__init__(config)
        
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_ms / 1000)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-KISWARM-Layer": "L0-LocalMaster"
                }
            )
        logger.info(f"[L0] Initialized with base URL: {self.base_url}")
    
    async def _execute_impl(self, request: Callable, *args, **kwargs) -> Any:
        """Execute request via local Flask API"""
        if self.session is None or self.session.closed:
            await self.initialize()
        
        # Extract endpoint and method from kwargs or use defaults
        endpoint = kwargs.pop('endpoint', '/api/v1/execute')
        method = kwargs.pop('method', 'POST').upper()
        data = kwargs.pop('data', None)
        params = kwargs.pop('params', None)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, 
                url, 
                json=data, 
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 503:
                    # Service unavailable - trigger failover
                    raise ConnectionError(f"Master API unavailable: {response.status}")
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection to Master API failed: {e}")
    
    async def health_check(self) -> bool:
        """Check if local master is healthy"""
        try:
            if self.session is None or self.session.closed:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def shutdown(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("[L0] Shutdown complete")
    
    def get_status(self) -> dict:
        status = super().get_status()
        status["base_url"] = self.base_url
        status["layer_type"] = "local_master"
        return status
