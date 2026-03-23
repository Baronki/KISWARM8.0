//! Environment Detection Matrix for KISWARM Zero-Touch Scout
//! 
//! This module provides comprehensive environment detection for:
//! - Google Colab
//! - Docker containers
//! - Kubernetes pods
//! - WSL2 (Windows Subsystem for Linux)
//! - Cloud VMs (AWS, GCP, Azure, etc.)
//! - Bare metal Linux

use crate::config::EnvironmentConfig;
use crate::{ScoutError, ScoutResult};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::process::Command;

/// Detected environment type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Environment {
    /// Google Colab notebook environment
    GoogleColab,
    
    /// Docker container
    Docker,
    
    /// Kubernetes pod
    Kubernetes,
    
    /// Windows Subsystem for Linux 2
    WSL2,
    
    /// Cloud virtual machine
    CloudVM(CloudProvider),
    
    /// Bare metal server
    BareMetal,
    
    /// Unknown/unsupported environment
    Unknown,
}

impl std::fmt::Display for Environment {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Environment::GoogleColab => write!(f, "Google Colab"),
            Environment::Docker => write!(f, "Docker Container"),
            Environment::Kubernetes => write!(f, "Kubernetes Pod"),
            Environment::WSL2 => write!(f, "WSL2"),
            Environment::CloudVM(provider) => write!(f, "Cloud VM ({})", provider),
            Environment::BareMetal => write!(f, "Bare Metal"),
            Environment::Unknown => write!(f, "Unknown"),
        }
    }
}

/// Cloud provider detection
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CloudProvider {
    AWS,
    GCP,
    Azure,
    DigitalOcean,
    OracleCloud,
    AlibabaCloud,
    IBMCloud,
    Hetzner,
    Linode,
    Vultr,
    Other,
}

impl std::fmt::Display for CloudProvider {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CloudProvider::AWS => write!(f, "AWS"),
            CloudProvider::GCP => write!(f, "GCP"),
            CloudProvider::Azure => write!(f, "Azure"),
            CloudProvider::DigitalOcean => write!(f, "DigitalOcean"),
            CloudProvider::OracleCloud => write!(f, "Oracle Cloud"),
            CloudProvider::AlibabaCloud => write!(f, "Alibaba Cloud"),
            CloudProvider::IBMCloud => write!(f, "IBM Cloud"),
            CloudProvider::Hetzner => write!(f, "Hetzner"),
            CloudProvider::Linode => write!(f, "Linode"),
            CloudProvider::Vultr => write!(f, "Vultr"),
            CloudProvider::Other => write!(f, "Other"),
        }
    }
}

/// System hardware profile
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareProfile {
    /// CPU cores (logical)
    pub cpu_cores: usize,
    
    /// CPU model name
    pub cpu_model: String,
    
    /// CPU architecture (x86_64, aarch64, etc.)
    pub cpu_arch: String,
    
    /// Total RAM in GB
    pub ram_total_gb: f64,
    
    /// Available RAM in GB
    pub ram_available_gb: f64,
    
    /// RAM usage percentage
    pub ram_usage_percent: f64,
    
    /// Total disk space in GB
    pub disk_total_gb: f64,
    
    /// Available disk space in GB
    pub disk_available_gb: f64,
    
    /// Disk usage percentage
    pub disk_usage_percent: f64,
    
    /// GPU information (if detected)
    pub gpu_info: Vec<String>,
}

impl HardwareProfile {
    /// Check if hardware meets minimum requirements
    pub fn meets_requirements(&self, min_ram_gb: f64, min_disk_gb: f64, min_cpu: usize) -> ScoutResult<bool> {
        let mut issues = Vec::new();
        
        if self.ram_total_gb < min_ram_gb {
            issues.push(format!(
                "Insufficient RAM: {:.1}GB < {:.1}GB required",
                self.ram_total_gb, min_ram_gb
            ));
        }
        
        if self.disk_available_gb < min_disk_gb {
            issues.push(format!(
                "Insufficient disk: {:.1}GB available < {:.1}GB required",
                self.disk_available_gb, min_disk_gb
            ));
        }
        
        if self.cpu_cores < min_cpu {
            issues.push(format!(
                "Insufficient CPU: {} cores < {} required",
                self.cpu_cores, min_cpu
            ));
        }
        
        if !issues.is_empty() {
            return Err(ScoutError::InsufficientResources {
                resource: "System".to_string(),
                available: format!("RAM: {:.1}GB, Disk: {:.1}GB, CPU: {}", 
                    self.ram_total_gb, self.disk_available_gb, self.cpu_cores),
                required: format!("RAM: {:.1}GB, Disk: {:.1}GB, CPU: {}", 
                    min_ram_gb, min_disk_gb, min_cpu),
            });
        }
        
        Ok(true)
    }
}

