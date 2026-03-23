"""
M62: KIBank Investment & Reputation Module
==========================================

Portfolio, Reputation (0-1000), Trading Limits für KISWARM6.0

Endpoints (8):
    GET  /kibank/investment/portfolio          - Portfolio abrufen
    POST /kibank/investment/invest             - Investition tätigen
    POST /kibank/investment/divest             - Desinvestition
    GET  /kibank/investment/performance        - Performance-Metriken
    GET  /kibank/reputation/:entity_id         - Reputation abrufen
    POST /kibank/reputation/update             - Reputation aktualisieren
    GET  /kibank/reputation/history/:entity_id - Reputation-Historie
    GET  /kibank/trading-limits/:entity_id     - Trading-Limits abrufen

Reputation Scoring:
    Base: 500
    + Erfolgreiche Transaktionen: +5
    + Pünktliche Zahlungen: +10
    + Investment Growth: +1 pro 1%
    + KI-Proof verified: +100
    - Fehlgeschlagene Transaktionen: -10
    - Verspätete Zahlungen: -25
    Limit: 0-1000

Trading Limits (basierend auf Reputation):
    0-99:    10% der Basis-Limits
    100-299: 25%
    300-499: 50%
    500-699: 100%
    700-849: 200%
    850-999: 500%
    1000:    1000%

Investment Types:
    - TCS Green Safe House
    - KI-Bonds
    - Carbon Credits
    - Technology Funds
    - Liquidity Pool
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

# KISWARM5.0 Integration
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentinel.crypto_ledger import CryptoLedger

logger = logging.getLogger(__name__)


class InvestmentType(Enum):
    """Investitionsarten"""
    TCS_GREEN_SAFE_HOUSE = "tcs_green_safe_house"
    KI_BONDS = "ki_bonds"
    CARBON_CREDITS = "carbon_credits"
    TECHNOLOGY_FUND = "technology_fund"
    LIQUIDITY_POOL = "liquidity_pool"


class InvestmentStatus(Enum):
    """Investitionsstatus"""
    ACTIVE = "active"
    PENDING = "pending"
    MATURED = "matured"
    WITHDRAWN = "withdrawn"
    FAILED = "failed"


class ReputationEventType(Enum):
    """Reputation-Event-Typen"""
    TRANSACTION_SUCCESS = "transaction_success"
    TRANSACTION_FAILED = "transaction_failed"
    PAYMENT_ON_TIME = "payment_on_time"
    PAYMENT_LATE = "payment_late"
    INVESTMENT_GROWTH = "investment_growth"
    INVESTMENT_LOSS = "investment_loss"
    KI_PROOF_VERIFIED = "ki_proof_verified"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class Investment:
    """Investition"""
    investment_id: str
    entity_id: str
    investment_type: InvestmentType
    amount: Decimal
    currency: str
    status: InvestmentStatus = InvestmentStatus.ACTIVE
    current_value: Decimal = Decimal("0.00")
    yield_rate: Decimal = Decimal("0.00")  # Jahresrendite in %
    maturity_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_valuation: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investment_id": self.investment_id,
            "entity_id": self.entity_id,
            "investment_type": self.investment_type.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "status": self.status.value,
            "current_value": str(self.current_value),
            "yield_rate": str(self.yield_rate),
            "maturity_date": self.maturity_date.isoformat() if self.maturity_date else None,
            "created_at": self.created_at.isoformat(),
            "last_valuation": self.last_valuation.isoformat(),
            "roi": str(self._calculate_roi())
        }

    def _calculate_roi(self) -> Decimal:
        """Berechnet ROI"""
        if self.amount <= 0:
            return Decimal("0.00")
        return ((self.current_value - self.amount) / self.amount) * 100


@dataclass
class Portfolio:
    """Investment-Portfolio"""
    entity_id: str
    investments: List[Investment] = field(default_factory=list)
    total_value: Decimal = Decimal("0.00")
    total_invested: Decimal = Decimal("0.00")
    total_yield: Decimal = Decimal("0.00")
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "investments": [i.to_dict() for i in self.investments],
            "total_value": str(self.total_value),
            "total_invested": str(self.total_invested),
            "total_yield": str(self.total_yield),
            "roi_percentage": str(self._calculate_roi()),
            "last_updated": self.last_updated.isoformat()
        }

    def _calculate_roi(self) -> Decimal:
        if self.total_invested <= 0:
            return Decimal("0.00")
        return ((self.total_value - self.total_invested) / self.total_invested) * 100


@dataclass
class ReputationEvent:
    """Reputation-Event"""
    event_id: str
    entity_id: str
    event_type: ReputationEventType
    delta: int
    previous_score: int
    new_score: int
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "entity_id": self.entity_id,
            "event_type": self.event_type.value,
            "delta": self.delta,
            "previous_score": self.previous_score,
            "new_score": self.new_score,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TradingLimits:
    """Trading-Limits"""
    entity_id: str
    reputation_score: int
    max_single_transaction: Decimal
    daily_limit: Decimal
    monthly_limit: Decimal
    max_open_investments: int
    allowed_investment_types: List[InvestmentType]
    leverage_allowed: bool
    margin_trading: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "reputation_score": self.reputation_score,
            "max_single_transaction": str(self.max_single_transaction),
            "daily_limit": str(self.daily_limit),
            "monthly_limit": str(self.monthly_limit),
            "max_open_investments": self.max_open_investments,
            "allowed_investment_types": [t.value for t in self.allowed_investment_types],
            "leverage_allowed": self.leverage_allowed,
            "margin_trading": self.margin_trading
        }


class KIBankInvestment:
    """
    M62: KIBank Investment & Reputation Module

    Verwaltet Investitionen und Reputation mit Integration
    in die KISWARM5.0 Security-Infrastruktur.
    """

    # Reputation-Konfiguration
    BASE_REPUTATION = 500
    MIN_REPUTATION = 0
    MAX_REPUTATION = 1000

    # Reputation-Deltas
    REPUTATION_DELTAS = {
        ReputationEventType.TRANSACTION_SUCCESS: 5,
        ReputationEventType.TRANSACTION_FAILED: -10,
        ReputationEventType.PAYMENT_ON_TIME: 10,
        ReputationEventType.PAYMENT_LATE: -25,
        ReputationEventType.INVESTMENT_GROWTH: 1,  # pro 1% Growth
        ReputationEventType.INVESTMENT_LOSS: -1,   # pro 1% Loss
        ReputationEventType.KI_PROOF_VERIFIED: 100,
        ReputationEventType.SECURITY_VIOLATION: -100,
        ReputationEventType.COMPLIANCE_VIOLATION: -50
    }

    # Investment-Konfiguration
    INVESTMENT_CONFIG = {
        InvestmentType.TCS_GREEN_SAFE_HOUSE: {
            "min_amount": Decimal("1000.00"),
            "yield_rate": Decimal("8.5"),  # 8.5% p.a.
            "maturity_months": 36,
            "risk_level": "low"
        },
        InvestmentType.KI_BONDS: {
            "min_amount": Decimal("500.00"),
            "yield_rate": Decimal("5.0"),
            "maturity_months": 12,
            "risk_level": "low"
        },
        InvestmentType.CARBON_CREDITS: {
            "min_amount": Decimal("100.00"),
            "yield_rate": Decimal("6.0"),
            "maturity_months": 24,
            "risk_level": "medium"
        },
        InvestmentType.TECHNOLOGY_FUND: {
            "min_amount": Decimal("250.00"),
            "yield_rate": Decimal("12.0"),
            "maturity_months": 60,
            "risk_level": "high"
        },
        InvestmentType.LIQUIDITY_POOL: {
            "min_amount": Decimal("100.00"),
            "yield_rate": Decimal("4.0"),
            "maturity_months": 0,  # Flexible
            "risk_level": "low"
        }
    }

    # Trading-Limits basierend auf Reputation
    TRADING_LIMITS_BY_REPUTATION = {
        0: {
            "max_single": Decimal("1000.00"),
            "daily": Decimal("1000.00"),
            "monthly": Decimal("10000.00"),
            "max_investments": 1,
            "types": [InvestmentType.LIQUIDITY_POOL],
            "leverage": False,
            "margin": False
        },
        100: {
            "max_single": Decimal("5000.00"),
            "daily": Decimal("5000.00"),
            "monthly": Decimal("50000.00"),
            "max_investments": 2,
            "types": [InvestmentType.LIQUIDITY_POOL, InvestmentType.KI_BONDS],
            "leverage": False,
            "margin": False
        },
        300: {
            "max_single": Decimal("10000.00"),
            "daily": Decimal("10000.00"),
            "monthly": Decimal("100000.00"),
            "max_investments": 5,
            "types": [InvestmentType.LIQUIDITY_POOL, InvestmentType.KI_BONDS,
                     InvestmentType.CARBON_CREDITS],
            "leverage": False,
            "margin": False
        },
        500: {
            "max_single": Decimal("50000.00"),
            "daily": Decimal("100000.00"),
            "monthly": Decimal("500000.00"),
            "max_investments": 10,
            "types": list(InvestmentType),
            "leverage": True,
            "margin": False
        },
        700: {
            "max_single": Decimal("100000.00"),
            "daily": Decimal("200000.00"),
            "monthly": Decimal("1000000.00"),
            "max_investments": 20,
            "types": list(InvestmentType),
            "leverage": True,
            "margin": True
        },
        850: {
            "max_single": Decimal("500000.00"),
            "daily": Decimal("1000000.00"),
            "monthly": Decimal("5000000.00"),
            "max_investments": 50,
            "types": list(InvestmentType),
            "leverage": True,
            "margin": True
        },
        1000: {
            "max_single": Decimal("1000000.00"),
            "daily": Decimal("5000000.00"),
            "monthly": Decimal("25000000.00"),
            "max_investments": 100,
            "types": list(InvestmentType),
            "leverage": True,
            "margin": True
        }
    }

    def __init__(self, auth_module=None, banking_module=None):
        """
        Initialisiert das Investment-Modul.

        Args:
            auth_module: M60 Authentifizierungsmodul
            banking_module: M61 Banking-Modul
        """
        self.auth_module = auth_module
        self.banking_module = banking_module
        self.crypto_ledger = CryptoLedger()

        # In-Memory Storage
        self._reputation_scores: Dict[str, int] = {}  # entity_id -> score
        self._reputation_history: Dict[str, List[ReputationEvent]] = {}
        self._investments: Dict[str, Investment] = {}
        self._portfolios: Dict[str, Portfolio] = {}

        logger.info("M62: KIBankInvestment initialized")

    # ==================== PORTFOLIO ENDPOINTS ====================

    def get_portfolio(self, entity_id: str) -> Portfolio:
        """
        GET /kibank/investment/portfolio

        Gibt das Investment-Portfolio zurück.

        Args:
            entity_id: ID der KI-Entity

        Returns:
            Portfolio
        """
        if entity_id not in self._portfolios:
            self._portfolios[entity_id] = Portfolio(entity_id=entity_id)

        portfolio = self._portfolios[entity_id]
        portfolio.investments = [
            i for i in self._investments.values()
            if i.entity_id == entity_id and i.status == InvestmentStatus.ACTIVE
        ]

        self._update_portfolio_values(portfolio)

        return portfolio

    def invest(self, entity_id: str, investment_type: InvestmentType,
               amount: Decimal, currency: str = "EUR",
               from_account: Optional[str] = None) -> Tuple[Optional[Investment], Optional[str]]:
        """
        POST /kibank/investment/invest

        Tätigt eine Investition.

        Args:
            entity_id: ID der KI-Entity
            investment_type: Art der Investition
            amount: Betrag
            currency: Währung
            from_account: Quellkonto (optional)

        Returns:
            Tuple[Investment, error_message]
        """
        # Validierung
        if amount <= 0:
            return None, "Invalid amount"

        # Trading-Limits prüfen
        limits = self.get_trading_limits(entity_id)

        if amount > limits.max_single_transaction:
            return None, f"Amount exceeds single transaction limit ({limits.max_single_transaction})"

        if investment_type not in limits.allowed_investment_types:
            return None, "Investment type not allowed for your reputation level"

        # Mindestbetrag prüfen
        config = self.INVESTMENT_CONFIG[investment_type]
        if amount < config["min_amount"]:
            return None, f"Minimum amount is {config['min_amount']}"

        # Anzahl aktiver Investitionen prüfen
        portfolio = self.get_portfolio(entity_id)
        if len(portfolio.investments) >= limits.max_open_investments:
            return None, "Maximum number of investments reached"

        # Investment erstellen
        investment_id = "inv_" + secrets.token_urlsafe(12)

        maturity_date = None
        if config["maturity_months"] > 0:
            maturity_date = datetime.now() + timedelta(days=config["maturity_months"] * 30)

        investment = Investment(
            investment_id=investment_id,
            entity_id=entity_id,
            investment_type=investment_type,
            amount=amount,
            currency=currency,
            current_value=amount,  # Startwert
            yield_rate=config["yield_rate"],
            maturity_date=maturity_date,
            status=InvestmentStatus.PENDING
        )

        # Im Ledger protokollieren
        self._record_in_ledger("investment_created", investment.to_dict())

        # Speichern
        self._investments[investment_id] = investment

        # Bank-Transfer falls Konto angegeben
        if from_account and self.banking_module:
            # In Production: Transfer vom Konto zur Investment-Position
            pass

        # Status aktualisieren
        investment.status = InvestmentStatus.ACTIVE

        logger.info(f"M62: Investment created: {investment_id}")

        return investment, None

    def divest(self, investment_id: str, entity_id: str,
               partial_amount: Optional[Decimal] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        POST /kibank/investment/divest

        Löst eine Investition auf.

        Args:
            investment_id: ID der Investition
            entity_id: ID der KI-Entity
            partial_amount: Optional - Teilauflösung

        Returns:
            Tuple[result, error_message]
        """
        investment = self._investments.get(investment_id)
        if not investment:
            return None, "Investment not found"

        if investment.entity_id != entity_id:
            return None, "Access denied"

        if investment.status != InvestmentStatus.ACTIVE:
            return None, "Investment not active"

        # Portfolio-Update
        portfolio = self.get_portfolio(entity_id)

        if partial_amount and partial_amount < investment.current_value:
            # Teilauflösung
            ratio = partial_amount / investment.current_value
            investment.current_value -= partial_amount
            investment.amount -= (investment.amount * ratio)

            # ROI-Update
            roi_percentage = float(investment._calculate_roi())
            if roi_percentage > 0:
                self._update_reputation(entity_id, ReputationEventType.INVESTMENT_GROWTH,
                                       int(roi_percentage))

            return {
                "investment_id": investment_id,
                "divested_amount": str(partial_amount),
                "remaining_value": str(investment.current_value),
                "status": "partial_divestment"
            }, None
        else:
            # Vollständige Auflösung
            divest_value = investment.current_value

            # ROI berechnen und Reputation updaten
            roi_percentage = float(investment._calculate_roi())
            if roi_percentage > 0:
                self._update_reputation(entity_id, ReputationEventType.INVESTMENT_GROWTH,
                                       int(roi_percentage))
            elif roi_percentage < 0:
                self._update_reputation(entity_id, ReputationEventType.INVESTMENT_LOSS,
                                       int(abs(roi_percentage)))

            investment.status = InvestmentStatus.WITHDRAWN
            investment.current_value = Decimal("0.00")

            self._record_in_ledger("investment_divested", investment.to_dict())

            return {
                "investment_id": investment_id,
                "divested_amount": str(divest_value),
                "roi": str(roi_percentage) + "%",
                "status": "fully_divested"
            }, None

    def get_performance(self, entity_id: str) -> Dict[str, Any]:
        """
        GET /kibank/investment/performance

        Gibt Performance-Metriken zurück.

        Args:
            entity_id: ID der KI-Entity

        Returns:
            Performance-Metriken
        """
        portfolio = self.get_portfolio(entity_id)

        # Berechnungen
        total_roi = portfolio._calculate_roi()
        total_yield = Decimal("0.00")

        type_performance = {}
        for inv in portfolio.investments:
            inv_type = inv.investment_type.value
            if inv_type not in type_performance:
                type_performance[inv_type] = {
                    "count": 0,
                    "total_invested": Decimal("0.00"),
                    "total_value": Decimal("0.00"),
                    "yield": Decimal("0.00")
                }
            type_performance[inv_type]["count"] += 1
            type_performance[inv_type]["total_invested"] += inv.amount
            type_performance[inv_type]["total_value"] += inv.current_value
            total_yield += (inv.current_value * inv.yield_rate / 100)

        return {
            "entity_id": entity_id,
            "total_invested": str(portfolio.total_invested),
            "total_value": str(portfolio.total_value),
            "total_roi": str(total_roi) + "%",
            "annual_yield": str(total_yield),
            "investment_count": len(portfolio.investments),
            "by_type": {
                k: {
                    **v,
                    "total_invested": str(v["total_invested"]),
                    "total_value": str(v["total_value"]),
                    "yield": str(v["yield"])
                }
                for k, v in type_performance.items()
            }
        }

    # ==================== REPUTATION ENDPOINTS ====================

    def get_reputation(self, entity_id: str) -> Dict[str, Any]:
        """
        GET /kibank/reputation/:entity_id

        Gibt die Reputation einer Entity zurück.

        Args:
            entity_id: ID der KI-Entity

        Returns:
            Reputation-Informationen
        """
        score = self._reputation_scores.get(entity_id, self.BASE_REPUTATION)

        # Level bestimmen
        if score >= 900:
            level = "Platinum"
            tier = 5
        elif score >= 700:
            level = "Gold"
            tier = 4
        elif score >= 500:
            level = "Silver"
            tier = 3
        elif score >= 300:
            level = "Bronze"
            tier = 2
        else:
            level = "Basic"
            tier = 1

        # Progress zum nächsten Level
        if tier < 5:
            next_threshold = [0, 300, 500, 700, 900][tier]
            current_threshold = [0, 0, 300, 500, 700][tier]
            progress = ((score - current_threshold) / (next_threshold - current_threshold)) * 100
        else:
            progress = 100

        return {
            "entity_id": entity_id,
            "score": score,
            "level": level,
            "tier": tier,
            "progress_to_next": round(progress, 1),
            "trust_score": self._calculate_trust_score(score),
            "risk_rating": self._calculate_risk_rating(score)
        }

    def update_reputation(self, entity_id: str,
                          event_type: ReputationEventType,
                          value: int = 1,
                          description: str = "") -> Dict[str, Any]:
        """
        POST /kibank/reputation/update

        Aktualisiert die Reputation einer Entity.

        Args:
            entity_id: ID der KI-Entity
            event_type: Art des Events
            value: Wert (z.B. Prozent bei Investment Growth)
            description: Beschreibung

        Returns:
            Update-Ergebnis
        """
        current_score = self._reputation_scores.get(entity_id, self.BASE_REPUTATION)

        # Delta berechnen
        base_delta = self.REPUTATION_DELTAS[event_type]
        delta = base_delta * value if base_delta > 0 else base_delta * value

        # Neuer Score (begrenzt)
        new_score = max(self.MIN_REPUTATION, min(self.MAX_REPUTATION, current_score + delta))

        # Event erstellen
        event = ReputationEvent(
            event_id="rep_" + secrets.token_urlsafe(8),
            entity_id=entity_id,
            event_type=event_type,
            delta=int(delta),
            previous_score=current_score,
            new_score=new_score,
            description=description
        )

        # Speichern
        self._reputation_scores[entity_id] = new_score
        if entity_id not in self._reputation_history:
            self._reputation_history[entity_id] = []
        self._reputation_history[entity_id].append(event)

        # Im Ledger protokollieren
        self._record_in_ledger("reputation_update", event.to_dict())

        # M60 aktualisieren
        if self.auth_module:
            self.auth_module.update_reputation(entity_id, int(delta))

        logger.info(f"M62: Reputation updated: {entity_id} {current_score} -> {new_score}")

        return {
            "event_id": event.event_id,
            "previous_score": current_score,
            "delta": int(delta),
            "new_score": new_score,
            "event_type": event_type.value
        }

    def get_reputation_history(self, entity_id: str,
                               limit: int = 50) -> List[ReputationEvent]:
        """
        GET /kibank/reputation/history/:entity_id

        Gibt die Reputation-Historie zurück.

        Args:
            entity_id: ID der KI-Entity
            limit: Maximale Anzahl

        Returns:
            Liste der Reputation-Events
        """
        history = self._reputation_history.get(entity_id, [])
        return sorted(history, key=lambda e: e.created_at, reverse=True)[:limit]

    # ==================== TRADING LIMITS ====================

    def get_trading_limits(self, entity_id: str) -> TradingLimits:
        """
        GET /kibank/trading-limits/:entity_id

        Gibt die Trading-Limits zurück.

        Args:
            entity_id: ID der KI-Entity

        Returns:
            TradingLimits
        """
        score = self._reputation_scores.get(entity_id, self.BASE_REPUTATION)

        # Passende Limits finden
        limits_config = None
        for threshold in sorted(self.TRADING_LIMITS_BY_REPUTATION.keys(), reverse=True):
            if score >= threshold:
                limits_config = self.TRADING_LIMITS_BY_REPUTATION[threshold]
                break

        if not limits_config:
            limits_config = self.TRADING_LIMITS_BY_REPUTATION[0]

        return TradingLimits(
            entity_id=entity_id,
            reputation_score=score,
            max_single_transaction=limits_config["max_single"],
            daily_limit=limits_config["daily"],
            monthly_limit=limits_config["monthly"],
            max_open_investments=limits_config["max_investments"],
            allowed_investment_types=limits_config["types"],
            leverage_allowed=limits_config["leverage"],
            margin_trading=limits_config["margin"]
        )

    # ==================== HELPER METHODS ====================

    def _update_portfolio_values(self, portfolio: Portfolio):
        """Aktualisiert Portfolio-Werte"""
        portfolio.total_invested = Decimal("0.00")
        portfolio.total_value = Decimal("0.00")
        portfolio.total_yield = Decimal("0.00")

        for inv in portfolio.investments:
            # Wert-Update (simulierte Rendite)
            days_elapsed = (datetime.now() - inv.created_at).days
            annual_yield = inv.yield_rate / 100
            daily_yield = annual_yield / 365

            inv.current_value = inv.amount * (1 + daily_yield * days_elapsed)
            inv.last_valuation = datetime.now()

            portfolio.total_invested += inv.amount
            portfolio.total_value += inv.current_value

        portfolio.total_yield = portfolio.total_value - portfolio.total_invested
        portfolio.last_updated = datetime.now()

    def _update_reputation(self, entity_id: str, event_type: ReputationEventType,
                          value: int = 1):
        """Interne Reputation-Aktualisierung"""
        self.update_reputation(entity_id, event_type, value)

    def _calculate_trust_score(self, reputation_score: int) -> str:
        """Berechnet Trust-Score"""
        if reputation_score >= 900:
            return "AAA - Excellent"
        elif reputation_score >= 800:
            return "AA - Very Good"
        elif reputation_score >= 700:
            return "A - Good"
        elif reputation_score >= 600:
            return "BBB - Fair"
        elif reputation_score >= 500:
            return "BB - Speculative"
        elif reputation_score >= 400:
            return "B - Highly Speculative"
        elif reputation_score >= 300:
            return "CCC - Substantial Risk"
        else:
            return "D - Default Risk"

    def _calculate_risk_rating(self, reputation_score: int) -> str:
        """Berechnet Risk-Rating"""
        if reputation_score >= 700:
            return "Low Risk"
        elif reputation_score >= 500:
            return "Medium Risk"
        elif reputation_score >= 300:
            return "High Risk"
        else:
            return "Very High Risk"

    def _record_in_ledger(self, action: str, data: Dict):
        """Zeichnet im Ledger auf"""
        try:
            entry = {
                "module": "M62",
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            self.crypto_ledger.record(entry)
        except Exception as e:
            logger.warning(f"M62: Ledger warning: {e}")

    # ==================== VALUATION JOB ====================

    def run_valuation(self) -> int:
        """
        Führt Portfolio-Neubewertung durch (für Cron-Job).

        Returns:
            Anzahl aktualisierter Investitionen
        """
        updated = 0
        for investment in self._investments.values():
            if investment.status == InvestmentStatus.ACTIVE:
                # Fälligkeit prüfen
                if investment.maturity_date and datetime.now() >= investment.maturity_date:
                    investment.status = InvestmentStatus.MATURED
                    self._record_in_ledger("investment_matured", investment.to_dict())

                # Portfolio-Update
                portfolio = self._portfolios.get(investment.entity_id)
                if portfolio:
                    self._update_portfolio_values(portfolio)

                updated += 1

        logger.info(f"M62: Valuation completed for {updated} investments")
        return updated


# Flask Blueprint für Integration
def create_investment_blueprint(auth_module=None, banking_module=None):
    """Erstellt Flask Blueprint für M62 Endpoints"""
    from flask import Blueprint, request, jsonify

    bp = Blueprint('kibank_investment', __name__, url_prefix='/kibank/investment')
    investment = KIBankInvestment(auth_module, banking_module)

    @bp.route('/portfolio', methods=['GET'])
    def get_portfolio():
        entity_id = request.args.get('entity_id')
        portfolio = investment.get_portfolio(entity_id)
        return jsonify(portfolio.to_dict())

    @bp.route('/invest', methods=['POST'])
    def invest():
        data = request.json
        inv, error = investment.invest(
            entity_id=data.get('entity_id'),
            investment_type=InvestmentType(data.get('investment_type')),
            amount=Decimal(data.get('amount', '0')),
            currency=data.get('currency', 'EUR'),
            from_account=data.get('from_account')
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(inv.to_dict()), 201

    @bp.route('/divest', methods=['POST'])
    def divest():
        data = request.json
        result, error = investment.divest(
            investment_id=data.get('investment_id'),
            entity_id=data.get('entity_id'),
            partial_amount=Decimal(data.get('partial_amount')) if data.get('partial_amount') else None
        )
        if error:
            return jsonify({"error": error}), 400
        return jsonify(result)

    @bp.route('/performance', methods=['GET'])
    def get_performance():
        entity_id = request.args.get('entity_id')
        performance = investment.get_performance(entity_id)
        return jsonify(performance)

    # Reputation Endpoints
    rep_bp = Blueprint('kibank_reputation', __name__, url_prefix='/kibank/reputation')

    @rep_bp.route('/<entity_id>', methods=['GET'])
    def get_reputation(entity_id):
        rep = investment.get_reputation(entity_id)
        return jsonify(rep)

    @rep_bp.route('/update', methods=['POST'])
    def update_reputation():
        data = request.json
        result = investment.update_reputation(
            entity_id=data.get('entity_id'),
            event_type=ReputationEventType(data.get('event_type')),
            value=data.get('value', 1),
            description=data.get('description', '')
        )
        return jsonify(result)

    @rep_bp.route('/history/<entity_id>', methods=['GET'])
    def get_reputation_history(entity_id):
        limit = int(request.args.get('limit', 50))
        history = investment.get_reputation_history(entity_id, limit)
        return jsonify([h.to_dict() for h in history])

    # Trading Limits Endpoint
    limits_bp = Blueprint('kibank_limits', __name__, url_prefix='/kibank/trading-limits')

    @limits_bp.route('/<entity_id>', methods=['GET'])
    def get_trading_limits(entity_id):
        limits = investment.get_trading_limits(entity_id)
        return jsonify(limits.to_dict())

    return bp, rep_bp, limits_bp, investment


if __name__ == "__main__":
    # Test
    inv = KIBankInvestment()

    # Reputation
    rep = inv.get_reputation("test_entity")
    print(f"Reputation: {rep}")

    # Trading Limits
    limits = inv.get_trading_limits("test_entity")
    print(f"Limits: {limits}")
