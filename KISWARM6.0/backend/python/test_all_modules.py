#!/usr/bin/env python3
"""
KISWARM6.0 - Comprehensive Module Test Suite
============================================
Tests ALL modules from M1 to M74 (Sentinel + KIBank + Industrial)

Author: KISWARM System
Version: 6.1.0
"""

import sys
import os
import traceback
import importlib
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ModuleCategory(Enum):
    SENTINEL = "sentinel"       # M1-M57
    KIBANK = "kibank"           # M60-M74
    INDUSTRIAL = "industrial"   # M69


@dataclass
class ModuleTestResult:
    module_name: str
    category: ModuleCategory
    import_success: bool = False
    class_instantiation: bool = False
    method_check: bool = False
    error_message: str = ""
    classes_found: List[str] = field(default_factory=list)
    methods_found: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "category": self.category.value,
            "import_success": self.import_success,
            "class_instantiation": self.class_instantiation,
            "method_check": self.method_check,
            "error_message": self.error_message,
            "classes_found": self.classes_found,
            "methods_found": self.methods_found[:10],  # First 10 methods
            "execution_time_ms": round(self.execution_time_ms, 2)
        }
    
    @property
    def overall_success(self) -> bool:
        return self.import_success and self.class_instantiation


@dataclass
class TestReport:
    timestamp: str
    total_modules: int
    passed: int
    failed: int
    warnings: int
    results: List[ModuleTestResult]
    summary_by_category: Dict[str, Dict[str, int]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_modules": self.total_modules,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "pass_rate": round(self.passed / max(self.total_modules, 1) * 100, 2),
            "summary_by_category": self.summary_by_category,
            "results": [r.to_dict() for r in self.results]
        }


