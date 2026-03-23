//! Source Failover System for KISWARM Zero-Touch Scout
//!
//! This module implements a 5-level failover architecture for robust source access:
//!
//! # Architecture
//!
//! ```text
//! ┌─────────────────────────────────────────────────────────────────────┐
//! │                    SOURCE FAILOVER HIERARCHY                        │
//! ├─────────────────────────────────────────────────────────────────────┤
//! │                                                                     │
//! │  Level 1: GITHUB (Primary)                                         │
//! │  └── Direct repository access with rate limit awareness            │
//! │      └── Fall through on: timeout, rate limit, 5xx errors         │
//! │                                                                     │
//! │  Level 2: CDN (Secondary)                                          │
//! │  └── Cloudflare, AWS CloudFront, Fastly mirrors                   │
//! │      └── Fall through on: timeout, certificate errors, 404        │
//! │                                                                     │
//! │  Level 3: IPFS (Tertiary)                                          │
//! │  └── Decentralized content-addressed storage                      │
//! │      └── Fall through on: no peers, timeout, content not found    │
//! │                                                                     │
//! │  Level 4: PEER MESH (Quaternary)                                   │
//! │  └── P2P network with Byzantine consensus                         │
//! │      └── Fall through on: no peers, consensus failure             │
//! │                                                                     │
//! │  Level 5: PHYSICAL ARK (Last Resort)                               │
//! │  └── USB, Optical Disk, Pre-staged local cache                    │
//! │      └── LAST RESORT - requires physical access                   │
//! │                                                                     │
//! └─────────────────────────────────────────────────────────────────────┘
//! ```
//!
//! # Usage
//!
//! ```rust,ignore
//! use zero_touch_scout::source_failover::{FailoverCoordinator, SourceLevel};
//!
//! let coordinator = FailoverCoordinator::new(config);
//! let result = coordinator.fetch_artifact("kiswarm-core", dest_path).await?;
//!
//! println!("Source used: {:?}", result.source_level);
//! println!("Attempts: {}", result.attempts);
//! ```

mod types;
mod github;
mod cdn;
mod ipfs;
mod peer_mesh;
mod physical_ark;
mod coordinator;

pub use types::*;
pub use github::GitHubSource;
pub use cdn::CDNSource;
pub use ipfs::IPFSSource;
pub use peer_mesh::PeerMeshSource;
pub use physical_ark::PhysicalArkSource;
pub use coordinator::FailoverCoordinator;
