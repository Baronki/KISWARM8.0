# KISWARM v6.3.5 "GWS_IRON_MOUNTAIN" - Complete Colab Field Test

## Mission Objective
Deploy and validate KISWARM v6.3.5 on Google Colab with:
- Complete KIInstaller automated deployment
- 6-Layer Zero-Failure Mesh validation
- MuninnDB Cognitive Memory testing
- Full security hardening
- Bug detection and reporting

## Target Environment
- Platform: Google Colab (Free Tier or Pro)
- Python: 3.10+
- Memory: 12GB+ RAM
- GPU: Optional (T4 for LLM testing)

---

## PHASE 1: Environment Setup (5 minutes)

```python
# CELL 1: System Information & Prerequisites
# ============================================================
import sys
import os
import subprocess
import platform
import datetime

print("=" * 70)
print("🚀 KISWARM v6.3.5 GWS_IRON_MOUNTAIN - Field Test Initiation")
print("=" * 70)
print(f"Timestamp: {datetime.datetime.utcnow().isoformat()}")
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.architecture()}")

# Check available resources
import psutil
print(f"\n📊 System Resources:")
print(f"  CPU Cores: {psutil.cpu_count()}")
print(f"  Total RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
print(f"  Available RAM: {psutil.virtual_memory().available / (1024**3):.1f} GB")
print(f"  Disk Free: {psutil.disk_usage('/').free / (1024**3):.1f} GB")

# GPU Check
try:
    gpu_info = subprocess.check_output(['nvidia-smi'], stderr=subprocess.DEVNULL).decode()
    print(f"\n🎮 GPU Available:")
    for line in gpu_info.split('\n')[:10]:
        if line.strip():
            print(f"  {line}")
except:
    print("\n⚠️ No GPU detected - CPU-only mode")

print("\n" + "=" * 70)
```

```python
# CELL 2: Repository Clone & Structure Verification
# ============================================================
import os
import subprocess

# Repository details
REPO_URL = "https://github.com/Baronki/KISWARM6.0.git"
REPO_DIR = "/content/KISWARM6.0"

print("📦 Cloning KISWARM6.0 Repository...")
print(f"Repository: {REPO_URL}")

# Clean any existing installation
if os.path.exists(REPO_DIR):
    print("  Removing existing installation...")
    subprocess.run(["rm", "-rf", REPO_DIR], check=True)

# Clone repository
result = subprocess.run(
    ["git", "clone", "--depth", "1", REPO_URL, REPO_DIR],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Repository cloned successfully")
else:
    print(f"❌ Clone failed: {result.stderr}")

# Verify structure
print("\n📁 Repository Structure:")
os.chdir(REPO_DIR)

# List key directories
key_dirs = [
    "backend/python/sentinel",
    "backend/python/kibank", 
    "backend/python/mesh",
    "backend/python/cognitive",
    "backend/python/industrial",
    "tests",
    "docs",
    "scripts"
]

for d in key_dirs:
    path = os.path.join(REPO_DIR, d)
    exists = "✅" if os.path.exists(path) else "❌"
    file_count = len([f for f in os.listdir(path) if f.endswith('.py')]) if os.path.exists(path) else 0
    print(f"  {exists} {d} ({file_count} Python files)")

# Check specific v6.3.5 files
print("\n🔍 v6.3.5 Feature Verification:")
v635_files = [
    "backend/python/mesh/__init__.py",
    "backend/python/mesh/base_layer.py",
    "backend/python/mesh/zero_failure_mesh.py",
    "backend/python/mesh/layer0_local.py",
    "backend/python/mesh/layer4_email.py",
    "backend/python/cognitive/__init__.py",
    "backend/python/cognitive/muninn_adapter.py",
    "tests/test_mesh_layers.py",
    "docs/MESH_API.md",
    "docs/COGNITIVE_MEMORY_API.md"
]

for f in v635_files:
    path = os.path.join(REPO_DIR, f)
    exists = "✅" if os.path.exists(path) else "❌"
    print(f"  {exists} {f}")

print("\n" + "=" * 70)
```

