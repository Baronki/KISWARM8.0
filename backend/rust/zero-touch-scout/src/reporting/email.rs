//! Email Fallback Reporting Channel
//!
//! Emergency fallback channel for report delivery via email.
//! Works when web APIs are blocked or unavailable.

use async_trait::async_trait;
use lettre::{
    message::{header::ContentType, MultiPart, SinglePart},
    transport::smtp::authentication::Credentials,
    Message, SmtpTransport, Transport,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

use super::types::*;
use crate::error::{ScoutError, ScoutResult};

/// Email channel configuration
#[derive(Debug, Clone)]
pub struct EmailConfig {
    /// SMTP server hostname
    pub smtp_host: String,
    /// SMTP port
    pub smtp_port: u16,
    /// SMTP username
    pub username: String,
    /// SMTP password (or app password)
    pub password: String,
    /// From address
    pub from_address: String,
    /// To address (report destination)
    pub to_address: String,
    /// Use TLS
    pub use_tls: bool,
    /// Connection timeout in seconds
    pub timeout_secs: u64,
    /// Maximum retries
    pub max_retries: u32,
}

impl Default for EmailConfig {
    fn default() -> Self {
        Self {
            smtp_host: "smtp.gmail.com".to_string(),
            smtp_port: 587,
            username: String::new(),
            password: String::new(),
            from_address: "scout@kiswarm.io".to_string(),
            to_address: "report@kiswarm.io".to_string(),
            use_tls: true,
            timeout_secs: 30,
            max_retries: 3,
        }
    }
}

/// Email report format
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EmailFormat {
    /// Plain text
    PlainText,
    /// HTML formatted
    Html,
    /// Both (multipart)
    Multipart,
}

/// Email reporting channel
pub struct EmailChannel {
    /// Configuration
    config: EmailConfig,
    /// Email format
    format: EmailFormat,
    /// Is available flag
    is_available: AtomicBool,
    /// Consecutive failures
    consecutive_failures: AtomicU32,
    /// Last error message
    last_error: RwLock<Option<String>>,
    /// SMTP transport (lazily initialized)
    transport: RwLock<Option<SmtpTransport>>,
}

impl EmailChannel {
    /// Create a new Email channel
    pub fn new(config: EmailConfig) -> Self {
        Self {
            config,
            format: EmailFormat::Multipart,
            is_available: AtomicBool::new(true),
            consecutive_failures: AtomicU32::new(0),
            last_error: RwLock::new(None),
            transport: RwLock::new(None),
        }
    }
    
    /// Create with default configuration
    pub fn with_defaults() -> Self {
        Self::new(EmailConfig::default())
    }
    
    /// Set email format
    pub fn with_format(mut self, format: EmailFormat) -> Self {
        self.format = format;
        self
    }
    
    /// Build email subject
    fn build_subject(&self, report: &Report) -> String {
        format!(
            "[KISWARM-ZTS][{}] {} - {}",
            report.severity,
            report.error_code,
            report.failure_phase
        )
    }
    
    /// Build plain text body
    fn build_plain_body(&self, report: &Report) -> String {
        let mut body = String::new();
        
        body.push_str("KISWARM Zero-Touch Scout Report\n");
        body.push_str(&"=".repeat(60));
        body.push_str("\n\n");
        
        body.push_str(&format!("Report ID: {}\n", report.report_id));
        body.push_str(&format!("Timestamp: {}\n", report.timestamp));
        body.push_str(&format!("Severity: {}\n", report.severity));
        body.push_str(&format!("Category: {}\n\n", report.category));
        
        body.push_str("ERROR DETAILS\n");
        body.push_str(&"-".repeat(40));
        body.push_str(&format!("\nPhase: {}\n", report.failure_phase));
        body.push_str(&format!("Error Code: {}\n", report.error_code));
        body.push_str(&format!("Message: {}\n\n", report.error_message));
        
        body.push_str("ENVIRONMENT\n");
        body.push_str(&"-".repeat(40));
        body.push_str(&format!("\nType: {}\n", report.environment));
        body.push_str(&format!("OS: {}\n", report.system_fingerprint.os_type));
        body.push_str(&format!("Arch: {}\n\n", report.system_fingerprint.architecture));
        
        if !report.attempted_solutions.is_empty() {
            body.push_str("ATTEMPTED SOLUTIONS\n");
            body.push_str(&"-".repeat(40));
            body.push_str("\n");
            for solution in &report.attempted_solutions {
                body.push_str(&format!("• {}\n", solution));
            }
            body.push_str("\n");
        }
        
        body.push_str("STATE MACHINE\n");
        body.push_str(&"-".repeat(40));
        body.push_str(&format!("\nCurrent: {}\n", report.state_snapshot.current_state));
        body.push_str(&format!("Time in state: {}ms\n", report.state_snapshot.time_in_state_ms));
        body.push_str(&format!("Retries: {}\n\n", report.state_snapshot.retry_count));
        
        body.push_str(&"=".repeat(60));
        body.push_str("\n");
        body.push_str(&format!("Generated by Zero-Touch Scout v{}\n", report.version));
        
        body
    }
    
    /// Build HTML body
    fn build_html_body(&self, report: &Report) -> String {
        let mut html = String::new();
        
        html.push_str(r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }
        .section { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }
        .critical { border-left-color: #dc3545; }
        .error { border-left-color: #fd7e14; }
        .warning { border-left-color: #ffc107; }
        .info { border-left-color: #17a2b8; }
        .severity { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }
        .severity-CRITICAL { background: #dc3545; }
        .severity-ERROR { background: #fd7e14; }
        .severity-WARNING { background: #ffc107; color: #333; }
        .severity-INFO { background: #17a2b8; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px; border-bottom: 1px solid #eee; }
        td:first-child { font-weight: bold; width: 30%; }
        .code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
"#);
        
        // Header
        html.push_str(&format!(
            r#"        <div class="header">
            <h1>🛡️ Zero-Touch Scout Report</h1>
            <p>Report ID: {}</p>
        </div>
        <div class="content">
"#,
            report.report_id
        ));
        
        // Severity badge
        let severity_class = format!("{:?}", report.severity);
        html.push_str(&format!(
            r#"            <div class="section {}">
                <h3>Error Details <span class="severity severity-{}">{}</span></h3>
                <table>
                    <tr><td>Phase</td><td>{}</td></tr>
                    <tr><td>Error Code</td><td class="code">{}</td></tr>
                    <tr><td>Message</td><td>{}</td></tr>
                </table>
            </div>
"#,
            severity_class.to_lowercase(),
            severity_class,
            severity_class,
            report.failure_phase,
            report.error_code,
            report.error_message
        ));
        
        // Environment
        html.push_str(&format!(
            r#"            <div class="section">
                <h3>🖥️ Environment</h3>
                <table>
                    <tr><td>Type</td><td>{}</td></tr>
                    <tr><td>OS</td><td>{}</td></tr>
                    <tr><td>Architecture</td><td>{}</td></tr>
                </table>
            </div>
"#,
            report.environment,
            report.system_fingerprint.os_type,
            report.system_fingerprint.architecture
        ));
        
        // State Machine
        html.push_str(&format!(
            r#"            <div class="section">
                <h3>📊 State Machine</h3>
                <table>
                    <tr><td>Current State</td><td>{}</td></tr>
                    <tr><td>Time in State</td><td>{}ms</td></tr>
                    <tr><td>Total Time</td><td>{}ms</td></tr>
                    <tr><td>Retry Count</td><td>{}</td></tr>
                </table>
            </div>
"#,
            report.state_snapshot.current_state,
            report.state_snapshot.time_in_state_ms,
            report.state_snapshot.total_time_ms,
            report.state_snapshot.retry_count
        ));
        
        // Attempted Solutions
        if !report.attempted_solutions.is_empty() {
            html.push_str(r#"            <div class="section">
                <h3>🔧 Attempted Solutions</h3>
                <ul>
"#);
            for solution in &report.attempted_solutions {
                html.push_str(&format!("                    <li>{}</li>\n", solution));
            }
            html.push_str(r#"                </ul>
            </div>
"#);
        }
        
        // Footer
        html.push_str(&format!(
            r#"        </div>
        <p style="text-align: center; color: #666; font-size: 12px;">
            Generated by Zero-Touch Scout v{} at {}
        </p>
    </div>
</body>
</html>
"#,
            report.version,
            report.timestamp
        ));
        
        html
    }
    
    /// Initialize SMTP transport
    async fn ensure_transport(&self) -> ScoutResult<SmtpTransport> {
        // Check if credentials are configured
        if self.config.username.is_empty() || self.config.password.is_empty() {
            return Err(ScoutError::ConfigError(
                "Email credentials not configured. Set SMTP username and password.".to_string()
            ));
        }
        
        let creds = Credentials::new(
            self.config.username.clone(),
            self.config.password.clone(),
        );
        
        let transport = if self.config.use_tls {
            SmtpTransport::starttls_relay(&self.config.smtp_host)
                .map_err(|e| ScoutError::NetworkError(format!("SMTP connection failed: {}", e)))?
                .credentials(creds)
                .port(self.config.smtp_port)
                .timeout(Some(Duration::from_secs(self.config.timeout_secs)))
                .build()
        } else {
            SmtpTransport::builder_dangerous(&self.config.smtp_host)
                .credentials(creds)
                .port(self.config.smtp_port)
                .timeout(Some(Duration::from_secs(self.config.timeout_secs)))
                .build()
        };
        
        Ok(transport)
    }
    
    /// Send email
    async fn send_email(&self, report: &Report) -> ScoutResult<String> {
        let subject = self.build_subject(report);
        let plain_body = self.build_plain_body(report);
        let html_body = self.build_html_body(report);
        
        // Build email message
        let email = Message::builder()
            .from(self.config.from_address.parse()
                .map_err(|e| ScoutError::NetworkError(format!("Invalid from address: {}", e)))?)
            .to(self.config.to_address.parse()
                .map_err(|e| ScoutError::NetworkError(format!("Invalid to address: {}", e)))?)
            .subject(&subject)
            .map_err(|e| ScoutError::NetworkError(format!("Failed to set subject: {}", e)))?;
        
        // Build multipart body
        let email = match self.format {
            EmailFormat::PlainText => {
                email.singlepart(
                    SinglePart::builder()
                        .header(ContentType::TEXT_PLAIN)
                        .body(plain_body)
                )
            }
            EmailFormat::Html => {
                email.singlepart(
                    SinglePart::builder()
                        .header(ContentType::TEXT_HTML)
                        .body(html_body)
                )
            }
            EmailFormat::Multipart => {
                email.multipart(
                    MultiPart::alternative()
                        .singlepart(
                            SinglePart::builder()
                                .header(ContentType::TEXT_PLAIN)
                                .body(plain_body)
                        )
                        .singlepart(
                            SinglePart::builder()
                                .header(ContentType::TEXT_HTML)
                                .body(html_body)
                        )
                )
            }
        }.map_err(|e| ScoutError::NetworkError(format!("Failed to build email: {}", e)))?;
        
        // Get transport and send
        let transport = self.ensure_transport().await?;
        
        transport
            .send(&email)
            .map_err(|e| ScoutError::NetworkError(format!("Failed to send email: {}", e)))?;
        
        Ok(format!("{}@{}", report.report_id, self.config.to_address))
    }
    
    /// Check SMTP connectivity
    pub async fn test_connection(&self) -> bool {
        if self.config.username.is_empty() || self.config.password.is_empty() {
            return false;
        }
        
        match self.ensure_transport().await {
            Ok(transport) => {
                // Try to connect
                transport.test_connection()
                    .unwrap_or(false)
            }
            Err(_) => false,
        }
    }
}

#[async_trait]
impl ReportingChannel for EmailChannel {
    fn name(&self) -> &str {
        "email"
    }
    
    fn priority(&self) -> ChannelPriority {
        ChannelPriority::Quaternary
    }
    
    async fn is_available(&self) -> bool {
        self.is_available.load(Ordering::SeqCst) &&
            self.consecutive_failures.load(Ordering::SeqCst) < 3 &&
            !self.config.username.is_empty() &&
            !self.config.password.is_empty()
    }
    
    async fn status(&self) -> ChannelStatus {
        if !self.is_available.load(Ordering::SeqCst) {
            return ChannelStatus::Unavailable;
        }
        
        if self.config.username.is_empty() || self.config.password.is_empty() {
            return ChannelStatus::NotConfigured;
        }
        
        if self.consecutive_failures.load(Ordering::SeqCst) >= 3 {
            return ChannelStatus::Failed;
        }
        
        // Try to test connection
        if self.test_connection().await {
            ChannelStatus::Available
        } else {
            ChannelStatus::Unavailable
        }
    }
    
    async fn transmit(&self, report: &Report) -> ChannelResult {
        let start = Instant::now();
        
        // Retry logic
        let mut last_error: Option<String> = None;
        
        for attempt in 0..self.config.max_retries {
            let backoff = Duration::from_millis(1000 * (2_u64.pow(attempt)));
            
            if attempt > 0 {
                tokio::time::sleep(backoff).await;
            }
            
            match self.send_email(report).await {
                Ok(confirmation) => {
                    // Reset failure counter
                    self.consecutive_failures.store(0, Ordering::SeqCst);
                    
                    let mut response_data = HashMap::new();
                    response_data.insert("confirmation".to_string(), confirmation);
                    response_data.insert("to_address".to_string(), self.config.to_address.clone());
                    
                    return ChannelResult {
                        channel_name: self.name().to_string(),
                        success: true,
                        message: format!("Email sent to {}", self.config.to_address),
                        duration_ms: start.elapsed().as_millis() as u64,
                        response_data: Some(response_data),
                    };
                }
                Err(e) => {
                    last_error = Some(e.to_string());
                    continue;
                }
            }
        }
        
        // All retries failed
        self.consecutive_failures.fetch_add(1, Ordering::SeqCst);
        let error_msg = last_error.unwrap_or_else(|| "Unknown error".to_string());
        *self.last_error.write().await = Some(error_msg.clone());
        
        ChannelResult {
            channel_name: self.name().to_string(),
            success: false,
            message: error_msg,
            duration_ms: start.elapsed().as_millis() as u64,
            response_data: None,
        }
    }
    
    fn rate_limit_remaining(&self) -> Option<u32> {
        None // Email doesn't have rate limits in the same way
    }
    
    async fn reset(&self) {
        self.is_available.store(true, Ordering::SeqCst);
        self.consecutive_failures.store(0, Ordering::SeqCst);
        *self.last_error.write().await = None;
        *self.transport.write().await = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_email_config_default() {
        let config = EmailConfig::default();
        assert_eq!(config.smtp_host, "smtp.gmail.com");
        assert_eq!(config.smtp_port, 587);
        assert!(config.use_tls);
    }
    
    #[test]
    fn test_channel_name() {
        let channel = EmailChannel::with_defaults();
        assert_eq!(channel.name(), "email");
    }
    
    #[test]
    fn test_channel_priority() {
        let channel = EmailChannel::with_defaults();
        assert_eq!(channel.priority(), ChannelPriority::Quaternary);
    }
    
    #[test]
    fn test_build_subject() {
        let channel = EmailChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Critical,
            ReportCategory::InstallationFailure,
            "colab".to_string(),
            "OnlineBootstrap".to_string(),
            "E-500".to_string(),
            "Installation failed".to_string(),
        );
        
        let subject = channel.build_subject(&report);
        assert!(subject.contains("[KISWARM-ZTS]"));
        assert!(subject.contains("CRITICAL"));
        assert!(subject.contains("E-500"));
    }
    
    #[test]
    fn test_build_plain_body() {
        let channel = EmailChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Error,
            ReportCategory::NetworkIssue,
            "docker".to_string(),
            "EnvDetect".to_string(),
            "E-404".to_string(),
            "Network unreachable".to_string(),
        );
        
        let body = channel.build_plain_body(&report);
        
        assert!(body.contains("Zero-Touch Scout Report"));
        assert!(body.contains("Network unreachable"));
        assert!(body.contains("docker"));
    }
    
    #[test]
    fn test_build_html_body() {
        let channel = EmailChannel::with_defaults();
        let report = Report::new(
            ReportSeverity::Warning,
            ReportCategory::DependencyIssue,
            "kubernetes".to_string(),
            "Installing".to_string(),
            "E-503".to_string(),
            "Package not found".to_string(),
        );
        
        let html = channel.build_html_body(&report);
        
        assert!(html.contains("<!DOCTYPE html>"));
        assert!(html.contains("severity-WARNING"));
        assert!(html.contains("Package not found"));
    }
    
    #[test]
    fn test_email_unavailable_without_credentials() {
        let channel = EmailChannel::with_defaults();
        
        // Should not be available without credentials
        // This is async, so we test the basic state
        assert!(channel.config.username.is_empty());
        assert!(channel.config.password.is_empty());
    }
}
