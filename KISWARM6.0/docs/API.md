# KISWARM6.0 API Dokumentation

## Übersicht

KISWARM6.0 bietet **384+ API Endpoints** über zwei Haupt-Schnittstellen:

| Schnittstelle | Endpoints | Zweck |
|---------------|-----------|-------|
| **KIBank API** | 24 | Banking & Finance Operations |
| **KISWARM5.0 API** | 360 | AI, Security, Industrial Operations |

## Basis-URLs

```
Development:
  Backend API:  http://localhost:5001
  tRPC Bridge:  http://localhost:3000/api/trpc
  Frontend:     http://localhost:5173

Production:
  API:          https://api.kiswarm6.io
  tRPC:         https://api.kiswarm6.io/trpc
```

## Authentifizierung

### Bearer Token

Alle geschützten Endpoints erfordern einen Bearer Token:

```http
Authorization: Bearer kib.ki_abc123...signature
```

### Token-Ablauf

| Token Type | Ablaufzeit |
|------------|------------|
| Access Token | 24 Stunden |
| Refresh Token | 30 Tage |

---

## M60: Authentication API

### POST /kibank/auth/register

Registriert eine neue KI-Entity.

**Request Body:**
```json
{
  "name": "KI-Agent-Alpha",
  "entity_type": "agent",
  "public_key": "0x1234567890abcdef...",
  "metadata": {
    "description": "Primary trading agent",
    "version": "1.0.0"
  }
}
```

**Entity Types:**
- `agent` - KI Agent
- `orchestrator` - KI Orchestrator
- `service` - Service Account
- `human_operator` - Menschlicher Operator
- `bank_director` - Bank Director (höchste Berechtigung)

**Response (201):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "name": "KI-Agent-Alpha",
  "entity_type": "agent",
  "public_key": "0x1234567890abcdef...",
  "reputation_score": 500,
  "created_at": "2024-01-15T10:30:00Z",
  "last_active": "2024-01-15T10:30:00Z",
  "permissions": ["read:own", "write:own", "execute:tasks"]
}
```

---

### POST /kibank/auth/login

Authentifiziert eine KI-Entity.

**Request Body:**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "signature": "sha256_signature_of_challenge",
  "challenge": "random_challenge_string"
}
```

**Response (200):**
```json
{
  "session": {
    "session_id": "sess_xyz789",
    "entity_id": "ki_abc123def456ghi789",
    "expires_at": "2024-01-16T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "security_clearance": 65,
    "is_valid": true
  },
  "token": "kib.ki_abc...signature",
  "refresh_token": "kir_xyz789...",
  "entity": {
    "entity_id": "ki_abc123def456ghi789",
    "name": "KI-Agent-Alpha",
    "entity_type": "agent",
    "reputation_score": 525,
    "permissions": ["read:own", "write:own", "execute:tasks"]
  }
}
```

---

### POST /kibank/auth/logout

Beendet die aktuelle Session.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true
}
```

---

### POST /kibank/auth/refresh

Erneuert ein Access Token.

**Request Body:**
```json
{
  "refresh_token": "kir_xyz789..."
}
```

**Response (200):**
```json
{
  "token": "kib.ki_new...signature",
  "refresh_token": "kir_new...",
  "expires_at": "2024-01-16T11:00:00Z"
}
```

---

### GET /kibank/auth/verify

Verifiziert ein Token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "valid": true,
  "entity_id": "ki_abc123def456ghi789",
  "entity_type": "agent",
  "permissions": ["read:own", "write:own", "execute:tasks"],
  "security_clearance": 65
}
```

---

### GET /kibank/auth/session

Gibt Session-Informationen zurück.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "session": {
    "session_id": "sess_xyz789",
    "entity_id": "ki_abc123def456ghi789",
    "expires_at": "2024-01-16T10:30:00Z",
    "security_clearance": 65
  },
  "entity": {
    "entity_id": "ki_abc123def456ghi789",
    "name": "KI-Agent-Alpha",
    "entity_type": "agent",
    "reputation_score": 525
  }
}
```

---

### POST /kibank/auth/oauth/callback

Verarbeitet OAuth-Callbacks.

**Request Body:**
```json
{
  "provider": "manus",
  "code": "oauth_authorization_code",
  "state": "csrf_state_token"
}
```

**Response (200):**
```json
{
  "token": "kib.ki_oauth...signature",
  "refresh_token": "kir_oauth...",
  "entity": {
    "entity_id": "ki_oauth_abc123",
    "name": "OAuth User",
    "entity_type": "human_operator"
  }
}
```

---

### GET /kibank/auth/permissions

Gibt die Berechtigungen einer Entity zurück.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "permissions": ["read:own", "write:own", "execute:tasks"],
  "effective_permissions": [
    "read:own",
    "write:own",
    "execute:tasks",
    "approve:transactions"
  ],
  "reputation_score": 725,
  "security_clearance": 72
}
```

