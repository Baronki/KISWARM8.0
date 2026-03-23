"""
Layer 0: Local Master API
Direct connection to KIBank Flask API
"""

from typing import Dict, Any, Optional
import aiohttp
import time
import logging

from .base_layer import MeshLayer, LayerResponse, LayerStatus

logger = logging.getLogger('KISWARM.Mesh.Layer0')


class Layer0LocalMaster(MeshLayer):
    """Layer 0: Local Master API - Direct Flask connection"""
    
    DEFAULT_API_URL = "http://localhost:5001/kibank"
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
        **kwargs
    ):
        super().__init__(
            layer_id=0,
            name="Local Master API",
            priority=1,
            timeout_seconds=timeout_seconds,
            **kwargs
        )
        self.api_url = api_url or self.DEFAULT_API_URL
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                base_url=self.api_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
            )
        return self._session
    
    async def execute(self, task: Dict[str, Any]) -> LayerResponse:
        start_time = time.monotonic()
        operation = task.get('operation', '')
        params = task.get('params', {})
        
        endpoint_map = {
            'auth/login': ('/auth/login', 'POST'),
            'auth/register': ('/auth/register', 'POST'),
            'auth/verify': ('/auth/verify', 'GET'),
            'banking/transfer': ('/banking/transfer', 'POST'),
            'banking/balance': ('/banking/balance', 'GET'),
            'investment/invest': ('/investment/invest', 'POST'),
            'reputation/get': ('/reputation/get', 'GET'),
        }
        
        if operation not in endpoint_map:
            return LayerResponse(
                success=False,
                error=f"Unknown operation: {operation}",
                layer_id=self.layer_id,
                layer_name=self.name
            )
        
        endpoint, method = endpoint_map[operation]
        
        try:
            session = await self._get_session()
            
            if method == 'GET':
                async with session.get(endpoint, params=params) as response:
                    data = await response.json()
            else:
                async with session.post(endpoint, json=params) as response:
                    data = await response.json()
            
            latency_ms = (time.monotonic() - start_time) * 1000
            
            if response.status in (200, 201):
                return LayerResponse(
                    success=True,
                    data=data,
                    layer_id=self.layer_id,
                    layer_name=self.name,
                    latency_ms=latency_ms
                )
            else:
                return LayerResponse(
                    success=False,
                    error=data.get('error', f"HTTP {response.status}"),
                    layer_id=self.layer_id,
                    layer_name=self.name,
                    latency_ms=latency_ms
                )
        except Exception as e:
            return LayerResponse(
                success=False,
                error=str(e),
                layer_id=self.layer_id,
                layer_name=self.name,
                latency_ms=(time.monotonic() - start_time) * 1000
            )
    
    async def health_check(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get('/health', timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    self._status = LayerStatus.HEALTHY
                    return True
        except Exception:
            pass
        self._status = LayerStatus.OFFLINE
        return False
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
