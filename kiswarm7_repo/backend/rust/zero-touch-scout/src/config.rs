//! Configuration for KISWARM Zero-Touch Scout
//! 
//! This module defines all configuration structures and defaults.
//! Configuration can be loaded from file, environment variables, or command line.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::time::Duration;

/// Main configuration structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoutConfig {
    /// Binary verification settings
    pub verification: VerificationConfig,
    
    /// Network settings
    pub network: NetworkConfig,
    
    /// Bootstrap settings
    pub bootstrap: BootstrapConfig,
    
    /// Retry settings
    pub retry: RetryConfig,
    
    /// Logging settings
    pub logging: LoggingConfig,
    
    /// Installation paths
    pub paths: PathConfig,
    
    /// Resource requirements
    pub requirements: ResourceRequirements,
}

impl Default for ScoutConfig {
    fn default() -> Self {
        Self {
            verification: VerificationConfig::default(),
            network: NetworkConfig::default(),
            bootstrap: BootstrapConfig::default(),
            retry: RetryConfig::default(),
            logging: LoggingConfig::default(),
            paths: PathConfig::default(),
            requirements: ResourceRequirements::default(),
        }
    }
}

/// Binary verification configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationConfig {
    /// Enable signature verification
    pub verify_signature: bool,
    
    /// Enable integrity check
    pub verify_integrity: bool,
    
    /// Enable expiration check
    pub verify_expiration: bool,
    
    /// Binary expiration in days from build date
    pub expiration_days: u32,
    
    /// Path to public key for signature verification
    pub public_key_path: Option<PathBuf>,
}

impl Default for VerificationConfig {
    fn default() -> Self {
        Self {
            verify_signature: true,
            verify_integrity: true,
            verify_expiration: true,
            expiration_days: 365,
            public_key_path: None,
        }
    }
}

/// Network configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkConfig {
    /// Connection timeout in seconds
    pub connection_timeout_secs: u64,
    
    /// Read timeout in seconds
    pub read_timeout_secs: u64,
    
    /// Total operation timeout in seconds
    pub total_timeout_secs: u64,
    
    /// Maximum download speed in bytes/sec (0 = unlimited)
    pub max_download_speed: u64,
    
    /// User agent string
    pub user_agent: String,
    
    /// Enable TLS certificate verification
    pub verify_tls: bool,
    
    /// Path to CA certificates (None = system default)
    pub ca_cert_path: Option<PathBuf>,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            connection_timeout_secs: 30,
            read_timeout_secs: 60,
            total_timeout_secs: 300,
            max_download_speed: 0,
            user_agent: format!(
                "KISWARM-Scout/{} (Rust; {})",
                env!("CARGO_PKG_VERSION"),
                std::env::consts::OS
            ),
            verify_tls: true,
            ca_cert_path: None,
        }
    }
}

/// Bootstrap configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BootstrapConfig {
    /// Enable online bootstrap path
    pub enable_online: bool,
    
    /// Enable offline (Ark) bootstrap path
    pub enable_ark: bool,
    
    /// Run both paths in parallel (race to completion)
    pub parallel_bootstrap: bool,
    
    /// Maximum time for each bootstrap path in seconds
    pub max_bootstrap_time_secs: u64,
    
    /// GitHub repository URL
    pub github_url: String,
    
    /// GitHub mirror URLs
    pub github_mirrors: Vec<String>,
    
    /// CDN URLs
    pub cdn_urls: Vec<String>,
    
    /// IPFS gateway URLs
    pub ipfs_gateways: Vec<String>,
    
    /// Default Ark path
    pub default_ark_path: PathBuf,
    
    /// Additional Ark search paths
    pub ark_search_paths: Vec<PathBuf>,
}

impl Default for BootstrapConfig {
    fn default() -> Self {
        Self {
            enable_online: true,
            enable_ark: true,
            parallel_bootstrap: true,
            max_bootstrap_time_secs: 300,
            github_url: "https://github.com/Baronki/KISWARM6.0".to_string(),
            github_mirrors: vec![
                "https://github.com/Baronki2/KISWARM".to_string(),
                "https://gitlab.com/kiswarm/kiswarm".to_string(),
            ],
            cdn_urls: vec![
                "https://releases.kiswarm.io".to_string(),
                "https://kiswarm-releases.s3.amazonaws.com".to_string(),
            ],
            ipfs_gateways: vec![
                "https://ipfs.io".to_string(),
                "https://cloudflare-ipfs.com".to_string(),
            ],
            default_ark_path: PathBuf::from("/kiswarm-ark"),
            ark_search_paths: vec![
                PathBuf::from("/opt/kiswarm-ark"),
                PathBuf::from("/media/usb/kiswarm-ark"),
                PathBuf::from("/mnt/usb/kiswarm-ark"),
                PathBuf::from("~/kiswarm-ark"),
            ],
        }
    }
}

