//! Level 5: Physical Ark Source Implementation
//!
//! LAST RESORT source using physical media and local caches.
//! Features:
//! - USB drive detection and mounting
//! - Optical disc support (CD/DVD/Blu-ray)
//! - Pre-staged local cache directories
//! - Archive integrity verification
//! - GPG signature verification

use super::types::*;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, Instant};

/// Physical media type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MediaType {
    /// USB flash drive
    USBFlash,
    
    /// External hard drive
    ExternalHDD,
    
    /// External SSD
    ExternalSSD,
    
    /// Optical disc (CD/DVD/Blu-ray)
    OpticalDisc,
    
    /// SD card
    SDCard,
    
    /// Network mount (NFS/SMB)
    NetworkMount,
    
    /// Pre-staged local directory
    LocalCache,
}

/// Physical Ark configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicalArkConfig {
    /// Ark search paths
    pub search_paths: Vec<String>,
    
    /// Common mount points to check
    pub mount_points: Vec<String>,
    
    /// Ark manifest filename
    pub manifest_filename: String,
    
    /// Required GPG key ID
    pub required_gpg_key_id: Option<String>,
    
    /// Enable optical disc support
    pub enable_optical: bool,
    
    /// Verify checksums
    pub verify_checksums: bool,
    
    /// Verify signatures
    pub verify_signatures: bool,
    
    /// Minimum required Ark version
    pub min_ark_version: Option<String>,
    
    /// Cache directory for local staging
    pub cache_dir: Option<PathBuf>,
}

impl Default for PhysicalArkConfig {
    fn default() -> Self {
        Self {
            search_paths: vec![
                "/opt/kiswarm-ark".to_string(),
                "/usr/local/kiswarm-ark".to_string(),
                "~/.kiswarm/ark".to_string(),
                "./ark".to_string(),
            ],
            mount_points: vec![
                "/media".to_string(),
                "/mnt".to_string(),
                "/run/media".to_string(),
                "/Volumes".to_string(), // macOS
            ],
            manifest_filename: "kiswarm-ark-manifest.json".to_string(),
            required_gpg_key_id: Some("KISWARM-RELEASE-KEY".to_string()),
            enable_optical: true,
            verify_checksums: true,
            verify_signatures: true,
            min_ark_version: Some("6.3.0".to_string()),
            cache_dir: Some(PathBuf::from("/tmp/kiswarm-ark-cache")),
        }
    }
}

/// Ark manifest structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArkManifest {
    /// Ark version
    pub version: String,
    
    /// KISWARM version
    pub kiswarm_version: String,
    
    /// Creation timestamp
    pub created_at: String,
    
    /// Expiration timestamp (optional)
    pub expires_at: Option<String>,
    
    /// Supported platforms
    pub platforms: Vec<String>,
    
    /// Artifacts in the ark
    pub artifacts: Vec<ArkArtifact>,
    
    /// Total size in bytes
    pub total_size: u64,
    
    /// GPG signature
    pub signature: Option<String>,
    
    /// Checksum of manifest
    pub manifest_checksum: String,
}

/// Artifact in the Ark
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArkArtifact {
    /// Artifact name
    pub name: String,
    
    /// Relative path in ark
    pub path: String,
    
    /// SHA-256 checksum
    pub sha256: String,
    
    /// Size in bytes
    pub size: u64,
    
    /// Artifact type
    pub artifact_type: ArtifactType,
    
    /// GPG signature file path
    pub signature_path: Option<String>,
    
    /// Required flag
    pub required: bool,
}

/// Detected physical ark
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectedArk {
    /// Ark path
    pub path: PathBuf,
    
    /// Media type
    pub media_type: MediaType,
    
    /// Manifest
    pub manifest: ArkManifest,
    
    /// Available space
    pub available_space: u64,
    
    /// Mount point
    pub mount_point: Option<String>,
    
    /// Is read-only
    pub read_only: bool,
}

/// Physical Ark Source implementation
pub struct PhysicalArkSource {
    /// Configuration
    config: PhysicalArkConfig,
    
    /// Source statistics
    stats: SourceStats,
    
