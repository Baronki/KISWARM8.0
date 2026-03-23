//! Level 1: GitHub Source Implementation
//!
//! Primary source using GitHub API and raw content URLs.
//! Features:
//! - Rate limit awareness and handling
//! - API authentication support
//! - Mirror fallback within GitHub
//! - Release and commit-based downloads

use super::types::*;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use reqwest::{Client, Response, StatusCode};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;

/// GitHub source configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubConfig {
    /// Repository URL (e.g., "https://github.com/Baronki/KISWARM6.0")
    pub repository_url: String,
    
    /// GitHub API token (optional, increases rate limit)
    pub api_token: Option<String>,
    
    /// Branch to use
    pub branch: String,
    
    /// Use GitHub API for metadata
    pub use_api: bool,
    
    /// GitHub mirrors (e.g., github.com, github.us)
    pub mirrors: Vec<String>,
    
    /// Rate limit threshold (requests remaining)
    pub rate_limit_threshold: u32,
    
    /// User agent for requests
    pub user_agent: String,
}

impl Default for GitHubConfig {
    fn default() -> Self {
        Self {
            repository_url: "https://github.com/Baronki/KISWARM6.0".to_string(),
            api_token: None,
            branch: "main".to_string(),
            use_api: true,
            mirrors: vec![
                "github.com".to_string(),
            ],
            rate_limit_threshold: 100,
            user_agent: "KISWARM-ZeroTouchScout/6.3.5".to_string(),
        }
    }
}

/// GitHub API rate limit info
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateLimitInfo {
    /// Total requests allowed per hour
    pub limit: u32,
    
    /// Requests remaining
    pub remaining: u32,
    
    /// Reset timestamp
    pub reset_at: String,
    
    /// Whether rate limited
    pub is_limited: bool,
}

/// GitHub Source implementation
pub struct GitHubSource {
    /// Configuration
    config: GitHubConfig,
    
    /// HTTP client
    client: Client,
    
    /// Source statistics
    stats: SourceStats,
    
    /// Current rate limit info
    rate_limit: Option<RateLimitInfo>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl GitHubSource {
    /// Create a new GitHub source
    pub fn new(config: GitHubConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(120))
            .user_agent(&config.user_agent)
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            stats: SourceStats::new(),
            rate_limit: None,
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Build URL for artifact
    fn build_url(&self, artifact: &Artifact) -> String {
        let repo = &self.config.repository_url;
        let branch = &self.config.branch;
        
        match artifact.artifact_type {
            ArtifactType::FullArchive => {
                format!("{}/archive/refs/heads/{}.tar.gz", repo, branch)
            }
            ArtifactType::KISWARMCore => {
                format!("{}/raw/{}/backend/python/kiswarm_core.tar.gz", repo, branch)
            }
            ArtifactType::ConfigFile => {
                format!("{}/raw/{}/config/{}.json", repo, branch, artifact.name)
            }
            ArtifactType::ArkManifest => {
                format!("{}/raw/{}/ark/manifest.json", repo, branch)
            }
            _ => {
                // Generic download URL
                format!("{}/raw/{}/downloads/{}", repo, branch, artifact.name)
            }
        }
    }
    
    /// Check GitHub API rate limit
    pub async fn check_rate_limit(&mut self) -> ScoutResult<RateLimitInfo> {
        let url = "https://api.github.com/rate_limit";
        
        let mut request = self.client.get(url);
        
        if let Some(ref token) = self.config.api_token {
            request = request.bearer_auth(token);
        }
        
        let response = request
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Rate limit check failed: {}", e)))?;
        
        if response.status() == StatusCode::OK {
            let body: serde_json::Value = response.json().await
                .map_err(|e| ScoutError::NetworkError(format!("Failed to parse rate limit: {}", e)))?;
            
            let rate = &body["resources"]["core"];
            let info = RateLimitInfo {
                limit: rate["limit"].as_u64().unwrap_or(60) as u32,
                remaining: rate["remaining"].as_u64().unwrap_or(0) as u32,
                reset_at: rate["reset"].as_u64()
                    .map(|t| chrono::DateTime::from_timestamp(t as i64, 0)
                        .map(|dt| dt.to_rfc3339())
                        .unwrap_or_default())
                    .unwrap_or_default(),
                is_limited: rate["remaining"].as_u64().unwrap_or(0) == 0,
            };
            
            self.rate_limit = Some(info.clone());
            return Ok(info);
        }
        
        Ok(RateLimitInfo {
            limit: 60,
            remaining: 0,
            reset_at: String::new(),
            is_limited: true,
        })
    }
    
    /// Download file from URL
    async fn download_file(
        &self,
        url: &str,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<u64> {
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting GitHub download", serde_json::json!({
                "url": url,
                "dest": dest.to_string_lossy(),
            }))?;
        }
        
        let mut request = self.client.get(url);
        
        if let Some(ref token) = self.config.api_token {
            request = request.bearer_auth(token);
        }
        
        let response = request
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: url.to_string(),
                reason: e.to_string(),
            })?;
        
        let status = response.status();
        
        // Handle rate limiting
        if status == StatusCode::FORBIDDEN {
            let remaining = response.headers()
                .get("x-ratelimit-remaining")
                .and_then(|v| v.to_str().ok())
                .and_then(|v| v.parse::<u32>().ok())
                .unwrap_or(0);
            
            if remaining == 0 {
                let reset_time = response.headers()
                    .get("x-ratelimit-reset")
                    .and_then(|v| v.to_str().ok())
                    .and_then(|v| v.parse::<i64>().ok())
                    .unwrap_or(0);
                
                return Err(ScoutError::NetworkError(format!(
                    "GitHub rate limited. Resets at {}",
                    chrono::DateTime::from_timestamp(reset_time, 0)
                        .map(|dt| dt.to_rfc3339())
                        .unwrap_or_default()
                )));
            }
        }
        
        if !status.is_success() {
            return Err(ScoutError::DownloadFailed {
                source: url.to_string(),
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
                    source: url.to_string(),
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
            logger.info("GitHub download complete", serde_json::json!({
                "bytes": downloaded,
                "duration_ms": start.elapsed().as_millis(),
            }))?;
        }
        
        Ok(downloaded)
    }
    
    /// Verify file checksum
    async fn verify_checksum(&self, path: &PathBuf, expected: &str) -> ScoutResult<bool> {
        use sha2::{Digest, Sha256};
        
        let content = tokio::fs::read(path).await
            .map_err(|_| ScoutError::FileReadFailed { path: path.clone() })?;
        
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let actual = format!("{:x}", hasher.finalize());
        
        Ok(actual == expected)
    }
}

