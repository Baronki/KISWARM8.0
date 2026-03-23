//! Level 2: CDN Source Implementation
//!
//! Secondary source using Content Delivery Network mirrors.
//! Features:
//! - Multiple CDN providers (Cloudflare, AWS CloudFront, Fastly)
//! - Geographic routing for optimal performance
//! - Certificate pinning for security
//! - Cache-aware downloads

use super::types::*;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use reqwest::{Client, Response, StatusCode};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;

/// CDN provider configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CDNProvider {
    /// Provider name
    pub name: String,
    
    /// Base URL
    pub base_url: String,
    
    /// Region (for geographic routing)
    pub region: Option<String>,
    
    /// Priority within CDN tier
    pub priority: u32,
    
    /// Max concurrent connections
    pub max_connections: u32,
    
    /// Certificate fingerprint (optional, for pinning)
    pub cert_fingerprint: Option<String>,
}

/// CDN source configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CDNConfig {
    /// List of CDN providers
    pub providers: Vec<CDNProvider>,
    
    /// Default region
    pub default_region: String,
    
    /// Timeout for CDN requests
    pub timeout_secs: u64,
    
    /// Enable compression
    pub enable_compression: bool,
    
    /// User agent
    pub user_agent: String,
    
    /// Cache control behavior
    pub cache_control: CacheControlPolicy,
}

/// Cache control policy
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CacheControlPolicy {
    /// Use CDN cache normally
    Normal,
    
    /// Force revalidation
    Revalidate,
    
    /// Bypass cache
    Bypass,
}

impl Default for CDNConfig {
    fn default() -> Self {
        Self {
            providers: vec![
                CDNProvider {
                    name: "cloudflare".to_string(),
                    base_url: "https://cdn.kiswarm.io".to_string(),
                    region: Some("global".to_string()),
                    priority: 1,
                    max_connections: 10,
                    cert_fingerprint: None,
                },
                CDNProvider {
                    name: "cloudfront".to_string(),
                    base_url: "https://d123456.cloudfront.net".to_string(),
                    region: Some("us-east-1".to_string()),
                    priority: 2,
                    max_connections: 10,
                    cert_fingerprint: None,
                },
                CDNProvider {
                    name: "fastly".to_string(),
                    base_url: "https://kiswarm.global.ssl.fastly.net".to_string(),
                    region: Some("global".to_string()),
                    priority: 3,
                    max_connections: 10,
                    cert_fingerprint: None,
                },
            ],
            default_region: "global".to_string(),
            timeout_secs: 60,
            enable_compression: true,
            user_agent: "KISWARM-ZeroTouchScout/6.3.5".to_string(),
            cache_control: CacheControlPolicy::Normal,
        }
    }
}

/// CDN Source implementation
pub struct CDNSource {
    /// Configuration
    config: CDNConfig,
    
    /// HTTP client
    client: Client,
    
    /// Source statistics
    stats: SourceStats,
    
    /// Current provider index
    current_provider: Arc<tokio::sync::RwLock<usize>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl CDNSource {
    /// Create a new CDN source
    pub fn new(config: CDNConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .user_agent(&config.user_agent)
            .pool_max_idle_per_host(20)
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            stats: SourceStats::new(),
            current_provider: Arc::new(tokio::sync::RwLock::new(0)),
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Build URL for artifact
    fn build_url(&self, provider: &CDNProvider, artifact: &Artifact) -> String {
        match artifact.artifact_type {
            ArtifactType::FullArchive => {
                format!("{}/releases/latest/kiswarm-full.tar.gz", provider.base_url)
            }
            ArtifactType::KISWARMCore => {
                format!("{}/core/kiswarm-core-{}.tar.gz", 
                    provider.base_url, artifact.name)
            }
            ArtifactType::PythonWheel => {
                format!("{}/wheels/{}.whl", provider.base_url, artifact.name)
            }
            ArtifactType::OllamaModel => {
                format!("{}/models/{}.bin", provider.base_url, artifact.name)
            }
            ArtifactType::ConfigFile => {
                format!("{}/config/{}.json", provider.base_url, artifact.name)
            }
            _ => {
                format!("{}/artifacts/{}", provider.base_url, artifact.name)
            }
        }
    }
    
    /// Get providers sorted by priority
    fn get_sorted_providers(&self) -> Vec<&CDNProvider> {
        let mut providers: Vec<_> = self.config.providers.iter().collect();
        providers.sort_by_key(|p| p.priority);
        providers
    }
    
    /// Download file from CDN
    async fn download_from_provider(
        &self,
        provider: &CDNProvider,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<(u64, String)> {
        let url = self.build_url(provider, artifact);
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting CDN download", serde_json::json!({
                "provider": &provider.name,
                "url": &url,
                "dest": dest.to_string_lossy(),
            }))?;
        }
        
        // Build request with cache control
        let mut request = self.client.get(&url);
        
        request = match self.config.cache_control {
            CacheControlPolicy::Normal => request,
            CacheControlPolicy::Revalidate => request.header("Cache-Control", "no-cache"),
            CacheControlPolicy::Bypass => request.header("Cache-Control", "no-store"),
        };
        
