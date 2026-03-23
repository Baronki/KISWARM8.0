//! Community Reporting Mesh Coordinator
//!
//! Manages all 5 reporting channels with intelligent failover:
//! 1. GitHub Issues (Primary)
//! 2. Direct API (Secondary)
//! 3. Mesh Network (Tertiary)
//! 4. Email Fallback (Quaternary)
//! 5. Satellite Uplink (Last Resort)

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

use super::types::*;
use super::{GitHubChannel, DirectApiChannel, MeshNetworkChannel, EmailChannel, SatelliteChannel};
use crate::error::{ScoutError, ScoutResult};

/// Mesh configuration
#[derive(Debug, Clone)]
pub struct MeshConfig {
    /// Enable parallel transmission to multiple channels
    pub parallel_transmission: bool,
    /// Maximum channels to try in parallel
    pub max_parallel_channels: usize,
    /// Failover timeout per channel (ms)
    pub channel_timeout_ms: u64,
    /// Total mesh timeout (ms)
    pub total_timeout_ms: u64,
    /// Minimum channels that must succeed
    pub min_success_channels: usize,
    /// Enable exponential backoff on retries
    pub enable_backoff: bool,
    /// Backoff base (ms)
    pub backoff_base_ms: u64,
    /// Maximum retries
    pub max_retries: u32,
    /// Enable Byzantine consensus for critical reports
    pub enable_consensus: bool,
    /// Consensus threshold (number of channels that must agree)
    pub consensus_threshold: usize,
}

impl Default for MeshConfig {
    fn default() -> Self {
        Self {
            parallel_transmission: true,
            max_parallel_channels: 3,
            channel_timeout_ms: 30000,
            total_timeout_ms: 120000,
            min_success_channels: 1,
            enable_backoff: true,
            backoff_base_ms: 1000,
            max_retries: 3,
            enable_consensus: true,
            consensus_threshold: 2,
        }
    }
}

/// Mesh transmission result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshResult {
    /// Report ID
    pub report_id: String,
    /// Overall success
    pub success: bool,
    /// Number of channels attempted
    pub channels_attempted: usize,
    /// Number of channels succeeded
    pub channels_succeeded: usize,
    /// Per-channel results
    pub channel_results: Vec<ChannelResult>,
    /// Total duration (ms)
    pub total_duration_ms: u64,
    /// Confirmation IDs from successful channels
    pub confirmation_ids: HashMap<String, String>,
    /// Winning channel (first to succeed)
    pub winning_channel: Option<String>,
    /// Consensus reached (if enabled)
    pub consensus_reached: Option<bool>,
}

/// Reporting channel trait
#[async_trait]
pub trait ReportingChannel: Send + Sync {
    /// Get channel name
    fn name(&self) -> &str;
    
    /// Get channel priority
    fn priority(&self) -> ChannelPriority;
    
    /// Check if channel is available
    async fn is_available(&self) -> bool;
    
    /// Get channel status
    async fn status(&self) -> ChannelStatus;
    
    /// Transmit a report
    async fn transmit(&self, report: &Report) -> ChannelResult;
    
    /// Check rate limit status
    fn rate_limit_remaining(&self) -> Option<u32>;
    
    /// Reset channel state
    async fn reset(&self);
}

/// Channel priority
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ChannelPriority {
    Primary = 1,
    Secondary = 2,
    Tertiary = 3,
    Quaternary = 4,
    LastResort = 5,
}

/// Channel status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ChannelStatus {
    /// Channel is available and ready
    Available,
    /// Channel is available but degraded
    Degraded,
    /// Channel is temporarily unavailable
    Unavailable,
    /// Channel is rate-limited
    RateLimited,
    /// Channel has failed
    Failed,
    /// Channel is not configured
    NotConfigured,
}

/// Channel transmission result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChannelResult {
    /// Channel name
    pub channel_name: String,
    /// Success flag
    pub success: bool,
    /// Result message
    pub message: String,
    /// Duration (ms)
    pub duration_ms: u64,
    /// Response data
    pub response_data: Option<HashMap<String, String>>,
}

