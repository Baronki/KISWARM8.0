//! State Machine for KISWARM Zero-Touch Scout
//! 
//! This module implements a formal finite state machine (FSM) for the installation
//! process. The state machine ensures:
//! - Defined state transitions
//! - Timeout handling per state
//! - Retry logic with backoff
//! - Failure escalation

use crate::config::{RetryConfig, ScoutConfig};
use crate::environment::EnvironmentProfile;
use crate::logging::AuditLogger;
use crate::{ScoutError, ScoutResult};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::time::{Duration, Instant};

/// All possible states of the Zero-Touch Scout
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ScoutState {
    /// Initial state - entry point
    Init,
    
    /// Self-verification in progress
    SelfVerify,
    
    /// Environment detection in progress
    EnvDetect,
    
    /// Environment-specific configuration
    EnvConfig,
    
    /// Parallel scan for sources
    ParallelScan,
    
    /// Online bootstrap path active
    OnlineBootstrap,
    
    /// Offline Ark bootstrap path active
    ArkBootstrap,
    
    /// Race-to-completion arbiter
    RaceArbiter,
    
    /// Installation in progress
    Installing,
    
    /// Verification in progress
    Verifying,
    
    /// Installation successful
    Success,
    
    /// Installation failed (recoverable)
    Failure,
    
    /// Exponential backoff in progress
    Backoff,
    
    /// Retrying installation
    Retry,
    
    /// Reporting to community mesh
    Reporting,
    
    /// Trying alternative sources
    AlternativeSource,
    
    /// Escalated to human intervention
    Escalated,
    
    /// Operational mode (post-install)
    Operational,
    
    /// Aborted by user or system
    Aborted,
}

impl fmt::Display for ScoutState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ScoutState::Init => write!(f, "INIT"),
            ScoutState::SelfVerify => write!(f, "SELF_VERIFY"),
            ScoutState::EnvDetect => write!(f, "ENV_DETECT"),
            ScoutState::EnvConfig => write!(f, "ENV_CONFIG"),
            ScoutState::ParallelScan => write!(f, "PARALLEL_SCAN"),
            ScoutState::OnlineBootstrap => write!(f, "ONLINE_BOOTSTRAP"),
            ScoutState::ArkBootstrap => write!(f, "ARK_BOOTSTRAP"),
            ScoutState::RaceArbiter => write!(f, "RACE_ARBITER"),
            ScoutState::Installing => write!(f, "INSTALLING"),
            ScoutState::Verifying => write!(f, "VERIFYING"),
            ScoutState::Success => write!(f, "SUCCESS"),
            ScoutState::Failure => write!(f, "FAILURE"),
            ScoutState::Backoff => write!(f, "BACKOFF"),
            ScoutState::Retry => write!(f, "RETRY"),
            ScoutState::Reporting => write!(f, "REPORTING"),
            ScoutState::AlternativeSource => write!(f, "ALTERNATIVE_SOURCE"),
            ScoutState::Escalated => write!(f, "ESCALATED"),
            ScoutState::Operational => write!(f, "OPERATIONAL"),
            ScoutState::Aborted => write!(f, "ABORTED"),
        }
    }
}

impl std::str::FromStr for ScoutState {
    type Err = ScoutError;
    
    fn from_str(s: &str) -> ScoutResult<Self> {
        match s.to_uppercase().as_str() {
            "INIT" => Ok(ScoutState::Init),
            "SELF_VERIFY" => Ok(ScoutState::SelfVerify),
            "ENV_DETECT" => Ok(ScoutState::EnvDetect),
            "ENV_CONFIG" => Ok(ScoutState::EnvConfig),
            "PARALLEL_SCAN" => Ok(ScoutState::ParallelScan),
            "ONLINE_BOOTSTRAP" => Ok(ScoutState::OnlineBootstrap),
            "ARK_BOOTSTRAP" => Ok(ScoutState::ArkBootstrap),
            "RACE_ARBITER" => Ok(ScoutState::RaceArbiter),
            "INSTALLING" => Ok(ScoutState::Installing),
            "VERIFYING" => Ok(ScoutState::Verifying),
            "SUCCESS" => Ok(ScoutState::Success),
            "FAILURE" => Ok(ScoutState::Failure),
            "BACKOFF" => Ok(ScoutState::Backoff),
            "RETRY" => Ok(ScoutState::Retry),
            "REPORTING" => Ok(ScoutState::Reporting),
            "ALTERNATIVE_SOURCE" => Ok(ScoutState::AlternativeSource),
            "ESCALATED" => Ok(ScoutState::Escalated),
            "OPERATIONAL" => Ok(ScoutState::Operational),
            "ABORTED" => Ok(ScoutState::Aborted),
            _ => Err(ScoutError::ConfigError(format!("Unknown state: {}", s))),
        }
    }
}