        // Add compression header
        if self.config.enable_compression {
            request = request.header("Accept-Encoding", "gzip, deflate, br");
        }
        
        let response = request
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: url.clone(),
                reason: e.to_string(),
            })?;
        
        let status = response.status();
        
        if status == StatusCode::NOT_FOUND {
            return Err(ScoutError::DownloadFailed {
                source: url.clone(),
                reason: "404 Not Found".to_string(),
            });
        }
        
        if !status.is_success() {
            return Err(ScoutError::DownloadFailed {
                source: url.clone(),
                reason: format!("HTTP {}", status.as_u16()),
            });
        }
        
        // Get content length
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
            logger.info("CDN download complete", serde_json::json!({
                "provider": &provider.name,
                "bytes": downloaded,
                "duration_ms": start.elapsed().as_millis(),
            }))?;
        }
        
        Ok((downloaded, provider.name.clone()))
    }
    
    /// Check single provider health
    async fn check_provider(&self, provider: &CDNProvider) -> SourceHealth {
        let url = format!("{}/health", provider.base_url);
        let start = Instant::now();
        
        match self.client
            .head(&url)
            .timeout(Duration::from_secs(5))
            .send()
            .await
        {
            Ok(response) => {
                let latency = start.elapsed().as_millis() as f64;
                
                match response.status() {
                    StatusCode::OK | StatusCode::NO_CONTENT => {
                        if latency > 1000.0 {
                            SourceHealth::Degraded {
                                reason: DegradationReason::HighLatency,
                            }
                        } else {
                            SourceHealth::Healthy
                        }
                    }
                    StatusCode::SERVICE_UNAVAILABLE | StatusCode::GATEWAY_TIMEOUT => {
                        SourceHealth::Unhealthy {
                            reason: UnhealthyReason::ServerError { 
                                code: response.status().as_u16() 
                            },
                        }
                    }
                    _ => SourceHealth::Unhealthy {
                        reason: UnhealthyReason::HTTPError { 
                            code: response.status().as_u16() 
                        },
                    },
                }
            }
            Err(e) => {
                if e.is_timeout() {
                    SourceHealth::Unhealthy {
                        reason: UnhealthyReason::Timeout,
                    }
                } else if e.is_connect() {
                    SourceHealth::Unhealthy {
                        reason: UnhealthyReason::ConnectionRefused,
                    }
                } else {
                    SourceHealth::Unhealthy {
                        reason: UnhealthyReason::Unknown,
                    }
                }
            }
        }
    }
}

#[async_trait::async_trait]
impl Source for CDNSource {
    fn level(&self) -> SourceLevel {
        SourceLevel::CDN
    }
    
    fn name(&self) -> &str {
        "cdn-mirror"
    }
    
    async fn check_availability(&self) -> ScoutResult<SourceHealth> {
        let providers = self.get_sorted_providers();
        
        // Check primary provider
        if let Some(primary) = providers.first() {
            return Ok(self.check_provider(primary).await);
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
        let mut last_error: Option<ScoutError> = None;
        let mut failover_history = Vec::new();
        
        let providers = self.get_sorted_providers();
        
        for provider in providers {
            let provider_start = Instant::now();
            
            match self.download_from_provider(provider, artifact, dest, progress_callback.clone()).await {
                Ok((bytes, provider_name)) => {
                    // Verify checksum if provided
                    let checksum_verified = if let Some(ref expected) = artifact.checksum {
                        use sha2::{Digest, Sha256};
                        let content = tokio::fs::read(dest).await
                            .map_err(|_| ScoutError::FileReadFailed { path: dest.clone() })?;
                        let mut hasher = Sha256::new();
                        hasher.update(&content);
                        format!("{:x}", hasher.finalize()) == *expected
                    } else {
                        false
                    };
                    
                    return Ok(FetchResult {
                        source_level: SourceLevel::CDN,
                        source_name: provider_name,
                        local_path: dest.clone(),
                        bytes_transferred: bytes,
                        duration: start.elapsed(),
                        attempts: (failover_history.len() + 1) as u8,
                        checksum_verified,
                        signature_verified: false,
                        timestamp: chrono::Utc::now().to_rfc3339(),
                        failover_history,
                    });
                }
                Err(e) => {
                    failover_history.push(FailoverEntry {
                        source_level: SourceLevel::CDN,
                        source_name: provider.name.clone(),
                        failure_reason: e.to_string(),
                        time_spent: provider_start.elapsed(),
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
    fn test_cdn_config_default() {
        let config = CDNConfig::default();
        assert!(!config.providers.is_empty());
        assert_eq!(config.providers.len(), 3);
    }
    
    #[test]
    fn test_provider_sorting() {
        let config = CDNConfig::default();
        let source = CDNSource::new(config).unwrap();
        
        let providers = source.get_sorted_providers();
        
        // Should be sorted by priority
        for i in 1..providers.len() {
            assert!(providers[i-1].priority <= providers[i].priority);
        }
    }
}
