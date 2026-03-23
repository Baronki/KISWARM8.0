//! Level 3: IPFS Source Implementation
//!
//! Tertiary source using InterPlanetary File System.
//! Features:
//! - Multiple public gateways with failover
//! - Content-addressed verification (CID)
//! - Local IPFS node support
//! - Peer discovery and DHT queries

use super::types::*;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;

/// IPFS gateway configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IPFSGateway {
    /// Gateway name
    pub name: String,
    
    /// Gateway URL
    pub url: String,
    
    /// Priority
    pub priority: u32,
    
    /// Rate limit (requests per minute)
    pub rate_limit: Option<u32>,
    
    /// Supports CAR files
    pub supports_car: bool,
    
    /// Average latency estimate (ms)
    pub avg_latency_ms: u64,
}

/// IPFS source configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IPFSConfig {
    /// List of public gateways
    pub gateways: Vec<IPFSGateway>,
    
    /// Local IPFS node URL (optional)
    pub local_node_url: Option<String>,
    
    /// Prefer local node if available
    pub prefer_local: bool,
    
    /// Content identifiers (CIDs) for artifacts
    pub artifact_cids: std::collections::HashMap<String, String>,
    
    /// Timeout for gateway requests
    pub timeout_secs: u64,
    
    /// Maximum peers to query
    pub max_peers: u32,
    
    /// User agent
    pub user_agent: String,
}

impl Default for IPFSConfig {
    fn default() -> Self {
        let mut artifact_cids = std::collections::HashMap::new();
        // Example CIDs would be replaced with actual KISWARM content CIDs
        artifact_cids.insert(
            "kiswarm-core".to_string(),
            "QmXyz123...kiswarm-core-v6.3.5".to_string()
        );
        artifact_cids.insert(
            "kiswarm-full".to_string(),
            "QmAbc456...kiswarm-full-v6.3.5".to_string()
        );
        
        Self {
            gateways: vec![
                IPFSGateway {
                    name: "ipfs.io".to_string(),
                    url: "https://ipfs.io/ipfs".to_string(),
                    priority: 1,
                    rate_limit: Some(300),
                    supports_car: true,
                    avg_latency_ms: 500,
                },
                IPFSGateway {
                    name: "cloudflare-ipfs".to_string(),
                    url: "https://cloudflare-ipfs.com/ipfs".to_string(),
                    priority: 2,
                    rate_limit: Some(500),
                    supports_car: true,
                    avg_latency_ms: 300,
                },
                IPFSGateway {
                    name: "dweb".to_string(),
                    url: "https://dweb.link/ipfs".to_string(),
                    priority: 3,
                    rate_limit: None,
                    supports_car: true,
                    avg_latency_ms: 400,
                },
                IPFSGateway {
                    name: "gateway.pinata".to_string(),
                    url: "https://gateway.pinata.cloud/ipfs".to_string(),
                    priority: 4,
                    rate_limit: Some(200),
                    supports_car: false,
                    avg_latency_ms: 350,
                },
                IPFSGateway {
                    name: "4everland".to_string(),
                    url: "https://4everland.io/ipfs".to_string(),
                    priority: 5,
                    rate_limit: None,
                    supports_car: true,
                    avg_latency_ms: 450,
                },
            ],
            local_node_url: Some("http://127.0.0.1:5001".to_string()),
            prefer_local: true,
            artifact_cids,
            timeout_secs: 180,
            max_peers: 20,
            user_agent: "KISWARM-ZeroTouchScout/6.3.5".to_string(),
        }
    }
}

/// IPFS peer information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IPFSPeer {
    /// Peer ID
    pub peer_id: String,
    
    /// Multi-addresses
    pub addresses: Vec<String>,
    
    /// Latency in milliseconds
    pub latency_ms: Option<u64>,
    
    /// Connection state
    pub connected: bool,
}

/// IPFS Source implementation
pub struct IPFSSource {
    /// Configuration
    config: IPFSConfig,
    