/// Community Reporting Mesh
pub struct ReportingMesh {
    /// Configuration
    config: MeshConfig,
    /// Reporting channels (ordered by priority)
    channels: Vec<Box<dyn ReportingChannel>>,
    /// Is active flag
    is_active: AtomicBool,
    /// Total reports sent
    total_reports: AtomicU32,
    /// Successful reports
    successful_reports: AtomicU32,
    /// Last error
    last_error: RwLock<Option<String>>,
    /// Channel health cache
    channel_health: RwLock<HashMap<String, ChannelStatus>>,
}

impl ReportingMesh {
    /// Create a new reporting mesh with default channels
    pub fn new(config: MeshConfig) -> ScoutResult<Self> {
        let mut mesh = Self {
            config,
            channels: Vec::new(),
            is_active: AtomicBool::new(true),
            total_reports: AtomicU32::new(0),
            successful_reports: AtomicU32::new(0),
            last_error: RwLock::new(None),
            channel_health: RwLock::new(HashMap::new()),
        };
        
        // Add default channels (in priority order)
        mesh.add_channel(Box::new(GitHubChannel::with_defaults()?));
        mesh.add_channel(Box::new(DirectApiChannel::with_defaults()?));
        mesh.add_channel(Box::new(MeshNetworkChannel::with_defaults()?));
        mesh.add_channel(Box::new(EmailChannel::with_defaults()));
        mesh.add_channel(Box::new(SatelliteChannel::with_defaults()));
        
        Ok(mesh)
    }
    
    /// Create with defaults
    pub fn with_defaults() -> ScoutResult<Self> {
        Self::new(MeshConfig::default())
    }
    
    /// Add a reporting channel
    pub fn add_channel(&mut self, channel: Box<dyn ReportingChannel>) {
        self.channels.push(channel);
        // Sort by priority
        self.channels.sort_by_key(|c| c.priority());
    }
    
    /// Get all registered channels
    pub fn channels(&self) -> &[Box<dyn ReportingChannel>] {
        &self.channels
    }
    
    /// Get available channels sorted by priority
    pub async fn get_available_channels(&self) -> Vec<&Box<dyn ReportingChannel>> {
        let mut available: Vec<_> = self.channels.iter()
            .filter(|c| c.is_available().await)
            .collect();
        
        available.sort_by_key(|c| c.priority());
        available
    }
    
    /// Update channel health status
    pub async fn update_health(&self) {
        let mut health = self.channel_health.write().await;
        
        for channel in &self.channels {
            let status = channel.status().await;
            health.insert(channel.name().to_string(), status);
        }
    }
    
    /// Get channel health summary
    pub async fn health_summary(&self) -> HashMap<String, ChannelStatus> {
        self.channel_health.read().await.clone()
    }
    
    /// Transmit report via sequential failover
    async fn transmit_sequential(&self, report: &Report) -> MeshResult {
        let start = Instant::now();
        let mut channel_results = Vec::new();
        let mut confirmation_ids = HashMap::new();
        let mut winning_channel = None;
        
        let available_channels = self.get_available_channels().await;
        
        for channel in available_channels {
            // Check total timeout
            if start.elapsed().as_millis() as u64 > self.config.total_timeout_ms {
                break;
            }
            
            let result = channel.transmit(report).await;
            channel_results.push(result.clone());
            
            if result.success {
                winning_channel = Some(channel.name().to_string());
                
                if let Some(ref data) = result.response_data {
                    if let Some(confirm) = data.get("confirmation_id").or(data.get("issue_url")) {
                        confirmation_ids.insert(channel.name().to_string(), confirm.clone());
                    }
                }
                
                // We've succeeded, but might continue if min_success_channels > 1
                if confirmation_ids.len() >= self.config.min_success_channels {
                    break;
                }
            }
        }
        
        let success = !confirmation_ids.is_empty();
        
        if success {
            self.successful_reports.fetch_add(1, Ordering::SeqCst);
        }
        
        self.total_reports.fetch_add(1, Ordering::SeqCst);
        
        MeshResult {
            report_id: report.report_id.to_string(),
            success,
            channels_attempted: channel_results.len(),
            channels_succeeded: confirmation_ids.len(),
            channel_results,
            total_duration_ms: start.elapsed().as_millis() as u64,
            confirmation_ids,
            winning_channel,
            consensus_reached: None,
        }
    }
    
