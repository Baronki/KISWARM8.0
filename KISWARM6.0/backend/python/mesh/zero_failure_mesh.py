"""
KISWARM Zero-Failure Mesh Coordinator
6-Layer redundant architecture for guaranteed operation execution
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import hashlib
import json
import logging

from .base_layer import MeshLayer, LayerResponse, LayerStatus

logger = logging.getLogger('KISWARM.ZeroFailureMesh')


@dataclass
class MeshConfig:
    """Configuration for Zero-Failure Mesh"""
    max_retries_per_layer: int = 2
    global_timeout_seconds: float = 120.0
    parallel_layer_attempts: int = 2
    enable_emergency_dead_drop: bool = True
    audit_all_operations: bool = True


@dataclass
class MeshOperationResult:
    """Result of a mesh operation"""
    success: bool
    data: Optional[Dict[str, Any]]
    primary_layer: int
    successful_layer: Optional[int]
    attempts: List[Dict[str, Any]]
    total_latency_ms: float
    timestamp: datetime
    operation_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'primary_layer': self.primary_layer,
            'successful_layer': self.successful_layer,
            'attempts': self.attempts,
            'total_latency_ms': self.total_latency_ms,
            'timestamp': self.timestamp.isoformat(),
            'operation_hash': self.operation_hash
        }


class ZeroFailureMesh:
    """
    Zero-Failure Mesh Coordinator
    
    Implements 6-layer redundant architecture with guaranteed execution.
    Operations cascade through layers in priority order until one succeeds.
    """
    
    def __init__(
        self,
        layers: List[MeshLayer],
        config: Optional[MeshConfig] = None
    ):
        self.layers = sorted(layers, key=lambda l: l.priority)
        self.config = config or MeshConfig()
        self._operation_history: List[MeshOperationResult] = []
        self._lock = asyncio.Lock()
        
        logger.info(f"ZeroFailureMesh initialized with {len(self.layers)} layers")
    
    def get_layer(self, layer_id: int) -> Optional[MeshLayer]:
        for layer in self.layers:
            if layer.layer_id == layer_id:
                return layer
        return None
    
    def get_available_layers(self) -> List[MeshLayer]:
        return [l for l in self.layers if l.is_available]
    
    async def execute_with_fallback(
        self,
        task: Dict[str, Any],
        required_layers: Optional[List[int]] = None
    ) -> MeshOperationResult:
        """Execute task with automatic fallback through layers"""
        import time
        start_time = time.monotonic()
        attempts: List[Dict[str, Any]] = []
        successful_layer: Optional[int] = None
        result_data: Optional[Dict[str, Any]] = None
        
        operation_hash = self._hash_operation(task)
        logger.info(f"Executing operation {operation_hash[:16]}...")
        
        layers_to_try = self.get_available_layers()
        
        for layer in layers_to_try:
            if not layer.is_available:
                continue
            
            for retry in range(self.config.max_retries_per_layer):
                response = await layer.execute_with_metrics(task)
                
                attempt_record = {
                    'layer_id': layer.layer_id,
                    'layer_name': layer.name,
                    'retry': retry,
                    'success': response.success,
                    'latency_ms': response.latency_ms,
                    'error': response.error,
                    'timestamp': datetime.utcnow().isoformat()
                }
                attempts.append(attempt_record)
                
                if response.success:
                    successful_layer = layer.layer_id
                    result_data = response.data
                    break
            
            if successful_layer is not None:
                break
        
        if successful_layer is None and self.config.enable_emergency_dead_drop:
            email_layer = self.get_layer(4)
            if email_layer and email_layer.is_available:
                emergency_task = {
                    'operation': 'EMERGENCY_DEAD_DROP',
                    'original_task': task,
                    'previous_attempts': attempts
                }
                response = await email_layer.execute_with_metrics(emergency_task)
                if response.success:
                    successful_layer = 4
                    result_data = response.data
        
        total_latency = (time.monotonic() - start_time) * 1000
        
        return MeshOperationResult(
            success=successful_layer is not None,
            data=result_data,
            primary_layer=layers_to_try[0].layer_id if layers_to_try else -1,
            successful_layer=successful_layer,
            attempts=attempts,
            total_latency_ms=total_latency,
            timestamp=datetime.utcnow(),
            operation_hash=operation_hash
        )
    
    def _hash_operation(self, task: Dict[str, Any]) -> str:
        content = json.dumps(task, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_status_report(self) -> Dict[str, Any]:
        layer_reports = [layer.get_status_report() for layer in self.layers]
        available_count = sum(1 for l in self.layers if l.is_available)
        
        return {
            'mesh_version': '6.3.5',
            'codename': 'GWS_IRON_MOUNTAIN',
            'total_layers': len(self.layers),
            'available_layers': available_count,
            'availability_percentage': round(
                (available_count / len(self.layers)) * 100, 2
            ) if self.layers else 0,
            'layers': layer_reports
        }
    
    async def health_check_all(self) -> Dict[int, bool]:
        results = {}
        for layer in self.layers:
            try:
                results[layer.layer_id] = await layer.health_check()
            except Exception:
                results[layer.layer_id] = False
        return results
    
    async def reset_all_circuit_breakers(self) -> None:
        for layer in self.layers:
            await layer.reset_circuit_breaker()
        logger.info("All circuit breakers reset")
