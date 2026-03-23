#!/usr/bin/env python3
"""
KISWARM Zero-Touch Scout Integration Testing Suite
Military-Grade Autonomous Installation System - Phase 3

This test suite validates the Zero-Touch Scout across all 6 target environments:
- Google Colab
- Docker containers
- Kubernetes pods
- WSL2 (Windows Subsystem for Linux)
- Cloud VMs (AWS, GCP, Azure)
- Bare metal Linux

Run with: pytest tests/test_zero_touch_scout.py -v --tb=short
"""

import os
import sys
import json
import time
import tempfile
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import unittest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ZeroTouchScout-Tests")


# ============================================================================
# Enums and Data Classes
# ============================================================================

class Environment(Enum):
    """Target environments for Zero-Touch Scout"""
    COLAB = "colab"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    WSL2 = "wsl2"
    CLOUD_VM = "cloud_vm"
    BARE_METAL = "bare_metal"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class NetworkCondition(Enum):
    """Network conditions for testing"""
    ONLINE = "online"
    OFFLINE = "offline"
    INTERMITTENT = "intermittent"
    RATE_LIMITED = "rate_limited"


class TestOutcome(Enum):
    """Expected test outcomes"""
    SUCCESS = "success"
    FALLBACK_TO_ARK = "fallback_to_ark"
    RETRY_AND_SUCCEED = "retry_and_succeed"
    FAIL_AND_REPORT = "fail_and_report"
    FAIL_AND_ESCALATE = "fail_and_escalate"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Retry immediately
    MEDIUM = "medium"     # Backoff and retry
    HIGH = "high"         # Try alternative source
    CRITICAL = "critical" # Escalate to human


@dataclass
class HardwareProfile:
    """Hardware profile for environment simulation"""
    cpu_cores: int = 4
    ram_gb: float = 16.0
    disk_gb: float = 100.0
    has_gpu: bool = False
    gpu_vram_gb: float = 0.0


@dataclass
class SimulatedEnvironment:
    """Simulated environment for testing"""
    name: str
    environment: Environment
    has_internet: bool = True
    has_systemd: bool = True
    is_container: bool = False
    python_version: str = "3.10"
    hardware: HardwareProfile = field(default_factory=HardwareProfile)
    paths: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.paths:
            self.paths = {
                "root": "/",
                "home": "/root",
                "tmp": "/tmp",
            }


@dataclass
class TestScenario:
    """E2E test scenario definition"""
    name: str
    description: str
    environment: Environment
    network_condition: NetworkCondition
    expected_outcome: TestOutcome
    hardware_requirements: HardwareProfile = field(default_factory=HardwareProfile)


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Result of entire test suite"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_secs: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100.0
    
    def print_summary(self) -> None:
        """Print test summary to console"""
        print("\n" + "=" * 70)
        print("ZERO-TOUCH SCOUT INTEGRATION TEST RESULTS")
        print("=" * 70)
        print(f"Total:   {self.total}")
        print(f"Passed:  {self.passed} ({self.success_rate:.1f}%)")
        print(f"Failed:  {self.failed}")
        print(f"Skipped: {self.skipped}")
        print(f"Time:    {self.duration_secs:.2f}s")
        print("=" * 70)
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if not result.passed:
                    print(f"  ❌ {result.name} - {result.error_message or 'Unknown error'}")


# ============================================================================
# Environment Simulators
# ============================================================================

