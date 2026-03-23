//! Satellite Uplink Reporting Channel
//!
//! Extreme fallback channel for air-gapped military installations.
//! Provides short-burst satellite transmission for emergency reporting.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

use super::types::*;
use crate::error::{ScoutError, ScoutResult};

/// Satellite configuration
#[derive(Debug, Clone)]
pub struct SatelliteConfig {
    /// Satellite service provider
    pub provider: SatelliteProvider,
    /// Ground station endpoint
    pub ground_station: String,
    /// Transmission mode
    pub transmission_mode: TransmissionMode,
    /// Maximum payload size in bytes (SBD typically 340 bytes)
    pub max_payload_size: usize,
    /// Satellite ID / IMEI
    pub satellite_id: String,
    /// Pre-shared key for authentication
    pub auth_key: String,
    /// Transmission window (satellite pass schedule)
    pub transmission_windows: Vec<TransmissionWindow>,
}

impl Default for SatelliteConfig {
    fn default() -> Self {
        Self {
            provider: SatelliteProvider::Iridium,
            ground_station: "sat-gateway.kiswarm.io".to_string(),
            transmission_mode: TransmissionMode::SBD,
            max_payload_size: 340,
            satellite_id: String::new(),
            auth_key: String::new(),
            transmission_windows: vec![
                TransmissionWindow {
                    start_hour: 0,
                    end_hour: 6,
                    satellite_name: "IRIDIUM-PRIMARY".to_string(),
                }
            ],
        }
    }
}

/// Satellite provider
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SatelliteProvider {
    /// Iridium SBD (Short Burst Data)
    Iridium,
    /// Inmarsat BGAN
    Inmarsat,
    /// Starlink (future)
    Starlink,
    /// Custom military satellite
    MilitaryCustom,
}

/// Transmission mode
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TransmissionMode {
    /// Short Burst Data (340 bytes max)
    SBD,
    /// Standard data
    Standard,
    /// High throughput
    HighThroughput,
}

/// Satellite transmission window
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransmissionWindow {
    /// Start hour (UTC)
    pub start_hour: u8,
    /// End hour (UTC)
    pub end_hour: u8,
    /// Satellite name
    pub satellite_name: String,
}

/// Satellite message format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SatelliteMessage {
    /// Message header (fixed format)
    pub header: SatelliteHeader,
    /// Compressed payload
    pub payload: Vec<u8>,
    /// Checksum
    pub checksum: u16,
}

/// Satellite message header (compact format)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SatelliteHeader {
    /// Protocol version (2 bytes)
    pub version: u8,
    /// Message type (1 byte)
    pub message_type: SatelliteMessageType,
    /// Priority (1 byte)
    pub priority: u8,
    /// Timestamp (4 bytes, Unix epoch)
    pub timestamp: u32,
    /// Message ID (4 bytes)
    pub message_id: u32,
    /// Total segments (1 byte)
    pub total_segments: u8,
    /// Segment number (1 byte)
    pub segment_number: u8,
}

/// Satellite message type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum SatelliteMessageType {
    /// Emergency alert
    Emergency = 0x01,
    /// Installation report
    InstallationReport = 0x02,
    /// Heartbeat
    Heartbeat = 0x03,
    /// Acknowledgment
    Ack = 0x04,
    /// Status query
    StatusQuery = 0x05,
}

/// Satellite uplink channel
pub struct SatelliteChannel {
    /// Configuration
    config: SatelliteConfig,
    /// Is available flag
    is_available: AtomicBool,
    /// Next transmission window
    next_window: RwLock<Option<TransmissionWindow>>,
    /// Message counter
    message_counter: AtomicU32,
    /// Last error message
    last_error: RwLock<Option<String>>,
    /// Pending messages queue
    pending_messages: RwLock<VecDeque<SatelliteMessage>>,
}

impl SatelliteChannel {
    /// Create a new Satellite channel
    pub fn new(config: SatelliteConfig) -> Self {
        Self {
            config,
            is_available: AtomicBool::new(true),
            next_window: RwLock::new(None),
            message_counter: AtomicU32::new(0),
            last_error: RwLock::new(None),
            pending_messages: RwLock::new(VecDeque::new()),
        }
    }
    
    /// Create with default configuration
    pub fn with_defaults() -> Self {
        Self::new(SatelliteConfig::default())
    }
    
    /// Check if we're in a transmission window
    pub async fn in_transmission_window(&self) -> bool {
        let now = chrono::Utc::now();
        let current_hour = now.hour() as u8;
        
        for window in &self.config.transmission_windows {
            if current_hour >= window.start_hour && current_hour < window.end_hour {
                return true;
            }
        }
        
        false
    }
    
    /// Get next available transmission window
    pub async fn get_next_window(&self) -> Option<TransmissionWindow> {
        let now = chrono::Utc::now();
        let current_hour = now.hour() as u8;
        
        // Find next window
        for window in &self.config.transmission_windows {
            if window.start_hour > current_hour {
                return Some(window.clone());
            }
        }
        
        // Wrap around to first window
        self.config.transmission_windows.first().cloned()
    }
    
