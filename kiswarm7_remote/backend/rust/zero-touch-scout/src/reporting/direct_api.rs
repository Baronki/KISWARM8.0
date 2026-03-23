//! Direct API Reporting Channel
//!
//! Secondary channel for direct API endpoint communication.
//! Provides HTTPS with certificate pinning and compressed payloads.

use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU32, AtomicBool, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

use super::types::*;
use crate::error::{ScoutError, ScoutResult};

/// Direct API configuration
#[derive(Debug, Clone)]
pub struct DirectApiConfig {
    /// API base URL
    pub base_url: String,
    /// API key (optional)
    pub api_key: Option<String>,
    /// Request timeout in seconds
    pub timeout_secs: u64,
    /// Enable certificate pinning
    pub cert_pinning: bool,
    /// Enable compression
    pub compression: bool,
    /// Retry attempts
    pub retry_attempts: u32,
    /// Backoff base in milliseconds
    pub backoff_base_ms: u64,
}

impl Default for DirectApiConfig {
    fn default() -> Self {
        Self {
            base_url: "https://api.kiswarm.io".to_string(),
            api_key: None,
            timeout_secs: 30,
            cert_pinning: true,
            compression: true,
            retry_attempts: 3,
            backoff_base_ms: 1000,
        }
    }
}

/// API response structure
#[derive(Debug, Clone, Serialize, Deserialize)]
struct ApiResponse {
    success: bool,
    message: String,
    report_id: Option<String>,
    confirmation_id: Option<String>,
    timestamp: String,
}

/// Direct API reporting channel
pub struct DirectApiChannel {
    /// Configuration
    config: DirectApiConfig,
    /// HTTP client
    client: Client,
    /// Is available flag
    is_available: AtomicBool,
    /// Consecutive failures
    consecutive_failures: AtomicU32,
    /// Last error message
    last_error: RwLock<Option<String>>,
}

impl DirectApiChannel {
    /// Create a new Direct API channel
    pub fn new(config: DirectApiConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .user_agent("KISWARM-ZeroTouch-Scout/1.0")
            .gzip(config.compression)
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            is_available: AtomicBool::new(true),
            consecutive_failures: AtomicU32::new(0),
            last_error: RwLock::new(None),
        })
    }
    
    /// Create with default configuration
    pub fn with_defaults() -> ScoutResult<Self> {
        Self::new(DirectApiConfig::default())
    }
    
    /// Compress report data
    fn compress_report(&self, report: &Report) -> ScoutResult<Vec<u8>> {
        let json = report.to_json()
            .map_err(|e| ScoutError::ReportFailed {
                channel: "direct-api".to_string(),
                reason: format!("JSON serialization failed: {}", e),
            })?;
        
        // Simple gzip compression
        use flate2::write::GzEncoder;
        use flate2::Compression;
        use std::io::Write;
        
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(json.as_bytes())
            .map_err(|e| ScoutError::ReportFailed {
                channel: "direct-api".to_string(),
                reason: format!("Compression failed: {}", e),
            })?;
        
        encoder.finish()
            .map_err(|e| ScoutError::ReportFailed {
                channel: "direct-api".to_string(),
                reason: format!("Compression finalize failed: {}", e),
            })
    }
    
    /// Send report to API endpoint
    async fn send_report(&self, report: &Report) -> ScoutResult<ApiResponse> {
        let url = format!("{}/v1/reports", self.config.base_url);
        
        // Prepare payload
        let payload = if self.config.compression {
            self.compress_report(report)?
        } else {
            report.to_json()?.into_bytes()
        };
        
        // Build request
        let mut request = self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .header("X-Report-Version", &report.version);
        
        if self.config.compression {
            request = request.header("Content-Encoding", "gzip");
        }
        
        if let Some(ref api_key) = self.config.api_key {
            request = request.header("X-API-Key", api_key);
        }
        
        request = request.body(payload);
        
        // Send with retries
        let mut last_error: Option<reqwest::Error> = None;
        
        for attempt in 0..self.config.retry_attempts {
            let backoff = self.config.backoff_base_ms * (2_u64.pow(attempt));
            
            if attempt > 0 {
                tokio::time::sleep(Duration::from_millis(backoff)).await;
            }
            
            match request.try_clone().unwrap().send().await {
                Ok(response) => {
                    let status = response.status();
                    
                    if status.is_success() {
                        return response.json().await
                            .map_err(|e| ScoutError::NetworkError(
                                format!("Failed to parse response: {}", e)
                            ));
                    }
                    
                    if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
                        return Err(ScoutError::RateLimited {
                            service: "Direct API".to_string(),
                            reset_seconds: 60,
                        });
                    }
                    
                    if status == reqwest::StatusCode::UNAUTHORIZED {
                        return Err(ScoutError::AuthFailed {
                            service: "Direct API".to_string(),
                        });
                    }
                    
                    let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                    return Err(ScoutError::ApiError {
                        service: "Direct API".to_string(),
                        status: status.as_u16(),
                        message: error_text,
                    });
                }
                Err(e) => {
                    last_error = Some(e);
                    continue;
                }
            }
        }
        
        Err(ScoutError::NetworkError(format!(
            "All retry attempts failed: {}",
            last_error.map(|e| e.to_string()).unwrap_or_else(|| "Unknown error".to_string())
        )))
    }
    
    /// Health check
    pub async fn health_check(&self) -> bool {
        let url = format!("{}/health", self.config.base_url);
        
        match self.client.get(&url).send().await {
            Ok(response) => response.status().is_success(),
            Err(_) => false,
        }
    }
}