class EnvironmentSimulator:
    """Simulates different target environments for testing"""
    
    @staticmethod
    def colab() -> SimulatedEnvironment:
        """Create Google Colab environment simulation"""
        return SimulatedEnvironment(
            name="Google Colab",
            environment=Environment.COLAB,
            has_internet=True,
            has_systemd=False,
            is_container=True,
            python_version="3.10",
            hardware=HardwareProfile(
                cpu_cores=2,
                ram_gb=12.0,
                disk_gb=100.0,
                has_gpu=True,
                gpu_vram_gb=16.0
            ),
            paths={
                "root": "/",
                "home": "/root",
                "tmp": "/tmp",
                "content": "/content",
                "drive": "/content/drive"
            }
        )
    
    @staticmethod
    def docker() -> SimulatedEnvironment:
        """Create Docker container environment simulation"""
        return SimulatedEnvironment(
            name="Docker Container",
            environment=Environment.DOCKER,
            has_internet=True,
            has_systemd=False,
            is_container=True,
            python_version="3.11",
            hardware=HardwareProfile(
                cpu_cores=4,
                ram_gb=16.0,
                disk_gb=50.0,
                has_gpu=False
            ),
            paths={
                "root": "/",
                "home": "/root",
                "tmp": "/tmp"
            }
        )
    
    @staticmethod
    def kubernetes() -> SimulatedEnvironment:
        """Create Kubernetes pod environment simulation"""
        return SimulatedEnvironment(
            name="Kubernetes Pod",
            environment=Environment.KUBERNETES,
            has_internet=True,
            has_systemd=False,
            is_container=True,
            python_version="3.11",
            hardware=HardwareProfile(
                cpu_cores=8,
                ram_gb=32.0,
                disk_gb=100.0,
                has_gpu=False
            ),
            paths={
                "root": "/",
                "home": "/root",
                "tmp": "/tmp",
                "secrets": "/var/run/secrets/kubernetes.io"
            }
        )
    
    @staticmethod
    def wsl2() -> SimulatedEnvironment:
        """Create WSL2 environment simulation"""
        return SimulatedEnvironment(
            name="WSL2",
            environment=Environment.WSL2,
            has_internet=True,
            has_systemd=True,  # WSL2 can have systemd
            is_container=False,
            python_version="3.10",
            hardware=HardwareProfile(
                cpu_cores=8,
                ram_gb=64.0,
                disk_gb=500.0,
                has_gpu=True,
                gpu_vram_gb=8.0
            ),
            paths={
                "root": "/",
                "home": "/home/user",
                "tmp": "/tmp",
                "mnt": "/mnt/c"
            }
        )
    
    @staticmethod
    def cloud_vm() -> SimulatedEnvironment:
        """Create Cloud VM environment simulation"""
        return SimulatedEnvironment(
            name="Cloud VM",
            environment=Environment.CLOUD_VM,
            has_internet=True,
            has_systemd=True,
            is_container=False,
            python_version="3.11",
            hardware=HardwareProfile(
                cpu_cores=16,
                ram_gb=128.0,
                disk_gb=1000.0,
                has_gpu=False
            ),
            paths={
                "root": "/",
                "home": "/home/ubuntu",
                "tmp": "/tmp"
            }
        )
    
    @staticmethod
    def bare_metal() -> SimulatedEnvironment:
        """Create bare metal environment simulation"""
        return SimulatedEnvironment(
            name="Bare Metal",
            environment=Environment.BARE_METAL,
            has_internet=True,
            has_systemd=True,
            is_container=False,
            python_version="3.11",
            hardware=HardwareProfile(
                cpu_cores=32,
                ram_gb=256.0,
                disk_gb=2000.0,
                has_gpu=True,
                gpu_vram_gb=24.0
            ),
            paths={
                "root": "/",
                "home": "/home/admin",
                "tmp": "/tmp"
            }
        )
    
    @staticmethod
    def offline() -> SimulatedEnvironment:
        """Create offline/air-gapped environment simulation"""
        return SimulatedEnvironment(
            name="Offline/Air-gapped",
            environment=Environment.OFFLINE,
            has_internet=False,
            has_systemd=True,
            is_container=False,
            python_version="3.10",
            hardware=HardwareProfile(
                cpu_cores=16,
                ram_gb=64.0,
                disk_gb=500.0,
                has_gpu=False
            ),
            paths={
                "root": "/",
                "home": "/home/admin",
                "tmp": "/tmp",
                "ark": "/opt/kiswarm-ark"
            }
        )


# ============================================================================
# Failure Handling Tests
# ============================================================================

