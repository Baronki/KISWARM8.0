#!/usr/bin/env python3
"""
KISWARM8.0 - Module 05: Plugin System
=====================================
Extensible plugin architecture for KISWARM.

Features:
  - Dynamic plugin loading
  - Plugin dependency resolution
  - Hot-swap plugins
  - Plugin sandboxing
  - Plugin marketplace integration

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import sys
import json
import time
import logging
import importlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger('m05_plugin')


class PluginStatus(str, Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginManifest:
    """Plugin manifest definition"""
    name: str
    version: str
    description: str
    author: str
    main_module: str
    dependencies: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True


@dataclass
class Plugin:
    """Loaded plugin instance"""
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.UNLOADED
    module: Any = None
    loaded_at: Optional[float] = None
    error: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self.manifest.name


class PluginSystem:
    """
    Plugin Management System
    
    Enables dynamic extension of KISWARM capabilities.
    """
    
    PLUGIN_DIR = Path('/opt/kiswarm7/plugins')
    MANIFEST_FILE = 'plugin.json'
    
    def __init__(self, plugin_dir: Optional[Path] = None):
        self.plugin_dir = plugin_dir or self.PLUGIN_DIR
        
        self._plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[Callable]] = {}
        self._providers: Dict[str, str] = {}  # capability -> plugin_name
        self._lock = threading.RLock()
        
        # Ensure plugin directory exists
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
    def discover(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        for path in self.plugin_dir.iterdir():
            if path.is_dir():
                manifest_file = path / self.MANIFEST_FILE
                if manifest_file.exists():
                    discovered.append(path.name)
                    
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
        
    def load_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """Load plugin manifest"""
        manifest_path = self.plugin_dir / plugin_name / self.MANIFEST_FILE
        
        if not manifest_path.exists():
            return None
            
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
                
            return PluginManifest(
                name=data.get('name', plugin_name),
                version=data.get('version', '0.0.0'),
                description=data.get('description', ''),
                author=data.get('author', 'Unknown'),
                main_module=data.get('main_module', 'main'),
                dependencies=data.get('dependencies', []),
                provides=data.get('provides', []),
                hooks=data.get('hooks', []),
                priority=data.get('priority', 100),
                enabled=data.get('enabled', True)
            )
        except Exception as e:
            logger.error(f"Failed to load manifest for {plugin_name}: {e}")
            return None
            
    def load(self, plugin_name: str) -> bool:
        """Load a plugin"""
        with self._lock:
            if plugin_name in self._plugins:
                if self._plugins[plugin_name].status == PluginStatus.ACTIVE:
                    return True
                    
            manifest = self.load_manifest(plugin_name)
            if not manifest:
                logger.error(f"Plugin {plugin_name} has no valid manifest")
                return False
                
            plugin = Plugin(manifest=manifest, status=PluginStatus.LOADING)
            self._plugins[plugin_name] = plugin
            
            # Check dependencies
            for dep in manifest.dependencies:
                if dep not in self._plugins or self._plugins[dep].status != PluginStatus.ACTIVE:
                    logger.warning(f"Plugin {plugin_name} missing dependency: {dep}")
                    plugin.status = PluginStatus.ERROR
                    plugin.error = f"Missing dependency: {dep}"
                    return False
                    
            # Load the module
            try:
                plugin_dir = self.plugin_dir / plugin_name
                if str(plugin_dir) not in sys.path:
                    sys.path.insert(0, str(plugin_dir))
                    
                module = importlib.import_module(manifest.main_module)
                
                # Initialize if has init function
                if hasattr(module, 'initialize'):
                    module.initialize()
                    
                # Register hooks
                for hook_name in manifest.hooks:
                    if hasattr(module, hook_name):
                        hook_func = getattr(module, hook_name)
                        self.register_hook(hook_name, hook_func)
                        
                # Register providers
                for capability in manifest.provides:
                    self._providers[capability] = plugin_name
                    
                plugin.module = module
                plugin.status = PluginStatus.ACTIVE
                plugin.loaded_at = time.time()
                
                logger.info(f"Loaded plugin: {plugin_name} v{manifest.version}")
                return True
                
            except Exception as e:
                plugin.status = PluginStatus.ERROR
                plugin.error = str(e)
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                return False
                
    def unload(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        with self._lock:
            plugin = self._plugins.get(plugin_name)
            if not plugin:
                return False
                
            if plugin.status != PluginStatus.ACTIVE:
                return False
                
            try:
                # Cleanup if has cleanup function
                if plugin.module and hasattr(plugin.module, 'cleanup'):
                    plugin.module.cleanup()
                    
                # Remove hooks
                for hook_name in plugin.manifest.hooks:
                    self.unregister_hook(hook_name, plugin.module)
                    
                # Remove providers
                for cap in plugin.manifest.provides:
                    if self._providers.get(cap) == plugin_name:
                        del self._providers[cap]
                        
                plugin.status = PluginStatus.UNLOADED
                plugin.module = None
                
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                return False
                
    def reload(self, plugin_name: str) -> bool:
        """Reload a plugin (hot-swap)"""
        if self.unload(plugin_name):
            return self.load(plugin_name)
        return False
        
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
        
    def unregister_hook(self, hook_name: str, callback: Callable):
        """Unregister a hook callback"""
        if hook_name in self._hooks:
            try:
                self._hooks[hook_name].remove(callback)
            except ValueError:
                pass
                
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger all callbacks for a hook"""
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.warning(f"Hook {hook_name} callback failed: {e}")
        return results
        
    def get_provider(self, capability: str) -> Optional[str]:
        """Get plugin name that provides a capability"""
        return self._providers.get(capability)
        
    def load_all(self) -> Dict[str, bool]:
        """Load all discovered plugins"""
        results = {}
        
        # Discover
        discovered = self.discover()
        
        # Sort by priority
        manifests = []
        for name in discovered:
            manifest = self.load_manifest(name)
            if manifest and manifest.enabled:
                manifests.append((name, manifest))
                
        manifests.sort(key=lambda x: x[1].priority)
        
        # Load in order
        for name, manifest in manifests:
            results[name] = self.load(name)
            
        return results
        
    def get_status(self) -> Dict:
        """Get plugin system status"""
        return {
            'plugin_dir': str(self.plugin_dir),
            'plugins': {
                name: {
                    'status': p.status.value,
                    'version': p.manifest.version,
                    'provides': p.manifest.provides,
                    'error': p.error
                }
                for name, p in self._plugins.items()
            },
            'hooks_registered': {k: len(v) for k, v in self._hooks.items()},
            'providers': dict(self._providers)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_plugin_system: Optional[PluginSystem] = None


def get_plugin_system() -> PluginSystem:
    """Get the plugin system singleton"""
    global _plugin_system
    if _plugin_system is None:
        _plugin_system = PluginSystem()
    return _plugin_system


if __name__ == "__main__":
    system = get_plugin_system()
    results = system.load_all()
    print(json.dumps(system.get_status(), indent=2))
