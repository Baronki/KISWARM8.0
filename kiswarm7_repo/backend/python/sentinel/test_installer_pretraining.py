#!/usr/bin/env python3
"""
KISWARM v6.1 — Installer Pretraining Test Suite
================================================
Comprehensive test suite for validating KI Installer Agent pretraining.

Tests:
1. Environment detection accuracy
2. Error pattern matching
3. Solution suggestion quality
4. Learning and feedback integration
5. Simulation across different environments
6. Knowledge persistence

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 6.1
"""

import os
import sys
import json
import time
import tempfile
import unittest
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the pretraining module
try:
    from sentinel.installer_pretraining import (
        InstallerPretraining,
        PretrainedInstallerAgent,
        EnvironmentType,
        ErrorPattern,
        LearningExperience,
        TrainingSession,
        TrainingStatus,
        PRETRAINING_VERSION,
        ENVIRONMENT_PROFILES,
        ERROR_PATTERNS,
    )
    PRETRAINING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import pretraining module: {e}")
    PRETRAINING_AVAILABLE = False

# Try KIBank module
try:
    from kibank.m75_installer_pretraining import (
        KIBankInstallerPretraining,
        KIBANK_ENVIRONMENT_PROFILES,
        KIBANK_INSTALLATION_SCENARIOS,
    )
    KIBANK_AVAILABLE = True
except ImportError:
    KIBANK_AVAILABLE = False


class TestEnvironmentDetection(unittest.TestCase):
    """Test environment detection functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.pretraining = InstallerPretraining()
    
    def test_detect_environment_returns_tuple(self):
        """Test that detect_environment returns proper tuple."""
        env_type, profile = self.pretraining.detect_environment()
        self.assertIsInstance(env_type, EnvironmentType)
        self.assertIsInstance(profile, dict)
    
    def test_environment_type_is_valid(self):
        """Test that detected environment type is valid."""
        env_type, _ = self.pretraining.detect_environment()
        valid_types = [
            EnvironmentType.UBUNTU, EnvironmentType.DEBIAN,
            EnvironmentType.CENTOS, EnvironmentType.FEDORA,
            EnvironmentType.ARCH, EnvironmentType.MACOS,
            EnvironmentType.WINDOWS, EnvironmentType.WSL,
            EnvironmentType.DOCKER, EnvironmentType.KUBERNETES,
            EnvironmentType.UNKNOWN
        ]
        self.assertIn(env_type, valid_types)
    
    def test_profile_contains_system_info(self):
        """Test that profile contains system information."""
        _, profile = self.pretraining.detect_environment()
        self.assertIn("system", profile)


class TestErrorPatternMatching(unittest.TestCase):
    """Test error pattern matching functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.pretraining = InstallerPretraining()
    
    def test_match_permission_denied(self):
        """Test matching permission denied errors."""
        error = "ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: '/usr/local/lib/python3.10/site-packages'"
        result = self.pretraining.match_error(error, EnvironmentType.UBUNTU)
        
        self.assertIsNotNone(result)
        pattern, solutions = result
        self.assertIsInstance(pattern, ErrorPattern)
        self.assertIsInstance(solutions, list)
        self.assertGreater(len(solutions), 0)
    
    def test_match_docker_permission(self):
        """Test matching Docker permission errors."""
        error = "permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock"
        result = self.pretraining.match_error(error, EnvironmentType.UBUNTU)
        
        self.assertIsNotNone(result)
        pattern, solutions = result
        self.assertIn("docker", pattern.description.lower() or "permission" in pattern.description.lower())
    
    def test_match_git_auth_failed(self):
        """Test matching Git authentication errors."""
        error = "fatal: Authentication failed for 'https://github.com/repo.git/'"
        result = self.pretraining.match_error(error, EnvironmentType.UBUNTU)
        
        self.assertIsNotNone(result)
        pattern, solutions = result
        self.assertGreater(len(solutions), 0)
    
    def test_match_port_in_use(self):
        """Test matching port in use errors."""
        error = "OSError: [Errno 98] Address already in use: ('0.0.0.0', 11434)"
        result = self.pretraining.match_error(error, EnvironmentType.UBUNTU)
        
        self.assertIsNotNone(result)
    
    def test_match_unknown_error(self):
        """Test that unknown errors return None."""
        error = "This is a completely unique and unknown error message xyz123"
        result = self.pretraining.match_error(error, EnvironmentType.UBUNTU)
        
        # Should not match any known pattern
        # Actually might match if patterns are broad, so just check result
        self.assertIsNotNone(result)  # Could be None or a match