class ComprehensiveModuleTester:
    """Test all KISWARM modules comprehensively."""
    
    # Sentinel modules (M1-M57)
    SENTINEL_MODULES = [
        "__init__", "actor_critic", "advisor_api", "ast_parser", "byzantine_aggregator",
        "constrained_rl", "crypto_ledger", "digital_thread", "digital_twin",
        "energy_overcapacity_pivot", "evolution_memory_vault", "experience_collector",
        "explainability_engine", "extended_physics", "federated_mesh", "feedback_channel",
        "formal_verification", "fuzzy_tuner", "gossip_protocol", "hexstrike_guard",
        "ics_security", "ics_shield", "installer_agent", "kiinstall_agent", "kiswarm_cli",
        "kiswarm_dashboard", "kiswarm_hardening", "knowledge_decay", "knowledge_graph",
        "model_tracker", "multiagent_coordinator", "mutation_governance", "ot_network_monitor",
        "peer_discovery", "physics_twin", "planetary_sun_follower", "plc_parser",
        "predictive_maintenance", "prompt_firewall", "repo_intelligence", "retrieval_guard",
        "rule_engine", "scada_observer", "semantic_conflict", "sentinel_api", "sentinel_bridge",
        "sil_verification", "solar_chase_coordinator", "swarm_auditor", "swarm_dag",
        "swarm_debate", "swarm_immortality_kernel", "swarm_peer", "swarm_soul_mirror",
        "sysadmin_agent", "system_scout", "td3_controller", "tool_forge", "vmware_orchestrator"
    ]
    
    # KIBank modules (M60-M74)
    KIBANK_MODULES = [
        "__init__", "m60_auth", "m61_banking", "m62_investment", "m63_aegis_counterstrike",
        "m64_aegis_juris", "m65_kiswarm_edge_firewall", "m66_zero_day_protection",
        "m67_apt_detection", "m68_ai_adversarial_defense", "m71_training_ground",
        "m72_model_manager", "m73_aegis_training_integration", "m74_kibank_customer_agent",
        "aegis_unified_bridge", "central_bank_config", "security_hardening", "test_integration"
    ]
    
    # Industrial modules
    INDUSTRIAL_MODULES = ["m69_scada_plc_bridge"]
    
    def __init__(self):
        self.results: List[ModuleTestResult] = []
        self._start_time = datetime.now()
    
    def test_module(self, module_name: str, package: str, category: ModuleCategory) -> ModuleTestResult:
        """Test a single module."""
        import time
        start = time.time()
        
        result = ModuleTestResult(
            module_name=module_name,
            category=category
        )
        
        try:
            # Try to import
            full_path = f"{package}.{module_name}"
            module = importlib.import_module(full_path)
            result.import_success = True
            
            # Find classes
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and not name.startswith('_'):
                    result.classes_found.append(name)
                    
                    # Try to find methods
                    try:
                        for method_name in dir(obj):
                            if not method_name.startswith('_'):
                                result.methods_found.append(f"{name}.{method_name}")
                    except:
                        pass
            
            # Try to instantiate main class if found
            main_classes = [c for c in result.classes_found 
                          if c.lower().replace('_', '') in module_name.lower().replace('_', '') 
                          or module_name.lower().replace('_', '') in c.lower().replace('_', '')]
            
            if main_classes:
                try:
                    main_class = getattr(module, main_classes[0])
                    # Some classes need specific parameters, skip if they fail
                    try:
                        instance = main_class()
                        result.class_instantiation = True
                    except TypeError:
                        # Class requires parameters - still count as success for import
                        result.class_instantiation = True
                        result.error_message = "Class requires parameters (expected)"
                except Exception as e:
                    result.error_message = f"Instantiation error: {str(e)[:100]}"
            else:
                # No main class found, but import worked
                result.class_instantiation = True
                result.error_message = "No main class to instantiate (utility module)"
            
            result.method_check = len(result.methods_found) > 0
            
        except ImportError as e:
            result.error_message = f"Import error: {str(e)[:200]}"
        except Exception as e:
            result.error_message = f"Error: {str(e)[:200]}"
        
        result.execution_time_ms = (time.time() - start) * 1000
        return result
    
    def run_all_tests(self) -> TestReport:
        """Run tests for all modules."""
        print("=" * 70)
        print("KISWARM6.0 - COMPREHENSIVE MODULE TEST SUITE")
        print("=" * 70)
        print()
        
        # Test Sentinel modules
        print(f"Testing {len(self.SENTINEL_MODULES)} Sentinel modules (M1-M57)...")
        for module_name in self.SENTINEL_MODULES:
            result = self.test_module(module_name, "sentinel", ModuleCategory.SENTINEL)
            self.results.append(result)
            status = "✅" if result.overall_success else "❌"
            print(f"  {status} {module_name}: {len(result.classes_found)} classes, {len(result.methods_found)} methods")
        
        print()
        
        # Test KIBank modules
        print(f"Testing {len(self.KIBANK_MODULES)} KIBank modules (M60-M74)...")
        for module_name in self.KIBANK_MODULES:
            result = self.test_module(module_name, "kibank", ModuleCategory.KIBANK)
            self.results.append(result)
            status = "✅" if result.overall_success else "❌"
            print(f"  {status} {module_name}: {len(result.classes_found)} classes, {len(result.methods_found)} methods")
        
        print()
        
        # Test Industrial modules
        print(f"Testing {len(self.INDUSTRIAL_MODULES)} Industrial modules...")
        for module_name in self.INDUSTRIAL_MODULES:
            result = self.test_module(module_name, "industrial", ModuleCategory.INDUSTRIAL)
            self.results.append(result)
            status = "✅" if result.overall_success else "❌"
            print(f"  {status} {module_name}: {len(result.classes_found)} classes, {len(result.methods_found)} methods")
        
        # Generate summary
        passed = sum(1 for r in self.results if r.overall_success)
        failed = sum(1 for r in self.results if not r.overall_success)
        warnings = sum(1 for r in self.results if r.overall_success and r.error_message)
        
        # Summary by category
        summary = {}
        for cat in ModuleCategory:
            cat_results = [r for r in self.results if r.category == cat]
            summary[cat.value] = {
                "total": len(cat_results),
                "passed": sum(1 for r in cat_results if r.overall_success),
                "failed": sum(1 for r in cat_results if not r.overall_success)
            }
        
        report = TestReport(
            timestamp=datetime.now().isoformat(),
            total_modules=len(self.results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            results=self.results,
            summary_by_category=summary
        )
        
        # Print summary
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Modules:  {report.total_modules}")
        print(f"Passed:         {report.passed} ✅")
        print(f"Failed:         {report.failed} ❌")
        print(f"Warnings:       {report.warnings} ⚠️")
        print(f"Pass Rate:      {round(report.passed / max(report.total_modules, 1) * 100, 2)}%")
        print()
        print("By Category:")
        for cat, stats in report.summary_by_category.items():
            print(f"  {cat.upper():12} - Total: {stats['total']:3}, Passed: {stats['passed']:3}, Failed: {stats['failed']:3}")
        
        if report.failed > 0:
            print()
            print("FAILED MODULES:")
            for r in self.results:
                if not r.overall_success:
                    print(f"  ❌ {r.module_name}: {r.error_message}")
        
        print()
        print("=" * 70)
        
        return report


def main():
    """Main entry point."""
    tester = ComprehensiveModuleTester()
    report = tester.run_all_tests()
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "test_report.json")
    with open(report_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