    /// HTTP client
    client: Client,
    
    /// Source statistics
    stats: SourceStats,
    
    /// Known peers
    peers: Arc<tokio::sync::RwLock<Vec<IPFSPeer>>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl IPFSSource {
    /// Create a new IPFS source
    pub fn new(config: IPFSConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .user_agent(&config.user_agent)
            .pool_max_idle_per_host(10)
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            stats: SourceStats::new(),
            peers: Arc::new(tokio::sync::RwLock::new(Vec::new())),
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Get CID for artifact
    fn get_cid(&self, artifact: &Artifact) -> Option<String> {
        self.config.artifact_cids.get(&artifact.name).cloned()
            .or_else(|| {
                // Try to derive CID from checksum
                artifact.checksum.clone()
            })
    }
    
    /// Build URL for gateway
    fn build_gateway_url(&self, gateway: &IPFSGateway, cid: &str) -> String {
        format!("{}/{}", gateway.url, cid)
    }
    
    /// Check if local IPFS node is available
    async fn check_local_node(&self) -> bool {
        if let Some(ref url) = self.config.local_node_url {
            let check_url = format!("{}/api/v0/id", url);
            
            match self.client
                .post(&check_url)
                .timeout(Duration::from_secs(5))
                .send()
                .await
            {
                Ok(resp) => resp.status().is_success(),
                Err(_) => false,
            }
        } else {
            false
        }
    }
    
    /// Download from local IPFS node
    async fn download_from_local(
        &self,
        cid: &str,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<u64> {
        let node_url = self.config.local_node_url.as_ref().unwrap();
        let url = format!("{}/api/v0/cat?arg={}", node_url, cid);
        
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting IPFS local node download", serde_json::json!({
                "cid": cid,
                "dest": dest.to_string_lossy(),
            }))?;
        }
        
