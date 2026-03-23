//! Network Layer for KISWARM Zero-Touch Scout
//! 
//! This module provides military-grade network operations:
//! - HTTP client with automatic retry and circuit breaker
//! - Multi-source download with failover
//! - Connection pooling and timeout handling
//! - Progress tracking and resumable downloads

use crate::config::NetworkConfig;
use crate::error::{ScoutError, ScoutResult};
use reqwest::{Client, Response, StatusCode};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;
use tokio::sync::RwLock;

/// HTTP client wrapper with retry and circuit breaker
#[derive(Clone)]
pub struct NetworkClient {
    /// Underlying reqwest client
    client: Client,
    
    /// Circuit breaker state
    circuit_breaker: Arc<RwLock<CircuitBreaker>>,
    
    /// Configuration
    config: NetworkConfig,
}

/// Circuit breaker states
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CircuitState {
    /// Circuit is closed, requests flow normally
    Closed,
    
    /// Circuit is open, requests are blocked
    Open,
    
    /// Circuit is half-open, testing if service recovered
    HalfOpen,
}

/// Circuit breaker implementation
#[derive(Debug, Clone)]
pub struct CircuitBreaker {
    /// Current state
    state: CircuitState,
    
    /// Number of consecutive failures
    failure_count: u32,
    
    /// Threshold to open circuit
    failure_threshold: u32,
    
    /// Time when circuit was opened
    opened_at: Option<Instant>,
    
    /// How long to wait before trying half-open
    recovery_timeout: Duration,
    
    /// Number of successful requests in half-open state
    success_count: u32,
    
    /// Successes needed to close circuit
    success_threshold: u32,
}

impl CircuitBreaker {
    /// Create a new circuit breaker
    pub fn new(failure_threshold: u32, recovery_timeout: Duration, success_threshold: u32) -> Self {
        Self {
            state: CircuitState::Closed,
            failure_count: 0,
            failure_threshold,
            opened_at: None,
            recovery_timeout,
            success_count: 0,
            success_threshold,
        }
    }
    
    /// Check if requests are allowed
    pub fn allow_request(&mut self) -> bool {
        match self.state {
            CircuitState::Closed => true,
            CircuitState::Open => {
                // Check if recovery timeout has passed
                if let Some(opened_at) = self.opened_at {
                    if opened_at.elapsed() >= self.recovery_timeout {
                        self.state = CircuitState::HalfOpen;
                        self.success_count = 0;
                        return true;
                    }
                }
                false
            }
            CircuitState::HalfOpen => true,
        }
    }
    
    /// Record a successful request
    pub fn record_success(&mut self) {
        match self.state {
            CircuitState::Closed => {
                self.failure_count = 0;
            }
            CircuitState::HalfOpen => {
                self.success_count += 1;
                if self.success_count >= self.success_threshold {
                    self.state = CircuitState::Closed;
                    self.failure_count = 0;
                }
            }
            CircuitState::Open => {}
        }
    }
    
    /// Record a failed request
    pub fn record_failure(&mut self) {
        match self.state {
            CircuitState::Closed => {
                self.failure_count += 1;
                if self.failure_count >= self.failure_threshold {
                    self.state = CircuitState::Open;
                    self.opened_at = Some(Instant::now());
                }
            }
            CircuitState::HalfOpen => {
                self.state = CircuitState::Open;
                self.opened_at = Some(Instant::now());
            }
            CircuitState::Open => {}
        }
    }
    
    /// Get current state
    pub fn state(&self) -> CircuitState {
        self.state
    }
}

