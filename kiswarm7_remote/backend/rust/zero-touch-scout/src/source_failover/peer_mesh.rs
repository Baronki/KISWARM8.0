//! Level 4: Peer Mesh Source Implementation
//!
//! Quaternary source using P2P mesh network with Byzantine consensus.
//! Features:
//! - Distributed peer discovery
//! - Byzantine fault tolerance for untrusted peers
//! - Gossip protocol for content propagation
//! - Reputation-based peer scoring

use super::types::*;
use crate::error::{ScoutError, ScoutResult};
use crate::logging::AuditLogger;
use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;
use tokio::sync::RwLock;

/// Peer information in the mesh network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MeshPeer {
    /// Unique peer identifier
    pub peer_id: String,
    
    /// Network endpoints
    pub endpoints: Vec<PeerEndpoint>,
    
    /// Reputation score (0.0 to 1.0)
    pub reputation: f64,
    
    /// Last successful connection
    pub last_seen: Option<String>,
    
    /// Peer capabilities
    pub capabilities: Vec<PeerCapability>,
    
    /// Geographic region
    pub region: Option<String>,
    
    /// Connection statistics
    pub stats: PeerConnectionStats,
}

/// Peer network endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerEndpoint {
    /// Endpoint URL
    pub url: String,
    
    /// Endpoint type
    pub endpoint_type: EndpointType,
    
    /// Priority
    pub priority: u32,
}

/// Type of peer endpoint
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EndpointType {
    /// HTTP/HTTPS endpoint
    HTTP,
    
    /// WebSocket endpoint
    WebSocket,
    
    /// libp2p endpoint
    LibP2P,
    
    /// QUIC endpoint
    QUIC,
}

/// Peer capability
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PeerCapability {
    /// Can serve files
    FileServer,
    
    /// Can relay connections
    Relay,
    
    /// Can provide DHT queries
    DHTProvider,
    
    /// Has storage capacity
    Storage,
    
    /// Can verify signatures
    SignatureVerifier,
}

/// Peer connection statistics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PeerConnectionStats {
    /// Total connections attempted
    pub total_connections: u64,
    
    /// Successful connections
    pub successful_connections: u64,
    
    /// Bytes transferred
    pub bytes_transferred: u64,
    
    /// Average latency (ms)
    pub avg_latency_ms: f64,
    
    /// Last error
    pub last_error: Option<String>,
}

/// Peer mesh configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerMeshConfig {
    /// Bootstrap peers (well-known entry points)
    pub bootstrap_peers: Vec<String>,
    
    /// Maximum peers to maintain connections with
    pub max_peers: usize,
    
    /// Minimum peers required for consensus
    pub min_consensus_peers: usize,
    
    /// Byzantine consensus threshold (fraction, e.g., 0.67 for 2/3)
    pub consensus_threshold: f64,
    
    /// Peer timeout
    pub peer_timeout_secs: u64,
    
    /// Reputation threshold for trusted peers
    pub reputation_threshold: f64,
    
    /// Enable gossip protocol
    pub enable_gossip: bool,
    
    /// User agent
    pub user_agent: String,
    
    /// Local peer ID
    pub local_peer_id: Option<String>,
}

impl Default for PeerMeshConfig {
    fn default() -> Self {
        Self {
            bootstrap_peers: vec![
                "https://mesh.kiswarm.io/peer/alpha".to_string(),
                "https://mesh.kiswarm.io/peer/beta".to_string(),
                "https://mesh.kiswarm.io/peer/gamma".to_string(),
            ],
            max_peers: 50,
            min_consensus_peers: 3,
            consensus_threshold: 0.67,
            peer_timeout_secs: 120,
            reputation_threshold: 0.5,
            enable_gossip: true,
            user_agent: "KISWARM-ZeroTouchScout/6.3.5".to_string(),
            local_peer_id: None,
        }
    }
}

/// Byzantine consensus result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusResult {
    /// Whether consensus was reached
    pub reached: bool,
    
    /// Agreed value (e.g., checksum)
    pub value: Option<String>,
    
    /// Number of agreeing peers
    pub agreeing_peers: usize,
    
    /// Total peers queried
    pub total_peers: usize,
    
    /// Consensus ratio
    pub ratio: f64,
}

/// Peer Mesh Source implementation
pub struct PeerMeshSource {
    /// Configuration
    config: PeerMeshConfig,
    
    /// HTTP client
    client: Client,
    
    /// Source statistics
    stats: SourceStats,
    
    /// Known peers
    peers: Arc<RwLock<HashMap<String, MeshPeer>>>,
    
    /// Message queue for gossip
    message_queue: Arc<RwLock<VecDeque<GossipMessage>>>,
    
    /// Logger
    logger: Option<Arc<AuditLogger>>,
}