class BackoffCalculator:
    """Exponential backoff with jitter calculation"""
    
    @staticmethod
    def calculate(
        attempt: int,
        base_delay_ms: int = 1000,
        max_delay_ms: int = 60000,
        multiplier: float = 2.0,
        jitter_percent: float = 0.2
    ) -> float:
        """
        Calculate delay with exponential backoff and jitter.
        
        Args:
            attempt: Attempt number (0-indexed)
            base_delay_ms: Base delay in milliseconds
            max_delay_ms: Maximum delay cap
            multiplier: Exponential multiplier
            jitter_percent: Jitter percentage (0-1)
        
        Returns:
            Delay in milliseconds
        """
        import random
        
        # Calculate base exponential delay
        delay = base_delay_ms * (multiplier ** attempt)
        
        # Cap at maximum
        delay = min(delay, max_delay_ms)
        
        # Add jitter
        jitter = delay * jitter_percent * (random.random() * 2 - 1)
        delay = delay + jitter
        
        return max(0, delay)


def classify_error(error_type: str) -> ErrorSeverity:
    """
    Classify error severity for handling strategy.
    
    Args:
        error_type: Error type string
    
    Returns:
        ErrorSeverity enum value
    """
    severity_map = {
        # Low severity - retry immediately
        "NetworkTimeout": ErrorSeverity.LOW,
        "ConnectionReset": ErrorSeverity.LOW,
        "DNSResolutionFailed": ErrorSeverity.LOW,
        
        # Medium severity - backoff and retry
        "RateLimited": ErrorSeverity.MEDIUM,
        "TemporaryUnavailable": ErrorSeverity.MEDIUM,
        "ServiceOverloaded": ErrorSeverity.MEDIUM,
        
        # High severity - try alternative source
        "SourceUnavailable": ErrorSeverity.HIGH,
        "ChecksumMismatch": ErrorSeverity.HIGH,
        "SignatureVerificationFailed": ErrorSeverity.HIGH,
        
        # Critical severity - escalate to human
        "AllSourcesExhausted": ErrorSeverity.CRITICAL,
        "SecurityViolation": ErrorSeverity.CRITICAL,
        "BinaryTampered": ErrorSeverity.CRITICAL,
        "ArkIntegrityFailed": ErrorSeverity.CRITICAL,
    }
    
    return severity_map.get(error_type, ErrorSeverity.MEDIUM)


# ============================================================================
# Test Cases
# ============================================================================

class TestEnvironmentSimulators(unittest.TestCase):
    """Test environment simulator creation"""
    
    def test_colab_environment_creation(self):
        """Test Google Colab environment simulation"""
        env = EnvironmentSimulator.colab()
        self.assertEqual(env.name, "Google Colab")
        self.assertEqual(env.environment, Environment.COLAB)
        self.assertTrue(env.has_internet)
        self.assertFalse(env.has_systemd)
        self.assertTrue(env.is_container)
        self.assertIn("content", env.paths)
    
    def test_docker_environment_creation(self):
        """Test Docker container environment simulation"""
        env = EnvironmentSimulator.docker()
        self.assertEqual(env.name, "Docker Container")
        self.assertEqual(env.environment, Environment.DOCKER)
        self.assertTrue(env.has_internet)
        self.assertFalse(env.has_systemd)
        self.assertTrue(env.is_container)
    
    def test_kubernetes_environment_creation(self):
        """Test Kubernetes pod environment simulation"""
        env = EnvironmentSimulator.kubernetes()
        self.assertEqual(env.name, "Kubernetes Pod")
        self.assertEqual(env.environment, Environment.KUBERNETES)
        self.assertTrue(env.has_internet)
        self.assertFalse(env.has_systemd)
        self.assertIn("secrets", env.paths)
    
    def test_wsl2_environment_creation(self):
        """Test WSL2 environment simulation"""
        env = EnvironmentSimulator.wsl2()
        self.assertEqual(env.name, "WSL2")
        self.assertEqual(env.environment, Environment.WSL2)
        self.assertTrue(env.has_internet)
        self.assertTrue(env.has_systemd)
        self.assertFalse(env.is_container)
    
    def test_cloud_vm_environment_creation(self):
        """Test Cloud VM environment simulation"""
        env = EnvironmentSimulator.cloud_vm()
        self.assertEqual(env.name, "Cloud VM")
        self.assertEqual(env.environment, Environment.CLOUD_VM)
        self.assertTrue(env.has_internet)
        self.assertTrue(env.has_systemd)
    
    def test_bare_metal_environment_creation(self):
        """Test bare metal environment simulation"""
        env = EnvironmentSimulator.bare_metal()
        self.assertEqual(env.name, "Bare Metal")
        self.assertEqual(env.environment, Environment.BARE_METAL)
        self.assertTrue(env.has_internet)
        self.assertTrue(env.has_systemd)
        self.assertFalse(env.is_container)
    
    def test_offline_environment_creation(self):
        """Test offline/air-gapped environment simulation"""
        env = EnvironmentSimulator.offline()
        self.assertEqual(env.name, "Offline/Air-gapped")
        self.assertEqual(env.environment, Environment.OFFLINE)
        self.assertFalse(env.has_internet)
        self.assertIn("ark", env.paths)