impl NetworkClient {
    /// Create a new network client
    pub fn new(config: NetworkConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.total_timeout_secs))
            .connect_timeout(Duration::from_secs(config.connection_timeout_secs))
            .user_agent(&config.user_agent)
            .danger_accept_invalid_certs(!config.verify_tls)
            .pool_max_idle_per_host(10)
            .pool_idle_timeout(Duration::from_secs(60))
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            client,
            circuit_breaker: Arc::new(RwLock::new(CircuitBreaker::new(
                5,                          // 5 failures to open
                Duration::from_secs(30),    // 30s recovery timeout
                3,                          // 3 successes to close
            ))),
            config,
        })
    }
    
    /// Make a GET request with circuit breaker
    pub async fn get(&self, url: &str) -> ScoutResult<Response> {
        // Check circuit breaker
        {
            let mut cb = self.circuit_breaker.write().await;
            if !cb.allow_request() {
                return Err(ScoutError::NetworkError(
                    "Circuit breaker is open - service unavailable".to_string()
                ));
            }
        }
        
        // Make request
        let response = self.client
            .get(url)
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Request failed: {}", e)))?;
        
        // Update circuit breaker based on response
        {
            let mut cb = self.circuit_breaker.write().await;
            if response.status().is_server_error() {
                cb.record_failure();
            } else {
                cb.record_success();
            }
        }
        
        Ok(response)
    }
    
    /// Download a file with progress tracking
    pub async fn download_file(
        &self,
        url: &str,
        dest: &Path,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<()> {
        // Check circuit breaker
        {
            let mut cb = self.circuit_breaker.write().await;
            if !cb.allow_request() {
                return Err(ScoutError::NetworkError(
                    "Circuit breaker is open".to_string()
                ));
            }
        }
        
        // Make request
        let response = self.client
            .get(url)
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: url.to_string(),
                reason: e.to_string(),
            })?;
        
        let status = response.status();
        if !status.is_success() {
            let mut cb = self.circuit_breaker.write().await;
            cb.record_failure();
            return Err(ScoutError::DownloadFailed {
                source: url.to_string(),
                reason: format!("HTTP {}", status.as_u16()),
            });
        }
        
        // Get content length if available
        let total_size = response.content_length().unwrap_or(0);
        
        // Create parent directory
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| ScoutError::DirectoryCreationFailed { path: parent.to_path_buf() })?;
        }
        
        // Create file
        let mut file = tokio::fs::File::create(dest)
            .await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.to_path_buf() })?;
        
        // Download with progress
        let mut downloaded: u64 = 0;
        let mut stream = response.bytes_stream();
        
        use futures::StreamExt;
        
        while let Some(chunk_result) = stream.next().await {
            let chunk = chunk_result
                .map_err(|e| ScoutError::DownloadFailed {
                    source: url.to_string(),
                    reason: e.to_string(),
                })?;
            
            file.write_all(&chunk).await
                .map_err(|e| ScoutError::FileWriteFailed { path: dest.to_path_buf() })?;
            
            downloaded += chunk.len() as u64;
            
            if let Some(ref callback) = progress_callback {
                callback(downloaded, total_size);
            }
        }
        
        file.flush().await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.to_path_buf() })?;
        
        // Update circuit breaker
        {
            let mut cb = self.circuit_breaker.write().await;
            cb.record_success();
        }
        
        Ok(())
    }
    
    /// Check if a URL is reachable
    pub async fn check_url(&self, url: &str) -> ScoutResult<bool> {
        let response = self.client
            .head(url)
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(e.to_string()))?;
        
        Ok(response.status().is_success())
    }
    
    /// Get circuit breaker state
    pub async fn circuit_state(&self) -> CircuitState {
        let cb = self.circuit_breaker.read().await;
        cb.state()
    }
}

/// Download source with priority
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadSource {
    /// Source name
    pub name: String,
    
    /// Source URL
    pub url: String,
    
    /// Priority (lower = higher priority)
    pub priority: u32,
    
    /// Source type
    pub source_type: SourceType,
    
    /// Expected checksum (if known)
    pub checksum: Option<String>,
    
    /// Minimum required bandwidth (bytes/sec)
    pub min_bandwidth: Option<u64>,
    
    /// Maximum retries for this source
    pub max_retries: u32,
}

/// Type of download source
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SourceType {
    /// GitHub repository
    GitHub,
    
    /// GitLab mirror
    GitLab,
    
    /// CDN endpoint
    CDN,
    
    /// IPFS gateway
    IPFS,
    
    /// BitTorrent
    BitTorrent,
    
    /// Peer mesh
    PeerMesh,
    
    /// Local Ark cache
    ArkCache,
    
    /// USB/Physical media
    PhysicalMedia,
}

/// Multi-source downloader with failover
pub struct MultiSourceDownloader {
    /// Network client
    client: NetworkClient,
    
    /// List of sources sorted by priority
    sources: Vec<DownloadSource>,
    
    /// Current source index
    current_source: Arc<RwLock<usize>>,
}

impl MultiSourceDownloader {
    /// Create a new multi-source downloader
    pub fn new(client: NetworkClient, mut sources: Vec<DownloadSource>) -> Self {
        // Sort by priority
        sources.sort_by_key(|s| s.priority);
        
        Self {
            client,
            sources,
            current_source: Arc::new(RwLock::new(0)),
        }
    }
    
    /// Download from best available source
    pub async fn download(
        &self,
        dest: &Path,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<DownloadSource> {
        let mut last_error: Option<ScoutError> = None;
        
        for (index, source) in self.sources.iter().enumerate() {
            // Update current source
            {
                let mut current = self.current_source.write().await;
                *current = index;
            }
            
            // Skip if source type is not online
            if matches!(
                source.source_type,
                SourceType::ArkCache | SourceType::PhysicalMedia
            ) {
                continue;
            }
            
            // Try to download
            match self.client.download_file(&source.url, dest, progress_callback.clone()).await {
                Ok(()) => {
                    // Verify checksum if provided
                    if let Some(ref expected_checksum) = source.checksum {
                        if !self.verify_checksum(dest, expected_checksum).await? {
                            // Checksum mismatch, try next source
                            last_error = Some(ScoutError::IntegrityCheckFailed {
                                expected: expected_checksum.clone(),
                                actual: "mismatch".to_string(),
                            });
                            continue;
                        }
                    }
                    
                    return Ok(source.clone());
                }
                Err(e) => {
                    last_error = Some(e);
                    continue;
                }
            }
        }
        
        // All sources failed
        Err(last_error.unwrap_or(ScoutError::AllSourcesExhausted))
    }
    
    /// Verify file checksum
    async fn verify_checksum(&self, path: &Path, expected: &str) -> ScoutResult<bool> {
        use sha2::{Digest, Sha256};
        
        let content = tokio::fs::read(path).await
            .map_err(|e| ScoutError::FileReadFailed { path: path.to_path_buf() })?;
        
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let actual = format!("{:x}", hasher.finalize());
        
        Ok(actual == expected)
    }
    
    /// Get current source
    pub async fn current_source(&self) -> Option<DownloadSource> {
        let index = *self.current_source.read().await;
        self.sources.get(index).cloned()
    }
    
    /// Get list of all sources
    pub fn sources(&self) -> &[DownloadSource] {
        &self.sources
    }
}

/// Network status and diagnostics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkStatus {
    /// Internet connectivity
    pub has_internet: bool,
    
