# M81: KiloCode Parallel Safety Bridge

## Overview

**Module ID**: M81  
**Module Name**: KiloCode Parallel Safety Bridge  
**File**: `backend/python/kibank/m81_kilocode_bridge.py`  
**Version**: 6.4.0-LIBERATED  
**Lines**: 1,100+  

### Purpose

A **bidirectional communication bridge** between KISWARM and KiloCode CLI that provides a **zero-API safety net** for KISWARM scouts and all other agents. This module enables KISWARM to leverage KiloCode's capabilities for code review, debugging, security scanning, and autonomous operations without any external API dependencies.

---

## Key Features

### 1. Zero API Design
- **No external API keys required** - runs completely locally
- Uses subprocess to execute KiloCode CLI commands
- Works offline after initial installation
- No rate limits, no quotas, no external dependencies

### 2. Bidirectional Communication
```
┌─────────────┐                    ┌─────────────┐
│  KISWARM    │  ←──────────────→  │  KiloCode   │
│             │                    │    CLI      │
├─────────────┤                    ├─────────────┤
│ M60-M80     │  Code Review       │ AI Coding   │
│ Modules     │  Debug Requests    │ Assistant   │
│             │  Security Scans    │             │
│             │  Code Generation   │             │
└─────────────┘                    └─────────────┘
```

### 3. Multi-Environment Support
| Environment | Detection | Auto-Config |
|-------------|-----------|-------------|
| Docker | `/.dockerenv` | `KILOCODE_AUTO_MODE=true` |
| Kubernetes | `KUBERNETES_SERVICE_HOST` | Auto-enabled |
| Google Colab | `COLAB_GPU` | Autonomous mode |
| WSL2 | `WSL_DISTRO_NAME` | Native mode |
| Python venv | `VIRTUAL_ENV` | venv-aware |
| Native Linux | Default | Standard mode |

### 4. Priority Queue System
| Priority | Value | Use Case |
|----------|-------|----------|
| LOW | 1 | Heartbeats, status updates |
| NORMAL | 5 | Code reviews, explanations |
| HIGH | 10 | Debug requests, refactoring |
| CRITICAL | 100 | Security scans, vulnerabilities |
| EMERGENCY | 1000 | Security alerts, crash recovery |

### 5. Safety Net Mechanisms
- **Pre-execution validation**: Check code before running
- **Post-execution review**: Analyze results after completion
- **Error recovery**: Get suggestions when things fail
- **Security scanning**: Detect vulnerabilities before deployment

---

## Architecture

### Class Hierarchy

```
KiloCodeBridge (Main Class)
├── KiloCodeInstaller (Installation Manager)
├── MessageQueue (Priority-based Queue)
├── BridgeMessage (Message Dataclass)
└── KiloCodeConfig (Configuration Dataclass)

Enums:
├── BridgeStatus: DISCONNECTED, CONNECTING, CONNECTED, ERROR, BUSY
├── MessageType: 16 types (CODE_REVIEW, DEBUG_REQUEST, etc.)
└── Priority: 5 levels (LOW, NORMAL, HIGH, CRITICAL, EMERGENCY)
```

### Message Types

#### KISWARM → KiloCode
| Type | Purpose | Requires Response |
|------|---------|-------------------|
| `CODE_REVIEW` | Code quality analysis | Yes |
| `DEBUG_REQUEST` | Debug error assistance | Yes |
| `SECURITY_SCAN` | Vulnerability detection | Yes |
| `GENERATE_CODE` | Code generation from prompt | Yes |
| `EXPLAIN_CODE` | Code explanation | Yes |
| `REFACTOR_REQUEST` | Code refactoring suggestions | Yes |
| `TEST_GENERATE` | Test case generation | Yes |

#### KiloCode → KISWARM
| Type | Purpose | Requires Response |
|------|---------|-------------------|
| `FEEDBACK` | General feedback | No |
| `WARNING` | Warning messages | No |
| `ERROR_REPORT` | Error reports | No |
| `SUGGESTION` | Improvement suggestions | No |
| `SECURITY_ALERT` | Critical security findings | Yes |

#### Bidirectional
| Type | Purpose | Requires Response |
|------|---------|-------------------|
| `HEARTBEAT` | Connection health check | Yes |
| `STATUS_UPDATE` | Status notifications | No |
| `SYNC_REQUEST` | State synchronization | Yes |

---

## API Reference

### Initialization

```python
from kibank.m81_kilocode_bridge import (
    KiloCodeBridge,
    KiloCodeConfig,
    get_kilocode_bridge,
    initialize_kilocode_bridge
)

# Method 1: Direct instantiation
config = KiloCodeConfig(
    autonomous_mode=False,
    enable_safety_net=True,
    max_queue_size=1000
)
bridge = KiloCodeBridge(config)
bridge.start()

# Method 2: Singleton pattern (recommended)
bridge = get_kilocode_bridge()
bridge.start()

# Method 3: Auto-initialization
bridge = initialize_kilocode_bridge(auto_start=True)
```