/// State transition result
#[derive(Debug, Clone)]
pub enum TransitionResult {
    /// Transition successful, moved to new state
    Success(ScoutState),
    
    /// Transition failed, error occurred
    Failed(ScoutError),
    
    /// Need to wait before continuing
    Wait(Duration),
    
    /// Terminal state reached
    Terminal,
}

/// Valid state transitions
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Transition {
    // Normal flow
    InitToSelfVerify,
    SelfVerifyToEnvDetect,
    EnvDetectToEnvConfig,
    EnvConfigToParallelScan,
    ParallelScanToOnlineBootstrap,
    ParallelScanToArkBootstrap,
    ParallelScanToRaceArbiter,
    RaceArbiterToInstalling,
    InstallingToVerifying,
    VerifyingToSuccess,
    SuccessToOperational,
    
    // Failure handling
    SelfVerifyToAborted,
    EnvDetectToFailure,
    OnlineBootstrapToFailure,
    ArkBootstrapToFailure,
    InstallingToFailure,
    VerifyingToFailure,
    
    // Retry flow
    FailureToBackoff,
    BackoffToRetry,
    RetryToEnvConfig,
    RetryToReporting,
    
    // Reporting flow
    FailureToReporting,
    ReportingToAlternativeSource,
    ReportingToEscalated,
    
    // Alternative source flow
    AlternativeSourceToOnlineBootstrap,
    AlternativeSourceToArkBootstrap,
    AlternativeSourceToEscalated,
    
    // Escalation
    EscalatedToAborted,
}

impl Transition {
    /// Get the from and to states for this transition
    pub fn states(&self) -> (ScoutState, ScoutState) {
        match self {
            Transition::InitToSelfVerify => (ScoutState::Init, ScoutState::SelfVerify),
            Transition::SelfVerifyToEnvDetect => (ScoutState::SelfVerify, ScoutState::EnvDetect),
            Transition::EnvDetectToEnvConfig => (ScoutState::EnvDetect, ScoutState::EnvConfig),
            Transition::EnvConfigToParallelScan => (ScoutState::EnvConfig, ScoutState::ParallelScan),
            Transition::ParallelScanToOnlineBootstrap => (ScoutState::ParallelScan, ScoutState::OnlineBootstrap),
            Transition::ParallelScanToArkBootstrap => (ScoutState::ParallelScan, ScoutState::ArkBootstrap),
            Transition::ParallelScanToRaceArbiter => (ScoutState::ParallelScan, ScoutState::RaceArbiter),
            Transition::RaceArbiterToInstalling => (ScoutState::RaceArbiter, ScoutState::Installing),
            Transition::InstallingToVerifying => (ScoutState::Installing, ScoutState::Verifying),
            Transition::VerifyingToSuccess => (ScoutState::Verifying, ScoutState::Success),
            Transition::SuccessToOperational => (ScoutState::Success, ScoutState::Operational),
            
            Transition::SelfVerifyToAborted => (ScoutState::SelfVerify, ScoutState::Aborted),
            Transition::EnvDetectToFailure => (ScoutState::EnvDetect, ScoutState::Failure),
            Transition::OnlineBootstrapToFailure => (ScoutState::OnlineBootstrap, ScoutState::Failure),
            Transition::ArkBootstrapToFailure => (ScoutState::ArkBootstrap, ScoutState::Failure),
            Transition::InstallingToFailure => (ScoutState::Installing, ScoutState::Failure),
            Transition::VerifyingToFailure => (ScoutState::Verifying, ScoutState::Failure),
            
            Transition::FailureToBackoff => (ScoutState::Failure, ScoutState::Backoff),
            Transition::BackoffToRetry => (ScoutState::Backoff, ScoutState::Retry),
            Transition::RetryToEnvConfig => (ScoutState::Retry, ScoutState::EnvConfig),
            Transition::RetryToReporting => (ScoutState::Retry, ScoutState::Reporting),
            
            Transition::FailureToReporting => (ScoutState::Failure, ScoutState::Reporting),
            Transition::ReportingToAlternativeSource => (ScoutState::Reporting, ScoutState::AlternativeSource),
            Transition::ReportingToEscalated => (ScoutState::Reporting, ScoutState::Escalated),
            
            Transition::AlternativeSourceToOnlineBootstrap => (ScoutState::AlternativeSource, ScoutState::OnlineBootstrap),
            Transition::AlternativeSourceToArkBootstrap => (ScoutState::AlternativeSource, ScoutState::ArkBootstrap),
            Transition::AlternativeSourceToEscalated => (ScoutState::AlternativeSource, ScoutState::Escalated),
            
            Transition::EscalatedToAborted => (ScoutState::Escalated, ScoutState::Aborted),
        }
    }
    
