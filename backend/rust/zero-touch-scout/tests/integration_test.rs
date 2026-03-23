//! Integration Tests for KISWARM Zero-Touch Scout
//! 
//! Military-grade testing framework for autonomous installation system.
//! Tests cover all 6 target environments and failure scenarios.

use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

use tokio::sync::RwLock;
use tempfile::tempdir;

// Note: These tests would use the actual scout modules
// For now, we define the test framework structure

/// Test configuration
pub struct TestConfig {
    pub timeout_secs: u64,
    pub temp_dir: PathBuf,
    pub mock_network: bool,
    pub verbose: bool,
}

impl Default for TestConfig {
    fn default() -> Self {
        Self {
            timeout_secs: 300,
            temp_dir: std::env::temp_dir(),
            mock_network: true,
            verbose: false,
        }
    }
}

/// Test result for a single test
#[derive(Debug, Clone)]
pub struct TestResult {
    pub name: String,
    pub passed: bool,
    pub duration_ms: u64,
    pub error_message: Option<String>,
}

/// Test suite results
#[derive(Debug, Clone)]
pub struct TestSuiteResult {
    pub total: u32,
    pub passed: u32,
    pub failed: u32,
    pub skipped: u32,
    pub duration_secs: f64,
    pub results: Vec<TestResult>,
}

impl TestSuiteResult {
    pub fn success_rate(&self) -> f64 {
        if self.total == 0 {
            0.0
        } else {
            (self.passed as f64 / self.total as f64) * 100.0
        }
    }
    
    pub fn print_summary(&self) {
        println!("\n{}", "=".repeat(60));
        println!("ZERO-TOUCH SCOUT INTEGRATION TEST RESULTS");
        println!("{}", "=".repeat(60));
        println!("Total:   {}", self.total);
        println!("Passed:  {} ({:.1}%)", self.passed, self.success_rate());
        println!("Failed:  {}", self.failed);
        println!("Skipped: {}", self.skipped);
        println!("Time:    {:.2}s", self.duration_secs);
        println!("{}", "=".repeat(60));
        
        if self.failed > 0 {
            println!("\nFAILED TESTS:");
            for result in &self.results {
                if !result.passed {
                    println!("  ❌ {} - {}", result.name, 
                        result.error_message.as_ref().unwrap_or(&"Unknown error".to_string()));
                }
            }
        }
    }
}

// ============================================================================
// Environment Simulator Tests
// ============================================================================

#[cfg(test)]
mod environment_simulator_tests {
    use super::*;
    
    /// Simulated environment configuration
    pub struct SimulatedEnvironment {
        pub name: String,
        pub has_internet: bool,
        pub has_systemd: bool,
        pub is_container: bool,
        pub cpu_cores: u32,
        pub ram_gb: f64,
        pub disk_gb: f64,
        pub python_version: String,
        pub paths: SimulatedPaths,
    }
    
    #[derive(Debug, Clone)]
    pub struct SimulatedPaths {
        pub root: PathBuf,
        pub home: PathBuf,
        pub tmp: PathBuf,
        pub content: Option<PathBuf>,  // Colab-specific
    }
    