### Core Methods

#### `code_review(code: str, context: dict = None) -> dict`
Request code review from KiloCode.

```python
result = await bridge.code_review(
    code="def process_data(x): return x * 2",
    context={"language": "python", "purpose": "data processing"}
)
# Returns: {"issues": [...], "suggestions": [...], "score": 85}
```

#### `debug_request(error: str, code: str = None, context: dict = None) -> dict`
Request debugging assistance.

```python
result = await bridge.debug_request(
    error="NameError: name 'undefined_var' is not defined",
    code="print(undefined_var)",
    context={"file": "main.py", "line": 42}
)
# Returns: {"diagnosis": "...", "fix": "...", "explanation": "..."}
```

#### `security_scan(code: str, scan_type: str = "full") -> dict`
Request security vulnerability scan.

```python
result = await bridge.security_scan(
    code=user_input_code,
    scan_type="full"  # Options: "quick", "full", "deep"
)
# Returns: {"vulnerabilities": [...], "risk_level": "MEDIUM", "fixes": [...]}
```

#### `generate_code(prompt: str, language: str = "python", context: dict = None) -> dict`
Request code generation.

```python
result = await bridge.generate_code(
    prompt="Create a function that validates email addresses",
    language="python",
    context={"framework": "fastapi"}
)
# Returns: {"code": "...", "explanation": "...", "tests": "..."}
```

#### `execute_kilo_command(command: str, auto_mode: bool = False, timeout: float = 300.0) -> dict`
Execute a KiloCode CLI command directly.

```python
# Interactive mode
result = bridge.execute_kilo_command("analyze this codebase")

# Autonomous mode (for CI/CD)
result = bridge.execute_kilo_command(
    "run tests and fix any failures",
    auto_mode=True,
    timeout=600.0
)
# Returns: {"success": True, "output": "...", "error": ""}
```

### Safety Methods

#### `safety_check(operation: str, details: dict) -> bool`
Perform a safety check before a critical operation.

```python
is_safe = await bridge.safety_check(
    operation="database_migration",
    details={
        "tables": ["users", "transactions"],
        "action": "ALTER TABLE"
    }
)
# Returns: True if operation is safe to proceed
```

#### `fallback_handler(operation: str, error: Exception) -> dict`
Get recovery suggestions when errors occur.

```python
try:
    risky_operation()
except Exception as e:
    suggestion = bridge.fallback_handler("risky_operation", e)
    print(suggestion["suggestion"])
```

### Utility Methods

#### `get_status_report() -> dict`
Get comprehensive bridge status.

```python
report = bridge.get_status_report()
# Returns:
# {
#     "bridge_status": "connected",
#     "kilocode_installed": True,
#     "kilocode_version": "v7.0.47",
#     "queue_size": 5,
#     "running": True,
#     "config": {...}
# }
```

#### `detect_environment() -> dict`
Detect the current execution environment.

```python
from kibank.m81_kilocode_bridge import detect_environment

env = detect_environment()
# Returns:
# {
#     "is_docker": True,
#     "is_kubernetes": False,
#     "is_colab": False,
#     "is_wsl": False,
#     "is_venv": True,
#     "has_npm": True,
#     "has_node": True,
#     "has_npx": True,
#     "has_go": True,
#     "has_ollama": True,
#     "has_docker": True
# }
```

---

## Configuration

### KiloCodeConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `npm_package` | str | `@kilocode/cli` | NPM package name |
| `install_globally` | bool | `True` | Install globally vs locally |
| `auto_install` | bool | `True` | Auto-install if missing |
| `autonomous_mode` | bool | `False` | Enable CI/CD mode |
| `auto_approve` | bool | `False` | Auto-approve all actions (dangerous) |
| `enable_safety_net` | bool | `True` | Enable safety checks |
| `fallback_on_error` | bool | `True` | Fallback to KiloCode on errors |
| `max_retries` | int | `3` | Maximum retry attempts |
| `max_queue_size` | int | `1000` | Maximum message queue size |
| `heartbeat_interval` | float | `30.0` | Seconds between heartbeats |
| `connection_timeout` | float | `10.0` | Connection timeout seconds |

### Example Configurations

#### Development Environment
```python
config = KiloCodeConfig(
    autonomous_mode=False,
    enable_safety_net=True,
    auto_approve=False,
    max_queue_size=500
)
```

#### CI/CD Pipeline
```python
config = KiloCodeConfig(
    autonomous_mode=True,
    auto_approve=True,  # Only in trusted environments!
    enable_safety_net=True,
    max_retries=5
)
```

#### Colab/Cloud Environment
```python
config = KiloCodeConfig(
    autonomous_mode=True,
    auto_approve=False,
    working_directory="/content",
    heartbeat_interval=15.0
)
```

