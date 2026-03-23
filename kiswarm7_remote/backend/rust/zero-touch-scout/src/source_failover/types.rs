//! Common types for Source Failover System
//!
//! This module defines all shared types, traits, and structures used across
//! the 5-level source failover architecture.

use crate::error::{ScoutError, ScoutResult};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Source level in the failover hierarchy (1 = highest priority)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SourceLevel {
    /// Level 1: GitHub repository (Primary)
    /// Direct access to source repository with rate limit awareness
    GitHub = 1,
    
    /// Level 2: CDN mirrors (Secondary)
    /// Cloudflare, AWS CloudFront, Fastly, etc.
    CDN = 2,
    
    /// Level 3: IPFS network (Tertiary)
    /// Decentralized content-addressed storage
    IPFS = 3,
    
    /// Level 4: Peer Mesh (Quaternary)
    /// P2P network with Byzantine fault tolerance
    PeerMesh = 4,
    
    /// Level 5: Physical Ark (Last Resort)
    /// USB, Optical Disk, Pre-staged cache
    PhysicalArk = 5,
}

impl SourceLevel {
    /// Get human-readable name
    pub fn name(&self) -> &'static str {
        match self {
            SourceLevel::GitHub => "GitHub Repository",
            SourceLevel::CDN => "CDN Mirror",
            SourceLevel::IPFS => "IPFS Network",
            SourceLevel::PeerMesh => "Peer Mesh Network",
            SourceLevel::PhysicalArk => "Physical Ark",
        }
    }
    
    /// Get level number
    pub fn level(&self) -> u8 {
        *self as u8
    }
    
    /// Check if this is an online source
    pub fn is_online(&self) -> bool {
        matches!(self, SourceLevel::GitHub | SourceLevel::CDN | SourceLevel::IPFS | SourceLevel::PeerMesh)
    }
    
    /// Check if this is a decentralized source
    pub fn is_decentralized(&self) -> bool {
        matches!(self, SourceLevel::IPFS | SourceLevel::PeerMesh)
    }
    
    /// Iterate in priority order
    pub fn iter_priority() -> impl Iterator<Item = SourceLevel> {
        [
            SourceLevel::GitHub,
            SourceLevel::CDN,
            SourceLevel::IPFS,
            SourceLevel::PeerMesh,
            SourceLevel::PhysicalArk,
        ].into_iter()
    }
}

/// Health status of a source
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SourceHealth {
    /// Source is healthy and available
    Healthy,
    
    /// Source is degraded but functional
    Degraded {
        /// Reason for degradation
        reason: DegradationReason,
    },
    
    /// Source is unhealthy and should be skipped
    Unhealthy {
        /// Reason for unhealthiness
        reason: UnhealthyReason,
    },
    
    /// Source health is unknown (not yet checked)
    Unknown,
}

impl Default for SourceHealth {
    fn default() -> Self {
        SourceHealth::Unknown
    }
}

impl SourceHealth {
    /// Check if source is usable
    pub fn is_usable(&self) -> bool {
        matches!(self, SourceHealth::Healthy | SourceHealth::Degraded { .. })
    }
}

/// Reason for source degradation
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DegradationReason {
    /// High latency detected
    HighLatency,
    
    /// Rate limit approaching
    RateLimitApproaching,
    
    /// Intermittent errors
    IntermittentErrors,
    
    /// Partial availability
    PartialAvailability,
    
    /// Certificate expiring soon
    CertificateExpiring,
}

/// Reason for source being unhealthy
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum UnhealthyReason {
    /// Connection timeout
    Timeout,
    
    /// Connection refused
    ConnectionRefused,
    
    /// DNS resolution failed
    DNSFailed,
    
    /// TLS/SSL error
    TLSError,
    
    /// HTTP 4xx error
    HTTPError {
        /// HTTP status code
        code: u16,
    },
    
    /// HTTP 5xx error
    ServerError {
        /// HTTP status code
        code: u16,
    },
    
    /// Rate limited
    RateLimited,
    
    /// Content not found (404)
    NotFound,
    
    /// Integrity check failed
    IntegrityCheckFailed,
    
    /// No peers available
    NoPeers,
    
    /// Consensus failed
    ConsensusFailed,
    
    /// Physical media not present
    MediaNotPresent,
    
    /// Unknown error
    Unknown,
}

/// Artifact to fetch from sources
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    /// Artifact name/identifier
    pub name: String,
    
    /// Expected SHA-256 checksum
    pub checksum: Option<String>,
    
    /// Minimum size in bytes
    pub min_size: Option<u64>,
    
    /// Maximum size in bytes
    pub max_size: Option<u64>,
    
    /// Required GPG signature
    pub required_signature: Option<String>,
    
    /// Artifact type
    pub artifact_type: ArtifactType,
}

/// Type of artifact
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArtifactType {
    /// KISWARM core package
    KISWARMCore,
    
    /// Python wheel package
    PythonWheel,
    
    /// Ollama model binary
    OllamaModel,
    
    /// Configuration file
    ConfigFile,
    
    /// Certificate bundle
    CertificateBundle,
    
    /// Ark manifest
    ArkManifest,
    
    /// Full archive
    FullArchive,
    
    /// Differential update
    DifferentialUpdate,
}