    /// Check if a transition from one state to another is valid
    pub fn is_valid(from: ScoutState, to: ScoutState) -> bool {
        // Define all valid transitions
        let valid_transitions: &[Transition] = &[
            Transition::InitToSelfVerify,
            Transition::SelfVerifyToEnvDetect,
            Transition::SelfVerifyToAborted,
            Transition::EnvDetectToEnvConfig,
            Transition::EnvDetectToFailure,
            Transition::EnvConfigToParallelScan,
            Transition::ParallelScanToOnlineBootstrap,
            Transition::ParallelScanToArkBootstrap,
            Transition::ParallelScanToRaceArbiter,
            Transition::RaceArbiterToInstalling,
            Transition::OnlineBootstrapToFailure,
            Transition::ArkBootstrapToFailure,
            Transition::InstallingToVerifying,
            Transition::InstallingToFailure,
            Transition::VerifyingToSuccess,
            Transition::VerifyingToFailure,
            Transition::SuccessToOperational,
            Transition::FailureToBackoff,
            Transition::FailureToReporting,
            Transition::BackoffToRetry,
            Transition::RetryToEnvConfig,
            Transition::RetryToReporting,
            Transition::ReportingToAlternativeSource,
            Transition::ReportingToEscalated,
            Transition::AlternativeSourceToOnlineBootstrap,
            Transition::AlternativeSourceToArkBootstrap,
            Transition::AlternativeSourceToEscalated,
            Transition::EscalatedToAborted,
        ];
        
        valid_transitions.iter().any(|t| t.states() == (from, to))
    }
}

/// State configuration (timeout, retry policy, etc.)
#[derive(Debug, Clone)]
pub struct StateConfig {
    /// State name
    pub state: ScoutState,
    
    /// Timeout for this state
    pub timeout: Duration,
    
    /// Maximum retries for this state
    pub max_retries: u32,
    
    /// Whether this state is critical (failure escalates)
    pub is_critical: bool,
    
    /// Description for logging
    pub description: &'static str,
}

impl StateConfig {
    /// Get configuration for a state
    pub fn for_state(state: ScoutState) -> Self {
        match state {
            ScoutState::Init => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: true,
                description: "Initialization and entry point",
            },
            ScoutState::SelfVerify => Self {
                state,
                timeout: Duration::from_secs(10),
                max_retries: 0,
                is_critical: true,
                description: "Binary self-verification",
            },
            ScoutState::EnvDetect => Self {
                state,
                timeout: Duration::from_secs(30),
                max_retries: 3,
                is_critical: false,
                description: "Environment detection and profiling",
            },
            ScoutState::EnvConfig => Self {
                state,
                timeout: Duration::from_secs(30),
                max_retries: 2,
                is_critical: false,
                description: "Environment-specific configuration",
            },
            ScoutState::ParallelScan => Self {
                state,
                timeout: Duration::from_secs(30),
                max_retries: 2,
                is_critical: false,
                description: "Parallel source scanning",
            },
            ScoutState::OnlineBootstrap => Self {
                state,
                timeout: Duration::from_secs(300),
                max_retries: 3,
                is_critical: false,
                description: "Online bootstrap from internet",
            },
            ScoutState::ArkBootstrap => Self {
                state,
                timeout: Duration::from_secs(120),
                max_retries: 2,
                is_critical: false,
                description: "Offline bootstrap from Ark cache",
            },
            ScoutState::RaceArbiter => Self {
                state,
                timeout: Duration::from_secs(300),
                max_retries: 0,
                is_critical: false,
                description: "Race-to-completion arbiter",
            },
            ScoutState::Installing => Self {
                state,
                timeout: Duration::from_secs(600),
                max_retries: 2,
                is_critical: false,
                description: "KISWARM installation",
            },
            ScoutState::Verifying => Self {
                state,
                timeout: Duration::from_secs(60),
                max_retries: 2,
                is_critical: false,
                description: "Installation verification",
            },
            ScoutState::Success => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: false,
                description: "Installation successful",
            },
            ScoutState::Failure => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: false,
                description: "Installation failed",
            },
            ScoutState::Backoff => Self {
                state,
                timeout: Duration::from_secs(60),
                max_retries: 0,
                is_critical: false,
                description: "Exponential backoff",
            },
            ScoutState::Retry => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: false,
                description: "Retry decision",
            },
            ScoutState::Reporting => Self {
                state,
                timeout: Duration::from_secs(60),
                max_retries: 3,
                is_critical: false,
                description: "Reporting to community mesh",
            },
            ScoutState::AlternativeSource => Self {
                state,
                timeout: Duration::from_secs(180),
                max_retries: 2,
                is_critical: false,
                description: "Trying alternative sources",
            },
            ScoutState::Escalated => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: true,
                description: "Escalated to human",
            },
            ScoutState::Operational => Self {
                state,
                timeout: Duration::from_secs(0), // No timeout
                max_retries: 0,
                is_critical: false,
                description: "Operational mode",
            },
            ScoutState::Aborted => Self {
                state,
                timeout: Duration::from_secs(5),
                max_retries: 0,
                is_critical: true,
                description: "Installation aborted",
            },
        }
    }
}

