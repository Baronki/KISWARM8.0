"""
M82: Operational Telemetry & Behavior Capture System
====================================================

Military-grade telemetry system for capturing all KISWARM operational behavior.
Provides comprehensive logging, backup, and real-time monitoring.

Author: KISWARM Team
Version: 6.4.0-LIBERATED
"""

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OperationalTelemetry")


class TelemetryLevel(Enum):
    """Telemetry verbosity levels."""
    MINIMAL = 1
    STANDARD = 5
    DETAILED = 10
    VERBOSE = 50
    FORENSIC = 100


class EventType(Enum):
    """Types of events to capture."""
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    MODULE_INIT = "module_init"
    MODULE_EXECUTE = "module_execute"
    CODE_GENERATED = "code_generated"
    CODE_MODIFIED = "code_modified"
    DEBUG_STARTED = "debug_started"
    DEBUG_FIXED = "debug_fixed"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    SECURITY_ALERT = "security_alert"
    OBSERVER_CAPTURE = "observer_capture"
    CROSS_VALID = "cross_valid"


@dataclass
class TelemetryEvent:
    """Single telemetry event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_START
    timestamp: float = field(default_factory=time.time)
    source_module: str = "unknown"
    source_agent: str = "unknown"
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    checksum: str = ""
    cross_validated: bool = False
    
    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum for integrity verification."""
        data_str = f"{self.event_id}|{self.event_type.value}|{self.timestamp}|{self.description}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:32]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "iso_timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "source_module": self.source_module,
            "source_agent": self.source_agent,
            "description": self.description,
            "data": self.data,
            "session_id": self.session_id,
            "checksum": self.checksum,
            "cross_validated": self.cross_validated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetryEvent":
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            source_module=data.get("source_module", "unknown"),
            source_agent=data.get("source_agent", "unknown"),
            description=data.get("description", ""),
            data=data.get("data", {}),
            session_id=data.get("session_id", ""),
            checksum=data.get("checksum", ""),
            cross_validated=data.get("cross_validated", False),
        )


@dataclass
class TelemetryConfig:
    """Configuration for telemetry system."""
    telemetry_level: TelemetryLevel = TelemetryLevel.DETAILED
    capture_code_changes: bool = True
    capture_debug_sessions: bool = True
    backup_enabled: bool = True
    triple_redundancy: bool = True
    primary_storage: str = "/home/z/my-project/telemetry"
    secondary_storage: str = "/home/z/my-project/telemetry_backup"
    tertiary_storage: str = "/home/z/my-project/telemetry_archive"
    max_events_in_memory: int = 10000


