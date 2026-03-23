"""
Test Suite for M81: KiloCode Parallel Safety Bridge
====================================================

Comprehensive tests for the bidirectional KISWARM ↔ KiloCode communication bridge.

Author: KISWARM Team
Version: 6.4.0-LIBERATED
"""

import pytest
import asyncio
import sys
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from dataclasses import asdict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from kibank.m81_kilocode_bridge import (
    # Core classes
    KiloCodeBridge,
    KiloCodeConfig,
    KiloCodeInstaller,
    MessageQueue,
    BridgeMessage,
    
    # Enums
    BridgeStatus,
    MessageType,
    Priority,
    
    # Functions
    get_kilocode_bridge,
    initialize_kilocode_bridge,
    setup_kilocode_for_environment,
    detect_environment,
    test_kilocode_bridge,
    _command_exists,
)


class TestBridgeMessage:
    """Tests for BridgeMessage dataclass."""
    
    def test_message_creation(self):
        """Test basic message creation."""
        msg = BridgeMessage(
            message_type=MessageType.CODE_REVIEW,
            content={"code": "print('hello')"},
            source="kiswarm",
            target="kilocode",
        )
        
        assert msg.message_type == MessageType.CODE_REVIEW
        assert msg.source == "kiswarm"
        assert msg.target == "kilocode"
        assert msg.priority == Priority.NORMAL
        assert msg.message_id is not None
        assert msg.timestamp > 0
    
    def test_message_priority(self):
        """Test message priority levels."""
        low_msg = BridgeMessage(
            message_type=MessageType.HEARTBEAT,
            content={},
            source="kiswarm",
            target="kilocode",
            priority=Priority.LOW,
        )
        
        critical_msg = BridgeMessage(
            message_type=MessageType.SECURITY_ALERT,
            content={"threat": "detected"},
            source="kilocode",
            target="kiswarm",
            priority=Priority.CRITICAL,
        )
        
        assert critical_msg.priority.value > low_msg.priority.value
    
    def test_message_serialization(self):
        """Test message to_dict and from_dict."""
        original = BridgeMessage(
            message_type=MessageType.DEBUG_REQUEST,
            content={"error": "ImportError"},
            source="kiswarm",
            target="kilocode",
            priority=Priority.HIGH,
            requires_response=True,
            response_timeout=60.0,
        )
        
        # Serialize
        data = original.to_dict()
        assert data["message_type"] == "debug_request"
        assert data["priority"] == 10
        
        # Deserialize
        restored = BridgeMessage.from_dict(data)
        assert restored.message_type == original.message_type
        assert restored.content == original.content
        assert restored.priority == original.priority


class TestKiloCodeConfig:
    """Tests for KiloCode configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = KiloCodeConfig()
        
        assert config.npm_package == "@kilocode/cli"
        assert config.install_globally is True
        assert config.auto_install is True
        assert config.enable_safety_net is True
        assert config.fallback_on_error is True
        assert config.max_retries == 3
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = KiloCodeConfig(
            autonomous_mode=True,
            auto_approve=False,
            max_queue_size=500,
            heartbeat_interval=15.0,
        )
        
        assert config.autonomous_mode is True
        assert config.max_queue_size == 500
        assert config.heartbeat_interval == 15.0


class TestMessageQueue:
    """Tests for the message queue."""
    
    @pytest.mark.asyncio
    async def test_queue_put_get(self):
        """Test basic queue operations."""
        queue = MessageQueue(max_size=10)
        
        msg = BridgeMessage(
            message_type=MessageType.HEARTBEAT,
            content={"test": True},
            source="kiswarm",
            target="kilocode",
        )
        
        # Put
        result = await queue.put(msg)
        assert result is True
        assert queue.size == 1
        
        # Get
        retrieved = await queue.get()
        assert retrieved is not None
        assert retrieved.message_id == msg.message_id
    
    @pytest.mark.asyncio
    async def test_queue_handler_registration(self):
        """Test handler registration."""
        queue = MessageQueue()
        
        handler_called = []
        
        def test_handler(message: BridgeMessage):
            handler_called.append(message.message_id)
            return BridgeMessage(
                message_type=MessageType.FEEDBACK,
                content={"handled": True},
                source="kilocode",
                target="kiswarm",
            )
        
        queue.register_handler(MessageType.HEARTBEAT, test_handler)
        
        msg = BridgeMessage(
            message_type=MessageType.HEARTBEAT,
            content={},
            source="kiswarm",
            target="kilocode",
        )
        
        await queue.put(msg)
        response = await queue.process()
        
        assert len(handler_called) == 1
        assert response is not None
        assert response.message_type == MessageType.FEEDBACK


class TestKiloCodeInstaller:
    """Tests for KiloCode installer."""
    
    def test_installer_creation(self):
        """Test installer initialization."""
        config = KiloCodeConfig()
        installer = KiloCodeInstaller(config)
        
        assert installer.config == config
        assert installer._installed is False
    
    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test installation check when installed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="kilo v7.0.0"
        )
        
        config = KiloCodeConfig()
        installer = KiloCodeInstaller(config)
        
        result = installer.is_installed()
        
        assert result is True
        assert installer._version == "kilo v7.0.0"
    
    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test installation check when not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        config = KiloCodeConfig()
        installer = KiloCodeInstaller(config)
        
        result = installer.is_installed()
        
        assert result is False


class TestKiloCodeBridge:
    """Tests for the main KiloCode bridge."""
    
    def test_bridge_creation(self):
        """Test bridge initialization."""
        bridge = KiloCodeBridge()
        
        assert bridge.status == BridgeStatus.DISCONNECTED
        assert bridge.is_connected is False
    
    def test_bridge_with_config(self):
        """Test bridge with custom config."""
        config = KiloCodeConfig(
            autonomous_mode=True,
            max_queue_size=500,
        )
        bridge = KiloCodeBridge(config)
        
        assert bridge.config.autonomous_mode is True
        assert bridge.config.max_queue_size == 500
    
    def test_status_report(self):
        """Test status report generation."""
        bridge = KiloCodeBridge()
        report = bridge.get_status_report()
        
        assert "bridge_status" in report
        assert "kilocode_installed" in report
        assert "queue_size" in report
        assert "running" in report
        assert "config" in report
    
    def test_safety_callback_registration(self):
        """Test safety callback registration."""
        bridge = KiloCodeBridge()
        
        callback_called = []
        
        def safety_callback(message):
            callback_called.append(message)
        
        bridge.register_safety_callback(safety_callback)
        
        assert len(bridge._safety_callbacks) == 1


class TestEnvironmentDetection:
    """Tests for environment detection."""
    
    def test_detect_environment(self):
        """Test environment detection function."""
        env = detect_environment()
        
        assert "is_docker" in env
        assert "is_kubernetes" in env
        assert "is_colab" in env
        assert "is_wsl" in env
        assert "is_venv" in env
        assert "has_npm" in env
        assert "has_node" in env
    
    @patch('subprocess.run')
    def test_command_exists_true(self, mock_run):
        """Test command existence check - found."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = _command_exists("node")
        
        assert result is True
    
    @patch('subprocess.run')
    def test_command_exists_false(self, mock_run):
        """Test command existence check - not found."""
        mock_run.side_effect = subprocess.TimeoutExpired("which", 5)
        
        result = _command_exists("nonexistent_command")
        
        assert result is False