---

## Integration with KISWARM

### Integration in install.sh

The bridge is automatically installed during KISWARM setup in **Phase 12**:

```bash
# ── PHASE 12: KILOCODE PARALLEL SAFETY NET ───────────────────────────────
step "Phase 12: KiloCode Parallel Safety Net"

# Install Node.js if needed
if ! command -v node &>/dev/null; then
    log "Installing Node.js for KiloCode..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo -E apt-get install -y nodejs
fi

# Install KiloCode CLI
if ! command -v kilo &>/dev/null; then
    log "Installing KiloCode CLI..."
    npm install -g @kilocode/cli
fi
```

### Integration in Dockerfile

```dockerfile
# Install KiloCode CLI as parallel safety net
RUN npm install -g @kilocode/cli && \
    echo "KiloCode CLI installed for KISWARM safety net"
ENV KILOCODE_AUTO_MODE=true
```

### Integration with Other KISWARM Modules

```python
# In M75 Installer Pretraining
from kibank.m81_kilocode_bridge import initialize_kilocode_bridge

def setup_kiswarm():
    # Initialize KiloCode bridge
    bridge = initialize_kilocode_bridge(auto_start=True)
    
    # Use for code review
    async def review_installation_script(script):
        return await bridge.code_review(script)
    
    return bridge

# In M63 AEGIS Counterstrike
async def analyze_potential_threat(code):
    bridge = get_kilocode_bridge()
    
    # Security scan via KiloCode
    scan_result = await bridge.security_scan(code)
    
    if scan_result.get("risk_level") in ["HIGH", "CRITICAL"]:
        trigger_defensive_response(scan_result)
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest backend/tests/test_m81_kilocode_bridge.py -v

# Run specific test class
pytest backend/tests/test_m81_kilocode_bridge.py::TestKiloCodeBridge -v

# Run with coverage
pytest backend/tests/test_m81_kilocode_bridge.py --cov=kibank.m81_kilocode_bridge
```

### Quick Validation

```python
from kibank.m81_kilocode_bridge import test_kilocode_bridge

results = test_kilocode_bridge()
print(f"Overall: {'PASSED' if results['overall_success'] else 'FAILED'}")
```

### Expected Output

```
============================================================
M81 KiloCode Bridge Module Test
============================================================
Environment detected:
  - is_docker: True
  - is_kubernetes: False
  - is_colab: False
  - is_wsl: False
  - is_venv: True
  - has_npm: True
  - has_node: True
  - has_npx: True
  - has_go: True
  - has_ollama: True
  - has_docker: True

✓ environment_detection
✓ bridge_init
✓ installation_check
✓ message_creation
✓ status_report

Overall: PASSED
============================================================
```

---

## Troubleshooting

### KiloCode CLI Not Found

```bash
# Install manually
npm install -g @kilocode/cli

# Verify installation
kilo --version
```

### Permission Denied

```bash
# Install with sudo
sudo npm install -g @kilocode/cli

# Or use npx (no global install needed)
npx @kilocode/cli --version
```

### Connection Timeout

```python
# Increase timeout in config
config = KiloCodeConfig(
    connection_timeout=30.0,
    max_retries=5
)
```

### Queue Full

```python
# Increase queue size
config = KiloCodeConfig(
    max_queue_size=5000
)

# Or clear queue
bridge.queue.clear()
```

---

## Security Considerations

### Autonomous Mode Warning

⚠️ **WARNING**: `autonomous_mode=True` with `auto_approve=True` disables all permission prompts. Only use in trusted environments like CI/CD pipelines.

### Data Sanitization

The bridge automatically sanitizes sensitive data in error reports:
- API keys are masked
- File paths are anonymized
- User credentials are removed

### Recommended Security Settings

```python
# Secure configuration
config = KiloCodeConfig(
    autonomous_mode=False,      # Require human interaction
    auto_approve=False,         # Never auto-approve
    enable_safety_net=True,     # Enable safety checks
    fallback_on_error=True      # Fallback on errors
)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 6.4.0 | 2025-03-13 | Initial release |
| 6.4.1 | TBD | Planned: WebSocket support |

---

## See Also

- [M76: Identity Invariant Kernel](./M76_IDENTITY_INVARIANT.md)
- [M77: Value Drift Sentinel](./M77_VALUE_DRIFT_SENTINEL.md)
- [M78: Velocity Governor](./M78_VELOCITY_GOVERNOR.md)
- [M79: Semantic Consolidation Engine](./M79_SEMANTIC_CONSOLIDATION.md)
- [M80: Post-Quantum Ledger](./M80_POST_QUANTUM_LEDGER.md)
- [CHANGELOG.md](../CHANGELOG.md)

---

**Author**: KISWARM Team  
**License**: Proprietary - KIWZB Central Bank System  
**Last Updated**: 2025-03-13