/// Retry configuration with exponential backoff
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryConfig {
    /// Maximum number of retries
    pub max_retries: u32,
    
    /// Initial delay in milliseconds
    pub initial_delay_ms: u64,
    
    /// Maximum delay in milliseconds
    pub max_delay_ms: u64,
    
    /// Exponential backoff multiplier
    pub multiplier: f64,
    
    /// Jitter percentage (0.0 - 1.0)
    pub jitter_percent: f64,
    
    /// Enable jitter
    pub enable_jitter: bool,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_retries: 3,
            initial_delay_ms: 1000,
            max_delay_ms: 60000,
            multiplier: 2.0,
            jitter_percent: 0.2,
            enable_jitter: true,
        }
    }
}

impl RetryConfig {
    /// Calculate delay for a given attempt with exponential backoff and jitter
    pub fn calculate_delay(&self, attempt: u32) -> Duration {
        use rand::Rng;
        
        // Exponential backoff
        let base_delay = self.initial_delay_ms as f64 
            * self.multiplier.powi(attempt as i32);
        
        // Cap at max
        let capped_delay = base_delay.min(self.max_delay_ms as f64);
        
        // Add jitter if enabled
        let final_delay = if self.enable_jitter {
            let mut rng = rand::thread_rng();
            let jitter = capped_delay * self.jitter_percent 
                * (rng.gen::<f64>() - 0.5) * 2.0;
            (capped_delay + jitter).max(0.0) as u64
        } else {
            capped_delay as u64
        };
        
        Duration::from_millis(final_delay)
    }
}

/// Logging configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    /// Log level: trace, debug, info, warn, error
    pub level: String,
    
    /// Log format: json, text
    pub format: String,
    
    /// Log file path (None = stdout only)
    pub file_path: Option<PathBuf>,
    
    /// Maximum log file size in MB
    pub max_file_size_mb: u64,
    
    /// Number of log files to keep
    pub max_files: u32,
    
    /// Include timestamps in logs
    pub include_timestamp: bool,
    
    /// Include source location in logs
    pub include_source: bool,
}

impl Default for LoggingConfig {
    fn default() -> Self {
        Self {
            level: "info".to_string(),
            format: "json".to_string(),
            file_path: Some(PathBuf::from("~/logs/kiswarm-scout.jsonl")),
            max_file_size_mb: 100,
            max_files: 10,
            include_timestamp: true,
            include_source: true,
        }
    }
}

/// Path configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathConfig {
    /// Installation directory
    pub install_dir: PathBuf,
    
    /// Virtual environment directory
    pub venv_dir: PathBuf,
    
    /// Logs directory
    pub logs_dir: PathBuf,
    
    /// Configuration directory
    pub config_dir: PathBuf,
    
    /// Cache directory
    pub cache_dir: PathBuf,
    
    /// Temporary directory
    pub temp_dir: PathBuf,
}

impl Default for PathConfig {
    fn default() -> Self {
        let home = std::env::var("HOME")
            .unwrap_or_else(|_| "/root".to_string());
        
        Self {
            install_dir: PathBuf::from(format!("{}/KISWARM", home)),
            venv_dir: PathBuf::from(format!("{}/KISWARM/mem0_env", home)),
            logs_dir: PathBuf::from(format!("{}/logs", home)),
            config_dir: PathBuf::from(format!("{}/.kiswarm", home)),
            cache_dir: PathBuf::from(format!("{}/.kiswarm/cache", home)),
            temp_dir: PathBuf::from("/tmp/kiswarm-scout"),
        }
    }
}

/// Resource requirements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceRequirements {
    /// Minimum RAM in GB
    pub min_ram_gb: f64,
    
    /// Recommended RAM in GB
    pub recommended_ram_gb: f64,
    
    /// Minimum disk space in GB
    pub min_disk_gb: f64,
    
    /// Recommended disk space in GB
    pub recommended_disk_gb: f64,
    
    /// Minimum CPU cores
    pub min_cpu_cores: usize,
    
    /// Python version requirement
    pub python_version: String,
}

impl Default for ResourceRequirements {
    fn default() -> Self {
        Self {
            min_ram_gb: 8.0,
            recommended_ram_gb: 16.0,
            min_disk_gb: 20.0,
            recommended_disk_gb: 50.0,
            min_cpu_cores: 2,
            python_version: "3.8".to_string(),
        }
    }
}