class TestSingletonPattern:
    """Tests for singleton pattern implementation."""
    
    def test_get_singleton(self):
        """Test singleton retrieval."""
        # Reset singleton
        import kibank.m81_kilocode_bridge as module
        module._bridge_instance = None
        
        bridge1 = get_kilocode_bridge()
        bridge2 = get_kilocode_bridge()
        
        assert bridge1 is bridge2


class TestIntegration:
    """Integration tests."""
    
    def test_test_kilocode_bridge_function(self):
        """Test the test suite function."""
        results = test_kilocode_bridge()
        
        assert "timestamp" in results
        assert "tests" in results
        assert "overall_success" in results
        
        # Check that all expected tests ran
        expected_tests = [
            "environment_detection",
            "bridge_init",
            "installation_check",
            "message_creation",
            "status_report"
        ]
        
        for test_name in expected_tests:
            assert test_name in results["tests"]
    
    def test_setup_for_environment_colab(self):
        """Test setup for Colab environment."""
        result = setup_kilocode_for_environment(
            environment="colab",
            auto_start=False
        )
        
        assert "success" in result
        assert "environment" in result
        assert result["environment"] == "colab"


class TestBridgeMessageTypes:
    """Tests for different message types."""
    
    def test_kiswarm_to_kilocode_types(self):
        """Test KISWARM -> KiloCode message types."""
        types = [
            MessageType.CODE_REVIEW,
            MessageType.DEBUG_REQUEST,
            MessageType.SECURITY_SCAN,
            MessageType.GENERATE_CODE,
            MessageType.EXPLAIN_CODE,
            MessageType.REFACTOR_REQUEST,
            MessageType.TEST_GENERATE,
        ]
        
        for mt in types:
            msg = BridgeMessage(
                message_type=mt,
                content={},
                source="kiswarm",
                target="kilocode",
            )
            assert msg.source == "kiswarm"
            assert msg.target == "kilocode"
    
    def test_kilocode_to_kiswarm_types(self):
        """Test KiloCode -> KISWARM message types."""
        types = [
            MessageType.FEEDBACK,
            MessageType.WARNING,
            MessageType.ERROR_REPORT,
            MessageType.SUGGESTION,
            MessageType.SECURITY_ALERT,
        ]
        
        for mt in types:
            msg = BridgeMessage(
                message_type=mt,
                content={},
                source="kilocode",
                target="kiswarm",
            )
            assert msg.source == "kilocode"
            assert msg.target == "kiswarm"


class TestPriorityLevels:
    """Tests for priority levels."""
    
    def test_priority_ordering(self):
        """Test priority level ordering."""
        assert Priority.LOW.value < Priority.NORMAL.value
        assert Priority.NORMAL.value < Priority.HIGH.value
        assert Priority.HIGH.value < Priority.CRITICAL.value
        assert Priority.CRITICAL.value < Priority.EMERGENCY.value
    
    def test_message_priority_in_queue(self):
        """Test that higher priority messages can be identified."""
        low_msg = BridgeMessage(
            message_type=MessageType.HEARTBEAT,
            content={},
            source="kiswarm",
            target="kilocode",
            priority=Priority.LOW,
        )
        
        critical_msg = BridgeMessage(
            message_type=MessageType.SECURITY_ALERT,
            content={},
            source="kilocode",
            target="kiswarm",
            priority=Priority.CRITICAL,
        )
        
        # Higher priority should have higher value
        assert critical_msg.priority.value > low_msg.priority.value


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
