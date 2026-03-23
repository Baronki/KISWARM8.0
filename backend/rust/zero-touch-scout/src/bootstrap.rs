//! Bootstrap Engine for KISWARM Zero-Touch Scout
//! 
//! This module implements the parallel bootstrap system:
//! - Online bootstrap from internet sources
//! - Offline bootstrap from Ark cache
//! - Race-to-completion arbiter
//! - Installation verification

use crate::config::{BootstrapConfig, ScoutConfig};
use crate::environment::EnvironmentProfile;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use crate::network::{DownloadSource, MultiSourceDownloader, NetworkClient, SourceType};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, RwLock};

/// Bootstrap method used
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BootstrapMethod {
    /// Downloaded from internet
    Online,
    
    /// Installed from local Ark cache
    ArkLocal,
    
    /// Received from peer Ark
    ArkPeer,
    
    /// Installed from physical media (USB)
    ArkPhysical,
    
    /// Hybrid (raced both paths)
    Hybrid,
}

/// Bootstrap result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BootstrapResult {
    /// Method that succeeded
    pub method: BootstrapMethod,
    
    /// Source that was used
    pub source: String,
    
    /// Time taken
    pub duration_secs: f64,
    
    /// Bytes transferred
    pub bytes_transferred: u64,
    
    /// Installation path
    pub install_path: PathBuf,
    
    /// Verification passed
    pub verified: bool,
}

/// Ark manifest structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArkManifest {
    /// Ark version
    pub ark_version: String,
    
    /// Creation timestamp
    pub created_at: String,
    
    /// KISWARM version
    pub kiswarm_version: String,
    
    /// Target platforms
    pub target_platforms: Vec<String>,
    
    /// Components in the Ark
    pub components: std::collections::HashMap<String, ArkComponent>,
    
    /// Minimum RAM required
    pub min_ram_gb: f64,
    
    /// Minimum disk required
    pub min_disk_gb: f64,
    
    /// GPG signature
    pub signature: Option<String>,
}

/// Component in the Ark
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArkComponent {
    /// Relative path in Ark
    pub path: String,
    
    /// SHA-256 checksum
    pub sha256: String,
    
    /// Size in bytes
    pub size_bytes: u64,
    
    /// Optional: list of packages for Python wheels
    pub packages: Option<Vec<String>>,
}

/// Ark cache manager
pub struct ArkManager {
    /// Path to Ark directory
    ark_path: PathBuf,
    
    /// Manifest (if loaded)
    manifest: Option<ArkManifest>,
}

impl ArkManager {
    /// Create a new Ark manager
    pub fn new(ark_path: PathBuf) -> Self {
        Self {
            ark_path,
            manifest: None,
        }
    }
    
    /// Check if Ark exists and is valid
    pub async fn exists(&self) -> bool {
        self.ark_path.exists() && self.manifest_path().exists()
    }
    
    /// Get manifest path
    fn manifest_path(&self) -> PathBuf {
        self.ark_path.join("manifest.json")
    }
    
    /// Load Ark manifest
    pub async fn load_manifest(&mut self) -> ScoutResult<ArkManifest> {
        let manifest_path = self.manifest_path();
        
        if !manifest_path.exists() {
            return Err(ScoutError::ArkNotFound { path: self.ark_path.clone() });
        }
        
        let content = tokio::fs::read_to_string(&manifest_path).await
            .map_err(|_| ScoutError::FileReadFailed { path: manifest_path.clone() })?;
        
        let manifest: ArkManifest = serde_json::from_str(&content)
            .map_err(|e| ScoutError::ArkManifestInvalid(e.to_string()))?;
        
        self.manifest = Some(manifest.clone());
        Ok(manifest)
    }
    
