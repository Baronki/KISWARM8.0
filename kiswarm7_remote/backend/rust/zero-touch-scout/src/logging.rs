//! Audit Logging System for KISWARM Zero-Touch Scout
//! 
//! This module provides comprehensive audit logging with:
//! - JSON Lines format for easy parsing
//! - Chronological integrity
//! - Tamper-evident log entries
//! - Multiple output destinations

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::Mutex;

/// Audit log entry structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    /// Unique entry ID (sequential)
    pub entry_id: u64,
    
    /// ISO 8601 timestamp with microsecond precision
    pub timestamp: DateTime<Utc>,
    
    /// Log level: TRACE, DEBUG, INFO, WARN, ERROR, FATAL
    pub level: String,
    
    /// Current state machine state
    pub state: String,
    
    /// Current phase of operation
    pub phase: String,
    
    /// Human-readable message
    pub message: String,
    
    /// Error code if applicable
    pub error_code: Option<String>,
    
    /// Additional structured details
    pub details: serde_json::Value,
    
    /// Hash chain (previous entry hash for tamper detection)
    pub prev_hash: Option<String>,
    
    /// Hash of this entry
    pub hash: String,
}

/// Audit logger with file output and rotation
pub struct AuditLogger {
    /// Output file path
    file_path: PathBuf,
    
    /// Current file handle
    file: Option<Arc<Mutex<std::fs::File>>>,
    
    /// Entry counter for this session
    entry_counter: Arc<Mutex<u64>>,
    
    /// Previous entry hash (for chain integrity)
    prev_hash: Arc<Mutex<Option<String>>>,
    
    /// Current state machine state
    current_state: Arc<Mutex<String>>,
    
    /// Current phase
    current_phase: Arc<Mutex<String>>,
}