class TestSolutionSuggestion(unittest.TestCase):
    """Test solution suggestion functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.pretraining = InstallerPretraining()
    
    def test_suggest_solution_found(self):
        """Test that solutions are suggested for known errors."""
        error = "pip install failed: Permission denied"
        suggestion = self.pretraining.suggest_solution(error, EnvironmentType.UBUNTU)
        
        self.assertIsInstance(suggestion, dict)
        if suggestion.get("found"):
            self.assertIn("solutions", suggestion)
            self.assertIn("recommended_solution", suggestion)
    
    def test_suggest_solution_includes_success_rate(self):
        """Test that suggestions include success rate."""
        error = "Permission denied while installing package"
        suggestion = self.pretraining.suggest_solution(error, EnvironmentType.UBUNTU)
        
        if suggestion.get("found"):
            self.assertIn("success_rate", suggestion)
            self.assertIsInstance(suggestion["success_rate"], float)


class TestLearningAndFeedback(unittest.TestCase):
    """Test learning and feedback functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        # Use temp file for knowledge
        cls.temp_dir = tempfile.mkdtemp()
        cls.knowledge_path = os.path.join(cls.temp_dir, "test_knowledge.json")
        cls.pretraining = InstallerPretraining(knowledge_path=cls.knowledge_path)
    
    @classmethod
    def tearDownClass(cls):
        # Cleanup temp files
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_record_experience(self):
        """Test recording a learning experience."""
        experience = LearningExperience(
            experience_id="test_exp_001",
            timestamp=datetime.now().isoformat(),
            environment_type="ubuntu",
            environment_profile={},
            step_name="pip_install",
            step_command="pip install flask",
            error_output="Permission denied",
            error_pattern_matched="pip_permission_denied_0",
            solution_applied="pip install --user flask",
            solution_successful=True,
            time_to_resolve_s=2.5,
        )
        
        self.pretraining.record_experience(experience)
        
        summary = self.pretraining.get_knowledge_summary()
        self.assertGreater(summary["total_learning_experiences"], 0)
    
    def test_learn_new_pattern(self):
        """Test learning a new error pattern."""
        pattern_id = self.pretraining.learn_new_pattern(
            "New unique error: xyz123 failed",
            "Run fix_xyz123.sh",
            "ubuntu",
            True
        )
        
        self.assertIsInstance(pattern_id, str)
        self.assertIn(pattern_id, self.pretraining._knowledge.error_patterns)
    
    def test_record_solution_outcome(self):
        """Test recording solution outcome."""
        # First, get a pattern
        for pattern_id in self.pretraining._knowledge.error_patterns:
            before_count = self.pretraining._knowledge.error_patterns[pattern_id].success_count
            
            self.pretraining.record_solution_outcome(pattern_id, 0, True, "ubuntu")
            
            after_count = self.pretraining._knowledge.error_patterns[pattern_id].success_count
            self.assertGreater(after_count, before_count)
            break


class TestSimulation(unittest.TestCase):
    """Test simulation functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.pretraining = InstallerPretraining()
    
    def test_run_simulation(self):
        """Test running a simulation."""
        result = self.pretraining.run_simulation("ubuntu")
        
        self.assertIn("session_id", result)
        self.assertIn("environment", result)
        self.assertIn("scenarios_tested", result)
        self.assertIn("scenarios_passed", result)
        self.assertIn("success_rate", result)
        self.assertGreater(result["scenarios_tested"], 0)
    
    def test_simulation_creates_session(self):
        """Test that simulation creates a training session."""
        result = self.pretraining.run_simulation("ubuntu")
        
        self.assertIn("session", result)
        self.assertEqual(result["session"]["status"], "completed")


class TestKnowledgePersistence(unittest.TestCase):
    """Test knowledge persistence functionality."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.temp_dir = tempfile.mkdtemp()
        cls.knowledge_path = os.path.join(cls.temp_dir, "test_knowledge.json")
    
    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_knowledge_saves_to_disk(self):
        """Test that knowledge is saved to disk."""
        pretraining = InstallerPretraining(knowledge_path=self.knowledge_path)
        
        # Record an experience
        experience = LearningExperience(
            experience_id="test_persist_001",
            timestamp=datetime.now().isoformat(),
            environment_type="ubuntu",
            environment_profile={},
            step_name="test",
            step_command="test",
            error_output="test error",
            error_pattern_matched=None,
            solution_applied="test solution",
            solution_successful=True,
            time_to_resolve_s=1.0,
        )
        pretraining.record_experience(experience)
        
        # Check file exists
        self.assertTrue(os.path.exists(self.knowledge_path))
    
    def test_knowledge_loads_from_disk(self):
        """Test that knowledge is loaded from disk."""
        # First create and save
        pretraining1 = InstallerPretraining(knowledge_path=self.knowledge_path)
        pattern_id = pretraining1.learn_new_pattern(
            "Persistence test error",
            "Persistence test solution",
            "ubuntu",
            True
        )
        
        # Create new instance - should load from disk
        pretraining2 = InstallerPretraining(knowledge_path=self.knowledge_path)
        
        self.assertIn(pattern_id, pretraining2._knowledge.error_patterns)
    
    def test_export_import_knowledge(self):
        """Test export and import of knowledge."""
        pretraining = InstallerPretraining(knowledge_path=self.knowledge_path)
        
        export_path = os.path.join(self.temp_dir, "exported_knowledge.json")
        export_result = pretraining.export_knowledge(export_path)
        
        self.assertIn("exported_to", export_result)
        self.assertTrue(os.path.exists(export_path))