    /// Verify Ark integrity
    pub async fn verify_integrity(&self) -> ScoutResult<bool> {
        let manifest = self.manifest.as_ref()
            .ok_or_else(|| ScoutError::ArkManifestInvalid("Manifest not loaded".to_string()))?;
        
        use sha2::{Digest, Sha256};
        
        for (name, component) in &manifest.components {
            let component_path = self.ark_path.join(&component.path);
            
            if !component_path.exists() {
                return Err(ScoutError::ArkIntegrityFailed(
                    format!("Component {} not found", name)
                ));
            }
            
            // Verify checksum
            let content = tokio::fs::read(&component_path).await
                .map_err(|e| ScoutError::FileReadFailed { path: component_path.clone() })?;
            
            let mut hasher = Sha256::new();
            hasher.update(&content);
            let actual = format!("{:x}", hasher.finalize());
            
            if actual != component.sha256 {
                return Err(ScoutError::ArkIntegrityFailed(
                    format!("Checksum mismatch for {}", name)
                ));
            }
        }
        
        Ok(true)
    }
    
    /// Get component path
    pub fn component_path(&self, component_name: &str) -> Option<PathBuf> {
        self.manifest.as_ref().and_then(|m| {
            m.components.get(component_name).map(|c| {
                self.ark_path.join(&c.path)
            })
        })
    }
    
    /// Get Python wheels path
    pub fn wheels_path(&self) -> Option<PathBuf> {
        self.component_path("python-wheels")
    }
    
    /// Get Ollama binary path
    pub fn ollama_binary_path(&self, arch: &str) -> Option<PathBuf> {
        let component_name = format!("ollama-{}", arch);
        self.component_path(&component_name)
    }
    
    /// Get KISWARM core bundle path
    pub fn kiswarm_bundle_path(&self) -> Option<PathBuf> {
        self.component_path("kiswarm-core")
    }
}

/// Online bootstrap implementation
pub struct OnlineBootstrap {
    /// Network client
    client: NetworkClient,
    
    /// Configuration
    config: BootstrapConfig,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl OnlineBootstrap {
    /// Create a new online bootstrap
    pub fn new(client: NetworkClient, config: BootstrapConfig) -> Self {
        Self {
            client,
            config,
            logger: None,
        }
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Get download sources in priority order
    pub fn get_sources(&self) -> Vec<DownloadSource> {
        let mut sources = Vec::new();
        
        // Primary: GitHub
        sources.push(DownloadSource {
            name: "github-primary".to_string(),
            url: format!("{}/archive/refs/heads/main.tar.gz", self.config.github_url),
            priority: 1,
            source_type: SourceType::GitHub,
            checksum: None,
            min_bandwidth: None,
            max_retries: 3,
        });
        
        // GitHub mirrors
        for (i, mirror) in self.config.github_mirrors.iter().enumerate() {
            sources.push(DownloadSource {
                name: format!("github-mirror-{}", i + 1),
                url: format!("{}/archive/refs/heads/main.tar.gz", mirror),
                priority: 2 + i as u32,
                source_type: SourceType::GitHub,
                checksum: None,
                min_bandwidth: None,
                max_retries: 3,
            });
        }
        
        // CDN URLs
        for (i, cdn) in self.config.cdn_urls.iter().enumerate() {
            sources.push(DownloadSource {
                name: format!("cdn-{}", i + 1),
                url: format!("{}/kiswarm-latest.tar.gz", cdn),
                priority: 10 + i as u32,
                source_type: SourceType::CDN,
                checksum: None,
                min_bandwidth: None,
                max_retries: 3,
            });
        }
        
        // IPFS gateways
        for (i, gateway) in self.config.ipfs_gateways.iter().enumerate() {
            sources.push(DownloadSource {
                name: format!("ipfs-{}", i + 1),
                url: format!("{}/ipfs/QmKISWARM/kiswarm-v{}.tar.gz", 
                    gateway, self.config.kiswarm_version),
                priority: 20 + i as u32,
                source_type: SourceType::IPFS,
                checksum: None,
                min_bandwidth: None,
                max_retries: 3,
            });
        }
        
        sources
    }
    
    /// Run online bootstrap
    pub async fn run(&self, dest: &Path) -> ScoutResult<BootstrapResult> {
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting online bootstrap", serde_json::json!({
                "dest": dest.to_string_lossy(),
                "sources_count": self.get_sources().len(),
            }))?;
        }
        
        // Create download sources
        let sources = self.get_sources();
        let downloader = MultiSourceDownloader::new(self.client.clone(), sources);
        
        // Download
        let progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>> = 
            if let Some(logger) = &self.logger {
                Some(Arc::new(move |downloaded, total| {
                    if total > 0 && downloaded % (1024 * 1024) == 0 {
                        let _ = logger.info(
                            &format!("Download progress: {}%", (downloaded * 100) / total),
                            serde_json::json!({
                                "downloaded_bytes": downloaded,
                                "total_bytes": total,
                            })
                        );
                    }
                }))
            } else {
                None
            };
        
        let source = downloader.download(dest, progress_callback).await?;
        
        // Extract
        self.extract_archive(dest).await?;
        
        let duration = start.elapsed();
        
        if let Some(logger) = &self.logger {
            logger.info("Online bootstrap complete", serde_json::json!({
                "source": &source.name,
                "duration_s": duration.as_secs_f64(),
            }))?;
        }
        
        Ok(BootstrapResult {
            method: BootstrapMethod::Online,
            source: source.name,
            duration_secs: duration.as_secs_f64(),
            bytes_transferred: 0, // Would track actual bytes
            install_path: dest.to_path_buf(),
            verified: false,
        })
    }
    
    /// Extract tar.gz archive
    async fn extract_archive(&self, archive: &Path) -> ScoutResult<()> {
        use flate2::read::GzDecoder;
        use std::fs::File;
        use tar::Archive;
        
        let file = File::open(archive)
            .map_err(|_| ScoutError::FileReadFailed { path: archive.to_path_buf() })?;
        
        let gz = GzDecoder::new(file);
        let mut tar = Archive::new(gz);
        
        let dest = archive.parent()
            .ok_or_else(|| ScoutError::ConfigError("Invalid archive path".to_string()))?;
        
        tar.unpack(dest)
            .map_err(|e| ScoutError::InstallationFailed(format!("Extract failed: {}", e)))?;
        
        Ok(())
    }
}