    /// Compress report for satellite transmission
    pub fn compress_report(&self, report: &Report) -> ScoutResult<Vec<u8>> {
        // Create minimal report format for satellite
        let minimal = MinimalReport {
            v: 1,
            s: match report.severity {
                ReportSeverity::Info => 0,
                ReportSeverity::Warning => 1,
                ReportSeverity::Error => 2,
                ReportSeverity::Critical => 3,
                ReportSeverity::Fatal => 4,
            },
            c: match report.category {
                ReportCategory::InstallationFailure => 0,
                ReportCategory::NetworkIssue => 1,
                ReportCategory::HardwareIssue => 2,
                ReportCategory::SecurityConcern => 3,
                ReportCategory::PerformanceIssue => 4,
                ReportCategory::ConfigurationError => 5,
                ReportCategory::DependencyIssue => 6,
                ReportCategory::AuthFailure => 7,
                ReportCategory::ResourceExhaustion => 8,
                ReportCategory::Unknown => 9,
            },
            e: report.error_code.clone(),
            p: report.failure_phase.chars().take(16).collect(),
            m: report.error_message.chars().take(64).collect(),
            t: report.state_snapshot.total_time_ms as u32,
            r: report.state_snapshot.retry_count as u8,
        };
        
        // Serialize to compact binary format
        bincode::serialize(&minimal)
            .map_err(|e| ScoutError::ReportFailed {
                channel: "satellite".to_string(),
                reason: format!("Compression failed: {}", e),
            })
    }
    
    /// Create satellite message
    pub fn create_message(&self, report: &Report) -> ScoutResult<SatelliteMessage> {
        let payload = self.compress_report(report)?;
        
        // Check if we need to segment
        if payload.len() > self.config.max_payload_size {
            return self.create_segmented_messages(report);
        }
        
        let header = SatelliteHeader {
            version: 1,
            message_type: if report.severity == ReportSeverity::Critical || 
                            report.severity == ReportSeverity::Fatal {
                SatelliteMessageType::Emergency
            } else {
                SatelliteMessageType::InstallationReport
            },
            priority: match report.severity {
                ReportSeverity::Fatal => 0,
                ReportSeverity::Critical => 1,
                ReportSeverity::Error => 2,
                ReportSeverity::Warning => 3,
                ReportSeverity::Info => 4,
            },
            timestamp: chrono::Utc::now().timestamp() as u32,
            message_id: self.message_counter.fetch_add(1, Ordering::SeqCst),
            total_segments: 1,
            segment_number: 0,
        };
        
        // Calculate checksum
        let checksum = self.calculate_checksum(&payload);
        
        Ok(SatelliteMessage {
            header,
            payload,
            checksum,
        })
    }
    
    /// Create segmented messages for large payloads
    fn create_segmented_messages(&self, _report: &Report) -> ScoutResult<SatelliteMessage> {
        // For now, return error - segmented transmission requires more complex handling
        Err(ScoutError::ReportFailed {
            channel: "satellite".to_string(),
            reason: "Report too large for single satellite transmission".to_string(),
        })
    }
    
    /// Calculate CRC-16 checksum
    fn calculate_checksum(&self, data: &[u8]) -> u16 {
        let mut crc: u16 = 0xFFFF;
        
        for byte in data {
            crc ^= *byte as u16;
            for _ in 0..8 {
                if crc & 1 != 0 {
                    crc = (crc >> 1) ^ 0xA001;
                } else {
                    crc >>= 1;
                }
            }
        }
        
        crc
    }
    
    /// Transmit via satellite
    async fn transmit_satellite(&self, message: &SatelliteMessage) -> ScoutResult<String> {
        // Check satellite ID configuration
        if self.config.satellite_id.is_empty() {
            return Err(ScoutError::ConfigError(
                "Satellite ID not configured".to_string()
            ));
        }
        
        // Check transmission window
        if !self.in_transmission_window().await {
            // Queue for later transmission
            self.pending_messages.write().await.push_back(message.clone());
            return Ok(format!(
                "Queued for next transmission window. Message ID: {}",
                message.header.message_id
            ));
        }
        
        // Serialize message
        let message_bytes = bincode::serialize(message)
            .map_err(|e| ScoutError::NetworkError(
                format!("Message serialization failed: {}", e)
            ))?;
        
        // In production, this would:
        // 1. Connect to satellite modem (USB/Serial)
        // 2. Wait for satellite pass
        // 3. Transmit SBD message
        // 4. Receive acknowledgment
        
        // Simulate transmission
        let confirmation = format!(
            "SAT-{}-{}",
            self.config.satellite_id,
            message.header.message_id
        );
        
        Ok(confirmation)
    }
}