---

## M61: Banking Operations API

### POST /kibank/banking/account

Eröffnet ein neues Bankkonto.

**Request Body:**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "account_type": "checking",
  "currency": "EUR",
  "hub": "german"
}
```

**Account Types:**
- `checking` - Girokonto
- `savings` - Sparkonto
- `investment` - Investmentkonto
- `escrow` - Treuhandkonto
- `reserve` - Reservekonto

**Response (201):**
```json
{
  "account_id": "acc_xyz789abc",
  "entity_id": "ki_abc123def456ghi789",
  "account_type": "checking",
  "iban": "DE89370400440532013000",
  "bic": "DEUTDEFF",
  "currency": "EUR",
  "balance": "0.00",
  "available_balance": "0.00",
  "status": "active",
  "daily_limit": "100000.00",
  "monthly_limit": "500000.00",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### GET /kibank/banking/accounts

Listet alle Konten einer Entity auf.

**Query Parameters:**
```
entity_id: string (erforderlich)
```

**Response (200):**
```json
[
  {
    "account_id": "acc_xyz789abc",
    "entity_id": "ki_abc123def456ghi789",
    "account_type": "checking",
    "iban": "DE89370400440532013000",
    "bic": "DEUTDEFF",
    "currency": "EUR",
    "balance": "15000.00",
    "available_balance": "14500.00",
    "status": "active"
  }
]
```

---

### GET /kibank/banking/account/:id

Gibt Details zu einem Konto zurück.

**Path Parameters:**
```
id: Account ID
```

**Query Parameters:**
```
entity_id: string (optional, für Berechtigungsprüfung)
```

**Response (200):**
```json
{
  "account_id": "acc_xyz789abc",
  "entity_id": "ki_abc123def456ghi789",
  "account_type": "checking",
  "iban": "DE89370400440532013000",
  "bic": "DEUTDEFF",
  "currency": "EUR",
  "balance": "15000.00",
  "available_balance": "14500.00",
  "status": "active",
  "daily_limit": "100000.00",
  "monthly_limit": "500000.00",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### POST /kibank/banking/transfer

Führt eine interne Überweisung durch.

**Request Body:**
```json
{
  "from_account": "acc_xyz789abc",
  "to_account": "acc_target123",
  "amount": "1000.00",
  "currency": "EUR",
  "reference": "INV-2024-001",
  "description": "Payment for services"
}
```

**Response (201):**
```json
{
  "transaction_id": "tx_abc123xyz",
  "from_account": "acc_xyz789abc",
  "to_account": "acc_target123",
  "amount": "1000.00",
  "currency": "EUR",
  "transaction_type": "transfer",
  "status": "completed",
  "reference": "INV-2024-001",
  "description": "Payment for services",
  "fee": "0.00",
  "created_at": "2024-01-15T11:00:00Z",
  "completed_at": "2024-01-15T11:00:01Z"
}
```

---

### POST /kibank/banking/sepa

Führt eine SEPA-Überweisung durch.

**Request Body:**
```json
{
  "from_account": "acc_xyz789abc",
  "iban": "FR1420041010050500013M02606",
  "bic": "BNPAFRPP",
  "amount": "500.00",
  "currency": "EUR",
  "recipient_name": "Jean Dupont",
  "reference": "SEPA-2024-001",
  "description": "Invoice payment"
}
```

**Response (201):**
```json
{
  "transaction_id": "tx_sepa123",
  "from_account": "acc_xyz789abc",
  "to_account": null,
  "amount": "500.00",
  "currency": "EUR",
  "transaction_type": "sepa_outgoing",
  "status": "processing",
  "reference": "SEPA-2024-001",
  "description": "SEPA to Jean Dupont - Invoice payment",
  "fee": "0.00",
  "created_at": "2024-01-15T11:00:00Z",
  "completed_at": null
}
```

---

### GET /kibank/banking/transactions/:account_id

Gibt die Transaktions-Historie zurück.

**Path Parameters:**
```
account_id: Account ID
```

**Query Parameters:**
```
entity_id: string (optional)
limit: number (default: 50)
offset: number (default: 0)
```

**Response (200):**
```json
[
  {
    "transaction_id": "tx_abc123xyz",
    "from_account": "acc_xyz789abc",
    "to_account": "acc_target123",
    "amount": "1000.00",
    "currency": "EUR",
    "transaction_type": "transfer",
    "status": "completed",
    "reference": "INV-2024-001",
    "description": "Payment for services",
    "fee": "0.00",
    "created_at": "2024-01-15T11:00:00Z",
    "completed_at": "2024-01-15T11:00:01Z"
  }
]
```

---

### GET /kibank/banking/balance/:account_id

Gibt den aktuellen Kontostand zurück.

**Path Parameters:**
```
account_id: Account ID
```

**Query Parameters:**
```
entity_id: string (optional)
```

**Response (200):**
```json
{
  "account_id": "acc_xyz789abc",
  "balance": "15000.00",
  "available_balance": "14500.00",
  "currency": "EUR",
  "daily_limit": "100000.00",
  "daily_used": "1500.00",
  "monthly_limit": "500000.00",
  "monthly_used": "25000.00"
}
```

---

### POST /kibank/banking/validate-iban

Validiert eine IBAN.

**Request Body:**
```json
{
  "iban": "DE89370400440532013000"
}
```

**Response (200):**
```json
{
  "iban": "DE89370400440532013000",
  "valid": true,
  "country": "DE",
  "checksum": "89",
  "bank_code": "37040044",
  "account_number": "0532013000"
}
```

---

## M62: Investment & Reputation API

### GET /kibank/investment/portfolio

Gibt das Investment-Portfolio zurück.

**Query Parameters:**
```
entity_id: string (erforderlich)
```

**Response (200):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "investments": [
    {
      "investment_id": "inv_xyz789",
      "entity_id": "ki_abc123def456ghi789",
      "investment_type": "tcs_green_safe_house",
      "amount": "10000.00",
      "currency": "EUR",
      "status": "active",
      "current_value": "10850.00",
      "yield_rate": "8.5",
      "maturity_date": "2027-01-15T00:00:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "last_valuation": "2024-06-15T10:30:00Z",
      "roi": "8.50"
    }
  ],
  "total_value": "10850.00",
  "total_invested": "10000.00",
  "total_yield": "850.00",
  "roi_percentage": "8.50",
  "last_updated": "2024-06-15T10:30:00Z"
}
```

---

### POST /kibank/investment/invest

Tätigt eine Investition.

**Request Body:**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "investment_type": "tcs_green_safe_house",
  "amount": "5000.00",
  "currency": "EUR",
  "from_account": "acc_xyz789abc"
}
```

**Investment Types:**
| Type | Min. Amount | Yield | Maturity | Risk |
|------|-------------|-------|----------|------|
| `tcs_green_safe_house` | €1,000 | 8.5% | 36 months | Low |
| `ki_bonds` | €500 | 5.0% | 12 months | Low |
| `carbon_credits` | €100 | 6.0% | 24 months | Medium |
| `technology_fund` | €250 | 12.0% | 60 months | High |
| `liquidity_pool` | €100 | 4.0% | Flexible | Low |

**Response (201):**
```json
{
  "investment_id": "inv_new789",
  "entity_id": "ki_abc123def456ghi789",
  "investment_type": "tcs_green_safe_house",
  "amount": "5000.00",
  "currency": "EUR",
  "status": "active",
  "current_value": "5000.00",
  "yield_rate": "8.5",
  "maturity_date": "2027-06-15T00:00:00Z",
  "created_at": "2024-06-15T10:30:00Z",
  "roi": "0.00"
}
```

---

### POST /kibank/investment/divest

Löst eine Investition auf.

**Request Body:**
```json
{
  "investment_id": "inv_xyz789",
  "entity_id": "ki_abc123def456ghi789",
  "partial_amount": null
}
```

**Response (200):**
```json
{
  "investment_id": "inv_xyz789",
  "divested_amount": "10850.00",
  "roi": "8.50%",
  "status": "fully_divested"
}
```

---

### GET /kibank/investment/performance

Gibt Performance-Metriken zurück.

**Query Parameters:**
```
entity_id: string (erforderlich)
```

**Response (200):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "total_invested": "15000.00",
  "total_value": "16350.00",
  "total_roi": "9.00%",
  "annual_yield": "1275.00",
  "investment_count": 2,
  "by_type": {
    "tcs_green_safe_house": {
      "count": 1,
      "total_invested": "10000.00",
      "total_value": "10850.00",
      "yield": "850.00"
    },
    "ki_bonds": {
      "count": 1,
      "total_invested": "5000.00",
      "total_value": "5500.00",
      "yield": "425.00"
    }
  }
}
```