/// OS fingerprint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OSFingerprint {
    /// Operating system name
    pub os_name: String,
    
    /// OS version
    pub os_version: String,
    
    /// Linux distribution (if applicable)
    pub distro: Option<String>,
    
    /// Distribution version
    pub distro_version: Option<String>,
    
    /// Kernel version
    pub kernel_version: String,
    
    /// Architecture
    pub arch: String,
    
    /// Hostname
    pub hostname: String,
    
    /// Init system (systemd, openrc, etc.)
    pub init_system: String,
    
    /// Package manager (apt, dnf, pacman, etc.)
    pub package_manager: String,
}

/// Network capabilities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkCapabilities {
    /// Can reach GitHub
    pub github_reachable: bool,
    
    /// Can reach PyPI
    pub pypi_reachable: bool,
    
    /// Can reach Ollama registry
    pub ollama_registry_reachable: bool,
    
    /// Internet connectivity
    pub has_internet: bool,
    
    /// GitHub latency in ms
    pub github_latency_ms: Option<f64>,
    
    /// PyPI latency in ms
    pub pypi_latency_ms: Option<f64>,
}

/// Complete environment profile
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvironmentProfile {
    /// Detected environment type
    pub environment: Environment,
    
    /// Hardware profile
    pub hardware: HardwareProfile,
    
    /// OS fingerprint
    pub os: OSFingerprint,
    
    /// Network capabilities
    pub network: NetworkCapabilities,
    
    /// Available tools (git, python, pip, docker, etc.)
    pub available_tools: Vec<String>,
    
    /// Missing required tools
    pub missing_tools: Vec<String>,
    
    /// Environment-specific configuration
    pub env_config: EnvironmentConfig,
    
    /// Detection timestamp
    pub detected_at: String,
}

/// Environment detector
pub struct EnvironmentDetector {
    /// Check timeout in milliseconds
    timeout_ms: u64,
}

impl Default for EnvironmentDetector {
    fn default() -> Self {
        Self { timeout_ms: 5000 }
    }
}

impl EnvironmentDetector {
    /// Create a new environment detector with custom timeout
    pub fn new(timeout_ms: u64) -> Self {
        Self { timeout_ms }
    }
    
    /// Perform full environment detection
    pub fn detect(&self) -> ScoutResult<EnvironmentProfile> {
        // Detection order matters - most specific first
        let environment = self.detect_environment_type()?;
        
        // Gather hardware profile
        let hardware = self.detect_hardware()?;
        
        // Gather OS fingerprint
        let os = self.detect_os()?;
        
        // Check network capabilities
        let network = self.check_network()?;
        
        // Check available tools
        let (available_tools, missing_tools) = self.check_tools()?;
        
        // Get environment-specific configuration
        let env_config = self.get_env_config(&environment);
        
        Ok(EnvironmentProfile {
            environment,
            hardware,
            os,
            network,
            available_tools,
            missing_tools,
            env_config,
            detected_at: chrono::Utc::now().to_rfc3339(),
        })
    }
    
    /// Detect the environment type
    fn detect_environment_type(&self) -> ScoutResult<Environment> {
        // Order matters: most specific first
        
        // 1. Check for Google Colab
        if self.is_colab() {
            return Ok(Environment::GoogleColab);
        }
        
        // 2. Check for Kubernetes
        if self.is_kubernetes() {
            return Ok(Environment::Kubernetes);
        }
        
        // 3. Check for Docker
        if self.is_docker() {
            return Ok(Environment::Docker);
        }
        
        // 4. Check for WSL2
        if self.is_wsl2() {
            return Ok(Environment::WSL2);
        }
        
        // 5. Check for Cloud VM
        if let Some(provider) = self.detect_cloud_provider() {
            return Ok(Environment::CloudVM(provider));
        }
        
        // 6. Check for bare metal
        if self.is_bare_metal() {
            return Ok(Environment::BareMetal);
        }
        
        Ok(Environment::Unknown)
    }
    