/// Offline (Ark) bootstrap implementation
pub struct ArkBootstrap {
    /// Ark manager
    ark: ArkManager,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl ArkBootstrap {
    /// Create a new Ark bootstrap
    pub fn new(ark_path: PathBuf) -> Self {
        Self {
            ark: ArkManager::new(ark_path),
            logger: None,
        }
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Check if Ark bootstrap is possible
    pub async fn is_available(&mut self) -> bool {
        self.ark.exists().await
    }
    
    /// Run Ark bootstrap
    pub async fn run(&mut self, dest: &Path, arch: &str) -> ScoutResult<BootstrapResult> {
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting Ark (offline) bootstrap", serde_json::json!({
                "dest": dest.to_string_lossy(),
                "arch": arch,
            }))?;
        }
        
        // Load manifest
        let manifest = self.ark.load_manifest().await?;
        
        if let Some(logger) = &self.logger {
            logger.info("Ark manifest loaded", serde_json::json!({
                "ark_version": &manifest.ark_version,
                "kiswarm_version": &manifest.kiswarm_version,
                "components": manifest.components.len(),
            }))?;
        }
        
        // Verify integrity
        self.ark.verify_integrity().await?;
        
        if let Some(logger) = &self.logger {
            logger.info("Ark integrity verified", serde_json::json!({}))?;
        }
        
        // Install components
        let mut bytes_transferred: u64 = 0;
        
        // 1. Extract KISWARM core
        if let Some(bundle_path) = self.ark.kiswarm_bundle_path() {
            bytes_transferred += self.extract_component(&bundle_path, dest).await?;
        }
        
        // 2. Install Python wheels (if venv exists)
        // Would install to venv here
        
        // 3. Install Ollama binary (if needed and present)
        if let Some(ollama_path) = self.ark.ollama_binary_path(arch) {
            // Copy to /usr/local/bin or ~/bin
        }
        
        let duration = start.elapsed();
        
        // Determine method based on Ark location
        let method = if self.ark.ark_path.starts_with("/media") || 
                     self.ark.ark_path.starts_with("/mnt") {
            BootstrapMethod::ArkPhysical
        } else if self.ark.ark_path.starts_with("/opt/kiswarm-ark") {
            BootstrapMethod::ArkPeer
        } else {
            BootstrapMethod::ArkLocal
        };
        
        if let Some(logger) = &self.logger {
            logger.info("Ark bootstrap complete", serde_json::json!({
                "method": format!("{:?}", method),
                "duration_s": duration.as_secs_f64(),
                "bytes_transferred": bytes_transferred,
            }))?;
        }
        
        Ok(BootstrapResult {
            method,
            source: "ark-cache".to_string(),
            duration_secs: duration.as_secs_f64(),
            bytes_transferred,
            install_path: dest.to_path_buf(),
            verified: true, // Ark is pre-verified
        })
    }
    
    /// Extract a component to destination
    async fn extract_component(&self, component: &Path, dest: &Path) -> ScoutResult<u64> {
        let metadata = tokio::fs::metadata(component).await
            .map_err(|_| ScoutError::FileReadFailed { path: component.to_path_buf() })?;
        
        let size = metadata.len();
        
        // If it's a tar.gz, extract it
        if component.extension().map_or(false, |e| e == "gz") {
            use flate2::read::GzDecoder;
            use std::fs::File;
            use tar::Archive;
            
            let file = File::open(component)
                .map_err(|_| ScoutError::FileReadFailed { path: component.to_path_buf() })?;
            
            let gz = GzDecoder::new(file);
            let mut tar = Archive::new(gz);
            
            tar.unpack(dest)
                .map_err(|e| ScoutError::InstallationFailed(format!("Extract failed: {}", e)))?;
        } else {
            // Just copy the file
            let dest_file = dest.join(component.file_name().unwrap_or_default());
            tokio::fs::copy(component, &dest_file).await
                .map_err(|_| ScoutError::FileWriteFailed { path: dest_file })?;
        }
        
        Ok(size)
    }
}

