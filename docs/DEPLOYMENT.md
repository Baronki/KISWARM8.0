# KISWARM6.0 Deployment Guide

## Übersicht

Diese Dokumentation beschreibt die Installation und den Betrieb von KISWARM6.0 in verschiedenen Umgebungen.

## Voraussetzungen

### Hardware-Anforderungen

| Komponente | Minimum | Empfohlen | Production |
|------------|---------|-----------|------------|
| CPU | 4 Cores | 8 Cores | 16+ Cores |
| RAM | 8 GB | 16 GB | 64+ GB |
| Disk | 50 GB SSD | 200 GB SSD | 1+ TB NVMe |
| Network | 100 Mbps | 1 Gbps | 10 Gbps |

### Software-Anforderungen

| Software | Version |
|----------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| MySQL/TiDB | 8.0+ |
| Qdrant | 1.7+ |
| Docker | 24.0+ |
| Docker Compose | 2.20+ |

## Installation

### Option 1: Script-Installation

```bash
# Repository klonen
git clone https://github.com/Baronki/KISWARM6.0.git
cd KISWARM6.0

# Installation ausführen
chmod +x scripts/install.sh
./scripts/install.sh
```

### Option 2: Docker-Installation

```bash
# Repository klonen
git clone https://github.com/Baronki/KISWARM6.0.git
cd KISWARM6.0

# Umgebung konfigurieren
cp .env.example .env
# .env Datei bearbeiten

# Container starten
docker-compose up -d
```

### Option 3: Manuelles Setup

#### Backend Setup

```bash
cd KISWARM6.0/backend

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export DATABASE_URL="mysql://user:password@localhost:3306/kiswarm6"
export KIBANK_SECRET_KEY="your-secret-key"
export KISWARM_API_URL="http://localhost:5001"

# Datenbank initialisieren
python -c "from db import init_db; init_db()"

# Server starten
python run.py
```

#### Frontend Setup

```bash
cd KISWARM6.0/frontend

# Abhängigkeiten installieren
pnpm install

# Umgebungsvariablen setzen
export VITE_KISWARM_API_URL="http://localhost:5001"
export VITE_TRPC_URL="http://localhost:3000/api/trpc"

# Entwicklungsserver starten
pnpm dev
```

#### tRPC Bridge Setup

```bash
cd KISWARM6.0/bridge

# Abhängigkeiten installieren
pnpm install

# Server starten
pnpm dev
```

## Konfiguration

### Umgebungsvariablen

#### Backend (.env)

```bash
# Database
DATABASE_URL=mysql://kiswarm:password@localhost:3306/kiswarm6
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# KIBank
KIBANK_SECRET_KEY=your-256-bit-secret-key-here
KIBANK_TOKEN_EXPIRY_HOURS=24
KIBANK_REFRESH_TOKEN_DAYS=30

# OAuth
OAUTH_PROVIDER=manus
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=https://your-domain/oauth/callback

# Security
HEXSTRIKE_ENABLED=true
BYZANTINE_NODES=4
CONSENSUS_TIMEOUT=30

# API
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=false

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=kiswarm6

# S3 Storage
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET=kiswarm6-files
```

#### Frontend (.env)

```bash
# API URLs
VITE_KISWARM_API_URL=http://localhost:5001
VITE_TRPC_URL=http://localhost:3000/api/trpc
VITE_WS_URL=ws://localhost:3000/ws

# OAuth
VITE_OAUTH_PORTAL_URL=https://oauth.manus.im
VITE_APP_ID=your-app-id

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_WEBSOCKET=true

# App Config
VITE_APP_TITLE="KISWARM6.0 - KIBank Portal"
VITE_APP_LOGO=/logo.svg
```

### Datenbank-Schema

```sql
-- Haupttabellen
CREATE TABLE entities (
    entity_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type ENUM('agent', 'orchestrator', 'service', 'human_operator', 'bank_director'),
    public_key TEXT NOT NULL,
    reputation_score INT DEFAULT 500,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON
);

CREATE TABLE accounts (
    account_id VARCHAR(32) PRIMARY KEY,
    entity_id VARCHAR(32) NOT NULL,
    account_type ENUM('checking', 'savings', 'investment', 'escrow', 'reserve'),
    iban VARCHAR(34) UNIQUE NOT NULL,
    bic VARCHAR(11) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    balance DECIMAL(20, 2) DEFAULT 0.00,
    available_balance DECIMAL(20, 2) DEFAULT 0.00,
    status ENUM('active', 'pending', 'frozen', 'closed', 'waitlist'),
    daily_limit DECIMAL(20, 2),
    monthly_limit DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    from_account VARCHAR(32),
    to_account VARCHAR(32),
    amount DECIMAL(20, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    transaction_type ENUM('deposit', 'withdrawal', 'transfer', 'sepa_incoming', 'sepa_outgoing', 'fee', 'interest'),
    status ENUM('pending', 'processing', 'completed', 'failed', 'reversed'),
    reference VARCHAR(255),
    description TEXT,
    fee DECIMAL(20, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    metadata JSON
);

CREATE TABLE investments (
    investment_id VARCHAR(32) PRIMARY KEY,
    entity_id VARCHAR(32) NOT NULL,
    investment_type ENUM('tcs_green_safe_house', 'ki_bonds', 'carbon_credits', 'technology_fund', 'liquidity_pool'),
    amount DECIMAL(20, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    status ENUM('active', 'pending', 'matured', 'withdrawn', 'failed'),
    current_value DECIMAL(20, 2),
    yield_rate DECIMAL(5, 2),
    maturity_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_valuation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

CREATE TABLE reputation_events (
    event_id VARCHAR(32) PRIMARY KEY,
    entity_id VARCHAR(32) NOT NULL,
    event_type ENUM('transaction_success', 'transaction_failed', 'payment_on_time', 'payment_late', 'investment_growth', 'investment_loss', 'ki_proof_verified', 'security_violation', 'compliance_violation'),
    delta INT NOT NULL,
    previous_score INT NOT NULL,
    new_score INT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
);

-- Indizes
CREATE INDEX idx_accounts_entity ON accounts(entity_id);
CREATE INDEX idx_transactions_from ON transactions(from_account);
CREATE INDEX idx_transactions_to ON transactions(to_account);
CREATE INDEX idx_transactions_created ON transactions(created_at);
CREATE INDEX idx_investments_entity ON investments(entity_id);
CREATE INDEX idx_reputation_entity ON reputation_events(entity_id);
```

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-Stage Build
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY frontend/ .
RUN pnpm build

FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=backend-builder /app/backend /app/backend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY bridge/ /app/bridge

# Install Node.js for bridge
RUN apt-get update && apt-get install -y nodejs npm

EXPOSE 5001 3000
CMD ["sh", "-c", "cd /app/backend && python run.py & cd /app/bridge && npm start"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      target: backend-builder
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=mysql://kiswarm:kiswarm@mysql:3306/kiswarm6
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - mysql
      - qdrant
    networks:
      - kiswarm-network

  frontend:
    build:
      context: .
      target: frontend-builder
    ports:
      - "5173:5173"
    environment:
      - VITE_KISWARM_API_URL=http://localhost:5001
    depends_on:
      - backend
    networks:
      - kiswarm-network

  bridge:
    build:
      context: ./bridge
    ports:
      - "3000:3000"
    environment:
      - KISWARM_API_URL=http://backend:5001
    depends_on:
      - backend
    networks:
      - kiswarm-network

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=kiswarm6
      - MYSQL_USER=kiswarm
      - MYSQL_PASSWORD=kiswarm
    volumes:
      - mysql-data:/var/lib/mysql
      - ./init-db:/docker-entrypoint-initdb.d
    ports:
      - "3306:3306"
    networks:
      - kiswarm-network

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant-data:/qdrant/storage
    networks:
      - kiswarm-network

volumes:
  mysql-data:
  qdrant-data:

networks:
  kiswarm-network:
    driver: bridge
```

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kiswarm6
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kiswarm-config
  namespace: kiswarm6
data:
  DATABASE_URL: "mysql://kiswarm:kiswarm@mysql:3306/kiswarm6"
  QDRANT_URL: "http://qdrant:6333"
  FLASK_PORT: "5001"
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kiswarm-secrets
  namespace: kiswarm6
type: Opaque
stringData:
  KIBANK_SECRET_KEY: "your-secret-key"
  DATABASE_PASSWORD: "kiswarm"
```

### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kiswarm-backend
  namespace: kiswarm6
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kiswarm-backend
  template:
    metadata:
      labels:
        app: kiswarm-backend
    spec:
      containers:
      - name: backend
        image: kiswarm6/backend:latest
        ports:
        - containerPort: 5001
        envFrom:
        - configMapRef:
            name: kiswarm-config
        - secretRef:
            name: kiswarm-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kiswarm-backend
  namespace: kiswarm6
spec:
  selector:
    app: kiswarm-backend
  ports:
  - port: 5001
    targetPort: 5001
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kiswarm-ingress
  namespace: kiswarm6
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.kiswarm6.io
    secretName: kiswarm-tls
  rules:
  - host: api.kiswarm6.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kiswarm-backend
            port:
              number: 5001
```

## Monitoring

### Prometheus Config

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kiswarm-backend'
    static_configs:
      - targets: ['backend:5001']
    metrics_path: /metrics

  - job_name: 'kiswarm-bridge'
    static_configs:
      - targets: ['bridge:3000']
```

### Grafana Dashboard

Key Metrics:
- Request Rate (req/s)
- Response Time (p50, p95, p99)
- Error Rate (%)
- Active Connections
- Database Query Time
- Memory Usage
- CPU Usage

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# MySQL Backup
mysqldump -u kiswarm -p kiswarm6 > $BACKUP_DIR/kiswarm6_$DATE.sql

# Qdrant Backup
curl -X POST http://localhost:6333/collections/kiswarm6/snapshots

# Upload to S3
aws s3 cp $BACKUP_DIR/kiswarm6_$DATE.sql s3://kiswarm-backups/
```

### Recovery

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

# MySQL Restore
mysql -u kiswarm -p kiswarm6 < $BACKUP_FILE

# Qdrant Restore
curl -X PUT http://localhost:6333/collections/kiswarm6/snapshots/upload \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@qdrant_snapshot"
```

## Troubleshooting

### Häufige Probleme

| Problem | Lösung |
|---------|--------|
| Database Connection Failed | DATABASE_URL prüfen, MySQL starten |
| Token Invalid | SECRET_KEY prüfen, Token refreshen |
| CORS Error | CORS origins konfigurieren |
| Memory Limit | Heap size erhöhen |
| Slow Queries | Indizes prüfen, Query optimieren |

### Logs

```bash
# Backend Logs
docker logs kiswarm-backend -f

# Frontend Logs
docker logs kiswarm-frontend -f

# Alle Logs
docker-compose logs -f
```

### Health Check

```bash
# API Health
curl http://localhost:5001/health

# Database Health
curl http://localhost:5001/api/v6/status

# Full Health Check
./scripts/health-check.sh
```