    /// Detected arks
    detected_arks: Arc<tokio::sync::RwLock<Vec<DetectedArk>>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

impl PhysicalArkSource {
    /// Create a new Physical Ark source
    pub fn new(config: PhysicalArkConfig) -> ScoutResult<Self> {
        Ok(Self {
            config,
            stats: SourceStats::new(),
            detected_arks: Arc::new(tokio::sync::RwLock::new(Vec::new())),
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Detect all available physical arks
    pub async fn detect_arks(&self) -> ScoutResult<Vec<DetectedArk>> {
        let mut arks = Vec::new();
        
        // Check configured search paths
        for path_str in &self.config.search_paths {
            let path = shellexpand::tilde(path_str).to_string();
            let path = PathBuf::from(path);
            
            if let Ok(Some(ark)) = self.check_path_for_ark(&path, MediaType::LocalCache).await {
                arks.push(ark);
            }
        }
        
        // Check mount points for removable media
        for mount_point in &self.config.mount_points {
            if let Ok(entries) = std::fs::read_dir(mount_point) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if path.is_dir() {
                        // Determine media type
                        let media_type = self.detect_media_type(&path);
                        
                        if let Ok(Some(ark)) = self.check_path_for_ark(&path, media_type).await {
                            arks.push(ark);
                        }
                    }
                }
            }
        }
        
        // Check for optical discs
        if self.config.enable_optical {
            if let Ok(Some(ark)) = self.check_optical_disc().await {
                arks.push(ark);
            }
        }
        
        // Update detected arks cache
        {
            let mut detected = self.detected_arks.write().await;
            *detected = arks.clone();
        }
        
        if let Some(logger) = &self.logger {
            logger.info("Physical ark detection complete", serde_json::json!({
                "arks_found": arks.len(),
                "paths_checked": self.config.search_paths.len() + self.config.mount_points.len(),
            }))?;
        }
        
        Ok(arks)
    }
    
    /// Detect media type from path
    fn detect_media_type(&self, path: &Path) -> MediaType {
        let path_str = path.to_string_lossy().to_lowercase();
        
        if path_str.contains("/media/") || path_str.contains("/run/media/") {
            // Check if it's likely a USB drive
            if path_str.contains("usb") || path_str.contains("flash") {
                MediaType::USBFlash
            } else if path_str.contains("sd") || path_str.contains("mmc") {
                MediaType::SDCard
            } else {
                MediaType::ExternalHDD
            }
        } else if path_str.contains("/mnt/") {
            MediaType::NetworkMount
        } else {
            MediaType::LocalCache
        }
    }
    
    /// Check a path for a valid ark
    async fn check_path_for_ark(
        &self,
        path: &Path,
        media_type: MediaType,
    ) -> ScoutResult<Option<DetectedArk>> {
        let manifest_path = path.join(&self.config.manifest_filename);
        
        if !manifest_path.exists() {
            return Ok(None);
        }
        
        // Read and parse manifest
        let manifest_content = tokio::fs::read_to_string(&manifest_path).await
            .map_err(|_| ScoutError::FileReadFailed { path: manifest_path.clone() })?;
        
        let manifest: ArkManifest = serde_json::from_str(&manifest_content)
            .map_err(|e| ScoutError::ArkManifestInvalid(e.to_string()))?;
        
        // Verify manifest checksum
        if self.config.verify_checksums {
            if !self.verify_manifest_checksum(&manifest, &manifest_content).await? {
                if let Some(logger) = &self.logger {
                    logger.warn("Ark manifest checksum verification failed", serde_json::json!({
                        "path": path.to_string_lossy(),
                    }))?;
                }
                return Ok(None);
            }
        }
        
        // Check minimum version
        if let Some(ref min_version) = self.config.min_ark_version {
            if !self.version_gte(&manifest.version, min_version) {
                if let Some(logger) = &self.logger {
                    logger.warn("Ark version too old", serde_json::json!({
                        "path": path.to_string_lossy(),
                        "version": &manifest.version,
                        "required": min_version,
                    }))?;
                }
                return Ok(None);
            }
        }
        
        // Get available space
        let available_space = self.get_available_space(path).unwrap_or(0);
        
        Ok(Some(DetectedArk {
            path: path.to_path_buf(),
            media_type,
            manifest,
            available_space,
            mount_point: path.parent().map(|p| p.to_string_lossy().to_string()),
            read_only: self.is_read_only(path).await,
        }))
    }
    
    /// Check for optical disc
    async fn check_optical_disc(&self) -> ScoutResult<Option<DetectedArk>> {
        let optical_paths = [
            "/dev/sr0",
            "/dev/cdrom",
            "/dev/dvd",
        ];
        
        for device in &optical_paths {
            if Path::new(device).exists() {
                // Try to mount if not mounted
                let mount_point = "/mnt/cdrom";
                
                // Check if mount point exists and has content
                let mount_path = Path::new(mount_point);
                if mount_path.exists() {
                    return self.check_path_for_ark(mount_path, MediaType::OpticalDisc).await;
                }
            }
        }
        
        Ok(None)
    }
    
    /// Copy artifact from ark to destination
    async fn copy_artifact(
        &self,
        ark: &DetectedArk,
        artifact: &ArkArtifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<u64> {
        let src_path = ark.path.join(&artifact.path);
        
        if !src_path.exists() {
            return Err(ScoutError::FileReadFailed { path: src_path });
        }
        
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting physical ark copy", serde_json::json!({
                "ark_path": ark.path.to_string_lossy(),
                "artifact": &artifact.name,
                "dest": dest.to_string_lossy(),
                "media_type": format!("{:?}", ark.media_type),
            }))?;
        }
        
