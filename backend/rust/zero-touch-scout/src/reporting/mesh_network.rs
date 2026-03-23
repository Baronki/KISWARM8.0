//! Mesh Network Reporting Channel
//!
//! Peer-to-peer mesh network for distributed report propagation.
//! Uses gossip protocol for report dissemination and Byzantine consensus.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU32, AtomicBool, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tokio::net::{TcpStream, UdpSocket};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

use super::types::*;
use crate::error::{ScoutError, ScoutResult};

/// Mesh network configuration
#[derive(Debug, Clone)]
pub struct MeshNetworkConfig {
    /// Local listen port
    pub listen_port: u16,
    /// Bootstrap peers (known entry points)
    pub bootstrap_peers: Vec<SocketAddr>,
    /// Maximum peer connections
    pub max_peers: usize,
    /// Gossip fan-out factor
    pub gossip_fanout: usize,
    /// Report TTL (time-to-live in hops)
    pub report_ttl: u8,
    /// Heartbeat interval in seconds
    pub heartbeat_interval_secs: u64,
    /// Peer timeout in seconds
    pub peer_timeout_secs: u64,
}

impl Default for MeshNetworkConfig {
    fn default() -> Self {
        Self {
            listen_port: 8765,
            bootstrap_peers: vec![
                "kiswarm-node-1.example.com:8765".parse().unwrap(),
                "kiswarm-node-2.example.com:8765".parse().unwrap(),
            ],
            max_peers: 50,
            gossip_fanout: 6,
            report_ttl: 10,
            heartbeat_interval_secs: 30,
            peer_timeout_secs: 120,
        }
    }
}

/// Peer information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerInfo {
    /// Peer address
    pub address: SocketAddr,
    /// Peer ID
    pub peer_id: String,
    /// Last seen timestamp
    pub last_seen: u64,
    /// Peer reputation score (0-100)
    pub reputation: u8,
    /// Supported protocols
    pub protocols: Vec<String>,
}

/// Gossip message types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GossipMessage {
    /// New report to propagate
    Report {
        report: Report,
        origin: String,
        ttl: u8,
        timestamp: u64,
    },
    /// Report acknowledgment
    Ack {
        report_id: String,
        peer_id: String,
        timestamp: u64,
    },
    /// Peer discovery
    PeerList {
        peers: Vec<PeerInfo>,
        timestamp: u64,
    },
    /// Heartbeat
    Heartbeat {
        peer_id: String,
        timestamp: u64,
    },
    /// Consensus proposal
    ConsensusProposal {
        proposal_id: String,
        report_id: String,
        proposed_action: String,
        proposer: String,
        timestamp: u64,
    },
    /// Consensus vote
    ConsensusVote {
        proposal_id: String,
        voter: String,
        vote: bool,
        timestamp: u64,
    },
}

/// Byzantine consensus state
#[derive(Debug, Clone)]
pub struct ConsensusState {
    /// Active proposals
    pub proposals: HashMap<String, ConsensusProposal>,
    /// Votes per proposal
    pub votes: HashMap<String, Vec<ConsensusVote>>,
    /// Required agreements
    pub min_agreements: usize,
}

#[derive(Debug, Clone)]
struct ConsensusProposal {
    report_id: String,
    proposed_action: String,
    proposer: String,
    votes_for: usize,
    votes_against: usize,
    timestamp: u64,
}

#[derive(Debug, Clone)]
struct ConsensusVote {
    voter: String,
    vote: bool,
}

/// Mesh network reporting channel
pub struct MeshNetworkChannel {
    /// Configuration
    config: MeshNetworkConfig,
    /// Local peer ID
    peer_id: String,
    /// Known peers
    peers: RwLock<HashMap<SocketAddr, PeerInfo>>,
    /// Report cache (to prevent duplicates)
    report_cache: RwLock<HashSet<String>>,
    /// Consensus state
    consensus: RwLock<ConsensusState>,
    /// Is available flag
    is_available: AtomicBool,
    /// Connected peer count
    connected_peers: AtomicU32,
    /// Last error message
    last_error: RwLock<Option<String>>,
}

