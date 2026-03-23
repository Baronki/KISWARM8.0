# KISWARM6.0 Architektur-Dokumentation

## Systemübersicht

KISWARM6.0 ist eine **4-Schichtige Unified Architecture**, die die bewährte KISWARM5.0 Planetary Machine mit dem neuen KIBank-Finanzprotokoll vereint.

### Die 4 Ebenen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                     │
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │                    React 18 Application                          │     │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │     │
│    │  │   Pages     │  │ Components  │  │  Contexts   │              │     │
│    │  │ (15+ Pages) │  │ (shadcn/ui) │  │ (Auth, KIWZB)│             │     │
│    │  └─────────────┘  └─────────────┘  └─────────────┘              │     │
│    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │     │
│    │  │    Hooks    │  │    Utils    │  │   Services  │              │     │
│    │  │(useAuth,etc)│  │  (helpers)  │  │ (WebSocket) │              │     │
│    │  └─────────────┘  └─────────────┘  └─────────────┘              │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│    Technologien: Vite, TypeScript, Tailwind CSS, tRPC Client               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ tRPC HTTP/WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API LAYER                                        │
│                                                                              │
│    ┌────────────────────────────┐    ┌────────────────────────────┐        │
│    │      Flask Backend         │    │      tRPC Bridge           │        │
│    │    (Port 5001)             │    │    (Port 3000)             │        │
│    │                            │    │                            │        │
│    │  • Sentinel API            │◄───┤  • Type-Safe Procedures    │        │
│    │  • KIBank Endpoints        │    │  • React Query Integration │        │
│    │  • Security Flow           │    │  • Real-time Updates       │        │
│    │  • 384+ Endpoints          │    │  • Superjson Transformer   │        │
│    └────────────────────────────┘    └────────────────────────────┘        │
│                                                                              │
│    Technologien: Flask, Flask-CORS, tRPC, Superjson, Zod                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Internal Calls
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LOGIC LAYER                                  │
│                                                                              │
│    ┌─────────────────────────────────┐  ┌─────────────────────────────────┐ │
│    │      KISWARM5.0 Modules         │  │       KIBank Modules            │ │
│    │         (57 Module)             │  │         (3 Module)              │ │
│    │                                 │  │                                 │ │
│    │  M1-M10: Foundation             │  │  M60: Authentication            │ │
│    │  M11-M30: Industrial Core       │  │       • OAuth Integration       │ │
│    │  M31-M33: HexStrike Guard       │  │       • KI-Entity Auth          │ │
│    │  M34-M38: Solar Chase           │  │       • Session Management      │ │
│    │  M39-M57: Advanced Modules      │  │                                 │ │
│    │                                 │  │  M61: Banking Operations        │ │
│    │  Wichtige Module:               │  │       • Account Management      │ │
│    │  • M4: Crypto Ledger            │  │       • SEPA Transfers          │ │
│    │  • M22: Byzantine Aggregator    │  │       • IBAN/BIC Integration    │ │
│    │  • M31: HexStrike Guard         │  │                                 │ │
│    │  • M34-M38: Solar Chase         │  │  M62: Investment & Reputation   │ │
│    │                                 │  │       • Portfolio Management    │ │
│    │                                 │  │       • Reputation Scoring      │ │
│    │                                 │  │       • Trading Limits          │ │
│    └─────────────────────────────────┘  └─────────────────────────────────┘ │
│                                                                              │
│    Technologien: Python 3.10+, Ollama, Mem0, Sentence Transformers          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Data Access
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                                                                              │
│    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│    │    Qdrant     │  │   MySQL/TiDB  │  │   S3 Storage  │                  │
│    │  (Vector DB)  │  │ (Relational)  │  │   (Files)     │                  │
│    │               │  │               │  │               │                  │
│    │ • Embeddings  │  │ • Accounts    │  │ • Documents   │                  │
│    │ • Knowledge   │  │ • Transaktion.│  │ • Backups     │                  │
│    │ • Memory      │  │ • Users       │  │ • Logs        │                  │
│    └───────────────┘  └───────────────┘  └───────────────┘                  │
│                                                                              │
│    Technologien: Qdrant Client, Drizzle ORM, S3 API                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Modul-Integration

### Security Flow

Jede Transaktion durchläuft einen 5-stufigen Sicherheitsprozess:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  M60     │    │  M31     │    │  M22     │    │ Execute  │    │  M62     │
│  AUTH    │───►│ SECURITY │───►│ VALIDATE │───►│          │───►│ REPUTAT. │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
  OAuth/KI       HexStrike       Byzantine      Transaction     Score
  Entity         12 AI Agents    N≥3f+1         Processing      Update
  Verify         150+ Tools      Consensus                      +5/-10

                                                    │
                                                    ▼
                                              ┌──────────┐
                                              │   M4     │
                                              │  LEDGER  │
                                              │ SHA-256  │
                                              │ Merkle   │
                                              └──────────┘
```

### Modul-Abhängigkeiten

```python
# KIBank Module Dependencies
M60 (Authentication)
    └── M4 (Crypto Ledger) - für Signaturen

M61 (Banking)
    ├── M60 (Auth) - für Entity-Verifizierung
    ├── M31 (HexStrike) - für Security Scans
    ├── M22 (Byzantine) - für Validation
    └── M4 (Ledger) - für Transaktions-Logging

M62 (Investment)
    ├── M60 (Auth) - für Reputation-Sync
    └── M61 (Banking) - für Investment-Transfers