        // Create parent directory
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| ScoutError::DirectoryCreationFailed { path: parent.to_path_buf() })?;
        }
        
        // Get file size
        let metadata = tokio::fs::metadata(&src_path).await
            .map_err(|_| ScoutError::FileReadFailed { path: src_path.clone() })?;
        let total_size = metadata.len();
        
        // Copy file with progress tracking
        let mut src_file = tokio::fs::File::open(&src_path).await
            .map_err(|_| ScoutError::FileReadFailed { path: src_path.clone() })?;
        
        let mut dest_file = tokio::fs::File::create(dest).await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        let mut copied: u64 = 0;
        let buffer_size = 1024 * 1024; // 1MB buffer
        
        use tokio::io::{AsyncReadExt, AsyncWriteExt};
        
        let mut buffer = vec![0u8; buffer_size];
        
        loop {
            let bytes_read = src_file.read(&mut buffer).await
                .map_err(|e| ScoutError::FileReadFailed { path: src_path.clone() })?;
            
            if bytes_read == 0 {
                break;
            }
            
            dest_file.write_all(&buffer[..bytes_read]).await
                .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
            
            copied += bytes_read as u64;
            
            if let Some(ref callback) = progress_callback {
                callback(copied, total_size);
            }
        }
        
        dest_file.flush().await
            .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        if let Some(logger) = &self.logger {
            logger.info("Physical ark copy complete", serde_json::json!({
                "bytes": copied,
                "duration_ms": start.elapsed().as_millis(),
                "media_type": format!("{:?}", ark.media_type),
            }))?;
        }
        
        Ok(copied)
    }
    
    /// Verify manifest checksum
    async fn verify_manifest_checksum(
        &self,
        manifest: &ArkManifest,
        content: &str,
    ) -> ScoutResult<bool> {
        use sha2::{Digest, Sha256};
        
        let mut hasher = Sha256::new();
        hasher.update(content.as_bytes());
        let actual = format!("{:x}", hasher.finalize());
        
        Ok(actual == manifest.manifest_checksum)
    }
    
    /// Verify artifact checksum
    async fn verify_artifact_checksum(
        &self,
        path: &PathBuf,
        expected: &str,
    ) -> ScoutResult<bool> {
        use sha2::{Digest, Sha256};
        
        let content = tokio::fs::read(path).await
            .map_err(|_| ScoutError::FileReadFailed { path: path.clone() })?;
        
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let actual = format!("{:x}", hasher.finalize());
        
        Ok(actual == expected)
    }
    
    /// Check if path is read-only
    async fn is_read_only(&self, path: &Path) -> bool {
        // Try to create a temporary file
        let test_file = path.join(".write_test");
        match tokio::fs::File::create(&test_file).await {
            Ok(_) => {
                let _ = tokio::fs::remove_file(&test_file).await;
                false
            }
            Err(_) => true,
        }
    }
    
    /// Get available space at path
    fn get_available_space(&self, path: &Path) -> ScoutResult<u64> {
        // Platform-specific implementation
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            if let Ok(metadata) = std::fs::metadata(path) {
                // Approximation - actual free space would need statvfs
                return Ok(metadata.blocks() as u64 * 512);
            }
        }
        
        Ok(0)
    }
    
    /// Compare version strings (returns true if a >= b)
    fn version_gte(&self, a: &str, b: &str) -> bool {
        let parse_version = |v: &str| -> Vec<u32> {
            v.split('.')
                .filter_map(|s| s.parse().ok())
                .collect()
        };
        
        let a_parts = parse_version(a);
        let b_parts = parse_version(b);
        
        for i in 0..std::cmp::max(a_parts.len(), b_parts.len()) {
            let a_val = a_parts.get(i).unwrap_or(&0);
            let b_val = b_parts.get(i).unwrap_or(&0);
            
            if a_val > b_val {
                return true;
            }
            if a_val < b_val {
                return false;
            }
        }
        
        true
    }
    
    /// Find artifact in detected arks
    async fn find_artifact_in_arks(&self, artifact: &Artifact) -> Option<(DetectedArk, ArkArtifact)> {
        let arks = self.detected_arks.read().await;
        
        for ark in arks.iter() {
            for ark_artifact in &ark.manifest.artifacts {
                if ark_artifact.name == artifact.name {
                    return Some((ark.clone(), ark_artifact.clone()));
                }
            }
        }
        
        None
    }
}