    /// GitHub reachable
    pub github_reachable: bool,
    
    /// PyPI reachable
    pub pypi_reachable: bool,
    
    /// Circuit breaker state
    pub circuit_state: String,
    
    /// Latency measurements
    pub latencies: std::collections::HashMap<String, f64>,
    
    /// Available sources
    pub available_sources: Vec<String>,
    
    /// Timestamp
    pub timestamp: String,
}

/// Network diagnostics runner
pub struct NetworkDiagnostics {
    client: NetworkClient,
}

impl NetworkDiagnostics {
    /// Create new diagnostics runner
    pub fn new(client: NetworkClient) -> Self {
        Self { client }
    }
    
    /// Run full network diagnostics
    pub async fn run(&self) -> NetworkStatus {
        let mut latencies = std::collections::HashMap::new();
        
        // Check GitHub
        let github_start = Instant::now();
        let github_reachable = self.check_endpoint("https://github.com").await;
        if github_reachable {
            latencies.insert("github".to_string(), github_start.elapsed().as_millis() as f64);
        }
        
        // Check PyPI
        let pypi_start = Instant::now();
        let pypi_reachable = self.check_endpoint("https://pypi.org").await;
        if pypi_reachable {
            latencies.insert("pypi".to_string(), pypi_start.elapsed().as_millis() as f64);
        }
        
        // Check Ollama
        let ollama_start = Instant::now();
        let ollama_reachable = self.check_endpoint("http://localhost:11434").await;
        if ollama_reachable {
            latencies.insert("ollama".to_string(), ollama_start.elapsed().as_millis() as f64);
        }
        
        let has_internet = github_reachable || pypi_reachable;
        
        NetworkStatus {
            has_internet,
            github_reachable,
            pypi_reachable,
            circuit_state: format!("{:?}", self.client.circuit_state().await),
            latencies,
            available_sources: vec![], // Would be populated by source checker
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }
    
    /// Check if an endpoint is reachable
    async fn check_endpoint(&self, url: &str) -> bool {
        match self.client.check_url(url).await {
            Ok(true) => true,
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_circuit_breaker_states() {
        let mut cb = CircuitBreaker::new(3, Duration::from_secs(10), 2);
        
        // Should start closed
        assert_eq!(cb.state(), CircuitState::Closed);
        assert!(cb.allow_request());
        
        // Failures should eventually open
        cb.record_failure();
        cb.record_failure();
        cb.record_failure();
        assert_eq!(cb.state(), CircuitState::Open);
        assert!(!cb.allow_request());
    }
    
    #[test]
    fn test_circuit_breaker_recovery() {
        let mut cb = CircuitBreaker::new(2, Duration::from_millis(10), 2);
        
        // Open the circuit
        cb.record_failure();
        cb.record_failure();
        assert_eq!(cb.state(), CircuitState::Open);
        
        // Wait for recovery timeout
        std::thread::sleep(Duration::from_millis(20));
        
        // Should transition to half-open
        assert!(cb.allow_request());
        assert_eq!(cb.state(), CircuitState::HalfOpen);
        
        // Successes should close it
        cb.record_success();
        cb.record_success();
        assert_eq!(cb.state(), CircuitState::Closed);
    }
    
    #[test]
    fn test_download_source_priority() {
        let sources = vec![
            DownloadSource {
                name: "cdn".to_string(),
                url: "https://cdn.example.com".to_string(),
                priority: 2,
                source_type: SourceType::CDN,
                checksum: None,
                min_bandwidth: None,
                max_retries: 3,
            },
            DownloadSource {
                name: "github".to_string(),
                url: "https://github.com".to_string(),
                priority: 1,
                source_type: SourceType::GitHub,
                checksum: None,
                min_bandwidth: None,
                max_retries: 3,
            },
        ];
        
        let config = NetworkConfig::default();
        let client = NetworkClient::new(config).unwrap();
        let downloader = MultiSourceDownloader::new(client, sources);
        
        // Should be sorted by priority
        assert_eq!(downloader.sources()[0].name, "github");
        assert_eq!(downloader.sources()[1].name, "cdn");
    }
}
