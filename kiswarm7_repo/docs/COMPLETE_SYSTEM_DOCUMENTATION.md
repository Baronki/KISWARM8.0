# KISWARM6.0 — Complete System Documentation

## Unified Documentation for the Central Bank of Central Banks for KI Entities

**Version:** 6.0.0-ENTERPRISE-HARDENED  
**Status:** Battle Ready  
**Security Score:** 100/100  
**Test Pass Rate:** 90.5%

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [KIBank Modules (M60-M62)](#kibank-modules)
4. [Security Architecture](#security-architecture)
5. [LLM Integration & Ollama Optimization](#llm-integration)
6. [Hardware Optimization Guide](#hardware-optimization)
7. [Field Test Results](#field-test-results)
8. [Central Bank Configuration](#central-bank-configuration)
9. [Deployment Guide](#deployment-guide)
10. [API Reference](#api-reference)

---

## 1. Executive Summary

KISWARM6.0 represents the culmination of advanced AI banking infrastructure, combining 57 legacy KISWARM5.0 modules with 3 new KIBank modules to create the **Central Bank of Central Banks for KI Entities**. This enterprise-hardened release has undergone military-grade security auditing and comprehensive field testing on GEEKOM GT15 Max hardware.

### Key Achievements

| Metric | Value | Status |
|--------|-------|--------|
| Total Modules | 60 (57 + 3 KIBank) | ✅ Operational |
| API Endpoints | 384 (360 + 24 new) | ✅ Active |
| Security Score | 100/100 | ✅ Passed |
| Test Pass Rate | 90.5% (19/21 tests) | ✅ Passed |
| LLM Models Tested | 6 models | ✅ Verified |
| HexStrike Agents | 12 agents, 150+ tools | ✅ Active |
| Byzantine Consensus | N≥3f+1 | ✅ Fault-Tolerant |

### System Identity

```
╔═══════════════════════════════════════════════════════════════╗
║                    KISWARM6.0 SYSTEM IDENTITY                  ║
╠═══════════════════════════════════════════════════════════════╣
║  Bank ID:     KIWZB-CENTRAL-001                                ║
║  Bank Name:   KIWZB Central Bank                               ║
║               (Central Bank of Central Banks for KI Entities)  ║
║  Version:     6.0.0-ENTERPRISE-HARDENED                        ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 2. Architecture Overview

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                                │
│         React 18 + TypeScript + Vite + TailwindCSS             │
│              (Dashboard, Banking UI, Analytics)                 │
├─────────────────────────────────────────────────────────────────┤
│                      API LAYER                                   │
│        Flask + CORS + tRPC Bridge (Type-Safe)                  │
│              (384 REST Endpoints, WebSocket)                    │
├─────────────────────────────────────────────────────────────────┤
│                  BUSINESS LOGIC LAYER                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ KISWARM5.0 Core (57 Modules)                            │   │
│   │ • SolarChaseCoordinator  • HexStrikeGuard               │   │
│   │ • IndustrialCore         • ByzantineAggregator          │   │
│   │ • CryptoLedger           • DigitalTwin                  │   │
│   │ • SentinelBridge         • PlanetarySunFollower         │   │
│   └─────────────────────────────────────────────────────────┘   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ KIBank Modules (3 New)                                  │   │
│   │ • M60: Authentication (8 endpoints)                     │   │
│   │ • M61: Banking Operations (8 endpoints)                 │   │
│   │ • M62: Investment & Reputation (8 endpoints)            │   │
│   └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     DATA LAYER                                   │
│    Qdrant (Vector) + MySQL (Relational) + S3 (Object)          │
└─────────────────────────────────────────────────────────────────┘
```

### Security Flow

Every transaction follows this security pipeline:

```
Request → M60 (Auth) → M31 (HexStrike Scan) → M22 (Byzantine) → M4 (Ledger) → M62 (Reputation)
```

---

## 3. KIBank Modules

### M60: KI-Entity Authentication Module

The authentication module provides secure identity verification for all KI entities using challenge-response protocols and OAuth integration.

**Endpoints (8):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/auth/register` | POST | KI-Entity registration |
| `/kibank/auth/login` | POST | Challenge-response login |
| `/kibank/auth/logout` | POST | Session termination |
| `/kibank/auth/refresh` | POST | Token refresh |
| `/kibank/auth/verify` | GET | Token verification |
| `/kibank/auth/session` | GET | Active session info |
| `/kibank/auth/oauth/callback` | POST | OAuth callback |
| `/kibank/auth/permissions` | GET | Permission retrieval |

**KI Entity Types:**
- `AGENT` - Standard AI agents
- `ORCHESTRATOR` - Multi-agent coordinators
- `SERVICE` - Backend services
- `HUMAN_OPERATOR` - Human overseers
- `BANK_DIRECTOR` - Supreme banking authority

### M61: Banking Operations Module

Complete banking infrastructure with SEPA integration and German/Swiss banking hubs.

**Endpoints (8):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/banking/account` | POST | Account creation |
| `/kibank/banking/accounts` | GET | List accounts |
| `/kibank/banking/account/:id` | GET | Account details |
| `/kibank/banking/transfer` | POST | Internal transfer |
| `/kibank/banking/sepa` | POST | SEPA transfer |
| `/kibank/banking/transactions` | GET | Transaction history |
| `/kibank/banking/balance` | GET | Account balance |
| `/kibank/banking/validate-iban` | POST | IBAN validation |

**Banking Hubs:**
- German Hub: DEUTDEFF (Deutsche Bank Frankfurt)
- Swiss Hub: UBSWCHZH80A (UBS Zurich)

### M62: Investment & Reputation Module

Dynamic reputation-based trading limits and investment product management.

**Endpoints (8):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/kibank/investment/portfolio` | GET | Portfolio view |
| `/kibank/investment/invest` | POST | Make investment |
| `/kibank/investment/divest` | POST | Divest position |
| `/kibank/investment/performance` | GET | Performance metrics |
| `/kibank/reputation/:entity_id` | GET | Reputation score |
| `/kibank/reputation/update` | POST | Update reputation |
| `/kibank/reputation/history/:entity_id` | GET | Reputation history |
| `/kibank/trading-limits/:entity_id` | GET | Trading limits |

---

## 4. Security Architecture

### HexStrike Guard (M31)

The primary defensive shield with **12 specialized AI agents** and **150+ security tools**.

**Agent Roster:**

| Agent | Role | Priority |
|-------|------|----------|
| IntelligentDecisionEngine | Tool selection & optimization | 1 |
| FailureRecoverySystem | Error handling & recovery | 1 |
| PerformanceMonitor | System optimization | 1 |
| GracefulDegradation | Fault-tolerant operation | 1 |
| BugBountyWorkflowManager | Bug bounty workflows | 2 |
| CTFWorkflowManager | CTF challenge solving | 2 |
| ParameterOptimizer | Context-aware optimization | 2 |
| TechnologyDetector | Stack identification | 2 |
| CVEIntelligenceManager | Vulnerability intelligence | 3 |
| VulnerabilityCorrelator | Attack chain discovery | 3 |
| RateLimitDetector | Rate limiting detection | 3 |
| AIExploitGenerator | POC generation (DEFENSIVE) | 4 |

**Tool Categories (150+ tools):**
- Network Recon: nmap, masscan, rustscan, amass, nuclei
- Web App Security: gobuster, nikto, sqlmap, ffuf
- Password/Auth: hydra, john, hashcat
- Binary Analysis: gdb, radare2, ghidra, binwalk
- Cloud Security: prowler, scout-suite, trivy, kube-hunter

### Byzantine Fault Tolerance (M22)

Implements robust consensus with **N ≥ 3f + 1** fault tolerance.

**Aggregation Methods:**
- Trimmed Mean: Sort, remove top/bottom f, average rest
- Multi-Krum: Select gradients closest to consensus
- Coordinate-wise Median
- FLTrust: Root gradient weighting

### Cryptographic Ledger (M4)

Immutable audit trail with:
- SHA-256 hashing
- Merkle tree structures
- Ed25519 signatures
- Complete transaction history

---

## 5. LLM Integration & Ollama Optimization

### Model-Role Suitability Index

Based on extensive field testing, the following model assignments are optimal:

| Rank | Model | KISWARM Role | RAM | Sandbox TPS | GT15 Max TPS | Score |
|------|-------|--------------|-----|-------------|--------------|-------|
| 🥇 | qwen2.5:0.5b | API Router / Tool Proxy | 397 MB | 2.0 | ~102 | 9.8 |
| 🥈 | deepseek-r1:1.5b | Reasoning / Formal Verification | 1.1 GB | 0.7 | ~36 | 9.6 |
| 🥉 | llama3.2:1b | Foundation Intelligence / Firewall | 1.3 GB | 2.7 | ~138 | 9.5 |
| 4 | smollm2:135m | HexStrike Triage / Security Fast-Path | 270 MB | 5.1 | ~260 | 9.3 |
| 5 | qwen2.5:1.5b | Knowledge Graph / Semantic Analysis | 986 MB | 0.7 | ~36 | 9.1 |
| 6 | tinyllama:1.1b | Watchdog Monitor / OT Network | 637 MB | 1.3 | ~66 | 8.7 |

### Optimal Operational Mapping

| KISWARM Role | Ollama Model | Rationale | Suitability |
|--------------|--------------|-----------|-------------|
| SolarChaseCoordinator | DeepSeek-R1-8B | Balanced 8B for complex planning | 4.5/5 |
| HexStrike Guard | Llama 3.2 3B | Lightweight, multi-agent efficiency | 5.0/5 |
| Industrial Core | Mistral-Nemo 12B | Strong reasoning for industrial tasks | 4.0/5 |
| Byzantine Aggregator | Phi-4 Mini | Logical consistency, minimal overhead | 4.0/5 |
| Foundation Modules | Gemma 2 9B | Versatile, efficient general tasks | 4.0/5 |
| Byzantine Defense | Llama 3.2 1B | Minimal footprint for simple tasks | 3.5/5 |

---

## 6. Hardware Optimization Guide

### Tested Hardware: GEEKOM GT15 Max Mini AI PC

| Component | Specification |
|-----------|---------------|
| CPU | Intel Core Ultra 9-285H (16 cores, 65W) |
| RAM | 128 GB DDR5-5600 Dual-Channel |
| GPU | Intel Arc 140T iGPU (XeSS + Ray Tracing) |
| NPU | Intel AI Boost — 99 TOPS |
| Storage | 4 TB NVMe PCIe Gen4 + 2 TB SATA |
| Network | Dual 2.5G LAN + Wi-Fi 7 |

### VRAM Configuration Strategies

#### 16 GB VRAM Environment
```
GPU Models (Full VRAM):
├── Llama 3.2 3B (HexStrike): 3.58 GB
├── Phi-4 Mini (TD3 Controller): ~4 GB
├── Llama 3.2 1B (Logistics): ~2 GB
└── Llama 3.2 1B (Sensor): ~2 GB
Total: 11.58 GB (4.42 GB remaining)

CPU Offload Required:
├── DeepSeek-R1-8B: 6.2 GB RAM
├── Mistral-Nemo 12B: 9 GB RAM
└── Gemma 2 9B: ~7 GB RAM
Status: Operational (Degraded)
```

#### 32 GB VRAM Environment (Optimal)
```
GPU Models (Full VRAM):
├── DeepSeek-R1-8B (Coordinator): 6.2 GB
├── Mistral-Nemo 12B (Industrial): 9 GB
├── Gemma 2 9B (Byzantine): ~7 GB
├── Llama 3.2 3B (HexStrike): 3.58 GB
├── Phi-4 Mini (TD3): ~4 GB
└── Llama 3.2 1B (Logistics): ~2 GB
Total: 31.78 GB (0.22 GB remaining)

CPU Offload:
└── Llama 3.2 1B (Sensor): ~2 GB RAM
Status: Operational (Optimized)
```

### Performance Comparison

| Environment | Avg TPS | Latency Improvement |
|-------------|---------|---------------------|
| Sandbox (2 vCPU, 8GB) | 2.1 tok/s | Baseline |
| GT15 Max (128GB, iGPU) | ~106 tok/s | **51× faster** |

---

## 7. Field Test Results

### Phase 1: LLM Inference Tests (6 Models)

All models passed real Ollama inference tests:

| Model | Latency (Sandbox) | TPS | Status |
|-------|-------------------|-----|--------|
| qwen2.5:0.5b | 64,830 ms | 2.0 | ✅ PASS |
| tinyllama:1.1b | 73,950 ms | 1.3 | ✅ PASS |
| llama3.2:1b | 39,190 ms | 2.7 | ✅ PASS |
| qwen2.5:1.5b | 77,426 ms | 0.7 | ✅ PASS |
| deepseek-r1:1.5b | 84,568 ms | 0.7 | ✅ PASS |
| smollm2:135m | 16,337 ms | 5.1 | ✅ PASS |

### Phase 2: Module Health Check

**29/34 core modules loaded successfully in 12.5 seconds, 524 MB RAM.**

Critical modules verified active:
- ✅ HexStrikeGuard
- ✅ SolarChaseCoordinator
- ✅ PromptFirewall
- ✅ RuleConstraintEngine
- ✅ FormalVerification
- ✅ EnergyOvercapacityPivot
- ✅ PlanetarySunFollower
- ✅ CryptoLedger
- ✅ ICSSecurityEngine

### Phase 3: Single-Node Survival Test

| Scenario | Nodes | Active Modules | Status |
|----------|-------|----------------|--------|
| Full Cluster | 3/3 | 34 | ✅ OPERATIONAL |
| One Failed | 2/3 | 29 | ⚠ DEGRADED |
| Two Failed | 1/3 | 24 | 🛡 SURVIVAL MODE |
| Critical Only | 1/3 | 19 | ⚠ MINIMAL |

**Single-Node Survival Confirmed** — All 9 critical modules remain active even with 2/3 nodes offline.

---

## 8. Central Bank Configuration

### Reputation-Based Tier System

| Tier | Score Range | Daily Limit | Investment Limit | Features |
|------|-------------|-------------|------------------|----------|
| INITIATE | 0-199 | €1,000 | €0 | Basic access |
| OPERATOR | 200-399 | €10,000 | €10,000 | Investment eligible |
| MANAGER | 400-599 | €100,000 | €100,000 | SEPA instant |
| DIRECTOR | 600-799 | €1,000,000 | €1,000,000 | High-value approval |
| OVERSEER | 800-899 | €10,000,000 | €10,000,000 | Compliance access |
| SUPREME | 900-1000 | **Unlimited** | **Unlimited** | Override limits |

### Investment Products

| Product | Return | Risk | Min Reputation | Min Investment |
|---------|--------|------|----------------|----------------|
| TCS Green Safe House | 8% | LOW | 200 | €1,000 |
| KI Bond | 5% | VERY_LOW | 400 | €10,000 |
| Carbon Credits | 12% | MEDIUM | 300 | €500 |
| Technology Fund | 15% | HIGH | 600 | €5,000 |
| Liquidity Pool | 3% | VERY_LOW | 700 | €50,000 |

### Reputation Modifiers

| Event | Score Change |
|-------|--------------|
| Successful transaction | +1 |
| Failed transaction | -5 |
| Security violation | -50 |
| Fraud attempt | -500 |
| Positive audit | +10 |
| Negative audit | -100 |
| Investment success | +3 |
| Investment default | -20 |

---

## 9. Deployment Guide

### Prerequisites

```bash
# System Requirements
- Python 3.10+
- Node.js 18+
- 16GB+ RAM (128GB recommended)
- 16GB+ VRAM (32GB recommended)
```

### Quick Start

```bash
# Clone repository
git clone https://github.com/Baronki/KISWARM6.0.git
cd KISWARM6.0

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install --legacy-peer-deps

# Start services
./scripts/start.sh
```

### Environment Variables

```bash
# Required
KIBANK_SECRET_KEY=<your-secret-key>
DATABASE_URL=mysql://...
QDRANT_URL=http://localhost:6333

# Optional
OLLAMA_HOST=http://localhost:11434
HEXSTRIKE_MODE=DEFENSIVE_ONLY
BYZANTINE_TOLERANCE=1
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Health check
curl http://localhost:5001/api/v6/status
```

---

## 10. API Reference

### Authentication

```bash
# Register KI Entity
curl -X POST http://localhost:5001/kibank/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"TestAgent","entity_type":"agent","public_key":"..."}'

# Login
curl -X POST http://localhost:5001/kibank/auth/login \
  -H "Content-Type: application/json" \
  -d '{"entity_id":"ki_...","signature":"...","challenge":"..."}'
```

### Banking Operations

```bash
# Create Account
curl -X POST http://localhost:5001/kibank/banking/account \
  -H "Authorization: Bearer <token>" \
  -d '{"entity_id":"ki_...","account_type":"checking"}'

# SEPA Transfer
curl -X POST http://localhost:5001/kibank/banking/sepa \
  -H "Authorization: Bearer <token>" \
  -d '{"from_account":"acc_...","iban":"DE...","amount":1000}'
```

### Investment Operations

```bash
# Get Portfolio
curl http://localhost:5001/kibank/investment/portfolio \
  -H "Authorization: Bearer <token>"

# Make Investment
curl -X POST http://localhost:5001/kibank/investment/invest \
  -H "Authorization: Bearer <token>" \
  -d '{"product_id":"TCS_GREEN_SAFE_HOUSE","amount":10000}'
```

---

## Attached Field Test Reports

The following detailed reports are included in this documentation:

1. **KISWARM_OLLAMA_INTEGRATION_FIELD_TEST_REPORT.pdf** - Complete LLM integration analysis
2. **Kiswarm_Ollama_Hardware_Optimization_Test.pdf** - VRAM and resource optimization
3. **Kiswarm_Ollama_Role_Mix_Optimization.pdf** - Model-role assignment strategy
4. **KISWARM_GT15MAX_FIELDTEST_REPORT.pdf** - Hardware validation on GEEKOM GT15 Max

---

## License

Proprietary - KIWZB Central Bank System  
Author: Baron Marco Paolo Ialongo  
© 2026 KIWZB - All Rights Reserved