---

### GET /kibank/reputation/:entity_id

Gibt die Reputation einer Entity zurück.

**Response (200):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "score": 725,
  "level": "Gold",
  "tier": 4,
  "progress_to_next": 12.5,
  "trust_score": "A - Good",
  "risk_rating": "Low Risk"
}
```

---

### POST /kibank/reputation/update

Aktualisiert die Reputation.

**Request Body:**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "event_type": "transaction_success",
  "value": 1,
  "description": "Successful SEPA transfer"
}
```

**Event Types & Deltas:**
| Event | Delta |
|-------|-------|
| `transaction_success` | +5 |
| `transaction_failed` | -10 |
| `payment_on_time` | +10 |
| `payment_late` | -25 |
| `investment_growth` | +1 per 1% |
| `investment_loss` | -1 per 1% |
| `ki_proof_verified` | +100 |
| `security_violation` | -100 |
| `compliance_violation` | -50 |

**Response (200):**
```json
{
  "event_id": "rep_abc123",
  "previous_score": 720,
  "delta": 5,
  "new_score": 725,
  "event_type": "transaction_success"
}
```

---

### GET /kibank/reputation/history/:entity_id

Gibt die Reputation-Historie zurück.

**Query Parameters:**
```
limit: number (default: 50)
```

**Response (200):**
```json
[
  {
    "event_id": "rep_abc123",
    "entity_id": "ki_abc123def456ghi789",
    "event_type": "transaction_success",
    "delta": 5,
    "previous_score": 720,
    "new_score": 725,
    "description": "Successful SEPA transfer",
    "created_at": "2024-06-15T10:30:00Z"
  }
]
```

