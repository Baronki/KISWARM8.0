//! Failover Coordinator for Source Failover System
//!
//! This module implements the central coordinator that manages all 5 source
//! levels and orchestrates intelligent failover with health monitoring.

use super::types::*;
use super::{GitHubSource, CDNSource, IPFSSource, PeerMeshSource, PhysicalArkSource};
use crate::config::ScoutConfig;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Failover mode
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FailoverMode {
    /// Try sources in order, fail over on error
    Sequential,
    
    /// Try multiple sources in parallel, use first success
    ParallelRace,
    
    /// Try sources in parallel, use best result
    ParallelBest,
    
    /// Emergency mode - try all sources simultaneously
    EmergencyBroadcast,
}

/// Coordinator configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoordinatorConfig {
    /// Failover mode
    pub mode: FailoverMode,
    
    /// Maximum total attempts across all sources
    pub max_total_attempts: u8,
    
    /// Maximum time to spend on all sources
    pub max_total_time_secs: u64,
    
    /// Health check interval
    pub health_check_interval_secs: u64,
    
    /// Enable health caching
    pub cache_health_checks: bool,
    
    /// Health cache TTL
    pub health_cache_ttl_secs: u64,
    
    /// Enable failover logging
    pub enable_logging: bool,
    
    /// Skip sources that are known unhealthy
    pub skip_unhealthy: bool,
    
    /// Time to wait between source switches
    pub source_switch_delay_ms: u64,
}

impl Default for CoordinatorConfig {
    fn default() -> Self {
        Self {
            mode: FailoverMode::Sequential,
            max_total_attempts: 15,
            max_total_time_secs: 600,
            health_check_interval_secs: 60,
            cache_health_checks: true,
            health_cache_ttl_secs: 30,
            enable_logging: true,
            skip_unhealthy: true,
            source_switch_delay_ms: 100,
        }
    }
}

/// Health check cache entry
#[derive(Debug, Clone)]
struct HealthCacheEntry {
    health: SourceHealth,
    timestamp: Instant,
}

/// Failover Coordinator
pub struct FailoverCoordinator {
    /// Configuration
    config: CoordinatorConfig,
    
    /// Scout configuration
    scout_config: ScoutConfig,
    
    /// GitHub source (Level 1)
    github_source: Option<GitHubSource>,
    
    /// CDN source (Level 2)
    cdn_source: Option<CDNSource>,
    
    /// IPFS source (Level 3)
    ipfs_source: Option<IPFSSource>,
    
    /// Peer mesh source (Level 4)
    peer_mesh_source: Option<PeerMeshSource>,
    
    /// Physical ark source (Level 5)
    physical_ark_source: Option<PhysicalArkSource>,
    