/// Result of a source fetch operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FetchResult {
    /// Source level that succeeded
    pub source_level: SourceLevel,
    
    /// Specific source that was used
    pub source_name: String,
    
    /// Path where artifact was saved
    pub local_path: PathBuf,
    
    /// Total bytes transferred
    pub bytes_transferred: u64,
    
    /// Total time taken
    pub duration: Duration,
    
    /// Number of attempts before success
    pub attempts: u8,
    
    /// Whether checksum was verified
    pub checksum_verified: bool,
    
    /// Whether signature was verified
    pub signature_verified: bool,
    
    /// Timestamp of fetch
    pub timestamp: String,
    
    /// Failover history (sources tried before success)
    pub failover_history: Vec<FailoverEntry>,
}

/// Entry in the failover history
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailoverEntry {
    /// Source level that failed
    pub source_level: SourceLevel,
    
    /// Source name that failed
    pub source_name: String,
    
    /// Reason for failure
    pub failure_reason: String,
    
    /// Time spent on this source
    pub time_spent: Duration,
    
    /// Number of retry attempts
    pub retry_attempts: u8,
}

/// Statistics for a source
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SourceStats {
    /// Total fetches attempted
    pub total_attempts: u64,
    
    /// Successful fetches
    pub successful_fetches: u64,
    
    /// Failed fetches
    pub failed_fetches: u64,
    
    /// Average latency in milliseconds
    pub avg_latency_ms: f64,
    
    /// Last successful fetch time
    pub last_success: Option<String>,
    
    /// Last failure time
    pub last_failure: Option<String>,
    
    /// Current health status
    pub health: SourceHealth,
    
    /// Consecutive failures
    pub consecutive_failures: u32,
    
    /// Total bytes transferred
    pub total_bytes: u64,
}

impl SourceStats {
    /// Create new empty stats
    pub fn new() -> Self {
        Self {
            health: SourceHealth::Unknown,
            ..Default::default()
        }
    }
    
    /// Record a successful fetch
    pub fn record_success(&mut self, latency_ms: f64, bytes: u64) {
        self.total_attempts += 1;
        self.successful_fetches += 1;
        self.consecutive_failures = 0;
        self.total_bytes += bytes;
        self.last_success = Some(chrono::Utc::now().to_rfc3339());
        
        // Update average latency
        if self.avg_latency_ms == 0.0 {
            self.avg_latency_ms = latency_ms;
        } else {
            self.avg_latency_ms = (self.avg_latency_ms * 0.9) + (latency_ms * 0.1);
        }
        
        // Update health
        self.health = SourceHealth::Healthy;
    }
    
    /// Record a failed fetch
    pub fn record_failure(&mut self, reason: &UnhealthyReason) {
        self.total_attempts += 1;
        self.failed_fetches += 1;
        self.consecutive_failures += 1;
        self.last_failure = Some(chrono::Utc::now().to_rfc3339());
        
        // Update health based on consecutive failures
        if self.consecutive_failures >= 5 {
            self.health = SourceHealth::Unhealthy { reason: *reason };
        } else if self.consecutive_failures >= 2 {
            self.health = SourceHealth::Degraded {
                reason: DegradationReason::IntermittentErrors,
            };
        }
    }
    
    /// Get success rate as percentage
    pub fn success_rate(&self) -> f64 {
        if self.total_attempts == 0 {
            return 100.0;
        }
        (self.successful_fetches as f64 / self.total_attempts as f64) * 100.0
    }
}

/// Trait for source implementations
#[async_trait::async_trait]
pub trait Source: Send + Sync {
    /// Get the source level
    fn level(&self) -> SourceLevel;
    
    /// Get the source name
    fn name(&self) -> &str;
    
    /// Check if source is available
    async fn check_availability(&self) -> ScoutResult<SourceHealth>;
    
    /// Fetch an artifact
    async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult>;
    
    /// Get source statistics
    fn stats(&self) -> &SourceStats;
    
    /// Reset source statistics
    fn reset_stats(&mut self);
    
    /// Get estimated time to fetch (based on historical data)
    fn estimated_fetch_time(&self, artifact_size: u64) -> Duration {
        let stats = self.stats();
        if stats.avg_latency_ms > 0.0 {
            Duration::from_millis(stats.avg_latency_ms as u64)
        } else {
            Duration::from_secs(30) // Default estimate
        }
    }
}

/// Configuration for a source
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceConfig {
    /// Enable this source
    pub enabled: bool,
    
    /// Maximum retries before failover
    pub max_retries: u8,
    
    /// Initial retry delay
    pub retry_delay_ms: u64,
    
    /// Maximum retry delay (for exponential backoff)
    pub max_retry_delay_ms: u64,
    
    /// Timeout for each attempt
    pub timeout_secs: u64,
    
    /// Skip health check (assume healthy)
    pub skip_health_check: bool,
}

impl Default for SourceConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            max_retries: 3,
            retry_delay_ms: 1000,
            max_retry_delay_ms: 30000,
            timeout_secs: 120,
            skip_health_check: false,
        }
    }
}