/// Race-to-completion arbiter for parallel bootstrap
pub struct RaceArbiter {
    /// Online bootstrap result (if succeeded)
    online_result: Arc<Mutex<Option<ScoutResult<BootstrapResult>>>>,
    
    /// Ark bootstrap result (if succeeded)
    ark_result: Arc<Mutex<Option<ScoutResult<BootstrapResult>>>>,
    
    /// Winning method
    winner: Arc<RwLock<Option<BootstrapMethod>>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl RaceArbiter {
    /// Create a new race arbiter
    pub fn new() -> Self {
        Self {
            online_result: Arc::new(Mutex::new(None)),
            ark_result: Arc::new(Mutex::new(None)),
            winner: Arc::new(RwLock::new(None)),
            logger: None,
        }
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Run both bootstrap paths in parallel
    pub async fn race(
        &self,
        online_bootstrap: OnlineBootstrap,
        ark_bootstrap: ArkBootstrap,
        dest: &Path,
        arch: &str,
        timeout: Duration,
    ) -> ScoutResult<BootstrapResult> {
        let dest_online = dest.to_path_buf();
        let dest_ark = dest.to_path_buf();
        let arch = arch.to_string();
        
        let online_result = self.online_result.clone();
        let ark_result = self.ark_result.clone();
        let winner = self.winner.clone();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting parallel bootstrap race", serde_json::json!({
                "timeout_s": timeout.as_secs(),
            }))?;
        }
        
        // Spawn online bootstrap task
        let online_handle = tokio::spawn(async move {
            let result = online_bootstrap.run(&dest_online).await;
            *online_result.lock().await = Some(result.clone());
            result
        });
        
        // Spawn Ark bootstrap task
        let ark_handle = tokio::spawn(async move {
            let result = ark_bootstrap.run(&dest_ark, &arch).await;
            *ark_result.lock().await = Some(result.clone());
            result
        });
        
        // Use tokio::select! for race semantics
        let result = tokio::select! {
            // Online bootstrap completed
            res = online_handle => {
                match res {
                    Ok(Ok(result)) => {
                        *winner.write().await = Some(result.method);
                        ark_handle.abort();
                        
                        if let Some(logger) = &self.logger {
                            let _ = logger.info("Online bootstrap won the race", serde_json::json!({
                                "method": format!("{:?}", result.method),
                                "duration_s": result.duration_secs,
                            }));
                        }
                        
                        return Ok(result);
                    }
                    _ => {
                        // Online failed, wait for ark
                        let res = ark_handle.await;
                        match res {
                            Ok(Ok(result)) => {
                                *winner.write().await = Some(result.method);
                                
                                if let Some(logger) = &self.logger {
                                    let _ = logger.info("Ark bootstrap won the race", serde_json::json!({
                                        "method": format!("{:?}", result.method),
                                        "duration_s": result.duration_secs,
                                    }));
                                }
                                
                                return Ok(result);
                            }
                            _ => {
                                return Err(ScoutError::BootstrapFailed {
                                    phase: "race".to_string(),
                                    reason: "Both bootstrap paths failed".to_string(),
                                });
                            }
                        }
                    }
                }
            }
            
            // Ark bootstrap completed
            res = ark_handle => {
                match res {
                    Ok(Ok(result)) => {
                        *winner.write().await = Some(result.method);
                        online_handle.abort();
                        
                        if let Some(logger) = &self.logger {
                            let _ = logger.info("Ark bootstrap won the race", serde_json::json!({
                                "method": format!("{:?}", result.method),
                                "duration_s": result.duration_secs,
                            }));
                        }
                        
                        return Ok(result);
                    }
                    _ => {
                        // Ark failed, wait for online
                        let res = online_handle.await;
                        match res {
                            Ok(Ok(result)) => {
                                *winner.write().await = Some(result.method);
                                
                                if let Some(logger) = &self.logger {
                                    let _ = logger.info("Online bootstrap won the race", serde_json::json!({
                                        "method": format!("{:?}", result.method),
                                        "duration_s": result.duration_secs,
                                    }));
                                }
                                
                                return Ok(result);
                            }
                            _ => {
                                return Err(ScoutError::BootstrapFailed {
                                    phase: "race".to_string(),
                                    reason: "Both bootstrap paths failed".to_string(),
                                });
                            }
                        }
                    }
                }
            }
            
            // Timeout
            _ = tokio::time::sleep(timeout) => {
                online_handle.abort();
                ark_handle.abort();
                
                return Err(ScoutError::BootstrapFailed {
                    phase: "race".to_string(),
                    reason: "Timeout - both paths failed to complete in time".to_string(),
                });
            }
        };
    }
    
    /// Get the winning method
    pub async fn winner(&self) -> Option<BootstrapMethod> {
        *self.winner.read().await
    }
}