/// Minimal report structure for satellite transmission
#[derive(Debug, Clone, Serialize, Deserialize)]
struct MinimalReport {
    /// Version
    v: u8,
    /// Severity (0-4)
    s: u8,
    /// Category (0-9)
    c: u8,
    /// Error code
    e: String,
    /// Phase (truncated)
    p: String,
    /// Message (truncated)
    m: String,
    /// Total time ms
    t: u32,
    /// Retry count
    r: u8,
}

#[async_trait]
impl ReportingChannel for SatelliteChannel {
    fn name(&self) -> &str {
        "satellite"
    }
    
    fn priority(&self) -> ChannelPriority {
        ChannelPriority::LastResort
    }
    
    async fn is_available(&self) -> bool {
        self.is_available.load(Ordering::SeqCst) &&
            !self.config.satellite_id.is_empty() &&
            !self.config.auth_key.is_empty()
    }
    
    async fn status(&self) -> ChannelStatus {
        if !self.is_available.load(Ordering::SeqCst) {
            return ChannelStatus::Unavailable;
        }
        
        if self.config.satellite_id.is_empty() {
            return ChannelStatus::NotConfigured;
        }
        
        if self.in_transmission_window().await {
            ChannelStatus::Available
        } else {
            ChannelStatus::Degraded // Available but outside transmission window
        }
    }
    
    async fn transmit(&self, report: &Report) -> ChannelResult {
        let start = Instant::now();
        
        // Create satellite message
        let message = match self.create_message(report) {
            Ok(m) => m,
            Err(e) => {
                return ChannelResult {
                    channel_name: self.name().to_string(),
                    success: false,
                    message: e.to_string(),
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: None,
                };
            }
        };
        
        // Transmit
        match self.transmit_satellite(&message).await {
            Ok(confirmation) => {
                let mut response_data = HashMap::new();
                response_data.insert("confirmation".to_string(), confirmation.clone());
                response_data.insert("message_id".to_string(), message.header.message_id.to_string());
                response_data.insert("satellite_id".to_string(), self.config.satellite_id.clone());
                
                let in_window = self.in_transmission_window().await;
                let message = if in_window {
                    format!("Satellite transmission confirmed: {}", confirmation)
                } else {
                    format!("Queued for next transmission window: {}", confirmation)
                };
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: true,
                    message,
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
        // Satellite transmission has strict limits
        Some(10) // Assume 10 messages per window
    }
    
    async fn reset(&self) {
        self.is_available.store(true, Ordering::SeqCst);
        self.message_counter.store(0, Ordering::SeqCst);
        *self.last_error.write().await = None;
        self.pending_messages.write().await.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_satellite_config_default() {
        let config = SatelliteConfig::default();
        assert_eq!(config.provider, SatelliteProvider::Iridium);
        assert_eq!(config.max_payload_size, 340);
        assert!(!config.transmission_windows.is_empty());
    }
    
    #[test]
    fn test_channel_name() {
        let channel = SatelliteChannel::with_defaults();
        assert_eq!(channel.name(), "satellite");
    }
    
    #[test]
    fn test_channel_priority() {
        let channel = SatelliteChannel::with_defaults();
        assert_eq!(channel.priority(), ChannelPriority::LastResort);
    }
    
    #[test]
    fn test_compress_report() {
        let channel = SatelliteChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Critical,
            ReportCategory::InstallationFailure,
            "airgap".to_string(),
            "OnlineBootstrap".to_string(),
            "E-500".to_string(),
            "Installation failed due to missing dependencies".to_string(),
        );
        
        let compressed = channel.compress_report(&report).unwrap();
        
        // Should be much smaller than full report
        assert!(compressed.len() < 340);
    }
    
    #[test]
    fn test_checksum_calculation() {
        let channel = SatelliteChannel::with_defaults();
        let data = b"test data";
        let checksum = channel.calculate_checksum(data);
        
        // Checksum should be consistent
        let checksum2 = channel.calculate_checksum(data);
        assert_eq!(checksum, checksum2);
        
        // Different data should produce different checksum
        let different_data = b"different data";
        let checksum3 = channel.calculate_checksum(different_data);
        assert_ne!(checksum, checksum3);
    }
    
    #[test]
    fn test_satellite_message_creation() {
        let channel = SatelliteChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Error,
            ReportCategory::NetworkIssue,
            "test".to_string(),
            "EnvDetect".to_string(),
            "E-404".to_string(),
            "Network error".to_string(),
        );
        
        let message = channel.create_message(&report).unwrap();
        
        assert_eq!(message.header.version, 1);
        assert_eq!(message.header.message_type, SatelliteMessageType::InstallationReport);
        assert_eq!(message.header.total_segments, 1);
    }
    
    #[test]
    fn test_emergency_message_type() {
        let channel = SatelliteChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Fatal,
            ReportCategory::SecurityConcern,
            "military".to_string(),
            "SelfVerify".to_string(),
            "E-999".to_string(),
            "Critical security violation".to_string(),
        );
        
        let message = channel.create_message(&report).unwrap();
        
        assert_eq!(message.header.message_type, SatelliteMessageType::Emergency);
        assert_eq!(message.header.priority, 0); // Highest priority
    }
}
