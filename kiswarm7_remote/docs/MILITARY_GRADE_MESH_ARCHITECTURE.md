# KISWARM Military-Grade Mesh Architecture v6.3.0

## Overview

This document defines the **Military-Grade Redundant Mesh Architecture** for KISWARM SCADA. The architecture ensures survivability under all circumstances with zero single points of failure.

---

## 1. Problem Statement

### 1.1 Current Limitation
The local development environment (Z.ai) **blocks or restricts external access** to the Mesh API routes. External installers (Colab, cloud instances) cannot reach the Master KISWARM API.

### 1.2 Requirements
- **Survivability**: Mesh must survive any single node failure
- **Redundancy**: Multiple layers of backup routing
- **Byzantine Tolerance**: Resist compromised nodes
- **24/7 Availability**: Permanent infrastructure, not dependent on local environment
- **No External Dependencies**: Self-contained routing infrastructure

---

## 2. Military-Grade Architecture

### 2.1 Multi-Layer Redundancy Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAYER 0: LOCAL MASTER (Development)                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Z.ai Environment (Port 3000)                                          ││
│  │  • Master API Routes (/api/master/*, /api/mesh/*)                      ││
│  │  • Dashboard UI                                                         ││
│  │  • Status: DEVELOPMENT ONLY (not externally accessible)                 ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ (Fallback)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: GEMINI CLI MESH ROUTER (Primary)                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Google Cloud Infrastructure                                            ││
│  │  • Gemini CLI as Mesh Router                                            ││
│  │  • Persistent session management                                        ││
│  │  • WebSocket relay for real-time communication                          ││
│  │  • Status: PRIMARY EXTERNAL ROUTER                                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ (Failover)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   LAYER 2: GITHUB ACTIONS MESH NODES (24/7)                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  GitHub Infrastructure (Always-On)                                      ││
│  │  • GitHub Actions Workflow (scheduled every 5 minutes)                  ││
│  │  • GitHub Issues as Message Queue                                       ││
│  │  • GitHub Releases as Knowledge Repository                              ││
│  │  • GitHub Pages as Status Dashboard                                     ││
│  │  • Status: PERMANENT INFRASTRUCTURE                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ (Distributed)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: FEDERATED MESH PROTOCOL (P2P)                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Distributed Node Network                                               ││
│  │  • Colab Instances (Transient)                                          ││
│  │  • Cloud VPS Nodes (Semi-Permanent)                                     ││
│  │  • Local Development Machines                                           ││
│  │  • Byzantine-fault-tolerant aggregation                                 ││
│  │  • Status: DYNAMIC MESH                                                 ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mesh Routing Table

| Layer | Component | Availability | Latency | Trust Score |
|-------|-----------|--------------|---------|-------------|
| 0 | Local Master | Development only | <10ms | 1.0 (trusted) |
| 1 | Gemini CLI Router | 99.9% | 50-200ms | 0.9 |
| 2 | GitHub Actions | 99.99% | 100-500ms | 0.95 |
| 3 | P2P Mesh | Variable | Variable | 0.5-0.9 |

---

## 3. Gemini CLI Mesh Router

### 3.1 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   GEMINI CLI MESH ROUTER                      │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  Installer  │  │  Installer  │  │  Installer  │           │
│  │  (Colab)    │  │  (Cloud)    │  │  (Local)    │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                   │
│         └────────────────┼────────────────┘                   │
│                          │                                    │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              GEMINI CLI SESSION                          │ │
│  │  ┌─────────────────────────────────────────────────┐    │ │
│  │  │  Mesh State Manager                              │    │ │
│  │  │  • Node Registry                                 │    │ │
│  │  │  • Message Queue                                 │    │ │
│  │  │  • Byzantine Aggregator                          │    │ │
│  │  │  • Trust Ledger                                  │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 3.2 Mesh Protocol Commands

```python
# Registration
{
    "command": "MESH_REGISTER",
    "entity_id": "ki_installer_xxxxx",
    "capabilities": ["ollama", "models", "scada"],
    "endpoint": "https://xxx.ngrok.io",
    "timestamp": "2026-01-01T00:00:00Z",
    "signature": "sha256..."
}

# Heartbeat
{
    "command": "MESH_HEARTBEAT",
    "entity_id": "ki_installer_xxxxx",
    "status": "active",
    "models_running": 6,
    "cpu": 45.2,
    "memory": 78.3,
    "timestamp": "2026-01-01T00:05:00Z"
}

# Status Query
{
    "command": "MESH_STATUS",
    "query": "all_nodes" | "node_id" | "trust_scores",
    "requester_id": "ki_installer_xxxxx"
}

# Model Share (Byzantine)
{
    "command": "MESH_SHARE",
    "entity_id": "ki_installer_xxxxx",
    "param_delta": [0.1, -0.05, 0.2, ...],
    "perf_delta": 0.15,
    "stability_cert": 0.85,
    "attestation": "sha256..."
}

# Message Relay
{
    "command": "MESH_RELAY",
    "from_id": "ki_installer_xxxxx",
    "to_id": "ki_installer_yyyyy",
    "message": {...},
    "ttl": 5
}
```

### 3.3 Deployment via Gemini CLI

```markdown
# KISWARM Mesh Router Deployment on Gemini CLI

## Prerequisites
- Google Account with Gemini CLI access
- Gemini Code Assist for Individuals plan

## Setup Steps

1. Open Gemini CLI in terminal
2. Copy the Mesh Router prompt:

\`\`\`
You are the KISWARM Mesh Router, a critical infrastructure component for the KISWARM SCADA system.

Your responsibilities:
1. Maintain a registry of all KISWARM installer nodes
2. Process MESH_REGISTER commands and track node capabilities
3. Handle MESH_HEARTBEAT to monitor node health
4. Execute Byzantine-fault-tolerant aggregation for MESH_SHARE commands
5. Relay messages between nodes via MESH_RELAY

Knowledge Base:
- KISWARM Version: 6.3.0 SEVENTY_FIVE_COMPLETE
- Modules: 75 (57 Sentinel + 18 KIBank)
- Trust Threshold: 0.67 (2/3 supermajority)
- Quorum: Minimum 3 nodes for global updates

Mesh State (initialize):
```json
{
  "nodes": {},
  "trust_scores": {},
  "message_queue": [],
  "round_id": 0
}
```

Respond to each command with:
1. Command validation
2. State update
3. Response to requester
4. Any necessary broadcasts
\`\`\`

3. Save this prompt as a reusable context
4. External installers can now communicate through this session
```

---

## 4. GitHub Actions Mesh Infrastructure

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GITHUB ACTIONS MESH INFRASTRUCTURE                       │
│                                                                              │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐   │
│  │ .github/workflows │    │ GitHub Issues     │    │ GitHub Releases   │   │
│  │                   │    │                   │    │                   │   │
│  │ mesh_router.yml   │    │ Mesh Messages     │    │ Knowledge Base    │   │
│  │ (every 5 min)     │    │ (async queue)     │    │ (snapshots)       │   │
│  └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘   │
│            │                        │                        │              │
│            └────────────────────────┼────────────────────────┘              │
│                                     │                                       │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    MESH STATE REPOSITORY                               │  │
│  │  docs/mesh_state.json                                                  │  │
│  │  • Node Registry                                                       │  │
│  │  • Trust Scores                                                        │  │
│  │  • Aggregation History                                                 │  │
│  │  • Message Queue                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    GITHUB PAGES DASHBOARD                              │  │
│  │  https://baronki.github.io/KISWARM6.0/mesh-status                     │  │
│  │  • Real-time Mesh Status                                               │  │
│  │  • Node Leaderboard                                                    │  │
│  │  • Trust Score Visualization                                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Mesh Router Workflow

```yaml
# .github/workflows/mesh_router.yml
name: KISWARM Mesh Router

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  issues:
    types: [opened, edited]
  workflow_dispatch:

jobs:
  mesh-router:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pages: write
    
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: |
          pip install -q flask flask-cors requests pyngrok
      
      - name: Process Mesh Messages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/mesh_router.py
      
      - name: Update Mesh State
        run: |
          python scripts/update_mesh_state.py
      
      - name: Deploy Status Page
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          publish_branch: gh-pages
      
      - name: Commit State Changes
        run: |
          git config --local user.email "mesh-router@kiswarm.local"
          git config --local user.name "KISWARM Mesh Router"
          git add -A
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: mesh state update [skip ci]"
          git push
```

### 4.3 GitHub Issues as Message Queue

```markdown
# Mesh Message Format (GitHub Issue)

## Title Format
`[MESH] <command> from <entity_id>`

## Body Format
```json
{
  "command": "MESH_REGISTER",
  "entity_id": "ki_installer_xxxxx",
  "timestamp": "2026-01-01T00:00:00Z",
  "payload": {
    "capabilities": ["ollama", "models", "scada"],
    "endpoint": "https://xxx.ngrok.io",
    "signature": "sha256..."
  }
}
```

## Labels
- `mesh-command` - All mesh commands
- `mesh-register` - Registration requests
- `mesh-heartbeat` - Heartbeat updates
- `mesh-share` - Byzantine shares
- `mesh-relay` - Message relay requests

## Processing
1. GitHub Actions reads issues with `mesh-command` label
2. Processes each command according to protocol
3. Updates mesh state in repository
4. Closes processed issues
5. Posts response as comment if needed
```

---

## 5. Distributed Mesh Protocol

### 5.1 Byzantine-Fault-Tolerant Aggregation

Based on the existing `federated_mesh.py` implementation:

```python
class MilitaryGradeAggregator:
    """
    Military-grade Byzantine-fault-tolerant aggregation.
    
    Protection Layers:
    1. Signature Verification - Reject unsigned/invalid shares
    2. Krum Filter - Reject statistical outliers
    3. Coordinate-wise Median - Robust to extreme values
    4. Quorum Validation - 2/3 supermajority required
    5. Trust Decay - Penalize unreliable nodes
    6. Partition Handling - Freeze updates during network issues
    """
    
    QUORUM_THRESHOLD = 0.67  # 2/3 supermajority
    MIN_TRUST_SCORE = 0.1    # Below this = compromised
    MAX_DRIFT = 0.10         # Maximum parameter drift during partition
    
    def aggregate(self, shares: List[NodeShare], nodes: Dict[str, NodeRecord]) -> AggregationReport:
        # Layer 1: Signature verification
        valid_shares = self._verify_signatures(shares, nodes)
        
        # Layer 2: Krum outlier rejection
        filtered_shares = self._krum_filter(valid_shares, nodes)
        
        # Layer 3: Quorum check
        if not self._check_quorum(filtered_shares, len(shares)):
            return self._create_failed_report("quorum_not_reached")
        
        # Layer 4: Trust-weighted coordinate median
        global_delta = self._coordinate_median(filtered_shares, nodes)
        
        # Layer 5: Apply trust rewards/penalties
        self._update_trust_scores(filtered_shares, nodes)
        
        return AggregationReport(
            quorum_reached=True,
            global_delta=global_delta,
            participating=len(filtered_shares)
        )
```

### 5.2 Node Lifecycle

```
┌─────────────────┐
│  UNREGISTERED   │
└────────┬────────┘
         │ MESH_REGISTER
         ▼
┌─────────────────┐
│   PENDING       │  ← Trust verification in progress
└────────┬────────┘
         │ Trust Score > 0.5
         ▼
┌─────────────────┐
│    ACTIVE       │  ← Participating in mesh
└────────┬────────┘
         │ No heartbeat for 5 min
         ▼
┌─────────────────┐
│    DORMANT      │  ← Suspended, awaiting reconnection
└────────┬────────┘
         │ No heartbeat for 30 min
         ▼
┌─────────────────┐
│  UNREGISTERED   │  ← Removed from mesh
└─────────────────┘
```

### 5.3 Trust Score Calculation

```python
def calculate_trust_score(node: NodeRecord) -> float:
    """
    Trust Score = f(
        history_reliability,
        uptime_ratio,
        share_quality,
        security_audit_score
    )
    """
    # Base score
    base = 0.8
    
    # Uptime factor (0.0-1.0)
    uptime_factor = node.uptime
    
    # Stability factor (0.0-1.0)
    stability_factor = node.stability_margin
    
    # Share acceptance rate
    acceptance_rate = (
        node.total_shares - node.rejected_shares
    ) / max(node.total_shares, 1)
    
    # Geometric mean
    trust = (uptime_factor * stability_factor * acceptance_rate) ** (1/3)
    
    # Apply penalties for security violations
    for violation in node.security_violations:
        trust *= 0.5  # 50% reduction per violation
    
    return max(MIN_TRUST_SCORE, min(1.0, trust))
```

---

## 6. Implementation Plan

### Phase 1: Gemini CLI Router (Week 1)
- [ ] Create Gemini CLI Mesh Router prompt
- [ ] Test with single installer connection
- [ ] Validate Byzantine aggregation
- [ ] Document session management

### Phase 2: GitHub Actions Infrastructure (Week 2)
- [ ] Create `mesh_router.yml` workflow
- [ ] Implement issue-based message queue
- [ ] Setup GitHub Pages dashboard
- [ ] Test 24/7 availability

### Phase 3: Integration (Week 3)
- [ ] Update autonomous installer to use layered routing
- [ ] Implement fallback chain (Local → Gemini → GitHub → P2P)
- [ ] Create mesh state persistence
- [ ] End-to-end testing

### Phase 4: Hardening (Week 4)
- [ ] Security audit
- [ ] Load testing
- [ ] Failure simulation
- [ ] Documentation completion

---

## 7. Security Considerations

### 7.1 Authentication
- All mesh commands must include valid signature
- Signatures computed using HMAC-SHA256
- Node identity verified before processing commands

### 7.2 Authorization
- Trust score determines command permissions
- Low trust nodes (< 0.3) can only read
- Medium trust nodes (0.3-0.7) can participate in aggregation
- High trust nodes (> 0.7) can propose updates

### 7.3 Audit Trail
- All mesh commands logged with timestamp
- Immutable audit ledger stored in repository
- Compliance with IEC 62443 security standards

---

## 8. Monitoring and Observability

### 8.1 Metrics
- Node count (active/dormant/unregistered)
- Average trust score
- Message latency
- Quorum success rate
- Byzantine rejection rate

### 8.2 Dashboards
- GitHub Pages: https://baronki.github.io/KISWARM6.0/mesh-status
- Local Dashboard: http://localhost:3000 (when available)

### 8.3 Alerts
- Quorum failure (no aggregation possible)
- Node compromise (trust score < 0.1)
- Network partition detected

---

## 9. Conclusion

This Military-Grade Mesh Architecture ensures KISWARM's survival under all circumstances through:

1. **Layered Redundancy**: Multiple fallback routing layers
2. **Byzantine Tolerance**: Resistant to compromised nodes
3. **24/7 Availability**: GitHub Actions provides permanent infrastructure
4. **No Single Point of Failure**: Distributed architecture

The KISWARM Mesh will continue operating even if:
- Local development environment is unavailable
- Gemini CLI session is interrupted
- Individual nodes are compromised
- Network partitions occur

**Survivability is not optional—it is engineered into every layer.**

---

*Document Version: 6.3.0*
*Author: KISWARM Project (Baron Marco Paolo Ialongo)*
*Classification: MILITARY-GRADE INFRASTRUCTURE*