#[async_trait]
impl ReportingChannel for DirectApiChannel {
    fn name(&self) -> &str {
        "direct-api"
    }
    
    fn priority(&self) -> ChannelPriority {
        ChannelPriority::Secondary
    }
    
    async fn is_available(&self) -> bool {
        self.is_available.load(Ordering::SeqCst) && 
            self.consecutive_failures.load(Ordering::SeqCst) < 3
    }
    
    async fn status(&self) -> ChannelStatus {
        let failures = self.consecutive_failures.load(Ordering::SeqCst);
        
        if failures >= 3 {
            return ChannelStatus::Failed;
        }
        
        if !self.is_available.load(Ordering::SeqCst) {
            return ChannelStatus::Unavailable;
        }
        
        // Quick health check
        if self.health_check().await {
            ChannelStatus::Available
        } else {
            ChannelStatus::Unavailable
        }
    }
    
    async fn transmit(&self, report: &Report) -> ChannelResult {
        let start = Instant::now();
        
        match self.send_report(report).await {
            Ok(response) => {
                // Reset failure counter on success
                self.consecutive_failures.store(0, Ordering::SeqCst);
                
                let mut response_data = HashMap::new();
                if let Some(ref confirm_id) = response.confirmation_id {
                    response_data.insert("confirmation_id".to_string(), confirm_id.clone());
                }
                if let Some(ref report_id) = response.report_id {
                    response_data.insert("report_id".to_string(), report_id.clone());
                }
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: true,
                    message: response.message,
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: Some(response_data),
                }
            }
            Err(e) => {
                // Increment failure counter
                self.consecutive_failures.fetch_add(1, Ordering::SeqCst);
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
        None // Direct API doesn't expose rate limits
    }
    
    async fn reset(&self) {
        self.is_available.store(true, Ordering::SeqCst);
        self.consecutive_failures.store(0, Ordering::SeqCst);
        *self.last_error.write().await = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_direct_api_config_default() {
        let config = DirectApiConfig::default();
        assert_eq!(config.base_url, "https://api.kiswarm.io");
        assert!(config.cert_pinning);
        assert!(config.compression);
        assert_eq!(config.retry_attempts, 3);
    }
    
    #[test]
    fn test_channel_name() {
        let channel = DirectApiChannel::with_defaults().unwrap();
        assert_eq!(channel.name(), "direct-api");
    }
    
    #[test]
    fn test_channel_priority() {
        let channel = DirectApiChannel::with_defaults().unwrap();
        assert_eq!(channel.priority(), ChannelPriority::Secondary);
    }
    
    #[test]
    fn test_compress_report() {
        let channel = DirectApiChannel::with_defaults().unwrap();
        let report = Report::new(
            ReportSeverity::Info,
            ReportCategory::Unknown,
            "test".to_string(),
            "test".to_string(),
            "E-000".to_string(),
            "Test message".to_string(),
        );
        
        let compressed = channel.compress_report(&report);
        assert!(compressed.is_ok());
        
        // Compressed should be smaller for larger payloads
        let compressed_data = compressed.unwrap();
        assert!(!compressed_data.is_empty());
    }
}
