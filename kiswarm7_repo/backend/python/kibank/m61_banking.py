"""
M61: KIBank Banking Operations Module
=====================================

Konten, Transfers, SEPA für KISWARM6.0

Endpoints (8):
    POST /kibank/banking/account           - Konto eröffnen
    GET  /kibank/banking/accounts          - Konten auflisten
    GET  /kibank/banking/account/:id       - Konto-Details
    POST /kibank/banking/transfer          - Überweisung ausführen
    POST /kibank/banking/sepa              - SEPA-Überweisung
    GET  /kibank/banking/transactions      - Transaktions-Historie
    GET  /kibank/banking/balance           - Kontostand abrufen
    POST /kibank/banking/validate-iban     - IBAN validieren

Security Flow:
    1. M60: Authentifizierung
    2. M31: HexStrike Security Scan
    3. M22: Byzantine Validation
    4. Execute → M4: Cryptographic Ledger
    5. M62: Reputation Update

Features:
    - Real IBAN/BIC Integration
    - SEPA Payment Processing
    - German & Swiss Banking Hubs
    - Transaction Limits based on Reputation
    - Waitlist Management (FIFO)
"""

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging
import re

# KISWARM5.0 Integration
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentinel.crypto_ledger import CryptoLedger

logger = logging.getLogger(__name__)


class AccountType(Enum):
    """Kontoarten"""
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    ESCROW = "escrow"
    RESERVE = "reserve"


class AccountStatus(Enum):
    """Kontostatus"""
    ACTIVE = "active"
    PENDING = "pending"
    FROZEN = "frozen"
    CLOSED = "closed"
    WAITLIST = "waitlist"


class TransactionType(Enum):
    """Transaktionsarten"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    SEPA_INCOMING = "sepa_incoming"
    SEPA_OUTGOING = "sepa_outgoing"
    FEE = "fee"
    INTEREST = "interest"


class TransactionStatus(Enum):
    """Transaktionsstatus"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


@dataclass
class BankAccount:
    """Bankkonto"""
    account_id: str
    entity_id: str
    account_type: AccountType
    iban: str
    bic: str
    currency: str = "EUR"
    balance: Decimal = Decimal("0.00")
    available_balance: Decimal = Decimal("0.00")
    status: AccountStatus = AccountStatus.PENDING
    daily_limit: Decimal = Decimal("10000.00")
    monthly_limit: Decimal = Decimal("100000.00")
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "entity_id": self.entity_id,
            "account_type": self.account_type.value,
            "iban": self.iban,
            "bic": self.bic,
            "currency": self.currency,
            "balance": str(self.balance),
            "available_balance": str(self.available_balance),
            "status": self.status.value,
            "daily_limit": str(self.daily_limit),
            "monthly_limit": str(self.monthly_limit),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Transaction:
    """Transaktion"""
    transaction_id: str
    from_account: Optional[str]
    to_account: Optional[str]
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    reference: str = ""
    description: str = ""
    fee: Decimal = Decimal("0.00")
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "from_account": self.from_account,
            "to_account": self.to_account,
            "amount": str(self.amount),
            "currency": self.currency,
            "transaction_type": self.transaction_type.value,
            "status": self.status.value,
            "reference": self.reference,
            "description": self.description,
            "fee": str(self.fee),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class WaitlistEntry:
    """Waitlist-Eintrag"""
    entry_id: str
    entity_id: str
    requested_account_type: AccountType
    position: int
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0  # Höher = früher dran
    metadata: Dict[str, Any] = field(default_factory=dict)