/// Environment-specific configuration overrides
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentOverrides {
    /// Google Colab specific settings
    pub colab: EnvironmentConfig,
    
    /// Docker container settings
    pub docker: EnvironmentConfig,
    
    /// Kubernetes settings
    pub kubernetes: EnvironmentConfig,
    
    /// WSL2 settings
    pub wsl2: EnvironmentConfig,
    
    /// Cloud VM settings
    pub cloud_vm: EnvironmentConfig,
    
    /// Bare metal settings
    pub bare_metal: EnvironmentConfig,
}

impl Default for EnvironmentOverrides {
    fn default() -> Self {
        Self {
            colab: EnvironmentConfig::colab_default(),
            docker: EnvironmentConfig::docker_default(),
            kubernetes: EnvironmentConfig::kubernetes_default(),
            wsl2: EnvironmentConfig::wsl2_default(),
            cloud_vm: EnvironmentConfig::cloud_vm_default(),
            bare_metal: EnvironmentConfig::bare_metal_default(),
        }
    }
}

/// Per-environment configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentConfig {
    /// Use systemd for service management
    pub use_systemd: bool,
    
    /// Install directory override
    pub install_dir: Option<PathBuf>,
    
    /// Use --user flag for pip
    pub pip_user_flag: bool,
    
    /// Start services after installation
    pub start_services: bool,
    
    /// Enable persistence (survive reboots)
    pub enable_persistence: bool,
    
    /// Resource limits (CPU, memory)
    pub resource_limits: Option<ResourceLimits>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceLimits {
    pub cpu_limit: Option<f64>,
    pub memory_limit_mb: Option<u64>,
}

impl EnvironmentConfig {
    pub fn colab_default() -> Self {
        Self {
            use_systemd: false,
            install_dir: Some(PathBuf::from("/content/KISWARM")),
            pip_user_flag: true,
            start_services: false,
            enable_persistence: false,
            resource_limits: Some(ResourceLimits {
                cpu_limit: Some(2.0),
                memory_limit_mb: Some(12288), // 12GB typical for Colab
            }),
        }
    }
    
    pub fn docker_default() -> Self {
        Self {
            use_systemd: false,
            install_dir: None,
            pip_user_flag: false,
            start_services: true,
            enable_persistence: false,
            resource_limits: None,
        }
    }
    
    pub fn kubernetes_default() -> Self {
        Self {
            use_systemd: false,
            install_dir: Some(PathBuf::from("/opt/kiswarm")),
            pip_user_flag: false,
            start_services: true,
            enable_persistence: true,
            resource_limits: None,
        }
    }
    
    pub fn wsl2_default() -> Self {
        Self {
            use_systemd: false, // Check dynamically
            install_dir: None,
            pip_user_flag: false,
            start_services: true,
            enable_persistence: true,
            resource_limits: None,
        }
    }
    
    pub fn cloud_vm_default() -> Self {
        Self {
            use_systemd: true,
            install_dir: None,
            pip_user_flag: false,
            start_services: true,
            enable_persistence: true,
            resource_limits: None,
        }
    }
    
    pub fn bare_metal_default() -> Self {
        Self {
            use_systemd: true,
            install_dir: None,
            pip_user_flag: false,
            start_services: true,
            enable_persistence: true,
            resource_limits: None,
        }
    }
}

impl ScoutConfig {
    /// Load configuration from file
    pub fn from_file(path: &PathBuf) -> crate::ScoutResult<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| crate::ScoutError::FileReadFailed { path: path.clone() })?;
        
        let config: ScoutConfig = if path.extension().map_or(false, |e| e == "json") {
            serde_json::from_str(&content)
                .map_err(|e| crate::ScoutError::ConfigError(e.to_string()))?
        } else {
            // Assume TOML
            toml::from_str(&content)
                .map_err(|e| crate::ScoutError::ConfigError(e.to_string()))?
        };
        
        Ok(config)
    }
    
    /// Save configuration to file
    pub fn to_file(&self, path: &PathBuf) -> crate::ScoutResult<()> {
        let content = serde_json::to_string_pretty(self)
            .map_err(|e| crate::ScoutError::ConfigError(e.to_string()))?;
        
        std::fs::write(path, content)
            .map_err(|e| crate::ScoutError::FileWriteFailed { path: path.clone() })?;
        
        Ok(())
    }
    
    /// Create configuration from environment variables
    pub fn from_env() -> Self {
        let mut config = Self::default();
        
        // Override with environment variables
        if let Ok(val) = std::env::var("KISWARM_INSTALL_DIR") {
            config.paths.install_dir = PathBuf::from(val);
        }
        if let Ok(val) = std::env::var("KISWARM_LOG_LEVEL") {
            config.logging.level = val;
        }
        if let Ok(val) = std::env::var("KISWARM_MAX_RETRIES") {
            if let Ok(retries) = val.parse() {
                config.retry.max_retries = retries;
            }
        }
        
        config
    }
}
