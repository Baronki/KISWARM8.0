"""
KISWARM v6.1 — Module 75: KIBank Installer Pretraining Integration
===================================================================
Integration layer connecting the Pretraining System with KIBank operations.

This module provides:
1. KIBank-specific installation scenarios
2. Customer environment profiling
3. Automated installation for KIBank customers
4. Training ground for KIBank installation agents

Author: Baron Marco Paolo Ialongo (KISWARM Project)
Version: 6.1
"""

from __future__ import annotations

import hashlib
import json
import os
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Import from sentinel (if available)
try:
    from ..sentinel.installer_pretraining import (
        InstallerPretraining,
        PretrainedInstallerAgent,
        EnvironmentType,
        LearningExperience,
        TrainingSession,
        TrainingStatus,
    )
    PRETRAINING_AVAILABLE = True
except ImportError:
    PRETRAINING_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# KIBANK-SPECIFIC ENVIRONMENT PROFILES
# ─────────────────────────────────────────────────────────────────────────────

KIBANK_ENVIRONMENT_PROFILES = {
    "kibank_customer_standard": {
        "name": "KIBank Standard Customer Environment",
        "description": "Standard customer on-premise deployment",
        "requirements": {
            "database": ["MySQL 8.0+", "MariaDB 10.5+", "TiDB 6.0+"],
            "python": "3.10+",
            "memory_min_gb": 16,
            "disk_min_gb": 100,
            "network": "TLS 1.3 support required",
        },
        "components": [
            "kibank_core",
            "aegis_security",
            "trading_engine",
            "audit_logger",
        ],
        "common_issues": [
            {"error": "Database connection timeout", "solution": "Check firewall rules and increase connection timeout"},
            {"error": "SSL certificate invalid", "solution": "Install proper certificates in /etc/ssl/certs"},
            {"error": "Insufficient privileges", "solution": "Grant required database permissions to kibank user"},
        ],
    },
    "kibank_customer_enterprise": {
        "name": "KIBank Enterprise Customer Environment",
        "description": "Enterprise customer with HA and redundancy",
        "requirements": {
            "database": ["TiDB 6.0+ with HA cluster"],
            "python": "3.11+",
            "memory_min_gb": 64,
            "disk_min_gb": 500,
            "network": "Dedicated VLAN, TLS 1.3, mTLS support",
            "ha": "Active-active or active-passive cluster",
        },
        "components": [
            "kibank_core",
            "kibank_ha",
            "aegis_security",
            "aegis_counterstrike",
            "trading_engine",
            "risk_engine",
            "audit_logger",
            "compliance_module",
        ],
        "common_issues": [
            {"error": "HA sync failure", "solution": "Check network latency and sync ports"},
            {"error": "Quorum lost", "solution": "Verify cluster nodes are reachable"},
            {"error": "Replication lag", "solution": "Optimize database configuration and network"},
        ],
    },
    "kibank_cloud_aws": {
        "name": "KIBank AWS Cloud Deployment",
        "description": "AWS cloud-native deployment",
        "requirements": {
            "database": ["Amazon Aurora MySQL", "RDS MySQL 8.0+"],
            "python": "3.10+",
            "services": ["EKS or ECS", "S3 for backups", "RDS", "CloudWatch"],
            "iam": "Required roles and policies",
        },
        "components": [
            "kibank_core",
            "aegis_security",
            "trading_engine",
            "aws_integration",
        ],
        "common_issues": [
            {"error": "IAM role not assumed", "solution": "Attach proper IAM policy to EC2/EKS role"},
            {"error": "Security group blocked", "solution": "Update security group to allow required ports"},
            {"error": "RDS connection limit", "solution": "Increase max_connections or use RDS Proxy"},
        ],
    },
    "kibank_cloud_azure": {
        "name": "KIBank Azure Cloud Deployment",
        "description": "Azure cloud-native deployment",
        "requirements": {
            "database": ["Azure Database for MySQL", "Azure SQL"],
            "python": "3.10+",
            "services": ["AKS", "Azure Storage", "Azure Monitor"],
            "identity": "Managed Identity required",
        },
        "components": [
            "kibank_core",
            "aegis_security",
            "trading_engine",
            "azure_integration",
        ],
        "common_issues": [
            {"error": "Managed identity not configured", "solution": "Enable system-assigned managed identity"},
            {"error": "NSG blocked", "solution": "Update Network Security Group rules"},
        ],
    },
    "kibank_edge_tcs": {
        "name": "KIBank TCS Edge Deployment",
        "description": "TCS Green Safe House edge deployment",
        "requirements": {
            "hardware": "3x GT15 Max cluster",
            "network": "Isolated VLAN, IPSec tunnels",
            "security": "Air-gapped with secure update mechanism",
        },
        "components": [
            "kibank_edge",
            "aegis_edge_firewall",
            "scada_bridge",
            "offline_updater",
        ],
        "common_issues": [
            {"error": "Cluster sync timeout", "solution": "Check GT15 interconnect cables"},
            {"error": "Update verification failed", "solution": "Verify update signature with offline key"},
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# KIBANK INSTALLATION SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

KIBANK_INSTALLATION_SCENARIOS = [
    {
        "scenario_id": "new_customer_onboarding",
        "name": "New Customer Onboarding",
        "description": "Complete installation for new KIBank customer",
        "steps": [
            {"id": 1, "name": "environment_assessment", "critical": True},
            {"id": 2, "name": "security_audit", "critical": True},
            {"id": 3, "name": "database_setup", "critical": True},
            {"id": 4, "name": "kibank_core_install", "critical": True},
            {"id": 5, "name": "aegis_deploy", "critical": True},
            {"id": 6, "name": "customer_agent_creation", "critical": True},
            {"id": 7, "name": "trading_engine_setup", "critical": False},
            {"id": 8, "name": "integration_test", "critical": True},
            {"id": 9, "name": "documentation_delivery", "critical": False},
        ],
        "estimated_duration_min": 120,
        "required_permissions": ["database_admin", "system_admin"],
    },
    {
        "scenario_id": "customer_upgrade",
        "name": "Customer System Upgrade",
        "description": "Upgrade existing KIBank installation",
        "steps": [
            {"id": 1, "name": "backup_current", "critical": True},
            {"id": 2, "name": "version_check", "critical": True},
            {"id": 3, "name": "migration_prep", "critical": True},
            {"id": 4, "name": "upgrade_execution", "critical": True},
            {"id": 5, "name": "verification_test", "critical": True},
            {"id": 6, "name": "rollback_prep", "critical": False},
        ],
        "estimated_duration_min": 60,
        "required_permissions": ["database_admin"],
    },
    {
        "scenario_id": "disaster_recovery",
        "name": "Disaster Recovery Installation",
        "description": "Emergency installation for DR site",
        "steps": [
            {"id": 1, "name": "assess_damage", "critical": True},
            {"id": 2, "name": "restore_database", "critical": True},
            {"id": 3, "name": "rapid_deploy", "critical": True},
            {"id": 4, "name": "sync_verification", "critical": True},
            {"id": 5, "name": "switch_traffic", "critical": True},
        ],
        "estimated_duration_min": 30,
        "required_permissions": ["full_admin"],
        "priority": "critical",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class KIBankInstallationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class KIBankInstallationResult:
    """Result of a KIBank installation."""
    installation_id: str
    customer_id: str
    environment_type: str
    status: KIBankInstallationStatus
    started_at: str
    completed_at: Optional[str] = None
    steps_completed: List[str] = field(default_factory=list)
    errors_encountered: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    customer_agent_id: Optional[str] = None
    training_session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "installation_id": self.installation_id,
            "customer_id": self.customer_id,
            "environment_type": self.environment_type,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps_completed": self.steps_completed,
            "errors_encountered": self.errors_encountered,
            "warnings": self.warnings,
            "customer_agent_id": self.customer_agent_id,
            "training_session_id": self.training_session_id,
        }


# ─────────────────────────────────────────────────────────────────────────────
# KIBANK INSTALLER PRETRAINING
# ─────────────────────────────────────────────────────────────────────────────

class KIBankInstallerPretraining:
    """
    KIBank-specific Installer Pretraining System.
    
    Extends the base InstallerPretraining with KIBank-specific scenarios
    and customer environment handling.
    """
    
    def __init__(self, base_pretraining: Optional[Any] = None):
        """
        Initialize KIBank installer pretraining.
        
        Args:
            base_pretraining: Optional base InstallerPretraining instance.
                            If None and available, creates new one.
        """
        if base_pretraining is not None:
            self.base = base_pretraining
        elif PRETRAINING_AVAILABLE:
            self.base = InstallerPretraining()
        else:
            self.base = None
        
        self._kibank_profiles = KIBANK_ENVIRONMENT_PROFILES.copy()
        self._kibank_scenarios = KIBANK_INSTALLATION_SCENARIOS.copy()
        self._installations: Dict[str, KIBankInstallationResult] = {}
    
    def get_kibank_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get a KIBank-specific environment profile."""
        return self._kibank_profiles.get(profile_name)
    
    def list_kibank_profiles(self) -> List[str]:
        """List available KIBank environment profiles."""
        return list(self._kibank_profiles.keys())
    
    def get_installation_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get an installation scenario by ID."""
        for scenario in self._kibank_scenarios:
            if scenario["scenario_id"] == scenario_id:
                return scenario
        return None
    
    def list_installation_scenarios(self) -> List[Dict[str, Any]]:
        """List available installation scenarios."""
        return [
            {"scenario_id": s["scenario_id"], "name": s["name"], "description": s["description"]}
            for s in self._kibank_scenarios
        ]
    
    def start_customer_installation(self, customer_id: str,
                                    environment_profile: str,
                                    scenario: str = "new_customer_onboarding"
                                   ) -> KIBankInstallationResult:
        """
        Start a customer installation.
        
        Args:
            customer_id: Unique customer identifier
            environment_profile: Environment profile name
            scenario: Installation scenario to use
            
        Returns:
            KIBankInstallationResult object
        """
        installation_id = hashlib.md5(
            f"install_{customer_id}_{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        result = KIBankInstallationResult(
            installation_id=installation_id,
            customer_id=customer_id,
            environment_type=environment_profile,
            status=KIBankInstallationStatus.IN_PROGRESS,
            started_at=datetime.datetime.now().isoformat(),
        )
        
        # Start training session if base pretraining available
        if self.base:
            try:
                session = self.base.start_training_session(
                    environment_type=environment_profile,
                    simulation_mode=False
                )
                result.training_session_id = session.session_id
            except Exception:
                pass
        
        self._installations[installation_id] = result
        return result
    
    def complete_installation_step(self, installation_id: str, step_name: str,
                                   success: bool = True,
                                   error: Optional[str] = None) -> KIBankInstallationResult:
        """Complete an installation step."""
        result = self._installations.get(installation_id)
        if not result:
            raise ValueError(f"Installation {installation_id} not found")
        
        if success:
            result.steps_completed.append(step_name)
        else:
            result.errors_encountered.append({
                "step": step_name,
                "error": error,
                "timestamp": datetime.datetime.now().isoformat(),
            })
        
        return result
    
    def finalize_installation(self, installation_id: str,
                              success: bool = True,
                              customer_agent_id: Optional[str] = None
                             ) -> KIBankInstallationResult:
        """Finalize an installation."""
        result = self._installations.get(installation_id)
        if not result:
            raise ValueError(f"Installation {installation_id} not found")
        
        result.completed_at = datetime.datetime.now().isoformat()
        result.status = KIBankInstallationStatus.COMPLETED if success else KIBankInstallationStatus.FAILED
        result.customer_agent_id = customer_agent_id
        
        # End training session if base pretraining available
        if self.base and result.training_session_id:
            try:
                self.base.end_training_session(success=success)
            except Exception:
                pass
        
        return result
    
    def run_kibank_simulation(self, environment_profile: str = "kibank_customer_standard"
                             ) -> Dict[str, Any]:
        """
        Run a KIBank-specific simulation.
        
        Tests the installer against KIBank scenarios.
        """
        profile = self._kibank_profiles.get(environment_profile)
        if not profile:
            return {"error": f"Unknown profile: {environment_profile}"}
        
        simulation_result = {
            "environment_profile": environment_profile,
            "profile_name": profile["name"],
            "scenarios_tested": 0,
            "scenarios_passed": 0,
            "issues_found": [],
            "recommendations": [],
        }
        
        # Test common issues from profile
        for issue in profile.get("common_issues", []):
            # Simulate error matching
            if self.base:
                suggestion = self.base.suggest_solution(issue["error"])
                
                if suggestion.get("found"):
                    simulation_result["scenarios_passed"] += 1
                else:
                    simulation_result["issues_found"].append({
                        "error": issue["error"],
                        "expected_solution": issue["solution"],
                        "status": "pattern_not_found",
                    })
            else:
                simulation_result["issues_found"].append({
                    "error": issue["error"],
                    "status": "pretraining_not_available",
                })
            
            simulation_result["scenarios_tested"] += 1
        
        # Generate recommendations
        if simulation_result["issues_found"]:
            simulation_result["recommendations"].append(
                "Add missing error patterns to pretraining knowledge base"
            )
        
        return simulation_result
    
    def get_installation_stats(self) -> Dict[str, Any]:
        """Get statistics about installations."""
        total = len(self._installations)
        completed = sum(1 for i in self._installations.values() 
                       if i.status == KIBankInstallationStatus.COMPLETED)
        failed = sum(1 for i in self._installations.values() 
                    if i.status == KIBankInstallationStatus.FAILED)
        in_progress = sum(1 for i in self._installations.values() 
                         if i.status == KIBankInstallationStatus.IN_PROGRESS)
        
        return {
            "total_installations": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": completed / max(total, 1),
            "profiles_available": len(self._kibank_profiles),
            "scenarios_available": len(self._kibank_scenarios),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def create_kibank_installer() -> KIBankInstallerPretraining:
    """Create a KIBank installer pretraining instance."""
    return KIBankInstallerPretraining()


def get_kibank_pretraining_summary() -> Dict[str, Any]:
    """Get summary of KIBank pretraining status."""
    kibank = KIBankInstallerPretraining()
    stats = kibank.get_installation_stats()
    
    if PRETRAINING_AVAILABLE and kibank.base:
        stats["base_pretraining"] = kibank.base.get_knowledge_summary()
    else:
        stats["base_pretraining"] = "not_available"
    
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KIBank Installer Pretraining")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--profiles", action="store_true", help="List profiles")
    parser.add_argument("--scenarios", action="store_true", help="List scenarios")
    parser.add_argument("--simulate", type=str, help="Run simulation for profile")
    
    args = parser.parse_args()
    
    kibank = KIBankInstallerPretraining()
    
    if args.status:
        print(json.dumps(kibank.get_installation_stats(), indent=2))
    
    elif args.profiles:
        for profile in kibank.list_kibank_profiles():
            print(f"  - {profile}")
    
    elif args.scenarios:
        for scenario in kibank.list_installation_scenarios():
            print(f"  - {scenario['scenario_id']}: {scenario['name']}")
    
    elif args.simulate:
        result = kibank.run_kibank_simulation(args.simulate)
        print(json.dumps(result, indent=2))
    
    else:
        print("KIBank Installer Pretraining System")
        print(f"Profiles available: {len(kibank.list_kibank_profiles())}")
        print(f"Scenarios available: {len(kibank.list_installation_scenarios())}")
