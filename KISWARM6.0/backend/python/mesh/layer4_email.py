"""
Layer 4: Email Beacon (Sentinel Watch)
Emergency communication via Gmail dead drop
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiosmtplib
import json
import logging
import time

from .base_layer import MeshLayer, LayerResponse, LayerStatus

logger = logging.getLogger('KISWARM.Mesh.Layer4')


@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    username: str = "sahgreenki@gmail.com"
    password: str = "YOUR_APP_PASSWORD_HERE"
    use_tls: bool = True


class Layer4EmailBeacon(MeshLayer):
    """Layer 4: Email Beacon for emergency operations"""
    
    COMMAND_PREFIX = "[KISWARM-CMD]"
    
    def __init__(
        self,
        config: Optional[EmailConfig] = None,
        authorized_senders: Optional[List[str]] = None,
        node_id: str = "KISWARM-MASTER",
        **kwargs
    ):
        super().__init__(
            layer_id=4,
            name="Email Beacon",
            priority=5,
            timeout_seconds=60.0,
            **kwargs
        )
        self.config = config or EmailConfig()
        self.authorized_senders = authorized_senders or ["sahgreenki@gmail.com"]
        self.node_id = node_id
        self._pending_commands: List[Dict[str, Any]] = []
    
    async def execute(self, task: Dict[str, Any]) -> LayerResponse:
        start_time = time.monotonic()
        operation = task.get('operation', '')
        
        if operation == 'send_alert' or operation == 'EMERGENCY_DEAD_DROP':
            return await self._send_alert(task)
        elif operation == 'send_command':
            params = task.get('params', {})
            return await self._send_command(
                params.get('recipients', self.authorized_senders),
                params.get('command', ''),
                params.get('payload', {})
            )
        else:
            return LayerResponse(
                success=False,
                error=f"Unknown operation: {operation}",
                layer_id=self.layer_id,
                layer_name=self.name
            )
    
    async def _send_alert(self, task: Dict[str, Any]) -> LayerResponse:
        start_time = time.monotonic()
        original_task = task.get('original_task', task)
        previous_attempts = task.get('previous_attempts', [])
        
        subject = f"{self.COMMAND_PREFIX} {self.node_id}: EMERGENCY_ALERT"
        
        body = f"""
KISWARM EMERGENCY ALERT
=======================
Node: {self.node_id}
Time: {datetime.utcnow().isoformat()}
Priority: CRITICAL

Original Task:
{json.dumps(original_task, indent=2, default=str)}

Previous Attempts:
{json.dumps(previous_attempts, indent=2, default=str)}

This is an automated emergency message from KISWARM v6.3.5.
"""
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message['From'] = self.config.username
            message['To'] = ', '.join(self.authorized_senders)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.username,
                password=self.config.password,
                start_tls=True
            )
            
            logger.warning(f"Emergency alert sent to {self.authorized_senders}")
            
            return LayerResponse(
                success=True,
                data={'message': 'Emergency alert sent', 'recipients': self.authorized_senders},
                layer_id=self.layer_id,
                layer_name=self.name,
                latency_ms=(time.monotonic() - start_time) * 1000
            )
        except Exception as e:
            return LayerResponse(
                success=False,
                error=str(e),
                layer_id=self.layer_id,
                layer_name=self.name,
                latency_ms=(time.monotonic() - start_time) * 1000
            )
    
    async def _send_command(
        self,
        recipients: List[str],
        command: str,
        payload: Dict[str, Any]
    ) -> LayerResponse:
        start_time = time.monotonic()
        subject = f"{self.COMMAND_PREFIX} {self.node_id}: {command}"
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart()
            message['From'] = self.config.username
            message['To'] = ', '.join(recipients)
            message['Subject'] = subject
            message.attach(MIMEText(json.dumps(payload, indent=2), 'plain'))
            
            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.username,
                password=self.config.password,
                start_tls=True
            )
            
            return LayerResponse(
                success=True,
                data={'message': 'Command sent', 'recipients': recipients},
                layer_id=self.layer_id,
                layer_name=self.name,
                latency_ms=(time.monotonic() - start_time) * 1000
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
            await aiosmtplib.send(
                None,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.username,
                password=self.config.password,
                start_tls=True
            )
            self._status = LayerStatus.HEALTHY
            return True
        except Exception:
            self._status = LayerStatus.OFFLINE
            return False
