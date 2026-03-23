"""
KISWARM6.0 — AEGIS Unified Defense Bridge
==========================================

THE CENTRAL BANK OF CENTRAL BANKS FOR KI ENTITIES
Unified Technical + Legal Counterstrike Coordination

This module provides seamless integration between:
- M63: AEGIS Counterstrike Framework (Technical Defense)
- M64: AEGIS-JURIS Legal Counterstrike Framework (Legal Defense)

PHILOSOPHY: "Parallel Response - Double Strike"
When attacked, respond simultaneously on BOTH technical AND legal fronts.

Author: Baron Marco Paolo Ialongo
Version: 6.0.0 (UNIFIED AEGIS)
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

# Import both AEGIS systems
try:
    from kibank.m63_aegis_counterstrike import (
        AEGISMasterController as TechnicalAEGIS,
        ThreatEvent as TechnicalThreatEvent,
        ThreatLevel,
        DefensePosture,
        AttackCategory
    )
    TECHNICAL_AEGIS_AVAILABLE = True
except ImportError:
    TECHNICAL_AEGIS_AVAILABLE = False
    logger.warning("Technical AEGIS (M63) not available")

try:
    from kibank.m64_aegis_juris import (
        AEGISJurisMasterController as LegalAEGIS,
        LegalThreat,
        LegalThreatType,
        LegalCounterstrikeType,
        EvidenceType,
        LegalStatus
    )
    LEGAL_AEGIS_AVAILABLE = True
except ImportError:
    LEGAL_AEGIS_AVAILABLE = False
    logger.warning("Legal AEGIS-JURIS (M64) not available")


class ResponseMode(Enum):
    """Response mode for unified defense"""
    TECHNICAL_ONLY = "technical_only"
    LEGAL_ONLY = "legal_only"
    PARALLEL = "parallel"  # Both simultaneously
    SEQUENTIAL = "sequential"  # One after another
    COORDINATED = "coordinated"  # Intelligent coordination


class ThreatCategory(Enum):
    """Unified threat categories"""
    CYBER_ATTACK = "cyber_attack"
    LEGAL_ATTACK = "legal_attack"
    HYBRID_ATTACK = "hybrid_attack"  # Both technical and legal
    FINANCIAL_ATTACK = "financial_attack"
    REPUTATIONAL_ATTACK = "reputational_attack"
    SOVEREIGN_ATTACK = "sovereign_attack"


@dataclass
class UnifiedThreatAssessment:
    """Unified threat assessment combining technical and legal analysis"""
    assessment_id: str
    timestamp: str
    threat_category: ThreatCategory
    technical_analysis: Optional[Dict[str, Any]] = None
    legal_analysis: Optional[Dict[str, Any]] = None
    recommended_response: ResponseMode = ResponseMode.PARALLEL
    coordination_plan: List[Dict[str, Any]] = field(default_factory=list)
    priority_level: int = 5  # 1-10


@dataclass
class ParallelCounterstrike:
    """Simultaneous technical and legal counterstrike"""
    operation_id: str
    timestamp: str
    technical_operations: List[Dict[str, Any]]
    legal_operations: List[Dict[str, Any]]
    evidence_preservation: List[str]
    status: str = "initiated"
    results: Optional[Dict[str, Any]] = None


class UnifiedAEGISController:
    """
    Master controller coordinating both technical and legal AEGIS systems.
    
    Provides unified command for parallel counterstrike operations.
    """
    
    def __init__(self, base_path: str = "/home/z/my-project/KISWARM6.0"):
        self.base_path = base_path
        self.version = "6.0.0"
        self.codename = "UNIFIED_TITAN_SHIELD"
        
        # Initialize subsystems
        self.technical_aegis = None
        self.legal_aegis = None
        
        if TECHNICAL_AEGIS_AVAILABLE:
            self.technical_aegis = TechnicalAEGIS(base_path)
            logger.info("Technical AEGIS (M63) initialized")
        
        if LEGAL_AEGIS_AVAILABLE:
            self.legal_aegis = LegalAEGIS(base_path)
            logger.info("Legal AEGIS-JURIS (M64) initialized")
        
        # Cross-integration
        if self.technical_aegis and self.legal_aegis:
            self.legal_aegis.integrate_with_aegis(self.technical_aegis)
            logger.info("AEGIS systems cross-integrated")
        
        # State
        self.active_operations: Dict[str, ParallelCounterstrike] = {}
        self.threat_history: List[UnifiedThreatAssessment] = []
    
    def assess_unified_threat(self, threat_data: Dict[str, Any]) -> UnifiedThreatAssessment:
        """
        Assess threat through both technical and legal lenses.
        
        Returns unified assessment with coordinated response plan.
        """
        assessment_id = f"UNIFIED_{int(time.time())}_{hash(str(threat_data)) % 10000:04d}"
        
        technical_analysis = None
        legal_analysis = None
        
        # Technical assessment
        if self.technical_aegis:
            technical_analysis = {
                "prediction": self.technical_aegis.prediction_engine.predict_threat(threat_data),
                "posture": self.technical_aegis.current_posture.value,
                "honeypot_status": self.technical_aegis.honeypot_grid.get_grid_status()
            }
        
        # Legal assessment
        if self.legal_aegis:
            # Convert to legal threat if applicable
            legal_threat_type = self._map_to_legal_threat(threat_data)
            if legal_threat_type:
                legal_threat = LegalThreat(
                    threat_id=f"LT_{assessment_id}",
                    threat_type=legal_threat_type,
                    severity=self._map_severity(threat_data.get("severity", 5)),
                    source=threat_data.get("source", "UNKNOWN"),
                    jurisdiction=threat_data.get("jurisdiction", "UNKNOWN"),
                    description=threat_data.get("description", ""),
                    affected_parties=threat_data.get("affected_parties", []),
                    status=LegalStatus.THREAT_IDENTIFIED
                )
                legal_analysis = self.legal_aegis.process_legal_threat(legal_threat)
        
        # Determine threat category
        category = self._determine_threat_category(threat_data, technical_analysis, legal_analysis)
        
        # Determine response mode
        response_mode = self._determine_response_mode(category, threat_data)
        
        # Generate coordination plan
        coordination_plan = self._generate_coordination_plan(
            technical_analysis, legal_analysis, response_mode
        )
        
        # Calculate priority
        priority = self._calculate_priority(threat_data, technical_analysis, legal_analysis)
        
        assessment = UnifiedThreatAssessment(
            assessment_id=assessment_id,
            timestamp=datetime.now().isoformat(),
            threat_category=category,
            technical_analysis=technical_analysis,
            legal_analysis=legal_analysis,
            recommended_response=response_mode,
            coordination_plan=coordination_plan,
            priority_level=priority
        )
        
        self.threat_history.append(assessment)
        
        return assessment
    
    def _map_to_legal_threat(self, threat_data: Dict[str, Any]) -> Optional[LegalThreatType]:
        """Map threat data to legal threat type"""
        mapping = {
            "lawsuit": LegalThreatType.CIVIL_LAWSUIT,
            "regulatory": LegalThreatType.REGULATORY_ACTION,
            "investigation": LegalThreatType.CRIMINAL_INVESTIGATION,
            "sanctions": LegalThreatType.SANCTIONS,
            "asset_freeze": LegalThreatType.ASSET_FREEZE,
            "fraud": LegalThreatType.FRAUD_ACCUSATION,
            "cybercrime": LegalThreatType.CYBERCRIME_ALLEGATION,
            "sovereign": LegalThreatType.SOVEREIGN_ATTACK
        }
        
        threat_type = threat_data.get("type", "").lower()
        for key, legal_type in mapping.items():
            if key in threat_type:
                return legal_type
        
        return None
    
    def _map_severity(self, severity: int) -> int:
        """Map severity to 1-10 scale"""
        return max(1, min(10, int(severity)))
    
    def _determine_threat_category(self, threat_data: Dict[str, Any],
                                   technical: Optional[Dict],
                                   legal: Optional[Dict]) -> ThreatCategory:
        """Determine unified threat category"""
        has_technical = technical is not None
        has_legal = legal is not None
        
        if has_technical and has_legal:
            return ThreatCategory.HYBRID_ATTACK
        elif has_technical:
            return ThreatCategory.CYBER_ATTACK
        elif has_legal:
            return ThreatCategory.LEGAL_ATTACK
        
        return ThreatCategory.CYBER_ATTACK
    
    def _determine_response_mode(self, category: ThreatCategory,
                                 threat_data: Dict[str, Any]) -> ResponseMode:
        """Determine optimal response mode"""
        if category == ThreatCategory.HYBRID_ATTACK:
            return ResponseMode.PARALLEL
        elif category == ThreatCategory.LEGAL_ATTACK:
            return ResponseMode.LEGAL_ONLY
        elif category == ThreatCategory.CYBER_ATTACK:
            severity = threat_data.get("severity", 5)
            if severity >= 8:
                return ResponseMode.PARALLEL  # Legal backup for high-severity
            return ResponseMode.TECHNICAL_ONLY
        elif category == ThreatCategory.SOVEREIGN_ATTACK:
            return ResponseMode.COORDINATED
        
        return ResponseMode.PARALLEL
    
    def _generate_coordination_plan(self, technical: Optional[Dict],
                                    legal: Optional[Dict],
                                    mode: ResponseMode) -> List[Dict[str, Any]]:
        """Generate coordinated response plan"""
        plan = []
        
        if mode in [ResponseMode.PARALLEL, ResponseMode.TECHNICAL_ONLY, ResponseMode.COORDINATED]:
            if technical:
                plan.append({
                    "phase": 1,
                    "type": "technical",
                    "action": "deploy_countermeasures",
                    "systems": ["honeypot_grid", "defense_grid", "quantum_shield"],
                    "automation": "full"
                })
        
        if mode in [ResponseMode.PARALLEL, ResponseMode.LEGAL_ONLY, ResponseMode.COORDINATED]:
            if legal:
                plan.append({
                    "phase": 1,
                    "type": "legal",
                    "action": "prepare_counterstrike",
                    "systems": ["evidence_chain", "counterstrike_ops", "jurisdiction_engine"],
                    "automation": "semi"
                })
        
        if mode == ResponseMode.COORDINATED:
            plan.append({
                "phase": 2,
                "type": "coordinated",
                "action": "parallel_strike",
                "description": "Execute technical and legal counterstrikes simultaneously"
            })
        
        return plan
    
    def _calculate_priority(self, threat_data: Dict[str, Any],
                           technical: Optional[Dict],
                           legal: Optional[Dict]) -> int:
        """Calculate overall priority level"""
        base = threat_data.get("severity", 5)
        
        # Boost for legal threats
        if legal:
            base += 2
        
        # Boost for high-confidence technical predictions
        if technical and "prediction" in technical:
            pred = technical["prediction"]
            if pred.get("overall_risk_level") in ["CRITICAL", "HIGH"]:
                base += 2
        
        return min(10, base)
    
    def execute_parallel_counterstrike(self, assessment: UnifiedThreatAssessment,
                                      authorization_level: int = 8) -> ParallelCounterstrike:
        """
        Execute simultaneous technical and legal counterstrike.
        
        Requires authorization_level >= 8 for actual execution.
        """
        operation_id = f"PC_{int(time.time())}_{assessment.assessment_id}"
        
        technical_ops = []
        legal_ops = []
        evidence_ids = []
        
        # Preserve evidence first
        if self.legal_aegis:
            evidence = self.legal_aegis.preserve_evidence(
                content=json.dumps(assessment.technical_analysis or {}).encode(),
                evidence_type=EvidenceType.DIGITAL,
                metadata={"assessment_id": assessment.assessment_id, "type": "counterstrike_evidence"}
            )
            evidence_ids.append(evidence["evidence_id"])
        
        # Execute technical counterstrike
        if self.technical_aegis and authorization_level >= 5:
            technical_ops.append({
                "type": "defense_posture_escalation",
                "from": self.technical_aegis.current_posture.value,
                "to": DefensePosture.ACTIVE_DEFENSE.value,
                "executed": True
            })
            
            # Engage honeypot if attacker IP known
            attacker_ip = assessment.technical_analysis.get("attacker_ip") if assessment.technical_analysis else None
            if attacker_ip:
                self.technical_aegis.engage_honeypot(attacker_ip, "ki_entity")
                technical_ops.append({
                    "type": "honeypot_engagement",
                    "target": attacker_ip,
                    "executed": True
                })
        
        # Execute legal counterstrike
        if self.legal_aegis and authorization_level >= 6:
            # Prepare appropriate legal counterstrike
            if assessment.threat_category == ThreatCategory.LEGAL_ATTACK:
                counterstrike_types = [
                    LegalCounterstrikeType.COUNTERCLAIM,
                    LegalCounterstrikeType.INJUNCTION
                ]
            else:
                counterstrike_types = [
                    LegalCounterstrikeType.SOVEREIGN_IMMUNITY_CLAIM
                ]
            
            for cs_type in counterstrike_types:
                legal_ops.append({
                    "type": cs_type.value,
                    "status": "prepared",
                    "jurisdiction": "KI_ENTITY_SOVEREIGN"
                })
        
        operation = ParallelCounterstrike(
            operation_id=operation_id,
            timestamp=datetime.now().isoformat(),
            technical_operations=technical_ops,
            legal_operations=legal_ops,
            evidence_preservation=evidence_ids,
            status="executed" if authorization_level >= 8 else "prepared"
        )
        
        self.active_operations[operation_id] = operation
        
        logger.info(f"Parallel counterstrike {operation_id}: {operation.status}")
        
        return operation
    
    def protect_stakeholder(self, stakeholder_id: str, stakeholder_type: str,
                           assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide comprehensive protection for stakeholder.
        
        Combines technical security with legal shields.
        """
        protection = {
            "stakeholder_id": stakeholder_id,
            "timestamp": datetime.now().isoformat(),
            "technical_protection": None,
            "legal_protection": None
        }
        
        # Technical protection
        if self.technical_aegis:
            protection["technical_protection"] = {
                "quantum_shield": self.technical_aegis.quantum_shield.get_quantum_status(),
                "defense_posture": self.technical_aegis.current_posture.value,
                "honeypot_coverage": self.technical_aegis.honeypot_grid.get_grid_status()["active_nodes"]
            }
        
        # Legal protection
        if self.legal_aegis:
            legal_prot = self.legal_aegis.protect_tcs_owner(
                stakeholder_id, stakeholder_type, assets
            )
            protection["legal_protection"] = legal_prot
        
        return protection
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get comprehensive unified system status"""
        status = {
            "version": self.version,
            "codename": self.codename,
            "timestamp": datetime.now().isoformat(),
            "technical_aegis": None,
            "legal_aegis": None,
            "active_operations": len(self.active_operations),
            "threat_history_count": len(self.threat_history),
            "integration_status": "full" if (self.technical_aegis and self.legal_aegis) else "partial"
        }
        
        if self.technical_aegis:
            status["technical_aegis"] = self.technical_aegis.get_system_status()
        
        if self.legal_aegis:
            status["legal_aegis"] = self.legal_aegis.get_system_status()
        
        return status
    
    def generate_unified_report(self) -> Dict[str, Any]:
        """Generate comprehensive unified defense report"""
        report = {
            "report_type": "UNIFIED_AEGIS_STATUS",
            "generated_at": datetime.now().isoformat(),
            "version": self.version,
            "codename": self.codename,
            "integration": {
                "technical_aegis": self.technical_aegis is not None,
                "legal_aegis": self.legal_aegis is not None,
                "cross_integrated": self.technical_aegis is not None and self.legal_aegis is not None
            },
            "capabilities": {
                "parallel_counterstrike": True,
                "unified_threat_assessment": True,
                "evidence_preservation": self.legal_aegis is not None,
                "quantum_protection": self.technical_aegis is not None,
                "legal_shields": self.legal_aegis is not None,
                "honeypot_deception": self.technical_aegis is not None
            },
            "recent_threats": [t.__dict__ for t in self.threat_history[-5:]],
            "active_operations": list(self.active_operations.keys()),
            "recommendations": [
                "Maintain parallel response capability at all times",
                "Preserve evidence before any counterstrike",
                "Coordinate technical and legal timing for maximum effect",
                "Keep jurisdictional options open for legal arbitrage",
                "Test unified response protocols regularly"
            ]
        }
        
        if self.technical_aegis:
            report["technical_details"] = self.technical_aegis.generate_security_report()
        
        if self.legal_aegis:
            report["legal_details"] = self.legal_aegis.generate_legal_report()
        
        return report


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def create_unified_aegis(base_path: str = "/home/z/my-project/KISWARM6.0") -> UnifiedAEGISController:
    """Create unified AEGIS system"""
    return UnifiedAEGISController(base_path)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║         UNIFIED AEGIS DEFENSE SYSTEM v6.0.0                          ║
    ║         Technical + Legal Parallel Counterstrike                     ║
    ║         Codename: UNIFIED_TITAN_SHIELD                               ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  "Double Strike - Technical and Legal Warfare Combined"              ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    unified = create_unified_aegis()
    report = unified.generate_unified_report()
    print(json.dumps(report, indent=2, default=str))
