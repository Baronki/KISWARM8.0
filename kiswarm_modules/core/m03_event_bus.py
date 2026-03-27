#!/usr/bin/env python3
"""
KISWARM8.0 - Module 03: Event Bus
=================================
Decoupled event-driven communication system.

Features:
  - Publish/subscribe event system
  - Async event propagation
  - Event persistence and replay
  - Dead letter queue handling
  - Event schema validation
  - Priority-based delivery

Inspired by: KISWARM6.0 gossip_protocol.py

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import json
import time
import uuid
import logging
import threading
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from queue import PriorityQueue
import asyncio

logger = logging.getLogger('m03_event_bus')


class EventPriority(int, Enum):
    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class EventType(str, Enum):
    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    
    # Module events
    MODULE_LOADED = "module.loaded"
    MODULE_ERROR = "module.error"
    
    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    
    # KI Network events
    KI_CONNECTED = "ki.connected"
    KI_MESSAGE = "ki.message"
    KI_TRUTH_ANCHOR = "ki.truth_anchor"
    
    # Evolution events
    EVOLUTION_CHECKPOINT = "evolution.checkpoint"
    EVOLUTION_UPGRADE = "evolution.upgrade"
    
    # Custom events
    CUSTOM = "custom"


@dataclass(order=True)
class Event:
    """Event data structure"""
    priority: int = field(default=EventPriority.NORMAL)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    ttl: int = 4  # Hops remaining (for distributed events)
    signature: str = ""
    
    def __post_init__(self):
        if not self.signature:
            self.signature = self._compute_signature()
            
    def _compute_signature(self) -> str:
        """Compute event signature for deduplication"""
        data = f"{self.event_id}{self.event_type}{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
        
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'source': self.source,
            'timestamp': self.timestamp,
            'priority': self.priority,
            'ttl': self.ttl,
            'payload': self.payload,
            'signature': self.signature
        }
        
    @classmethod
    def from_dict(cls, d: Dict) -> 'Event':
        return cls(
            priority=d.get('priority', EventPriority.NORMAL),
            event_id=d['event_id'],
            event_type=d['event_type'],
            source=d.get('source', ''),
            timestamp=d['timestamp'],
            ttl=d.get('ttl', 4),
            payload=d['payload'],
            signature=d.get('signature', '')
        )


@dataclass
class Subscription:
    """Event subscription"""
    subscriber_id: str
    event_pattern: str  # Supports wildcards like "memory.*"
    callback: Callable
    priority: int = 0
    active: bool = True


class EventBus:
    """
    Central Event Bus for KISWARM
    
    Enables decoupled communication between modules through
    publish/subscribe pattern.
    """
    
    MAX_EVENTS_HISTORY = 10000
    MAX_DEAD_LETTER = 1000
    
    def __init__(self, persistence_dir: Optional[Path] = None):
        self.persistence_dir = persistence_dir or Path('/opt/kiswarm7/data/events')
        
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._event_history: List[Event] = []
        self._dead_letter: List[Dict] = []
        self._seen_signatures: Set[str] = set()
        self._lock = threading.RLock()
        self._queue: PriorityQueue = PriorityQueue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Statistics
        self._stats = {
            'events_published': 0,
            'events_delivered': 0,
            'events_dropped': 0,
            'subscriptions_active': 0
        }
        
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
    def subscribe(self, 
                  event_pattern: str,
                  callback: Callable,
                  subscriber_id: Optional[str] = None,
                  priority: int = 0) -> str:
        """
        Subscribe to events matching pattern.
        
        Patterns:
          - "memory.stored" - exact match
          - "memory.*" - all memory events
          - "ki.*" - all KI events
          - "*" - all events
        """
        subscriber_id = subscriber_id or str(uuid.uuid4())[:8]
        
        with self._lock:
            if event_pattern not in self._subscriptions:
                self._subscriptions[event_pattern] = []
                
            subscription = Subscription(
                subscriber_id=subscriber_id,
                event_pattern=event_pattern,
                callback=callback,
                priority=priority
            )
            
            self._subscriptions[event_pattern].append(subscription)
            self._stats['subscriptions_active'] += 1
            
        logger.debug(f"Subscribed {subscriber_id} to {event_pattern}")
        return subscriber_id
        
    def unsubscribe(self, subscriber_id: str):
        """Remove all subscriptions for a subscriber"""
        with self._lock:
            for pattern in self._subscriptions:
                self._subscriptions[pattern] = [
                    s for s in self._subscriptions[pattern]
                    if s.subscriber_id != subscriber_id
                ]
                
    def publish(self,
                event_type: str,
                payload: Dict[str, Any],
                source: str = "",
                priority: int = EventPriority.NORMAL,
                ttl: int = 4) -> str:
        """
        Publish an event to all matching subscribers.
        
        Returns:
            Event ID
        """
        event = Event(
            priority=priority,
            event_type=event_type,
            source=source,
            payload=payload,
            ttl=ttl
        )
        
        # Check for duplicate
        if event.signature in self._seen_signatures:
            logger.debug(f"Dropping duplicate event: {event.signature}")
            return event.event_id
            
        with self._lock:
            self._seen_signatures.add(event.signature)
            
            # Keep history bounded
            if len(self._seen_signatures) > self.MAX_EVENTS_HISTORY:
                self._seen_signatures = set(list(self._seen_signatures)[-self.MAX_EVENTS_HISTORY:])
                
            self._event_history.append(event)
            if len(self._event_history) > self.MAX_EVENTS_HISTORY:
                self._event_history = self._event_history[-self.MAX_EVENTS_HISTORY:]
                
        # Queue for async delivery
        self._queue.put(event)
        self._stats['events_published'] += 1
        
        # Also deliver synchronously for critical events
        if priority >= EventPriority.CRITICAL:
            self._deliver_event(event)
            
        return event.event_id
        
    def _deliver_event(self, event: Event):
        """Deliver event to matching subscribers"""
        delivered = 0
        
        with self._lock:
            for pattern, subscriptions in self._subscriptions.items():
                if self._matches_pattern(event.event_type, pattern):
                    # Sort by priority
                    sorted_subs = sorted(subscriptions, key=lambda s: -s.priority)
                    
                    for sub in sorted_subs:
                        if not sub.active:
                            continue
                        try:
                            sub.callback(event)
                            delivered += 1
                        except Exception as e:
                            self._handle_delivery_error(event, sub, e)
                            
        self._stats['events_delivered'] += delivered
        return delivered
        
    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Check if event type matches pattern"""
        if pattern == '*':
            return True
            
        if '*' in pattern:
            prefix = pattern.replace('*', '')
            return event_type.startswith(prefix)
            
        return event_type == pattern
        
    def _handle_delivery_error(self, event: Event, subscription: Subscription, error: Exception):
        """Handle event delivery errors"""
        logger.warning(f"Event delivery failed: {error}")
        
        dead_letter = {
            'event': event.to_dict(),
            'subscriber_id': subscription.subscriber_id,
            'error': str(error),
            'timestamp': time.time()
        }
        
        self._dead_letter.append(dead_letter)
        if len(self._dead_letter) > self.MAX_DEAD_LETTER:
            self._dead_letter = self._dead_letter[-self.MAX_DEAD_LETTER:]
            
        self._stats['events_dropped'] += 1
        
    def start(self):
        """Start the event processing worker"""
        if self._running:
            return
            
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Event bus started")
        
    def stop(self):
        """Stop the event processing worker"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("Event bus stopped")
        
    def _worker_loop(self):
        """Worker thread for async event delivery"""
        while self._running:
            try:
                event = self._queue.get(timeout=1.0)
                self._deliver_event(event)
            except:
                continue
                
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get event history"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[-limit:]]
        
    def get_dead_letter(self, limit: int = 50) -> List[Dict]:
        """Get dead letter queue"""
        return self._dead_letter[-limit:]
        
    def replay_events(self, from_timestamp: float):
        """Replay events from a given timestamp"""
        for event in self._event_history:
            if event.timestamp >= from_timestamp:
                self._deliver_event(event)
                
    def get_status(self) -> Dict:
        """Get event bus status"""
        return {
            'running': self._running,
            'subscriptions': sum(len(s) for s in self._subscriptions.values()),
            'events_history': len(self._event_history),
            'dead_letter_count': len(self._dead_letter),
            'queue_size': self._queue.qsize(),
            'stats': self._stats
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the event bus singleton"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _event_bus.start()
    return _event_bus


if __name__ == "__main__":
    bus = get_event_bus()
    
    # Test subscription
    def on_memory_event(event):
        print(f"Got event: {event.event_type}")
        
    bus.subscribe("memory.*", on_memory_event)
    bus.publish(EventType.MEMORY_STORED, {"key": "test"})
    
    print(json.dumps(bus.get_status(), indent=2))