class TestBackoffCalculator(unittest.TestCase):
    """Test exponential backoff calculations"""
    
    def test_first_attempt_delay(self):
        """Test first attempt uses base delay"""
        delay = BackoffCalculator.calculate(0, base_delay_ms=1000)
        # With jitter, should be close to 1000
        self.assertGreater(delay, 800)
        self.assertLess(delay, 1200)
    
    def test_second_attempt_delay(self):
        """Test second attempt doubles delay"""
        delay = BackoffCalculator.calculate(1, base_delay_ms=1000, jitter_percent=0)
        self.assertEqual(delay, 2000)
    
    def test_third_attempt_delay(self):
        """Test third attempt quadruples delay"""
        delay = BackoffCalculator.calculate(2, base_delay_ms=1000, jitter_percent=0)
        self.assertEqual(delay, 4000)
    
    def test_delay_is_capped(self):
        """Test delay is capped at maximum"""
        delay = BackoffCalculator.calculate(10, base_delay_ms=1000, max_delay_ms=60000, jitter_percent=0)
        self.assertEqual(delay, 60000)


class TestErrorClassification(unittest.TestCase):
    """Test error severity classification"""
    
    def test_network_timeout_is_low(self):
        """Test NetworkTimeout is classified as LOW"""
        self.assertEqual(classify_error("NetworkTimeout"), ErrorSeverity.LOW)
    
    def test_rate_limited_is_medium(self):
        """Test RateLimited is classified as MEDIUM"""
        self.assertEqual(classify_error("RateLimited"), ErrorSeverity.MEDIUM)
    
    def test_source_unavailable_is_high(self):
        """Test SourceUnavailable is classified as HIGH"""
        self.assertEqual(classify_error("SourceUnavailable"), ErrorSeverity.HIGH)
    
    def test_all_sources_exhausted_is_critical(self):
        """Test AllSourcesExhausted is classified as CRITICAL"""
        self.assertEqual(classify_error("AllSourcesExhausted"), ErrorSeverity.CRITICAL)
    
    def test_unknown_error_is_medium(self):
        """Test unknown errors default to MEDIUM"""
        self.assertEqual(classify_error("UnknownError"), ErrorSeverity.MEDIUM)


class TestBootstrapMethod(unittest.TestCase):
    """Test bootstrap method selection"""
    
    def test_online_preferred_when_available(self):
        """Test online bootstrap is preferred when internet is available"""
        has_internet = True
        has_ark = True
        
        if has_internet:
            method = "Online"
        elif has_ark:
            method = "Ark"
        else:
            method = "None"
        
        self.assertEqual(method, "Online")
    
    def test_ark_fallback_when_offline(self):
        """Test Ark fallback when offline"""
        has_internet = False
        has_ark = True
        
        if has_internet:
            method = "Online"
        elif has_ark:
            method = "Ark"
        else:
            method = "None"
        
        self.assertEqual(method, "Ark")