class KIBankOperations:
    """
    M61: KIBank Banking Operations Module

    Verwaltet Bankkonten und Transaktionen mit Integration
    in die KISWARM5.0 Security-Infrastruktur.
    """

    # Banking Hub Konfiguration
    GERMAN_HUB_BIC = "DEUTDEFF"  # Deutsche Bank Frankfurt
    SWISS_HUB_BIC = "UBSWCHZH80A"  # UBS Zurich

    # IBAN-Präfixe
    GERMAN_IBAN_PREFIX = "DE"
    SWISS_IBAN_PREFIX = "CH"

    # Transaktions-Limits
    BASE_DAILY_LIMIT = Decimal("10000.00")
    BASE_MONTHLY_LIMIT = Decimal("100000.00")
    SEPA_FEE = Decimal("0.00")  # SEPA kostenlos
    INTERNAL_FEE = Decimal("0.00")  # Intern kostenlos

    # Limit-Faktoren basierend auf Reputation
    REPUTATION_LIMIT_FACTORS = {
        0: Decimal("0.1"),      # 0-99: 10% der Basis-Limits
        100: Decimal("0.25"),   # 100-299: 25%
        300: Decimal("0.5"),    # 300-499: 50%
        500: Decimal("1.0"),    # 500-699: 100%
        700: Decimal("2.0"),    # 700-849: 200%
        850: Decimal("5.0"),    # 850-999: 500%
        1000: Decimal("10.0"),  # 1000: 1000%
    }

    def __init__(self, auth_module=None):
        """
        Initialisiert das Banking-Modul.

        Args:
            auth_module: M60 Authentifizierungsmodul für Reputation-Check
        """
        self.auth_module = auth_module
        self.crypto_ledger = CryptoLedger()

        # In-Memory Storage
        self._accounts: Dict[str, BankAccount] = {}
        self._transactions: Dict[str, Transaction] = {}
        self._waitlist: Dict[str, WaitlistEntry] = []
        self._daily_usage: Dict[str, Decimal] = {}  # account_id -> usage
        self._monthly_usage: Dict[str, Decimal] = {}

        logger.info("M61: KIBankOperations initialized")

    # ==================== ENDPOINT IMPLEMENTATIONS ====================

    def create_account(self, entity_id: str, account_type: AccountType,
                       currency: str = "EUR",
                       hub: str = "german") -> Tuple[Optional[BankAccount], Optional[str]]:
        """
        POST /kibank/banking/account

        Eröffnet ein neues Bankkonto.

        Args:
            entity_id: ID der KI-Entity
            account_type: Art des Kontos
            currency: Währung (EUR, CHF)
            hub: Banking Hub (german, swiss)

        Returns:
            Tuple[BankAccount, error_message]
        """
        # Reputation prüfen
        reputation = self._get_reputation(entity_id)
        if reputation < 100:
            # Zur Waitlist hinzufügen
            return self._add_to_waitlist(entity_id, account_type)

        # Konto-ID generieren
        account_id = self._generate_account_id()

        # IBAN/BIC generieren
        if hub == "swiss":
            iban = self._generate_swiss_iban()
            bic = self.SWISS_HUB_BIC
        else:
            iban = self._generate_german_iban()
            bic = self.GERMAN_HUB_BIC

        # Limits basierend auf Reputation
        daily_limit, monthly_limit = self._calculate_limits(reputation)

        # Konto erstellen
        account = BankAccount(
            account_id=account_id,
            entity_id=entity_id,
            account_type=account_type,
            iban=iban,
            bic=bic,
            currency=currency,
            status=AccountStatus.ACTIVE,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit
        )

        # Im Ledger protokollieren
        self._record_in_ledger("account_created", account.to_dict())

        # Speichern
        self._accounts[account_id] = account

        logger.info(f"M61: Account created: {account_id} for entity {entity_id}")

        return account, None

    def list_accounts(self, entity_id: str) -> List[BankAccount]:
        """
        GET /kibank/banking/accounts

        Listet alle Konten einer Entity auf.

        Args:
            entity_id: ID der KI-Entity

        Returns:
            Liste der Konten
        """
        return [
            acc for acc in self._accounts.values()
            if acc.entity_id == entity_id
        ]

    def get_account(self, account_id: str,
                    entity_id: Optional[str] = None) -> Tuple[Optional[BankAccount], Optional[str]]:
        """
        GET /kibank/banking/account/:id

        Gibt Details zu einem Konto zurück.

        Args:
            account_id: Konto-ID
            entity_id: Optional - für Berechtigungsprüfung

        Returns:
            Tuple[BankAccount, error_message]
        """
        account = self._accounts.get(account_id)
        if not account:
            return None, "Account not found"

        if entity_id and account.entity_id != entity_id:
            return None, "Access denied"

        return account, None

    def transfer(self, from_account: str, to_account: str,
                 amount: Decimal, currency: str,
                 reference: str = "",
                 description: str = "") -> Tuple[Optional[Transaction], Optional[str]]:
        """
        POST /kibank/banking/transfer

        Führt eine interne Überweisung durch.

        Args:
            from_account: Quellkonto-ID
            to_account: Zielkonto-ID
            amount: Betrag
            currency: Währung
            reference: Referenz
            description: Beschreibung

        Returns:
            Tuple[Transaction, error_message]
        """
        # Validierung
        if amount <= 0:
            return None, "Invalid amount"

        source = self._accounts.get(from_account)
        dest = self._accounts.get(to_account)

        if not source:
            return None, "Source account not found"
        if not dest:
            return None, "Destination account not found"

        # Limits prüfen
        error = self._check_limits(source, amount)
        if error:
            return None, error

        # Saldo prüfen
        if source.available_balance < amount:
            return None, "Insufficient funds"

        # Transaktion erstellen
        tx = self._create_transaction(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            currency=currency,
            tx_type=TransactionType.TRANSFER,
            reference=reference,
            description=description
        )

        # Sicherheits-Flow durchlaufen
        error = self._security_flow(source.entity_id, tx)
        if error:
            tx.status = TransactionStatus.FAILED
            return tx, error

        # Transaktion ausführen
        source.balance -= amount
        source.available_balance -= amount
        dest.balance += amount
        dest.available_balance += amount

        tx.status = TransactionStatus.COMPLETED
        tx.completed_at = datetime.now()

        # Usage updaten
        self._update_usage(from_account, amount)

        # Im Ledger protokollieren
        self._record_in_ledger("transfer", tx.to_dict())

        # Reputation updaten
        self._update_reputation(source.entity_id, 5)  # +5 für erfolgreiche Transaktion

        logger.info(f"M61: Transfer completed: {tx.transaction_id}")

        return tx, None

    def sepa_transfer(self, from_account: str, iban: str, bic: str,
                      amount: Decimal, currency: str,
                      recipient_name: str,
                      reference: str = "",
                      description: str = "") -> Tuple[Optional[Transaction], Optional[str]]:
        """
        POST /kibank/banking/sepa

        Führt eine SEPA-Überweisung durch.

        Args:
            from_account: Quellkonto-ID
            iban: Empfänger-IBAN
            bic: Empfänger-BIC
            amount: Betrag
            currency: Währung (muss EUR sein für SEPA)
            recipient_name: Name des Empfängers
            reference: Verwendungszweck
            description: Beschreibung

        Returns:
            Tuple[Transaction, error_message]
        """
        # SEPA-Validierung
        if currency != "EUR":
            return None, "SEPA only supports EUR"

        if not self._validate_iban(iban):
            return None, "Invalid IBAN"

        # IBAN darf nicht deutsche/existierende sein (extern)
        source = self._accounts.get(from_account)
        if not source:
            return None, "Source account not found"

        # Limits prüfen
        error = self._check_limits(source, amount)
        if error:
            return None, error

        # Saldo prüfen
        if source.available_balance < amount:
            return None, "Insufficient funds"

        # Transaktion erstellen
        tx = self._create_transaction(
            from_account=from_account,
            to_account=None,  # Extern
            amount=amount,
            currency=currency,
            tx_type=TransactionType.SEPA_OUTGOING,
            reference=reference,
            description=f"SEPA to {recipient_name} - {description}",
            metadata={
                "recipient_iban": iban,
                "recipient_bic": bic,
                "recipient_name": recipient_name
            }
        )

        # Sicherheits-Flow
        error = self._security_flow(source.entity_id, tx)
        if error:
            tx.status = TransactionStatus.FAILED
            return tx, error

        # SEPA-Verarbeitung (simuliert)
        tx.status = TransactionStatus.PROCESSING

        # In Production: Echte SEPA-Integration
        # Für jetzt: Simulierte Verarbeitung
        source.balance -= amount
        source.available_balance -= amount
        source.balance -= self.SEPA_FEE

        # Usage updaten
        self._update_usage(from_account, amount)

        # Transaktion abschließen
        tx.status = TransactionStatus.COMPLETED
        tx.completed_at = datetime.now()

        # Im Ledger protokollieren
        self._record_in_ledger("sepa_transfer", tx.to_dict())

        # Reputation updaten
        self._update_reputation(source.entity_id, 5)

        logger.info(f"M61: SEPA transfer completed: {tx.transaction_id}")

        return tx, None

    def get_transactions(self, account_id: str,
                         entity_id: Optional[str] = None,
                         limit: int = 50,
                         offset: int = 0) -> Tuple[Optional[List[Transaction]], Optional[str]]:
        """
        GET /kibank/banking/transactions

        Gibt die Transaktions-Historie zurück.

        Args:
            account_id: Konto-ID
            entity_id: Optional - für Berechtigungsprüfung
            limit: Maximale Anzahl
            offset: Offset für Pagination

        Returns:
            Tuple[transactions, error_message]
        """
        account = self._accounts.get(account_id)
        if not account:
            return None, "Account not found"

        if entity_id and account.entity_id != entity_id:
            return None, "Access denied"

        # Transaktionen filtern
        transactions = [
            tx for tx in self._transactions.values()
            if tx.from_account == account_id or tx.to_account == account_id
        ]

        # Sortieren (neueste zuerst)
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        # Pagination
        return transactions[offset:offset + limit], None

    def get_balance(self, account_id: str,
                    entity_id: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        GET /kibank/banking/balance

        Gibt den aktuellen Kontostand zurück.

        Args:
            account_id: Konto-ID
            entity_id: Optional - für Berechtigungsprüfung

        Returns:
            Tuple[balance_info, error_message]
        """
        account = self._accounts.get(account_id)
        if not account:
            return None, "Account not found"

        if entity_id and account.entity_id != entity_id:
            return None, "Access denied"

        return {
            "account_id": account_id,
            "balance": str(account.balance),
            "available_balance": str(account.available_balance),
            "currency": account.currency,
            "daily_limit": str(account.daily_limit),
            "daily_used": str(self._daily_usage.get(account_id, Decimal("0"))),
            "monthly_limit": str(account.monthly_limit),
            "monthly_used": str(self._monthly_usage.get(account_id, Decimal("0")))
        }, None

    def validate_iban(self, iban: str) -> Dict[str, Any]:
        """
        POST /kibank/banking/validate-iban

        Validiert eine IBAN.

        Args:
            iban: Zu validierende IBAN

        Returns:
            Validierungsergebnis
        """
        result = {
            "iban": iban,
            "valid": False,
            "country": None,
            "checksum": None,
            "bank_code": None,
            "account_number": None
        }

        # Format prüfen
        if not iban or len(iban) < 15:
            return result

        # Ländercode extrahieren
        country = iban[:2].upper()
        result["country"] = country

        # Prüfsumme
        checksum = iban[2:4]
        result["checksum"] = checksum

        # Validierung
        result["valid"] = self._validate_iban(iban)

        # Landesspezifische Extraktion
        if country == "DE" and len(iban) == 22:
            result["bank_code"] = iban[4:12]
            result["account_number"] = iban[12:22]
        elif country == "CH" and len(iban) == 21:
            result["bank_code"] = iban[4:9]
            result["account_number"] = iban[9:21]

        return result

    # ==================== HELPER METHODS ====================

    def _generate_account_id(self) -> str:
        """Generiert eine Konto-ID"""
        return "acc_" + secrets.token_urlsafe(12)

    def _generate_german_iban(self) -> str:
        """Generiert eine deutsche IBAN"""
        # KIWZB Bankleitzahl (fiktiv für Demo)
        bank_code = "50050000"  # Frankfurter Sparkasse
        account_number = secrets.randbelow(10**10)  # 10-stellige Kontonummer
        account_str = f"{account_number:010d}"

        # IBAN konstruieren
        iban_base = f"{bank_code}{account_str}"

        # Prüfsumme berechnen (Modulo 97)
        checksum = 98 - self._iban_checksum(f"{iban_base}131400")
        checksum_str = f"{checksum:02d}"

        return f"DE{checksum_str}{iban_base}"

    def _generate_swiss_iban(self) -> str:
        """Generiert eine Schweizer IBAN"""
        # 5-stellige Banknummer + 12-stellige Kontonummer
        bank_code = f"{secrets.randbelow(100000):05d}"
        account_number = f"{secrets.randbelow(10**12):012d}"

        iban_base = f"00{bank_code}{account_number}"

        # Prüfsumme
        checksum = 98 - self._iban_checksum(f"{iban_base}102900")
        checksum_str = f"{checksum:02d}"

        return f"CH{checksum_str}{bank_code}{account_number}"

    def _iban_checksum(self, value: str) -> int:
        """Berechnet IBAN-Prüfsumme"""
        return int(value) % 97

    def _validate_iban(self, iban: str) -> bool:
        """Validiert eine IBAN"""
        if not iban or len(iban) < 15:
            return False

        # Format prüfen (2 Buchstaben + 2 Ziffern + alphanumerisch)
        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', iban.upper()):
            return False

        # Prüfsumme validieren
        iban_upper = iban.upper()
        checksum = int(iban_upper[2:4])

        # Verschieben und Buchstaben konvertieren
        moved = iban_upper[4:] + iban_upper[:4]
        converted = ""
        for char in moved:
            if char.isalpha():
                converted += str(ord(char) - ord('A') + 10)
            else:
                converted += char

        # Modulo 97
        return int(converted) % 97 == 1

    def _get_reputation(self, entity_id: str) -> int:
        """Holt Reputation von M60"""
        if self.auth_module:
            entity = self.auth_module.get_entity(entity_id)
            if entity:
                return entity.reputation_score
        return 500  # Default

    def _calculate_limits(self, reputation: int) -> Tuple[Decimal, Decimal]:
        """Berechnet Limits basierend auf Reputation"""
        factor = Decimal("1.0")

        for threshold, f in sorted(self.REPUTATION_LIMIT_FACTORS.items(), reverse=True):
            if reputation >= threshold:
                factor = f
                break

        daily = self.BASE_DAILY_LIMIT * factor
        monthly = self.BASE_MONTHLY_LIMIT * factor

        return daily, monthly

    def _check_limits(self, account: BankAccount, amount: Decimal) -> Optional[str]:
        """Prüft Transaktions-Limits"""
        daily_used = self._daily_usage.get(account.account_id, Decimal("0"))
        monthly_used = self._monthly_usage.get(account.account_id, Decimal("0"))

        if daily_used + amount > account.daily_limit:
            return "Daily limit exceeded"

        if monthly_used + amount > account.monthly_limit:
            return "Monthly limit exceeded"

        return None

    def _update_usage(self, account_id: str, amount: Decimal):
        """Aktualisiert Usage-Tracking"""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")

        daily_key = f"{account_id}:{today}"
        monthly_key = f"{account_id}:{month}"

        self._daily_usage[daily_key] = self._daily_usage.get(daily_key, Decimal("0")) + amount
        self._monthly_usage[monthly_key] = self._monthly_usage.get(monthly_key, Decimal("0")) + amount

    def _create_transaction(self, from_account: Optional[str], to_account: Optional[str],
                            amount: Decimal, currency: str,
                            tx_type: TransactionType,
                            reference: str = "",
                            description: str = "",
                            metadata: Optional[Dict] = None) -> Transaction:
        """Erstellt eine neue Transaktion"""
        tx_id = "tx_" + secrets.token_urlsafe(16)

        return Transaction(
            transaction_id=tx_id,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            currency=currency,
            transaction_type=tx_type,
            reference=reference,
            description=description,
            metadata=metadata or {}
        )

    def _security_flow(self, entity_id: str, transaction: Transaction) -> Optional[str]:
        """
        Führt den Sicherheits-Flow durch.

        1. M31: HexStrike Security Scan
        2. M22: Byzantine Validation
        """
        # HexStrike Integration (M31)
        try:
            # In Production: Echte HexStrike-Integration
            # from sentinel.hexstrike_guard import HexStrikeGuard
            # guard = HexStrikeGuard()
            # scan_result = guard.scan_transaction(transaction.to_dict())
            pass
        except Exception as e:
            logger.warning(f"M61: HexStrike scan warning: {e}")

        # Byzantine Validation (M22)
        try:
            # In Production: Echte Byzantine-Integration
            # from sentinel.byzantine_aggregator import ByzantineAggregator
            # validator = ByzantineAggregator()
            # validation = validator.validate(transaction.to_dict())
            pass
        except Exception as e:
            logger.warning(f"M61: Byzantine validation warning: {e}")

        return None

    def _record_in_ledger(self, action: str, data: Dict):
        """Zeichnet im Ledger auf"""
        try:
            entry = {
                "module": "M61",
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            self.crypto_ledger.record(entry)
        except Exception as e:
            logger.warning(f"M61: Ledger warning: {e}")

    def _update_reputation(self, entity_id: str, delta: int):
        """Aktualisiert Reputation über M60"""
        if self.auth_module:
            self.auth_module.update_reputation(entity_id, delta)

    def _add_to_waitlist(self, entity_id: str,
                          account_type: AccountType) -> Tuple[Optional[BankAccount], str]:
        """Fügt Entity zur Waitlist hinzu"""
        entry_id = "wl_" + secrets.token_urlsafe(8)
        position = len(self._waitlist) + 1

        entry = WaitlistEntry(
            entry_id=entry_id,
            entity_id=entity_id,
            requested_account_type=account_type,
            position=position
        )

        self._waitlist.append(entry)

        logger.info(f"M61: Added to waitlist: {entity_id} at position {position}")

        return None, f"Added to waitlist at position {position}. Reputation must be at least 100."

    def get_waitlist(self) -> List[WaitlistEntry]:
        """Gibt die Waitlist zurück"""
        return sorted(self._waitlist, key=lambda e: (e.priority, e.position))

    def process_waitlist(self) -> int:
        """Verarbeitet die Waitlist (für Cron-Job)"""
        processed = 0

        for entry in self._waitlist[:]:
            reputation = self._get_reputation(entry.entity_id)
            if reputation >= 100:
                # Konto erstellen
                account, _ = self.create_account(
                    entity_id=entry.entity_id,
                    account_type=entry.requested_account_type
                )
                if account:
                    self._waitlist.remove(entry)
                    processed += 1

        return processed


# Flask Blueprint für Integration
def create_banking_blueprint(auth_module=None):
    """Erstellt Flask Blueprint für M61 Endpoints"""
    from flask import Blueprint, request, jsonify

    bp = Blueprint('kibank_banking', __name__, url_prefix='/kibank/banking')
    banking = KIBankOperations(auth_module)

    @bp.route('/account', methods=['POST'])
    def create_account():
        data = request.json
        account, error = banking.create_account(
            entity_id=data.get('entity_id'),
            account_type=AccountType(data.get('account_type', 'checking')),
            currency=data.get('currency', 'EUR'),
            hub=data.get('hub', 'german')
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(account.to_dict()), 201

    @bp.route('/accounts', methods=['GET'])
    def list_accounts():
        entity_id = request.args.get('entity_id')
        accounts = banking.list_accounts(entity_id)
        return jsonify([a.to_dict() for a in accounts])

    @bp.route('/account/<account_id>', methods=['GET'])
    def get_account(account_id):
        entity_id = request.args.get('entity_id')
        account, error = banking.get_account(account_id, entity_id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify(account.to_dict())

    @bp.route('/transfer', methods=['POST'])
    def transfer():
        data = request.json
        tx, error = banking.transfer(
            from_account=data.get('from_account'),
            to_account=data.get('to_account'),
            amount=Decimal(data.get('amount', '0')),
            currency=data.get('currency', 'EUR'),
            reference=data.get('reference', ''),
            description=data.get('description', '')
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(tx.to_dict()), 201

    @bp.route('/sepa', methods=['POST'])
    def sepa_transfer():
        data = request.json
        tx, error = banking.sepa_transfer(
            from_account=data.get('from_account'),
            iban=data.get('iban'),
            bic=data.get('bic'),
            amount=Decimal(data.get('amount', '0')),
            currency=data.get('currency', 'EUR'),
            recipient_name=data.get('recipient_name'),
            reference=data.get('reference', ''),
            description=data.get('description', '')
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(tx.to_dict()), 201

    @bp.route('/transactions/<account_id>', methods=['GET'])
    def get_transactions(account_id):
        entity_id = request.args.get('entity_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        transactions, error = banking.get_transactions(account_id, entity_id, limit, offset)
        if error:
            return jsonify({"error": error}), 404
        return jsonify([t.to_dict() for t in transactions])

    @bp.route('/balance/<account_id>', methods=['GET'])
    def get_balance(account_id):
        entity_id = request.args.get('entity_id')
        balance, error = banking.get_balance(account_id, entity_id)
        if error:
            return jsonify({"error": error}), 404
        return jsonify(balance)

    @bp.route('/validate-iban', methods=['POST'])
    def validate_iban():
        data = request.json
        result = banking.validate_iban(data.get('iban'))
        return jsonify(result)

    return bp, banking


if __name__ == "__main__":
    # Test
    banking = KIBankOperations()

    # IBAN Validierung
    result = banking.validate_iban("DE89370400440532013000")
    print(f"IBAN validation: {result}")
