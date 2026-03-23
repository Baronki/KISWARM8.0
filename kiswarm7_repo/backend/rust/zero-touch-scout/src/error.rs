//! Error types for KISWARM Zero-Touch Scout
//! 
//! This module defines all error types used throughout the application.
//! Each error is designed to be actionable and recoverable where possible.

use std::path::PathBuf;
use thiserror::Error;

/// Main error type for the Zero-Touch Scout
#[derive(Error, Debug, Clone)]
pub enum ScoutError {
    // === Binary Verification Errors ===
    #[error("Binary signature verification failed: {0}")]
    SignatureVerificationFailed(String),
    
    #[error("Binary integrity check failed: expected {expected}, got {actual}")]
    IntegrityCheckFailed { expected: String, actual: String },
    
    #[error("Binary has been tampered with")]
    BinaryTampered,
    
    #[error("Binary build timestamp is in the future")]
    BinaryFromFuture,
    
    #[error("Binary has expired (built at {built_at}, expired at {expired_at})")]
    BinaryExpired { built_at: String, expired_at: String },
    
    // === Environment Detection Errors ===
    #[error("Failed to detect environment: {0}")]
    EnvironmentDetectionFailed(String),
    
    #[error("Unsupported environment: {0}")]
    UnsupportedEnvironment(String),
    
    #[error("Failed to read system information: {0}")]
    SystemInfoError(String),
    
    // === Network Errors ===
    #[error("Network connection failed: {0}")]
    NetworkError(String),
    
    #[error("Download failed from {source}: {reason}")]
    DownloadFailed { source: String, reason: String },
    
    #[error("Connection timeout after {timeout_ms}ms")]
    ConnectionTimeout { timeout_ms: u64 },
    
    #[error("All download sources exhausted")]
    AllSourcesExhausted,
    
    #[error("Rate limited")]
    RateLimited,
    
    #[error("Authentication failed: {0}")]
    AuthFailed(String),
    
    #[error("API error: {0}")]
    ApiError(String),
    
    // === Bootstrap Errors ===
    #[error("Bootstrap failed in phase {phase}: {reason}")]
    BootstrapFailed { phase: String, reason: String },
    
    #[error("Ark not found at {path}")]
    ArkNotFound { path: PathBuf },
    
    #[error("Ark integrity check failed: {0}")]
    ArkIntegrityFailed(String),
    
    #[error("Ark manifest is invalid: {0}")]
    ArkManifestInvalid(String),
    
    // === Installation Errors ===
    #[error("Installation failed: {0}")]
    InstallationFailed(String),
    
    #[error("Failed to create virtual environment: {0}")]
    VenvCreationFailed(String),
    
    #[error("Failed to install Python packages: {0}")]
    PipInstallFailed(String),
    
    #[error("Failed to clone repository: {0}")]
    GitCloneFailed(String),
    
    #[error("Failed to configure KISWARM: {0}")]
    ConfigurationFailed(String),
    
    // === Verification Errors ===
    #[error("Verification failed: {0}")]
    VerificationFailed(String),
    
    #[error("Module import failed: {module}")]
    ModuleImportFailed { module: String },
    
    #[error("Service not responding: {service} on port {port}")]
    ServiceNotResponding { service: String, port: u16 },
    
    // === State Machine Errors ===
    #[error("Invalid state transition: from {from} to {to}")]
    InvalidStateTransition { from: String, to: String },
    
    #[error("State machine timeout in state {state}")]
    StateTimeout { state: String },
    
    // === Reporting Errors ===
    #[error("Failed to report to community: {channel}: {reason}")]
    ReportFailed { channel: String, reason: String },
    
    #[error("All reporting channels failed")]
    AllReportChannelsFailed,
    
    // === I/O Errors ===
    #[error("I/O error: {0}")]
    IoError(String),
    
    #[error("Failed to create directory: {path}")]
    DirectoryCreationFailed { path: PathBuf },
    
    #[error("Failed to write file: {path}")]
    FileWriteFailed { path: PathBuf },
    
    #[error("Failed to read file: {path}")]
    FileReadFailed { path: PathBuf },
    
    // === Configuration Errors ===
    #[error("Configuration error: {0}")]
    ConfigError(String),
    
    #[error("Missing required configuration: {0}")]
    MissingConfig(String),
    
    // === Process Errors ===
    #[error("Process execution failed: {command} (exit code: {code})")]
    ProcessFailed { command: String, code: i32 },
    
    #[error("Process timeout: {command} after {timeout_ms}ms")]
    ProcessTimeout { command: String, timeout_ms: u64 },
    
    // === Resource Errors ===
    #[error("Insufficient resources: {resource} ({available} < {required})")]
    InsufficientResources {
        resource: String,
        available: String,
        required: String,
    },
    
    #[error("Disk space critical: {available_gb:.1}GB available, {required_gb:.1}GB required")]
    DiskSpaceCritical { available_gb: f64, required_gb: f64 },
    
    #[error("Memory critical: {available_gb:.1}GB available, {required_gb:.1}GB required")]
    MemoryCritical { available_gb: f64, required_gb: f64 },
    
    // === Critical Errors ===
    #[error("Critical error: {0}")]
    Critical(String),
    
    #[error("Unrecoverable error: {0}")]
    Unrecoverable(String),
    
    #[error("Maximum retries ({max}) exceeded")]
    MaxRetriesExceeded { max: u32 },
    
    // === JSON Errors ===
    #[error("JSON error: {0}")]
    JsonError(String),
}