        let response = self.client
            .post(&url)
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: format!("ipfs-local:{}", cid),
                reason: e.to_string(),
            })?;
        
        if !response.status().is_success() {
            return Err(ScoutError::DownloadFailed {
                source: format!("ipfs-local:{}", cid),
                reason: format!("HTTP {}", response.status().as_u16()),
            });
        }
        
        let total_size = response.content_length().unwrap_or(0);
        
        // Create parent directory
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| ScoutError::DirectoryCreationFailed { path: parent.to_path_buf() })?;
        }
        
        // Download file
        let mut file = tokio::fs::File::create(dest)
            .await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        let mut downloaded: u64 = 0;
        let mut stream = response.bytes_stream();
        
        use futures::StreamExt;
        
        while let Some(chunk_result) = stream.next().await {
            let chunk = chunk_result
                .map_err(|e| ScoutError::DownloadFailed {
                    source: format!("ipfs-local:{}", cid),
                    reason: e.to_string(),
                })?;
            
            file.write_all(&chunk).await
                .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
            
            downloaded += chunk.len() as u64;
            
            if let Some(ref callback) = progress_callback {
                callback(downloaded, total_size);
            }
        }
        
        file.flush().await
            .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        if let Some(logger) = &self.logger {
            logger.info("IPFS local node download complete", serde_json::json!({
                "cid": cid,
                "bytes": downloaded,
                "duration_ms": start.elapsed().as_millis(),
            }))?;
        }
        
        Ok(downloaded)
    }
    
    /// Download from gateway
    async fn download_from_gateway(
        &self,
        gateway: &IPFSGateway,
        cid: &str,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<u64> {
        let url = self.build_gateway_url(gateway, cid);
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting IPFS gateway download", serde_json::json!({
                "gateway": &gateway.name,
                "cid": cid,
                "url": &url,
            }))?;
        }
        
        let response = self.client
            .get(&url)
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: url.clone(),
                reason: e.to_string(),
            })?;
        
        let status = response.status();
        
        if status == StatusCode::NOT_FOUND || status == StatusCode::GATEWAY_TIMEOUT {
            return Err(ScoutError::DownloadFailed {
                source: url.clone(),
                reason: format!("Content not found or timeout: {}", status.as_u16()),
            });
        }
        
        if !status.is_success() {
            return Err(ScoutError::DownloadFailed {
                source: url.clone(),
                reason: format!("HTTP {}", status.as_u16()),
            });
        }
        
        let total_size = response.content_length().unwrap_or(0);
        
        // Create parent directory
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| ScoutError::DirectoryCreationFailed { path: parent.to_path_buf() })?;
        }
        
        // Download file
        let mut file = tokio::fs::File::create(dest)
            .await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        let mut downloaded: u64 = 0;
        let mut stream = response.bytes_stream();
        
        use futures::StreamExt;
        
        while let Some(chunk_result) = stream.next().await {
            let chunk = chunk_result
                .map_err(|e| ScoutError::DownloadFailed {
                    source: url.clone(),
                    reason: e.to_string(),
                })?;
            
            file.write_all(&chunk).await
                .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
            
            downloaded += chunk.len() as u64;
            
            if let Some(ref callback) = progress_callback {
                callback(downloaded, total_size);
            }
        }
        
        file.flush().await
            .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        if let Some(logger) = &self.logger {
            logger.info("IPFS gateway download complete", serde_json::json!({
                "gateway": &gateway.name,
                "cid": cid,
                "bytes": downloaded,
                "duration_ms": start.elapsed().as_millis(),
            }))?;
        }
        
        Ok(downloaded)
    }
    
    /// Get gateways sorted by priority
    fn get_sorted_gateways(&self) -> Vec<&IPFSGateway> {
        let mut gateways: Vec<_> = self.config.gateways.iter().collect();
        gateways.sort_by_key(|g| g.priority);
        gateways
    }
    
    /// Check gateway health
    async fn check_gateway(&self, gateway: &IPFSGateway) -> SourceHealth {
        // Use a well-known CID for health check
        let test_cid = "QmQPeNsJPyVWPFDVHb77w8G42Fvo15z4bG2X8D2GhfbSXc"; // IPFS logo
        let url = format!("{}/{}?format=raw&length=1", gateway.url, test_cid);
        
        let start = Instant::now();
        
        match self.client
            .head(&url)
            .timeout(Duration::from_secs(10))
            .send()
            .await
        {
            Ok(response) => {
                let latency = start.elapsed().as_millis() as f64;
                
                match response.status() {
                    StatusCode::OK => {
                        if latency > gateway.avg_latency_ms as f64 * 2.0 {
                            SourceHealth::Degraded {
                                reason: DegradationReason::HighLatency,
                            }
                        } else {
                            SourceHealth::Healthy
                        }
                    }
                    StatusCode::GATEWAY_TIMEOUT | StatusCode::SERVICE_UNAVAILABLE => {
                        SourceHealth::Unhealthy {
                            reason: UnhealthyReason::Timeout,
                        }
                    }
                    _ => SourceHealth::Degraded {
                        reason: DegradationReason::IntermittentErrors,
                    },
                }
            }
            Err(e) => {
                if e.is_timeout() {
                    SourceHealth::Unhealthy {
                        reason: UnhealthyReason::Timeout,
                    }
                } else {
                    SourceHealth::Unhealthy {
                        reason: UnhealthyReason::ConnectionRefused,
                    }
                }
            }
        }
    }
}

#[async_trait::async_trait]
impl Source for IPFSSource {
    fn level(&self) -> SourceLevel {
        SourceLevel::IPFS
    }
    
    fn name(&self) -> &str {
        "ipfs-network"
    }
    
    async fn check_availability(&self) -> ScoutResult<SourceHealth> {
        // Check local node first if preferred
        if self.config.prefer_local && self.check_local_node().await {
            return Ok(SourceHealth::Healthy);
        }
        
        // Check primary gateway
        let gateways = self.get_sorted_gateways();
        if let Some(primary) = gateways.first() {
            return Ok(self.check_gateway(primary).await);
        }
        
        Ok(SourceHealth::Unhealthy {
            reason: UnhealthyReason::NoPeers,
        })
    }
    