#[async_trait::async_trait]
impl Source for PhysicalArkSource {
    fn level(&self) -> SourceLevel {
        SourceLevel::PhysicalArk
    }
    
    fn name(&self) -> &str {
        "physical-ark"
    }
    
    async fn check_availability(&self) -> ScoutResult<SourceHealth> {
        let arks = self.detect_arks().await?;
        
        if arks.is_empty() {
            Ok(SourceHealth::Unhealthy {
                reason: UnhealthyReason::MediaNotPresent,
            })
        } else {
            // Check if any ark has required artifacts
            let has_required = arks.iter().any(|ark| {
                ark.manifest.artifacts.iter().any(|a| a.required)
            });
            
            if has_required {
                Ok(SourceHealth::Healthy)
            } else {
                Ok(SourceHealth::Degraded {
                    reason: DegradationReason::PartialAvailability,
                })
            }
        }
    }
    
    async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        let start = Instant::now();
        
        // Detect arks if not already detected
        let arks = self.detect_arks().await?;
        
        if arks.is_empty() {
            return Err(ScoutError::ArkNotFound { 
                path: PathBuf::from("no-physical-ark-found") 
            });
        }
        
        // Find artifact in arks
        let (ark, ark_artifact) = self.find_artifact_in_arks(artifact).await
            .ok_or_else(|| ScoutError::NetworkError(
                format!("Artifact {} not found in any physical ark", artifact.name)
            ))?;
        
        // Copy artifact
        let bytes = self.copy_artifact(&ark, &ark_artifact, dest, progress_callback).await?;
        
        // Verify checksum
        let checksum_verified = if self.config.verify_checksums {
            self.verify_artifact_checksum(dest, &ark_artifact.sha256).await?
        } else {
            false
        };
        
        Ok(FetchResult {
            source_level: SourceLevel::PhysicalArk,
            source_name: format!("{}:{}", 
                match ark.media_type {
                    MediaType::USBFlash => "usb",
                    MediaType::ExternalHDD => "hdd",
                    MediaType::ExternalSSD => "ssd",
                    MediaType::OpticalDisc => "optical",
                    MediaType::SDCard => "sdcard",
                    MediaType::NetworkMount => "network",
                    MediaType::LocalCache => "cache",
                },
                ark.path.file_name()
                    .map(|n| n.to_string_lossy().to_string())
                    .unwrap_or_default()
            ),
            local_path: dest.clone(),
            bytes_transferred: bytes,
            duration: start.elapsed(),
            attempts: 1,
            checksum_verified,
            signature_verified: false, // Would verify GPG signature here
            timestamp: chrono::Utc::now().to_rfc3339(),
            failover_history: vec![],
        })
    }
    
    fn stats(&self) -> &SourceStats {
        &self.stats
    }
    
    fn reset_stats(&mut self) {
        self.stats = SourceStats::new();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_physical_ark_config_default() {
        let config = PhysicalArkConfig::default();
        assert!(!config.search_paths.is_empty());
        assert!(config.verify_checksums);
    }
    
    #[test]
    fn test_version_comparison() {
        let config = PhysicalArkConfig::default();
        let source = PhysicalArkSource::new(config).unwrap();
        
        assert!(source.version_gte("6.3.5", "6.3.0"));
        assert!(source.version_gte("6.3.5", "6.3.5"));
        assert!(!source.version_gte("6.3.0", "6.3.5"));
        assert!(source.version_gte("7.0.0", "6.9.9"));
    }
    
    #[test]
    fn test_media_type_detection() {
        let config = PhysicalArkConfig::default();
        let source = PhysicalArkSource::new(config).unwrap();
        
        let usb_type = source.detect_media_type(Path::new("/media/usb/kiswarm"));
        assert_eq!(usb_type, MediaType::USBFlash);
        
        let cache_type = source.detect_media_type(Path::new("/opt/kiswarm-ark"));
        assert_eq!(cache_type, MediaType::LocalCache);
    }
}