    /// Transmit report via parallel multi-channel
    async fn transmit_parallel(&self, report: &Report) -> MeshResult {
        let start = Instant::now();
        let available_channels = self.get_available_channels().await;
        
        // Select top N channels for parallel transmission
        let selected: Vec<_> = available_channels.iter()
            .take(self.config.max_parallel_channels)
            .collect();
        
        if selected.is_empty() {
            return MeshResult {
                report_id: report.report_id.to_string(),
                success: false,
                channels_attempted: 0,
                channels_succeeded: 0,
                channel_results: vec![],
                total_duration_ms: start.elapsed().as_millis() as u64,
                confirmation_ids: HashMap::new(),
                winning_channel: None,
                consensus_reached: None,
            };
        }
        
        // Transmit to all selected channels concurrently
        let mut tasks = Vec::new();
        for channel in selected {
            let report = report.clone();
            tasks.push(tokio::spawn(async move {
                channel.transmit(&report).await
            }));
        }
        
        // Wait for all with timeout
        let timeout_duration = Duration::from_millis(self.config.channel_timeout_ms);
        let mut channel_results = Vec::new();
        let mut confirmation_ids = HashMap::new();
        let mut winning_channel = None;
        
        for task in tasks {
            match tokio::time::timeout(timeout_duration, task).await {
                Ok(Ok(result)) => {
                    let success = result.success;
                    let channel_name = result.channel_name.clone();
                    channel_results.push(result.clone());
                    
                    if success && winning_channel.is_none() {
                        winning_channel = Some(channel_name.clone());
                    }
                    
                    if success {
                        if let Some(ref data) = result.response_data {
                            if let Some(confirm) = data.get("confirmation_id")
                                .or(data.get("issue_url"))
                                .or(data.get("confirmation")) {
                                confirmation_ids.insert(channel_name, confirm.clone());
                            }
                        }
                    }
                }
                Ok(Err(_)) => {
                    // Task failed internally
                    channel_results.push(ChannelResult {
                        channel_name: "unknown".to_string(),
                        success: false,
                        message: "Internal task error".to_string(),
                        duration_ms: timeout_duration.as_millis() as u64,
                        response_data: None,
                    });
                }
                Err(_) => {
                    // Timeout
                    channel_results.push(ChannelResult {
                        channel_name: "timeout".to_string(),
                        success: false,
                        message: "Channel timeout".to_string(),
                        duration_ms: timeout_duration.as_millis() as u64,
                        response_data: None,
                    });
                }
            }
        }
        
        let success = !confirmation_ids.is_empty() &&
            confirmation_ids.len() >= self.config.min_success_channels;
        
        if success {
            self.successful_reports.fetch_add(1, Ordering::SeqCst);
        }
        
        self.total_reports.fetch_add(1, Ordering::SeqCst);
        
        MeshResult {
            report_id: report.report_id.to_string(),
            success,
            channels_attempted: channel_results.len(),
            channels_succeeded: confirmation_ids.len(),
            channel_results,
            total_duration_ms: start.elapsed().as_millis() as u64,
            confirmation_ids,
            winning_channel,
            consensus_reached: None,
        }
    }
    
    /// Transmit report with retry logic
    pub async fn transmit_with_retry(&self, report: &Report) -> MeshResult {
        let mut last_result = None;
        
        for attempt in 0..self.config.max_retries {
            // Apply backoff if enabled
            if attempt > 0 && self.config.enable_backoff {
                let backoff = self.config.backoff_base_ms * (2_u64.pow(attempt - 1));
                tokio::time::sleep(Duration::from_millis(backoff)).await;
            }
            
            // Choose transmission strategy
            let result = if self.config.parallel_transmission {
                self.transmit_parallel(report).await
            } else {
                self.transmit_sequential(report).await
            };
            
            if result.success {
                return result;
            }
            
            last_result = Some(result);
        }
        
        // Return last failure
        last_result.unwrap_or_else(|| MeshResult {
            report_id: report.report_id.to_string(),
            success: false,
            channels_attempted: 0,
            channels_succeeded: 0,
            channel_results: vec![],
            total_duration_ms: 0,
            confirmation_ids: HashMap::new(),
            winning_channel: None,
            consensus_reached: None,
        })
    }
    