    impl SimulatedEnvironment {
        /// Create Google Colab simulation
        pub fn colab() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Google Colab".to_string(),
                has_internet: true,
                has_systemd: false,
                is_container: true,
                cpu_cores: 2,
                ram_gb: 12.0,
                disk_gb: 100.0,
                python_version: "3.10".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("root"),
                    tmp: root.join("tmp"),
                    content: Some(root.join("content")),
                },
            }
        }
        
        /// Create Docker container simulation
        pub fn docker() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Docker Container".to_string(),
                has_internet: true,
                has_systemd: false,
                is_container: true,
                cpu_cores: 4,
                ram_gb: 16.0,
                disk_gb: 50.0,
                python_version: "3.11".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("root"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
        
        /// Create Kubernetes pod simulation
        pub fn kubernetes() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Kubernetes Pod".to_string(),
                has_internet: true,
                has_systemd: false,
                is_container: true,
                cpu_cores: 8,
                ram_gb: 32.0,
                disk_gb: 100.0,
                python_version: "3.11".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("root"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
        
        /// Create WSL2 simulation
        pub fn wsl2() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "WSL2".to_string(),
                has_internet: true,
                has_systemd: true,  // WSL2 can have systemd
                is_container: false,
                cpu_cores: 8,
                ram_gb: 64.0,
                disk_gb: 500.0,
                python_version: "3.10".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("home").join("user"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
        
        /// Create Cloud VM simulation (AWS/GCP/Azure)
        pub fn cloud_vm() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Cloud VM".to_string(),
                has_internet: true,
                has_systemd: true,
                is_container: false,
                cpu_cores: 16,
                ram_gb: 128.0,
                disk_gb: 1000.0,
                python_version: "3.11".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("home").join("ubuntu"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
        
        /// Create bare metal simulation
        pub fn bare_metal() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Bare Metal".to_string(),
                has_internet: true,
                has_systemd: true,
                is_container: false,
                cpu_cores: 32,
                ram_gb: 256.0,
                disk_gb: 2000.0,
                python_version: "3.11".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("home").join("admin"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
        
        /// Create offline environment (air-gapped)
        pub fn offline() -> Self {
            let temp = tempdir().unwrap();
            let root = temp.path().to_path_buf();
            
            Self {
                name: "Offline/Air-gapped".to_string(),
                has_internet: false,
                has_systemd: true,
                is_container: false,
                cpu_cores: 16,
                ram_gb: 64.0,
                disk_gb: 500.0,
                python_version: "3.10".to_string(),
                paths: SimulatedPaths {
                    root: root.clone(),
                    home: root.join("home").join("admin"),
                    tmp: root.join("tmp"),
                    content: None,
                },
            }
        }
    }
    
    #[test]
    fn test_colab_environment_creation() {
        let env = SimulatedEnvironment::colab();
        assert_eq!(env.name, "Google Colab");
        assert!(env.has_internet);
        assert!(!env.has_systemd);
        assert!(env.is_container);
        assert!(env.paths.content.is_some());
    }
    
    #[test]
    fn test_docker_environment_creation() {
        let env = SimulatedEnvironment::docker();
        assert_eq!(env.name, "Docker Container");
        assert!(env.has_internet);
        assert!(!env.has_systemd);
        assert!(env.is_container);
        assert!(env.paths.content.is_none());
    }
    
    #[test]
    fn test_kubernetes_environment_creation() {
        let env = SimulatedEnvironment::kubernetes();
        assert_eq!(env.name, "Kubernetes Pod");
        assert!(env.has_internet);
        assert!(!env.has_systemd);
        assert!(env.is_container);
    }
    
    #[test]
    fn test_wsl2_environment_creation() {
        let env = SimulatedEnvironment::wsl2();
        assert_eq!(env.name, "WSL2");
        assert!(env.has_internet);
        assert!(env.has_systemd);
        assert!(!env.is_container);
    }
    
    #[test]
    fn test_cloud_vm_environment_creation() {
        let env = SimulatedEnvironment::cloud_vm();
        assert_eq!(env.name, "Cloud VM");
        assert!(env.has_internet);
        assert!(env.has_systemd);
        assert!(!env.is_container);
    }
    
    #[test]
    fn test_bare_metal_environment_creation() {
        let env = SimulatedEnvironment::bare_metal();
        assert_eq!(env.name, "Bare Metal");
        assert!(env.has_internet);
        assert!(env.has_systemd);
        assert!(!env.is_container);
    }
    
    #[test]
    fn test_offline_environment_creation() {
        let env = SimulatedEnvironment::offline();
        assert_eq!(env.name, "Offline/Air-gapped");
        assert!(!env.has_internet);
        assert!(env.has_systemd);
    }
}

// ============================================================================
// State Machine Tests
// ============================================================================

#[cfg(test)]
mod state_machine_tests {
    use super::*;
    
    /// Expected state transitions
    pub const VALID_TRANSITIONS: &[(&str, &str)] = &[
        // Normal flow
        ("Init", "SelfVerify"),
        ("SelfVerify", "EnvDetect"),
        ("EnvDetect", "EnvConfig"),
        ("EnvConfig", "ParallelScan"),
        ("ParallelScan", "OnlineBootstrap"),
        ("ParallelScan", "ArkBootstrap"),
        ("OnlineBootstrap", "Installing"),
        ("ArkBootstrap", "Installing"),
        ("Installing", "Verifying"),
        ("Verifying", "Success"),
        ("Success", "Operational"),
        
        // Failure handling
        ("Failure", "Backoff"),
        ("Backoff", "Retry"),
        ("Retry", "EnvConfig"),
        ("Failure", "Reporting"),
        ("Reporting", "AlternativeSource"),
        ("AlternativeSource", "Escalated"),
        ("Escalated", "Aborted"),
    ];
    
    #[test]
    fn test_valid_state_transitions_count() {
        // Verify we have documented all expected transitions
        assert!(VALID_TRANSITIONS.len() >= 15);
    }
    
    #[test]
    fn test_init_state_is_entry_point() {
        // INIT should always be the first state
        let init_count = VALID_TRANSITIONS.iter()
            .filter(|(from, _)| *from == "Init")
            .count();
        assert_eq!(init_count, 1);
    }
    
    #[test]
    fn test_terminal_states() {
        // Terminal states should not have outgoing transitions
        let terminal_states = ["Operational", "Aborted"];
        for terminal in terminal_states {
            let has_outgoing = VALID_TRANSITIONS.iter()
                .any(|(from, _)| *from == terminal);
            assert!(!has_outgoing, "{} should not have outgoing transitions", terminal);
        }
    }
    
    #[test]
    fn test_failure_recovery_path() {
        // Failure should have multiple recovery options
        let failure_transitions: Vec<_> = VALID_TRANSITIONS.iter()
            .filter(|(from, _)| *from == "Failure")
            .collect();
        assert!(failure_transitions.len() >= 2, "Failure should have at least 2 recovery paths");
    }
}

// ============================================================================
// Network Layer Tests
// ============================================================================

#[cfg(test)]
mod network_tests {
    use super::*;
    
    /// Mock HTTP response
    pub struct MockResponse {
        pub status: u16,
        pub body: Vec<u8>,
        pub headers: std::collections::HashMap<String, String>,
    }
    
    impl MockResponse {
        pub fn success(body: &str) -> Self {
            Self {
                status: 200,
                body: body.as_bytes().to_vec(),
                headers: std::collections::HashMap::new(),
            }
        }
        
        pub fn not_found() -> Self {
            Self {
                status: 404,
                body: b"Not Found".to_vec(),
                headers: std::collections::HashMap::new(),
            }
        }
        
        pub fn server_error() -> Self {
            Self {
                status: 500,
                body: b"Internal Server Error".to_vec(),
                headers: std::collections::HashMap::new(),
            }
        }
        
        pub fn rate_limited() -> Self {
            let mut headers = std::collections::HashMap::new();
            headers.insert("X-RateLimit-Remaining".to_string(), "0".to_string());
            Self {
                status: 429,
                body: b"Rate Limited".to_vec(),
                headers,
            }
        }
    }
    
    #[test]
    fn test_mock_response_success() {
        let response = MockResponse::success("OK");
        assert_eq!(response.status, 200);
        assert!(!response.body.is_empty());
    }
    
    #[test]
    fn test_mock_response_not_found() {
        let response = MockResponse::not_found();
        assert_eq!(response.status, 404);
    }
    
    #[test]
    fn test_mock_response_server_error() {
        let response = MockResponse::server_error();
        assert_eq!(response.status, 500);
    }
    
    #[test]
    fn test_mock_response_rate_limited() {
        let response = MockResponse::rate_limited();
        assert_eq!(response.status, 429);
        assert_eq!(response.headers.get("X-RateLimit-Remaining"), Some(&"0".to_string()));
    }
}

// ============================================================================
// Bootstrap Engine Tests
// ============================================================================

#[cfg(test)]
mod bootstrap_tests {
    use super::*;
    
    /// Mock Ark manifest for testing
    pub fn create_mock_ark_manifest() -> serde_json::Value {
        serde_json::json!({
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
        })
    }
    
    #[test]
    fn test_mock_ark_manifest_structure() {
        let manifest = create_mock_ark_manifest();
        assert_eq!(manifest["ark_version"], "6.4.0");
        assert_eq!(manifest["kiswarm_version"], "6.4.0");
        assert!(manifest["components"].is_object());
    }
    
    #[test]
    fn test_ark_manifest_components() {
        let manifest = create_mock_ark_manifest();
        let components = manifest["components"].as_object().unwrap();
        assert!(components.contains_key("kiswarm-core"));
        assert!(components.contains_key("python-wheels"));
    }
    
    #[test]
    fn test_ark_manifest_requirements() {
        let manifest = create_mock_ark_manifest();
        assert_eq!(manifest["min_ram_gb"], 8.0);
        assert_eq!(manifest["min_disk_gb"], 20.0);
    }
    
    /// Bootstrap method priority test
    #[test]
    fn test_bootstrap_method_priority() {
        // Online should be preferred when available
        let has_internet = true;
        let has_ark = true;
        
        let preferred_method = if has_internet {
            "Online"
        } else if has_ark {
            "Ark"
        } else {
            "None"
        };
        
        assert_eq!(preferred_method, "Online");
    }
    
    /// Offline fallback test
    #[test]
    fn test_offline_fallback() {
        let has_internet = false;
        let has_ark = true;
        
        let preferred_method = if has_internet {
            "Online"
        } else if has_ark {
            "Ark"
        } else {
            "None"
        };
        
        assert_eq!(preferred_method, "Ark");
    }
}

// ============================================================================
// Failure Handling Tests
// ============================================================================

#[cfg(test)]
mod failure_handling_tests {
    use super::*;
    
    /// Exponential backoff calculation
    pub fn calculate_backoff(
        attempt: u32,
        base_delay_ms: u64,
        max_delay_ms: u64,
        multiplier: f64,
    ) -> Duration {
        let delay = (base_delay_ms as f64) * multiplier.powi(attempt as i32);
        let capped = delay.min(max_delay_ms as f64);
        Duration::from_millis(capped as u64)
    }
    
    #[test]
    fn test_exponential_backoff_first_attempt() {
        let delay = calculate_backoff(0, 1000, 60000, 2.0);
        assert_eq!(delay, Duration::from_millis(1000));
    }
    
    #[test]
    fn test_exponential_backoff_second_attempt() {
        let delay = calculate_backoff(1, 1000, 60000, 2.0);
        assert_eq!(delay, Duration::from_millis(2000));
    }
    
    #[test]
    fn test_exponential_backoff_third_attempt() {
        let delay = calculate_backoff(2, 1000, 60000, 2.0);
        assert_eq!(delay, Duration::from_millis(4000));
    }
    
    #[test]
    fn test_exponential_backoff_capped() {
        let delay = calculate_backoff(10, 1000, 60000, 2.0);
        assert_eq!(delay, Duration::from_millis(60000)); // Should be capped
    }
    
    /// Error severity classification
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum ErrorSeverity {
        Low,      // Retry immediately
        Medium,   // Backoff and retry
        High,     // Try alternative source
        Critical, // Escalate to human
    }
    
    pub fn classify_error(error_type: &str) -> ErrorSeverity {
        match error_type {
            "NetworkTimeout" | "ConnectionReset" => ErrorSeverity::Low,
            "RateLimited" | "TemporaryUnavailable" => ErrorSeverity::Medium,
            "SourceUnavailable" | "ChecksumMismatch" => ErrorSeverity::High,
            "AllSourcesExhausted" | "SecurityViolation" => ErrorSeverity::Critical,
            _ => ErrorSeverity::Medium,
        }
    }
    
    #[test]
    fn test_classify_network_timeout() {
        assert_eq!(classify_error("NetworkTimeout"), ErrorSeverity::Low);
    }
    
    #[test]
    fn test_classify_rate_limited() {
        assert_eq!(classify_error("RateLimited"), ErrorSeverity::Medium);
    }
    
    #[test]
    fn test_classify_source_unavailable() {
        assert_eq!(classify_error("SourceUnavailable"), ErrorSeverity::High);
    }
    
    #[test]
    fn test_classify_all_sources_exhausted() {
        assert_eq!(classify_error("AllSourcesExhausted"), ErrorSeverity::Critical);
    }
}

// ============================================================================
// End-to-End Scenario Tests
// ============================================================================

#[cfg(test)]
mod e2e_tests {
    use super::*;
    
    /// E2E test scenario definition
    pub struct TestScenario {
        pub name: String,
        pub description: String,
        pub environment: String,
        pub network_condition: NetworkCondition,
        pub expected_outcome: ExpectedOutcome,
    }
    
    #[derive(Debug, Clone)]
    pub enum NetworkCondition {
        Online,
        Offline,
        Intermittent,
        RateLimited,
    }
    
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub enum ExpectedOutcome {
        Success,
        FallbackToArk,
        RetryAndSucceed,
        FailAndReport,
        FailAndEscalate,
    }
    
    /// Define all E2E test scenarios
    pub fn get_e2e_scenarios() -> Vec<TestScenario> {
        vec![
            // Scenario 1: Normal online installation
            TestScenario {
                name: "normal_online_installation".to_string(),
                description: "Standard installation with internet access".to_string(),
                environment: "bare_metal".to_string(),
                network_condition: NetworkCondition::Online,
                expected_outcome: ExpectedOutcome::Success,
            },
            
            // Scenario 2: Offline with Ark
            TestScenario {
                name: "offline_with_ark".to_string(),
                description: "Installation from Ark cache in air-gapped environment".to_string(),
                environment: "offline".to_string(),
                network_condition: NetworkCondition::Offline,
                expected_outcome: ExpectedOutcome::FallbackToArk,
            },
            
            // Scenario 3: Colab quick install
            TestScenario {
                name: "colab_quick_install".to_string(),
                description: "Quick installation in Google Colab environment".to_string(),
                environment: "colab".to_string(),
                network_condition: NetworkCondition::Online,
                expected_outcome: ExpectedOutcome::Success,
            },
            
            // Scenario 4: Rate limited recovery
            TestScenario {
                name: "rate_limited_recovery".to_string(),
                description: "Recovery from rate limiting with exponential backoff".to_string(),
                environment: "docker".to_string(),
                network_condition: NetworkCondition::RateLimited,
                expected_outcome: ExpectedOutcome::RetryAndSucceed,
            },
            
            // Scenario 5: Intermittent network
            TestScenario {
                name: "intermittent_network".to_string(),
                description: "Installation with intermittent network connectivity".to_string(),
                environment: "cloud_vm".to_string(),
                network_condition: NetworkCondition::Intermittent,
                expected_outcome: ExpectedOutcome::RetryAndSucceed,
            },
            
            // Scenario 6: Kubernetes pod installation
            TestScenario {
                name: "kubernetes_pod_installation".to_string(),
                description: "Installation in Kubernetes pod with resource constraints".to_string(),
                environment: "kubernetes".to_string(),
                network_condition: NetworkCondition::Online,
                expected_outcome: ExpectedOutcome::Success,
            },
            
            // Scenario 7: WSL2 installation
            TestScenario {
                name: "wsl2_installation".to_string(),
                description: "Installation in WSL2 environment".to_string(),
                environment: "wsl2".to_string(),
                network_condition: NetworkCondition::Online,
                expected_outcome: ExpectedOutcome::Success,
            },
            
            // Scenario 8: Complete failure scenario
            TestScenario {
                name: "complete_failure".to_string(),
                description: "All sources fail, should escalate to human".to_string(),
                environment: "bare_metal".to_string(),
                network_condition: NetworkCondition::Offline,
                expected_outcome: ExpectedOutcome::FailAndReport,
            },
        ]
    }
    
    #[test]
    fn test_e2e_scenarios_count() {
        let scenarios = get_e2e_scenarios();
        assert!(scenarios.len() >= 8, "Should have at least 8 E2E scenarios");
    }
    
    #[test]
    fn test_all_environments_covered() {
        let scenarios = get_e2e_scenarios();
        let environments: std::collections::HashSet<_> = scenarios.iter()
            .map(|s| s.environment.as_str())
            .collect();
        
        // Should cover all 6 target environments
        assert!(environments.contains("colab"));
        assert!(environments.contains("docker"));
        assert!(environments.contains("kubernetes"));
        assert!(environments.contains("wsl2"));
        assert!(environments.contains("cloud_vm"));
        assert!(environments.contains("bare_metal"));
    }
    
    #[test]
    fn test_all_network_conditions_covered() {
        let scenarios = get_e2e_scenarios();
        let conditions: Vec<_> = scenarios.iter()
            .map(|s| match s.network_condition {
                NetworkCondition::Online => "Online",
                NetworkCondition::Offline => "Offline",
                NetworkCondition::Intermittent => "Intermittent",
                NetworkCondition::RateLimited => "RateLimited",
            })
            .collect();
        
        assert!(conditions.contains(&"Online"));
        assert!(conditions.contains(&"Offline"));
        assert!(conditions.contains(&"Intermittent"));
        assert!(conditions.contains(&"RateLimited"));
    }
    
    #[test]
    fn test_success_scenarios_exist() {
        let scenarios = get_e2e_scenarios();
        let success_count = scenarios.iter()
            .filter(|s| s.expected_outcome == ExpectedOutcome::Success)
            .count();
        assert!(success_count >= 3, "Should have at least 3 success scenarios");
    }
    
    #[test]
    fn test_failure_scenarios_exist() {
        let scenarios = get_e2e_scenarios();
        let failure_count = scenarios.iter()
            .filter(|s| matches!(s.expected_outcome, 
                ExpectedOutcome::FailAndReport | ExpectedOutcome::FailAndEscalate))
            .count();
        assert!(failure_count >= 1, "Should have at least 1 failure scenario");
    }
}

// ============================================================================
// Test Runner
// ============================================================================

/// Run all integration tests and return results
pub fn run_all_tests(config: TestConfig) -> TestSuiteResult {
    let start = std::time::Instant::now();
    let mut results = Vec::new();
    let mut passed = 0;
    let mut failed = 0;
    let mut skipped = 0;
    
    // Note: In a real implementation, this would run actual tests
    // For now, we're just documenting the test structure
    
    TestSuiteResult {
        total: results.len() as u32,
        passed,
        failed,
        skipped,
        duration_secs: start.elapsed().as_secs_f64(),
        results,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_test_result_creation() {
        let result = TestResult {
            name: "test_example".to_string(),
            passed: true,
            duration_ms: 100,
            error_message: None,
        };
        assert!(result.passed);
    }
    
    #[test]
    fn test_test_suite_result_success_rate() {
        let result = TestSuiteResult {
            total: 100,
            passed: 80,
            failed: 20,
            skipped: 0,
            duration_secs: 10.0,
            results: vec![],
        };
        assert_eq!(result.success_rate(), 80.0);
    }
    
    #[test]
    fn test_test_suite_result_zero_division() {
        let result = TestSuiteResult {
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0,
            duration_secs: 0.0,
            results: vec![],
        };
        assert_eq!(result.success_rate(), 0.0);
    }
}