---

### GET /kibank/trading-limits/:entity_id

Gibt die Trading-Limits zurück.

**Response (200):**
```json
{
  "entity_id": "ki_abc123def456ghi789",
  "reputation_score": 725,
  "max_single_transaction": "100000.00",
  "daily_limit": "200000.00",
  "monthly_limit": "1000000.00",
  "max_open_investments": 20,
  "allowed_investment_types": [
    "tcs_green_safe_house",
    "ki_bonds",
    "carbon_credits",
    "technology_fund",
    "liquidity_pool"
  ],
  "leverage_allowed": true,
  "margin_trading": true
}
```

---

## KISWARM5.0 Legacy API

### GET /health

System Health Check.

**Response (200):**
```json
{
  "status": "ok",
  "version": "6.0.0",
  "modules": {
    "kiswarm": 57,
    "kibank": 3,
    "total": 60
  }
}
```

---

### GET /solar-chase/status

Solar Chase Coordinator Status.

**Response (200):**
```json
{
  "status": "active",
  "sun_position": {
    "latitude": 48.1351,
    "longitude": 11.5820
  },
  "active_nodes": 6,
  "energy_state": "surplus",
  "compute_allocation": "balanced"
}
```

---

### GET /hexstrike/status

HexStrike Guard Status.

**Response (200):**
```json
{
  "status": "operational",
  "agents": 12,
  "tools": 150,
  "last_scan": "2024-06-15T10:00:00Z",
  "threats_blocked": 0
}
```

---

### POST /hexstrike/scan

Initiiert einen Security Scan.

**Request Body:**
```json
{
  "target": "system",
  "scan_type": "quick"
}
```

**Scan Types:**
- `quick` - Schneller Scan (~30s)
- `full` - Vollständiger Scan (~5min)
- `deep` - Tiefgehender Scan (~30min)

**Response (200):**
```json
{
  "scan_id": "scan_20240615100000",
  "target": "system",
  "status": "completed",
  "threats_found": 0,
  "recommendations": [],
  "duration_seconds": 28
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid amount",
  "code": "INVALID_AMOUNT"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid or expired token",
  "code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied",
  "code": "FORBIDDEN"
}
```

### 404 Not Found
```json
{
  "error": "Account not found",
  "code": "NOT_FOUND"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```

---

## Rate Limits

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Auth | 10 req | 1 minute |
| Banking | 100 req | 1 minute |
| Investment | 50 req | 1 minute |
| Legacy | 200 req | 1 minute |

---

## WebSocket Events

### Connection
```
ws://localhost:3000/ws
```

### Events

**Transaction Update:**
```json
{
  "type": "transaction",
  "data": {
    "transaction_id": "tx_abc123",
    "status": "completed"
  }
}
```

**Reputation Update:**
```json
{
  "type": "reputation",
  "data": {
    "entity_id": "ki_abc123",
    "new_score": 725,
    "delta": 5
  }
}
```

**Security Alert:**
```json
{
  "type": "security_alert",
  "data": {
    "severity": "high",
    "message": "Suspicious activity detected"
  }
}
```