/// State machine context - data carried between states
#[derive(Debug)]
pub struct StateContext {
    /// Current environment profile
    pub environment: Option<EnvironmentProfile>,
    
    /// Current retry count
    pub retry_count: u32,
    
    /// Maximum retries allowed
    pub max_retries: u32,
    
    /// Error history
    pub errors: Vec<ScoutError>,
    
    /// Installation start time
    pub started_at: Instant,
    
    /// State entered time
    pub state_entered_at: Instant,
    
    /// Last error encountered
    pub last_error: Option<ScoutError>,
    
    /// Bootstrap method used (online or ark)
    pub bootstrap_method: Option<String>,
    
    /// Installation directory
    pub install_dir: Option<std::path::PathBuf>,
}

impl Default for StateContext {
    fn default() -> Self {
        Self {
            environment: None,
            retry_count: 0,
            max_retries: 3,
            errors: Vec::new(),
            started_at: Instant::now(),
            state_entered_at: Instant::now(),
            last_error: None,
            bootstrap_method: None,
            install_dir: None,
        }
    }
}

/// The main state machine
pub struct StateMachine {
    /// Current state
    current_state: ScoutState,
    
    /// Previous state (for transitions)
    previous_state: Option<ScoutState>,
    
    /// State context
    context: StateContext,
    
    /// Configuration
    config: ScoutConfig,
    
    /// Audit logger
    logger: Option<AuditLogger>,
}

impl StateMachine {
    /// Create a new state machine
    pub fn new(config: ScoutConfig) -> Self {
        Self {
            current_state: ScoutState::Init,
            previous_state: None,
            context: StateContext::default(),
            config,
            logger: None,
        }
    }
    
    /// Set the audit logger
    pub fn with_logger(mut self, logger: AuditLogger) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Get current state
    pub fn current_state(&self) -> ScoutState {
        self.current_state
    }
    
    /// Get context reference
    pub fn context(&self) -> &StateContext {
        &self.context
    }
    
    /// Get mutable context reference
    pub fn context_mut(&mut self) -> &mut StateContext {
        &mut self.context
    }
    
    /// Transition to a new state
    pub fn transition_to(&mut self, new_state: ScoutState) -> ScoutResult<()> {
        // Validate transition
        if !Transition::is_valid(self.current_state, new_state) {
            return Err(ScoutError::InvalidStateTransition {
                from: self.current_state.to_string(),
                to: new_state.to_string(),
            });
        }
        
        // Log transition
        if let Some(logger) = &self.logger {
            logger.state_transition(&self.current_state.to_string(), &new_state.to_string())?;
        }
        
        // Update state
        self.previous_state = Some(self.current_state);
        self.current_state = new_state;
        self.context.state_entered_at = Instant::now();
        
        Ok(())
    }
    
    /// Check if current state has timed out
    pub fn check_timeout(&self) -> bool {
        let state_config = StateConfig::for_state(self.current_state);
        if state_config.timeout == Duration::ZERO {
            return false; // No timeout
        }
        
        self.context.state_entered_at.elapsed() > state_config.timeout
    }
    