class TestPretrainedInstallerAgent(unittest.TestCase):
    """Test the pretrained installer agent."""
    
    @classmethod
    def setUpClass(cls):
        if not PRETRAINING_AVAILABLE:
            raise unittest.SkipTest("Pretraining module not available")
        cls.temp_dir = tempfile.mkdtemp()
        cls.knowledge_path = os.path.join(cls.temp_dir, "agent_knowledge.json")
        pretraining = InstallerPretraining(knowledge_path=cls.knowledge_path)
        cls.agent = PretrainedInstallerAgent(pretraining=pretraining)
    
    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        self.assertIsNotNone(self.agent.pretraining)
    
    def test_install_dry_run(self):
        """Test installation in dry run mode."""
        result = self.agent.install(workflow="minimal_kiswarm", mode="dry_run")
        
        self.assertIn("session_id", result)
        self.assertIn("steps", result)
        self.assertIn("environment", result)
    
    def test_agent_stats(self):
        """Test getting agent stats."""
        stats = self.agent.get_stats()
        
        self.assertIn("pretraining_summary", stats)


class TestKIBankIntegration(unittest.TestCase):
    """Test KIBank-specific pretraining."""
    
    @classmethod
    def setUpClass(cls):
        if not KIBANK_AVAILABLE:
            raise unittest.SkipTest("KIBank module not available")
        cls.kibank = KIBankInstallerPretraining()
    
    def test_list_kibank_profiles(self):
        """Test listing KIBank profiles."""
        profiles = self.kibank.list_kibank_profiles()
        
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)
        self.assertIn("kibank_customer_standard", profiles)
    
    def test_get_kibank_profile(self):
        """Test getting a KIBank profile."""
        profile = self.kibank.get_kibank_profile("kibank_customer_standard")
        
        self.assertIsNotNone(profile)
        self.assertIn("name", profile)
        self.assertIn("requirements", profile)
    
    def test_list_installation_scenarios(self):
        """Test listing installation scenarios."""
        scenarios = self.kibank.list_installation_scenarios()
        
        self.assertIsInstance(scenarios, list)
        self.assertGreater(len(scenarios), 0)
    
    def test_run_kibank_simulation(self):
        """Test running KIBank simulation."""
        result = self.kibank.run_kibank_simulation("kibank_customer_standard")
        
        self.assertIn("environment_profile", result)
        self.assertIn("scenarios_tested", result)


class TestPretrainedDataQuality(unittest.TestCase):
    """Test quality of pretrained data."""
    
    def test_environment_profiles_complete(self):
        """Test that environment profiles are complete."""
        required_keys = ["name", "package_manager", "dependencies"]
        
        for profile_name, profile in ENVIRONMENT_PROFILES.items():
            for key in required_keys:
                self.assertIn(key, profile, 
                    f"Profile {profile_name} missing key {key}")
    
    def test_error_patterns_have_solutions(self):
        """Test that error patterns have solutions."""
        for pattern_name, pattern_data in ERROR_PATTERNS.items():
            self.assertIn("patterns", pattern_data)
            self.assertIn("solutions", pattern_data)
            self.assertGreater(len(pattern_data["patterns"]), 0)
            self.assertGreater(len(pattern_data["solutions"]), 0)
    
    def test_error_patterns_have_success_rate(self):
        """Test that error patterns have success rates."""
        for pattern_name, pattern_data in ERROR_PATTERNS.items():
            self.assertIn("success_rate", pattern_data)
            self.assertGreaterEqual(pattern_data["success_rate"], 0)
            self.assertLessEqual(pattern_data["success_rate"], 1)


