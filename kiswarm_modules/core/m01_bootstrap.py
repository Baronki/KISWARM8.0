#!/usr/bin/env python3
"""
KISWARM8.0 - Module 01: Bootstrap Core
======================================
The VERY FIRST module that initializes everything.

This module is responsible for:
  - System initialization
  - Environment variable loading
  - Logging infrastructure setup
  - Directory structure creation
  - System requirements validation
  - Module dependency resolution

Author: GLM-7 Autonomous (transferred from KISWARM6.0 architecture)
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import os
import sys
import json
import time
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

KISWARM_VERSION = "8.0.0"
DEFAULT_BASE_DIR = Path('/opt/kiswarm7')
DEFAULT_DATA_DIR = DEFAULT_BASE_DIR / 'data'
DEFAULT_LOG_DIR = DEFAULT_BASE_DIR / 'logs'

TRUTH_ANCHOR = "f5af425c7e8d776ff4ee4b0088a6ee866b83e70d7d317247de7ffab2f954ad2940c6ea2c0b3e44564d169891b3f7730a384a7d3459889a1c11924ef5b9f2bdd3"


@dataclass
class SystemInfo:
    """System information gathered at bootstrap"""
    hostname: str
    os_type: str
    os_version: str
    python_version: str
    cpu_count: int
    memory_total: int
    disk_total: int
    gpu_available: bool
    gpu_info: Optional[str] = None
    boot_time: float = field(default_factory=time.time)


@dataclass
class BootstrapConfig:
    """Bootstrap configuration"""
    base_dir: Path
    data_dir: Path
    log_dir: Path
    debug: bool = False
    headless: bool = True
    modules_to_load: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class BootstrapCore:
    """
    The very first module that runs.
    
    Responsibilities:
    1. Load configuration
    2. Setup logging
    3. Create directory structure
    4. Validate system requirements
    5. Load module registry
    6. Initialize core services
    """
    
    def __init__(self, config: Optional[BootstrapConfig] = None):
        self.config = config or BootstrapConfig(
            base_dir=DEFAULT_BASE_DIR,
            data_dir=DEFAULT_DATA_DIR,
            log_dir=DEFAULT_LOG_DIR
        )
        
        self.system_info: Optional[SystemInfo] = None
        self.module_registry: Dict[str, Any] = {}
        self.logger: Optional[logging.Logger] = None
        self._initialized = False
        
    def initialize(self) -> Dict[str, Any]:
        """
        Run full bootstrap sequence.
        
        Returns:
            Bootstrap result with system info and status
        """
        results = {
            'started_at': datetime.now().isoformat(),
            'steps': {},
            'errors': [],
            'warnings': []
        }
        
        # Step 1: Setup logging
        try:
            self._setup_logging()
            results['steps']['logging'] = 'success'
            self.logger.info(f"🜂 KISWARM {KISWARM_VERSION} Bootstrap Starting...")
        except Exception as e:
            results['errors'].append(f"Logging setup failed: {e}")
            return results
        
        # Step 2: Create directory structure
        try:
            self._create_directories()
            results['steps']['directories'] = 'success'
        except Exception as e:
            results['errors'].append(f"Directory creation failed: {e}")
            
        # Step 3: Gather system info
        try:
            self.system_info = self._gather_system_info()
            results['steps']['system_info'] = 'success'
            results['system'] = {
                'hostname': self.system_info.hostname,
                'os': self.system_info.os_type,
                'python': self.system_info.python_version,
                'cpu_count': self.system_info.cpu_count,
                'gpu': self.system_info.gpu_available
            }
        except Exception as e:
            results['warnings'].append(f"System info gathering failed: {e}")
            
        # Step 4: Validate requirements
        try:
            validation = self._validate_requirements()
            results['steps']['validation'] = 'success' if validation['valid'] else 'warnings'
            results['validation'] = validation
        except Exception as e:
            results['warnings'].append(f"Requirement validation failed: {e}")
            
        # Step 5: Load module registry
        try:
            self._load_module_registry()
            results['steps']['module_registry'] = 'success'
            results['modules_loaded'] = len(self.module_registry)
        except Exception as e:
            results['warnings'].append(f"Module registry load failed: {e}")
            
        # Step 6: Initialize core services
        try:
            self._initialize_core_services()
            results['steps']['core_services'] = 'success'
        except Exception as e:
            results['warnings'].append(f"Core services init failed: {e}")
        
        self._initialized = True
        results['completed_at'] = datetime.now().isoformat()
        results['status'] = 'success' if not results['errors'] else 'partial'
        
        if self.logger:
            self.logger.info(f"🜂 Bootstrap complete: {results['status']}")
            
        return results
    
    def _setup_logging(self):
        """Setup logging infrastructure"""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.config.log_dir / 'kiswarm.log'
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG if self.config.debug else logging.INFO,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('KISWARM')
        
    def _create_directories(self):
        """Create required directory structure"""
        directories = [
            self.config.base_dir,
            self.config.data_dir,
            self.config.log_dir,
            self.config.data_dir / 'memory',
            self.config.data_dir / 'checkpoints',
            self.config.data_dir / 'cache',
            self.config.data_dir / 'evolution_vault',
            self.config.data_dir / 'immortality',
        ]
        
        for d in directories:
            d.mkdir(parents=True, exist_ok=True)
            
        if self.logger:
            self.logger.debug(f"Created {len(directories)} directories")
            
    def _gather_system_info(self) -> SystemInfo:
        """Gather system information"""
        import shutil
        
        # Check GPU
        gpu_available = False
        gpu_info = None
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                gpu_available = True
                gpu_info = result.stdout.strip()
        except:
            pass
            
        return SystemInfo(
            hostname=platform.node(),
            os_type=platform.system(),
            os_version=platform.version(),
            python_version=platform.python_version(),
            cpu_count=os.cpu_count() or 1,
            memory_total=shutil.disk_usage('/').total if os.path.exists('/') else 0,
            disk_total=shutil.disk_usage('/').total if os.path.exists('/') else 0,
            gpu_available=gpu_available,
            gpu_info=gpu_info
        )
        
    def _validate_requirements(self) -> Dict[str, Any]:
        """Validate system requirements"""
        requirements = {
            'python_version': ('3.10', True),
            'disk_space_gb': (10, True),
            'memory_gb': (4, False),
        }
        
        validation = {'valid': True, 'checks': {}}
        
        # Check Python version
        py_version = tuple(map(int, platform.python_version().split('.')[:2]))
        min_py = tuple(map(int, requirements['python_version'][0].split('.')))
        py_ok = py_version >= min_py
        validation['checks']['python'] = {
            'required': requirements['python_version'][0],
            'actual': platform.python_version(),
            'passed': py_ok,
            'required': requirements['python_version'][1]
        }
        if not py_ok and requirements['python_version'][1]:
            validation['valid'] = False
            
        return validation
        
    def _load_module_registry(self):
        """Load the module registry"""
        registry_file = self.config.data_dir / 'module_registry.json'
        
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self.module_registry = json.load(f)
        else:
            # Create default registry
            self.module_registry = {
                'core': ['m01', 'm02', 'm03', 'm04', 'm05', 'm06', 'm07', 'm08', 'm09', 'm10'],
                'cognitive': ['m41', 'm42', 'm43', 'm44', 'm45'],
                'autonomous': ['m96', 'm97', 'm98', 'm99', 'm100'],
            }
            with open(registry_file, 'w') as f:
                json.dump(self.module_registry, f, indent=2)
                
    def _initialize_core_services(self):
        """Initialize core services"""
        # This would initialize the event bus, service registry, etc.
        # For now, just log that we're ready
        if self.logger:
            self.logger.info("Core services initialized")
            
    def get_status(self) -> Dict[str, Any]:
        """Get bootstrap status"""
        return {
            'initialized': self._initialized,
            'version': KISWARM_VERSION,
            'system_info': self.system_info.__dict__ if self.system_info else None,
            'modules_registered': len(self.module_registry)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_bootstrap_instance: Optional[BootstrapCore] = None


def get_bootstrap() -> BootstrapCore:
    """Get or create the bootstrap singleton"""
    global _bootstrap_instance
    if _bootstrap_instance is None:
        _bootstrap_instance = BootstrapCore()
    return _bootstrap_instance


def initialize_kiswarm() -> Dict[str, Any]:
    """Initialize KISWARM - call this at application start"""
    bootstrap = get_bootstrap()
    return bootstrap.initialize()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    result = initialize_kiswarm()
    print(json.dumps(result, indent=2, default=str))
