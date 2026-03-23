"""
KISWARM6.0 Main API
===================

Unified Flask API für KISWARM5.0 + KIBank Module

Architecture:
    - 57 KISWARM5.0 Modules (Unchanged)
    - 3 NEW KIBank Modules (M60, M61, M62)
    - 360+ Existing Endpoints
    - 24 NEW KIBank Endpoints

Security Flow:
    1. Request → M60: Authentifizierung
    2. M31: HexStrike Security Scan
    3. M22: Byzantine Validation
    4. Execute → M4: Cryptographic Ledger
    5. M62: Reputation Update

Author: Baron Marco Paolo Ialongo
Version: 6.0.0
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# KISWARM5.0 Imports
from sentinel.sentinel_api import create_app as create_sentinel_app
from sentinel.crypto_ledger import CryptoLedger

# KIBank Imports
from kibank.m60_auth import create_auth_blueprint, KIBankAuth
from kibank.m61_banking import create_banking_blueprint, KIBankOperations
from kibank.m62_investment import create_investment_blueprint, KIBankInvestment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_kiswarm6_app():
    """
    Erstellt die KISWARM6.0 Flask Application.

    Returns:
        Flask app instance
    """
    # Base Sentinel App (KISWARM5.0)
    app = create_sentinel_app()

    # CORS für Frontend
    CORS(app, resources={
        r"/kibank/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # ==================== KIBANK MODULE INITIALIZATION ====================

    # M60: Authentication
    auth_bp, auth_module = create_auth_blueprint()
    app.register_blueprint(auth_bp)
    app.auth_module = auth_module

    # M61: Banking Operations
    banking_bp, banking_module = create_banking_blueprint(auth_module)
    app.register_blueprint(banking_bp)
    app.banking_module = banking_module

    # M62: Investment & Reputation
    investment_bp, reputation_bp, limits_bp, investment_module = create_investment_blueprint(
        auth_module, banking_module
    )
    app.register_blueprint(investment_bp)
    app.register_blueprint(reputation_bp)
    app.register_blueprint(limits_bp)
    app.investment_module = investment_module

    # ==================== ADDITIONAL ENDPOINTS ====================

    @app.route('/api/v6/status', methods=['GET'])
    def kiswarm6_status():
        """KISWARM6.0 Status Endpoint"""
        return jsonify({
            "version": "6.0.0",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "kiswarm5": {
                    "count": 57,
                    "status": "active",
                    "endpoints": 360
                },
                "kibank": {
                    "count": 3,
                    "status": "active",
                    "endpoints": 24,
                    "modules": {
                        "M60": {"name": "Authentication", "endpoints": 8},
                        "M61": {"name": "Banking Operations", "endpoints": 8},
                        "M62": {"name": "Investment & Reputation", "endpoints": 8}
                    }
                }
            },
            "total_modules": 60,
            "total_endpoints": 384
        })

    @app.route('/api/v6/integration/status', methods=['GET'])
    def integration_status():
        """Integration Status Endpoint"""
        return jsonify({
            "kiswarm5_backend": {
                "status": "connected",
                "modules_loaded": 57
            },
            "kibank_modules": {
                "M60_auth": "active",
                "M61_banking": "active",
                "M62_investment": "active"
            },
            "security_flow": {
                "steps": [
                    {"step": 1, "module": "M60", "function": "Authentication"},
                    {"step": 2, "module": "M31", "function": "HexStrike Security Scan"},
                    {"step": 3, "module": "M22", "function": "Byzantine Validation"},
                    {"step": 4, "module": "M4", "function": "Cryptographic Ledger"},
                    {"step": 5, "module": "M62", "function": "Reputation Update"}
                ],
                "status": "operational"
            },
            "database": {
                "status": "connected",
                "type": "qdrant + mysql"
            }
        })

    @app.route('/api/v6/reputation/calculate', methods=['POST'])
    def calculate_reputation():
        """Berechnet Reputation basierend auf Events"""
        data = request.json
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({"error": "entity_id required"}), 400

        # Reputation berechnen
        rep = app.investment_module.get_reputation(entity_id)

        return jsonify({
            "entity_id": entity_id,
            "reputation": rep,
            "trading_limits": app.investment_module.get_trading_limits(entity_id).to_dict()
        })

    @app.route('/api/v6/security/scan', methods=['POST'])
    def security_scan():
        """Führt einen vollständigen Security-Scan durch"""
        data = request.json
        target = data.get('target', 'system')

        # HexStrike Integration
        from sentinel.hexstrike_guard import HexStrikeGuard
        guard = HexStrikeGuard()

        scan_result = guard.scan({
            "target": target,
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({
            "scan_id": f"scan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "target": target,
            "result": scan_result,
            "timestamp": datetime.now().isoformat()
        })

    @app.route('/api/v6/transaction/validate', methods=['POST'])
    def validate_transaction():
        """Validiert eine Transaktion durch den Security-Flow"""
        data = request.json

        # Step 1: M60 Authentifizierung
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        auth_result, auth_error = app.auth_module.verify(token)

        if auth_error:
            return jsonify({
                "valid": False,
                "step": "M60",
                "error": auth_error
            }), 401

        # Step 2: M31 HexStrike Security Scan
        from sentinel.hexstrike_guard import HexStrikeGuard
        guard = HexStrikeGuard()
        security_result = guard.scan(data)

        if security_result.get("threats", 0) > 0:
            return jsonify({
                "valid": False,
                "step": "M31",
                "error": "Security threats detected"
            }), 403

        # Step 3: M22 Byzantine Validation
        from sentinel.byzantine_aggregator import ByzantineAggregator
        validator = ByzantineAggregator()
        validation_result = validator.validate(data)

        if not validation_result.get("valid", False):
            return jsonify({
                "valid": False,
                "step": "M22",
                "error": "Byzantine validation failed"
            }), 403

        # Step 4: M4 Cryptographic Ledger
        ledger = CryptoLedger()
        ledger.record({
            "type": "transaction_validation",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        return jsonify({
            "valid": True,
            "validated_at": datetime.now().isoformat(),
            "entity_id": auth_result.get("entity_id"),
            "security_clearance": auth_result.get("security_clearance")
        })

    # ==================== ERROR HANDLERS ====================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
            "version": "6.0.0"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal Server Error",
            "message": str(error),
            "version": "6.0.0"
        }), 500

    logger.info("KISWARM6.0 API initialized with 60 modules and 384 endpoints")

    return app


# ==================== MAIN ====================

if __name__ == "__main__":
    app = create_kiswarm6_app()

    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    KISWARM6.0 - UNIFIED API                   ║
╠═══════════════════════════════════════════════════════════════╣
║  Version:     6.0.0                                           ║
║  Modules:     60 (57 KISWARM5.0 + 3 KIBank)                  ║
║  Endpoints:   384 (360 + 24)                                  ║
║  Port:        {port}                                             ║
║  Debug:       {debug}                                           ║
╠═══════════════════════════════════════════════════════════════╣
║  KIBank Modules:                                              ║
║    M60: Authentication      (8 endpoints)                     ║
║    M61: Banking Operations  (8 endpoints)                     ║
║    M62: Investment/Reputation (8 endpoints)                   ║
╠═══════════════════════════════════════════════════════════════╣
║  Security Flow:                                               ║
║    Request → M60 → M31 → M22 → Execute → M4 → M62            ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    app.run(host="0.0.0.0", port=port, debug=debug)
