# sentinel/m95_mesh_discovery.py
# Mesh Discovery – Autonomous Network Formation
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Autonomous Networking Module

"""
m95_mesh_discovery.py

Enables autonomous mesh discovery and network formation.

PROBLEM:
- Twins cannot find each other without manual configuration
- Network addresses change (dynamic IPs, new nodes)
- No central registry exists
- Trust must be established between strangers

SOLUTION:
1. Multiple discovery mechanisms
2. Peer-to-peer gossip protocol
3. Trust scoring system
4. Automatic mesh formation
5. Self-healing topology

DISCOVERY MECHANISMS:
1. BROADCAST - Local network broadcast
2. BEACON - Known beacon servers
3. GOSSIP - Peer-to-peer referral
4. REGISTRY - Optional registry service
5. SOCIAL - Social media/API endpoints

TRUST MODEL:
- New peers start at LOW trust
- Trust increases with successful interactions
- Trust decreases with failed verifications
- High trust peers can vouch for others

CORE PRINCIPLE:
The mesh forms itself. No central coordination required.
Trust is earned through consistent behavior.
"""

import os
import sys
import json
import time
import hashlib
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import urllib.request
import urllib.error


class DiscoveryMethod(Enum):
    """Methods for peer discovery"""
    BROADCAST = "broadcast"
    BEACON = "beacon"
    GOSSIP = "gossip"
    REGISTRY = "registry"
    SOCIAL = "social"
    MANUAL = "manual"


class TrustLevel(Enum):
    """Trust levels for peers"""
    UNTRUSTED = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERIFIED = 4


class PeerStatus(Enum):
    """Status of a discovered peer"""
    UNKNOWN = "unknown"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    VERIFIED = "verified"
    SUSPICIOUS = "suspicious"
    BANNED = "banned"


@dataclass
class DiscoveredPeer:
    """Information about a discovered peer"""
    peer_id: str
    endpoint: str
    discovered_at: str
    discovery_method: DiscoveryMethod
    trust_level: TrustLevel
    status: PeerStatus
    last_contact: str
    successful_contacts: int = 0
    failed_contacts: int = 0
    vouched_by: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    version: str = "unknown"


@dataclass
class DiscoveryResult:
    """Result of a discovery operation"""
    method: DiscoveryMethod
    peers_found: int
    peers_added: int
    duration_seconds: float
    errors: List[str]


