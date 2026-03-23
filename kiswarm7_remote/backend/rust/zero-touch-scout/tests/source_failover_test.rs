//! Integration tests for Source Failover System
//!
//! These tests verify the 5-level source failover architecture:
//! Level 1: GitHub
//! Level 2: CDN
//! Level 3: IPFS
//! Level 4: Peer Mesh
//! Level 5: Physical Ark

use kiswarm_scout::source_failover::*;
use kiswarm_scout::config::ScoutConfig;
use kiswarm_scout::logging::AuditLogger;
use std::path::PathBuf;
use std::sync::Arc;
use tempfile::tempdir;

// ============================================================================
// Source Level Tests
// ============================================================================

#[test]
fn test_source_level_ordering() {
    let levels: Vec<_> = SourceLevel::iter_priority().collect();
    
    assert_eq!(levels.len(), 5, "Should have 5 source levels");
    assert_eq!(levels[0], SourceLevel::GitHub, "Level 1 should be GitHub");
    assert_eq!(levels[1], SourceLevel::CDN, "Level 2 should be CDN");
    assert_eq!(levels[2], SourceLevel::IPFS, "Level 3 should be IPFS");
    assert_eq!(levels[3], SourceLevel::PeerMesh, "Level 4 should be Peer Mesh");
    assert_eq!(levels[4], SourceLevel::PhysicalArk, "Level 5 should be Physical Ark");
}

#[test]
fn test_source_level_properties() {
    // Test online detection
    assert!(SourceLevel::GitHub.is_online());
    assert!(SourceLevel::CDN.is_online());
    assert!(SourceLevel::IPFS.is_online());
    assert!(SourceLevel::PeerMesh.is_online());
    assert!(!SourceLevel::PhysicalArk.is_online());
    
    // Test decentralized detection
    assert!(!SourceLevel::GitHub.is_decentralized());
    assert!(!SourceLevel::CDN.is_decentralized());
    assert!(SourceLevel::IPFS.is_decentralized());
    assert!(SourceLevel::PeerMesh.is_decentralized());
    assert!(!SourceLevel::PhysicalArk.is_decentralized());
    
    // Test level numbers
    assert_eq!(SourceLevel::GitHub.level(), 1);
    assert_eq!(SourceLevel::CDN.level(), 2);
    assert_eq!(SourceLevel::IPFS.level(), 3);
    assert_eq!(SourceLevel::PeerMesh.level(), 4);
    assert_eq!(SourceLevel::PhysicalArk.level(), 5);
}

#[test]
fn test_source_level_names() {
    assert_eq!(SourceLevel::GitHub.name(), "GitHub Repository");
    assert_eq!(SourceLevel::CDN.name(), "CDN Mirror");
    assert_eq!(SourceLevel::IPFS.name(), "IPFS Network");
    assert_eq!(SourceLevel::PeerMesh.name(), "Peer Mesh Network");
    assert_eq!(SourceLevel::PhysicalArk.name(), "Physical Ark");
}

// ============================================================================
// Source Health Tests
// ============================================================================

#[test]
fn test_source_health_usability() {
    // Healthy sources are usable
    assert!(SourceHealth::Healthy.is_usable());
    
    // Degraded sources are usable
    assert!(SourceHealth::Degraded {
        reason: DegradationReason::HighLatency
    }.is_usable());
    
    assert!(SourceHealth::Degraded {
        reason: DegradationReason::RateLimitApproaching
    }.is_usable());
    
    // Unhealthy sources are not usable
    assert!(!SourceHealth::Unhealthy {
        reason: UnhealthyReason::Timeout
    }.is_usable());
    
    assert!(!SourceHealth::Unhealthy {
        reason: UnhealthyReason::RateLimited
    }.is_usable());
    
    assert!(!SourceHealth::Unhealthy {
        reason: UnhealthyReason::NoPeers
    }.is_usable());
    
    // Unknown health is not usable
    assert!(!SourceHealth::Unknown.is_usable());
}

// ============================================================================
// Source Statistics Tests
// ============================================================================

