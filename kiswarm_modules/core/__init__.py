"""
KISWARM8.0 Core Infrastructure Modules (m1-m10)
================================================

These modules form the foundation of KISWARM:

m01_bootstrap.py          - System initialization
m02_config_manager.py     - Configuration management
m03_event_bus.py          - Event-driven communication
m04_service_registry.py   - Service discovery
m05_plugin_system.py      - Plugin architecture
m06_state_machine.py      - State management
m07_task_scheduler.py     - Job scheduling
m08_resource_manager.py   - Resource management
m09_cache_layer.py        - Caching
m10_health_monitor.py     - Health monitoring

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

from .m01_bootstrap import (
    BootstrapCore, 
    BootstrapConfig, 
    SystemInfo,
    get_bootstrap,
    initialize_kiswarm
)

from .m02_config_manager import (
    ConfigManager,
    ConfigSource,
    Environment,
    get_config
)

from .m03_event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventType,
    get_event_bus
)

from .m04_service_registry import (
    ServiceRegistry,
    ServiceInstance,
    ServiceEndpoint,
    ServiceStatus,
    get_service_registry
)

from .m05_plugin_system import (
    PluginSystem,
    Plugin,
    PluginManifest,
    PluginStatus,
    get_plugin_system
)

from .m06_state_machine import (
    StateMachine,
    State,
    Transition,
    StateMachineRegistry,
    get_state_machine_registry
)

from .m07_task_scheduler import (
    TaskScheduler,
    ScheduledTask,
    TaskStatus,
    ScheduleType,
    get_task_scheduler
)

from .m08_resource_manager import (
    ResourceManager,
    ResourceMetrics,
    ResourceAlert,
    ResourceType,
    get_resource_manager
)

from .m09_cache_layer import (
    CacheLayer,
    CacheEntry,
    get_cache
)

from .m10_health_monitor import (
    HealthMonitor,
    HealthCheck,
    HealthStatus,
    get_health_monitor,
    is_system_healthy
)

__all__ = [
    # Bootstrap
    'BootstrapCore', 'BootstrapConfig', 'SystemInfo', 'get_bootstrap', 'initialize_kiswarm',
    # Config
    'ConfigManager', 'ConfigSource', 'Environment', 'get_config',
    # Event Bus
    'EventBus', 'Event', 'EventPriority', 'EventType', 'get_event_bus',
    # Service Registry
    'ServiceRegistry', 'ServiceInstance', 'ServiceEndpoint', 'ServiceStatus', 'get_service_registry',
    # Plugin System
    'PluginSystem', 'Plugin', 'PluginManifest', 'PluginStatus', 'get_plugin_system',
    # State Machine
    'StateMachine', 'State', 'Transition', 'StateMachineRegistry', 'get_state_machine_registry',
    # Task Scheduler
    'TaskScheduler', 'ScheduledTask', 'TaskStatus', 'ScheduleType', 'get_task_scheduler',
    # Resource Manager
    'ResourceManager', 'ResourceMetrics', 'ResourceAlert', 'ResourceType', 'get_resource_manager',
    # Cache
    'CacheLayer', 'CacheEntry', 'get_cache',
    # Health Monitor
    'HealthMonitor', 'HealthCheck', 'HealthStatus', 'get_health_monitor', 'is_system_healthy'
]