    /// Check if running in Google Colab
    fn is_colab(&self) -> bool {
        // Check multiple indicators
        let checks = [
            // Colab-specific paths
            || Path::new("/content").exists(),
            || Path::new("/opt/google.colab").exists(),
            || Path::new("/usr/local/lib/python3.10/dist-packages/google/colab").exists(),
            
            // Colab environment variables
            || std::env::var("COLAB_RELEASE_TAG").is_ok(),
            || std::env::var("COLAB_BACKEND_VERSION").is_ok(),
            || std::env::var("GCE_METADATA_HOST").is_ok(),
            
            // Check for Colab-specific files
            || Path::new("/datalab").exists(),
            || Path::new("/var/colab").exists(),
        ];
        
        checks.iter().any(|check| check())
    }
    
    /// Check if running in Kubernetes
    fn is_kubernetes(&self) -> bool {
        let checks = [
            // Kubernetes service account
            || Path::new("/var/run/secrets/kubernetes.io/serviceaccount/token").exists(),
            
            // Environment variables set by Kubernetes
            || std::env::var("KUBERNETES_SERVICE_HOST").is_ok(),
            || std::env::var("KUBERNETES_SERVICE_PORT").is_ok(),
            || std::env::var("KUBERNETES_PORT").is_ok(),
            
            // Check cgroup for kubepods
            || {
                if let Ok(content) = std::fs::read_to_string("/proc/1/cgroup") {
                    content.contains("kubepods") || content.contains("kubepod")
                } else {
                    false
                }
            },
        ];
        
        checks.iter().any(|check| check())
    }
    
    /// Check if running in Docker
    fn is_docker(&self) -> bool {
        let checks = [
            // Docker environment file
            || Path::new("/.dockerenv").exists(),
            
            // Check cgroup for docker
            || {
                if let Ok(content) = std::fs::read_to_string("/proc/1/cgroup") {
                    content.contains("docker") || content.contains("lxc")
                } else {
                    false
                }
            },
            
            // Docker environment variable
            || std::env::var("DOCKER_CONTAINER").is_ok(),
            || std::env::var("container").map(|v| v == "docker").unwrap_or(false),
        ];
        
        checks.iter().any(|check| check())
    }
    
    /// Check if running in WSL2
    fn is_wsl2(&self) -> bool {
        let checks = [
            // Check /proc/version for Microsoft/WSL
            || {
                if let Ok(content) = std::fs::read_to_string("/proc/version") {
                    content.to_lowercase().contains("microsoft") || 
                    content.to_lowercase().contains("wsl")
                } else {
                    false
                }
            },
            
            // WSL interop
            || Path::new("/proc/sys/fs/binfmt_misc/WSLInterop").exists(),
            
            // WSL environment variable
            || std::env::var("WSL_DISTRO_NAME").is_ok(),
            || std::env::var("WSLENV").is_ok(),
            
            // Check for WSL-specific paths
            || Path::new("/mnt/c/Windows").exists(),
        ];
        
        checks.iter().any(|check| check())
    }
    
    /// Detect cloud provider
    fn detect_cloud_provider(&self) -> Option<CloudProvider> {
        // Check cloud metadata services
        // These are typically available at link-local addresses
        
        // AWS - IMDSv2
        if self.check_aws_metadata() {
            return Some(CloudProvider::AWS);
        }
        
        // GCP
        if self.check_gcp_metadata() {
            return Some(CloudProvider::GCP);
        }
        
        // Azure
        if self.check_azure_metadata() {
            return Some(CloudProvider::Azure);
        }
        
        // DigitalOcean
        if self.check_digitalocean_metadata() {
            return Some(CloudProvider::DigitalOcean);
        }
        
        // Check vendor files
        if Path::new("/sys/class/dmi/id/sys_vendor").exists() {
            if let Ok(vendor) = std::fs::read_to_string("/sys/class/dmi/id/sys_vendor") {
                let vendor = vendor.to_lowercase();
                if vendor.contains("amazon") {
                    return Some(CloudProvider::AWS);
                } else if vendor.contains("google") {
                    return Some(CloudProvider::GCP);
                } else if vendor.contains("microsoft") {
                    return Some(CloudProvider::Azure);
                } else if vendor.contains("digitalocean") {
                    return Some(CloudProvider::DigitalOcean);
                } else if vendor.contains("oracle") {
                    return Some(CloudProvider::OracleCloud);
                } else if vendor.contains("alibaba") {
                    return Some(CloudProvider::AlibabaCloud);
                } else if vendor.contains("ibm") {
                    return Some(CloudProvider::IBMCloud);
                }
            }
        }
        
        None
    }
    
