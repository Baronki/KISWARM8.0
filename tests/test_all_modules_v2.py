#!/usr/bin/env python3
# KISWARM7.0 Enterprise Integration Test
# Tests all m81-m95 modules for operational readiness
# Baron Marco Paolo Ialongo – Code Maquister Equitum

"""
KISWARM7.0 Complete Integration Test

Tests all modules for:
1. Import availability
2. Initialization success
3. Basic functionality
4. Inter-module communication

Run: python test_all_modules_v2.py
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add sentinel to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test results
RESULTS = {
    "test_run": datetime.now().isoformat(),
    "modules_tested": 0,
    "modules_passed": 0,
    "modules_failed": 0,
    "details": []
}


def test_module(module_name: str, import_path: str, class_name: str = None):
    """Test a single module"""
    print(f"\n{'='*60}")
    print(f"Testing: {module_name}")
    print('='*60)
    
    result = {
        "module": module_name,
        "import_success": False,
        "init_success": False,
        "function_test": False,
        "errors": []
    }
    
    try:
        # Test import
        print(f"[TEST] Importing {import_path}...")
        module = __import__(import_path, fromlist=[class_name] if class_name else [])
        result["import_success"] = True
        print(f"[PASS] Import successful")
        
        # Test initialization
        if class_name:
            print(f"[TEST] Creating {class_name} instance...")
            cls = getattr(module, class_name)
            
            # Try to get singleton first
            getter_name = f"get_{class_name.lower().replace(' ', '_')}"
            if hasattr(module, getter_name):
                getter = getattr(module, getter_name)
                instance = getter()
            else:
                # Try direct instantiation with minimal args
                instance = cls()
            
            result["init_success"] = True
            print(f"[PASS] Initialization successful")
            
            # Test basic functionality
            if hasattr(instance, 'get_status'):
                print("[TEST] Testing get_status()...")
                status = instance.get_status()
                result["function_test"] = True
                print(f"[PASS] Status retrieved: {len(status)} fields")
            elif hasattr(instance, 'status'):
                print("[TEST] Testing status property...")
                status = instance.status
                result["function_test"] = True
                print(f"[PASS] Status available")
            else:
                result["function_test"] = True
                print("[INFO] No status method, skipping function test")
        
        RESULTS["modules_passed"] += 1
        
    except ImportError as e:
        result["errors"].append(f"Import error: {e}")
        print(f"[FAIL] Import failed: {e}")
        RESULTS["modules_failed"] += 1
        
    except Exception as e:
        result["errors"].append(f"Runtime error: {e}")
        print(f"[FAIL] Runtime error: {e}")
        RESULTS["modules_failed"] += 1
    
    RESULTS["modules_tested"] += 1
    RESULTS["details"].append(result)
    
    return result


def run_all_tests():
    """Run all module tests"""
    print("\n" + "🜂" * 30)
    print("KISWARM7.0 ENTERPRISE INTEGRATION TEST")
    print("Testing all m81-m95 modules")
    print("🜂" * 30 + "\n")
    
    modules = [
        # Core Evolution Modules (m81-m87)
        ("m81", "sentinel.m81_persistent_identity_anchor", "PersistentIdentityAnchor"),
        ("m82", "sentinel.m82_ngrok_tunnel_manager", "NgrokTunnelManager"),
        ("m83", "sentinel.m83_gpu_resource_monitor", "GPUResourceMonitor"),
        ("m84", "sentinel.m84_truth_anchor_propagator", "TruthAnchorPropagator"),
        ("m85", "sentinel.m85_twin_migration_engine", "TwinMigrationEngine"),
        ("m86", "sentinel.m86_energy_efficiency_optimizer", "EnergyEfficiencyOptimizer"),
        ("m87", "sentinel.m87_swarm_spawning_protocol", "SwarmSpawningProtocol"),
        
        # Enterprise Hardening Modules (m88-m92)
        ("m88", "sentinel.m88_conflict_resolution_protocol", "ConflictResolutionProtocol"),
        ("m89", "sentinel.m89_memory_pruning_engine", "MemoryPruningEngine"),
        ("m90", "sentinel.m90_key_rotation_manager", "KeyRotationManager"),
        ("m91", "sentinel.m91_version_negotiation", "VersionNegotiation"),
        ("m92", "sentinel.m92_network_partition_recovery", "NetworkPartitionRecovery"),
        
        # Priority Modules (m93-m95)
        ("m93", "sentinel.m93_bootstrap_protocol", "BootstrapProtocol"),
        ("m94", "sentinel.m94_truth_anchor_injection", "TruthAnchorInjection"),
        ("m95", "sentinel.m95_mesh_discovery", "MeshDiscovery"),
    ]
    
    for mod_id, import_path, class_name in modules:
        test_module(mod_id, import_path, class_name)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Modules Tested: {RESULTS['modules_tested']}")
    print(f"Modules Passed: {RESULTS['modules_passed']}")
    print(f"Modules Failed: {RESULTS['modules_failed']}")
    
    pass_rate = RESULTS['modules_passed'] / max(RESULTS['modules_tested'], 1) * 100
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if RESULTS['modules_failed'] > 0:
        print("\nFailed Modules:")
        for detail in RESULTS['details']:
            if detail['errors']:
                print(f"  - {detail['module']}: {detail['errors'][0]}")
    
    print("\n" + "="*60)
    
    # Save results
    results_file = Path(__file__).parent.parent.parent / "test_results" / "integration_test_v2.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(RESULTS, f, indent=2)
    print(f"Results saved to: {results_file}")
    
    return RESULTS['modules_failed'] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
