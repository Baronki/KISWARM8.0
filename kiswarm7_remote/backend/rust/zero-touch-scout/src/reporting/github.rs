//! GitHub Issues Reporting Channel
//!
//! Primary channel for community reporting via GitHub Issues API.
//! Provides authenticated issue creation with rate limit awareness.

use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU32, AtomicBool, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

use super::types::*;
use crate::error::{ScoutError, ScoutResult};

/// GitHub API configuration
#[derive(Debug, Clone)]
pub struct GitHubConfig {
    /// GitHub API base URL
    pub api_url: String,
    /// Repository owner
    pub owner: String,
    /// Repository name
    pub repo: String,
    /// GitHub token (optional - for higher rate limits)
    pub token: Option<String>,
    /// Issue labels to apply
    pub labels: Vec<String>,
    /// Request timeout in seconds
    pub timeout_secs: u64,
}

impl Default for GitHubConfig {
    fn default() -> Self {
        Self {
            api_url: "https://api.github.com".to_string(),
            owner: "Baronki".to_string(),
            repo: "KISWARM6.0".to_string(),
            token: None,
            labels: vec![
                "automated-report".to_string(),
                "zero-touch-scout".to_string(),
            ],
            timeout_secs: 30,
        }
    }
}

/// GitHub issue response
#[derive(Debug, Clone, Serialize, Deserialize)]
struct GitHubIssueResponse {
    number: u32,
    html_url: String,
    id: u64,
    state: String,
}

/// GitHub rate limit response
#[derive(Debug, Clone, Serialize, Deserialize)]
struct GitHubRateLimitResponse {
    resources: GitHubRateLimitResources,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct GitHubRateLimitResources {
    core: GitHubRateLimitInfo,
    search: GitHubRateLimitInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct GitHubRateLimitInfo {
    limit: u32,
    remaining: u32,
    reset: u64,
}

/// GitHub Issues reporting channel
pub struct GitHubChannel {
    /// Configuration
    config: GitHubConfig,
    /// HTTP client
    client: Client,
    /// Rate limit remaining
    rate_limit_remaining: AtomicU32,
    /// Rate limit reset time
    rate_limit_reset: RwLock<Option<Instant>>,
    /// Is available flag
    is_available: AtomicBool,
    /// Last error message
    last_error: RwLock<Option<String>>,
}

impl GitHubChannel {
    /// Create a new GitHub Issues channel
    pub fn new(config: GitHubConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .user_agent("KISWARM-ZeroTouch-Scout/1.0")
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            rate_limit_remaining: AtomicU32::new(5000), // Default GitHub limit
            rate_limit_reset: RwLock::new(None),
            is_available: AtomicBool::new(true),
            last_error: RwLock::new(None),
        })
    }
    
    /// Create with default configuration
    pub fn with_defaults() -> ScoutResult<Self> {
        Self::new(GitHubConfig::default())
    }
    
    /// Build issue title from report
    fn build_title(&self, report: &Report) -> String {
        format!(
            "[{}] {} - {} - {}",
            report.severity,
            report.error_code,
            report.failure_phase,
            &report.error_message.chars().take(50).collect::<String>()
        )
    }
    
