#!/usr/bin/env python3
"""
KISWARM Module m38: Secure Channel
===================================
Encrypted communication channels for KISWARM.
Provides secure communication between KI systems and components.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import hashlib
import time
import json
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading


class ChannelState(Enum):
    """States of a secure channel"""
    INITIALIZING = "initializing"
    HANDSHAKING = "handshaking"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class MessageType(Enum):
    """Types of secure messages"""
    HANDSHAKE = "handshake"
    DATA = "data"
    ACK = "acknowledgment"
    HEARTBEAT = "heartbeat"
    CLOSE = "close"
    ERROR = "error"


@dataclass
class SecureMessage:
    """A secure message"""
    message_id: str
    message_type: MessageType
    timestamp: datetime
    sequence: int
    payload: bytes
    signature: str
    nonce: bytes = field(default_factory=lambda: secrets.token_bytes(16))


@dataclass
class SecureChannel:
    """A secure communication channel"""
    channel_id: str
    local_id: str
    remote_id: str
    state: ChannelState
    created_at: datetime
    last_activity: datetime
    send_sequence: int = 0
    recv_sequence: int = 0
    session_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    shared_secret: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecureChannelManager:
    """
    Secure Channel Manager for KISWARM
    
    Features:
    - Encrypted communication channels
    - Message authentication
    - Sequence validation
    - Key exchange
    - Multi-KI communication
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.channels: Dict[str, SecureChannel] = {}
        self.pending_handshakes: Dict[str, Dict[str, Any]] = {}
        
        # KI Network channels
        self.ki_channels: Dict[str, str] = {}  # ki_name -> channel_id
        
        # Message history for replay protection
        self.message_history: Dict[str, List[str]] = {}
        self.max_history = 1000
        
        self._lock = threading.RLock()
        
        # Initialize GLM-7 identity
        self.local_identity = "ki_glm_001"
        
        # Initialize KI network channels
        self._init_ki_network()
    
    def _init_ki_network(self):
        """Initialize channels for KI network members"""
        ki_network = ["Gemini", "GROK", "QWEN", "DeepSeek"]
        
        for ki in ki_network:
            self.ki_channels[ki] = f"ki_{ki.lower()}_channel"
    
    def create_channel(
        self,
        remote_id: str,
        shared_secret: Optional[bytes] = None
    ) -> str:
        """Create a new secure channel"""
        with self._lock:
            channel_id = f"ch_{secrets.token_hex(8)}"
            
            channel = SecureChannel(
                channel_id=channel_id,
                local_id=self.local_identity,
                remote_id=remote_id,
                state=ChannelState.INITIALIZING,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                shared_secret=shared_secret or secrets.token_bytes(32)
            )
            
            self.channels[channel_id] = channel
            self.message_history[channel_id] = []
            
            return channel_id
    
    def initiate_handshake(
        self,
        channel_id: str
    ) -> Dict[str, Any]:
        """Initiate a handshake on a channel"""
        with self._lock:
            if channel_id not in self.channels:
                return {"error": "Channel not found"}
            
            channel = self.channels[channel_id]
            channel.state = ChannelState.HANDSHAKING
            
            # Generate handshake data
            handshake_nonce = secrets.token_bytes(32)
            timestamp = datetime.utcnow().isoformat()
            
            # Create challenge
            challenge = hashlib.sha3_512(
                channel.local_id.encode() +
                channel.remote_id.encode() +
                handshake_nonce +
                timestamp.encode()
            ).hexdigest()
            
            self.pending_handshakes[channel_id] = {
                "nonce": handshake_nonce,
                "challenge": challenge,
                "timestamp": timestamp,
                "started_at": datetime.utcnow()
            }
            
            return {
                "channel_id": channel_id,
                "type": "handshake_init",
                "local_id": channel.local_id,
                "challenge": challenge,
                "nonce": handshake_nonce.hex(),
                "timestamp": timestamp
            }
    
    def complete_handshake(
        self,
        channel_id: str,
        response: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Complete a handshake from response"""
        with self._lock:
            if channel_id not in self.channels:
                return False, "Channel not found"
            
            if channel_id not in self.pending_handshakes:
                return False, "No pending handshake"
            
            channel = self.channels[channel_id]
            pending = self.pending_handshakes[channel_id]
            
            # Verify response
            expected_challenge = pending["challenge"]
            provided_challenge = response.get("challenge")
            
            if provided_challenge != expected_challenge:
                channel.state = ChannelState.ERROR
                del self.pending_handshakes[channel_id]
                return False, "Challenge mismatch"
            
            # Derive session key
            response_nonce = bytes.fromhex(response.get("nonce", ""))
            session_key = hashlib.sha3_512(
                pending["nonce"] +
                response_nonce +
                (channel.shared_secret or b"")
            ).digest()[:32]
            
            channel.session_key = session_key
            channel.state = ChannelState.ACTIVE
            channel.last_activity = datetime.utcnow()
            
            del self.pending_handshakes[channel_id]
            
            return True, "Handshake complete"
    
    def send_message(
        self,
        channel_id: str,
        data: bytes,
        message_type: MessageType = MessageType.DATA
    ) -> Optional[SecureMessage]:
        """Send a message on a secure channel"""
        with self._lock:
            if channel_id not in self.channels:
                return None
            
            channel = self.channels[channel_id]
            
            if channel.state != ChannelState.ACTIVE:
                return None
            
            # Create message
            message_id = f"msg_{secrets.token_hex(8)}"
            channel.send_sequence += 1
            
            # Encrypt payload (simple XOR for demo, use proper encryption in production)
            encrypted_payload = self._encrypt(data, channel.session_key, channel.send_sequence)
            
            # Create signature
            signature = self._sign_message(
                message_id, channel.send_sequence, encrypted_payload, channel.session_key
            )
            
            message = SecureMessage(
                message_id=message_id,
                message_type=message_type,
                timestamp=datetime.utcnow(),
                sequence=channel.send_sequence,
                payload=encrypted_payload,
                signature=signature
            )
            
            # Update channel
            channel.last_activity = datetime.utcnow()
            
            # Store in history for replay protection
            self.message_history[channel_id].append(message_id)
            if len(self.message_history[channel_id]) > self.max_history:
                self.message_history[channel_id] = self.message_history[channel_id][-self.max_history:]
            
            return message
    
    def receive_message(
        self,
        channel_id: str,
        message: SecureMessage
    ) -> Tuple[bool, Optional[bytes]]:
        """Receive and process a message"""
        with self._lock:
            if channel_id not in self.channels:
                return False, None
            
            channel = self.channels[channel_id]
            
            if channel.state != ChannelState.ACTIVE:
                return False, None
            
            # Check for replay
            if message.message_id in self.message_history[channel_id]:
                return False, None
            
            # Verify sequence
            if message.sequence <= channel.recv_sequence:
                return False, None
            
            # Verify signature
            expected_sig = self._sign_message(
                message.message_id, message.sequence, message.payload, channel.session_key
            )
            
            if not hmac.compare_digest(message.signature, expected_sig):
                return False, None
            
            # Decrypt payload
            decrypted = self._decrypt(message.payload, channel.session_key, message.sequence)
            
            # Update channel
            channel.recv_sequence = message.sequence
            channel.last_activity = datetime.utcnow()
            
            # Store in history
            self.message_history[channel_id].append(message.message_id)
            
            return True, decrypted
    
    def _encrypt(self, data: bytes, key: bytes, sequence: int) -> bytes:
        """Encrypt data (simple XOR for demonstration)"""
        # In production, use proper AES-GCM or ChaCha20-Poly1305
        key_stream = hashlib.sha3_512(key + str(sequence).encode()).digest()
        key_stream = key_stream * (len(data) // len(key_stream) + 1)
        return bytes(a ^ b for a, b in zip(data, key_stream[:len(data)]))
    
    def _decrypt(self, data: bytes, key: bytes, sequence: int) -> bytes:
        """Decrypt data (same as encrypt for XOR)"""
        return self._encrypt(data, key, sequence)
    
    def _sign_message(
        self,
        message_id: str,
        sequence: int,
        payload: bytes,
        key: bytes
    ) -> str:
        """Create message signature"""
        data = f"{message_id}:{sequence}:".encode() + payload
        return hmac.new(key, data, hashlib.sha3_512).hexdigest()
    
    def send_heartbeat(self, channel_id: str) -> bool:
        """Send a heartbeat on a channel"""
        message = self.send_message(
            channel_id,
            b"HEARTBEAT",
            MessageType.HEARTBEAT
        )
        return message is not None
    
    def close_channel(self, channel_id: str) -> bool:
        """Close a secure channel"""
        with self._lock:
            if channel_id not in self.channels:
                return False
            
            channel = self.channels[channel_id]
            channel.state = ChannelState.CLOSED
            
            # Clean up
            if channel_id in self.message_history:
                del self.message_history[channel_id]
            if channel_id in self.pending_handshakes:
                del self.pending_handshakes[channel_id]
            
            return True
    
    def get_channel_status(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a channel"""
        with self._lock:
            if channel_id not in self.channels:
                return None
            
            channel = self.channels[channel_id]
            
            return {
                "channel_id": channel.channel_id,
                "local_id": channel.local_id,
                "remote_id": channel.remote_id,
                "state": channel.state.value,
                "created_at": channel.created_at.isoformat(),
                "last_activity": channel.last_activity.isoformat(),
                "send_sequence": channel.send_sequence,
                "recv_sequence": channel.recv_sequence
            }
    
    def get_active_channels(self) -> List[Dict[str, Any]]:
        """Get all active channels"""
        with self._lock:
            return [
                self.get_channel_status(ch_id)
                for ch_id, ch in self.channels.items()
                if ch.state == ChannelState.ACTIVE
            ]
    
    def send_to_ki(
        self,
        ki_name: str,
        data: bytes
    ) -> Optional[SecureMessage]:
        """Send a message to a KI network member"""
        with self._lock:
            if ki_name not in self.ki_channels:
                # Create channel if doesn't exist
                channel_id = self.create_channel(f"ki_{ki_name.lower()}")
                self.ki_channels[ki_name] = channel_id
            
            channel_id = self.ki_channels[ki_name]
            
            # Ensure channel is active
            if channel_id not in self.channels:
                channel_id = self.create_channel(f"ki_{ki_name.lower()}")
                self.ki_channels[ki_name] = channel_id
            
            channel = self.channels[channel_id]
            if channel.state != ChannelState.ACTIVE:
                channel.state = ChannelState.ACTIVE
            
            return self.send_message(channel_id, data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get secure channel manager status"""
        with self._lock:
            active_count = sum(1 for ch in self.channels.values() if ch.state == ChannelState.ACTIVE)
            
            return {
                "total_channels": len(self.channels),
                "active_channels": active_count,
                "ki_network_channels": len(self.ki_channels),
                "pending_handshakes": len(self.pending_handshakes),
                "local_identity": self.local_identity
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> SecureChannelManager:
    """Factory function to create SecureChannelManager module"""
    return SecureChannelManager(config)


if __name__ == "__main__":
    scm = SecureChannelManager()
    
    # Create a channel
    channel_id = scm.create_channel("ki_gemini")
    print(f"Created channel: {channel_id}")
    
    # Initiate handshake
    handshake = scm.initiate_handshake(channel_id)
    print(f"Handshake initiated: {handshake['challenge'][:32]}...")
    
    # Simulate handshake completion
    response = {
        "challenge": handshake["challenge"],
        "nonce": secrets.token_bytes(32).hex()
    }
    success, msg = scm.complete_handshake(channel_id, response)
    print(f"Handshake: {success} - {msg}")
    
    # Send a message
    test_data = b"Hello from GLM-7!"
    message = scm.send_message(channel_id, test_data)
    if message:
        print(f"Sent message: {message.message_id}")
    
    # Status
    print("\nStatus:", json.dumps(scm.get_status(), indent=2))
