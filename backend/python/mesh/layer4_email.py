"""
KISWARM Mesh Layer 4: Email Beacon
Emergency dead drop for fail-safe communication

Priority: 5 (Emergency fallback)
Latency: 1-60 seconds
Reliability: 99.99% (email delivery)

Use case: Last resort when all other layers fail.
Messages are stored in email for later retrieval.
"""

import asyncio
import smtplib
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Callable, Optional
import logging
from datetime import datetime

from .base_layer import BaseLayer, LayerConfig

logger = logging.getLogger(__name__)


class Layer4EmailBeacon(BaseLayer):
    """
    Layer 4: Email Beacon for emergency communications
    
    Implements "dead drop" pattern:
    - Encodes requests as email payloads
    - Sends to monitored inbox
    - External system retrieves and processes
    - Response via email reply or separate channel
    """
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        beacon_address: str = "",
        sender_name: str = "KISWARM-Mesh"
    ):
        config = LayerConfig(
            name="email_beacon",
            priority=4,  # Emergency layer
            timeout_ms=30000,
            failure_threshold=3,
            recovery_timeout_ms=300000  # 5 minutes
        )
        super().__init__(config)
        
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.beacon_address = beacon_address
        self.sender_name = sender_name
        
    async def initialize(self):
        """Initialize SMTP connection (lazy)"""
        logger.info(f"[L4-Email] Initialized for beacon: {self.beacon_address}")
    
    async def _execute_impl(self, request: Callable, *args, **kwargs) -> Any:
        """
        Send request via email beacon.
        
        Note: This is asynchronous fire-and-forget by default.
        For synchronous responses, use the request_id to poll.
        """
        # Generate request ID for tracking
        request_id = kwargs.pop('request_id', self._generate_request_id())
        operation = kwargs.pop('operation', 'execute')
        payload = kwargs.pop('payload', {})
        
        # Encode the request
        message_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "payload": payload,
            "source": "KISWARM-Mesh-L4",
            "priority": "EMERGENCY"
        }
        
        # Send email
        await self._send_beacon_email(message_data)
        
        # Return acknowledgment with request ID
        return {
            "status": "beacon_sent",
            "request_id": request_id,
            "message": "Request sent via email beacon. Check inbox for response.",
            "layer": "email_beacon"
        }
    
    async def _send_beacon_email(self, data: dict):
        """Send beacon email via SMTP"""
        
        def _send_sync():
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.sender_name} <{self.smtp_user}>"
            msg['To'] = self.beacon_address
            msg['Subject'] = f"[KISWARM-BEACON] {data['request_id']} - {data['operation']}"
            
            # Encode payload as base64 for safety
            payload_json = json.dumps(data, indent=2)
            payload_b64 = base64.b64encode(payload_json.encode()).decode()
            
            # Body with both readable and encoded parts
            body = f"""
KISWARM MESH BEACON - EMERGENCY COMMUNICATION
=============================================

Request ID: {data['request_id']}
Timestamp: {data['timestamp']}
Operation: {data['operation']}
Priority: {data['priority']}

--- ENCODED PAYLOAD (Base64) ---
{payload_b64}
--- END PAYLOAD ---

This is an automated message from KISWARM Mesh Layer 4.
Do not reply directly to this email.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_sync)
        
        logger.info(f"[L4-Email] Beacon sent: {data['request_id']}")
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return f"KSB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    
    async def send_alert(self, subject: str, message: str, priority: str = "HIGH"):
        """
        Send an alert email (non-mesh, direct notification)
        """
        data = {
            "request_id": self._generate_request_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "alert",
            "payload": {
                "subject": subject,
                "message": message,
                "priority": priority
            }
        }
        await self._send_beacon_email(data)
    
    def get_status(self) -> dict:
        status = super().get_status()
        status["layer_type"] = "email_beacon"
        status["beacon_address"] = self.beacon_address
        status["smtp_host"] = self.smtp_host
        return status
