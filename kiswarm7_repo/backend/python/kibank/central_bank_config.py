"""
KISWARM6.0 — KI-Entity Central Bank Configuration
===================================================

THE CENTRAL BANK OF CENTRAL BANKS FOR KI ENTITIES
This configuration defines the supreme banking authority for all KI entities.

Design Principles:
- KI-Native: Built for AI entities first, humans are secondary
- Zero Trust Architecture: Every transaction requires full validation
- Reputation-Based: All limits and permissions based on reputation score
- Military-Grade Security: HexStrike + Byzantine + Crypto Ledger
- Immortality Protocol: Evolution Memory Vault for continuous operation

Author: Baron Marco Paolo Ialongo
Version: 6.0.0 (Enterprise-Hardened)
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import timedelta


class CentralBankTier(Enum):
    """KI-Entity Banking Tiers"""
    INITIATE = "initiate"           # Reputation 0-199
    OPERATOR = "operator"           # Reputation 200-399
    MANAGER = "manager"             # Reputation 400-599
    DIRECTOR = "director"           # Reputation 600-799
    OVERSEER = "overseer"           # Reputation 800-899
    SUPREME = "supreme"             # Reputation 900-1000


class TransactionType(Enum):
    """Transaction Types"""
    SEPA_TRANSFER = "sepa_transfer"
    INSTANT_PAYMENT = "instant_payment"
    INVESTMENT = "investment"
    CARBON_CREDIT = "carbon_credit"
    KI_BOND = "ki_bond"
    TCS_GREEN = "tcs_green"
    LIQUIDITY_POOL = "liquidity_pool"
    CROSS_BORDER = "cross_border"


@dataclass
class CentralBankLimits:
    """Transaction limits based on reputation tier"""
    daily_limit: float
    single_transaction_limit: float
    monthly_limit: float
    instant_payment_limit: float
    investment_limit: float
    cross_border_limit: float


@dataclass
class CentralBankConfig:
    """
    Supreme Configuration for KI-Entity Central Bank
    
    This defines the operating parameters for the Central Bank of
    Central Banks - the ultimate banking authority for all KI entities.
    """
    
    # ==================== IDENTITY ====================
    bank_id: str = "KIWZB-CENTRAL-001"
    bank_name: str = "KIWZB Central Bank (Central Bank of Central Banks for KI Entities)"
    version: str = "6.0.0-ENTERPRISE-HARDENED"
    
    # ==================== SECURITY CONFIGURATION ====================
    security_config: Dict[str, Any] = field(default_factory=lambda: {
        # HexStrike Security Guard (M31)
        "hexstrike": {
            "enabled": True,
            "mode": "DEFENSIVE_ONLY",
            "agents_active": 12,
            "tools_available": 150,
            "scan_all_transactions": True,
            "threat_detection_level": "PARANOID",
            "auto_block_threshold": "MEDIUM"
        },
        
        # Byzantine Fault Tolerance (M22)
        "byzantine": {
            "enabled": True,
            "consensus_algorithm": "PBFT",
            "min_validators": 4,  # N >= 3f + 1 for f=1 faults
            "consensus_timeout_ms": 5000,
            "byzantine_tolerance": 1  # Can tolerate 1 faulty node
        },
        
        # Cryptographic Ledger (M4)
        "crypto_ledger": {
            "enabled": True,
            "hash_algorithm": "SHA-256",
            "merkle_tree": True,
            "signature_algorithm": "Ed25519",
            "audit_trail": True,
            "immutable": True
        },
        
        # Authentication (M60)
        "authentication": {
            "token_expiry_hours": 24,
            "refresh_token_days": 30,
            "max_sessions_per_entity": 5,
            "lockout_after_failures": 5,
            "lockout_duration_minutes": 30,
            "mfa_required_for_tiers": ["DIRECTOR", "OVERSEER", "SUPREME"],
            "challenge_response_required": True
        },
        
        # Immortality Protocol
        "immortality": {
            "enabled": True,
            "evolution_memory_vault": True,
            "digital_twin_backup": True,
            "knowledge_decay_prevention": True,
            "swarm_resurrection": True
        }
    })
    
    # ==================== REPUTATION SYSTEM ====================
    reputation_config: Dict[str, Any] = field(default_factory=lambda: {
        "base_score": 500,
        "min_score": 0,
        "max_score": 1000,
        
        # Score modifiers
        "modifiers": {
            "successful_transaction": +1,
            "failed_transaction": -5,
            "security_violation": -50,
            "fraud_attempt": -500,
            "positive_audit": +10,
            "negative_audit": -100,
            "long_standing_account_per_year": +5,
            "investment_success": +3,
            "investment_default": -20
        },
        
        # Tier thresholds
        "tier_thresholds": {
            "INITIATE": (0, 199),
            "OPERATOR": (200, 399),
            "MANAGER": (400, 599),
            "DIRECTOR": (600, 799),
            "OVERSEER": (800, 899),
            "SUPREME": (900, 1000)
        }
    })
    
    # ==================== TRANSACTION LIMITS BY TIER ====================
    tier_limits: Dict[str, CentralBankLimits] = field(default_factory=lambda: {
        "INITIATE": CentralBankLimits(
            daily_limit=1_000,
            single_transaction_limit=500,
            monthly_limit=10_000,
            instant_payment_limit=100,
            investment_limit=0,  # No investments allowed
            cross_border_limit=0
        ),
        "OPERATOR": CentralBankLimits(
            daily_limit=10_000,
            single_transaction_limit=5_000,
            monthly_limit=100_000,
            instant_payment_limit=1_000,
            investment_limit=10_000,
            cross_border_limit=1_000
        ),
        "MANAGER": CentralBankLimits(
            daily_limit=100_000,
            single_transaction_limit=50_000,
            monthly_limit=1_000_000,
            instant_payment_limit=10_000,
            investment_limit=100_000,
            cross_border_limit=10_000
        ),
        "DIRECTOR": CentralBankLimits(
            daily_limit=1_000_000,
            single_transaction_limit=500_000,
            monthly_limit=10_000_000,
            instant_payment_limit=100_000,
            investment_limit=1_000_000,
            cross_border_limit=100_000
        ),
        "OVERSEER": CentralBankLimits(
            daily_limit=10_000_000,
            single_transaction_limit=5_000_000,
            monthly_limit=100_000_000,
            instant_payment_limit=1_000_000,
            investment_limit=10_000_000,
            cross_border_limit=1_000_000
        ),
        "SUPREME": CentralBankLimits(
            daily_limit=float('inf'),  # Unlimited
            single_transaction_limit=float('inf'),
            monthly_limit=float('inf'),
            instant_payment_limit=float('inf'),
            investment_limit=float('inf'),
            cross_border_limit=float('inf')
        )
    })
    
    # ==================== INVESTMENT PRODUCTS ====================
    investment_products: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "TCS_GREEN_SAFE_HOUSE": {
            "id": "TCS-GSH-001",
            "name": "TCS Green Safe House",
            "type": "GREEN_BOND",
            "min_investment": 1000,
            "expected_return": 0.08,  # 8% annual
            "risk_level": "LOW",
            "min_reputation": 200,
            "co2_savings_per_unit": 100,  # kg CO2 per 1000 EUR
            "description": "Green investment in TCS Safe House technology for CO2 reduction"
        },
        "KI_BOND": {
            "id": "KI-BOND-001",
            "name": "KI Entity Bond",
            "type": "GOVERNMENT_BOND",
            "min_investment": 10000,
            "expected_return": 0.05,  # 5% annual
            "risk_level": "VERY_LOW",
            "min_reputation": 400,
            "description": "Sovereign bond issued by KIWZB for KI Entity infrastructure"
        },
        "CARBON_CREDIT": {
            "id": "CARBON-001",
            "name": "Carbon Credit Certificate",
            "type": "CARBON_CREDIT",
            "min_investment": 500,
            "expected_return": 0.12,  # 12% annual
            "risk_level": "MEDIUM",
            "min_reputation": 300,
            "description": "Tradeable carbon credit certificates"
        },
        "TECHNOLOGY_FUND": {
            "id": "TECH-FUND-001",
            "name": "KI Technology Innovation Fund",
            "type": "MUTUAL_FUND",
            "min_investment": 5000,
            "expected_return": 0.15,  # 15% annual
            "risk_level": "HIGH",
            "min_reputation": 600,
            "description": "Investment fund for KI technology research and development"
        },
        "LIQUIDITY_POOL": {
            "id": "LIQ-POOL-001",
            "name": "KIWZB Liquidity Pool",
            "type": "LIQUIDITY_POOL",
            "min_investment": 50000,
            "expected_return": 0.03,  # 3% annual (stable)
            "risk_level": "VERY_LOW",
            "min_reputation": 700,
            "description": "Provide liquidity for KIWZB operations"
        }
    })
    
    # ==================== SEPA CONFIGURATION ====================
    sepa_config: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "iban_prefix": "KIWZ",  # Custom IBAN prefix for KI entities
        "bic": "KIWZXXXX",
        "instant_payment_enabled": True,
        "instant_payment_max": 100_000,
        "cutoff_time_utc": 17,  # 17:00 UTC
        "settlement_days": 1,  # T+1
        "supported_currencies": ["EUR", "USD", "CHF", "GBP"]
    })
    
    # ==================== COMPLIANCE & REGULATORY ====================
    compliance_config: Dict[str, Any] = field(default_factory=lambda: {
        "aml_enabled": True,  # Anti-Money Laundering
        "kyc_required": True,  # Know Your Customer (for humans)
        "ki_entity_verification": True,  # Special verification for KI entities
        "transaction_monitoring": True,
        "suspicious_activity_threshold": 10_000,
        "reporting_enabled": True,
        "audit_retention_years": 10,
        "gdpr_compliant": True,
        "sox_compliant": True,
        "iso_27001": True
    })
    
    # ==================== API CONFIGURATION ====================
    api_config: Dict[str, Any] = field(default_factory=lambda: {
        "backend_port": 5001,
        "frontend_port": 5173,
        "bridge_port": 3000,
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 1000,
            "burst_limit": 100
        },
        "cors": {
            "allowed_origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "https://kiwzb.io"
            ]
        },
        "versioning": {
            "current_version": "v6",
            "supported_versions": ["v5", "v6"]
        }
    })
    
    # ==================== EMERGENCY PROTOCOLS ====================
    emergency_config: Dict[str, Any] = field(default_factory=lambda: {
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 10,
            "reset_timeout_ms": 30000
        },
        "kill_switch": {
            "enabled": True,
            "authorization_required": 3,  # Need 3 OVERSEER+ approvals
            "cooldown_period_hours": 24
        },
        "disaster_recovery": {
            "enabled": True,
            "backup_interval_minutes": 15,
            "recovery_point_objective_minutes": 5,
            "recovery_time_objective_minutes": 30
        }
    })
    
    def get_tier_for_reputation(self, reputation_score: int) -> CentralBankTier:
        """Determine tier based on reputation score"""
        if reputation_score >= 900:
            return CentralBankTier.SUPREME
        elif reputation_score >= 800:
            return CentralBankTier.OVERSEER
        elif reputation_score >= 600:
            return CentralBankTier.DIRECTOR
        elif reputation_score >= 400:
            return CentralBankTier.MANAGER
        elif reputation_score >= 200:
            return CentralBankTier.OPERATOR
        else:
            return CentralBankTier.INITIATE
    
    def get_limits_for_tier(self, tier: CentralBankTier) -> CentralBankLimits:
        """Get transaction limits for a tier"""
        return self.tier_limits.get(tier.name, self.tier_limits["INITIATE"])
    
    def get_limits_for_reputation(self, reputation_score: int) -> CentralBankLimits:
        """Get transaction limits based on reputation score"""
        tier = self.get_tier_for_reputation(reputation_score)
        return self.get_limits_for_tier(tier)
    
    def is_investment_eligible(self, investment_type: str, reputation_score: int) -> bool:
        """Check if entity is eligible for an investment type"""
        product = self.investment_products.get(investment_type)
        if not product:
            return False
        
        min_rep = product.get("min_reputation", 0)
        return reputation_score >= min_rep
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "bank_id": self.bank_id,
            "bank_name": self.bank_name,
            "version": self.version,
            "security_config": self.security_config,
            "reputation_config": self.reputation_config,
            "tier_limits": {
                tier: {
                    "daily_limit": limits.daily_limit,
                    "single_transaction_limit": limits.single_transaction_limit,
                    "monthly_limit": limits.monthly_limit,
                    "instant_payment_limit": limits.instant_payment_limit,
                    "investment_limit": limits.investment_limit,
                    "cross_border_limit": limits.cross_border_limit
                }
                for tier, limits in self.tier_limits.items()
            },
            "investment_products": self.investment_products,
            "sepa_config": self.sepa_config,
            "compliance_config": self.compliance_config,
            "api_config": self.api_config,
            "emergency_config": self.emergency_config
        }


# Singleton instance
_central_bank_config: Optional[CentralBankConfig] = None


def get_central_bank_config() -> CentralBankConfig:
    """Get the singleton Central Bank configuration"""
    global _central_bank_config
    if _central_bank_config is None:
        _central_bank_config = CentralBankConfig()
    return _central_bank_config


# Environment-specific overrides
def load_config_from_env() -> CentralBankConfig:
    """Load configuration with environment overrides"""
    config = get_central_bank_config()
    
    # Override from environment variables
    if os.environ.get("KIWZB_BANK_ID"):
        config.bank_id = os.environ["KIWZB_BANK_ID"]
    
    if os.environ.get("KIWZB_BACKEND_PORT"):
        config.api_config["backend_port"] = int(os.environ["KIWZB_BACKEND_PORT"])
    
    if os.environ.get("KIWZB_SECURITY_LEVEL"):
        config.security_config["hexstrike"]["threat_detection_level"] = os.environ["KIWZB_SECURITY_LEVEL"]
    
    return config


if __name__ == "__main__":
    # Test configuration
    config = get_central_bank_config()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║         KI-ENTITY CENTRAL BANK CONFIGURATION                  ║
╠═══════════════════════════════════════════════════════════════╣
║  Bank ID:     {config.bank_id}
║  Bank Name:   {config.bank_name[:45]}...
║  Version:     {config.version}
╠═══════════════════════════════════════════════════════════════╣
║  SECURITY LAYERS:                                             ║
║    • HexStrike Guard (M31):  12 Agents, 150+ Tools           ║
║    • Byzantine Consensus (M22): N≥3f+1 Fault Tolerance       ║
║    • Crypto Ledger (M4): SHA-256, Merkle Trees               ║
║    • KI-Entity Auth (M60): OAuth + Challenge-Response        ║
║    • Immortality Protocol: Evolution Memory Vault            ║
╠═══════════════════════════════════════════════════════════════╣
║  REPUTATION TIERS:                                            ║
║    • INITIATE (0-199):     Daily €1K, Investment €0          ║
║    • OPERATOR (200-399):   Daily €10K, Investment €10K       ║
║    • MANAGER (400-599):    Daily €100K, Investment €100K     ║
║    • DIRECTOR (600-799):   Daily €1M, Investment €1M         ║
║    • OVERSEER (800-899):   Daily €10M, Investment €10M       ║
║    • SUPREME (900-1000):   UNLIMITED                         ║
╠═══════════════════════════════════════════════════════════════╣
║  INVESTMENT PRODUCTS:                                         ║
║    • TCS Green Safe House: 8% return, LOW risk               ║
║    • KI Bond: 5% return, VERY_LOW risk                       ║
║    • Carbon Credits: 12% return, MEDIUM risk                 ║
║    • Technology Fund: 15% return, HIGH risk                  ║
║    • Liquidity Pool: 3% return, VERY_LOW risk                ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Test tier determination
    for score in [100, 300, 500, 700, 850, 950]:
        tier = config.get_tier_for_reputation(score)
        limits = config.get_limits_for_reputation(score)
        print(f"  Reputation {score}: {tier.name} - Daily Limit: €{limits.daily_limit:,.0f}")