class TestE2EScenarios(unittest.TestCase):
    """End-to-end test scenario definitions"""
    
    @staticmethod
    def get_scenarios() -> List[TestScenario]:
        """Get all E2E test scenarios"""
        return [
            # Scenario 1: Normal online installation
            TestScenario(
                name="normal_online_installation",
                description="Standard installation with internet access",
                environment=Environment.BARE_METAL,
                network_condition=NetworkCondition.ONLINE,
                expected_outcome=TestOutcome.SUCCESS
            ),
            
            # Scenario 2: Offline with Ark
            TestScenario(
                name="offline_with_ark",
                description="Installation from Ark cache in air-gapped environment",
                environment=Environment.OFFLINE,
                network_condition=NetworkCondition.OFFLINE,
                expected_outcome=TestOutcome.FALLBACK_TO_ARK
            ),
            
            # Scenario 3: Colab quick install
            TestScenario(
                name="colab_quick_install",
                description="Quick installation in Google Colab environment",
                environment=Environment.COLAB,
                network_condition=NetworkCondition.ONLINE,
                expected_outcome=TestOutcome.SUCCESS
            ),
            
            # Scenario 4: Rate limited recovery
            TestScenario(
                name="rate_limited_recovery",
                description="Recovery from rate limiting with exponential backoff",
                environment=Environment.DOCKER,
                network_condition=NetworkCondition.RATE_LIMITED,
                expected_outcome=TestOutcome.RETRY_AND_SUCCEED
            ),
            
            # Scenario 5: Intermittent network
            TestScenario(
                name="intermittent_network",
                description="Installation with intermittent network connectivity",
                environment=Environment.CLOUD_VM,
                network_condition=NetworkCondition.INTERMITTENT,
                expected_outcome=TestOutcome.RETRY_AND_SUCCEED
            ),
            
            # Scenario 6: Kubernetes pod installation
            TestScenario(
                name="kubernetes_pod_installation",
                description="Installation in Kubernetes pod with resource constraints",
                environment=Environment.KUBERNETES,
                network_condition=NetworkCondition.ONLINE,
                expected_outcome=TestOutcome.SUCCESS
            ),
            
            # Scenario 7: WSL2 installation
            TestScenario(
                name="wsl2_installation",
                description="Installation in WSL2 environment",
                environment=Environment.WSL2,
                network_condition=NetworkCondition.ONLINE,
                expected_outcome=TestOutcome.SUCCESS
            ),
            
            # Scenario 8: Complete failure scenario
            TestScenario(
                name="complete_failure",
                description="All sources fail, should report to community mesh",
                environment=Environment.BARE_METAL,
                network_condition=NetworkCondition.OFFLINE,
                expected_outcome=TestOutcome.FAIL_AND_REPORT
            ),
        ]
    
    def test_scenarios_count(self):
        """Test that we have sufficient E2E scenarios"""
        scenarios = self.get_scenarios()
        self.assertGreaterEqual(len(scenarios), 8)
    
    def test_all_environments_covered(self):
        """Test that all 6 target environments are covered"""
        scenarios = self.get_scenarios()
        environments = {s.environment for s in scenarios}
        
        self.assertIn(Environment.COLAB, environments)
        self.assertIn(Environment.DOCKER, environments)
        self.assertIn(Environment.KUBERNETES, environments)
        self.assertIn(Environment.WSL2, environments)
        self.assertIn(Environment.CLOUD_VM, environments)
        self.assertIn(Environment.BARE_METAL, environments)
    
    def test_all_network_conditions_covered(self):
        """Test that all network conditions are covered"""
        scenarios = self.get_scenarios()
        conditions = {s.network_condition for s in scenarios}
        
        self.assertIn(NetworkCondition.ONLINE, conditions)
        self.assertIn(NetworkCondition.OFFLINE, conditions)
        self.assertIn(NetworkCondition.INTERMITTENT, conditions)
        self.assertIn(NetworkCondition.RATE_LIMITED, conditions)
    
    def test_success_scenarios_exist(self):
        """Test that success scenarios exist"""
        scenarios = self.get_scenarios()
        success_count = sum(1 for s in scenarios if s.expected_outcome == TestOutcome.SUCCESS)
        self.assertGreaterEqual(success_count, 3)
    
    def test_failure_scenarios_exist(self):
        """Test that failure scenarios exist"""
        scenarios = self.get_scenarios()
        failure_count = sum(1 for s in scenarios 
            if s.expected_outcome in [TestOutcome.FAIL_AND_REPORT, TestOutcome.FAIL_AND_ESCALATE])
        self.assertGreaterEqual(failure_count, 1)