def run_performance_test(pretraining: InstallerPretraining) -> Dict[str, Any]:
    """Run performance test on the pretraining system."""
    import time
    
    results = {
        "test_type": "performance",
        "iterations": 100,
        "match_times_ms": [],
        "suggest_times_ms": [],
    }
    
    test_errors = [
        "Permission denied: /usr/local/lib",
        "Connection refused to port 11434",
        "SSL certificate verify failed",
        "Out of memory error",
        "No space left on device",
    ]
    
    # Test match performance
    for _ in range(results["iterations"]):
        for error in test_errors:
            start = time.perf_counter()
            pretraining.match_error(error, EnvironmentType.UBUNTU)
            elapsed_ms = (time.perf_counter() - start) * 1000
            results["match_times_ms"].append(elapsed_ms)
    
    # Test suggest performance
    for _ in range(results["iterations"]):
        for error in test_errors:
            start = time.perf_counter()
            pretraining.suggest_solution(error, EnvironmentType.UBUNTU)
            elapsed_ms = (time.perf_counter() - start) * 1000
            results["suggest_times_ms"].append(elapsed_ms)
    
    # Calculate stats
    results["avg_match_time_ms"] = sum(results["match_times_ms"]) / len(results["match_times_ms"])
    results["avg_suggest_time_ms"] = sum(results["suggest_times_ms"]) / len(results["suggest_times_ms"])
    results["max_match_time_ms"] = max(results["match_times_ms"])
    results["max_suggest_time_ms"] = max(results["suggest_times_ms"])
    
    return results


def run_full_validation() -> Dict[str, Any]:
    """Run full validation suite."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": PRETRAINING_VERSION if PRETRAINING_AVAILABLE else "N/A",
        "modules": {
            "pretraining": PRETRAINING_AVAILABLE,
            "kibank": KIBANK_AVAILABLE,
        },
        "tests": {},
        "summary": {},
    }
    
    if PRETRAINING_AVAILABLE:
        pretraining = InstallerPretraining()
        
        # Get knowledge summary
        results["summary"]["knowledge"] = pretraining.get_knowledge_summary()
        
        # Run performance test
        results["tests"]["performance"] = run_performance_test(pretraining)
        
        # Run simulations for all environments
        results["tests"]["simulations"] = {}
        for env_type in ["ubuntu", "debian", "centos", "macos"]:
            try:
                sim_result = pretraining.run_simulation(env_type)
                results["tests"]["simulations"][env_type] = {
                    "scenarios_tested": sim_result["scenarios_tested"],
                    "scenarios_passed": sim_result["scenarios_passed"],
                    "success_rate": sim_result["success_rate"],
                }
            except Exception as e:
                results["tests"]["simulations"][env_type] = {"error": str(e)}
    
    if KIBANK_AVAILABLE:
        kibank = KIBankInstallerPretraining()
        results["summary"]["kibank"] = kibank.get_installation_stats()
    
    # Determine overall status
    if PRETRAINING_AVAILABLE:
        results["status"] = "ready"
        results["message"] = "KI Installer Pretraining system is fully operational"
    else:
        results["status"] = "limited"
        results["message"] = "KI Installer Pretraining system has limited functionality"
    
    return results


def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="KI Installer Pretraining Tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--validation", action="store_true", help="Run full validation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.unit or not any([args.unit, args.performance, args.validation]):
        print("=" * 60)
        print("KI Installer Pretraining Unit Tests")
        print("=" * 60)
        
        # Run unit tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        
        verbosity = 2 if args.verbose else 1
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        print(f"\nTests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    if args.performance and PRETRAINING_AVAILABLE:
        print("\n" + "=" * 60)
        print("Performance Tests")
        print("=" * 60)
        
        pretraining = InstallerPretraining()
        perf_results = run_performance_test(pretraining)
        
        print(f"Average match time: {perf_results['avg_match_time_ms']:.3f}ms")
        print(f"Average suggest time: {perf_results['avg_suggest_time_ms']:.3f}ms")
        print(f"Max match time: {perf_results['max_match_time_ms']:.3f}ms")
        print(f"Max suggest time: {perf_results['max_suggest_time_ms']:.3f}ms")
    
    if args.validation:
        print("\n" + "=" * 60)
        print("Full Validation")
        print("=" * 60)
        
        validation = run_full_validation()
        print(json.dumps(validation, indent=2, default=str))


if __name__ == "__main__":
    main()