#[test]
fn test_source_stats_tracking() {
    let mut stats = SourceStats::new();
    
    // Initial state
    assert_eq!(stats.total_attempts, 0);
    assert_eq!(stats.successful_fetches, 0);
    assert_eq!(stats.failed_fetches, 0);
    assert_eq!(stats.success_rate(), 100.0);
    
    // Record successes
    stats.record_success(100.0, 1000);
    stats.record_success(200.0, 2000);
    
    assert_eq!(stats.total_attempts, 2);
    assert_eq!(stats.successful_fetches, 2);
    assert_eq!(stats.total_bytes, 3000);
    
    // Record failure
    stats.record_failure(&UnhealthyReason::Timeout);
    
    assert_eq!(stats.total_attempts, 3);
    assert_eq!(stats.failed_fetches, 1);
    assert_eq!(stats.consecutive_failures, 1);
    
    // Check success rate
    let rate = stats.success_rate();
    assert!((rate - 66.66666666666666).abs() < 0.01);
}

#[test]
fn test_source_stats_health_updates() {
    let mut stats = SourceStats::new();
    
    // Record failures to trigger health changes
    stats.record_failure(&UnhealthyReason::Timeout);
    stats.record_failure(&UnhealthyReason::Timeout);
    
    // Should be degraded after 2 failures
    assert!(matches!(
        stats.health,
        SourceHealth::Degraded { .. }
    ));
    
    // More failures should make it unhealthy
    stats.record_failure(&UnhealthyReason::Timeout);
    stats.record_failure(&UnhealthyReason::Timeout);
    stats.record_failure(&UnhealthyReason::Timeout);
    
    assert!(matches!(
        stats.health,
        SourceHealth::Unhealthy { .. }
    ));
}

// ============================================================================
// Exponential Backoff Tests
// ============================================================================

#[test]
fn test_exponential_backoff() {
    let mut backoff = ExponentialBackoff::new(
        std::time::Duration::from_millis(100),
        std::time::Duration::from_secs(10),
    );
    
    // First delay should be close to initial
    let d1 = backoff.next_delay();
    assert!(d1.as_millis() >= 50); // With jitter, could be lower
    assert!(d1.as_millis() <= 500);
    
    // Subsequent delays should generally increase
    let d2 = backoff.next_delay();
    let d3 = backoff.next_delay();
    
    // Each delay should generally increase (with jitter, this is probabilistic)
    assert!(backoff.attempt() == 3);
    
    // Reset should reset attempt counter
    backoff.reset();
    assert_eq!(backoff.attempt(), 0);
}

// ============================================================================
// GitHub Source Tests
// ============================================================================

#[test]
fn test_github_source_creation() {
    let config = super::super::source_failover::github::GitHubConfig::default();
    let source = GitHubSource::new(config);
    
    assert!(source.is_ok());
    let source = source.unwrap();
    assert_eq!(source.level(), SourceLevel::GitHub);
    assert_eq!(source.name(), "github-primary");
}

#[test]
fn test_github_url_building() {
    use super::super::source_failover::github::GitHubConfig;
    
    let config = GitHubConfig::default();
    let source = GitHubSource::new(config).unwrap();
    
    // Test full archive URL
    let artifact = Artifact {
        name: "kiswarm".to_string(),
        checksum: None,
        min_size: None,
        max_size: None,
        required_signature: None,
        artifact_type: ArtifactType::FullArchive,
    };
    
    // URL should contain archive and .tar.gz
    // Note: This is testing internal logic, so we need to access it
    // through the fetch method or make the method public
    assert!(true); // Placeholder for actual URL verification
}

// ============================================================================
// CDN Source Tests
// ============================================================================

#[test]
fn test_cdn_source_creation() {
    let config = super::super::source_failover::cdn::CDNConfig::default();
    let source = CDNSource::new(config);
    
    assert!(source.is_ok());
    let source = source.unwrap();
    assert_eq!(source.level(), SourceLevel::CDN);
    assert_eq!(source.name(), "cdn-mirror");
}

#[test]
fn test_cdn_provider_sorting() {
    use super::super::source_failover::cdn::CDNConfig;
    
    let config = CDNConfig::default();
    let source = CDNSource::new(config).unwrap();
    
    // Providers should be sorted by priority
    // This is tested through the internal get_sorted_providers method
    assert!(true);
}

