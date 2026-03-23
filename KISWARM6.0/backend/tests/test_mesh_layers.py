"""
Tests for KISWARM Zero-Failure Mesh Layers
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


class TestBaseLayer:
    """Tests for the base MeshLayer class"""
    
    def test_layer_status_enum(self):
        """Test LayerStatus enum values"""
        from mesh.base_layer import LayerStatus
        
        assert LayerStatus.HEALTHY.value == "healthy"
        assert LayerStatus.DEGRADED.value == "degraded"
        assert LayerStatus.OFFLINE.value == "offline"
        assert LayerStatus.CIRCUIT_OPEN.value == "circuit_open"
    
    def test_layer_response_creation(self):
        """Test LayerResponse dataclass"""
        from mesh.base_layer import LayerResponse
        
        response = LayerResponse(
            success=True,
            data={'result': 'ok'},
            layer_id=0,
            layer_name="Test Layer",
            latency_ms=50.0
        )
        
        assert response.success is True
        assert response.data == {'result': 'ok'}
        assert response.error is None
    
    def test_layer_response_to_dict(self):
        """Test LayerResponse serialization"""
        from mesh.base_layer import LayerResponse
        
        response = LayerResponse(
            success=False,
            error="Test error",
            layer_id=1,
            layer_name="Gemini CLI"
        )
        
        result = response.to_dict()
        
        assert result['success'] is False
        assert result['error'] == "Test error"
        assert result['layer_id'] == 1


class TestLayer0LocalMaster:
    """Tests for Layer 0: Local Master API"""
    
    def test_initialization(self):
        """Test Layer 0 initialization"""
        from mesh.layer0_local import Layer0LocalMaster
        
        layer = Layer0LocalMaster(
            api_url="http://localhost:5001/kibank",
            timeout_seconds=10.0
        )
        
        assert layer.api_url == "http://localhost:5001/kibank"
        assert layer.timeout_seconds == 10.0
        assert layer.priority == 1
        assert layer.layer_id == 0
    
    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self):
        """Test executing unknown operation returns error"""
        from mesh.layer0_local import Layer0LocalMaster
        
        layer = Layer0LocalMaster()
        
        response = await layer.execute({
            'operation': 'unknown_operation',
            'params': {}
        })
        
        assert response.success is False
        assert "Unknown operation" in response.error


class TestLayer4EmailBeacon:
    """Tests for Layer 4: Email Beacon"""
    
    def test_initialization(self):
        """Test Layer 4 initialization"""
        from mesh.layer4_email import Layer4EmailBeacon, EmailConfig
        
        config = EmailConfig(
            username="test@example.com",
            password="test_password"
        )
        layer = Layer4EmailBeacon(
            config=config,
            node_id="TEST-NODE"
        )
        
        assert layer.node_id == "TEST-NODE"
        assert layer.config.username == "test@example.com"
        assert layer.priority == 5
    
    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self):
        """Test executing unknown operation"""
        from mesh.layer4_email import Layer4EmailBeacon
        
        layer = Layer4EmailBeacon()
        
        response = await layer.execute({
            'operation': 'unknown_op',
            'params': {}
        })
        
        assert response.success is False
        assert "Unknown" in response.error


class TestZeroFailureMesh:
    """Tests for Zero-Failure Mesh Coordinator"""
    
    def test_initialization(self):
        """Test mesh initialization"""
        from mesh.zero_failure_mesh import ZeroFailureMesh, MeshConfig
        
        mesh = ZeroFailureMesh([], MeshConfig())
        
        assert mesh.config.max_retries_per_layer == 2
        assert mesh.config.enable_emergency_dead_drop is True
    
    def test_get_status_report(self):
        """Test getting mesh status report"""
        from mesh.zero_failure_mesh import ZeroFailureMesh
        
        mesh = ZeroFailureMesh([])
        
        report = mesh.get_status_report()
        
        assert report['mesh_version'] == '6.3.5'
        assert report['codename'] == 'GWS_IRON_MOUNTAIN'


class TestCognitiveMemory:
    """Tests for Cognitive Memory (MuninnDB)"""
    
    def test_memory_type_enum(self):
        """Test MemoryType enum values"""
        from cognitive.muninn_adapter import MemoryType
        
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SECURITY.value == "security"
        assert MemoryType.FINANCIAL.value == "financial"
    
    def test_memory_event_creation(self):
        """Test MemoryEvent dataclass"""
        from cognitive.muninn_adapter import MemoryEvent, MemoryType
        
        event = MemoryEvent(
            event_id="test-001",
            event_type=MemoryType.OPERATIONAL,
            content={'operation': 'transfer', 'amount': 1000}
        )
        
        assert event.event_id == "test-001"
        assert event.event_type == MemoryType.OPERATIONAL
        assert event.importance == 0.5
        assert len(event.associations) == 0
    
    def test_memory_event_serialization(self):
        """Test MemoryEvent serialization"""
        from cognitive.muninn_adapter import MemoryEvent, MemoryType
        
        event = MemoryEvent(
            event_id="test-002",
            event_type=MemoryType.SECURITY,
            content={'alert': 'intrusion'},
            importance=0.9,
            tags={'security', 'alert'}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_id'] == "test-002"
        assert event_dict['event_type'] == 'security'
        assert 'security' in event_dict['tags']


class TestEbbinghausDecay:
    """Tests for Ebbinghaus decay calculations"""
    
    def test_retention_calculation(self):
        """Test retention calculation"""
        from cognitive.muninn_adapter import MemoryEvent, MemoryType, EbbinghausDecay
        
        event = MemoryEvent(
            event_id="test",
            event_type=MemoryType.OPERATIONAL,
            content={'test': 'data'}
        )
        
        retention = EbbinghausDecay.calculate_retention(event)
        
        assert 0.0 <= retention <= 1.0
        assert retention > 0.9  # Fresh memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