    /// Build issue body from report
    fn build_body(&self, report: &Report) -> String {
        let mut body = String::new();
        
        // Header
        body.push_str("## 🤖 Automated Report from Zero-Touch Scout\n\n");
        body.push_str(&format!("**Report ID:** {}\n", report.report_id));
        body.push_str(&format!("**Timestamp:** {}\n", report.timestamp));
        body.push_str(&format!("**Severity:** {}\n", report.severity));
        body.push_str(&format!("**Category:** {}\n\n", report.category));
        
        // Environment
        body.push_str("## 🔧 Environment\n\n");
        body.push_str(&format!("**Type:** {}\n", report.environment));
        body.push_str(&format!("**OS:** {}\n", report.system_fingerprint.os_type));
        body.push_str(&format!("**Architecture:** {}\n\n", report.system_fingerprint.architecture));
        
        // Error Details
        body.push_str("## ❌ Error Details\n\n");
        body.push_str(&format!("**Phase:** {}\n", report.failure_phase));
        body.push_str(&format!("**Error Code:** {}\n", report.error_code));
        body.push_str(&format!("**Message:** {}\n\n", report.error_message));
        
        // State Snapshot
        body.push_str("## 📊 State Machine Snapshot\n\n");
        body.push_str(&format!("**Current State:** {}\n", report.state_snapshot.current_state));
        if let Some(ref prev) = report.state_snapshot.previous_state {
            body.push_str(&format!("**Previous State:** {}\n", prev));
        }
        body.push_str(&format!("**Time in State:** {}ms\n", report.state_snapshot.time_in_state_ms));
        body.push_str(&format!("**Total Time:** {}ms\n", report.state_snapshot.total_time_ms));
        body.push_str(&format!("**Retry Count:** {}\n\n", report.state_snapshot.retry_count));
        
        // Error History
        if !report.state_snapshot.error_history.is_empty() {
            body.push_str("## 📜 Error History\n\n```\n");
            for error in &report.state_snapshot.error_history {
                body.push_str(&format!("{}\n", error));
            }
            body.push_str("```\n\n");
        }
        
        // Attempted Solutions
        if !report.attempted_solutions.is_empty() {
            body.push_str("## 🔧 Attempted Solutions\n\n");
            for (i, solution) in report.attempted_solutions.iter().enumerate() {
                body.push_str(&format!("{}. {}\n", i + 1, solution));
            }
            body.push_str("\n");
        }
        
        // Hardware Profile
        body.push_str("## 💻 Hardware Profile\n\n");
        body.push_str(&format!("**CPU Cores:** {}\n", report.hardware_profile.cpu_cores));
        body.push_str(&format!("**RAM:** {:.1} GB\n", report.hardware_profile.ram_gb));
        body.push_str(&format!("**Disk:** {:.1} GB\n", report.hardware_profile.disk_gb));
        body.push_str(&format!("**GPU:** {}\n", if report.hardware_profile.has_gpu { "Yes" } else { "No" }));
        if let Some(vram) = report.hardware_profile.gpu_vram_gb {
            body.push_str(&format!("**GPU VRAM:** {:.1} GB\n", vram));
        }
        body.push_str("\n");
        
        // Network Profile
        body.push_str("## 🌐 Network Profile\n\n");
        body.push_str(&format!("**Internet:** {}\n", if report.network_profile.has_internet { "Yes" } else { "No" }));
        body.push_str(&format!("**GitHub Reachable:** {}\n", if report.network_profile.github_reachable { "Yes" } else { "No" }));
        body.push_str(&format!("**PyPI Reachable:** {}\n", if report.network_profile.pypi_reachable { "Yes" } else { "No" }));
        if let Some(latency) = report.network_profile.latency_ms {
            body.push_str(&format!("**Latency:** {:.0}ms\n", latency));
        }
        body.push_str("\n");
        
        // Debug Info
        if let Some(ref debug) = report.debug_info {
            body.push_str("## 🔍 Debug Information\n\n```\n");
            body.push_str(debug);
            body.push_str("\n```\n\n");
        }
        
        // Metadata
        if !report.metadata.is_empty() {
            body.push_str("## 📋 Additional Information\n\n");
            for (key, value) in &report.metadata {
                body.push_str(&format!("**{}:** {}\n", key, value));
            }
            body.push_str("\n");
        }
        
        // Footer
        body.push_str("---\n");
        body.push_str(&format!("*Generated by Zero-Touch Scout v{}*\n", report.version));
        
        body
    }
    
    /// Check GitHub API rate limit
    async fn check_rate_limit(&self) -> ScoutResult<()> {
        let url = format!("{}/rate_limit", self.config.api_url);
        
        let mut request = self.client.get(&url);
        
        if let Some(ref token) = self.config.token {
            request = request.bearer_auth(token);
        }
        
        let response = request
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Rate limit check failed: {}", e)))?;
        
        if response.status().is_success() {
            let rate_limit: GitHubRateLimitResponse = response
                .json()
                .await
                .map_err(|e| ScoutError::NetworkError(format!("Failed to parse rate limit: {}", e)))?;
            
            self.rate_limit_remaining.store(
                rate_limit.resources.core.remaining,
                Ordering::SeqCst,
            );
            
            if rate_limit.resources.core.remaining == 0 {
                let reset_time = Instant::now() + Duration::from_secs(
                    rate_limit.resources.core.reset.saturating_sub(
                        std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .unwrap()
                            .as_secs()
                    )
                );
                
                *self.rate_limit_reset.write().await = Some(reset_time);
                return Err(ScoutError::RateLimited {
                    service: "GitHub API".to_string(),
                    reset_seconds: rate_limit.resources.core.reset as u64,
                });
            }
        }
        
        Ok(())
    }
    
    /// Create GitHub issue
    async fn create_issue(&self, title: &str, body: &str, labels: &[String]) -> ScoutResult<GitHubIssueResponse> {
        let url = format!(
            "{}/repos/{}/{}/issues",
            self.config.api_url,
            self.config.owner,
            self.config.repo
        );
        
        let issue_data = serde_json::json!({
            "title": title,
            "body": body,
            "labels": labels,
        });
        
        let mut request = self.client.post(&url)
            .json(&issue_data);
        
        if let Some(ref token) = self.config.token {
            request = request.bearer_auth(token);
        }
        
        let response = request
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Issue creation failed: {}", e)))?;
        
        let status = response.status();
        
        if status == reqwest::StatusCode::FORBIDDEN {
            return Err(ScoutError::RateLimited {
                service: "GitHub API".to_string(),
                reset_seconds: 3600,
            });
        }
        
        if status == reqwest::StatusCode::UNAUTHORIZED {
            return Err(ScoutError::AuthFailed {
                service: "GitHub API".to_string(),
            });
        }
        
        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
            return Err(ScoutError::ApiError {
                service: "GitHub API".to_string(),
                status: status.as_u16(),
                message: error_text,
            });
        }
        