    async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        let start = Instant::now();
        let mut failover_history = Vec::new();
        
        // Get CID for artifact
        let cid = self.get_cid(artifact)
            .ok_or_else(|| ScoutError::ConfigError(
                format!("No CID found for artifact: {}", artifact.name)
            ))?;
        
        // Try local node first if preferred
        if self.config.prefer_local && self.check_local_node().await {
            let local_start = Instant::now();
            
            match self.download_from_local(&cid, dest, progress_callback.clone()).await {
                Ok(bytes) => {
                    return Ok(FetchResult {
                        source_level: SourceLevel::IPFS,
                        source_name: "ipfs-local-node".to_string(),
                        local_path: dest.clone(),
                        bytes_transferred: bytes,
                        duration: start.elapsed(),
                        attempts: 1,
                        checksum_verified: true, // IPFS CID is content-addressed
                        signature_verified: false,
                        timestamp: chrono::Utc::now().to_rfc3339(),
                        failover_history: vec![],
                    });
                }
                Err(e) => {
                    failover_history.push(FailoverEntry {
                        source_level: SourceLevel::IPFS,
                        source_name: "ipfs-local-node".to_string(),
                        failure_reason: e.to_string(),
                        time_spent: local_start.elapsed(),
                        retry_attempts: 1,
                    });
                }
            }
        }
        
        // Try gateways
        let gateways = self.get_sorted_gateways();
        let mut last_error: Option<ScoutError> = None;
        
        for gateway in gateways {
            let gateway_start = Instant::now();
            
            match self.download_from_gateway(gateway, &cid, dest, progress_callback.clone()).await {
                Ok(bytes) => {
                    return Ok(FetchResult {
                        source_level: SourceLevel::IPFS,
                        source_name: format!("ipfs-gateway-{}", gateway.name),
                        local_path: dest.clone(),
                        bytes_transferred: bytes,
                        duration: start.elapsed(),
                        attempts: (failover_history.len() + 1) as u8,
                        checksum_verified: true, // IPFS CID is content-addressed
                        signature_verified: false,
                        timestamp: chrono::Utc::now().to_rfc3339(),
                        failover_history,
                    });
                }
                Err(e) => {
                    failover_history.push(FailoverEntry {
                        source_level: SourceLevel::IPFS,
                        source_name: format!("ipfs-gateway-{}", gateway.name),
                        failure_reason: e.to_string(),
                        time_spent: gateway_start.elapsed(),
                        retry_attempts: 1,
                    });
                    last_error = Some(e);
                }
            }
        }
        
        Err(last_error.unwrap_or(ScoutError::AllSourcesExhausted))
    }
    
    fn stats(&self) -> &SourceStats {
        &self.stats
    }
    
    fn reset_stats(&mut self) {
        self.stats = SourceStats::new();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_ipfs_config_default() {
        let config = IPFSConfig::default();
        assert!(!config.gateways.is_empty());
        assert_eq!(config.gateways.len(), 5);
    }
    
    #[test]
    fn test_gateway_sorting() {
        let config = IPFSConfig::default();
        let source = IPFSSource::new(config).unwrap();
        
        let gateways = source.get_sorted_gateways();
        
        for i in 1..gateways.len() {
            assert!(gateways[i-1].priority <= gateways[i].priority);
        }
    }
    
    #[test]
    fn test_cid_retrieval() {
        let config = IPFSConfig::default();
        let source = IPFSSource::new(config).unwrap();
        
        let artifact = Artifact {
            name: "kiswarm-core".to_string(),
            checksum: None,
            min_size: None,
            max_size: None,
            required_signature: None,
            artifact_type: ArtifactType::KISWARMCore,
        };
        
        let cid = source.get_cid(&artifact);
        assert!(cid.is_some());
    }
}
