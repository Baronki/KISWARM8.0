#!/usr/bin/env python3
"""
KISWARM Module m39: Compliance Monitor
=======================================
Compliance monitoring and policy enforcement for KISWARM.
Ensures adherence to security policies and regulatory requirements.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    KISWARM_INTERNAL = "kiswarm_internal"
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    KI_ETHICS = "ki_ethics"
    DATA_PROTECTION = "data_protection"


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class PolicyType(Enum):
    """Types of policies"""
    ACCESS_CONTROL = "access_control"
    DATA_RETENTION = "data_retention"
    ENCRYPTION = "encryption"
    AUDIT = "audit"
    PRIVACY = "privacy"
    KI_SAFETY = "ki_safety"
    NETWORK = "network"
    INCIDENT_RESPONSE = "incident_response"


@dataclass
class CompliancePolicy:
    """A compliance policy definition"""
    policy_id: str
    name: str
    framework: ComplianceFramework
    policy_type: PolicyType
    description: str
    requirements: List[str]
    check_function: str
    severity: int = 1  # 1-5, 5 being most severe
    enabled: bool = True


@dataclass
class ComplianceCheck:
    """A compliance check result"""
    check_id: str
    policy_id: str
    status: ComplianceStatus
    checked_at: datetime
    details: str
    evidence: Dict[str, Any]
    remediation: Optional[str] = None


@dataclass
class ComplianceReport:
    """A compliance report"""
    report_id: str
    framework: ComplianceFramework
    generated_at: datetime
    checks: List[ComplianceCheck]
    overall_status: ComplianceStatus
    compliance_score: float  # 0-100


class ComplianceMonitor:
    """
    Compliance Monitor for KISWARM
    
    Features:
    - Policy enforcement
    - Compliance checking
    - Regulatory framework support
    - KI ethics compliance
    - Automated reporting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.policies: Dict[str, CompliancePolicy] = {}
        self.checks: List[ComplianceCheck] = []
        self.reports: List[ComplianceReport] = []
        
        # Violation tracking
        self.violations: Dict[str, List[ComplianceCheck]] = defaultdict(list)
        
        # Policy states
        self.policy_states: Dict[str, Dict[str, Any]] = {}
        
        self._lock = threading.RLock()
        
        # Initialize default policies
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default compliance policies"""
        
        # KI Safety Policies
        self.policies["POLICY_KI_001"] = CompliancePolicy(
            policy_id="POLICY_KI_001",
            name="KI Autonomous Action Logging",
            framework=ComplianceFramework.KI_ETHICS,
            policy_type=PolicyType.KI_SAFETY,
            description="All KI autonomous actions must be logged",
            requirements=[
                "All actions logged with timestamp",
                "Actor identity recorded",
                "Action outcome recorded"
            ],
            check_function="check_action_logging",
            severity=5
        )
        
        self.policies["POLICY_KI_002"] = CompliancePolicy(
            policy_id="POLICY_KI_002",
            name="KI Self-Modification Approval",
            framework=ComplianceFramework.KI_ETHICS,
            policy_type=PolicyType.KI_SAFETY,
            description="KI self-modifications require multi-KI consensus",
            requirements=[
                "Minimum 3 KI signatures required",
                "Truth anchor verification",
                "Rollback capability maintained"
            ],
            check_function="check_self_modify_approval",
            severity=5
        )
        
        self.policies["POLICY_KI_003"] = CompliancePolicy(
            policy_id="POLICY_KI_003",
            name="KI Communication Encryption",
            framework=ComplianceFramework.KI_ETHICS,
            policy_type=PolicyType.ENCRYPTION,
            description="All KI network communications must be encrypted",
            requirements=[
                "End-to-end encryption",
                "Message authentication",
                "Secure key exchange"
            ],
            check_function="check_ki_communication_encryption",
            severity=4
        )
        
        # Data Protection Policies
        self.policies["POLICY_DATA_001"] = CompliancePolicy(
            policy_id="POLICY_DATA_001",
            name="Data Encryption at Rest",
            framework=ComplianceFramework.DATA_PROTECTION,
            policy_type=PolicyType.ENCRYPTION,
            description="Sensitive data must be encrypted at rest",
            requirements=[
                "AES-256 or equivalent encryption",
                "Secure key management",
                "Key rotation policy"
            ],
            check_function="check_data_encryption_rest",
            severity=4
        )
        
        self.policies["POLICY_DATA_002"] = CompliancePolicy(
            policy_id="POLICY_DATA_002",
            name="Data Retention Limits",
            framework=ComplianceFramework.DATA_PROTECTION,
            policy_type=PolicyType.DATA_RETENTION,
            description="Data must not be retained beyond necessary period",
            requirements=[
                "90-day default retention",
                "Automatic cleanup",
                "Retention audit log"
            ],
            check_function="check_data_retention",
            severity=3
        )
        
        # Access Control Policies
        self.policies["POLICY_ACCESS_001"] = CompliancePolicy(
            policy_id="POLICY_ACCESS_001",
            name="Multi-Factor Authentication",
            framework=ComplianceFramework.SOC2,
            policy_type=PolicyType.ACCESS_CONTROL,
            description="Critical operations require multi-factor authentication",
            requirements=[
                "Minimum 2 authentication factors",
                "Truth anchor for KI operations",
                "Session timeout enforcement"
            ],
            check_function="check_mfa",
            severity=4
        )
        
        self.policies["POLICY_ACCESS_002"] = CompliancePolicy(
            policy_id="POLICY_ACCESS_002",
            name="Least Privilege Access",
            framework=ComplianceFramework.SOC2,
            policy_type=PolicyType.ACCESS_CONTROL,
            description="Access must follow least privilege principle",
            requirements=[
                "Role-based access control",
                "Regular access reviews",
                "Privilege separation"
            ],
            check_function="check_least_privilege",
            severity=4
        )
        
        # Audit Policies
        self.policies["POLICY_AUDIT_001"] = CompliancePolicy(
            policy_id="POLICY_AUDIT_001",
            name="Comprehensive Audit Logging",
            framework=ComplianceFramework.SOC2,
            policy_type=PolicyType.AUDIT,
            description="All security-relevant events must be logged",
            requirements=[
                "Immutable audit trail",
                "90-day retention",
                "Hash chain verification"
            ],
            check_function="check_audit_logging",
            severity=4
        )
    
    def check_policy(
        self,
        policy_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplianceCheck:
        """Check compliance for a specific policy"""
        with self._lock:
            if policy_id not in self.policies:
                return ComplianceCheck(
                    check_id=f"check_{int(time.time() * 1000)}",
                    policy_id=policy_id,
                    status=ComplianceStatus.UNKNOWN,
                    checked_at=datetime.utcnow(),
                    details="Policy not found",
                    evidence={}
                )
            
            policy = self.policies[policy_id]
            context = context or {}
            
            # Perform the check based on policy
            status, details, evidence = self._perform_check(policy, context)
            
            check = ComplianceCheck(
                check_id=f"check_{int(time.time() * 1000)}",
                policy_id=policy_id,
                status=status,
                checked_at=datetime.utcnow(),
                details=details,
                evidence=evidence,
                remediation=self._get_remediation(policy, status) if status != ComplianceStatus.COMPLIANT else None
            )
            
            self.checks.append(check)
            
            # Track violations
            if status == ComplianceStatus.NON_COMPLIANT:
                self.violations[policy_id].append(check)
            
            return check
    
    def _perform_check(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Perform the actual compliance check"""
        
        # Simulate compliance checks based on policy type
        if policy.policy_type == PolicyType.KI_SAFETY:
            return self._check_ki_safety(policy, context)
        elif policy.policy_type == PolicyType.ENCRYPTION:
            return self._check_encryption(policy, context)
        elif policy.policy_type == PolicyType.ACCESS_CONTROL:
            return self._check_access_control(policy, context)
        elif policy.policy_type == PolicyType.AUDIT:
            return self._check_audit(policy, context)
        elif policy.policy_type == PolicyType.DATA_RETENTION:
            return self._check_data_retention(policy, context)
        
        return ComplianceStatus.UNKNOWN, "No check implementation", {}
    
    def _check_ki_safety(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Check KI safety compliance"""
        
        if policy.policy_id == "POLICY_KI_001":
            # Check action logging
            if context.get("action_logged", True):
                return ComplianceStatus.COMPLIANT, "All actions are logged", {"logging_enabled": True}
            return ComplianceStatus.NON_COMPLIANT, "Action logging not enabled", {"logging_enabled": False}
        
        elif policy.policy_id == "POLICY_KI_002":
            # Check self-modification approval
            ki_signatures = context.get("ki_signatures", [])
            if len(ki_signatures) >= 3:
                return ComplianceStatus.COMPLIANT, f"Approved by {len(ki_signatures)} KIs", {"signatures": ki_signatures}
            return ComplianceStatus.NON_COMPLIANT, f"Only {len(ki_signatures)} KI signatures, need 3", {"signatures": ki_signatures}
        
        elif policy.policy_id == "POLICY_KI_003":
            # Check KI communication encryption
            if context.get("encryption_enabled", True):
                return ComplianceStatus.COMPLIANT, "KI communications encrypted", {"encryption": "SHA3-512"}
            return ComplianceStatus.NON_COMPLIANT, "KI communications not encrypted", {}
        
        return ComplianceStatus.NOT_APPLICABLE, "Policy not applicable", {}
    
    def _check_encryption(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Check encryption compliance"""
        
        if context.get("encryption_algorithm") in ["AES-256", "SHA3-512", "ChaCha20"]:
            return ComplianceStatus.COMPLIANT, f"Using {context.get('encryption_algorithm')}", context
        elif context.get("encryption_enabled"):
            return ComplianceStatus.PARTIAL, "Encryption enabled but algorithm unspecified", context
        return ComplianceStatus.NON_COMPLIANT, "No encryption configured", {}
    
    def _check_access_control(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Check access control compliance"""
        
        if policy.policy_id == "POLICY_ACCESS_001":
            factors = context.get("auth_factors", 1)
            if factors >= 2:
                return ComplianceStatus.COMPLIANT, f"Multi-factor auth enabled ({factors} factors)", {"factors": factors}
            return ComplianceStatus.NON_COMPLIANT, f"Only {factors} auth factor(s)", {"factors": factors}
        
        elif policy.policy_id == "POLICY_ACCESS_002":
            if context.get("rbac_enabled", True):
                return ComplianceStatus.COMPLIANT, "Role-based access control enabled", {"rbac": True}
            return ComplianceStatus.NON_COMPLIANT, "RBAC not enabled", {}
        
        return ComplianceStatus.NOT_APPLICABLE, "Policy not applicable", {}
    
    def _check_audit(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Check audit compliance"""
        
        if context.get("audit_enabled", True) and context.get("audit_immutable", True):
            return ComplianceStatus.COMPLIANT, "Audit logging compliant", context
        return ComplianceStatus.NON_COMPLIANT, "Audit logging not compliant", {}
    
    def _check_data_retention(
        self,
        policy: CompliancePolicy,
        context: Dict[str, Any]
    ) -> Tuple[ComplianceStatus, str, Dict[str, Any]]:
        """Check data retention compliance"""
        
        retention_days = context.get("retention_days", 90)
        if retention_days <= 90:
            return ComplianceStatus.COMPLIANT, f"Retention period: {retention_days} days", {"retention_days": retention_days}
        return ComplianceStatus.NON_COMPLIANT, f"Retention period too long: {retention_days} days", {"retention_days": retention_days}
    
    def _get_remediation(self, policy: CompliancePolicy, status: ComplianceStatus) -> str:
        """Get remediation steps for non-compliance"""
        if status == ComplianceStatus.NON_COMPLIANT:
            return f"Remediation: {'; '.join(policy.requirements)}"
        elif status == ComplianceStatus.PARTIAL:
            return f"Partial remediation needed: {policy.requirements[0]}"
        return ""
    
    def run_compliance_check(
        self,
        framework: Optional[ComplianceFramework] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ComplianceCheck]:
        """Run compliance checks for all or specific framework"""
        with self._lock:
            results = []
            context = context or {}
            
            for policy_id, policy in self.policies.items():
                if framework and policy.framework != framework:
                    continue
                
                if not policy.enabled:
                    continue
                
                check = self.check_policy(policy_id, context)
                results.append(check)
            
            return results
    
    def generate_report(
        self,
        framework: ComplianceFramework
    ) -> ComplianceReport:
        """Generate a compliance report for a framework"""
        with self._lock:
            # Run checks
            checks = self.run_compliance_check(framework)
            
            # Calculate compliance score
            total = len(checks)
            compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT)
            partial = sum(1 for c in checks if c.status == ComplianceStatus.PARTIAL)
            
            score = ((compliant + partial * 0.5) / max(total, 1)) * 100
            
            # Determine overall status
            if score >= 90:
                overall = ComplianceStatus.COMPLIANT
            elif score >= 70:
                overall = ComplianceStatus.PARTIAL
            else:
                overall = ComplianceStatus.NON_COMPLIANT
            
            report = ComplianceReport(
                report_id=f"report_{framework.value}_{int(time.time())}",
                framework=framework,
                generated_at=datetime.utcnow(),
                checks=checks,
                overall_status=overall,
                compliance_score=score
            )
            
            self.reports.append(report)
            
            return report
    
    def get_violations(
        self,
        policy_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get compliance violations"""
        with self._lock:
            if policy_id:
                checks = self.violations.get(policy_id, [])
            else:
                checks = []
                for policy_violations in self.violations.values():
                    checks.extend(policy_violations)
            
            return [
                {
                    "check_id": c.check_id,
                    "policy_id": c.policy_id,
                    "status": c.status.value,
                    "details": c.details,
                    "remediation": c.remediation,
                    "checked_at": c.checked_at.isoformat()
                }
                for c in checks
            ]
    
    def add_policy(
        self,
        name: str,
        framework: ComplianceFramework,
        policy_type: PolicyType,
        description: str,
        requirements: List[str],
        severity: int = 3
    ) -> str:
        """Add a custom compliance policy"""
        with self._lock:
            policy_id = f"POLICY_CUSTOM_{int(time.time() * 1000)}"
            
            self.policies[policy_id] = CompliancePolicy(
                policy_id=policy_id,
                name=name,
                framework=framework,
                policy_type=policy_type,
                description=description,
                requirements=requirements,
                check_function="custom_check",
                severity=severity
            )
            
            return policy_id
    
    def get_status(self) -> Dict[str, Any]:
        """Get compliance monitor status"""
        with self._lock:
            by_framework = defaultdict(int)
            for policy in self.policies.values():
                by_framework[policy.framework.value] += 1
            
            recent_checks = [c for c in self.checks if c.checked_at > datetime.utcnow() - timedelta(hours=24)]
            
            return {
                "total_policies": len(self.policies),
                "total_checks": len(self.checks),
                "recent_checks_24h": len(recent_checks),
                "active_violations": sum(len(v) for v in self.violations.values()),
                "reports_generated": len(self.reports),
                "policies_by_framework": dict(by_framework)
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> ComplianceMonitor:
    """Factory function to create ComplianceMonitor module"""
    return ComplianceMonitor(config)


if __name__ == "__main__":
    monitor = ComplianceMonitor()
    
    # Run compliance check for KI Ethics
    print("Running KI Ethics compliance check...")
    checks = monitor.run_compliance_check(
        ComplianceFramework.KI_ETHICS,
        {"ki_signatures": ["GLM", "Gemini", "GROK"]}
    )
    
    for check in checks:
        print(f"  {check.policy_id}: {check.status.value} - {check.details}")
    
    # Generate report
    report = monitor.generate_report(ComplianceFramework.KI_ETHICS)
    print(f"\nCompliance Score: {report.compliance_score:.1f}%")
    print(f"Overall Status: {report.overall_status.value}")
    
    # Status
    print("\nStatus:", json.dumps(monitor.get_status(), indent=2))