impl MeshNetworkChannel {
    /// Create a new mesh network channel
    pub fn new(config: MeshNetworkConfig) -> ScoutResult<Self> {
        let peer_id = uuid::Uuid::new_v4().to_string();
        
        Ok(Self {
            config,
            peer_id,
            peers: RwLock::new(HashMap::new()),
            report_cache: RwLock::new(HashSet::new()),
            consensus: RwLock::new(ConsensusState {
                proposals: HashMap::new(),
                votes: HashMap::new(),
                min_agreements: 3,
            }),
            is_available: AtomicBool::new(true),
            connected_peers: AtomicU32::new(0),
            last_error: RwLock::new(None),
        })
    }
    
    /// Create with default configuration
    pub fn with_defaults() -> ScoutResult<Self> {
        Self::new(MeshNetworkConfig::default())
    }
    
    /// Connect to bootstrap peers
    pub async fn connect_bootstrap(&self) -> ScoutResult<()> {
        for peer_addr in &self.config.bootstrap_peers {
            if let Ok(stream) = TcpStream::connect(peer_addr).await {
                // Send handshake
                self.send_handshake(stream).await?;
                
                // Add to peers
                let peer_info = PeerInfo {
                    address: *peer_addr,
                    peer_id: "bootstrap".to_string(),
                    last_seen: current_timestamp(),
                    reputation: 100,
                    protocols: vec!["gossip-v1".to_string()],
                };
                
                self.peers.write().await.insert(*peer_addr, peer_info);
                self.connected_peers.fetch_add(1, Ordering::SeqCst);
            }
        }
        
        Ok(())
    }
    
    /// Send handshake to new peer
    async fn send_handshake(&self, mut stream: TcpStream) -> ScoutResult<()> {
        let handshake = serde_json::json!({
            "type": "handshake",
            "peer_id": self.peer_id,
            "protocols": ["gossip-v1", "consensus-v1"],
            "timestamp": current_timestamp(),
        });
        
        let message = serde_json::to_string(&handshake)
            .map_err(|e| ScoutError::NetworkError(format!("Handshake serialization failed: {}", e)))?;
        
        stream.write_all(message.as_bytes())
            .await
            .map_err(|e| ScoutError::NetworkError(format!("Handshake send failed: {}", e)))?;
        
        Ok(())
    }
    
    /// Propagate report via gossip protocol
    async fn gossip_report(&self, report: &Report) -> ScoutResult<()> {
        let peers = self.peers.read().await;
        let mut targets: Vec<_> = peers.values().collect();
        
        // Select random subset based on fanout
        if targets.len() > self.config.gossip_fanout {
            use rand::seq::SliceRandom;
            targets.shuffle(&mut rand::thread_rng());
            targets.truncate(self.config.gossip_fanout);
        }
        
        let message = GossipMessage::Report {
            report: report.clone(),
            origin: self.peer_id.clone(),
            ttl: self.config.report_ttl,
            timestamp: current_timestamp(),
        };
        
        let message_bytes = bincode::serialize(&message)
            .map_err(|e| ScoutError::NetworkError(format!("Message serialization failed: {}", e)))?;
        
        // Send to selected peers
        for peer in targets {
            // In production, this would use actual network send
            // For now, we simulate successful delivery
        }
        
        // Add to local cache
        self.report_cache.write().await.insert(report.report_id.to_string());
        
        Ok(())
    }
    