impl Default for RaceArbiter {
    fn default() -> Self {
        Self::new()
    }
}

/// Bootstrap orchestrator - main entry point for bootstrap
pub struct BootstrapOrchestrator {
    /// Configuration
    config: ScoutConfig,
    
    /// Logger
    logger: Arc<AuditLogger>,
}

impl BootstrapOrchestrator {
    /// Create a new orchestrator
    pub fn new(config: ScoutConfig, logger: Arc<AuditLogger>) -> Self {
        Self { config, logger }
    }
    
    /// Run bootstrap with all available methods
    pub async fn bootstrap(
        &self,
        dest: &Path,
        env_profile: &EnvironmentProfile,
        offline_only: bool,
    ) -> ScoutResult<BootstrapResult> {
        let arch = &env_profile.os.arch;
        let has_internet = env_profile.network.has_internet;
        
        self.logger.info("Bootstrap orchestrator starting", serde_json::json!({
            "dest": dest.to_string_lossy(),
            "arch": arch,
            "has_internet": has_internet,
            "offline_only": offline_only,
        }))?;
        
        // Try Ark first if available (faster)
        let ark_path = self.find_ark_path().await;
        let ark_available = if let Some(ref path) = ark_path {
            let mut ark = ArkBootstrap::new(path.clone());
            ark.is_available().await
        } else {
            false
        };
        
        // Decide on strategy
        if offline_only || !has_internet {
            // Offline only mode
            if ark_available {
                let path = ark_path.unwrap();
                let mut ark_bootstrap = ArkBootstrap::new(path)
                    .with_logger(self.logger.clone());
                return ark_bootstrap.run(dest, arch).await;
            } else {
                return Err(ScoutError::ArkNotFound { 
                    path: self.config.bootstrap.default_ark_path.clone() 
                });
            }
        }
        
        // Online mode - check if we should race
        if self.config.bootstrap.parallel_bootstrap && ark_available {
            // Parallel race
            let network_client = NetworkClient::new(self.config.network.clone())?;
            let online_bootstrap = OnlineBootstrap::new(
                network_client,
                self.config.bootstrap.clone(),
            ).with_logger(self.logger.clone());
            
            let ark_bootstrap = ArkBootstrap::new(ark_path.unwrap())
                .with_logger(self.logger.clone());
            
            let arbiter = RaceArbiter::new()
                .with_logger(self.logger.clone());
            
            return arbiter.race(
                online_bootstrap,
                ark_bootstrap,
                dest,
                arch,
                Duration::from_secs(self.config.bootstrap.max_bootstrap_time_secs),
            ).await;
        }
        
        // Online only
        let network_client = NetworkClient::new(self.config.network.clone())?;
        let online_bootstrap = OnlineBootstrap::new(
            network_client,
            self.config.bootstrap.clone(),
        ).with_logger(self.logger.clone());
        
        online_bootstrap.run(dest).await
    }
    