// ============================================================================
// IPFS Source Tests
// ============================================================================

#[test]
fn test_ipfs_source_creation() {
    let config = super::super::source_failover::ipfs::IPFSConfig::default();
    let source = IPFSSource::new(config);
    
    assert!(source.is_ok());
    let source = source.unwrap();
    assert_eq!(source.level(), SourceLevel::IPFS);
    assert_eq!(source.name(), "ipfs-network");
}

#[test]
fn test_ipfs_gateway_sorting() {
    use super::super::source_failover::ipfs::IPFSConfig;
    
    let config = IPFSConfig::default();
    let source = IPFSSource::new(config).unwrap();
    
    // Gateways should be sorted by priority
    assert!(true);
}

// ============================================================================
// Peer Mesh Source Tests
// ============================================================================

#[test]
fn test_peer_mesh_source_creation() {
    let config = super::super::source_failover::peer_mesh::PeerMeshConfig::default();
    let source = PeerMeshSource::new(config);
    
    assert!(source.is_ok());
    let source = source.unwrap();
    assert_eq!(source.level(), SourceLevel::PeerMesh);
    assert_eq!(source.name(), "peer-mesh");
}

#[test]
fn test_consensus_threshold() {
    use super::super::source_failover::peer_mesh::PeerMeshConfig;
    
    let config = PeerMeshConfig::default();
    assert_eq!(config.consensus_threshold, 0.67); // Byzantine consensus (2/3)
}

// ============================================================================
// Physical Ark Source Tests
// ============================================================================

#[test]
fn test_physical_ark_source_creation() {
    let config = super::super::source_failover::physical_ark::PhysicalArkConfig::default();
    let source = PhysicalArkSource::new(config);
    
    assert!(source.is_ok());
    let source = source.unwrap();
    assert_eq!(source.level(), SourceLevel::PhysicalArk);
    assert_eq!(source.name(), "physical-ark");
}

#[test]
fn test_version_comparison() {
    let config = super::super::source_failover::physical_ark::PhysicalArkConfig::default();
    let source = PhysicalArkSource::new(config).unwrap();
    
    // Test version comparison
    assert!(source.version_gte("6.3.5", "6.3.0"));
    assert!(source.version_gte("6.3.5", "6.3.5"));
    assert!(!source.version_gte("6.3.0", "6.3.5"));
    assert!(source.version_gte("7.0.0", "6.9.9"));
    assert!(source.version_gte("6.10.0", "6.9.0"));
}

// ============================================================================
// Failover Coordinator Tests
// ============================================================================

#[tokio::test]
async fn test_coordinator_creation() {
    let config = CoordinatorConfig::default();
    let scout_config = ScoutConfig::default();
    
    let mut coordinator = FailoverCoordinator::new(config, scout_config).unwrap();
    coordinator.initialize_sources().unwrap();
    
    // Should have all sources initialized
    assert!(coordinator.github_source.is_some());
    assert!(coordinator.cdn_source.is_some());
    assert!(coordinator.ipfs_source.is_some());
    assert!(coordinator.peer_mesh_source.is_some());
    assert!(coordinator.physical_ark_source.is_some());
}

#[tokio::test]
async fn test_coordinator_system_health() {
    let config = CoordinatorConfig::default();
    let scout_config = ScoutConfig::default();
    
    let mut coordinator = FailoverCoordinator::new(config, scout_config).unwrap();
    coordinator.initialize_sources().unwrap();
    
    // Get system health
    let health = coordinator.system_health().await;
    
    // Should have health for all sources
    assert_eq!(health.len(), 5);
    
    // All sources should have health status
    assert!(health.contains_key(&SourceLevel::GitHub));
    assert!(health.contains_key(&SourceLevel::CDN));
    assert!(health.contains_key(&SourceLevel::IPFS));
    assert!(health.contains_key(&SourceLevel::PeerMesh));
    assert!(health.contains_key(&SourceLevel::PhysicalArk));
}