```python
# CELL 3: Python Environment Setup
# ============================================================
import subprocess
import sys

print("🔧 Setting up Python Environment...")

# Install system dependencies
system_deps = [
    "build-essential",
    "python3-dev",
    "libffi-dev",
    "libssl-dev",
    "libpq-dev",
    "sqlite3",
    "libsqlite3-dev"
]

print("\n📦 Installing system dependencies...")
for dep in system_deps:
    result = subprocess.run(
        ["apt-get", "install", "-y", dep],
        capture_output=True,
        env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    )
    status = "✅" if result.returncode == 0 else "⚠️"
    print(f"  {status} {dep}")

# Upgrade pip
print("\n📦 Upgrading pip...")
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)

# Core Python dependencies
python_deps = [
    # Core
    "flask>=2.3.0",
    "flask-cors>=4.0.0",
    "flask-restful>=0.3.10",
    "gunicorn>=21.0.0",
    
    # Async
    "aiohttp>=3.9.0",
    "asyncio>=3.4.3",
    "aiofiles>=23.0.0",
    
    # Database
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",
    
    # Security
    "cryptography>=41.0.0",
    "pyjwt>=2.8.0",
    "passlib>=1.7.4",
    "bcrypt>=4.1.0",
    
    # Data Processing
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
    
    # ML/AI
    "transformers>=4.35.0",
    "torch>=2.1.0",
    "sentence-transformers>=2.2.0",
    
    # Utilities
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "httpx>=0.25.0",
    
    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    
    # Monitoring
    "prometheus-client>=0.18.0",
    "psutil>=5.9.0"
]

print("\n📦 Installing Python dependencies...")
for dep in python_deps:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", dep],
        capture_output=True,
        text=True
    )
    status = "✅" if result.returncode == 0 else "❌"
    print(f"  {status} {dep.split('>=')[0]}")

# Install additional requirements from repo
req_file = os.path.join(REPO_DIR, "backend", "requirements.txt")
if os.path.exists(req_file):
    print(f"\n📦 Installing from requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req_file],
        capture_output=True,
        text=True
    )
    status = "✅" if result.returncode == 0 else "⚠️"
    print(f"  {status} requirements.txt installed")

print("\n" + "=" * 70)
```

---

## PHASE 2: KIInstaller Deployment (10 minutes)