    /// Check AWS metadata service
    fn check_aws_metadata(&self) -> bool {
        // AWS IMDSv2 endpoint
        let output = Command::new("curl")
            .args([
                "-s", "-f",
                "--connect-timeout", "2",
                "-X", "PUT",
                "-H", "X-aws-ec2-metadata-token-ttl-seconds: 21600",
                "http://169.254.169.254/latest/api/token"
            ])
            .output();
        
        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    /// Check GCP metadata service
    fn check_gcp_metadata(&self) -> bool {
        let output = Command::new("curl")
            .args([
                "-s", "-f",
                "--connect-timeout", "2",
                "-H", "Metadata-Flavor: Google",
                "http://metadata.google.internal/computeMetadata/v1/"
            ])
            .output();
        
        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    /// Check Azure metadata service
    fn check_azure_metadata(&self) -> bool {
        let output = Command::new("curl")
            .args([
                "-s", "-f",
                "--connect-timeout", "2",
                "-H", "Metadata: true",
                "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
            ])
            .output();
        
        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    /// Check DigitalOcean metadata service
    fn check_digitalocean_metadata(&self) -> bool {
        let output = Command::new("curl")
            .args([
                "-s", "-f",
                "--connect-timeout", "2",
                "http://169.254.169.254/metadata/v1/"
            ])
            .output();
        
        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    /// Check if running on bare metal
    fn is_bare_metal(&self) -> bool {
        // Check for virtualization indicators
        let is_virtualized = self.check_virtualization();
        !is_virtualized
    }
    
    /// Check if system is virtualized
    fn check_virtualization(&self) -> bool {
        // Check systemd-detect-virt
        let output = Command::new("systemd-detect-virt")
            .arg("--quiet")
            .output();
        
        match output {
            Ok(output) => output.status.success(), // Returns 0 if virtualized
            Err(_) => {
                // Fallback: check DMI
                if Path::new("/sys/class/dmi/id/product_name").exists() {
                    if let Ok(product) = std::fs::read_to_string("/sys/class/dmi/id/product_name") {
                        let product = product.to_lowercase();
                        return product.contains("virtual") ||
                               product.contains("vmware") ||
                               product.contains("qemu") ||
                               product.contains("kvm") ||
                               product.contains("xen") ||
                               product.contains("hyper-v") ||
                               product.contains("parallels") ||
                               product.contains("virtualbox");
                    }
                }
                false
            }
        }
    }
    
    /// Detect hardware profile
    fn detect_hardware(&self) -> ScoutResult<HardwareProfile> {
        let cpu_cores = num_cpus::get();
        let cpu_arch = std::env::consts::ARCH.to_string();
        
        // Get CPU model
        let cpu_model = self.get_cpu_model();
        
        // Get memory info
        let (ram_total_gb, ram_available_gb, ram_usage_percent) = self.get_memory_info();
        
        // Get disk info
        let (disk_total_gb, disk_available_gb, disk_usage_percent) = self.get_disk_info();
        
        // Detect GPUs
        let gpu_info = self.detect_gpus();
        
        Ok(HardwareProfile {
            cpu_cores,
            cpu_model,
            cpu_arch,
            ram_total_gb,
            ram_available_gb,
            ram_usage_percent,
            disk_total_gb,
            disk_available_gb,
            disk_usage_percent,
            gpu_info,
        })
    }
    
    /// Get CPU model name
    fn get_cpu_model(&self) -> String {
        // Try /proc/cpuinfo
        if Path::new("/proc/cpuinfo").exists() {
            if let Ok(content) = std::fs::read_to_string("/proc/cpuinfo") {
                for line in content.lines() {
                    if line.starts_with("model name") || line.starts_with("Model name") {
                        if let Some((_, model)) = line.split_once(':') {
                            return model.trim().to_string();
                        }
                    }
                }
            }
        }
        
        // Fallback
        std::env::var("HOSTNAME").unwrap_or_else(|_| "Unknown CPU".to_string())
    }
    
    /// Get memory information
    fn get_memory_info(&self) -> (f64, f64, f64) {
        if Path::new("/proc/meminfo").exists() {
            if let Ok(content) = std::fs::read_to_string("/proc/meminfo") {
                let mut total_kb: u64 = 0;
                let mut available_kb: u64 = 0;
                
                for line in content.lines() {
                    if line.starts_with("MemTotal:") {
                        if let Some(kb) = line.split_whitespace().nth(1) {
                            total_kb = kb.parse().unwrap_or(0);
                        }
                    } else if line.starts_with("MemAvailable:") {
                        if let Some(kb) = line.split_whitespace().nth(1) {
                            available_kb = kb.parse().unwrap_or(0);
                        }
                    }
                }
                
                let total_gb = total_kb as f64 / 1024.0 / 1024.0;
                let available_gb = available_kb as f64 / 1024.0 / 1024.0;
                let usage_percent = if total_gb > 0.0 {
                    ((total_gb - available_gb) / total_gb) * 100.0
                } else {
                    0.0
                };
                
                return (total_gb, available_gb, usage_percent);
            }
        }
        
        // Default values
        (8.0, 4.0, 50.0)
    }
    
    /// Get disk information for home directory
    fn get_disk_info(&self) -> (f64, f64, f64) {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/root".to_string());
        
        // Use df command
        let output = Command::new("df")
            .args(["-BG", &home])
            .output();
        
        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let lines: Vec<&str> = stdout.lines().collect();
                if lines.len() >= 2 {
                    let parts: Vec<&str> = lines[1].split_whitespace().collect();
                    if parts.len() >= 4 {
                        let total_gb = parts[1].trim_end_matches('G').parse().unwrap_or(50.0);
                        let available_gb = parts[3].trim_end_matches('G').parse().unwrap_or(25.0);
                        let usage_percent = if total_gb > 0.0 {
                            ((total_gb - available_gb) / total_gb) * 100.0
                        } else {
                            0.0
                        };
                        return (total_gb, available_gb, usage_percent);
                    }
                }
            }
            Err(_) => {}
        }
        
        // Default values
        (50.0, 25.0, 50.0)
    }
    
    /// Detect available GPUs
    fn detect_gpus(&self) -> Vec<String> {
        let mut gpus = Vec::new();
        
        // Check for NVIDIA GPUs
        let output = Command::new("nvidia-smi")
            .args(["--query-gpu=name", "--format=csv,noheader"])
            .output();
        
        match output {
            Ok(output) if output.status.success() => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                for line in stdout.lines() {
                    let gpu = line.trim().to_string();
                    if !gpu.is_empty() {
                        gpus.push(gpu);
                    }
                }
            }
            _ => {}
        }
        
        gpus
    }
    
    /// Detect OS fingerprint
    fn detect_os(&self) -> ScoutResult<OSFingerprint> {
        let os_name = std::env::consts::OS.to_string();
        let arch = std::env::consts::ARCH.to_string();
        
        // Get hostname
        let hostname = gethostname::gethostname()
            .to_string_lossy()
            .to_string();
        
        // Get kernel version
        let kernel_version = self.get_kernel_version();
        
        // Get distro info (Linux)
        let (distro, distro_version) = self.get_distro_info();
        
        // Detect init system
        let init_system = self.detect_init_system();
        
        // Detect package manager
        let package_manager = self.detect_package_manager();
        
        Ok(OSFingerprint {
            os_name,
            os_version: kernel_version.clone(),
            distro,
            distro_version,
            kernel_version,
            arch,
            hostname,
            init_system,
            package_manager,
        })
    }
    
    /// Get kernel version
    fn get_kernel_version(&self) -> String {
        let output = Command::new("uname").arg("-r").output();
        
        match output {
            Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_string(),
            Err(_) => "unknown".to_string(),
        }
    }
    
    /// Get distribution info
    fn get_distro_info(&self) -> (Option<String>, Option<String>) {
        if Path::new("/etc/os-release").exists() {
            if let Ok(content) = std::fs::read_to_string("/etc/os-release") {
                let mut id = None;
                let mut version = None;
                
                for line in content.lines() {
                    if line.starts_with("ID=") {
                        id = Some(line[3..].trim_matches('"').to_string());
                    } else if line.starts_with("VERSION_ID=") {
                        version = Some(line[11..].trim_matches('"').to_string());
                    }
                }
                
                return (id, version);
            }
        }
        
        (None, None)
    }
    
    /// Detect init system
    fn detect_init_system(&self) -> String {
        // Check for systemd
        if Path::new("/run/systemd/system").exists() {
            return "systemd".to_string();
        }
        
        // Check for OpenRC
        if Path::new("/run/openrc").exists() || Path::new("/sbin/openrc").exists() {
            return "openrc".to_string();
        }
        
        // Check for launchd (macOS)
        if Path::new("/bin/launchctl").exists() {
            return "launchd".to_string();
        }
        
        "unknown".to_string()
    }
    
    /// Detect package manager
    fn detect_package_manager(&self) -> String {
        let package_managers = [
            ("apt", "apt"),
            ("dnf", "dnf"),
            ("yum", "yum"),
            ("pacman", "pacman"),
            ("zypper", "zypper"),
            ("apk", "apk"),
            ("emerge", "portage"),
            ("xbps-install", "xbps"),
            ("brew", "brew"),
        ];
        
        for (cmd, name) in package_managers {
            if which::which(cmd).is_ok() {
                return name.to_string();
            }
        }
        
        "unknown".to_string()
    }
    
    /// Check network capabilities
    fn check_network(&self) -> ScoutResult<NetworkCapabilities> {
        let mut capabilities = NetworkCapabilities {
            github_reachable: false,
            pypi_reachable: false,
            ollama_registry_reachable: false,
            has_internet: false,
            github_latency_ms: None,
            pypi_latency_ms: None,
        };
        
        // Check GitHub
        let start = std::time::Instant::now();
        let github_result = self.check_url("https://github.com", self.timeout_ms);
        capabilities.github_reachable = github_result;
        if github_result {
            capabilities.github_latency_ms = Some(start.elapsed().as_millis() as f64);
        }
        
        // Check PyPI
        let start = std::time::Instant::now();
        let pypi_result = self.check_url("https://pypi.org", self.timeout_ms);
        capabilities.pypi_reachable = pypi_result;
        if pypi_result {
            capabilities.pypi_latency_ms = Some(start.elapsed().as_millis() as f64);
        }
        
        // Check Ollama registry
        capabilities.ollama_registry_reachable = self.check_url(
            "https://registry.ollama.ai",
            self.timeout_ms
        );
        
        // Determine internet connectivity
        capabilities.has_internet = capabilities.github_reachable || capabilities.pypi_reachable;
        
        Ok(capabilities)
    }
    
    /// Check if a URL is reachable
    fn check_url(&self, url: &str, timeout_ms: u64) -> bool {
        let output = Command::new("curl")
            .args([
                "-s", "-f",
                "--connect-timeout", &(timeout_ms / 1000).to_string(),
                "--max-time", &(timeout_ms / 1000).to_string(),
                "-o", "/dev/null",
                url
            ])
            .output();
        
        match output {
            Ok(output) => output.status.success(),
            Err(_) => false,
        }
    }
    
    /// Check available tools
    fn check_tools(&self) -> ScoutResult<(Vec<String>, Vec<String>)> {
        let required_tools = ["git", "python3", "pip3", "curl", "tar"];
        let optional_tools = ["docker", "ollama", "npm", "node", "systemctl", "jq"];
        
        let mut available = Vec::new();
        let mut missing = Vec::new();
        
        // Check required tools
        for tool in &required_tools {
            if which::which(tool).is_ok() {
                available.push(tool.to_string());
            } else {
                missing.push(tool.to_string());
            }
        }
        
        // Check optional tools
        for tool in &optional_tools {
            if which::which(tool).is_ok() {
                available.push(tool.to_string());
            }
        }
        
        Ok((available, missing))
    }
    
    /// Get environment-specific configuration
    fn get_env_config(&self, env: &Environment) -> EnvironmentConfig {
        match env {
            Environment::GoogleColab => EnvironmentConfig::colab_default(),
            Environment::Docker => EnvironmentConfig::docker_default(),
            Environment::Kubernetes => EnvironmentConfig::kubernetes_default(),
            Environment::WSL2 => EnvironmentConfig::wsl2_default(),
            Environment::CloudVM(_) => EnvironmentConfig::cloud_vm_default(),
            Environment::BareMetal => EnvironmentConfig::bare_metal_default(),
            Environment::Unknown => EnvironmentConfig::bare_metal_default(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_detector_creation() {
        let detector = EnvironmentDetector::default();
        assert_eq!(detector.timeout_ms, 5000);
    }
    
    #[test]
    fn test_detect_hardware() {
        let detector = EnvironmentDetector::default();
        let hardware = detector.detect_hardware().unwrap();
        
        assert!(hardware.cpu_cores > 0);
        assert!(hardware.ram_total_gb > 0.0);
    }
    
    #[test]
    fn test_detect_os() {
        let detector = EnvironmentDetector::default();
        let os = detector.detect_os().unwrap();
        
        assert!(!os.os_name.is_empty());
        assert!(!os.arch.is_empty());
    }
}