/// Gossip message for mesh communication
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GossipMessage {
    /// Message ID
    pub message_id: String,
    
    /// Message type
    pub message_type: GossipMessageType,
    
    /// Payload
    pub payload: String,
    
    /// Sender peer ID
    pub sender: String,
    
    /// Timestamp
    pub timestamp: String,
    
    /// TTL (hops remaining)
    pub ttl: u8,
}

/// Type of gossip message
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GossipMessageType {
    /// Peer announcement
    PeerAnnounce,
    
    /// Content announcement
    ContentAnnounce,
    
    /// Content request
    ContentRequest,
    
    /// Content response
    ContentResponse,
    
    /// Consensus proposal
    ConsensusProposal,
    
    /// Consensus vote
    ConsensusVote,
}

impl PeerMeshSource {
    /// Create a new Peer Mesh source
    pub fn new(config: PeerMeshConfig) -> ScoutResult<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(config.peer_timeout_secs))
            .user_agent(&config.user_agent)
            .pool_max_idle_per_host(10)
            .build()
            .map_err(|e| ScoutError::NetworkError(format!("Failed to create HTTP client: {}", e)))?;
        
        Ok(Self {
            config,
            client,
            stats: SourceStats::new(),
            peers: Arc::new(RwLock::new(HashMap::new())),
            message_queue: Arc::new(RwLock::new(VecDeque::new())),
            logger: None,
        })
    }
    
    /// Set logger
    pub fn with_logger(mut self, logger: Arc<AuditLogger>) -> Self {
        self.logger = Some(logger);
        self
    }
    
    /// Discover peers from bootstrap nodes
    async fn discover_peers(&self) -> ScoutResult<Vec<MeshPeer>> {
        let mut discovered = Vec::new();
        
        for bootstrap_url in &self.config.bootstrap_peers {
            match self.query_bootstrap_peer(bootstrap_url).await {
                Ok(mut peers) => discovered.append(&mut peers),
                Err(e) => {
                    if let Some(logger) = &self.logger {
                        let _ = logger.warn("Bootstrap peer query failed", serde_json::json!({
                            "url": bootstrap_url,
                            "error": e.to_string(),
                        }));
                    }
                }
            }
        }
        
        // Sort by reputation
        discovered.sort_by(|a, b| b.reputation.partial_cmp(&a.reputation).unwrap_or(std::cmp::Ordering::Equal));
        
        // Limit to max peers
        discovered.truncate(self.config.max_peers);
        
        Ok(discovered)
    }
    
    /// Query a bootstrap peer for more peers
    async fn query_bootstrap_peer(&self, url: &str) -> ScoutResult<Vec<MeshPeer>> {
        let peers_url = format!("{}/api/v1/peers", url);
        
        let response = self.client
            .get(&peers_url)
            .timeout(Duration::from_secs(10))
            .send()
            .await
            .map_err(|e| ScoutError::NetworkError(e.to_string()))?;
        
        if !response.status().is_success() {
            return Err(ScoutError::NetworkError(
                format!("Bootstrap peer returned {}", response.status().as_u16())
            ));
        }
        
        let peers: Vec<MeshPeer> = response.json().await
            .map_err(|e| ScoutError::NetworkError(format!("Failed to parse peer list: {}", e)))?;
        
        Ok(peers)
    }
    
    /// Request artifact from a specific peer
    async fn request_from_peer(
        &self,
        peer: &MeshPeer,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<u64> {
        let endpoint = peer.endpoints.iter()
            .find(|e| e.endpoint_type == EndpointType::HTTP)
            .ok_or_else(|| ScoutError::NetworkError("No HTTP endpoint available".to_string()))?;
        
        let url = format!("{}/api/v1/artifacts/{}", endpoint.url, artifact.name);
        let start = Instant::now();
        
        if let Some(logger) = &self.logger {
            logger.info("Starting peer mesh download", serde_json::json!({
                "peer_id": &peer.peer_id,
                "artifact": &artifact.name,
                "url": &url,
            }))?;
        }
        
        let response = self.client
            .get(&url)
            .send()
            .await
            .map_err(|e| ScoutError::DownloadFailed {
                source: url.clone(),
                reason: e.to_string(),
            })?;
        
        if !response.status().is_success() {
            return Err(ScoutError::DownloadFailed {
                source: url.clone(),
                reason: format!("HTTP {}", response.status().as_u16()),
            });
        }
        
        let total_size = response.content_length().unwrap_or(0);
        
        // Create parent directory
        if let Some(parent) = dest.parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| ScoutError::DirectoryCreationFailed { path: parent.to_path_buf() })?;
        }
        
        // Download file
        let mut file = tokio::fs::File::create(dest)
            .await
            .map_err(|e| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        let mut downloaded: u64 = 0;
        let mut stream = response.bytes_stream();
        
        use futures::StreamExt;
        
        while let Some(chunk_result) = stream.next().await {
            let chunk = chunk_result
                .map_err(|e| ScoutError::DownloadFailed {
                    source: url.clone(),
                    reason: e.to_string(),
                })?;
            
            file.write_all(&chunk).await
                .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
            
            downloaded += chunk.len() as u64;
            
            if let Some(ref callback) = progress_callback {
                callback(downloaded, total_size);
            }
        }
        
        file.flush().await
            .map_err(|_| ScoutError::FileWriteFailed { path: dest.clone() })?;
        
        if let Some(logger) = &self.logger {
            logger.info("Peer mesh download complete", serde_json::json!({
                "peer_id": &peer.peer_id,
                "bytes": downloaded,
                "duration_ms": start.elapsed().as_millis(),
            }))?;
        }
        
        Ok(downloaded)
    }
    
    /// Perform Byzantine consensus on artifact checksum
    async fn consensus_check(
        &self,
        peers: &[MeshPeer],
        artifact: &Artifact,
    ) -> ScoutResult<ConsensusResult> {
        let checksum_key = format!("checksum:{}", artifact.name);
        let mut checksum_votes: HashMap<String, usize> = HashMap::new();
        let mut total_responses = 0;
        
        // Query each peer for their checksum
        for peer in peers.iter().take(self.config.min_consensus_peers) {
            let endpoint = peer.endpoints.iter()
                .find(|e| e.endpoint_type == EndpointType::HTTP);
            
            let Some(endpoint) = endpoint else { continue };
            
            let url = format!("{}/api/v1/verify/{}", endpoint.url, artifact.name);
            
            if let Ok(response) = self.client
                .get(&url)
                .timeout(Duration::from_secs(10))
                .send()
                .await
            {
                if response.status().is_success() {
                    if let Ok(body) = response.json::<serde_json::Value>().await {
                        if let Some(checksum) = body["checksum"].as_str() {
                            *checksum_votes.entry(checksum.to_string()).or_insert(0) += 1;
                            total_responses += 1;
                        }
                    }
                }
            }
        }
        
        // Find most voted checksum
        let (most_voted, votes) = checksum_votes.iter()
            .max_by_key(|(_, v)| *v)
            .map(|(k, v)| (k.clone(), *v))
            .unwrap_or((String::new(), 0));
        
        let ratio = if total_responses > 0 {
            votes as f64 / total_responses as f64
        } else {
            0.0
        };
        
        let reached = ratio >= self.config.consensus_threshold && 
            votes >= self.config.min_consensus_peers;
        
        Ok(ConsensusResult {
            reached,
            value: if reached { Some(most_voted) } else { None },
            agreeing_peers: votes,
            total_peers: total_responses,
            ratio,
        })
    }
    
    /// Get peers sorted by reputation
    async fn get_trusted_peers(&self) -> Vec<MeshPeer> {
        let peers = self.peers.read().await;
        let mut trusted: Vec<_> = peers.values()
            .filter(|p| p.reputation >= self.config.reputation_threshold)
            .cloned()
            .collect();
        
        trusted.sort_by(|a, b| b.reputation.partial_cmp(&a.reputation).unwrap_or(std::cmp::Ordering::Equal));
        trusted
    }
    
    /// Update peer reputation
    async fn update_peer_reputation(&self, peer_id: &str, success: bool) {
        let mut peers = self.peers.write().await;
        if let Some(peer) = peers.get_mut(peer_id) {
            // Update reputation using exponential moving average
            let delta = if success { 0.1 } else { -0.2 };
            peer.reputation = (peer.reputation + delta).clamp(0.0, 1.0);
            peer.last_seen = Some(chrono::Utc::now().to_rfc3339());
        }
    }
}