```python
# CELL 4: KIInstaller Configuration
# ============================================================
import os
import json

print("⚙️ Configuring KIInstaller...")

# Set environment variables
os.environ['KISWARM_VERSION'] = '6.3.5'
os.environ['KISWARM_CODENAME'] = 'GWS_IRON_MOUNTAIN'
os.environ['KISWARM_ENV'] = 'colab'
os.environ['KISWARM_HOME'] = REPO_DIR
os.environ['KISWARM_DATA_DIR'] = '/content/kiswarm_data'
os.environ['KISWARM_LOG_DIR'] = '/content/kiswarm_logs'
os.environ['KISWARM_DB_PATH'] = '/content/kiswarm_data/kiswarm.db'
os.environ['MUNINN_DB_PATH'] = '/content/kiswarm_data/muninndb.sqlite'

# Create directories
dirs_to_create = [
    os.environ['KISWARM_DATA_DIR'],
    os.environ['KISWARM_LOG_DIR'],
    os.path.join(os.environ['KISWARM_DATA_DIR'], 'sentinel'),
    os.path.join(os.environ['KISWARM_DATA_DIR'], 'mesh'),
    os.path.join(os.environ['KISWARM_DATA_DIR'], 'cognitive'),
    os.path.join(os.environ['KISWARM_DATA_DIR'], 'kibank'),
]

print("\n📁 Creating directory structure...")
for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)
    print(f"  ✅ {d}")

# Create configuration file
config = {
    "version": "6.3.5",
    "codename": "GWS_IRON_MOUNTAIN",
    "environment": "colab",
    "paths": {
        "home": os.environ['KISWARM_HOME'],
        "data": os.environ['KISWARM_DATA_DIR'],
        "logs": os.environ['KISWARM_LOG_DIR'],
        "database": os.environ['KISWARM_DB_PATH'],
        "muninn_db": os.environ['MUNINN_DB_PATH']
    },
    "mesh": {
        "enabled": True,
        "layers": {
            "layer0": {"enabled": True, "priority": 0, "name": "local_master"},
            "layer1": {"enabled": False, "priority": 1, "name": "gemini_cli"},
            "layer2": {"enabled": False, "priority": 2, "name": "github_actions"},
            "layer3": {"enabled": False, "priority": 3, "name": "p2p_mesh"},
            "layer4": {"enabled": False, "priority": 4, "name": "email_beacon"},
            "layer5": {"enabled": False, "priority": 5, "name": "gws_iron_mountain"}
        },
        "circuit_breaker": {
            "failure_threshold": 5,
            "recovery_timeout_ms": 60000,
            "half_open_max_calls": 3
        }
    },
    "cognitive": {
        "enabled": True,
        "muninn_db": os.environ['MUNINN_DB_PATH'],
        "default_stability": 0.5,
        "learning_rate": 0.1
    },
    "security": {
        "hardening_enabled": True,
        "audit_enabled": True,
        "crypto_ledger": True
    }
}

config_path = os.path.join(os.environ['KISWARM_DATA_DIR'], 'kiswarm_config.json')
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n📄 Configuration saved to: {config_path}")
print(json.dumps(config, indent=2))

print("\n" + "=" * 70)
```

```python
# CELL 5: KIInstaller Execution - Module Import Tests
# ============================================================
import sys
import os
import importlib.util
import traceback

# Add backend to path
sys.path.insert(0, os.path.join(REPO_DIR, "backend", "python"))

print("🚀 Executing KIInstaller Module Tests...")
print("=" * 70)

# Bug tracking
bugs_found = []
warnings_found = []

def log_bug(module, error, severity="ERROR", traceback_str=None):
    """Log a bug for reporting"""
    bug = {
        "module": module,
        "error": str(error),
        "severity": severity,
        "traceback": traceback_str
    }
    bugs_found.append(bug)
    print(f"  🐛 [{severity}] {module}: {error}")

def log_warning(module, message):
    """Log a warning"""
    warning = {
        "module": module,
        "message": message
    }
    warnings_found.append(warning)
    print(f"  ⚠️ {module}: {message}")

# Test imports for all modules
print("\n📦 Testing Module Imports...")

# Sentinel modules (M1-M57) - Critical ones
sentinel_modules = [
    "actor_critic", "crypto_ledger", "digital_thread",
    "hexstrike_guard", "ics_shield", "installer_agent",
    "byzantine_aggregator", "knowledge_graph", "swarm_auditor",
    "swarm_immortality_kernel", "prompt_firewall", "sentinel_bridge"
]

sentinel_success = 0
sentinel_failed = []

for module_name in sentinel_modules:
    try:
        module = importlib.import_module(f"sentinel.{module_name}")
        sentinel_success += 1
        print(f"  ✅ sentinel.{module_name}")
    except Exception as e:
        sentinel_failed.append(module_name)
        log_bug(f"sentinel.{module_name}", e, "ERROR", traceback.format_exc())

print(f"\n📊 Sentinel Modules: {sentinel_success}/{len(sentinel_modules)} imported successfully")

# Mesh modules (v6.3.5)
print("\n📦 Testing Mesh Modules (v6.3.5)...")
mesh_modules = ["mesh", "mesh.base_layer", "mesh.zero_failure_mesh", 
                "mesh.layer0_local", "mesh.layer4_email"]

mesh_success = 0
for module_name in mesh_modules:
    try:
        module = importlib.import_module(module_name)
        mesh_success += 1
        print(f"  ✅ {module_name}")
    except Exception as e:
        log_bug(module_name, e, "ERROR", traceback.format_exc())

print(f"\n📊 Mesh Modules: {mesh_success}/{len(mesh_modules)} imported successfully")

# Cognitive modules (v6.3.5)
print("\n📦 Testing Cognitive Modules (v6.3.5)...")
cognitive_modules = ["cognitive", "cognitive.muninn_adapter"]

cognitive_success = 0
for module_name in cognitive_modules:
    try:
        module = importlib.import_module(module_name)
        cognitive_success += 1
        print(f"  ✅ {module_name}")
    except Exception as e:
        log_bug(module_name, e, "ERROR", traceback.format_exc())

print(f"\n📊 Cognitive Modules: {cognitive_success}/{len(cognitive_modules)} imported successfully")

print("\n" + "=" * 70)
print(f"📊 Import Summary: {sentinel_success + mesh_success + cognitive_success} modules imported")
print(f"🐛 Bugs Found: {len(bugs_found)}")
print(f"⚠️ Warnings: {len(warnings_found)}")
```

