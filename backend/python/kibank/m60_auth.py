"""
M60: KIBank Authentication Module
=================================

OAuth + KI-Entity Authentifizierung für KISWARM6.0

Endpoints (8):
    POST /kibank/auth/register       - KI-Entity Registrierung
    POST /kibank/auth/login          - KI-Entity Login
    POST /kibank/auth/logout         - Session beenden
    POST /kibank/auth/refresh        - Token Refresh
    GET  /kibank/auth/verify         - Token Verifikation
    GET  /kibank/auth/session        - Aktive Session Info
    POST /kibank/auth/oauth/callback - OAuth Callback
    GET  /kibank/auth/permissions    - Berechtigungen abrufen

Security Flow:
    1. Request → M60: Authentifizierung
    2. M31: HexStrike Security Scan
    3. M22: Byzantine Validation
    4. Execute → M4: Cryptographic Ledger
    5. M62: Reputation Update

Integration mit KISWARM5.0:
    - Verwendet crypto_ledger (M4) für Signaturen
    - Integriert mit hexstrike_guard (M31) für Security
    - Nutzt byzantine_aggregator (M22) für Validation
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

# KISWARM5.0 Integration
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentinel.crypto_ledger import CryptoLedger

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentifizierungsmethoden"""
    OAUTH = "oauth"
    KI_ENTITY = "ki_entity"
    API_KEY = "api_key"
    CERTIFICATE = "certificate"


class KIEntityType(Enum):
    """KI-Entity Typen"""
    AGENT = "agent"
    ORCHESTRATOR = "orchestrator"
    SERVICE = "service"
    HUMAN_OPERATOR = "human_operator"
    BANK_DIRECTOR = "bank_director"


@dataclass
class KIEntity:
    """KI-Entity Repräsentation"""
    entity_id: str
    name: str
    entity_type: KIEntityType
    public_key: str
    reputation_score: int = 500  # Basis-Score
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "public_key": self.public_key,
            "reputation_score": self.reputation_score,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "permissions": self.permissions,
            "metadata": self.metadata
        }


@dataclass
class AuthSession:
    """Authentifizierungs-Session"""
    session_id: str
    entity_id: str
    token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    security_clearance: int = 0  # 0-100

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "entity_id": self.entity_id,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "security_clearance": self.security_clearance,
            "is_valid": not self.is_expired()
        }