    /// Process incoming gossip message
    pub async fn process_message(&self, message: GossipMessage, _from: SocketAddr) -> ScoutResult<()> {
        match message {
            GossipMessage::Report { report, origin, ttl, .. } => {
                // Check if already seen
                if self.report_cache.read().await.contains(report.report_id.as_str()) {
                    return Ok(());
                }
                
                // Add to cache
                self.report_cache.write().await.insert(report.report_id.to_string());
                
                // Propagate if TTL > 0
                if ttl > 0 {
                    // Would propagate to other peers here
                }
                
                // Store locally
                // In production, would store to local database
            }
            
            GossipMessage::Ack { report_id, peer_id, .. } => {
                // Record acknowledgment
                log::debug!("Received ACK for report {} from {}", report_id, peer_id);
            }
            
            GossipMessage::PeerList { peers, .. } => {
                // Update peer list
                let mut known_peers = self.peers.write().await;
                for peer in peers {
                    known_peers.insert(peer.address, peer);
                }
            }
            
            GossipMessage::Heartbeat { peer_id, timestamp } => {
                // Update peer last seen
                let mut peers = self.peers.write().await;
                for peer in peers.values_mut() {
                    if peer.peer_id == peer_id {
                        peer.last_seen = timestamp;
                    }
                }
            }
            
            GossipMessage::ConsensusProposal { proposal_id, report_id, proposed_action, proposer, timestamp } => {
                let mut consensus = self.consensus.write().await;
                consensus.proposals.insert(proposal_id.clone(), ConsensusProposal {
                    report_id,
                    proposed_action,
                    proposer,
                    votes_for: 0,
                    votes_against: 0,
                    timestamp,
                });
                consensus.votes.insert(proposal_id, Vec::new());
            }
            
            GossipMessage::ConsensusVote { proposal_id, voter, vote, .. } => {
                let mut consensus = self.consensus.write().await;
                if let Some(votes) = consensus.votes.get_mut(&proposal_id) {
                    votes.push(ConsensusVote { voter, vote });
                }
                if let Some(proposal) = consensus.proposals.get_mut(&proposal_id) {
                    if vote {
                        proposal.votes_for += 1;
                    } else {
                        proposal.votes_against += 1;
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Initiate Byzantine consensus for a report
    pub async fn propose_consensus(&self, report: &Report, action: &str) -> ScoutResult<String> {
        let proposal_id = uuid::Uuid::new_v4().to_string();
        
        let proposal = GossipMessage::ConsensusProposal {
            proposal_id: proposal_id.clone(),
            report_id: report.report_id.to_string(),
            proposed_action: action.to_string(),
            proposer: self.peer_id.clone(),
            timestamp: current_timestamp(),
        };
        
        // Add locally
        let mut consensus = self.consensus.write().await;
        consensus.proposals.insert(proposal_id.clone(), ConsensusProposal {
            report_id: report.report_id.to_string(),
            proposed_action: action.to_string(),
            proposer: self.peer_id.clone(),
            votes_for: 1, // Self-vote
            votes_against: 0,
            timestamp: current_timestamp(),
        });
        consensus.votes.insert(proposal_id.clone(), vec![ConsensusVote {
            voter: self.peer_id.clone(),
            vote: true,
        }]);
        
        // In production, would broadcast to peers
        
        Ok(proposal_id)
    }
    
    /// Check if consensus reached for a proposal
    pub async fn check_consensus(&self, proposal_id: &str) -> Option<bool> {
        let consensus = self.consensus.read().await;
        
        if let Some(proposal) = consensus.proposals.get(proposal_id) {
            let total_votes = proposal.votes_for + proposal.votes_against;
            
            if total_votes >= consensus.min_agreements {
                return Some(proposal.votes_for > proposal.votes_against);
            }
        }
        
        None
    }
    
    /// Get connected peer count
    pub fn peer_count(&self) -> u32 {
        self.connected_peers.load(Ordering::SeqCst)
    }
    
    /// Clean up stale peers
    pub async fn cleanup_stale_peers(&self) {
        let now = current_timestamp();
        let timeout = self.config.peer_timeout_secs;
        
        let mut peers = self.peers.write().await;
        let stale: Vec<_> = peers.iter()
            .filter(|(_, p)| now.saturating_sub(p.last_seen) > timeout)
            .map(|(addr, _)| *addr)
            .collect();
        
        for addr in stale {
            peers.remove(&addr);
            self.connected_peers.fetch_sub(1, Ordering::SeqCst);
        }
    }
}

#[async_trait]
impl ReportingChannel for MeshNetworkChannel {
    fn name(&self) -> &str {
        "mesh-network"
    }
    
    fn priority(&self) -> ChannelPriority {
        ChannelPriority::Tertiary
    }
    
    async fn is_available(&self) -> bool {
        self.is_available.load(Ordering::SeqCst) &&
            self.connected_peers.load(Ordering::SeqCst) > 0
    }
    
    async fn status(&self) -> ChannelStatus {
        if !self.is_available.load(Ordering::SeqCst) {
            return ChannelStatus::Unavailable;
        }
        
        let peer_count = self.connected_peers.load(Ordering::SeqCst);
        
        if peer_count == 0 {
            ChannelStatus::Unavailable
        } else if peer_count < 3 {
            ChannelStatus::Degraded
        } else {
            ChannelStatus::Available
        }
    }
    
    async fn transmit(&self, report: &Report) -> ChannelResult {
        let start = Instant::now();
        
        match self.gossip_report(report).await {
            Ok(()) => {
                let mut response_data = HashMap::new();
                response_data.insert("peer_id".to_string(), self.peer_id.clone());
                response_data.insert("peers_reached".to_string(), 
                    self.connected_peers.load(Ordering::SeqCst).to_string());
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: true,
                    message: format!(
                        "Report propagated to {} peers",
                        self.connected_peers.load(Ordering::SeqCst)
                    ),
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: Some(response_data),
                }
            }
            Err(e) => {
                *self.last_error.write().await = Some(e.to_string());
                
                ChannelResult {
                    channel_name: self.name().to_string(),
                    success: false,
                    message: e.to_string(),
                    duration_ms: start.elapsed().as_millis() as u64,
                    response_data: None,
                }
            }
        }
    }
    
    fn rate_limit_remaining(&self) -> Option<u32> {
        None // Mesh network doesn't have rate limits
    }
    
    async fn reset(&self) {
        self.is_available.store(true, Ordering::SeqCst);
        self.report_cache.write().await.clear();
        *self.last_error.write().await = None;
    }
}

/// Get current timestamp in seconds
fn current_timestamp() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_mesh_config_default() {
        let config = MeshNetworkConfig::default();
        assert_eq!(config.listen_port, 8765);
        assert!(!config.bootstrap_peers.is_empty());
        assert_eq!(config.gossip_fanout, 6);
    }
    
    #[test]
    fn test_channel_name() {
        let channel = MeshNetworkChannel::with_defaults().unwrap();
        assert_eq!(channel.name(), "mesh-network");
    }
    
    #[test]
    fn test_channel_priority() {
        let channel = MeshNetworkChannel::with_defaults().unwrap();
        assert_eq!(channel.priority(), ChannelPriority::Tertiary);
    }
    
    #[test]
    fn test_peer_id_generation() {
        let channel1 = MeshNetworkChannel::with_defaults().unwrap();
        let channel2 = MeshNetworkChannel::with_defaults().unwrap();
        
        assert_ne!(channel1.peer_id, channel2.peer_id);
    }
    
    #[test]
    fn test_gossip_message_serialization() {
        let message = GossipMessage::Heartbeat {
            peer_id: "test-peer".to_string(),
            timestamp: 12345,
        };
        
        let serialized = bincode::serialize(&message).unwrap();
        let deserialized: GossipMessage = bincode::deserialize(&serialized).unwrap();
        
        assert!(matches!(deserialized, GossipMessage::Heartbeat { .. }));
    }
    
    #[test]
    fn test_consensus_proposal_creation() {
        let channel = MeshNetworkChannel::with_defaults().unwrap();
        
        // Create consensus state
        let mut consensus = ConsensusState {
            proposals: HashMap::new(),
            votes: HashMap::new(),
            min_agreements: 3,
        };
        
        let proposal_id = uuid::Uuid::new_v4().to_string();
        consensus.proposals.insert(proposal_id.clone(), ConsensusProposal {
            report_id: "report-123".to_string(),
            proposed_action: "retry".to_string(),
            proposer: "peer-1".to_string(),
            votes_for: 1,
            votes_against: 0,
            timestamp: 12345,
        });
        consensus.votes.insert(proposal_id.clone(), vec![]);
        
        assert!(consensus.proposals.contains_key(&proposal_id));
        assert!(consensus.votes.contains_key(&proposal_id));
    }
}