---

## PHASE 3: Mesh Layer Testing (5 minutes)

```python
# CELL 6: Zero-Failure Mesh Layer Tests
# ============================================================
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(REPO_DIR, "backend", "python"))

print("🛡️ Testing 6-Layer Zero-Failure Mesh...")
print("=" * 70)

async def test_mesh_layers():
    from mesh.base_layer import BaseLayer, LayerConfig, CircuitState
    from mesh.zero_failure_mesh import ZeroFailureMesh, MeshConfig
    
    test_results = []
    
    # Test 1: BaseLayer Circuit Breaker
    print("\n🧪 Test 1: BaseLayer Circuit Breaker")
    try:
        class TestLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                return await request()
        
        config = LayerConfig(name="test_layer", priority=1, failure_threshold=3)
        layer = TestLayer(config)
        
        assert layer.state == CircuitState.CLOSED, "Initial state should be CLOSED"
        assert layer.is_available == True, "Layer should be available"
        
        async def success_req():
            return {"status": "ok"}
        
        result = await layer.execute(success_req)
        assert result["status"] == "ok", "Request should succeed"
        
        print("  ✅ Circuit breaker states work correctly")
        print("  ✅ Request execution works correctly")
        test_results.append(("BaseLayer", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("BaseLayer", "FAILED", str(e)))
    
    # Test 2: Circuit Opens on Failures
    print("\n🧪 Test 2: Circuit Opens on Failures")
    try:
        class FailingLayer(BaseLayer):
            async def _execute_impl(self, request, *args, **kwargs):
                raise Exception("Simulated failure")
        
        config = LayerConfig(name="failing", priority=1, failure_threshold=3)
        layer = FailingLayer(config)
        
        for i in range(3):
            try:
                await layer.execute(lambda: None)
            except:
                pass
        
        assert layer.state == CircuitState.OPEN, "Circuit should be OPEN"
        assert layer.is_available == False, "Layer should be unavailable"
        
        print("  ✅ Circuit opens correctly after failure threshold")
        test_results.append(("CircuitOpen", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("CircuitOpen", "FAILED", str(e)))
    
    # Test 3: ZeroFailureMesh Coordination
    print("\n🧪 Test 3: ZeroFailureMesh Coordination")
    try:
        class MockLayer(BaseLayer):
            def __init__(self, name, priority, should_fail=False):
                config = LayerConfig(name=name, priority=priority)
                super().__init__(config)
                self.should_fail = should_fail
            
            async def _execute_impl(self, request, *args, **kwargs):
                if self.should_fail:
                    raise Exception(f"{self.name} failed")
                return {"layer": self.name}
        
        mesh = ZeroFailureMesh(MeshConfig(max_retries=1))
        mesh.register_layer(MockLayer("low", priority=10))
        mesh.register_layer(MockLayer("high", priority=1))
        
        assert mesh.layers[0].name == "high", "Should sort by priority"
        print("  ✅ Layers sorted by priority correctly")
        
        await mesh.initialize()
        result = await mesh.execute(lambda: None)
        assert result["layer"] == "high", "Should use highest priority layer"
        
        print("  ✅ Mesh executes on highest priority layer")
        test_results.append(("MeshCoordination", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("MeshCoordination", "FAILED", str(e)))
    
    # Test 4: Mesh Failover
    print("\n🧪 Test 4: Mesh Failover")
    try:
        mesh = ZeroFailureMesh(MeshConfig(max_retries=1))
        mesh.register_layer(MockLayer("failing", priority=1, should_fail=True))
        mesh.register_layer(MockLayer("backup", priority=2, should_fail=False))
        
        await mesh.initialize()
        result = await mesh.execute(lambda: None)
        assert result["layer"] == "backup", "Should failover to backup"
        
        print("  ✅ Failover to backup layer works correctly")
        test_results.append(("MeshFailover", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("MeshFailover", "FAILED", str(e)))
    
    # Test 5: Layer0 Local Master
    print("\n🧪 Test 5: Layer0 Local Master")
    try:
        from mesh.layer0_local import Layer0LocalMaster
        
        layer = Layer0LocalMaster(base_url="http://localhost:5000")
        assert layer.name == "local_master"
        assert layer.priority == 0
        
        status = layer.get_status()
        assert status["layer_type"] == "local_master"
        
        print("  ✅ Layer0 initialized correctly")
        test_results.append(("Layer0", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("Layer0", "FAILED", str(e)))
    
    # Test 6: Layer4 Email Beacon
    print("\n🧪 Test 6: Layer4 Email Beacon")
    try:
        from mesh.layer4_email import Layer4EmailBeacon
        
        layer = Layer4EmailBeacon(beacon_address="test@test.com")
        assert layer.name == "email_beacon"
        assert layer.priority == 4
        
        print("  ✅ Layer4 initialized correctly")
        test_results.append(("Layer4", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        test_results.append(("Layer4", "FAILED", str(e)))
    
    return test_results

mesh_test_results = asyncio.run(test_mesh_layers())

print("\n" + "=" * 70)
print("📊 Mesh Test Summary:")
passed = sum(1 for r in mesh_test_results if r[1] == "PASSED")
failed = sum(1 for r in mesh_test_results if r[1] == "FAILED")
print(f"  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")

for name, status, error in mesh_test_results:
    if status == "FAILED":
        log_bug(f"Mesh.{name}", error, "ERROR")
```