impl AuditLogger {
    /// Create a new audit logger
    pub fn new(file_path: PathBuf) -> crate::ScoutResult<Self> {
        // Ensure parent directory exists
        if let Some(parent) = file_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|_| crate::ScoutError::DirectoryCreationFailed { 
                    path: parent.to_path_buf() 
                })?;
        }
        
        // Open or create file
        let file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&file_path)
            .map_err(|_| crate::ScoutError::FileWriteFailed { 
                path: file_path.clone() 
            })?;
        
        Ok(Self {
            file_path,
            file: Some(Arc::new(Mutex::new(file))),
            entry_counter: Arc::new(Mutex::new(0)),
            prev_hash: Arc::new(Mutex::new(None)),
            current_state: Arc::new(Mutex::new("INIT".to_string())),
            current_phase: Arc::new(Mutex::new("startup".to_string())),
        })
    }
    
    /// Create a null logger (no file output)
    pub fn null() -> Self {
        Self {
            file_path: PathBuf::from("/dev/null"),
            file: None,
            entry_counter: Arc::new(Mutex::new(0)),
            prev_hash: Arc::new(Mutex::new(None)),
            current_state: Arc::new(Mutex::new("INIT".to_string())),
            current_phase: Arc::new(Mutex::new("startup".to_string())),
        }
    }
    
    /// Log an audit entry
    pub fn log(
        &self,
        level: &str,
        message: &str,
        error_code: Option<&str>,
        details: serde_json::Value,
    ) -> crate::ScoutResult<()> {
        let mut counter = self.entry_counter.lock().unwrap();
        *counter += 1;
        
        let mut prev_hash = self.prev_hash.lock().unwrap();
        let current_state = self.current_state.lock().unwrap();
        let current_phase = self.current_phase.lock().unwrap();
        
        let timestamp = Utc::now();
        
        // Create entry without hash
        let entry_without_hash = AuditEntryWithoutHash {
            entry_id: *counter,
            timestamp,
            level: level.to_string(),
            state: current_state.clone(),
            phase: current_phase.clone(),
            message: message.to_string(),
            error_code: error_code.map(|s| s.to_string()),
            details: details.clone(),
            prev_hash: prev_hash.clone(),
        };
        
        // Calculate hash
        let entry_json = serde_json::to_string(&entry_without_hash)
            .map_err(|e| crate::ScoutError::JsonError(e.to_string()))?;
        let hash = sha256_hash(&entry_json);
        
        // Create full entry
        let entry = AuditEntry {
            entry_id: entry_without_hash.entry_id,
            timestamp: entry_without_hash.timestamp,
            level: entry_without_hash.level,
            state: entry_without_hash.state,
            phase: entry_without_hash.phase,
            message: entry_without_hash.message,
            error_code: entry_without_hash.error_code,
            details: entry_without_hash.details,
            prev_hash: entry_without_hash.prev_hash,
            hash,
        };
        
        // Write to file
        if let Some(file) = &self.file {
            let mut file = file.lock().unwrap();
            let json_line = serde_json::to_string(&entry)
                .map_err(|e| crate::ScoutError::JsonError(e.to_string()))?;
            writeln!(file, "{}", json_line)
                .map_err(|e| crate::ScoutError::IoError(e.to_string()))?;
        }
        
        // Update previous hash for next entry
        *prev_hash = Some(entry.hash);
        
        Ok(())
    }
    
    /// Update current state
    pub fn set_state(&self, state: &str) {
        let mut current_state = self.current_state.lock().unwrap();
        *current_state = state.to_string();
    }
    
    /// Update current phase
    pub fn set_phase(&self, phase: &str) {
        let mut current_phase = self.current_phase.lock().unwrap();
        *current_phase = phase.to_string();
    }
    
    /// Log an INFO message
    pub fn info(&self, message: &str, details: serde_json::Value) -> crate::ScoutResult<()> {
        self.log("INFO", message, None, details)
    }
    
    /// Log a WARNING message
    pub fn warn(&self, message: &str, details: serde_json::Value) -> crate::ScoutResult<()> {
        self.log("WARN", message, None, details)
    }
    
    /// Log an ERROR message
    pub fn error(&self, message: &str, error_code: &str, details: serde_json::Value) -> crate::ScoutResult<()> {
        self.log("ERROR", message, Some(error_code), details)
    }
    
    /// Log a FATAL message
    pub fn fatal(&self, message: &str, error_code: &str, details: serde_json::Value) -> crate::ScoutResult<()> {
        self.log("FATAL", message, Some(error_code), details)
    }
    
    /// Log a phase transition
    pub fn phase_transition(&self, from: &str, to: &str) -> crate::ScoutResult<()> {
        self.info(
            &format!("Phase transition: {} -> {}", from, to),
            serde_json::json!({
                "transition": "phase",
                "from": from,
                "to": to
            }),
        )?;
        self.set_phase(to);
        Ok(())
    }
    
    /// Log a state transition
    pub fn state_transition(&self, from: &str, to: &str) -> crate::ScoutResult<()> {
        self.info(
            &format!("State transition: {} -> {}", from, to),
            serde_json::json!({
                "transition": "state",
                "from": from,
                "to": to
            }),
        )?;
        self.set_state(to);
        Ok(())
    }
    
    /// Verify log chain integrity
    pub fn verify_chain(&self) -> crate::ScoutResult<bool> {
        let file = std::fs::File::open(&self.file_path)
            .map_err(|e| crate::ScoutError::IoError(e.to_string()))?;
        
        use std::io::BufRead;
        let reader = std::io::BufReader::new(file);
        let mut prev_hash: Option<String> = None;
        
        for (line_num, line_result) in reader.lines().enumerate() {
            let line = line_result
                .map_err(|e| crate::ScoutError::IoError(e.to_string()))?;
            
            let entry: AuditEntry = serde_json::from_str(&line)
                .map_err(|e| crate::ScoutError::JsonError(
                    format!("Invalid log entry at line {}: {}", line_num + 1, e)
                ))?;
            
            // Verify chain
            if entry.entry_id > 1 {
                if entry.prev_hash != prev_hash {
                    return Ok(false);
                }
            }
            
            // Verify hash
            let entry_without_hash = AuditEntryWithoutHash {
                entry_id: entry.entry_id,
                timestamp: entry.timestamp,
                level: entry.level.clone(),
                state: entry.state.clone(),
                phase: entry.phase.clone(),
                message: entry.message.clone(),
                error_code: entry.error_code.clone(),
                details: entry.details.clone(),
                prev_hash: entry.prev_hash.clone(),
            };
            
            let entry_json = serde_json::to_string(&entry_without_hash)
                .map_err(|e| crate::ScoutError::JsonError(e.to_string()))?;
            let computed_hash = sha256_hash(&entry_json);
            
            if computed_hash != entry.hash {
                return Ok(false);
            }
            
            prev_hash = Some(entry.hash);
        }
        
        Ok(true)
    }
}

/// Entry without hash for hash computation
#[derive(Debug, Clone, Serialize, Deserialize)]
struct AuditEntryWithoutHash {
    pub entry_id: u64,
    pub timestamp: DateTime<Utc>,
    pub level: String,
    pub state: String,
    pub phase: String,
    pub message: String,
    pub error_code: Option<String>,
    pub details: serde_json::Value,
    pub prev_hash: Option<String>,
}

/// SHA-256 hash function
fn sha256_hash(input: &str) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_audit_logger_basic() {
        let dir = tempdir().unwrap();
        let log_path = dir.path().join("test.jsonl");
        
        let logger = AuditLogger::new(log_path.clone()).unwrap();
        
        logger.info("Test message", serde_json::json!({"key": "value"})).unwrap();
        logger.warn("Warning message", serde_json::json!({"warning": true})).unwrap();
        logger.error("Error message", "E001", serde_json::json!({"error": true})).unwrap();
        
        // Verify chain integrity
        assert!(logger.verify_chain().unwrap());
    }
    
    #[test]
    fn test_hash_chain() {
        let dir = tempdir().unwrap();
        let log_path = dir.path().join("chain.jsonl");
        
        let logger = AuditLogger::new(log_path.clone()).unwrap();
        
        // Log multiple entries
        for i in 0..10 {
            logger.info(&format!("Message {}", i), serde_json::json!({"index": i})).unwrap();
        }
        
        // Verify chain
        assert!(logger.verify_chain().unwrap());
    }
}