    /// Health check cache
    health_cache: Arc<tokio::sync::RwLock<std::collections::HashMap<SourceLevel, HealthCacheEntry>>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl FailoverCoordinator {
    /// Create a new failover coordinator
    pub fn new(config: CoordinatorConfig, scout_config: ScoutConfig) -> ScoutResult<Self> {
        Ok(Self {
            config,
            scout_config,
            github_source: None,
            cdn_source: None,
            ipfs_source: None,
            peer_mesh_source: None,
            physical_ark_source: None,
            health_cache: Arc::new(tokio::sync::RwLock::new(std::collections::HashMap::new())),
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Initialize all sources
    pub fn initialize_sources(&mut self) -> ScoutResult<()> {
        // Initialize GitHub source
        let github_config = super::github::GitHubConfig::default();
        let mut github = GitHubSource::new(github_config)?;
        if let Some(ref logger) = self.logger {
            github = github.with_logger(logger.clone());
        }
        self.github_source = Some(github);
        
        // Initialize CDN source
        let cdn_config = super::cdn::CDNConfig::default();
        let mut cdn = CDNSource::new(cdn_config)?;
        if let Some(ref logger) = self.logger {
            cdn = cdn.with_logger(logger.clone());
        }
        self.cdn_source = Some(cdn);
        
        // Initialize IPFS source
        let ipfs_config = super::ipfs::IPFSConfig::default();
        let mut ipfs = IPFSSource::new(ipfs_config)?;
        if let Some(ref logger) = self.logger {
            ipfs = ipfs.with_logger(logger.clone());
        }
        self.ipfs_source = Some(ipfs);
        
        // Initialize Peer Mesh source
        let mesh_config = super::peer_mesh::PeerMeshConfig::default();
        let mut mesh = PeerMeshSource::new(mesh_config)?;
        if let Some(ref logger) = self.logger {
            mesh = mesh.with_logger(logger.clone());
        }
        self.peer_mesh_source = Some(mesh);
        
        // Initialize Physical Ark source
        let ark_config = super::physical_ark::PhysicalArkConfig::default();
        let mut ark = PhysicalArkSource::new(ark_config)?;
        if let Some(ref logger) = self.logger {
            ark = ark.with_logger(logger.clone());
        }
        self.physical_ark_source = Some(ark);
        
        Ok(())
    }
    
    /// Get cached health or check source
    async fn get_source_health(&self, level: SourceLevel) -> ScoutResult<SourceHealth> {
        // Check cache first
        if self.config.cache_health_checks {
            let cache = self.health_cache.read().await;
            if let Some(entry) = cache.get(&level) {
                if entry.timestamp.elapsed().as_secs() < self.config.health_cache_ttl_secs {
                    return Ok(entry.health);
                }
            }
        }
        
        // Check actual health
        let health = match level {
            SourceLevel::GitHub => {
                if let Some(ref source) = self.github_source {
                    source.check_availability().await?
                } else {
                    SourceHealth::Unhealthy { reason: UnhealthyReason::Unknown }
                }
            }
            SourceLevel::CDN => {
                if let Some(ref source) = self.cdn_source {
                    source.check_availability().await?
                } else {
                    SourceHealth::Unhealthy { reason: UnhealthyReason::Unknown }
                }
            }
            SourceLevel::IPFS => {
                if let Some(ref source) = self.ipfs_source {
                    source.check_availability().await?
                } else {
                    SourceHealth::Unhealthy { reason: UnhealthyReason::Unknown }
                }
            }
            SourceLevel::PeerMesh => {
                if let Some(ref source) = self.peer_mesh_source {
                    source.check_availability().await?
                } else {
                    SourceHealth::Unhealthy { reason: UnhealthyReason::Unknown }
                }
            }
            SourceLevel::PhysicalArk => {
                if let Some(ref source) = self.physical_ark_source {
                    source.check_availability().await?
                } else {
                    SourceHealth::Unhealthy { reason: UnhealthyReason::Unknown }
                }
            }
        };
        
        // Update cache
        if self.config.cache_health_checks {
            let mut cache = self.health_cache.write().await;
            cache.insert(level, HealthCacheEntry {
                health,
                timestamp: Instant::now(),
            });
        }
        
        Ok(health)
    }
    
    /// Fetch artifact with sequential failover
    async fn fetch_sequential(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        let start = Instant::now();
        let mut failover_history = Vec::new();
        let mut total_attempts = 0;
        
        for level in SourceLevel::iter_priority() {
            // Check time limit
            if start.elapsed().as_secs() >= self.config.max_total_time_secs {
                return Err(ScoutError::NetworkError("Total time limit exceeded".to_string()));
            }
            
            // Check attempt limit
            if total_attempts >= self.config.max_total_attempts {
                return Err(ScoutError::NetworkError("Maximum attempts exceeded".to_string()));
            }
            
            // Check health if skipping unhealthy
            if self.config.skip_unhealthy {
                let health = self.get_source_health(level).await?;
                if !health.is_usable() {
                    failover_history.push(FailoverEntry {
                        source_level: level,
                        source_name: format!("{:?}-skipped", level),
                        failure_reason: format!("Source unhealthy: {:?}", health),
                        time_spent: Duration::from_millis(0),
                        retry_attempts: 0,
                    });
                    continue;
                }
            }
            
            // Try to fetch from this source
            let source_start = Instant::now();
            let result = self.fetch_from_source(level, artifact, dest, progress_callback.clone()).await;
            
            total_attempts += 1;
            
            match result {
                Ok(fetch_result) => {
                    // Success!
                    if let Some(logger) = &self.logger {
                        logger.info("Artifact fetch successful", serde_json::json!({
                            "source_level": format!("{:?}", fetch_result.source_level),
                            "source_name": &fetch_result.source_name,
                            "bytes": fetch_result.bytes_transferred,
                            "duration_ms": fetch_result.duration.as_millis(),
                            "failover_count": failover_history.len(),
                        }))?;
                    }
                    
                    let mut result = fetch_result;
                    result.failover_history = failover_history;
                    return Ok(result);
                }
                Err(e) => {
                    failover_history.push(FailoverEntry {
                        source_level: level,
                        source_name: format!("{:?}", level),
                        failure_reason: e.to_string(),
                        time_spent: source_start.elapsed(),
                        retry_attempts: 1,
                    });
                    
                    if let Some(logger) = &self.logger {
                        logger.warn("Source fetch failed, failing over", serde_json::json!({
                            "source_level": format!("{:?}", level),
                            "error": e.to_string(),
                        }))?;
                    }
                    
                    // Delay before next source
                    if self.config.source_switch_delay_ms > 0 {
                        tokio::time::sleep(Duration::from_millis(self.config.source_switch_delay_ms)).await;
                    }
                }
            }
        }
        
        // All sources failed
        if let Some(logger) = &self.logger {
            logger.error("All sources exhausted", "E203", serde_json::json!({
                "attempts": total_attempts,
                "failover_history": failover_history.iter().map(|e| &e.source_level).collect::<Vec<_>>(),
            }))?;
        }
        
        Err(ScoutError::AllSourcesExhausted)
    }
    
    /// Fetch from a specific source
    async fn fetch_from_source(
        &self,
        level: SourceLevel,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        match level {
            SourceLevel::GitHub => {
                if let Some(ref source) = self.github_source {
                    source.fetch(artifact, dest, progress_callback).await
                } else {
                    Err(ScoutError::ConfigError("GitHub source not initialized".to_string()))
                }
            }
            SourceLevel::CDN => {
                if let Some(ref source) = self.cdn_source {
                    source.fetch(artifact, dest, progress_callback).await
                } else {
                    Err(ScoutError::ConfigError("CDN source not initialized".to_string()))
                }
            }
            SourceLevel::IPFS => {
                if let Some(ref source) = self.ipfs_source {
                    source.fetch(artifact, dest, progress_callback).await
                } else {
                    Err(ScoutError::ConfigError("IPFS source not initialized".to_string()))
                }
            }
            SourceLevel::PeerMesh => {
                if let Some(ref source) = self.peer_mesh_source {
                    source.fetch(artifact, dest, progress_callback).await
                } else {
                    Err(ScoutError::ConfigError("Peer Mesh source not initialized".to_string()))
                }
            }
            SourceLevel::PhysicalArk => {
                if let Some(ref source) = self.physical_ark_source {
                    source.fetch(artifact, dest, progress_callback).await
                } else {
                    Err(ScoutError::ConfigError("Physical Ark source not initialized".to_string()))
                }
            }
        }
    }
    
    /// Fetch artifact with failover
    pub async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        match self.config.mode {
            FailoverMode::Sequential => {
                self.fetch_sequential(artifact, dest, progress_callback).await
            }
            FailoverMode::ParallelRace => {
                // TODO: Implement parallel race mode
                self.fetch_sequential(artifact, dest, progress_callback).await
            }
            FailoverMode::ParallelBest => {
                // TODO: Implement parallel best mode
                self.fetch_sequential(artifact, dest, progress_callback).await
            }
            FailoverMode::EmergencyBroadcast => {
                // TODO: Implement emergency broadcast mode
                self.fetch_sequential(artifact, dest, progress_callback).await
            }
        }
    }
    
    /// Get overall system health
    pub async fn system_health(&self) -> std::collections::HashMap<SourceLevel, SourceHealth> {
        let mut health = std::collections::HashMap::new();
        
        for level in SourceLevel::iter_priority() {
            if let Ok(h) = self.get_source_health(level).await {
                health.insert(level, h);
            }
        }
        
        health
    }
    
    /// Get best available source
    pub async fn best_available_source(&self) -> Option<SourceLevel> {
        for level in SourceLevel::iter_priority() {
            if let Ok(health) = self.get_source_health(level).await {
                if health.is_usable() {
                    return Some(level);
                }
            }
        }
        None
    }
    
    /// Run health check on all sources
    pub async fn check_all_sources(&self) -> ScoutResult<SourceHealthReport> {
        let mut report = SourceHealthReport {
            timestamp: chrono::Utc::now().to_rfc3339(),
            sources: std::collections::HashMap::new(),
            best_source: None,
            all_unhealthy: true,
        };
        
        for level in SourceLevel::iter_priority() {
            let health = self.get_source_health(level).await?;
            if health.is_usable() {
                report.all_unhealthy = false;
                if report.best_source.is_none() {
                    report.best_source = Some(level);
                }
            }
            report.sources.insert(level, health);
        }
        
        Ok(report)
    }
}

/// Source health report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceHealthReport {
    /// Report timestamp
    pub timestamp: String,
    
    /// Health by source level
    pub sources: std::collections::HashMap<SourceLevel, SourceHealth>,
    
    /// Best available source
    pub best_source: Option<SourceLevel>,
    
    /// All sources unhealthy
    pub all_unhealthy: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_coordinator_config_default() {
        let config = CoordinatorConfig::default();
        assert_eq!(config.mode, FailoverMode::Sequential);
        assert_eq!(config.max_total_attempts, 15);
    }
    
    #[tokio::test]
    async fn test_coordinator_creation() {
        let config = CoordinatorConfig::default();
        let scout_config = ScoutConfig::default();
        
        let mut coordinator = FailoverCoordinator::new(config, scout_config).unwrap();
        coordinator.initialize_sources().unwrap();
        
        assert!(coordinator.github_source.is_some());
        assert!(coordinator.cdn_source.is_some());
        assert!(coordinator.ipfs_source.is_some());
        assert!(coordinator.peer_mesh_source.is_some());
        assert!(coordinator.physical_ark_source.is_some());
    }
    
    #[test]
    fn test_source_level_priority() {
        let levels: Vec<_> = SourceLevel::iter_priority().collect();
        
        assert_eq!(levels[0], SourceLevel::GitHub);
        assert_eq!(levels[1], SourceLevel::CDN);
        assert_eq!(levels[2], SourceLevel::IPFS);
        assert_eq!(levels[3], SourceLevel::PeerMesh);
        assert_eq!(levels[4], SourceLevel::PhysicalArk);
    }
}
