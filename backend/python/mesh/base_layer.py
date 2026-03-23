"""
KISWARM Mesh Base Layer
Implements Circuit Breaker Pattern for fault tolerance
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class LayerMetrics:
    """Performance metrics for a mesh layer"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_latency_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests


@dataclass
class LayerConfig:
    """Configuration for a mesh layer"""
    name: str
    priority: int  # Lower = higher priority
    timeout_ms: int = 30000
    failure_threshold: int = 5
    recovery_timeout_ms: int = 60000
    half_open_max_calls: int = 3
    enabled: bool = True


class BaseLayer(ABC):
    """
    Abstract base class for all mesh layers.
    Implements circuit breaker pattern for fault tolerance.
    """
    
    def __init__(self, config: LayerConfig):
        self.config = config
        self.metrics = LayerMetrics()
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
        
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def priority(self) -> int:
        return self.config.priority
    
    @property
    def is_available(self) -> bool:
        """Check if layer is available for requests"""
        if not self.config.enabled:
            return False
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            elapsed_ms = (time.time() - self.last_state_change) * 1000
            if elapsed_ms >= self.config.recovery_timeout_ms:
                self._transition_to_half_open()
                return True
            return False
        return True
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"[{self.name}] Circuit OPEN - too many failures")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(f"[{self.name}] Circuit HALF_OPEN - testing recovery")
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.half_open_calls = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            logger.info(f"[{self.name}] Circuit CLOSED - recovered")
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.metrics.consecutive_failures = 0
    
    async def execute(self, request: Callable, *args, **kwargs) -> Any:
        """
        Execute a request through this layer with circuit breaker protection.
        """
        async with self._lock:
            if not self.is_available:
                raise LayerUnavailableError(f"Layer {self.name} is not available")
            
            # Handle half-open state
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise LayerUnavailableError(f"Layer {self.name} in half-open, max calls reached")
                self.half_open_calls += 1
        
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_impl(request, *args, **kwargs),
                timeout=self.config.timeout_ms / 1000
            )
            
            # Record success
            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)
            
            return result
            
        except asyncio.TimeoutError:
            self._record_failure("Timeout")
            raise LayerTimeoutError(f"Layer {self.name} timed out")
        except Exception as e:
            self._record_failure(str(e))
            raise
    
    @abstractmethod
    async def _execute_impl(self, request: Callable, *args, **kwargs) -> Any:
        """Implementation-specific execution logic"""
        pass
    
    def _record_success(self, latency_ms: float):
        """Record a successful request"""
        self.metrics.successful_requests += 1
        self.metrics.total_latency_ms += latency_ms
        self.metrics.last_success_time = time.time()
        self.metrics.consecutive_failures = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_closed()
    
    def _record_failure(self, error: str):
        """Record a failed request"""
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = time.time()
        self.metrics.consecutive_failures += 1
        
        logger.error(f"[{self.name}] Request failed: {error} "
                    f"(consecutive: {self.metrics.consecutive_failures})")
        
        if self.metrics.consecutive_failures >= self.config.failure_threshold:
            self._transition_to_open()
    
    def get_status(self) -> Dict:
        """Get layer status for monitoring"""
        return {
            "name": self.name,
            "priority": self.priority,
            "state": self.state.value,
            "available": self.is_available,
            "enabled": self.config.enabled,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": round(self.metrics.success_rate * 100, 2),
                "avg_latency_ms": round(self.metrics.avg_latency_ms, 2),
                "consecutive_failures": self.metrics.consecutive_failures
            }
        }
    
    def reset(self):
        """Reset layer to initial state"""
        self.state = CircuitState.CLOSED
        self.metrics = LayerMetrics()
        self.last_state_change = time.time()
        self.half_open_calls = 0
        logger.info(f"[{self.name}] Layer reset to initial state")


class LayerUnavailableError(Exception):
    """Raised when a layer is not available"""
    pass


class LayerTimeoutError(Exception):
    """Raised when a layer request times out"""
    pass