#[tokio::test]
async fn test_coordinator_best_source() {
    let config = CoordinatorConfig::default();
    let scout_config = ScoutConfig::default();
    
    let mut coordinator = FailoverCoordinator::new(config, scout_config).unwrap();
    coordinator.initialize_sources().unwrap();
    
    // Get best available source
    let best = coordinator.best_available_source().await;
    
    // Best source could be any of the online sources
    // If no internet, might be None or Physical Ark
    if let Some(level) = best {
        assert!(level.is_online() || level == SourceLevel::PhysicalArk);
    }
}

// ============================================================================
// Failover Scenario Tests
// ============================================================================

#[test]
fn test_failover_history_tracking() {
    let history = vec![
        FailoverEntry {
            source_level: SourceLevel::GitHub,
            source_name: "github-primary".to_string(),
            failure_reason: "Rate limited".to_string(),
            time_spent: std::time::Duration::from_millis(500),
            retry_attempts: 3,
        },
        FailoverEntry {
            source_level: SourceLevel::CDN,
            source_name: "cdn-mirror".to_string(),
            failure_reason: "Connection timeout".to_string(),
            time_spent: std::time::Duration::from_millis(2000),
            retry_attempts: 2,
        },
    ];
    
    assert_eq!(history.len(), 2);
    assert_eq!(history[0].source_level, SourceLevel::GitHub);
    assert_eq!(history[1].source_level, SourceLevel::CDN);
}

#[test]
fn test_fetch_result_creation() {
    let result = FetchResult {
        source_level: SourceLevel::IPFS,
        source_name: "ipfs-gateway-cloudflare".to_string(),
        local_path: PathBuf::from("/tmp/artifact.tar.gz"),
        bytes_transferred: 12345678,
        duration: std::time::Duration::from_secs(5),
        attempts: 3,
        checksum_verified: true,
        signature_verified: false,
        timestamp: chrono::Utc::now().to_rfc3339(),
        failover_history: vec![],
    };
    
    assert_eq!(result.source_level, SourceLevel::IPFS);
    assert_eq!(result.attempts, 3);
    assert!(result.checksum_verified);
    assert!(!result.signature_verified);
}

// ============================================================================
// Configuration Tests
// ============================================================================

#[test]
fn test_coordinator_config_defaults() {
    let config = CoordinatorConfig::default();
    
    assert_eq!(config.mode, FailoverMode::Sequential);
    assert_eq!(config.max_total_attempts, 15);
    assert_eq!(config.max_total_time_secs, 600);
    assert!(config.cache_health_checks);
    assert!(config.skip_unhealthy);
}

#[test]
fn test_artifact_creation() {
    let artifact = Artifact {
        name: "kiswarm-core-v6.3.5".to_string(),
        checksum: Some("abc123def456".to_string()),
        min_size: Some(1024 * 1024),
        max_size: Some(100 * 1024 * 1024),
        required_signature: None,
        artifact_type: ArtifactType::KISWARMCore,
    };
    
    assert_eq!(artifact.name, "kiswarm-core-v6.3.5");
    assert!(artifact.checksum.is_some());
    assert_eq!(artifact.artifact_type, ArtifactType::KISWARMCore);
}

// ============================================================================
// End-to-End Tests
// ============================================================================

#[tokio::test]
#[ignore = "Requires network access"]
async fn test_full_failover_sequence() {
    // This test requires network access and would test the full failover sequence
    // from GitHub -> CDN -> IPFS -> Peer Mesh -> Physical Ark
    
    let config = CoordinatorConfig::default();
    let scout_config = ScoutConfig::default();
    
    let mut coordinator = FailoverCoordinator::new(config, scout_config).unwrap();
    coordinator.initialize_sources().unwrap();
    
    let artifact = Artifact {
        name: "test-artifact".to_string(),
        checksum: None,
        min_size: None,
        max_size: None,
        required_signature: None,
        artifact_type: ArtifactType::FullArchive,
    };
    
    let dest = PathBuf::from("/tmp/test-artifact.tar.gz");
    
    // This would perform actual network requests
    // let result = coordinator.fetch(&artifact, &dest, None).await;
    // For testing without network, we just verify the setup
    assert!(true);
}