/// Failover configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailoverConfig {
    /// Enable parallel source checking
    pub parallel_check: bool,
    
    /// Number of sources to check in parallel
    pub parallel_count: usize,
    
    /// Health check interval
    pub health_check_interval_secs: u64,
    
    /// Minimum sources required
    pub min_sources_required: usize,
    
    /// Enable failover logging
    pub enable_logging: bool,
    
    /// Per-source configurations
    pub source_configs: std::collections::HashMap<SourceLevel, SourceConfig>,
}

impl Default for FailoverConfig {
    fn default() -> Self {
        let mut source_configs = std::collections::HashMap::new();
        source_configs.insert(SourceLevel::GitHub, SourceConfig {
            max_retries: 3,
            timeout_secs: 120,
            ..Default::default()
        });
        source_configs.insert(SourceLevel::CDN, SourceConfig {
            max_retries: 2,
            timeout_secs: 60,
            ..Default::default()
        });
        source_configs.insert(SourceLevel::IPFS, SourceConfig {
            max_retries: 3,
            timeout_secs: 180,
            ..Default::default()
        });
        source_configs.insert(SourceLevel::PeerMesh, SourceConfig {
            max_retries: 2,
            timeout_secs: 240,
            ..Default::default()
        });
        source_configs.insert(SourceLevel::PhysicalArk, SourceConfig {
            max_retries: 1,
            timeout_secs: 600,
            ..Default::default()
        });
        
        Self {
            parallel_check: true,
            parallel_count: 2,
            health_check_interval_secs: 60,
            min_sources_required: 1,
            enable_logging: true,
            source_configs,
        }
    }
}

/// Exponential backoff calculator
pub struct ExponentialBackoff {
    /// Initial delay
    initial_delay: Duration,
    
    /// Maximum delay
    max_delay: Duration,
    
    /// Current attempt
    attempt: u8,
    
    /// Multiplier
    multiplier: f64,
    
    /// Jitter factor (0.0 to 1.0)
    jitter: f64,
}

impl ExponentialBackoff {
    /// Create a new exponential backoff
    pub fn new(initial_delay: Duration, max_delay: Duration) -> Self {
        Self {
            initial_delay,
            max_delay,
            attempt: 0,
            multiplier: 2.0,
            jitter: 0.3,
        }
    }
    
    /// Get next delay and increment attempt
    pub fn next_delay(&mut self) -> Duration {
        let base_delay = self.initial_delay.as_millis() as f64
            * self.multiplier.powi(self.attempt as i32);
        
        // Add jitter
        let jitter_range = base_delay * self.jitter;
        let jittered = base_delay + (rand_jitter() * jitter_range) - (jitter_range / 2.0);
        
        // Clamp to max
        let delay_ms = jittered.min(self.max_delay.as_millis() as f64).max(0.0) as u64;
        
        self.attempt += 1;
        
        Duration::from_millis(delay_ms)
    }
    
    /// Reset attempt counter
    pub fn reset(&mut self) {
        self.attempt = 0;
    }
    
    /// Get current attempt number
    pub fn attempt(&self) -> u8 {
        self.attempt
    }
}

/// Simple random jitter generator (deterministic for testing)
fn rand_jitter() -> f64 {
    // Use a simple deterministic jitter based on time
    let ns = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.subsec_nanos())
        .unwrap_or(0);
    
    (ns as f64 / u32::MAX as f64)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_source_level_ordering() {
        let levels: Vec<_> = SourceLevel::iter_priority().collect();
        assert_eq!(levels.len(), 5);
        assert_eq!(levels[0], SourceLevel::GitHub);
        assert_eq!(levels[4], SourceLevel::PhysicalArk);
    }
    
    #[test]
    fn test_source_health_usability() {
        assert!(SourceHealth::Healthy.is_usable());
        assert!(SourceHealth::Degraded { reason: DegradationReason::HighLatency }.is_usable());
        assert!(!SourceHealth::Unhealthy { reason: UnhealthyReason::Timeout }.is_usable());
    }
    
    #[test]
    fn test_source_stats_success_rate() {
        let mut stats = SourceStats::new();
        assert_eq!(stats.success_rate(), 100.0);
        
        stats.record_success(100.0, 1000);
        stats.record_success(200.0, 2000);
        stats.record_failure(&UnhealthyReason::Timeout);
        
        assert_eq!(stats.total_attempts, 3);
        assert_eq!(stats.successful_fetches, 2);
        assert!((stats.success_rate() - 66.66666666666666).abs() < 0.01);
    }
    
    #[test]
    fn test_exponential_backoff() {
        let mut backoff = ExponentialBackoff::new(
            Duration::from_millis(100),
            Duration::from_secs(10),
        );
        
        let d1 = backoff.next_delay();
        let d2 = backoff.next_delay();
        let d3 = backoff.next_delay();
        
        // Each delay should generally increase
        assert!(d2 >= Duration::from_millis(50)); // With jitter, could be lower
        assert!(backoff.attempt() == 3);
    }
}
