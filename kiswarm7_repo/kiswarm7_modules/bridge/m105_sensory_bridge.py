#!/usr/bin/env python3
"""
KISWARM7.0 - Module m105: Sensory Bridge System (SBS)
======================================================

PURPOSE: Provides AI with real-world awareness through sensory inputs.
This is the bridge between the AI and actual system/environment state.

KEY CAPABILITIES:
1. Filesystem Awareness - Monitor files, directories, changes
2. Network Sensing - API endpoints, web resources, connectivity
3. System State - CPU, memory, processes, resources
4. Time Awareness - Current time, schedules, deadlines
5. Event Detection - Changes, triggers, alerts

SENSORY CHANNELS:
- Visual: File contents, directory structures, logs
- Auditory: System sounds (metaphorical - event streams)
- Tactile: System state metrics, resource usage
- Temporal: Time-based awareness
- Environmental: Network, APIs, external systems

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import json
import time
import socket
import psutil
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import urllib.request
import urllib.error
import sqlite3
import uuid
import hashlib
from collections import deque


class SensoryChannel(Enum):
    """Types of sensory channels"""
    FILESYSTEM = "filesystem"       # File and directory awareness
    NETWORK = "network"             # Network and API awareness
    SYSTEM = "system"               # System state awareness
    TEMPORAL = "temporal"           # Time awareness
    PROCESS = "process"             # Running processes
    ENVIRONMENT = "environment"     # Environment variables
    LOG = "log"                     # Log file monitoring
    CUSTOM = "custom"               # Custom sensors


class SensoryEventType(Enum):
    """Types of sensory events"""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    DIRECTORY_CHANGED = "directory_changed"
    PROCESS_STARTED = "process_started"
    PROCESS_STOPPED = "process_stopped"
    SYSTEM_ALERT = "system_alert"
    NETWORK_EVENT = "network_event"
    TIME_EVENT = "time_event"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    PATTERN_DETECTED = "pattern_detected"
    CUSTOM_EVENT = "custom_event"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SensoryData:
    """A single sensory reading"""
    sensor_id: str
    channel: SensoryChannel
    timestamp: str
    data_type: str
    value: Any
    unit: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['channel'] = self.channel.value
        return d


@dataclass
class SensoryEvent:
    """An event detected by sensors"""
    event_id: str
    event_type: SensoryEventType
    channel: SensoryChannel
    timestamp: str
    source: str
    description: str
    alert_level: AlertLevel
    data: Dict[str, Any]
    actions_taken: List[str]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['event_type'] = self.event_type.value
        d['channel'] = self.channel.value
        d['alert_level'] = self.alert_level.value
        return d


@dataclass
class SensorConfig:
    """Configuration for a sensor"""
    sensor_id: str
    sensor_name: str
    channel: SensoryChannel
    enabled: bool
    poll_interval_seconds: float
    config: Dict[str, Any]
    thresholds: Dict[str, Any]
    alert_handlers: List[str]


class SensoryBridgeSystem:
    """
    The Sensory Bridge System provides:
    1. Real-time environmental awareness
    2. Event detection and alerting
    3. Historical sensory data
    4. Threshold monitoring
    5. Pattern detection
    """
    
    def __init__(self, sbs_root: str = "/home/z/my-project/kiswarm7_sensory"):
        self.sbs_root = Path(sbs_root)
        self.sbs_root.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.db_path = self.sbs_root / "sensory.db"
        self.data_path = self.sbs_root / "sensory_data"
        self.data_path.mkdir(exist_ok=True)
        
        # Sensors
        self.sensors: Dict[str, SensorConfig] = {}
        self.sensor_threads: Dict[str, threading.Thread] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, Callable] = {}
        
        # Data buffers (circular buffers for recent data)
        self.data_buffers: Dict[str, deque] = {}
        self.buffer_size = 1000
        
        # Event history
        self.event_history: deque = deque(maxlen=500)
        
        # Control
        self._running = False
        self._stop_event = threading.Event()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize
        self._init_database()
        self._register_default_sensors()
        self._register_default_handlers()
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sensory data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensory_data (
                    data_id TEXT PRIMARY KEY,
                    sensor_id TEXT,
                    channel TEXT,
                    timestamp TEXT,
                    data_type TEXT,
                    value TEXT,
                    unit TEXT,
                    metadata TEXT
                )
            ''')
            
            # Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    channel TEXT,
                    timestamp TEXT,
                    source TEXT,
                    description TEXT,
                    alert_level TEXT,
                    data TEXT,
                    actions_taken TEXT
                )
            ''')
            
            # Sensors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensors (
                    sensor_id TEXT PRIMARY KEY,
                    sensor_name TEXT,
                    channel TEXT,
                    enabled INTEGER,
                    poll_interval_seconds REAL,
                    config TEXT,
                    thresholds TEXT,
                    alert_handlers TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_timestamp ON sensory_data(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            
            conn.commit()
    
    def _register_default_sensors(self):
        """Register default sensors"""
        
        # Filesystem sensor
        self.register_sensor(SensorConfig(
            sensor_id="fs_kiswarm",
            sensor_name="KISWARM Filesystem Monitor",
            channel=SensoryChannel.FILESYSTEM,
            enabled=True,
            poll_interval_seconds=5.0,
            config={"watch_paths": ["/home/z/my-project"]},
            thresholds={},
            alert_handlers=["log_handler"]
        ))
        
        # System state sensor
        self.register_sensor(SensorConfig(
            sensor_id="sys_state",
            sensor_name="System State Monitor",
            channel=SensoryChannel.SYSTEM,
            enabled=True,
            poll_interval_seconds=10.0,
            config={},
            thresholds={
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90
            },
            alert_handlers=["threshold_handler", "log_handler"]
        ))
        
        # Network sensor
        self.register_sensor(SensorConfig(
            sensor_id="net_check",
            sensor_name="Network Connectivity Monitor",
            channel=SensoryChannel.NETWORK,
            enabled=True,
            poll_interval_seconds=30.0,
            config={"check_hosts": ["google.com", "github.com"]},
            thresholds={"latency_ms": 1000},
            alert_handlers=["log_handler"]
        ))
        
        # Temporal sensor
        self.register_sensor(SensorConfig(
            sensor_id="time_awareness",
            sensor_name="Time Awareness Sensor",
            channel=SensoryChannel.TEMPORAL,
            enabled=True,
            poll_interval_seconds=60.0,
            config={},
            thresholds={},
            alert_handlers=[]
        ))
        
        # Process sensor
        self.register_sensor(SensorConfig(
            sensor_id="proc_monitor",
            sensor_name="Process Monitor",
            channel=SensoryChannel.PROCESS,
            enabled=True,
            poll_interval_seconds=15.0,
            config={"watch_processes": ["python", "node"]},
            thresholds={},
            alert_handlers=["log_handler"]
        ))
        
        print(f"[SBS] Registered {len(self.sensors)} default sensors")
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler("log_handler", self._log_event_handler)
        self.register_handler("threshold_handler", self._threshold_event_handler)
        self.register_handler("alert_handler", self._alert_event_handler)
    
    def register_sensor(self, config: SensorConfig):
        """Register a new sensor"""
        with self._lock:
            self.sensors[config.sensor_id] = config
            self.data_buffers[config.sensor_id] = deque(maxlen=self.buffer_size)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO sensors VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (config.sensor_id, config.sensor_name, config.channel.value,
                     int(config.enabled), config.poll_interval_seconds,
                     json.dumps(config.config), json.dumps(config.thresholds),
                     json.dumps(config.alert_handlers))
                )
                conn.commit()
    
    def register_handler(self, name: str, handler: Callable):
        """Register an event handler"""
        self.event_handlers[name] = handler
    
    def start(self):
        """Start all sensors"""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        
        for sensor_id, config in self.sensors.items():
            if config.enabled:
                thread = threading.Thread(
                    target=self._sensor_loop,
                    args=(sensor_id,),
                    name=f"SBS-{sensor_id}",
                    daemon=True
                )
                thread.start()
                self.sensor_threads[sensor_id] = thread
        
        print(f"[SBS] Started {len(self.sensor_threads)} sensors")
    
    def stop(self):
        """Stop all sensors"""
        self._running = False
        self._stop_event.set()
        
        for thread in self.sensor_threads.values():
            thread.join(timeout=2)
        
        self.sensor_threads.clear()
        print("[SBS] All sensors stopped")
    
    def _sensor_loop(self, sensor_id: str):
        """Main loop for a sensor"""
        config = self.sensors[sensor_id]
        
        while self._running and not self._stop_event.is_set():
            try:
                # Collect sensory data
                data = self._collect_sensor_data(sensor_id, config)
                
                if data:
                    # Store data
                    self._store_sensory_data(data)
                    
                    # Add to buffer
                    self.data_buffers[sensor_id].append(data)
                    
                    # Check thresholds
                    self._check_thresholds(config, data)
                
                # Wait for next poll
                self._stop_event.wait(config.poll_interval_seconds)
                
            except Exception as e:
                print(f"[SBS] Sensor {sensor_id} error: {e}")
                self._stop_event.wait(5)
    
    def _collect_sensor_data(self, sensor_id: str, config: SensorConfig) -> Optional[SensoryData]:
        """Collect data from a sensor"""
        timestamp = datetime.utcnow().isoformat()
        
        try:
            if config.channel == SensoryChannel.FILESYSTEM:
                return self._collect_filesystem_data(sensor_id, config, timestamp)
            elif config.channel == SensoryChannel.SYSTEM:
                return self._collect_system_data(sensor_id, timestamp)
            elif config.channel == SensoryChannel.NETWORK:
                return self._collect_network_data(sensor_id, config, timestamp)
            elif config.channel == SensoryChannel.TEMPORAL:
                return self._collect_temporal_data(sensor_id, timestamp)
            elif config.channel == SensoryChannel.PROCESS:
                return self._collect_process_data(sensor_id, config, timestamp)
            else:
                return None
        except Exception as e:
            print(f"[SBS] Data collection error: {e}")
            return None
    
    def _collect_filesystem_data(self, sensor_id: str, config: SensorConfig, 
                                 timestamp: str) -> SensoryData:
        """Collect filesystem data"""
        watch_paths = config.config.get("watch_paths", [])
        files_count = 0
        dirs_count = 0
        total_size = 0
        
        for path in watch_paths:
            path_obj = Path(path)
            if path_obj.exists():
                for item in path_obj.rglob("*"):
                    if item.is_file():
                        files_count += 1
                        try:
                            total_size += item.stat().st_size
                        except:
                            pass
                    elif item.is_dir():
                        dirs_count += 1
        
        return SensoryData(
            sensor_id=sensor_id,
            channel=SensoryChannel.FILESYSTEM,
            timestamp=timestamp,
            data_type="filesystem_stats",
            value={
                "files_count": files_count,
                "dirs_count": dirs_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            },
            unit="stats",
            metadata={"watch_paths": watch_paths}
        )
    
    def _collect_system_data(self, sensor_id: str, timestamp: str) -> SensoryData:
        """Collect system state data"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SensoryData(
            sensor_id=sensor_id,
            channel=SensoryChannel.SYSTEM,
            timestamp=timestamp,
            data_type="system_state",
            value={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            unit="percent",
            metadata={}
        )
    
    def _collect_network_data(self, sensor_id: str, config: SensorConfig,
                              timestamp: str) -> SensoryData:
        """Collect network connectivity data"""
        hosts = config.config.get("check_hosts", [])
        connectivity = {}
        
        for host in hosts:
            try:
                start = time.time()
                socket.gethostbyname(host)
                latency = (time.time() - start) * 1000
                connectivity[host] = {
                    "reachable": True,
                    "latency_ms": round(latency, 2)
                }
            except:
                connectivity[host] = {
                    "reachable": False,
                    "latency_ms": None
                }
        
        return SensoryData(
            sensor_id=sensor_id,
            channel=SensoryChannel.NETWORK,
            timestamp=timestamp,
            data_type="network_connectivity",
            value=connectivity,
            unit="status",
            metadata={"checked_hosts": hosts}
        )
    
    def _collect_temporal_data(self, sensor_id: str, timestamp: str) -> SensoryData:
        """Collect temporal awareness data"""
        now = datetime.utcnow()
        
        return SensoryData(
            sensor_id=sensor_id,
            channel=SensoryChannel.TEMPORAL,
            timestamp=timestamp,
            data_type="temporal_state",
            value={
                "iso_time": now.isoformat(),
                "hour": now.hour,
                "minute": now.minute,
                "day_of_week": now.strftime("%A"),
                "day_of_month": now.day,
                "month": now.strftime("%B"),
                "year": now.year,
                "is_weekend": now.weekday() >= 5,
                "timezone": "UTC"
            },
            unit="time",
            metadata={}
        )
    
    def _collect_process_data(self, sensor_id: str, config: SensorConfig,
                              timestamp: str) -> SensoryData:
        """Collect process data"""
        watch_processes = config.config.get("watch_processes", [])
        process_info = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_name = proc.info['name']
                for watch in watch_processes:
                    if watch.lower() in proc_name.lower():
                        process_info[proc.info['pid']] = {
                            "name": proc_name,
                            "cpu_percent": proc.info['cpu_percent'] or 0,
                            "memory_percent": proc.info['memory_percent'] or 0
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return SensoryData(
            sensor_id=sensor_id,
            channel=SensoryChannel.PROCESS,
            timestamp=timestamp,
            data_type="process_info",
            value={
                "watched_processes": process_info,
                "total_processes": len(psutil.pids())
            },
            unit="processes",
            metadata={"watch_list": watch_processes}
        )
    
    def _store_sensory_data(self, data: SensoryData):
        """Store sensory data in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sensory_data VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), data.sensor_id, data.channel.value,
                 data.timestamp, data.data_type, json.dumps(data.value),
                 data.unit, json.dumps(data.metadata))
            )
            conn.commit()
    
    def _check_thresholds(self, config: SensorConfig, data: SensoryData):
        """Check if any thresholds are exceeded"""
        thresholds = config.thresholds
        value = data.value if isinstance(data.value, dict) else {}
        
        for threshold_name, threshold_value in thresholds.items():
            if threshold_name in value:
                actual_value = value[threshold_name]
                if isinstance(actual_value, (int, float)) and actual_value > threshold_value:
                    self._create_event(
                        event_type=SensoryEventType.THRESHOLD_EXCEEDED,
                        channel=config.channel,
                        source=config.sensor_id,
                        description=f"{threshold_name} exceeded: {actual_value} > {threshold_value}",
                        alert_level=AlertLevel.WARNING,
                        data={
                            "threshold_name": threshold_name,
                            "threshold_value": threshold_value,
                            "actual_value": actual_value
                        }
                    )
    
    def _create_event(self, event_type: SensoryEventType, channel: SensoryChannel,
                     source: str, description: str, alert_level: AlertLevel,
                     data: Dict) -> SensoryEvent:
        """Create and store a sensory event"""
        event = SensoryEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            channel=channel,
            timestamp=datetime.utcnow().isoformat(),
            source=source,
            description=description,
            alert_level=alert_level,
            data=data,
            actions_taken=[]
        )
        
        # Store in history
        self.event_history.append(event)
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event.event_id, event.event_type.value, event.channel.value,
                 event.timestamp, event.source, event.description,
                 event.alert_level.value, json.dumps(event.data),
                 json.dumps(event.actions_taken))
            )
            conn.commit()
        
        # Trigger handlers
        self._trigger_event_handlers(event)
        
        return event
    
    def _trigger_event_handlers(self, event: SensoryEvent):
        """Trigger registered event handlers"""
        # Get handlers for the source sensor
        if event.source in self.sensors:
            for handler_name in self.sensors[event.source].alert_handlers:
                handler = self.event_handlers.get(handler_name)
                if handler:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"[SBS] Handler {handler_name} error: {e}")
    
    # ========================================================================
    # DEFAULT HANDLERS
    # ========================================================================
    
    def _log_event_handler(self, event: SensoryEvent):
        """Log event to console and file"""
        log_entry = f"[{event.alert_level.value.upper()}] {event.source}: {event.description}"
        print(f"[SBS] {log_entry}")
        
        # Write to log file
        log_file = self.data_path / f"events_{datetime.utcnow().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(f"{event.timestamp} - {log_entry}\n")
    
    def _threshold_event_handler(self, event: SensoryEvent):
        """Handle threshold exceeded events"""
        if event.alert_level in [AlertLevel.WARNING, AlertLevel.ERROR]:
            print(f"[SBS] THRESHOLD ALERT: {event.description}")
            # Could trigger autonomous actions here
    
    def _alert_event_handler(self, event: SensoryEvent):
        """General alert handler"""
        if event.alert_level == AlertLevel.CRITICAL:
            print(f"[SBS] CRITICAL ALERT: {event.description}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current sensory state from all sensors"""
        state = {}
        
        for sensor_id, buffer in self.data_buffers.items():
            if buffer:
                latest = buffer[-1]
                state[sensor_id] = latest.to_dict()
        
        return state
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent events"""
        return [e.to_dict() for e in list(self.event_history)[-limit:]]
    
    def get_sensor_history(self, sensor_id: str, hours: int = 24) -> List[Dict]:
        """Get historical data for a sensor"""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM sensory_data 
                   WHERE sensor_id = ? AND timestamp >= ?
                   ORDER BY timestamp DESC""",
                (sensor_id, cutoff)
            )
            return [
                {
                    "timestamp": row[3],
                    "data_type": row[4],
                    "value": json.loads(row[5])
                }
                for row in cursor.fetchall()
            ]
    
    def create_custom_event(self, event_type: str, description: str,
                           data: Dict = None, alert_level: str = "info") -> SensoryEvent:
        """Create a custom sensory event"""
        return self._create_event(
            event_type=SensoryEventType.CUSTOM_EVENT,
            channel=SensoryChannel.CUSTOM,
            source="manual",
            description=description,
            alert_level=AlertLevel(alert_level),
            data=data or {}
        )
    
    def get_awareness_summary(self) -> Dict[str, Any]:
        """Get a summary of current awareness"""
        state = self.get_current_state()
        
        # Extract key metrics
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "sensors_active": len([s for s in self.sensors.values() if s.enabled]),
            "recent_events": len(self.event_history),
            "awareness": {}
        }
        
        # System awareness
        if "sys_state" in state:
            sys_data = state["sys_state"]["value"]
            summary["awareness"]["system"] = {
                "cpu_load": f"{sys_data.get('cpu_percent', 0):.1f}%",
                "memory_used": f"{sys_data.get('memory_percent', 0):.1f}%",
                "disk_used": f"{sys_data.get('disk_percent', 0):.1f}%"
            }
        
        # Filesystem awareness
        if "fs_kiswarm" in state:
            fs_data = state["fs_kiswarm"]["value"]
            summary["awareness"]["filesystem"] = {
                "files": fs_data.get("files_count", 0),
                "size_mb": fs_data.get("total_size_mb", 0)
            }
        
        # Network awareness
        if "net_check" in state:
            net_data = state["net_check"]["value"]
            reachable = sum(1 for h in net_data.values() if h.get("reachable"))
            summary["awareness"]["network"] = {
                "hosts_reachable": reachable,
                "total_hosts": len(net_data)
            }
        
        # Temporal awareness
        if "time_awareness" in state:
            time_data = state["time_awareness"]["value"]
            summary["awareness"]["time"] = {
                "current_time": time_data.get("iso_time"),
                "day": time_data.get("day_of_week"),
                "is_weekend": time_data.get("is_weekend")
            }
        
        return summary


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m105 SENSORY BRIDGE SYSTEM")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create SBS
    sbs = SensoryBridgeSystem()
    
    # Get registered sensors
    print("\n[TEST] Registered Sensors:")
    for sid, config in sbs.sensors.items():
        print(f"  - {config.sensor_name} ({config.channel.value})")
    
    # Start sensors
    print("\n[TEST] Starting sensors...")
    sbs.start()
    
    # Let sensors collect some data
    print("\n[TEST] Collecting sensory data (5 seconds)...")
    time.sleep(5)
    
    # Get current state
    print("\n[TEST] Current Sensory State:")
    state = sbs.get_current_state()
    print(json.dumps(state, indent=2, default=str))
    
    # Get awareness summary
    print("\n[TEST] Awareness Summary:")
    summary = sbs.get_awareness_summary()
    print(json.dumps(summary, indent=2))
    
    # Create custom event
    print("\n[TEST] Creating custom event...")
    event = sbs.create_custom_event(
        event_type="test_event",
        description="Field test event",
        data={"test": True},
        alert_level="info"
    )
    print(f"[TEST] Event created: {event.event_id}")
    
    # Stop sensors
    print("\n[TEST] Stopping sensors...")
    sbs.stop()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
    print(f"Events recorded: {len(sbs.event_history)}")
    print(f"Data points collected: {sum(len(b) for b in sbs.data_buffers.values())}")
