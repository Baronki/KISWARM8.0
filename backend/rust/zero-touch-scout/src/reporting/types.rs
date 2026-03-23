//! Common types for Community Reporting Mesh

use serde::{Deserialize, Serialize};

/// Unique report identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ReportId(pub String);

impl Default for ReportId {
    fn default() -> Self {
        Self(uuid::Uuid::new_v4().to_string())
    }
}

impl ReportId {
    /// Create a new report ID
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Get as string
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Report severity levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReportSeverity {
    /// Informational
    Info = 1,
    /// Warning
    Warning = 2,
    /// Error
    Error = 3,
    /// Critical
    Critical = 4,
    /// Fatal
    Fatal = 5,
}

/// Report category
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReportCategory {
    /// Installation issue
    Installation,
    /// Network issue
    Network,
    /// Configuration issue
    Configuration,
    /// Resource issue (memory, disk, CPU)
    Resource,
    /// Dependency issue
    Dependency,
    /// Permission issue
    Permission,
    /// State machine error
    StateMachine,
    /// Verification failure
    Verification,
    /// Timeout
    Timeout,
    /// Unknown/Other
    Unknown,
}

/// A report to be sent through the reporting mesh
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Report {
    /// Unique report ID
    pub id: ReportId,
    
    /// Severity level
    pub severity: ReportSeverity,
    
    /// Category
    pub category: ReportCategory,
    
    /// Human-readable message
    pub message: String,
    
    /// Error code (if applicable)
    pub error_code: Option<String>,
    
    /// System fingerprint (anonymized)
    pub system_fingerprint: String,
    
    /// Current state
    pub current_state: String,
    
    /// Timestamp
    pub timestamp: String,
    
    /// Additional context
    pub context: serde_json::Value,
}

impl Report {
    /// Create a new report
    pub fn new(
        severity: ReportSeverity,
        category: ReportCategory,
        message: impl Into<String>,
    ) -> Self {
        Self {
            id: ReportId::new(),
            severity,
            category,
            message: message.into(),
            error_code: None,
            system_fingerprint: generate_fingerprint(),
            current_state: "unknown".to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
            context: serde_json::Value::Null,
        }
    }
    
    /// Set error code
    pub fn with_error_code(mut self, code: impl Into<String>) -> Self {
        self.error_code = Some(code.into());
        self
    }
    
    /// Set current state
    pub fn with_state(mut self, state: impl Into<String>) -> Self {
        self.current_state = state.into();
        self
    }
    
    /// Set context
    pub fn with_context(mut self, context: serde_json::Value) -> Self {
        self.context = context;
        self
    }
    
    /// Convert to JSON
    pub fn to_json(&self) -> crate::ScoutResult<String> {
        serde_json::to_string(self)
            .map_err(|e| crate::ScoutError::JsonError(e.to_string()))
    }
}

/// Generate an anonymized system fingerprint
fn generate_fingerprint() -> String {
    // Create a hash based on system characteristics
    use sha2::{Digest, Sha256};
    
    let mut hasher = Sha256::new();
    
    // Add OS info
    hasher.update(std::env::consts::OS.as_bytes());
    hasher.update(std::env::consts::ARCH.as_bytes());
    
    // Add hostname (truncated for privacy)
    if let Ok(hostname) = gethostname::gethostname().into_string() {
        hasher.update(&hostname.as_bytes()[..hostname.len().min(16)]);
    }
    
    // Add timestamp bucket (hour precision for privacy)
    let hour_bucket = chrono::Utc::now().format("%Y-%m-%d-%H").to_string();
    hasher.update(hour_bucket.as_bytes());
    
    // Return truncated hash
    let hash = format!("{:x}", hasher.finalize());
    format!("fp-{}", &hash[..16])
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_report_creation() {
        let report = Report::new(
            ReportSeverity::Error,
            ReportCategory::Network,
            "Connection failed",
        );
        
        assert_eq!(report.severity, ReportSeverity::Error);
        assert_eq!(report.category, ReportCategory::Network);
        assert!(report.error_code.is_none());
    }
    
    #[test]
    fn test_report_with_error_code() {
        let report = Report::new(
            ReportSeverity::Warning,
            ReportCategory::Installation,
            "Package not found",
        ).with_error_code("E402");
        
        assert_eq!(report.error_code, Some("E402".to_string()));
    }
    
    #[test]
    fn test_report_id_uniqueness() {
        let id1 = ReportId::new();
        let id2 = ReportId::new();
        assert_ne!(id1, id2);
    }
}