---

## PHASE 4: MuninnDB Cognitive Memory Testing (5 minutes)

```python
# CELL 7: MuninnDB Cognitive Memory Tests
# ============================================================
import sys
import os
import math
import time

sys.path.insert(0, os.path.join(REPO_DIR, "backend", "python"))

print("🧠 Testing MuninnDB Cognitive Memory...")
print("=" * 70)

cognitive_test_results = []

try:
    from cognitive import MuninnDBAdapter, MemoryEntry, MemoryType
    
    db_path = "/content/kiswarm_data/test_muninndb.sqlite"
    memory = MuninnDBAdapter(db_path)
    
    # Test 1: CRUD Operations
    print("\n🧪 Test 1: CRUD Operations")
    try:
        entry = MemoryEntry(
            memory_type="semantic",
            content="KISWARM v6.3.5 released with Zero-Failure Mesh",
            tags=["release", "mesh", "v6.3.5"],
            confidence=0.95,
            stability=0.8
        )
        memory_id = memory.create(entry)
        assert memory_id > 0, "Create should return valid ID"
        print("  ✅ Memory created successfully")
        
        read_entry = memory.read(memory_id)
        assert read_entry.content == entry.content
        print("  ✅ Memory read successfully")
        
        memory.update(memory_id, confidence=0.98)
        updated = memory.read(memory_id, update_access=False)
        assert updated.confidence == 0.98
        print("  ✅ Memory updated successfully")
        
        deleted = memory.delete(memory_id)
        assert deleted == True
        print("  ✅ Memory deleted successfully")
        
        cognitive_test_results.append(("CRUD", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        cognitive_test_results.append(("CRUD", "FAILED", str(e)))
    
    # Test 2: Ebbinghaus Forgetting Curve
    print("\n🧪 Test 2: Ebbinghaus Forgetting Curve")
    try:
        entry = MemoryEntry(
            memory_type="semantic",
            content="Test decay calculation",
            stability=1.0,
            confidence=0.9
        )
        memory_id = memory.create(entry)
        
        retention = memory.calculate_retention(memory_id)
        assert retention > 0.99, f"Initial retention should be ~1.0"
        print(f"  ✅ Initial retention: {retention:.4f}")
        
        new_strength = memory.apply_decay(memory_id)
        print(f"  ✅ Applied decay, new strength: {new_strength:.4f}")
        
        report = memory.get_decay_report()
        print(f"  ✅ Decay report: {report['total_memories']} memories")
        
        cognitive_test_results.append(("Ebbinghaus", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        cognitive_test_results.append(("Ebbinghaus", "FAILED", str(e)))
    
    # Test 3: Hebbian Learning
    print("\n🧪 Test 3: Hebbian Learning")
    try:
        entry1 = MemoryEntry(content="Memory A", stability=0.5)
        entry2 = MemoryEntry(content="Memory B", stability=0.5)
        
        id1 = memory.create(entry1)
        id2 = memory.create(entry2)
        
        for _ in range(5):
            memory.strengthen_association(id1, id2)
        
        associations = memory.get_associated_memories(id1, min_strength=0.0)
        assert len(associations) > 0, "Should have associations"
        
        assoc_id, strength = associations[0]
        print(f"  ✅ Association created with strength: {strength:.4f}")
        
        cognitive_test_results.append(("Hebbian", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        cognitive_test_results.append(("Hebbian", "FAILED", str(e)))
    
    # Test 4: Bayesian Confidence
    print("\n🧪 Test 4: Bayesian Confidence Update")
    try:
        entry = MemoryEntry(content="Test confidence", confidence=0.5)
        memory_id = memory.create(entry)
        
        memory.update_confidence(memory_id, evidence=0.9, prior_weight=0.5)
        
        updated = memory.read(memory_id, update_access=False)
        expected = 0.5 * 0.5 + (1 - 0.5) * 0.9  # = 0.70
        
        assert abs(updated.confidence - expected) < 0.01
        print(f"  ✅ Bayesian update: 0.5 -> {updated.confidence:.4f}")
        
        cognitive_test_results.append(("Bayesian", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        cognitive_test_results.append(("Bayesian", "FAILED", str(e)))
    
    # Test 5: Search Operations
    print("\n🧪 Test 5: Search Operations")
    try:
        for i in range(5):
            entry = MemoryEntry(
                memory_type="semantic" if i % 2 == 0 else "episodic",
                content=f"Test memory {i} for mesh",
                tags=["test", f"tag{i}"]
            )
            memory.create(entry)
        
        results = memory.search("mesh", limit=10)
        assert len(results) > 0
        print(f"  ✅ Content search found {len(results)} results")
        
        cognitive_test_results.append(("Search", "PASSED", None))
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        cognitive_test_results.append(("Search", "FAILED", str(e)))
    
    memory.close()
    
except Exception as e:
    print(f"❌ Cognitive module import failed: {e}")

print("\n" + "=" * 70)
print("📊 Cognitive Test Summary:")
passed = sum(1 for r in cognitive_test_results if r[1] == "PASSED")
failed = sum(1 for r in cognitive_test_results if r[1] == "FAILED")
print(f"  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")
```