    /// Find Ark path
    async fn find_ark_path(&self) -> Option<PathBuf> {
        // Check default path first
        if self.config.bootstrap.default_ark_path.exists() {
            return Some(self.config.bootstrap.default_ark_path.clone());
        }
        
        // Check search paths
        for path in &self.config.bootstrap.ark_search_paths {
            if path.exists() {
                return Some(path.clone());
            }
        }
        
        // Check common locations
        let common_paths = [
            "/opt/kiswarm-ark",
            "/media/usb/kiswarm-ark",
            "/mnt/usb/kiswarm-ark",
            "/media/external/kiswarm-ark",
        ];
        
        for path in common_paths {
            if Path::new(path).exists() {
                return Some(PathBuf::from(path));
            }
        }
        
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_ark_manifest_parsing() {
        let manifest_json = r#"{
            "ark_version": "6.4.0",
            "created_at": "2025-01-15T00:00:00Z",
            "kiswarm_version": "6.4.0",
            "target_platforms": ["linux-x86_64", "linux-arm64"],
            "components": {
                "kiswarm-core": {
                    "path": "core/kiswarm-core.tar.gz",
                    "sha256": "abc123",
                    "size_bytes": 12345678
                }
            },
            "min_ram_gb": 8.0,
            "min_disk_gb": 20.0
        }"#;
        
        let manifest: ArkManifest = serde_json::from_str(manifest_json).unwrap();
        assert_eq!(manifest.ark_version, "6.4.0");
        assert_eq!(manifest.components.len(), 1);
    }
    
    #[test]
    fn test_bootstrap_method_serialization() {
        let method = BootstrapMethod::Online;
        let json = serde_json::to_string(&method).unwrap();
        assert!(json.contains("Online"));
        
        let parsed: BootstrapMethod = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed, BootstrapMethod::Online);
    }
    
    #[test]
    fn test_race_arbiter_creation() {
        let arbiter = RaceArbiter::new();
        assert!(arbiter.winner.try_read().unwrap().is_none());
    }
}
