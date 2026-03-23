# KISWARM6.0 Developer Guide

## Einführung

Dieser Guide richtet sich an Entwickler, die an KISWARM6.0 mitarbeiten oder eigene Module entwickeln möchten.

## Development Setup

### Repository Setup

```bash
# Repository klonen
git clone https://github.com/Baronki/KISWARM6.0.git
cd KISWARM6.0

# Entwicklungsumgebung einrichten
make setup-dev

# oder manuell:
./scripts/install.sh
```

### IDE Konfiguration

#### VS Code

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
```

## Code Style

### Python

```python
# Verwende Black für Formatierung
# Zeilenlänge: 88 Zeichen
# Docstrings: Google Style

def process_transaction(
    entity_id: str,
    amount: Decimal,
    currency: str = "EUR"
) -> Tuple[Optional[Transaction], Optional[str]]:
    """
    Verarbeitet eine Transaktion.

    Args:
        entity_id: Die ID der Entity
        amount: Der Transaktionsbetrag
        currency: Die Währung (Standard: EUR)

    Returns:
        Tuple mit Transaction und Fehlermeldung

    Raises:
        ValueError: Wenn amount <= 0
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")

    # Implementation
    transaction = Transaction(
        transaction_id=generate_id(),
        amount=amount,
        currency=currency
    )

    return transaction, None
```

### TypeScript

```typescript
// Verwende Prettier für Formatierung
// Strict mode aktivieren

interface TransactionRequest {
  entityId: string;
  amount: string;
  currency?: string;
}

interface TransactionResponse {
  transactionId: string;
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
}

async function processTransaction(
  request: TransactionRequest
): Promise<TransactionResponse> {
  const { entityId, amount, currency = 'EUR' } = request;

  // Validation
  if (parseFloat(amount) <= 0) {
    throw new Error('Amount must be positive');
  }

  // Implementation
  const response = await trpc.banking.transfer.mutate({
    fromAccount: entityId,
    amount,
    currency,
  });

  return response;
}
```

## Modul-Entwicklung

### Neues KIBank Modul erstellen

```python
# backend/python/kibank/m63_example.py

"""
M63: Example Module
===================

Beschreibung des Moduls.

Endpoints (8):
    POST /kibank/example/create    - Erstellen
    GET  /kibank/example/list      - Auflisten
    ...
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# KISWARM5.0 Integration
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentinel.crypto_ledger import CryptoLedger

logger = logging.getLogger(__name__)