#[async_trait::async_trait]
impl Source for PeerMeshSource {
    fn level(&self) -> SourceLevel {
        SourceLevel::PeerMesh
    }
    
    fn name(&self) -> &str {
        "peer-mesh"
    }
    
    async fn check_availability(&self) -> ScoutResult<SourceHealth> {
        // Try to discover peers
        let peers = self.discover_peers().await?;
        
        // Update stored peers
        {
            let mut stored_peers = self.peers.write().await;
            for peer in &peers {
                stored_peers.insert(peer.peer_id.clone(), peer.clone());
            }
        }
        
        // Check if we have enough peers for consensus
        let trusted_peers = self.get_trusted_peers().await;
        
        if trusted_peers.is_empty() {
            Ok(SourceHealth::Unhealthy {
                reason: UnhealthyReason::NoPeers,
            })
        } else if trusted_peers.len() < self.config.min_consensus_peers {
            Ok(SourceHealth::Degraded {
                reason: DegradationReason::PartialAvailability,
            })
        } else {
            Ok(SourceHealth::Healthy)
        }
    }
    
    async fn fetch(
        &self,
        artifact: &Artifact,
        dest: &PathBuf,
        progress_callback: Option<Arc<dyn Fn(u64, u64) + Send + Sync>>,
    ) -> ScoutResult<FetchResult> {
        let start = Instant::now();
        let mut failover_history = Vec::new();
        
        // Discover peers if needed
        let peers = self.get_trusted_peers().await;
        
        if peers.is_empty() {
            // Try to discover peers
            let discovered = self.discover_peers().await?;
            if discovered.is_empty() {
                return Err(ScoutError::NetworkError("No peers available in mesh".to_string()));
            }
            
            // Store discovered peers
            {
                let mut stored = self.peers.write().await;
                for peer in &discovered {
                    stored.insert(peer.peer_id.clone(), peer.clone());
                }
            }
        }
        
        let peers = self.get_trusted_peers().await;
        
        // Perform consensus check on artifact checksum
        let consensus = self.consensus_check(&peers, artifact).await?;
        
        if !consensus.reached {
            if let Some(logger) = &self.logger {
                logger.warn("Consensus not reached", serde_json::json!({
                    "artifact": &artifact.name,
                    "ratio": consensus.ratio,
                    "peers_queried": consensus.total_peers,
                }))?;
            }
            
            // Continue anyway but note the lack of consensus
            if consensus.total_peers < self.config.min_consensus_peers {
                return Err(ScoutError::NetworkError(
                    format!("Insufficient consensus: {} peers, need {}", 
                        consensus.total_peers, self.config.min_consensus_peers)
                ));
            }
        }
        
        // Try to fetch from peers in reputation order
        let mut last_error: Option<ScoutError> = None;
        
        for peer in &peers {
            let peer_start = Instant::now();
            
            match self.request_from_peer(peer, artifact, dest, progress_callback.clone()).await {
                Ok(bytes) => {
                    // Update peer reputation
                    self.update_peer_reputation(&peer.peer_id, true).await;
                    
                    // Verify checksum if consensus was reached
                    let checksum_verified = if let Some(ref expected) = consensus.value {
                        use sha2::{Digest, Sha256};
                        let content = tokio::fs::read(dest).await
                            .map_err(|_| ScoutError::FileReadFailed { path: dest.clone() })?;
                        let mut hasher = Sha256::new();
                        hasher.update(&content);
                        format!("{:x}", hasher.finalize()) == *expected
                    } else {
                        false
                    };
                    
                    return Ok(FetchResult {
                        source_level: SourceLevel::PeerMesh,
                        source_name: format!("peer-{}", peer.peer_id),
                        local_path: dest.clone(),
                        bytes_transferred: bytes,
                        duration: start.elapsed(),
                        attempts: (failover_history.len() + 1) as u8,
                        checksum_verified,
                        signature_verified: false,
                        timestamp: chrono::Utc::now().to_rfc3339(),
                        failover_history,
                    });
                }
                Err(e) => {
                    // Update peer reputation
                    self.update_peer_reputation(&peer.peer_id, false).await;
                    
                    failover_history.push(FailoverEntry {
                        source_level: SourceLevel::PeerMesh,
                        source_name: format!("peer-{}", peer.peer_id),
                        failure_reason: e.to_string(),
                        time_spent: peer_start.elapsed(),
                        retry_attempts: 1,
                    });
                    last_error = Some(e);
                }
            }
        }
        
        Err(last_error.unwrap_or(ScoutError::AllSourcesExhausted))
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
    fn test_peer_mesh_config_default() {
        let config = PeerMeshConfig::default();
        assert!(!config.bootstrap_peers.is_empty());
        assert_eq!(config.consensus_threshold, 0.67);
    }
    
    #[test]
    fn test_consensus_result() {
        let result = ConsensusResult {
            reached: true,
            value: Some("abc123".to_string()),
            agreeing_peers: 5,
            total_peers: 7,
            ratio: 0.71,
        };
        
        assert!(result.reached);
        assert!(result.ratio >= 0.67);
    }
    
    #[test]
    fn test_peer_reputation_update() {
        let config = PeerMeshConfig::default();
        let source = PeerMeshSource::new(config).unwrap();
        
        // Add a test peer
        {
            let mut peers = futures::executor::block_on(source.peers.write());
            peers.insert("test-peer".to_string(), MeshPeer {
                peer_id: "test-peer".to_string(),
                endpoints: vec![],
                reputation: 0.5,
                last_seen: None,
                capabilities: vec![],
                region: None,
                stats: PeerConnectionStats::default(),
            });
        }
        
        // Update reputation
        futures::executor::block_on(source.update_peer_reputation("test-peer", true));
        
        let peers = futures::executor::block_on(source.peers.read());
        assert_eq!(peers["test-peer"].reputation, 0.6);
    }
}
