"""
KISWARM Mesh Layer Tests
Tests for 6-Layer Zero-Failure Mesh Architecture - v6.3.5
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'python'))

from mesh.base_layer import BaseLayer, LayerConfig, CircuitState, LayerUnavailableError
from mesh.zero_failure_mesh import ZeroFailureMesh, MeshConfig, MeshExhaustedError
from mesh.layer0_local import Layer0LocalMaster
from mesh.layer4_email import Layer4EmailBeacon


class TestBaseLayer:
    """Tests for BaseLayer circuit breaker"""
    
    def test_layer_config_defaults(self):
        """Test default layer configuration"""
        config = LayerConfig(name="test", priority=1)
        assert config.name == "test"
        assert config.priority == 1
        assert config.timeout_ms == 30000
        assert config.failure_threshold == 5
        assert config.enabled is True
    
    def test_layer_initial_state(self):
        """Test layer starts in CLOSED state"""
        config = LayerConfig(name="test", priority=1)
        
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return {"result": "ok"}
        
        layer = TestLayer(config)
        assert layer.state == CircuitState.CLOSED
        assert layer.is_available is True
    
    @pytest.mark.asyncio
    async def test_layer_successful_request(self):
        """Test successful request execution"""
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return await request()
        
        config = LayerConfig(name="test", priority=1)
        layer = TestLayer(config)
        
        async def success_request():
            return {"data": "success"}
        
        result = await layer.execute(success_request)
        assert result == {"data": "success"}
        assert layer.metrics.successful_requests == 1
    
    @pytest.mark.asyncio
    async def test_layer_circuit_opens_on_failures(self):
        """Test circuit opens after threshold failures"""
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                raise Exception("Simulated failure")
        
        config = LayerConfig(
            name="test", 
            priority=1,
            failure_threshold=3
        )
        layer = TestLayer(config)
        
        async def failing_request():
            pass
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                await layer.execute(failing_request)
        
        # Circuit should be open now
        assert layer.state == CircuitState.OPEN
        assert layer.is_available is False
    
    def test_layer_status_reporting(self):
        """Test layer status reporting"""
        config = LayerConfig(name="test", priority=1)
        
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return {}
        
        layer = TestLayer(config)
        status = layer.get_status()
        
        assert "name" in status
        assert "state" in status
        assert "metrics" in status
        assert status["name"] == "test"


class TestZeroFailureMesh:
    """Tests for Zero-Failure Mesh coordinator"""
    
    @pytest.fixture
    def mesh(self):
        """Create a mesh with test config"""
        return ZeroFailureMesh(MeshConfig(max_retries=1))
    
    def test_mesh_priority_ordering(self, mesh):
        """Test layers are sorted by priority"""
        class MockLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return {"layer": self.name}
        
        layer1 = MockLayer(LayerConfig(name="low", priority=10))
        layer2 = MockLayer(LayerConfig(name="high", priority=1))
        layer3 = MockLayer(LayerConfig(name="mid", priority=5))
        
        mesh.register_layer(layer1)
        mesh.register_layer(layer2)
        mesh.register_layer(layer3)
        
        # Should be sorted by priority
        assert mesh.layers[0].name == "high"
        assert mesh.layers[1].name == "mid"
        assert mesh.layers[2].name == "low"
    
    @pytest.mark.asyncio
    async def test_mesh_failover(self, mesh):
        """Test failover to next layer on failure"""
        class FailingLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                raise Exception("Layer failed")
        
        class SuccessLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return {"success": True, "layer": self.name}
        
        failing = FailingLayer(LayerConfig(name="failing", priority=1))
        success = SuccessLayer(LayerConfig(name="success", priority=2))
        
        mesh.register_layer(failing)
        mesh.register_layer(success)
        await mesh.initialize()
        
        result = await mesh.execute(lambda: None)
        assert result["success"] is True
        assert result["layer"] == "success"
    
    @pytest.mark.asyncio
    async def test_mesh_all_layers_fail(self, mesh):
        """Test exception when all layers fail"""
        class FailingLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                raise Exception("All layers failed")
        
        layer1 = FailingLayer(LayerConfig(name="layer1", priority=1))
        layer2 = FailingLayer(LayerConfig(name="layer2", priority=2))
        
        mesh.register_layer(layer1)
        mesh.register_layer(layer2)
        await mesh.initialize()
        
        with pytest.raises(MeshExhaustedError):
            await mesh.execute(lambda: None)
    
    def test_mesh_status(self, mesh):
        """Test mesh status reporting"""
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return {}
        
        mesh.register_layer(TestLayer(LayerConfig(name="test", priority=1)))
        
        status = mesh.get_status()
        assert "total_layers" in status
        assert "available_layers" in status
        assert status["total_layers"] == 1


class TestLayer0LocalMaster:
    """Tests for Layer 0 Local Master API"""
    
    def test_layer0_initialization(self):
        """Test Layer 0 initialization"""
        layer = Layer0LocalMaster(base_url="http://localhost:5000")
        assert layer.name == "local_master"
        assert layer.priority == 0
        assert layer.base_url == "http://localhost:5000"
    
    def test_layer0_status(self):
        """Test Layer 0 status reporting"""
        layer = Layer0LocalMaster()
        status = layer.get_status()
        
        assert status["name"] == "local_master"
        assert status["priority"] == 0
        assert status["layer_type"] == "local_master"


class TestLayer4EmailBeacon:
    """Tests for Layer 4 Email Beacon"""
    
    def test_layer4_initialization(self):
        """Test Layer 4 initialization"""
        layer = Layer4EmailBeacon(
            smtp_host="smtp.test.com",
            beacon_address="beacon@test.com"
        )
        assert layer.name == "email_beacon"
        assert layer.priority == 4
    
    def test_layer4_status(self):
        """Test Layer 4 status reporting"""
        layer = Layer4EmailBeacon(beacon_address="test@test.com")
        status = layer.get_status()
        
        assert status["name"] == "email_beacon"
        assert status["priority"] == 4
        assert status["layer_type"] == "email_beacon"


class TestMeshIntegration:
    """Integration tests for complete mesh"""
    
    @pytest.mark.asyncio
    async def test_full_mesh_initialization(self):
        """Test complete mesh with all layers"""
        mesh = ZeroFailureMesh()
        
        # Register all 6 layers
        mesh.register_layer(Layer0LocalMaster())
        mesh.register_layer(Layer4EmailBeacon(beacon_address="test@test.com"))
        
        await mesh.initialize()
        
        status = mesh.get_status()
        assert status["initialized"] is True
        assert status["total_layers"] == 2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