impl From<std::io::Error> for ScoutError {
    fn from(e: std::io::Error) -> Self {
        ScoutError::IoError(e.to_string())
    }
}

impl From<serde_json::Error> for ScoutError {
    fn from(e: serde_json::Error) -> Self {
        ScoutError::JsonError(e.to_string())
    }
}

/// Error severity levels for categorization
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorSeverity {
    /// Warning - can be recovered automatically
    Warning,
    /// Error - requires retry or alternative path
    Error,
    /// Critical - requires intervention
    Critical,
    /// Fatal - cannot continue
    Fatal,
}

impl ScoutError {
    /// Get the severity level of this error
    pub fn severity(&self) -> ErrorSeverity {
        match self {
            // Warnings
            ScoutError::ConnectionTimeout { .. } => ErrorSeverity::Warning,
            ScoutError::DownloadFailed { .. } => ErrorSeverity::Warning,
            ScoutError::ArkNotFound { .. } => ErrorSeverity::Warning,
            
            // Errors
            ScoutError::NetworkError(_) => ErrorSeverity::Error,
            ScoutError::ProcessFailed { .. } => ErrorSeverity::Error,
            ScoutError::PipInstallFailed(_) => ErrorSeverity::Error,
            ScoutError::GitCloneFailed(_) => ErrorSeverity::Error,
            
            // Critical
            ScoutError::InsufficientResources { .. } => ErrorSeverity::Critical,
            ScoutError::DiskSpaceCritical { .. } => ErrorSeverity::Critical,
            ScoutError::MemoryCritical { .. } => ErrorSeverity::Critical,
            ScoutError::BinaryTampered => ErrorSeverity::Critical,
            
            // Fatal
            ScoutError::Unrecoverable(_) => ErrorSeverity::Fatal,
            ScoutError::MaxRetriesExceeded { .. } => ErrorSeverity::Fatal,
            ScoutError::AllSourcesExhausted => ErrorSeverity::Fatal,
            ScoutError::Critical(_) => ErrorSeverity::Fatal,
            
            // Default to Error
            _ => ErrorSeverity::Error,
        }
    }
    
    /// Check if this error is recoverable
    pub fn is_recoverable(&self) -> bool {
        matches!(self.severity(), ErrorSeverity::Warning | ErrorSeverity::Error)
    }
    
    /// Check if this error requires retry
    pub fn should_retry(&self) -> bool {
        matches!(
            self,
            ScoutError::ConnectionTimeout { .. }
                | ScoutError::NetworkError(_)
                | ScoutError::DownloadFailed { .. }
                | ScoutError::ProcessFailed { .. }
        )
    }
    
    /// Get a unique error code for this error
    pub fn error_code(&self) -> &'static str {
        match self {
            ScoutError::SignatureVerificationFailed(_) => "E001",
            ScoutError::IntegrityCheckFailed { .. } => "E002",
            ScoutError::BinaryTampered => "E003",
            ScoutError::BinaryFromFuture => "E004",
            ScoutError::BinaryExpired { .. } => "E005",
            ScoutError::EnvironmentDetectionFailed(_) => "E100",
            ScoutError::UnsupportedEnvironment(_) => "E101",
            ScoutError::SystemInfoError(_) => "E102",
            ScoutError::NetworkError(_) => "E200",
            ScoutError::DownloadFailed { .. } => "E201",
            ScoutError::ConnectionTimeout { .. } => "E202",
            ScoutError::AllSourcesExhausted => "E203",
            ScoutError::RateLimited => "E204",
            ScoutError::AuthFailed(_) => "E205",
            ScoutError::ApiError(_) => "E206",
            ScoutError::BootstrapFailed { .. } => "E300",
            ScoutError::ArkNotFound { .. } => "E301",
            ScoutError::ArkIntegrityFailed(_) => "E302",
            ScoutError::ArkManifestInvalid(_) => "E303",
            ScoutError::InstallationFailed(_) => "E400",
            ScoutError::VenvCreationFailed(_) => "E401",
            ScoutError::PipInstallFailed(_) => "E402",
            ScoutError::GitCloneFailed(_) => "E403",
            ScoutError::ConfigurationFailed(_) => "E404",
            ScoutError::VerificationFailed(_) => "E500",
            ScoutError::ModuleImportFailed { .. } => "E501",
            ScoutError::ServiceNotResponding { .. } => "E502",
            ScoutError::InvalidStateTransition { .. } => "E600",
            ScoutError::StateTimeout { .. } => "E601",
            ScoutError::ReportFailed { .. } => "E700",
            ScoutError::AllReportChannelsFailed => "E701",
            ScoutError::IoError(_) => "E800",
            ScoutError::DirectoryCreationFailed { .. } => "E801",
            ScoutError::FileWriteFailed { .. } => "E802",
            ScoutError::FileReadFailed { .. } => "E803",
            ScoutError::ConfigError(_) => "E900",
            ScoutError::MissingConfig(_) => "E901",
            ScoutError::ProcessFailed { .. } => "E1000",
            ScoutError::ProcessTimeout { .. } => "E1001",
            ScoutError::InsufficientResources { .. } => "E1100",
            ScoutError::DiskSpaceCritical { .. } => "E1101",
            ScoutError::MemoryCritical { .. } => "E1102",
            ScoutError::Critical(_) => "E9998",
            ScoutError::Unrecoverable(_) => "E9999",
            ScoutError::MaxRetriesExceeded { .. } => "E9997",
            ScoutError::JsonError(_) => "E1200",
        }
    }
}

/// Result type alias for Scout operations
pub type ScoutResult<T> = Result<T, ScoutError>;