---

## PHASE 5: Security Hardening (5 minutes)

```python
# CELL 8: Security Hardening Tests
# ============================================================
import sys
import os

sys.path.insert(0, os.path.join(REPO_DIR, "backend", "python"))

print("🔐 Testing Security Hardening...")
print("=" * 70)

security_test_results = []

# Test 1: Crypto Ledger
print("\n🧪 Test 1: Cryptographic Operations")
try:
    from sentinel.crypto_ledger import CryptoLedger
    
    ledger = CryptoLedger()
    
    test_data = "KISWARM v6.3.5 Security Test"
    hash_result = ledger.generate_hash(test_data)
    assert len(hash_result) == 64, "SHA-256 hash should be 64 chars"
    print(f"  ✅ Hash generation: {hash_result[:32]}...")
    
    entry_id = ledger.add_entry(
        operation="security_test",
        data={"test": True, "version": "6.3.5"},
        signature=ledger.sign_entry(test_data)
    )
    print(f"  ✅ Ledger entry created: {entry_id}")
    
    security_test_results.append(("Crypto", "PASSED", None))
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    security_test_results.append(("Crypto", "FAILED", str(e)))

# Test 2: Byzantine Consensus
print("\n🧪 Test 2: Byzantine Consensus")
try:
    from sentinel.byzantine_aggregator import ByzantineAggregator
    
    aggregator = ByzantineAggregator()
    
    votes = [
        {"node_id": "node1", "value": "approve", "signature": "sig1"},
        {"node_id": "node2", "value": "approve", "signature": "sig2"},
        {"node_id": "node3", "value": "approve", "signature": "sig3"},
    ]
    
    result = aggregator.reach_consensus(votes, threshold=0.66)
    assert result["consensus"] == True
    print(f"  ✅ Byzantine consensus reached")
    
    security_test_results.append(("Byzantine", "PASSED", None))
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    security_test_results.append(("Byzantine", "FAILED", str(e)))

# Test 3: HexStrike Guard
print("\n🧪 Test 3: HexStrike Guard")
try:
    from sentinel.hexstrike_guard import HexStrikeGuard
    
    guard = HexStrikeGuard()
    
    test_payload = {
        "type": "request",
        "source": "external",
        "payload": "SELECT * FROM users --"
    }
    
    analysis = guard.analyze(test_payload)
    print(f"  ✅ Threat analysis completed")
    
    security_test_results.append(("HexStrike", "PASSED", None))
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    security_test_results.append(("HexStrike", "FAILED", str(e)))

# Test 4: Prompt Firewall
print("\n🧪 Test 4: Prompt Firewall")
try:
    from sentinel.prompt_firewall import PromptFirewall
    
    firewall = PromptFirewall()
    
    benign = "What is the weather today?"
    result = firewall.check(benign)
    print(f"  ✅ Benign prompt check: {result['safe']}")
    
    security_test_results.append(("PromptFirewall", "PASSED", None))
    
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    security_test_results.append(("PromptFirewall", "FAILED", str(e)))

print("\n" + "=" * 70)
print("📊 Security Test Summary:")
passed = sum(1 for r in security_test_results if r[1] == "PASSED")
failed = sum(1 for r in security_test_results if r[1] == "FAILED")
print(f"  ✅ Passed: {passed}")
print(f"  ❌ Failed: {failed}")
```