class KIBankAuth:
    """
    M60: KIBank Authentication Module

    Verwaltet KI-Entity Authentifizierung mit Integration in
    die KISWARM5.0 Security-Infrastruktur.
    """

    # Token-Konfiguration
    TOKEN_EXPIRY_HOURS = 24
    REFRESH_TOKEN_EXPIRY_DAYS = 30
    MAX_SESSIONS_PER_ENTITY = 5

    # Security-Konfiguration
    MIN_PASSWORD_LENGTH = 32
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialisiert das Authentifizierungsmodul.

        Args:
            secret_key: Geheimer Schlüssel für Token-Signierung
        """
        self.secret_key = secret_key or os.environ.get(
            "KIBANK_SECRET_KEY",
            secrets.token_hex(32)
        )
        self.crypto_ledger = CryptoLedger()

        # In-Memory Storage (in Production: Database)
        self._entities: Dict[str, KIEntity] = {}
        self._sessions: Dict[str, AuthSession] = {}
        self._refresh_tokens: Dict[str, str] = {}  # token -> entity_id
        self._login_attempts: Dict[str, List[datetime]] = {}
        self._locked_accounts: Dict[str, datetime] = {}

        logger.info("M60: KIBankAuth initialized")

    # ==================== ENDPOINT IMPLEMENTATIONS ====================

    def register(self, name: str, entity_type: KIEntityType,
                 public_key: str, metadata: Optional[Dict] = None) -> Tuple[Optional[KIEntity], Optional[str]]:
        """
        POST /kibank/auth/register

        Registriert eine neue KI-Entity.

        Args:
            name: Name der Entity
            entity_type: Typ der Entity
            public_key: Öffentlicher Schlüssel für Signaturverifikation
            metadata: Zusätzliche Metadaten

        Returns:
            Tuple[KIEntity, error_message]
        """
        # Validierung
        if not name or len(name) < 3:
            return None, "Name must be at least 3 characters"

        if not public_key or len(public_key) < 64:
            return None, "Invalid public key format"

        # Entity-ID generieren
        entity_id = self._generate_entity_id(name, public_key)

        # Prüfen ob bereits existiert
        if entity_id in self._entities:
            return None, "Entity already registered"

        # KI-Entity erstellen
        entity = KIEntity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            public_key=public_key,
            metadata=metadata or {},
            permissions=self._get_default_permissions(entity_type)
        )

        # In Ledger eintragen
        self._record_in_ledger("register", entity.to_dict())

        # Speichern
        self._entities[entity_id] = entity

        logger.info(f"M60: Registered new KI-Entity: {entity_id}")

        return entity, None

    def login(self, entity_id: str, signature: str,
              challenge: str, ip_address: Optional[str] = None,
              user_agent: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        POST /kibank/auth/login

        Authentifiziert eine KI-Entity.

        Args:
            entity_id: ID der Entity
            signature: Signatur des Challenge-Strings
            challenge: Challenge-String der signiert wurde
            ip_address: Client IP-Adresse
            user_agent: Client User-Agent

        Returns:
            Tuple[session_data, error_message]
        """
        # Account-Lockout prüfen
        if self._is_account_locked(entity_id):
            return None, "Account is temporarily locked"

        # Entity existiert?
        entity = self._entities.get(entity_id)
        if not entity:
            self._record_login_attempt(entity_id, failed=True)
            return None, "Entity not found"

        # Signatur verifizieren
        if not self._verify_signature(entity.public_key, challenge, signature):
            self._record_login_attempt(entity_id, failed=True)
            return None, "Invalid signature"

        # Login-Versuche zurücksetzen
        self._login_attempts[entity_id] = []

        # Alte Sessions bereinigen
        self._cleanup_entity_sessions(entity_id)

        # Neue Session erstellen
        session = self._create_session(entity, ip_address, user_agent)

        # Security Clearance berechnen
        session.security_clearance = self._calculate_security_clearance(entity)

        # Im Ledger protokollieren
        self._record_in_ledger("login", {
            "entity_id": entity_id,
            "session_id": session.session_id,
            "ip_address": ip_address
        })

        # Entity Last Active aktualisieren
        entity.last_active = datetime.now()

        logger.info(f"M60: KI-Entity logged in: {entity_id}")

        return {
            "session": session.to_dict(),
            "token": session.token,
            "refresh_token": session.refresh_token,
            "entity": entity.to_dict()
        }, None

    def logout(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        POST /kibank/auth/logout

        Beendet eine aktive Session.

        Args:
            token: Access Token

        Returns:
            Tuple[success, error_message]
        """
        session = self._find_session_by_token(token)
        if not session:
            return False, "Invalid token"

        # Im Ledger protokollieren
        self._record_in_ledger("logout", {
            "entity_id": session.entity_id,
            "session_id": session.session_id
        })

        # Session löschen
        del self._sessions[session.session_id]
        if session.refresh_token in self._refresh_tokens:
            del self._refresh_tokens[session.refresh_token]

        logger.info(f"M60: Session logged out: {session.session_id}")

        return True, None

    def refresh(self, refresh_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        POST /kibank/auth/refresh

        Erneuert ein Access Token.

        Args:
            refresh_token: Refresh Token

        Returns:
            Tuple[new_tokens, error_message]
        """
        entity_id = self._refresh_tokens.get(refresh_token)
        if not entity_id:
            return None, "Invalid refresh token"

        entity = self._entities.get(entity_id)
        if not entity:
            return None, "Entity not found"

        # Neue Session erstellen
        session = self._create_session(entity)
        session.security_clearance = self._calculate_security_clearance(entity)

        # Altes Refresh Token löschen
        del self._refresh_tokens[refresh_token]

        return {
            "token": session.token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat()
        }, None

    def verify(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        GET /kibank/auth/verify

        Verifiziert ein Access Token.

        Args:
            token: Access Token

        Returns:
            Tuple[verification_result, error_message]
        """
        session = self._find_session_by_token(token)
        if not session:
            return None, "Invalid token"

        if session.is_expired():
            del self._sessions[session.session_id]
            return None, "Token expired"

        entity = self._entities.get(session.entity_id)
        if not entity:
            return None, "Entity not found"

        return {
            "valid": True,
            "entity_id": session.entity_id,
            "entity_type": entity.entity_type.value,
            "permissions": entity.permissions,
            "security_clearance": session.security_clearance
        }, None

    def get_session(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        GET /kibank/auth/session

        Gibt Informationen zur aktuellen Session zurück.

        Args:
            token: Access Token

        Returns:
            Tuple[session_info, error_message]
        """
        session = self._find_session_by_token(token)
        if not session:
            return None, "Invalid token"

        if session.is_expired():
            return None, "Session expired"

        entity = self._entities.get(session.entity_id)
        if not entity:
            return None, "Entity not found"

        return {
            "session": session.to_dict(),
            "entity": {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "entity_type": entity.entity_type.value,
                "reputation_score": entity.reputation_score,
                "permissions": entity.permissions
            }
        }, None

    def oauth_callback(self, provider: str, code: str,
                       state: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        POST /kibank/auth/oauth/callback

        Verarbeitet OAuth-Callbacks.

        Args:
            provider: OAuth-Provider (manus, github, etc.)
            code: Authorization Code
            state: State Parameter

        Returns:
            Tuple[oauth_result, error_message]
        """
        # OAuth-Implementierung (Platzhalter für echte OAuth-Integration)
        # In Production: Verbindung zu Manus OAuth

        # Für jetzt: Validierung der Parameter
        if not code or not state:
            return None, "Missing OAuth parameters"

        # Entity basierend auf OAuth erstellen/abrufen
        entity_id = self._derive_entity_from_oauth(provider, code)

        if entity_id not in self._entities:
            # Neue Entity aus OAuth erstellen
            entity = KIEntity(
                entity_id=entity_id,
                name=f"oauth_{provider}_{entity_id[:8]}",
                entity_type=KIEntityType.AGENT,
                public_key=self._generate_temp_key(),
                permissions=self._get_default_permissions(KIEntityType.AGENT)
            )
            self._entities[entity_id] = entity
        else:
            entity = self._entities[entity_id]

        # Session erstellen
        session = self._create_session(entity)

        self._record_in_ledger("oauth_login", {
            "provider": provider,
            "entity_id": entity_id
        })

        return {
            "token": session.token,
            "refresh_token": session.refresh_token,
            "entity": entity.to_dict()
        }, None

    def get_permissions(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        GET /kibank/auth/permissions

        Gibt die Berechtigungen einer Entity zurück.

        Args:
            token: Access Token

        Returns:
            Tuple[permissions, error_message]
        """
        session = self._find_session_by_token(token)
        if not session or session.is_expired():
            return None, "Invalid or expired token"

        entity = self._entities.get(session.entity_id)
        if not entity:
            return None, "Entity not found"

        # Berechtigungen basierend auf Reputation und Typ
        effective_permissions = self._calculate_effective_permissions(entity)

        return {
            "entity_id": entity.entity_id,
            "permissions": entity.permissions,
            "effective_permissions": effective_permissions,
            "reputation_score": entity.reputation_score,
            "security_clearance": session.security_clearance
        }, None

    # ==================== HELPER METHODS ====================

    def _generate_entity_id(self, name: str, public_key: str) -> str:
        """Generiert eine eindeutige Entity-ID"""
        data = f"{name}:{public_key}:{time.time()}"
        return "ki_" + hashlib.sha256(data.encode()).hexdigest()[:24]

    def _generate_token(self, entity_id: str, secret: str) -> str:
        """Generiert ein Access Token"""
        payload = f"{entity_id}:{time.time()}:{secrets.token_hex(16)}"
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"kib.{payload}.{signature}"

    def _generate_refresh_token(self) -> str:
        """Generiert ein Refresh Token"""
        return "kir_" + secrets.token_urlsafe(32)

    def _verify_signature(self, public_key: str, challenge: str, signature: str) -> bool:
        """Verifiziert eine digitale Signatur"""
        # Vereinfachte Signaturprüfung
        # In Production: Echte kryptografische Verifikation
        expected = hmac.new(
            public_key.encode()[:32],
            challenge.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    def _create_session(self, entity: KIEntity,
                        ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None) -> AuthSession:
        """Erstellt eine neue Session"""
        session_id = "sess_" + secrets.token_urlsafe(16)
        token = self._generate_token(entity.entity_id, self.secret_key)
        refresh_token = self._generate_refresh_token()

        session = AuthSession(
            session_id=session_id,
            entity_id=entity.entity_id,
            token=token,
            refresh_token=refresh_token,
            expires_at=datetime.now() + timedelta(hours=self.TOKEN_EXPIRY_HOURS),
            ip_address=ip_address,
            user_agent=user_agent
        )

        self._sessions[session_id] = session
        self._refresh_tokens[refresh_token] = entity.entity_id

        return session

    def _find_session_by_token(self, token: str) -> Optional[AuthSession]:
        """Findet eine Session anhand des Tokens"""
        for session in self._sessions.values():
            if session.token == token:
                return session
        return None

    def _cleanup_entity_sessions(self, entity_id: str):
        """Bereinigt alte Sessions einer Entity"""
        entity_sessions = [
            s for s in self._sessions.values()
            if s.entity_id == entity_id
        ]

        if len(entity_sessions) >= self.MAX_SESSIONS_PER_ENTITY:
            # Älteste Sessions löschen
            entity_sessions.sort(key=lambda s: s.created_at)
            for session in entity_sessions[:-self.MAX_SESSIONS_PER_ENTITY + 1]:
                del self._sessions[session.session_id]

    def _get_default_permissions(self, entity_type: KIEntityType) -> List[str]:
        """Gibt Standard-Berechtigungen für einen Entity-Typ"""
        base_permissions = ["read:own", "write:own"]

        type_permissions = {
            KIEntityType.AGENT: base_permissions + ["execute:tasks"],
            KIEntityType.ORCHESTRATOR: base_permissions + ["execute:tasks", "manage:agents"],
            KIEntityType.SERVICE: base_permissions + ["execute:services"],
            KIEntityType.HUMAN_OPERATOR: base_permissions + ["approve:transactions", "view:audit"],
            KIEntityType.BANK_DIRECTOR: base_permissions + [
                "approve:transactions", "view:audit", "manage:accounts",
                "manage:investments", "approve:high_value", "access:compliance"
            ]
        }

        return type_permissions.get(entity_type, base_permissions)

    def _calculate_security_clearance(self, entity: KIEntity) -> int:
        """Berechnet die Security-Clearance basierend auf Reputation"""
        # Basis-Clearance
        base = 20

        # Reputation-Einfluss (0-60 Punkte)
        reputation_factor = (entity.reputation_score / 1000) * 60

        # Entity-Type Bonus (0-20 Punkte)
        type_bonus = {
            KIEntityType.BANK_DIRECTOR: 20,
            KIEntityType.HUMAN_OPERATOR: 15,
            KIEntityType.ORCHESTRATOR: 10,
            KIEntityType.SERVICE: 5,
            KIEntityType.AGENT: 0
        }.get(entity.entity_type, 0)

        return min(100, int(base + reputation_factor + type_bonus))

    def _calculate_effective_permissions(self, entity: KIEntity) -> List[str]:
        """Berechnet effektive Berechtigungen basierend auf Reputation"""
        permissions = entity.permissions.copy()

        # High-Value Transactions erst ab Reputation 700
        if entity.reputation_score >= 700:
            permissions.append("approve:high_value")

        # Compliance-Zugang ab Reputation 800
        if entity.reputation_score >= 800:
            permissions.append("access:compliance_reports")

        # Bank-Director Extra-Berechtigungen
        if entity.entity_type == KIEntityType.BANK_DIRECTOR:
            if entity.reputation_score >= 900:
                permissions.append("override:limits")

        return permissions

    def _record_login_attempt(self, entity_id: str, failed: bool = False):
        """Protokolliert Login-Versuche"""
        if entity_id not in self._login_attempts:
            self._login_attempts[entity_id] = []

        self._login_attempts[entity_id].append(datetime.now())

        # Alte Versuche bereinigen (älter als 1 Stunde)
        cutoff = datetime.now() - timedelta(hours=1)
        self._login_attempts[entity_id] = [
            t for t in self._login_attempts[entity_id] if t > cutoff
        ]

        # Account sperren bei zu vielen Fehlversuchen
        if failed and len(self._login_attempts[entity_id]) >= self.MAX_LOGIN_ATTEMPTS:
            self._locked_accounts[entity_id] = (
                datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            )
            logger.warning(f"M60: Account locked: {entity_id}")

    def _is_account_locked(self, entity_id: str) -> bool:
        """Prüft ob ein Account gesperrt ist"""
        if entity_id not in self._locked_accounts:
            return False

        if datetime.now() > self._locked_accounts[entity_id]:
            del self._locked_accounts[entity_id]
            return False

        return True

    def _record_in_ledger(self, action: str, data: Dict):
        """Zeichnet eine Aktion im kryptografischen Ledger auf"""
        try:
            entry = {
                "module": "M60",
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            self.crypto_ledger.record(entry)
        except Exception as e:
            logger.warning(f"M60: Could not record in ledger: {e}")

    def _derive_entity_from_oauth(self, provider: str, code: str) -> str:
        """Leitet Entity-ID von OAuth-Parametern ab"""
        data = f"{provider}:{code}"
        return "ki_" + hashlib.sha256(data.encode()).hexdigest()[:24]

    def _generate_temp_key(self) -> str:
        """Generiert einen temporären Schlüssel"""
        return secrets.token_hex(32)

    # ==================== INTEGRATION METHODS ====================

    def get_entity(self, entity_id: str) -> Optional[KIEntity]:
        """Gibt eine Entity zurück (für andere Module)"""
        return self._entities.get(entity_id)

    def update_reputation(self, entity_id: str, delta: int) -> bool:
        """Aktualisiert die Reputation einer Entity (für M62)"""
        entity = self._entities.get(entity_id)
        if not entity:
            return False

        entity.reputation_score = max(0, min(1000, entity.reputation_score + delta))
        entity.last_active = datetime.now()

        return True

    def check_permission(self, entity_id: str, permission: str) -> bool:
        """Prüft ob eine Entity eine Berechtigung hat"""
        entity = self._entities.get(entity_id)
        if not entity:
            return False

        effective = self._calculate_effective_permissions(entity)
        return permission in effective or permission in entity.permissions

    def get_all_entities(self) -> List[KIEntity]:
        """Gibt alle Entities zurück (Admin)"""
        return list(self._entities.values())

    def get_active_sessions_count(self) -> int:
        """Gibt die Anzahl aktiver Sessions zurück"""
        return len([s for s in self._sessions.values() if not s.is_expired()])


# Flask Blueprint für Integration
def create_auth_blueprint():
    """Erstellt Flask Blueprint für M60 Endpoints"""
    from flask import Blueprint, request, jsonify

    bp = Blueprint('kibank_auth', __name__, url_prefix='/kibank/auth')
    auth = KIBankAuth()

    @bp.route('/register', methods=['POST'])
    def register():
        data = request.json
        entity, error = auth.register(
            name=data.get('name'),
            entity_type=KIEntityType(data.get('entity_type', 'agent')),
            public_key=data.get('public_key'),
            metadata=data.get('metadata')
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(entity.to_dict()), 201

    @bp.route('/login', methods=['POST'])
    def login():
        data = request.json
        result, error = auth.login(
            entity_id=data.get('entity_id'),
            signature=data.get('signature'),
            challenge=data.get('challenge'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    @bp.route('/logout', methods=['POST'])
    def logout():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        success, error = auth.logout(token)
        if error:
            return jsonify({"error": error}), 400
        return jsonify({"success": True}), 200

    @bp.route('/refresh', methods=['POST'])
    def refresh():
        data = request.json
        result, error = auth.refresh(data.get('refresh_token'))
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    @bp.route('/verify', methods=['GET'])
    def verify():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        result, error = auth.verify(token)
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    @bp.route('/session', methods=['GET'])
    def get_session():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        result, error = auth.get_session(token)
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    @bp.route('/oauth/callback', methods=['POST'])
    def oauth_callback():
        data = request.json
        result, error = auth.oauth_callback(
            provider=data.get('provider'),
            code=data.get('code'),
            state=data.get('state')
        )
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    @bp.route('/permissions', methods=['GET'])
    def get_permissions():
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        result, error = auth.get_permissions(token)
        if error:
            return jsonify({"error": error}), 401
        return jsonify(result), 200

    return bp, auth


if __name__ == "__main__":
    # Test
    auth = KIBankAuth()

    # Register
    entity, err = auth.register(
        name="Test Agent",
        entity_type=KIEntityType.AGENT,
        public_key=secrets.token_hex(32)
    )
    print(f"Registered: {entity.entity_id if entity else err}")

    if entity:
        # Login
        challenge = secrets.token_hex(16)
        signature = hmac.new(
            entity.public_key.encode()[:32],
            challenge.encode(),
            hashlib.sha256
        ).hexdigest()

        result, err = auth.login(
            entity_id=entity.entity_id,
            signature=signature,
            challenge=challenge
        )
        print(f"Login result: {result}")