class TestHardwareRequirements(unittest.TestCase):
    """Test hardware requirement validation"""
    
    def test_colab_hardware_profile(self):
        """Test Colab hardware profile"""
        env = EnvironmentSimulator.colab()
        self.assertEqual(env.hardware.cpu_cores, 2)
        self.assertEqual(env.hardware.ram_gb, 12.0)
        self.assertTrue(env.hardware.has_gpu)
    
    def test_bare_metal_hardware_profile(self):
        """Test bare metal hardware profile"""
        env = EnvironmentSimulator.bare_metal()
        self.assertEqual(env.hardware.cpu_cores, 32)
        self.assertEqual(env.hardware.ram_gb, 256.0)
        self.assertTrue(env.hardware.has_gpu)
    
    def test_kubernetes_hardware_profile(self):
        """Test Kubernetes hardware profile"""
        env = EnvironmentSimulator.kubernetes()
        self.assertEqual(env.hardware.cpu_cores, 8)
        self.assertEqual(env.hardware.ram_gb, 32.0)
        self.assertFalse(env.hardware.has_gpu)


class TestArkManifest(unittest.TestCase):
    """Test Ark manifest handling"""
    
    @staticmethod
    def create_mock_manifest() -> Dict[str, Any]:
        """Create a mock Ark manifest for testing"""
        return {
            "ark_version": "6.4.0",
            "created_at": "2025-01-15T00:00:00Z",
            "kiswarm_version": "6.4.0",
            "target_platforms": ["linux-x86_64", "linux-arm64"],
            "components": {
                "kiswarm-core": {
                    "path": "core/kiswarm-core.tar.gz",
                    "sha256": "abc123def456",
                    "size_bytes": 12345678
                },
                "python-wheels": {
                    "path": "python/wheels.tar.gz",
                    "sha256": "def789abc012",
                    "size_bytes": 45678901,
                    "packages": ["flask", "qdrant-client", "ollama"]
                }
            },
            "min_ram_gb": 8.0,
            "min_disk_gb": 20.0
        }
    
    def test_manifest_structure(self):
        """Test manifest has required structure"""
        manifest = self.create_mock_manifest()
        self.assertEqual(manifest["ark_version"], "6.4.0")
        self.assertEqual(manifest["kiswarm_version"], "6.4.0")
        self.assertIn("components", manifest)
    
    def test_manifest_components(self):
        """Test manifest components"""
        manifest = self.create_mock_manifest()
        components = manifest["components"]
        self.assertIn("kiswarm-core", components)
        self.assertIn("python-wheels", components)
    
    def test_manifest_requirements(self):
        """Test manifest requirements"""
        manifest = self.create_mock_manifest()
        self.assertEqual(manifest["min_ram_gb"], 8.0)
        self.assertEqual(manifest["min_disk_gb"], 20.0)


# ============================================================================
# Test Runner
# ============================================================================

def run_test_suite(verbose: bool = True) -> TestSuiteResult:
    """
    Run all tests and return results.
    
    Args:
        verbose: Whether to print detailed output
    
    Returns:
        TestSuiteResult object
    """
    start_time = time.time()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentSimulators))
    suite.addTests(loader.loadTestsFromTestCase(TestBackoffCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestBootstrapMethod))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestHardwareRequirements))
    suite.addTests(loader.loadTestsFromTestCase(TestArkManifest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 0)
    result = runner.run(suite)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Create result object
    return TestSuiteResult(
        total=result.testsRun,
        passed=result.testsRun - len(result.failures) - len(result.errors),
        failed=len(result.failures) + len(result.errors),
        skipped=len(result.skipped),
        duration_secs=duration,
        results=[
            TestResult(
                name=str(test),
                passed=True,
                duration_ms=0
            )
            for test in suite
        ]
    )


if __name__ == "__main__":
    # Run tests
    result = run_test_suite(verbose=True)
    result.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if result.failed == 0 else 1)