class ExampleStatus(Enum):
    """Status Enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class ExampleEntity:
    """Example Entity Dataclass"""
    id: str
    name: str
    status: ExampleStatus = ExampleStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class KIBankExample:
    """
    M63: Example Module Implementation
    """

    def __init__(self, auth_module=None, banking_module=None):
        """
        Initialisiert das Modul.

        Args:
            auth_module: M60 Authentifizierungsmodul
            banking_module: M61 Banking-Modul
        """
        self.auth_module = auth_module
        self.banking_module = banking_module
        self.crypto_ledger = CryptoLedger()

        # Storage
        self._entities: Dict[str, ExampleEntity] = {}

        logger.info("M63: KIBankExample initialized")

    def create(self, name: str, **kwargs) -> Tuple[Optional[ExampleEntity], Optional[str]]:
        """
        POST /kibank/example/create

        Erstellt eine neue Entity.

        Args:
            name: Name der Entity

        Returns:
            Tuple[Entity, error_message]
        """
        # Validierung
        if not name or len(name) < 3:
            return None, "Name must be at least 3 characters"

        # Entity erstellen
        entity_id = self._generate_id()
        entity = ExampleEntity(
            id=entity_id,
            name=name,
            metadata=kwargs
        )

        # Speichern
        self._entities[entity_id] = entity

        # Im Ledger protokollieren
        self._record_in_ledger("created", entity.to_dict())

        logger.info(f"M63: Created entity: {entity_id}")

        return entity, None

    def list(self) -> List[ExampleEntity]:
        """
        GET /kibank/example/list

        Listet alle Entities auf.

        Returns:
            Liste der Entities
        """
        return list(self._entities.values())

    def _generate_id(self) -> str:
        """Generiert eine eindeutige ID"""
        import secrets
        return "ex_" + secrets.token_urlsafe(12)

    def _record_in_ledger(self, action: str, data: Dict):
        """Protokolliert im Ledger"""
        try:
            entry = {
                "module": "M63",
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            self.crypto_ledger.record(entry)
        except Exception as e:
            logger.warning(f"M63: Ledger warning: {e}")


# Flask Blueprint
def create_example_blueprint(auth_module=None, banking_module=None):
    """Erstellt Flask Blueprint für M63 Endpoints"""
    from flask import Blueprint, request, jsonify

    bp = Blueprint('kibank_example', __name__, url_prefix='/kibank/example')
    example = KIBankExample(auth_module, banking_module)

    @bp.route('/create', methods=['POST'])
    def create():
        data = request.json
        entity, error = example.create(
            name=data.get('name'),
            **data.get('metadata', {})
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(entity.to_dict()), 201

    @bp.route('/list', methods=['GET'])
    def list_all():
        entities = example.list()
        return jsonify([e.to_dict() for e in entities])

    return bp, example
```

### Modul registrieren

```python
# backend/run.py erweitern

from kibank.m63_example import create_example_blueprint, KIBankExample

# In create_kiswarm6_app():
example_bp, example_module = create_example_blueprint(auth_module, banking_module)
app.register_blueprint(example_bp)
app.example_module = example_module
```

### tRPC Router erweitern

```typescript
// bridge/trpc-bridge.ts erweitern

const exampleRouter = t.router({
  create: t.procedure
    .input(z.object({
      name: z.string().min(3),
      metadata: z.record(z.unknown()).optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<ExampleEntity>('/example/create', 'POST', input);
    }),

  list: t.procedure
    .query(async () => {
      return kibankRequest<ExampleEntity[]>('/example/list');
    })
});

// Zu appRouter hinzufügen
export const appRouter = t.router({
  // ... existing routers
  example: exampleRouter
});
```

## Testing

### Python Tests

```python
# tests/test_m63_example.py

import pytest
from kibank.m63_example import KIBankExample

@pytest.fixture
def example_module():
    return KIBankExample()

class TestKIBankExample:
    """Tests für M63 Example Module"""

    def test_create_entity_success(self, example_module):
        """Test erfolgreiche Erstellung"""
        entity, error = example_module.create("Test Entity")

        assert entity is not None
        assert error is None
        assert entity.name == "Test Entity"
        assert entity.id.startswith("ex_")

    def test_create_entity_invalid_name(self, example_module):
        """Test ungültiger Name"""
        entity, error = example_module.create("ab")

        assert entity is None
        assert error == "Name must be at least 3 characters"

    def test_list_entities(self, example_module):
        """Test Auflistung"""
        example_module.create("Entity 1")
        example_module.create("Entity 2")

        entities = example_module.list()

        assert len(entities) == 2

    def test_entity_to_dict(self, example_module):
        """Test to_dict Methode"""
        entity, _ = example_module.create("Test")
        entity_dict = entity.to_dict()

        assert "id" in entity_dict
        assert "name" in entity_dict
        assert "status" in entity_dict
        assert "created_at" in entity_dict
```

### TypeScript Tests

```typescript
// bridge/__tests__/example.test.ts

import { describe, it, expect } from 'vitest';
import { exampleRouter } from '../src/routers/example';

describe('Example Router', () => {
  it('should create an entity', async () => {
    const caller = exampleRouter.createCaller({});
    const result = await caller.create({
      name: 'Test Entity',
    });

    expect(result.name).toBe('Test Entity');
    expect(result.id).toMatch(/^ex_/);
  });

  it('should list entities', async () => {
    const caller = exampleRouter.createCaller({});

    await caller.create({ name: 'Entity 1' });
    await caller.create({ name: 'Entity 2' });

    const entities = await caller.list();
    expect(entities.length).toBe(2);
  });
});
```

### Tests ausführen

```bash
# Python Tests
cd backend
pytest tests/ -v --cov=kibank

# TypeScript Tests
cd bridge
pnpm test

# Alle Tests
make test
```

## Contributing

### Workflow

```
1. Fork erstellen
2. Feature Branch: git checkout -b feature/my-feature
3. Änderungen committen: git commit -m 'feat: add feature'
4. Push: git push origin feature/my-feature
5. Pull Request erstellen
```

### Commit Messages

```
feat: Neue Funktion
fix: Bug-Fix
docs: Dokumentation
style: Formatierung
refactor: Refactoring
test: Tests
chore: Build/CI

Beispiele:
feat(kibank): add M63 example module
fix(auth): resolve token refresh issue
docs(api): update endpoint documentation
```

### Pull Request Checklist

- [ ] Code compiliert ohne Fehler
- [ ] Alle Tests bestehen
- [ ] Coverage >= 80%
- [ ] Dokumentation aktualisiert
- [ ] CHANGELOG.md aktualisiert
- [ ] Keine Secrets committed

## Debugging

### Backend Debugging

```python
# Logging aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# Debugger
import pdb; pdb.set_trace()

# oder mit ipdb
import ipdb; ipdb.set_trace()
```

### Frontend Debugging

```typescript
// Console Logging
console.log('Debug:', variable);

// React DevTools
// Browser Extension installieren

// tRPC Debug
const client = createTRPCProxyClient({
  links: [
    httpLink({
      url: '/api/trpc',
      headers: { 'x-debug': 'true' }
    })
  ]
});
```

## Performance Optimization

### Backend

```python
# Query Optimization
# Indizes verwenden
accounts = db.query(Account).filter(
    Account.entity_id == entity_id
).options(
    joinedload(Account.transactions)  # Eager Loading
).all()

# Caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_entity(entity_id: str):
    return db.query(Entity).get(entity_id)

# Async Operations
import asyncio

async def process_batch(items):
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

### Frontend

```typescript
// React Query Caching
const { data } = trpc.banking.listAccounts.useQuery(
  { entityId },
  {
    staleTime: 5 * 60 * 1000, // 5 Minuten
    cacheTime: 10 * 60 * 1000, // 10 Minuten
  }
);

// Lazy Loading
const LazyComponent = React.lazy(() => import('./HeavyComponent'));

// Memoization
const memoizedValue = useMemo(() => computeExpensive(a, b), [a, b]);
```

## Release Process

### Version Bumping

```bash
# Patch Release (6.0.1)
npm version patch

# Minor Release (6.1.0)
npm version minor

# Major Release (7.0.0)
npm version major
```

### Release Checklist

1. [ ] Tests bestehen
2. [ ] Dokumentation aktuell
3. [ ] CHANGELOG.md aktualisiert
4. [ ] Version bumpen
5. [ ] Git Tag erstellen
6. [ ] Build erstellen
7. [ ] Deployen
8. [ ] GitHub Release

## Support

- **Dokumentation**: `/docs`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: dev@kiswarm6.io