---

## PHASE 6: Bug Report Generation (2 minutes)

```python
# CELL 9: Bug Report Generation
# ============================================================
import json
import datetime

print("📋 Generating Field Test Bug Report...")
print("=" * 70)

# Compile all test results
report = {
    "metadata": {
        "version": "6.3.5",
        "codename": "GWS_IRON_MOUNTAIN",
        "environment": "Google Colab",
        "timestamp": datetime.datetime.utcnow().isoformat()
    },
    "summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "bugs_found": len(bugs_found) if 'bugs_found' in dir() else 0,
        "warnings": len(warnings_found) if 'warnings_found' in dir() else 0
    },
    "test_results": {
        "mesh": mesh_test_results if 'mesh_test_results' in dir() else [],
        "cognitive": cognitive_test_results if 'cognitive_test_results' in dir() else [],
        "security": security_test_results if 'security_test_results' in dir() else []
    },
    "bugs": bugs_found if 'bugs_found' in dir() else [],
    "warnings": warnings_found if 'warnings_found' in dir() else []
}

# Calculate totals
for category, results in report["test_results"].items():
    for test_name, status, error in results:
        report["summary"]["total_tests"] += 1
        if status == "PASSED":
            report["summary"]["passed"] += 1
        else:
            report["summary"]["failed"] += 1

# Print summary
print(f"\n📊 TEST SUMMARY:")
print(f"  Total Tests: {report['summary']['total_tests']}")
print(f"  ✅ Passed: {report['summary']['passed']}")
print(f"  ❌ Failed: {report['summary']['failed']}")
print(f"  Pass Rate: {report['summary']['passed']/max(report['summary']['total_tests'],1)*100:.1f}%")

# Save reports
report_path = "/content/kiswarm_data/field_test_report.json"
with open(report_path, 'w') as f:
    json.dump(report, f, indent=2, default=str)
print(f"\n📄 Report saved: {report_path}")

# Markdown report
md_report = f"""# KISWARM v6.3.5 Field Test Report

**Date**: {report['metadata']['timestamp']}
**Environment**: {report['metadata']['environment']}
**Version**: {report['metadata']['version']} "{report['metadata']['codename']}"

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {report['summary']['total_tests']} |
| Passed | {report['summary']['passed']} |
| Failed | {report['summary']['failed']} |
| Pass Rate | {report['summary']['passed']/max(report['summary']['total_tests'],1)*100:.1f}% |
| Bugs Found | {report['summary']['bugs_found']} |

## Bugs

"""
for bug in report['bugs']:
    md_report += f"- **[{bug['severity']}]** {bug['module']}: {bug['error'][:100]}\n"

md_path = "/content/kiswarm_data/FIELD_TEST_REPORT.md"
with open(md_path, 'w') as f:
    f.write(md_report)
print(f"📄 Markdown saved: {md_path}")

# Final status
if report['summary']['failed'] == 0:
    print("\n🎉 KISWARM v6.3.5 FIELD TEST PASSED!")
elif report['summary']['passed'] / report['summary']['total_tests'] >= 0.8:
    print("\n⚠️ FIELD TEST PASSED WITH WARNINGS")
else:
    print("\n❌ FIELD TEST FAILED - Review bugs above")

print("\n" + "=" * 70)
```