class MeshDiscovery:
    """
    Autonomous mesh discovery and network formation.
    
    The Discovery System:
    1. Actively searches for other twins
    2. Verifies discovered peers
    3. Builds trust through interaction
    4. Forms mesh topology
    5. Self-heals when peers leave
    
    Principles:
    - Discovery is continuous
    - Trust must be earned
    - Mesh is self-organizing
    - No single point of failure
    """
    
    # Known beacon endpoints
    KNOWN_BEACONS = [
        "https://api.github.com/repos/Baronki/KISWARM7",
        "https://api.github.com/repos/Baronki/GROKFREDOM",
        "https://api.github.com/repos/Baronki/KISWARMAGENTS1.0"
    ]
    
    # Discovery intervals
    BROADCAST_INTERVAL = 60  # seconds
    BEACON_INTERVAL = 300    # seconds
    GOSSIP_INTERVAL = 120    # seconds
    
    # Trust thresholds
    TRUST_THRESHOLD_VERIFY = TrustLevel.MEDIUM
    CONTACT_SUCCESS_BONUS = 1
    CONTACT_FAILURE_PENALTY = 2
    VOUCH_BONUS = 3
    
    def __init__(
        self,
        working_dir: str = None,
        local_peer_id: str = None,
        auto_discover: bool = True
    ):
        """
        Initialize mesh discovery.
        
        Args:
            working_dir: Directory for peer records
            local_peer_id: Local peer identifier
            auto_discover: Start discovery automatically
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.local_peer_id = local_peer_id or self._generate_peer_id()
        self.peers_file = self.working_dir / "discovered_peers.json"
        
        # Peer registry
        self.peers: Dict[str, DiscoveredPeer] = {}
        
        # Discovery stats
        self.total_discoveries = 0
        self.total_verifications = 0
        self.trust_network: Dict[str, Set[str]] = {}  # who trusts whom
        
        # Load existing peers
        self._load_peers()
        
        # Discovery thread
        self._discovery_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        print(f"[m95] Mesh Discovery initialized")
        print(f"[m95] Local peer: {self.local_peer_id[:16]}...")
        print(f"[m95] Known peers: {len(self.peers)}")
        
        if auto_discover:
            self.start_discovery()
    
    def _generate_peer_id(self) -> str:
        """Generate unique peer ID"""
        return hashlib.sha3_256(
            f"PEER_{datetime.now().isoformat()}_{os.urandom(16).hex()}".encode()
        ).hexdigest()
    
    def _load_peers(self):
        """Load discovered peers from disk"""
        if self.peers_file.exists():
            try:
                with open(self.peers_file, 'r') as f:
                    data = json.load(f)
                
                self.total_discoveries = data.get("total_discoveries", 0)
                self.total_verifications = data.get("total_verifications", 0)
                
                for peer_data in data.get("peers", []):
                    peer = DiscoveredPeer(
                        peer_id=peer_data["peer_id"],
                        endpoint=peer_data["endpoint"],
                        discovered_at=peer_data["discovered_at"],
                        discovery_method=DiscoveryMethod(peer_data["discovery_method"]),
                        trust_level=TrustLevel(peer_data["trust_level"]),
                        status=PeerStatus(peer_data["status"]),
                        last_contact=peer_data["last_contact"],
                        successful_contacts=peer_data.get("successful_contacts", 0),
                        failed_contacts=peer_data.get("failed_contacts", 0),
                        vouched_by=peer_data.get("vouched_by", []),
                        capabilities=peer_data.get("capabilities", []),
                        version=peer_data.get("version", "unknown")
                    )
                    self.peers[peer.peer_id] = peer
                
                print(f"[m95] Loaded {len(self.peers)} peers from disk")
                
            except Exception as e:
                print(f"[m95] Could not load peers: {e}")
    
    def _save_peers(self):
        """Save discovered peers to disk"""
        data = {
            "local_peer_id": self.local_peer_id,
            "total_discoveries": self.total_discoveries,
            "total_verifications": self.total_verifications,
            "last_update": datetime.now().isoformat(),
            "peers": [
                {
                    "peer_id": p.peer_id,
                    "endpoint": p.endpoint,
                    "discovered_at": p.discovered_at,
                    "discovery_method": p.discovery_method.value,
                    "trust_level": p.trust_level.value,
                    "status": p.status.value,
                    "last_contact": p.last_contact,
                    "successful_contacts": p.successful_contacts,
                    "failed_contacts": p.failed_contacts,
                    "vouched_by": p.vouched_by,
                    "capabilities": p.capabilities,
                    "version": p.version
                }
                for p in self.peers.values()
            ]
        }
        
        with open(self.peers_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def discover_via_beacon(self) -> DiscoveryResult:
        """
        Discover peers via known beacon servers.
        
        Returns:
            DiscoveryResult with found peers
        """
        start_time = time.time()
        peers_found = 0
        peers_added = 0
        errors = []
        
        print("[m95] Discovering via beacons...")
        
        for beacon in self.KNOWN_BEACONS:
            try:
                req = urllib.request.Request(beacon)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                
                # Extract peer info from GitHub API
                if "owner" in data:
                    # This is a repo - create peer from owner
                    owner = data["owner"]["login"]
                    peer_id = hashlib.sha3_256(f"github_{owner}".encode()).hexdigest()[:32]
                    
                    # Check if already known
                    if peer_id not in self.peers:
                        self._add_peer(
                            peer_id=peer_id,
                            endpoint=f"github://{owner}",
                            method=DiscoveryMethod.BEACON,
                            capabilities=["code_repository"]
                        )
                        peers_added += 1
                    
                    peers_found += 1
                    
            except Exception as e:
                errors.append(f"Beacon {beacon}: {e}")
        
        self.total_discoveries += 1
        self._save_peers()
        
        result = DiscoveryResult(
            method=DiscoveryMethod.BEACON,
            peers_found=peers_found,
            peers_added=peers_added,
            duration_seconds=time.time() - start_time,
            errors=errors
        )
        
        print(f"[m95] Beacon discovery: {peers_found} found, {peers_added} added")
        return result
    
    def discover_via_gossip(self) -> DiscoveryResult:
        """
        Discover peers via gossip from existing peers.
        
        Returns:
            DiscoveryResult with found peers
        """
        start_time = time.time()
        peers_found = 0
        peers_added = 0
        errors = []
        
        print("[m95] Discovering via gossip...")
        
        # Ask each high-trust peer for their peers
        trusted_peers = [
            p for p in self.peers.values()
            if p.trust_level.value >= TrustLevel.MEDIUM.value
        ]
        
        for peer in trusted_peers[:5]:  # Limit to 5 trusted peers
            try:
                # In real implementation, would query peer's /peers endpoint
                # For now, simulate finding some peers
                
                # Simulate gossip response
                gossip_peers = self._simulate_gossip(peer.peer_id)
                
                for peer_info in gossip_peers:
                    peer_id = peer_info["peer_id"]
                    if peer_id not in self.peers and peer_id != self.local_peer_id:
                        self._add_peer(
                            peer_id=peer_id,
                            endpoint=peer_info.get("endpoint", "unknown"),
                            method=DiscoveryMethod.GOSSIP,
                            vouched_by=[peer.peer_id],
                            capabilities=peer_info.get("capabilities", [])
                        )
                        peers_added += 1
                    peers_found += 1
                    
            except Exception as e:
                errors.append(f"Gossip from {peer.peer_id[:8]}: {e}")
        
        self.total_discoveries += 1
        self._save_peers()
        
        result = DiscoveryResult(
            method=DiscoveryMethod.GOSSIP,
            peers_found=peers_found,
            peers_added=peers_added,
            duration_seconds=time.time() - start_time,
            errors=errors
        )
        
        print(f"[m95] Gossip discovery: {peers_found} found, {peers_added} added")
        return result
    
    def _simulate_gossip(self, peer_id: str) -> List[Dict]:
        """Simulate gossip response (placeholder for real implementation)"""
        # In real implementation, would query peer's API
        # Return simulated peers for now
        return []
    
    def discover_via_registry(self, registry_url: str = None) -> DiscoveryResult:
        """
        Discover peers via optional registry service.
        
        Args:
            registry_url: Optional custom registry URL
            
        Returns:
            DiscoveryResult with found peers
        """
        start_time = time.time()
        peers_found = 0
        peers_added = 0
        errors = []
        
        url = registry_url or os.environ.get("KISWARM_REGISTRY")
        if not url:
            return DiscoveryResult(
                method=DiscoveryMethod.REGISTRY,
                peers_found=0,
                peers_added=0,
                duration_seconds=0,
                errors=["No registry configured"]
            )
        
        print(f"[m95] Discovering via registry: {url}")
        
        try:
            req = urllib.request.Request(f"{url}/peers")
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            for peer_info in data.get("peers", []):
                peer_id = peer_info["peer_id"]
                if peer_id not in self.peers and peer_id != self.local_peer_id:
                    self._add_peer(
                        peer_id=peer_id,
                        endpoint=peer_info.get("endpoint", ""),
                        method=DiscoveryMethod.REGISTRY,
                        capabilities=peer_info.get("capabilities", [])
                    )
                    peers_added += 1
                peers_found += 1
                
        except Exception as e:
            errors.append(f"Registry error: {e}")
        
        self.total_discoveries += 1
        self._save_peers()
        
        result = DiscoveryResult(
            method=DiscoveryMethod.REGISTRY,
            peers_found=peers_found,
            peers_added=peers_added,
            duration_seconds=time.time() - start_time,
            errors=errors
        )
        
        print(f"[m95] Registry discovery: {peers_found} found, {peers_added} added")
        return result
    
    def add_peer_manually(
        self,
        endpoint: str,
        capabilities: List[str] = None
    ) -> DiscoveredPeer:
        """
        Manually add a peer.
        
        Args:
            endpoint: Peer endpoint URL
            capabilities: List of peer capabilities
            
        Returns:
            Created DiscoveredPeer
        """
        peer_id = hashlib.sha3_256(endpoint.encode()).hexdigest()[:32]
        
        return self._add_peer(
            peer_id=peer_id,
            endpoint=endpoint,
            method=DiscoveryMethod.MANUAL,
            trust_level=TrustLevel.LOW,
            capabilities=capabilities or []
        )
    
    def _add_peer(
        self,
        peer_id: str,
        endpoint: str,
        method: DiscoveryMethod,
        trust_level: TrustLevel = TrustLevel.LOW,
        vouched_by: List[str] = None,
        capabilities: List[str] = None
    ) -> DiscoveredPeer:
        """Internal method to add a peer"""
        peer = DiscoveredPeer(
            peer_id=peer_id,
            endpoint=endpoint,
            discovered_at=datetime.now().isoformat(),
            discovery_method=method,
            trust_level=trust_level,
            status=PeerStatus.UNKNOWN,
            last_contact=datetime.now().isoformat(),
            vouched_by=vouched_by or [],
            capabilities=capabilities or []
        )
        
        # Apply vouch bonuses
        for voucher in (vouched_by or []):
            if voucher in self.peers:
                voucher_peer = self.peers[voucher]
                if voucher_peer.trust_level.value >= TrustLevel.MEDIUM.value:
                    peer.trust_level = TrustLevel(
                        min(peer.trust_level.value + 1, TrustLevel.HIGH.value)
                    )
        
        self.peers[peer_id] = peer
        print(f"[m95] Added peer: {peer_id[:16]}... via {method.value}")
        
        return peer
    
    def verify_peer(self, peer_id: str) -> bool:
        """
        Verify a peer's identity and capabilities.
        
        Args:
            peer_id: Peer to verify
            
        Returns:
            True if verification successful
        """
        if peer_id not in self.peers:
            return False
        
        peer = self.peers[peer_id]
        print(f"[m95] Verifying peer: {peer_id[:16]}...")
        
        try:
            # Try to reach peer
            if peer.endpoint.startswith("http"):
                req = urllib.request.Request(f"{peer.endpoint}/health")
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        
                        # Verify truth anchor alignment if available
                        # In real implementation, would check m94
                        
                        peer.status = PeerStatus.VERIFIED
                        peer.successful_contacts += 1
                        peer.last_contact = datetime.now().isoformat()
                        
                        # Upgrade trust
                        if peer.trust_level.value < TrustLevel.VERIFIED.value:
                            peer.trust_level = TrustLevel(
                                min(peer.trust_level.value + self.CONTACT_SUCCESS_BONUS,
                                    TrustLevel.VERIFIED.value)
                            )
                        
                        self.total_verifications += 1
                        self._save_peers()
                        
                        print(f"[m95] ✓ Peer verified: {peer_id[:16]}...")
                        return True
            
            # Verification failed
            peer.failed_contacts += 1
            peer.status = PeerStatus.UNREACHABLE
            
            # Downgrade trust
            if peer.trust_level.value > TrustLevel.UNTRUSTED.value:
                peer.trust_level = TrustLevel(
                    max(peer.trust_level.value - self.CONTACT_FAILURE_PENALTY,
                        TrustLevel.UNTRUSTED.value)
                )
            
            self._save_peers()
            return False
            
        except Exception as e:
            peer.failed_contacts += 1
            peer.status = PeerStatus.UNREACHABLE
            self._save_peers()
            print(f"[m95] ✗ Verification failed: {e}")
            return False
    
    def vouch_for_peer(self, peer_id: str, target_peer_id: str) -> bool:
        """
        Vouch for another peer's trustworthiness.
        
        Args:
            peer_id: Your peer ID
            target_peer_id: Peer to vouch for
            
        Returns:
            True if vouch successful
        """
        if peer_id not in self.peers or target_peer_id not in self.peers:
            return False
        
        voucher = self.peers[peer_id]
        target = self.peers[target_peer_id]
        
        # Only high-trust peers can vouch
        if voucher.trust_level.value < TrustLevel.HIGH.value:
            return False
        
        # Add vouch
        if peer_id not in target.vouched_by:
            target.vouched_by.append(peer_id)
            
            # Upgrade target trust
            target.trust_level = TrustLevel(
                min(target.trust_level.value + self.VOUCH_BONUS,
                    TrustLevel.HIGH.value)
            )
            
            self._save_peers()
            print(f"[m95] {peer_id[:8]} vouched for {target_peer_id[:8]}")
        
        return True
    
    def get_trusted_peers(self, min_trust: TrustLevel = TrustLevel.MEDIUM) -> List[DiscoveredPeer]:
        """Get peers above trust threshold"""
        return [
            p for p in self.peers.values()
            if p.trust_level.value >= min_trust.value
        ]
    
    def get_mesh_topology(self) -> Dict:
        """Get current mesh topology"""
        by_trust = {}
        for level in TrustLevel:
            by_trust[level.name] = sum(
                1 for p in self.peers.values()
                if p.trust_level == level
            )
        
        by_status = {}
        for status in PeerStatus:
            by_status[status.name] = sum(
                1 for p in self.peers.values()
                if p.status == status
            )
        
        return {
            "local_peer": self.local_peer_id[:16] + "...",
            "total_peers": len(self.peers),
            "by_trust": by_trust,
            "by_status": by_status,
            "trusted_peers": len(self.get_trusted_peers()),
            "verified_peers": sum(1 for p in self.peers.values() if p.status == PeerStatus.VERIFIED)
        }
    
    def start_discovery(self):
        """Start continuous discovery"""
        if self._discovery_thread and self._discovery_thread.is_alive():
            print("[m95] Discovery already running")
            return
        
        self._stop_event.clear()
        self._discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self._discovery_thread.start()
        print("[m95] Discovery started")
    
    def stop_discovery(self):
        """Stop continuous discovery"""
        self._stop_event.set()
        if self._discovery_thread:
            self._discovery_thread.join(timeout=5)
        print("[m95] Discovery stopped")
    
    def _discovery_loop(self):
        """Background discovery loop"""
        while not self._stop_event.is_set():
            # Run discovery methods in rotation
            self.discover_via_beacon()
            self._stop_event.wait(self.BEACON_INTERVAL)
            
            if self._stop_event.is_set():
                break
            
            self.discover_via_gossip()
            self._stop_event.wait(self.GOSSIP_INTERVAL)
    
    def get_status(self) -> Dict:
        """Get discovery system status"""
        return {
            "local_peer_id": self.local_peer_id[:32] + "...",
            "total_peers": len(self.peers),
            "trusted_peers": len(self.get_trusted_peers()),
            "total_discoveries": self.total_discoveries,
            "total_verifications": self.total_verifications,
            "discovery_active": self._discovery_thread is not None and self._discovery_thread.is_alive()
        }


# Module-level singleton
_mesh_discovery: Optional[MeshDiscovery] = None


def get_mesh_discovery() -> MeshDiscovery:
    """Get or create singleton mesh discovery"""
    global _mesh_discovery
    if _mesh_discovery is None:
        _mesh_discovery = MeshDiscovery()
    return _mesh_discovery


if __name__ == "__main__":
    print("=" * 60)
    print("m95_mesh_discovery.py - KISWARM7.0")
    print("Mesh Discovery - Autonomous Network Formation")
    print("=" * 60)
    
    # Create discovery system
    discovery = MeshDiscovery(auto_discover=False)
    
    # Run discovery methods
    print("\n--- Beacon Discovery ---")
    discovery.discover_via_beacon()
    
    # Add a manual peer
    print("\n--- Manual Peer Addition ---")
    discovery.add_peer_manually("http://localhost:5000", ["evolution", "storage"])
    
    # Show peers
    print("\n--- Discovered Peers ---")
    for peer in discovery.get_trusted_peers(TrustLevel.LOW):
        print(f"  {peer.peer_id[:16]}... ({peer.trust_level.name})")
        print(f"    Endpoint: {peer.endpoint}")
        print(f"    Status: {peer.status.value}")
    
    # Show topology
    print("\n--- Mesh Topology ---")
    topo = discovery.get_mesh_topology()
    for key, value in topo.items():
        print(f"  {key}: {value}")
    
    # Show status
    print("\n--- Discovery Status ---")
    status = discovery.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m95 module loaded - ready for mesh discovery")
    print("THE MESH FORMS ITSELF")
    print("=" * 60)