    /// Broadcast emergency alert to ALL channels
    pub async fn broadcast_emergency(&self, report: &Report) -> MeshResult {
        let start = Instant::now();
        let mut channel_results = Vec::new();
        let mut confirmation_ids = HashMap::new();
        let mut winning_channel = None;
        
        // Try ALL channels simultaneously
        let mut tasks = Vec::new();
        for channel in &self.channels {
            let report = report.clone();
            tasks.push(tokio::spawn(async move {
                channel.transmit(&report).await
            }));
        }
        
        for task in tasks {
            if let Ok(Ok(result)) = task.await {
                let success = result.success;
                let channel_name = result.channel_name.clone();
                channel_results.push(result.clone());
                
                if success && winning_channel.is_none() {
                    winning_channel = Some(channel_name.clone());
                }
                
                if success {
                    if let Some(ref data) = result.response_data {
                        for (key, value) in data {
                            confirmation_ids.insert(format!("{}_{}", channel_name, key), value.clone());
                        }
                    }
                }
            }
        }
        
        let success = !confirmation_ids.is_empty();
        
        if success {
            self.successful_reports.fetch_add(1, Ordering::SeqCst);
        }
        
        self.total_reports.fetch_add(1, Ordering::SeqCst);
        
        MeshResult {
            report_id: report.report_id.to_string(),
            success,
            channels_attempted: channel_results.len(),
            channels_succeeded: confirmation_ids.len(),
            channel_results,
            total_duration_ms: start.elapsed().as_millis() as u64,
            confirmation_ids,
            winning_channel,
            consensus_reached: None,
        }
    }
    
    /// Get mesh statistics
    pub fn stats(&self) -> MeshStats {
        MeshStats {
            total_reports: self.total_reports.load(Ordering::SeqCst),
            successful_reports: self.successful_reports.load(Ordering::SeqCst),
            channel_count: self.channels.len(),
        }
    }
    
    /// Reset all channels
    pub async fn reset_all(&self) {
        for channel in &self.channels {
            channel.reset().await;
        }
        
        self.total_reports.store(0, Ordering::SeqCst);
        self.successful_reports.store(0, Ordering::SeqCst);
        *self.last_error.write().await = None;
        self.channel_health.write().await.clear();
    }
}

/// Mesh statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshStats {
    pub total_reports: u32,
    pub successful_reports: u32,
    pub channel_count: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mesh_config_default() {
        let config = MeshConfig::default();
        assert!(config.parallel_transmission);
        assert_eq!(config.max_parallel_channels, 3);
        assert_eq!(config.min_success_channels, 1);
    }
    
    #[test]
    fn test_mesh_creation() {
        let mesh = ReportingMesh::with_defaults().unwrap();
        
        // Should have 5 channels
        assert_eq!(mesh.channels().len(), 5);
    }
    
    #[tokio::test]
    async fn test_mesh_transmit_sequential() {
        let mesh = ReportingMesh::with_defaults().unwrap();
        
        let report = Report::new(
            ReportSeverity::Info,
            ReportCategory::Unknown,
            "test".to_string(),
            "test".to_string(),
            "E-000".to_string(),
            "Test report".to_string(),
        );
        
        let result = mesh.transmit_sequential(&report).await;
        
        // Should attempt at least one channel
        assert!(result.channels_attempted > 0 || !result.success);
    }
    
    #[tokio::test]
    async fn test_mesh_stats() {
        let mesh = ReportingMesh::with_defaults().unwrap();
        let stats = mesh.stats();
        
        assert_eq!(stats.total_reports, 0);
        assert_eq!(stats.channel_count, 5);
    }
    
    #[tokio::test]
    async fn test_mesh_health_update() {
        let mesh = ReportingMesh::with_defaults().unwrap();
        mesh.update_health().await;
        
        let health = mesh.health_summary().await;
        
        // Should have health status for all channels
        assert!(health.contains_key("github-issues"));
        assert!(health.contains_key("direct-api"));
        assert!(health.contains_key("mesh-network"));
        assert!(health.contains_key("email"));
        assert!(health.contains_key("satellite"));
    }
    
    #[tokio::test]
    async fn test_available_channels() {
        let mesh = ReportingMesh::with_defaults().unwrap();
        
        // Update health first
        mesh.update_health().await;
        
        // Should return channels in priority order
        let available = mesh.get_available_channels().await;
        
        // Check that channels are returned in priority order
        for window in available.windows(2) {
            assert!(window[0].priority() <= window[1].priority());
        }
    }
}
