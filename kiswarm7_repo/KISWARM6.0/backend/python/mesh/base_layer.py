"""
KISWARM Mesh Layer Base Class
Abstract foundation for all 6 mesh layers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger('KISWARM.Mesh')


class LayerStatus(Enum):
    """Mesh layer operational status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class LayerResponse:
    """Standardized response from mesh layer operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    layer_id: int = 0
    layer_name: str = "Unknown"
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    fallback_used: bool = False
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'layer_id': self.layer_id,
            'layer_name': self.layer_name,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp.isoformat(),
            'fallback_used': self.fallback_used,
            'signature': self.signature
        }


class MeshLayer(ABC):
    """Abstract base class for KISWARM mesh layers"""
    
    def __init__(
        self,
        layer_id: int,
        name: str,
        priority: int = 1,
        timeout_seconds: float = 30.0,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_reset_seconds: float = 60.0
    ):
        self.layer_id = layer_id
        self.name = name
        self.priority = priority
        self.timeout_seconds = timeout_seconds
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_reset_seconds = circuit_breaker_reset_seconds
        self._status = LayerStatus.HEALTHY
        self._consecutive_failures = 0
        self._circuit_opened_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    @property
    def status(self) -> LayerStatus:
        return self._status
    
    @property
    def is_available(self) -> bool:
        if self._status == LayerStatus.CIRCUIT_OPEN:
            if self._circuit_opened_at:
                elapsed = (datetime.utcnow() - self._circuit_opened_at).total_seconds()
                if elapsed >= self.circuit_breaker_reset_seconds:
                    return True
            return False
        return self._status in (LayerStatus.HEALTHY, LayerStatus.DEGRADED)
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> LayerResponse:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
    
    async def execute_with_metrics(self, task: Dict[str, Any]) -> LayerResponse:
        if not self.is_available:
            return LayerResponse(
                success=False,
                error=f"Layer {self.name} not available",
                layer_id=self.layer_id,
                layer_name=self.name
            )
        
        start_time = time.monotonic()
        
        try:
            response = await asyncio.wait_for(
                self.execute(task),
                timeout=self.timeout_seconds
            )
            await self._record_success()
            return response
        except asyncio.TimeoutError:
            return await self._record_failure(f"Timeout after {self.timeout_seconds}s")
        except Exception as e:
            return await self._record_failure(str(e))
    
    async def _record_success(self):
        async with self._lock:
            self._consecutive_failures = 0
            self._status = LayerStatus.HEALTHY
    
    async def _record_failure(self, error: str) -> LayerResponse:
        async with self._lock:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.circuit_breaker_threshold:
                self._status = LayerStatus.CIRCUIT_OPEN
                self._circuit_opened_at = datetime.utcnow()
            elif self._consecutive_failures > 1:
                self._status = LayerStatus.DEGRADED
        
        return LayerResponse(
            success=False,
            error=error,
            layer_id=self.layer_id,
            layer_name=self.name
        )
    
    async def reset_circuit_breaker(self):
        async with self._lock:
            self._consecutive_failures = 0
            self._circuit_opened_at = None
            self._status = LayerStatus.HEALTHY
    
    def get_status_report(self) -> Dict[str, Any]:
        return {
            'layer_id': self.layer_id,
            'name': self.name,
            'status': self._status.value,
            'priority': self.priority,
            'is_available': self.is_available,
            'consecutive_failures': self._consecutive_failures
        }