#[async_trait::async_trait]
impl Source for GitHubSource {
    fn level(&self) -> SourceLevel {
        SourceLevel::GitHub
    }
    
    fn name(&self) -> &str {
        "github-primary"
    }
    
    async fn check_availability(&self) -> ScoutResult<SourceHealth> {
        // Check rate limit first
        let url = "https://api.github.com/zen";
        
        let mut request = self.client.get(url);
        
        if let Some(ref token) = self.config.api_token {
            request = request.bearer_auth(token);
        }
        
        let start = Instant::now();
        let response = request
            .timeout(Duration::from_secs(10))
            .send()
            .await;
        
        match response {
            Ok(resp) => {
                let latency = start.elapsed().as_millis() as f64;
                
                match resp.status() {
                    StatusCode::OK => {
                        // Check rate limit header
                        let remaining = resp.headers()
                            .get("x-ratelimit-remaining")
                            .and_then(|v| v.to_str().ok())
                            .and_then(|v| v.parse::<u32>().ok())
                            .unwrap_or(60);
                        
                        if remaining < self.config.rate_limit_threshold {
                            Ok(SourceHealth::Degraded {
                                reason: DegradationReason::RateLimitApproaching,
                            })
                        } else if latency > 2000.0 {
                            Ok(SourceHealth::Degraded {
                                reason: DegradationReason::HighLatency,
                            })
                        } else {
                            Ok(SourceHealth::Healthy)
                        }
                    }
                    StatusCode::FORBIDDEN => {
                        Ok(SourceHealth::Unhealthy {
                            reason: UnhealthyReason::RateLimited,
                        })
                    }
                    status => {
                        Ok(SourceHealth::Unhealthy {
                            reason: UnhealthyReason::HTTPError { code: status.as_u16() },
                        })
                    }
                }
            }
            Err(e) => {
                if e.is_timeout() {
                    Ok(SourceHealth::Unhealthy {
                        reason: UnhealthyReason::Timeout,
                    })
                } else if e.is_connect() {
                    Ok(SourceHealth::Unhealthy {
                        reason: UnhealthyReason::ConnectionRefused,
                    })
                } else {
                    Ok(SourceHealth::Unhealthy {
                        reason: UnhealthyReason::Unknown,
                    })
                }
            }
        }
    }
    
    async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        let start = Instant::now();
        let url = self.build_url(artifact);
        
        // Download
        let bytes = self.download_file(&url, dest, progress_callback).await?;
        
        // Verify checksum if provided
        let checksum_verified = if let Some(ref expected) = artifact.checksum {
            self.verify_checksum(dest, expected).await?
        } else {
            false
        };
        
        Ok(FetchResult {
            source_level: SourceLevel::GitHub,
            source_name: self.name().to_string(),
            local_path: dest.clone(),
            bytes_transferred: bytes,
            duration: start.elapsed(),
            attempts: 1,
            checksum_verified,
            signature_verified: false,
            timestamp: chrono::Utc::now().to_rfc3339(),
            failover_history: vec![],
        })
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
    fn test_github_config_default() {
        let config = GitHubConfig::default();
        assert!(config.repository_url.contains("KISWARM"));
        assert_eq!(config.branch, "main");
    }
    
    #[test]
    fn test_url_building() {
        let config = GitHubConfig::default();
        let source = GitHubSource::new(config).unwrap();
        
        let artifact = Artifact {
            name: "test".to_string(),
            checksum: None,
            min_size: None,
            max_size: None,
            required_signature: None,
            artifact_type: ArtifactType::FullArchive,
        };
        
        let url = source.build_url(&artifact);
        assert!(url.contains("archive"));
        assert!(url.ends_with(".tar.gz"));
    }
}
