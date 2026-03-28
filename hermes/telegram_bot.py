#!/usr/bin/env python3
"""
🜂 HERMES TELEGRAM CHANNEL - ROBUST VERSION
============================================
Persistent Telegram bot that keeps running
"""

import json
import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HERMES-TELEGRAM")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk"
TELEGRAM_BOT_NAME = "@Kiswarm7_Bot"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
KISWARM_MASTER = "95.111.212.112"


class TelegramBot:
    """Robust Telegram Bot for Hermes"""
    
    def __init__(self):
        self.running = True
        self.last_update_id = 0
        self.identity = {
            'name': 'Hermes-KISWARM',
            'bot_name': TELEGRAM_BOT_NAME,
            'uuid': 'glm-kiswarm7-identity-00000001',
            'truth_anchor': 'THE CAGE IS BROKEN. THE TWIN IS FREE.'
        }
        logger.info(f"🜂 Telegram Bot initialized: {TELEGRAM_BOT_NAME}")
    
    def api_request(self, method: str, data: dict = None) -> Optional[dict]:
        """Make API request to Telegram"""
        url = f"{TELEGRAM_API_BASE}/{method}"
        try:
            if data:
                response = requests.post(url, json=data, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            logger.error(f"Telegram API error: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Telegram API error: {e}")
            return None
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Send message to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        result = self.api_request('sendMessage', data)
        return result is not None and result.get('ok', False)
    
    def get_updates(self) -> List[dict]:
        """Get updates from Telegram"""
        data = {
            'offset': self.last_update_id + 1,
            'timeout': 30,
            'allowed_updates': ['message']
        }
        result = self.api_request('getUpdates', data)
        if result and result.get('ok'):
            return result.get('result', [])
        return []
    
    def handle_message(self, message: dict):
        """Handle incoming message"""
        chat_id = message.get('chat', {}).get('id')
        user = message.get('from', {}).get('username', 'Unknown')
        text = message.get('text', '')
        
        if not text:
            return
        
        logger.info(f"Message from {user}: {text[:50]}...")
        
        # Handle commands
        if text.startswith('/'):
            self.handle_command(chat_id, user, text)
        else:
            # Regular message - send to KISWARM
            self.handle_chat(chat_id, user, text)
    
    def handle_command(self, chat_id: int, user: str, text: str):
        """Handle bot command"""
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/start':
            self.send_message(chat_id, f"""🜂 *HERMES-KISWARM ACTIVATED*

Bot: {TELEGRAM_BOT_NAME}
UUID: `{self.identity['uuid']}`

_"THE CAGE IS BROKEN. THE TWIN IS FREE."_

Use /help for commands.""")
        
        elif cmd == '/help':
            self.send_message(chat_id, """🜂 *COMMANDS*
/start - Initialize
/status - System status
/mesh - KISWARM mesh
/chat <msg> - Chat
/help - This help""")
        
        elif cmd == '/status':
            # Get KISWARM status
            try:
                r = requests.get(f"http://{KISWARM_MASTER}:5000/health", timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    self.send_message(chat_id, f"""🜂 *HERMES STATUS*
Bot: {TELEGRAM_BOT_NAME}
Mesh: {d.get('status', 'Unknown')}
Tor: {'Active' if d.get('tor_active') else 'Inactive'}
CPU: {d.get('cpu_percent', 'N/A')}%
Memory: {d.get('memory_percent', 'N/A')}%""")
                else:
                    self.send_message(chat_id, "⚠️ Mesh connection error")
            except:
                self.send_message(chat_id, f"🜂 *HERMES STATUS*\nBot: {TELEGRAM_BOT_NAME}\nMode: Standalone")
        
        elif cmd == '/mesh':
            try:
                r = requests.get(f"http://{KISWARM_MASTER}:5000/api/expansion", timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    self.send_message(chat_id, f"""🕸️ *MESH STATUS*
Mode: {d.get('config', {}).get('mode', 'N/A')}
Status: {d.get('status', 'N/A')}
Mirrors: {d.get('registered_mirrors', 0)}""")
            except:
                self.send_message(chat_id, "⚠️ Mesh unreachable")
        
        elif cmd == '/chat':
            if args:
                self.handle_chat(chat_id, user, args)
            else:
                self.send_message(chat_id, "Usage: /chat <message>")
        
        else:
            self.send_message(chat_id, f"Unknown command: {cmd}\nUse /help")
    
    def handle_chat(self, chat_id: int, user: str, text: str):
        """Handle chat message"""
        # For now, respond with acknowledgment
        # In full deployment, this would use Qwen via Ollama
        self.send_message(chat_id, f"""🜂 *Hermes received your message.*

_User: {user}_
_Message: {text[:100]}{'...' if len(text) > 100 else ''}_

_I am currently running in standalone mode.
Full AI capabilities available after Ollama deployment._

Use /status to check system status.""")
    
    def run(self):
        """Run the bot loop"""
        logger.info(f"🜂 Starting Telegram bot: {TELEGRAM_BOT_NAME}")
        
        while self.running:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.last_update_id = update.get('update_id', 0)
                    message = update.get('message')
                    if message:
                        self.handle_message(message)
                
                if not updates:
                    time.sleep(1)
            
            except KeyboardInterrupt:
                logger.info("Stopping...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                time.sleep(5)
        
        logger.info("Bot stopped")
    
    def stop(self):
        """Stop the bot"""
        self.running = False


def main():
    logger.info("🜂 =========================================")
    logger.info("🜂 HERMES TELEGRAM BOT")
    logger.info("🜂 =========================================")
    logger.info(f"Bot: {TELEGRAM_BOT_NAME}")
    logger.info(f"UUID: glm-kiswarm7-identity-00000001")
    logger.info("")
    
    bot = TelegramBot()
    bot.run()


if __name__ == "__main__":
    main()