        response
            .json()
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Failed to parse response: {}", e)))
    }
}

#[async_trait]
impl ReportingChannel for GitHubChannel {
    fn name(&self) -> &str {
        "github-issues"
    }
    
    fn priority(&self) -> ChannelPriority {
        ChannelPriority::Primary
    }
    
    async fn is_available(&self) -> bool {
        // Check rate limit
        if self.rate_limit_remaining.load(Ordering::SeqCst) == 0 {
            // Check if reset time has passed
            if let Some(reset) = *self.rate_limit_reset.read().await {
                if Instant::now() < reset {
                    return false;
                }
            }
        }
        
        self.is_available.load(Ordering::SeqCst)
    }
    
    async fn status(&self) -> ChannelStatus {
        if !self.is_available.load(Ordering::SeqCst) {
            return ChannelStatus::Unavailable;
        }
        
        if self.rate_limit_remaining.load(Ordering::SeqCst) == 0 {
            return ChannelStatus::RateLimited;
        }
        
        ChannelStatus::Available
    }
    
    async fn transmit(&self, report: &Report) -> ChannelResult {
        let start = Instant::now();
        
        // Check rate limit first
        if let Err(e) = self.check_rate_limit().await {
            *self.last_error.write().await = Some(e.to_string());
            return ChannelResult {
                channel_name: self.name().to_string(),
                success: false,
                message: format!("Rate limit check failed: {}", e),
                duration_ms: start.elapsed().as_millis() as u64,
                response_data: None,
            };
        }
        
        // Build issue content
        let title = self.build_title(report);
        let body = self.build_body(report);
        
        // Combine default labels with severity/category
        let mut labels = self.config.labels.clone();
        labels.push(format!("severity-{}", report.severity).to_lowercase());
        labels.push(report.category.to_string());
        
        // Create the issue
        match self.create_issue(&title, &body, &labels).await {
            Ok(issue) => {
                let mut response_data = HashMap::new();
                response_data.insert("issue_number".to_string(), issue.number.to_string());
                response_data.insert("issue_url".to_string(), issue.html_url.clone());
                response_data.insert("issue_id".to_string(), issue.id.to_string());
                
                // Decrement rate limit
                self.rate_limit_remaining.fetch_sub(1, Ordering::SeqCst);
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: true,
                    message: format!("Issue #{} created: {}", issue.number, issue.html_url),
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: Some(response_data),
                }
            }
            Err(e) => {
                *self.last_error.write().await = Some(e.to_string());
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: false,
                    message: e.to_string(),
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: None,
                }
            }
        }
    }
    
    fn rate_limit_remaining(&self) -> Option<u32> {
        Some(self.rate_limit_remaining.load(Ordering::SeqCst))
    }
    
    async fn reset(&self) {
        self.is_available.store(true, Ordering::SeqCst);
        self.rate_limit_remaining.store(5000, Ordering::SeqCst);
        *self.rate_limit_reset.write().await = None;
        *self.last_error.write().await = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_github_config_default() {
        let config = GitHubConfig::default();
        assert_eq!(config.owner, "Baronki");
        assert_eq!(config.repo, "KISWARM6.0");
        assert!(config.labels.contains(&"automated-report".to_string()));
    }
    
    #[test]
    fn test_build_title() {
        let channel = GitHubChannel::with_defaults().unwrap();
        let report = Report::new(
            ReportSeverity::Error,
            ReportCategory::InstallationFailure,
            "colab".to_string(),
            "OnlineBootstrap".to_string(),
            "E-404".to_string(),
            "Failed to download package xyz".to_string(),
        );
        
        let title = channel.build_title(&report);
        assert!(title.contains("[ERROR]"));
        assert!(title.contains("E-404"));
        assert!(title.contains("OnlineBootstrap"));
    }
    
    #[test]
    fn test_build_body_contains_sections() {
        let channel = GitHubChannel::with_defaults().unwrap();
        let report = Report::new(
            ReportSeverity::Critical,
            ReportCategory::NetworkIssue,
            "docker".to_string(),
            "EnvDetect".to_string(),
            "E-503".to_string(),
            "Network unreachable".to_string(),
        );
        
        let body = channel.build_body(&report);
        
        assert!(body.contains("## 🤖 Automated Report"));
        assert!(body.contains("## 🔧 Environment"));
        assert!(body.contains("## ❌ Error Details"));
        assert!(body.contains("## 📊 State Machine Snapshot"));
        assert!(body.contains("## 💻 Hardware Profile"));
        assert!(body.contains("## 🌐 Network Profile"));
        assert!(body.contains("CRITICAL"));
        assert!(body.contains("network-issue"));
    }
    
    #[test]
    fn test_channel_name() {
        let channel = GitHubChannel::with_defaults().unwrap();
        assert_eq!(channel.name(), "github-issues");
    }
    
    #[test]
    fn test_channel_priority() {
        let channel = GitHubChannel::with_defaults().unwrap();
        assert_eq!(channel.priority(), ChannelPriority::Primary);
    }
}
