//! KISWARM Zero-Touch Scout Library
//!
//! This library provides the core functionality for the Zero-Touch Scout binary.
//! It can also be used as a library for embedding KISWARM installation capabilities
//! into other applications.
//!
//! # Modules
//!
//! - `config` - Configuration management
//! - `environment` - Environment detection for 6 target platforms
//! - `error` - Error types with severity levels
//! - `logging` - Audit logging
//! - `network` - HTTP client with circuit breaker
//! - `bootstrap` - Parallel bootstrap with race arbiter
//! - `state_machine` - 18-state finite state machine
//! - `reporting` - 5-channel community reporting mesh
//! - `source_failover` - 5-level source failover system

pub mod config;
pub mod environment;
pub mod error;
pub mod logging;
pub mod network;
pub mod bootstrap;
pub mod state_machine;
pub mod reporting;
pub mod source_failover;

// Re-export main types
pub use config::{ScoutConfig, BootstrapConfig, NetworkConfig, RetryConfig};
pub use environment::{Environment, EnvironmentDetector, EnvironmentProfile, HardwareProfile, OSFingerprint};
pub use error::{ScoutError, ScoutResult, ErrorSeverity};
pub use logging::AuditLogger;
pub use network::{NetworkClient, CircuitBreaker, CircuitState, MultiSourceDownloader, DownloadSource, SourceType};
pub use bootstrap::{BootstrapMethod, BootstrapResult, ArkManager, ArkManifest, OnlineBootstrap, ArkBootstrap, RaceArbiter, BootstrapOrchestrator};
pub use state_machine::{ScoutState, StateMachine, StateConfig, StateContext};

// Re-export source failover types
pub use source_failover::{
    SourceLevel, SourceHealth, Artifact, ArtifactType, FetchResult,
    FailoverCoordinator,
};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Scout version information
pub fn version_info() -> String {
    format!(
        "KISWARM Zero-Touch Scout v{} ({})",
        VERSION,
        std::env::consts::ARCH
    )
}