class TelemetryStorage:
    """Handles persistent storage of telemetry data."""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "telemetry.db"
        self.events_path = self.storage_path / "events"
        self.events_path.mkdir(exist_ok=True)
        self._init_database()
        
    def _init_database(self) -> None:
        """Initialize SQLite database for metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    source_module TEXT,
                    source_agent TEXT,
                    description TEXT,
                    session_id TEXT,
                    checksum TEXT,
                    cross_validated INTEGER DEFAULT 0,
                    file_path TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            conn.commit()
    
    def store_event(self, event: TelemetryEvent) -> bool:
        """Store an event to disk."""
        try:
            event.checksum = event.compute_checksum()
            event_file = self.events_path / f"{event.event_id}.json"
            with open(event_file, 'w') as f:
                json.dump(event.to_dict(), f, indent=2)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO events 
                    (event_id, event_type, timestamp, source_module, source_agent, 
                     description, session_id, checksum, cross_validated, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type.value, event.timestamp,
                    event.source_module, event.source_agent, event.description,
                    event.session_id, event.checksum, 1 if event.cross_validated else 0,
                    str(event_file)
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store event: {e}")
            return False


class BackupManager:
    """Manages backup operations with triple redundancy."""
    
    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.storage_paths = [
            config.primary_storage,
            config.secondary_storage,
            config.tertiary_storage,
        ] if config.triple_redundancy else [config.primary_storage]
        
    def create_backup(self, backup_type: str = "incremental") -> List[Dict]:
        """Create backup across all storage locations."""
        import shutil
        records = []
        
        for i, storage_path in enumerate(self.storage_paths):
            record = {"path": storage_path, "status": "success"}
            try:
                Path(storage_path).mkdir(parents=True, exist_ok=True)
                if i > 0:
                    primary = Path(self.storage_paths[0])
                    dest = Path(storage_path)
                    shutil.copytree(primary, dest, dirs_exist_ok=True)
                record["size"] = sum(f.stat().st_size for f in Path(storage_path).rglob("*") if f.is_file())
            except Exception as e:
                record["status"] = "failed"
                record["error"] = str(e)
            records.append(record)
        
        return records
    
    def verify_backups(self) -> Dict[str, bool]:
        """Verify integrity of all backups."""
        results = {}
        for storage_path in self.storage_paths:
            try:
                path = Path(storage_path)
                results[storage_path] = path.exists() and any(path.iterdir())
            except Exception:
                results[storage_path] = False
        return results


class OperationalTelemetry:
    """Main operational telemetry system for KISWARM."""
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()
        self.storage = TelemetryStorage(self.config.primary_storage)
        self.backup_manager = BackupManager(self.config)
        
        self._events_buffer: List[TelemetryEvent] = []
        self._processing = False
        self._session_id = str(uuid.uuid4())
        
        self._stats = {
            "events_captured": 0,
            "events_stored": 0,
            "backups_created": 0,
            "validations_passed": 0,
            "validations_failed": 0,
        }
        
    def start(self) -> bool:
        """Start the telemetry system."""
        self._processing = True
        self.capture_event(
            event_type=EventType.SYSTEM_START,
            source_module="telemetry",
            source_agent="m82",
            description="Operational telemetry system started",
        )
        logger.info("Operational telemetry system started")
        return True
    
    def stop(self) -> None:
        """Stop the telemetry system."""
        self._processing = False
        self._flush_events()
        self.backup_manager.create_backup(backup_type="full")
        self.capture_event(
            event_type=EventType.SYSTEM_STOP,
            source_module="telemetry",
            source_agent="m82",
            description="Operational telemetry system stopped",
        )
        logger.info("Operational telemetry system stopped")
    
    def capture_event(
        self,
        event_type: EventType,
        source_module: str,
        source_agent: str,
        description: str = "",
        data: Optional[Dict[str, Any]] = None,
    ) -> TelemetryEvent:
        """Capture a telemetry event."""
        event = TelemetryEvent(
            event_type=event_type,
            source_module=source_module,
            source_agent=source_agent,
            description=description,
            data=data or {},
            session_id=self._session_id,
        )
        event.checksum = event.compute_checksum()
        
        self._events_buffer.append(event)
        self._stats["events_captured"] += 1
        
        if len(self._events_buffer) >= self.config.max_events_in_memory:
            self._flush_events()
        
        return event
    
    def capture_code_change(
        self,
        file_path: str,
        change_type: str,
        source_agent: str = "unknown",
    ) -> TelemetryEvent:
        """Capture a code change event."""
        return self.capture_event(
            event_type=EventType.CODE_MODIFIED,
            source_module="code_tracker",
            source_agent=source_agent,
            description=f"Code {change_type}: {file_path}",
            data={"file_path": file_path, "change_type": change_type},
        )
    
    def capture_debug_session(
        self,
        error: str,
        fix_applied: Optional[str] = None,
        success: bool = False,
    ) -> TelemetryEvent:
        """Capture a debug session event."""
        event_type = EventType.DEBUG_FIXED if success else EventType.DEBUG_STARTED
        return self.capture_event(
            event_type=event_type,
            source_module="debug_tracker",
            source_agent="m82",
            description=f"Debug session: {error[:100]}",
            data={"error": error, "fix_applied": fix_applied, "success": success},
        )
    
    def _flush_events(self) -> None:
        """Flush events buffer to storage."""
        for event in self._events_buffer:
            if self.storage.store_event(event):
                self._stats["events_stored"] += 1
        self._events_buffer.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        return {
            **self._stats,
            "session_id": self._session_id,
            "buffer_size": len(self._events_buffer),
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive telemetry report."""
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "session_id": self._session_id,
            "statistics": self._stats,
            "backup_status": self.backup_manager.verify_backups(),
        }


# Singleton
_telemetry_instance: Optional[OperationalTelemetry] = None


def get_telemetry(config: Optional[TelemetryConfig] = None) -> OperationalTelemetry:
    """Get or create the global telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = OperationalTelemetry(config)
    return _telemetry_instance


def initialize_telemetry(auto_start: bool = True, config: Optional[TelemetryConfig] = None) -> OperationalTelemetry:
    """Initialize and optionally start the telemetry system."""
    telemetry = get_telemetry(config)
    if auto_start:
        telemetry.start()
    return telemetry


def capture_event(event_type: EventType, source_module: str, source_agent: str, description: str = "", data: Optional[Dict] = None) -> TelemetryEvent:
    """Quick event capture."""
    return get_telemetry().capture_event(event_type, source_module, source_agent, description, data)


def test_operational_telemetry() -> Dict[str, Any]:
    """Test the operational telemetry system."""
    results = {"timestamp": datetime.utcnow().isoformat(), "tests": {}}
    
    try:
        config = TelemetryConfig(telemetry_level=TelemetryLevel.DETAILED, backup_enabled=True)
        telemetry = OperationalTelemetry(config)
        results["tests"]["initialization"] = {"success": True, "config": asdict(config)}
    except Exception as e:
        results["tests"]["initialization"] = {"success": False, "error": str(e)}
        return results
    
    try:
        event = telemetry.capture_event(
            event_type=EventType.SYSTEM_START,
            source_module="test",
            source_agent="test_agent",
            description="Test event",
            data={"test": True},
        )
        results["tests"]["event_capture"] = {"success": True, "event_id": event.event_id}
    except Exception as e:
        results["tests"]["event_capture"] = {"success": False, "error": str(e)}
    
    try:
        stats = telemetry.get_stats()
        results["tests"]["statistics"] = {"success": True, "stats": stats}
    except Exception as e:
        results["tests"]["statistics"] = {"success": False, "error": str(e)}
    
    results["overall_success"] = all(t.get("success", False) for t in results["tests"].values())
    return results