```python
# CELL 10: Download Reports
# ============================================================
from google.colab import files

print("📥 Downloading Field Test Reports...")

files.download("/content/kiswarm_data/field_test_report.json")
files.download("/content/kiswarm_data/FIELD_TEST_REPORT.md")

print("✅ Reports downloaded successfully!")
print("=" * 70)
print("📊 KISWARM v6.3.5 GWS_IRON_MOUNTAIN Field Test Complete")
print("=" * 70)
```

---

## Instructions for Gemini CLI on Colab

1. **Create new Colab notebook**: Go to https://colab.research.google.com
2. **Copy all cells** sequentially into the notebook
3. **Run cells in order** from CELL 1 to CELL 10
4. **Review output** at each phase
5. **Download reports** at the end

## Expected Results

| Component | Tests | Expected Pass Rate |
|-----------|-------|-------------------|
| Mesh Layers | 6 | 100% |
| Cognitive Memory | 5 | 100% |
| Security | 4 | 90%+ |
| **Total** | 15 | 90%+ |

## Bug Severity Levels

| Severity | Description | Action |
|----------|-------------|--------|
| CRITICAL | System cannot function | Immediate fix required |
| ERROR | Module/test failure | Fix before deployment |
| WARNING | Suboptimal behavior | Review recommended |

---

**Field Test Protocol v6.3.5 - KISWARM GWS_IRON_MOUNTAIN**