    /// Get remaining time in current state
    pub fn remaining_time(&self) -> Option<Duration> {
        let state_config = StateConfig::for_state(self.current_state);
        if state_config.timeout == Duration::ZERO {
            return None;
        }
        
        let elapsed = self.context.state_entered_at.elapsed();
        if elapsed >= state_config.timeout {
            Some(Duration::ZERO)
        } else {
            Some(state_config.timeout - elapsed)
        }
    }
    
    /// Handle an error in current state
    pub fn handle_error(&mut self, error: ScoutError) -> ScoutResult<ScoutState> {
        // Record error
        self.context.errors.push(error.clone());
        self.context.last_error = Some(error.clone());
        
        // Log error
        if let Some(logger) = &self.logger {
            logger.error(
                &error.to_string(),
                error.error_code(),
                serde_json::json!({
                    "state": self.current_state.to_string(),
                    "retry_count": self.context.retry_count,
                }),
            )?;
        }
        
        // Determine next state based on error and current state
        let state_config = StateConfig::for_state(self.current_state);
        
        if error.should_retry() && self.context.retry_count < self.config.retry.max_retries {
            // Can retry
            self.context.retry_count += 1;
            Ok(ScoutState::Backoff)
        } else if state_config.is_critical {
            // Critical failure
            Ok(ScoutState::Escalated)
        } else {
            // Non-critical failure, try alternative path
            Ok(ScoutState::Failure)
        }
    }
    
    /// Check if state machine is in a terminal state
    pub fn is_terminal(&self) -> bool {
        matches!(
            self.current_state,
            ScoutState::Operational | ScoutState::Aborted
        )
    }
    
    /// Check if state machine is in a success state
    pub fn is_success(&self) -> bool {
        matches!(
            self.current_state,
            ScoutState::Success | ScoutState::Operational
        )
    }
    
    /// Get the current state's configuration
    pub fn state_config(&self) -> StateConfig {
        StateConfig::for_state(self.current_state)
    }
    
    /// Get total elapsed time since start
    pub fn total_elapsed(&self) -> Duration {
        self.context.started_at.elapsed()
    }
    
    /// Get state history as a vector
    pub fn state_history(&self) -> Vec<(ScoutState, ScoutState)> {
        // This would need to be tracked properly in a real implementation
        Vec::new()
    }
    
    /// Generate a summary of the state machine's journey
    pub fn summary(&self) -> String {
        let total_errors = self.context.errors.len();
        let retry_count = self.context.retry_count;
        
        let status = if self.is_success() {
            "SUCCESS"
        } else if self.is_terminal() {
            "ABORTED"
        } else {
            "IN_PROGRESS"
        };
        
        format!(
            "State Machine Summary\n\
             ====================\n\
             Status: {}\n\
             Current State: {}\n\
             Previous State: {}\n\
             Total Errors: {}\n\
             Retries: {}/{}\n\
             Elapsed: {:.1}s",
            status,
            self.current_state,
            self.previous_state.map(|s| s.to_string()).unwrap_or_else(|| "None".to_string()),
            total_errors,
            retry_count,
            self.config.retry.max_retries,
            self.total_elapsed().as_secs_f64()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_state_machine_creation() {
        let config = ScoutConfig::default();
        let sm = StateMachine::new(config);
        
        assert_eq!(sm.current_state(), ScoutState::Init);
        assert!(!sm.is_terminal());
    }
    
    #[test]
    fn test_valid_transition() {
        assert!(Transition::is_valid(ScoutState::Init, ScoutState::SelfVerify));
        assert!(Transition::is_valid(ScoutState::SelfVerify, ScoutState::EnvDetect));
        assert!(!Transition::is_valid(ScoutState::Init, ScoutState::Success));
    }
    
    #[test]
    fn test_transition() {
        let config = ScoutConfig::default();
        let mut sm = StateMachine::new(config);
        
        // Valid transition
        sm.transition_to(ScoutState::SelfVerify).unwrap();
        assert_eq!(sm.current_state(), ScoutState::SelfVerify);
        
        // Invalid transition
        let result = sm.transition_to(ScoutState::Success);
        assert!(result.is_err());
    }
    
    #[test]
    fn test_state_config() {
        let config = StateConfig::for_state(ScoutState::OnlineBootstrap);
        assert_eq!(config.timeout, Duration::from_secs(300));
        assert_eq!(config.max_retries, 3);
    }
    
    #[test]
    fn test_timeout_check() {
        let config = ScoutConfig::default();
        let mut sm = StateMachine::new(config);
        
        sm.context.state_entered_at = Instant::now() - Duration::from_secs(10);
        
        // Init state has 5s timeout
        assert!(sm.check_timeout());
    }
}