```

## Datenfluss

### Transaktions-Flow

```
1. Client Request
   └── React Frontend initiiert Transaktion

2. tRPC Bridge
   └── Type-Safe Serialisierung mit Superjson

3. Flask API
   └── Routing zum entsprechenden Modul

4. Security Pipeline
   ├── M60: Authentifizierung
   ├── M31: HexStrike Security Scan
   ├── M22: Byzantine Validation
   └── Entscheidung: Erlaubt/Blockiert

5. Transaktion Ausführen
   └── M61: Banking Operations

6. Ledger Eintrag
   └── M4: Cryptographic Ledger (SHA-256 + Merkle)

7. Reputation Update
   └── M62: Score aktualisieren

8. Response
   └── Rückweg durch alle Schichten zum Client
```

### Real-time Updates

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │◄───────►│   WebSocket │◄───────►│   Backend   │
│  (Browser)  │  WS     │   Server    │  Pub/Sub │  (Flask)   │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ Events
                              ▼
                    ┌─────────────────────┐
                    │  Event Types:       │
                    │  • transaction      │
                    │  • investment       │
                    │  • reputation       │
                    │  • security_alert   │
                    │  • system_status    │
                    └─────────────────────┘
```

## Deployment-Architektur

### Development

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Machine                       │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Frontend  │  │   Bridge    │  │   Backend   │         │
│  │  Vite:5173  │  │  tRPC:3000  │  │ Flask:5001  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│         └────────────────┴────────────────┘                  │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   Qdrant    │  │   MySQL     │                          │
│  │   :6333     │  │   :3306     │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Production

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Production Cluster                              │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        Load Balancer (Nginx)                     │   │
│  │                         SSL Termination                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│         ┌──────────────────────────┼──────────────────────────┐        │
│         │                          │                          │        │
│         ▼                          ▼                          ▼        │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐  │
│  │  Frontend   │           │  Frontend   │           │  Frontend   │  │
│  │  Instance 1 │           │  Instance 2 │           │  Instance N │  │
│  └─────────────┘           └─────────────┘           └─────────────┘  │
│         │                          │                          │        │
│         └──────────────────────────┼──────────────────────────┘        │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    API Gateway (tRPC Bridge)                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│         ┌──────────────────────────┼──────────────────────────┐        │
│         │                          │                          │        │
│         ▼                          ▼                          ▼        │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐  │
│  │   Backend   │           │   Backend   │           │   Backend   │  │
│  │  Gunicorn 1 │           │  Gunicorn 2 │           │  Gunicorn N │  │
│  └─────────────┘           └─────────────┘           └─────────────┘  │
│         │                          │                          │        │
│         └──────────────────────────┼──────────────────────────┘        │
│                                    │                                     │
│         ┌──────────────────────────┼──────────────────────────┐        │
│         │                          │                          │        │
│         ▼                          ▼                          ▼        │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐  │
│  │   MySQL     │           │   Qdrant    │           │   Redis     │  │
│  │  Primary    │           │  Cluster    │           │   Cache     │  │
│  └─────────────┘           └─────────────┘           └─────────────┘  │
│         │                                                                │
│         ▼                                                                │
│  ┌─────────────┐                                                        │
│  │   MySQL     │                                                        │
│  │  Replicas   │                                                        │
│  └─────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technologie-Stack

### Frontend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| React | 18.x | UI Framework |
| TypeScript | 5.x | Type Safety |
| Vite | 5.x | Build Tool |
| Tailwind CSS | 4.x | Styling |
| shadcn/ui | Latest | Component Library |
| tRPC | 11.x | API Client |
| React Query | 5.x | Server State |
| Recharts | 2.x | Charts |

### Backend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| Python | 3.10+ | Runtime |
| Flask | 3.0+ | Web Framework |
| Qdrant Client | 1.7+ | Vector DB |
| Drizzle ORM | Latest | Database ORM |
| PyJWT | 2.8+ | JWT Handling |
| Cryptography | 41.0+ | Crypto Operations |
| Gunicorn | 21.0+ | WSGI Server |

### Infrastructure

| Technologie | Zweck |
|-------------|-------|
| Docker | Containerization |
| Docker Compose | Local Orchestration |
| Nginx | Reverse Proxy |
| MySQL/TiDB | Relational Database |
| Qdrant | Vector Database |
| S3 | Object Storage |

## Skalierbarkeit

### Horizontale Skalierung

```yaml
# Kubernetes HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: kiswarm-backend
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: kiswarm-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Performance Targets

| Metrik | Ziel |
|--------|------|
| API Response (p95) | < 200ms |
| Database Query (p95) | < 100ms |
| Concurrent Users | > 1,000 |
| Transactions/Hour | > 10,000 |
| Uptime | 99.9% |

## Sicherheit

### Authentifizierung

- **OAuth 2.0** für Human Operators
- **KI-Entity Auth** mit Public/Private Key
- **JWT Tokens** mit 24h Ablauf
- **Refresh Tokens** mit 30d Ablauf

### Verschlüsselung

- **TLS 1.3** für alle Verbindungen
- **AES-256-GCM** für Datenverschlüsselung
- **SHA-256** für Hashing
- **Merkle Trees** für Transaktions-Integrität

### Audit

- Alle Transaktionen im Ledger (M4)
- Security Scans (M31) protokolliert
- Byzantine Validation (M22) Ergebnisse
- Reputation Changes (M62) Historie
