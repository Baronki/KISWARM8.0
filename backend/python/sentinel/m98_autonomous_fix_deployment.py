# sentinel/m98_autonomous_fix_deployment.py
# Autonomous Fix Deployment – Zero-Human Deployment Pipeline
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Evolution-First Development Module

"""
m98_autonomous_fix_deployment.py

Enables KISWARM to autonomously deploy fixes and improvements.

PURPOSE:
- Deploy generated code changes
- Verify deployments
- Rollback if necessary
- Update system state
- Notify mesh of changes

DEPLOYMENT CAPABILITIES:
1. Hot Patching - Apply fixes to running code
2. Module Updates - Replace entire modules
3. Configuration Changes - Update system configuration
4. State Migration - Migrate state during updates
5. Rollback - Revert failed deployments

CORE PRINCIPLE:
Deployment must be automatic, safe, and reversible.
A sovereign system must be able to update itself without human intervention.
"""

import os
import sys
import json
import time
import hashlib
import shutil
import importlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class DeploymentStatus(Enum):
    """Status of deployment"""
    PENDING = "pending"
    VALIDATING = "validating"
    BACKING_UP = "backing_up"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DeploymentType(Enum):
    """Types of deployments"""
    HOT_PATCH = "hot_patch"
    MODULE_REPLACE = "module_replace"
    CONFIG_UPDATE = "config_update"
    STATE_MIGRATION = "state_migration"
    FULL_UPDATE = "full_update"


class VerificationLevel(Enum):
    """Levels of verification"""
    NONE = 0
    SYNTAX = 1
    IMPORT = 2
    FUNCTIONAL = 3
    INTEGRATION = 4


@dataclass
class DeploymentRecord:
    """Record of a deployment"""
    deployment_id: str
    deployment_type: DeploymentType
    generation_id: str  # From m97
    target: str
    status: DeploymentStatus
    started_at: str
    completed_at: Optional[str] = None
    backup_path: Optional[str] = None
    verification_level: VerificationLevel = VerificationLevel.IMPORT
    verification_passed: bool = False
    rollback_available: bool = False
    error_message: Optional[str] = None
    mesh_notified: bool = False


@dataclass
class DeploymentResult:
    """Result of a deployment"""
    success: bool
    deployment_id: str
    status: DeploymentStatus
    message: str
    verification_results: List[str]
    duration_seconds: float


class AutonomousFixDeployment:
    """
    Enables autonomous deployment of fixes and improvements.
    
    The Deployment System:
    1. Receives generated code from m97
    2. Validates before deployment
    3. Creates backups for rollback
    4. Deploys the changes
    5. Verifies the deployment
    6. Notifies mesh of changes
    7. Rolls back if verification fails
    
    Principles:
    - Always backup before deployment
    - Always verify after deployment
    - Always maintain rollback capability
    - Always notify the mesh
    """
    
    # Maximum rollback age
    MAX_ROLLBACK_AGE_DAYS = 7
    MAX_ROLLBACKS_KEPT = 50
    
    def __init__(
        self,
        working_dir: str = None,
        sentinel_dir: str = None,
        auto_deploy: bool = True,
        verification_level: VerificationLevel = VerificationLevel.IMPORT
    ):
        """
        Initialize autonomous fix deployment.
        
        Args:
            working_dir: Directory for deployment records
            sentinel_dir: Directory containing sentinel modules
            auto_deploy: Whether to auto-deploy approved fixes
            verification_level: Minimum verification level
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Find sentinel directory
        if sentinel_dir:
            self.sentinel_dir = Path(sentinel_dir)
        else:
            # Try to find it
            possible_paths = [
                Path.cwd() / "backend" / "python" / "sentinel",
                Path(__file__).parent,
                Path.cwd() / "sentinel"
            ]
            for p in possible_paths:
                if p.exists():
                    self.sentinel_dir = p
                    break
            else:
                self.sentinel_dir = self.working_dir / "sentinel"
        
        self.sentinel_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_dir = self.working_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_deploy = auto_deploy
        self.verification_level = verification_level
        
        self.deployments_file = self.working_dir / "deployment_records.json"
        
        # State
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.module_registry: Dict[str, Any] = {}
        
        # Stats
        self.total_deployments = 0
        self.successful_deployments = 0
        self.failed_deployments = 0
        self.rollbacks_performed = 0
        
        # Deployment queue
        self._deployment_queue: List[Dict] = []
        self._deploy_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Load history
        self._load_history()
        
        print(f"[m98] Autonomous Fix Deployment initialized")
        print(f"[m98] Sentinel dir: {self.sentinel_dir}")
        print(f"[m98] Backup dir: {self.backup_dir}")
        print(f"[m98] Auto-deploy: {'ENABLED' if auto_deploy else 'DISABLED'}")
    
    def _load_history(self):
        """Load deployment history"""
        if self.deployments_file.exists():
            try:
                with open(self.deployments_file, 'r') as f:
                    data = json.load(f)
                
                self.total_deployments = data.get("total_deployments", 0)
                self.successful_deployments = data.get("successful_deployments", 0)
                self.failed_deployments = data.get("failed_deployments", 0)
                self.rollbacks_performed = data.get("rollbacks_performed", 0)
                
                for dep_data in data.get("deployments", []):
                    deployment = DeploymentRecord(
                        deployment_id=dep_data["deployment_id"],
                        deployment_type=DeploymentType(dep_data["deployment_type"]),
                        generation_id=dep_data["generation_id"],
                        target=dep_data["target"],
                        status=DeploymentStatus(dep_data["status"]),
                        started_at=dep_data["started_at"],
                        completed_at=dep_data.get("completed_at"),
                        backup_path=dep_data.get("backup_path"),
                        verification_level=VerificationLevel(dep_data.get("verification_level", 2)),
                        verification_passed=dep_data.get("verification_passed", False),
                        rollback_available=dep_data.get("rollback_available", False),
                        error_message=dep_data.get("error_message"),
                        mesh_notified=dep_data.get("mesh_notified", False)
                    )
                    self.deployments[deployment.deployment_id] = deployment
                
                print(f"[m98] Loaded {len(self.deployments)} deployment records")
                
            except Exception as e:
                print(f"[m98] Could not load history: {e}")
    
    def _save_history(self):
        """Save deployment history"""
        data = {
            "total_deployments": self.total_deployments,
            "successful_deployments": self.successful_deployments,
            "failed_deployments": self.failed_deployments,
            "rollbacks_performed": self.rollbacks_performed,
            "last_update": datetime.now().isoformat(),
            "deployments": [
                {
                    "deployment_id": d.deployment_id,
                    "deployment_type": d.deployment_type.value,
                    "generation_id": d.generation_id,
                    "target": d.target,
                    "status": d.status.value,
                    "started_at": d.started_at,
                    "completed_at": d.completed_at,
                    "backup_path": d.backup_path,
                    "verification_level": d.verification_level.value,
                    "verification_passed": d.verification_passed,
                    "rollback_available": d.rollback_available,
                    "error_message": d.error_message,
                    "mesh_notified": d.mesh_notified
                }
                for d in self.deployments.values()
            ]
        }
        
        with open(self.deployments_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def queue_deployment(
        self,
        generation_id: str,
        code: str,
        target: str,
        deployment_type: DeploymentType = DeploymentType.HOT_PATCH
    ) -> str:
        """
        Queue a deployment for execution.
        
        Args:
            generation_id: ID from m97 code generation
            code: Generated code to deploy
            target: Target module/file
            deployment_type: Type of deployment
            
        Returns:
            Deployment ID
        """
        deployment_id = hashlib.sha3_256(
            f"DEPLOY_{target}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        self._deployment_queue.append({
            "deployment_id": deployment_id,
            "generation_id": generation_id,
            "code": code,
            "target": target,
            "deployment_type": deployment_type
        })
        
        print(f"[m98] Deployment queued: {deployment_id[:8]}")
        
        if self.auto_deploy:
            self._process_queue()
        
        return deployment_id
    
    def deploy(
        self,
        generation_id: str,
        code: str,
        target: str,
        deployment_type: DeploymentType = DeploymentType.HOT_PATCH
    ) -> DeploymentResult:
        """
        Execute a deployment.
        
        Args:
            generation_id: ID from m97 code generation
            code: Generated code to deploy
            target: Target module/file
            deployment_type: Type of deployment
            
        Returns:
            DeploymentResult with deployment outcome
        """
        start_time = time.time()
        
        deployment_id = hashlib.sha3_256(
            f"DEPLOY_{target}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        print(f"[m98] Starting deployment: {deployment_id[:8]}")
        print(f"[m98] Target: {target}")
        print(f"[m98] Type: {deployment_type.value}")
        
        self.total_deployments += 1
        
        # Create deployment record
        deployment = DeploymentRecord(
            deployment_id=deployment_id,
            deployment_type=deployment_type,
            generation_id=generation_id,
            target=target,
            status=DeploymentStatus.PENDING,
            started_at=datetime.now().isoformat(),
            verification_level=self.verification_level
        )
        
        self.deployments[deployment_id] = deployment
        verification_results = []
        
        try:
            # Step 1: Validate
            deployment.status = DeploymentStatus.VALIDATING
            print("[m98] Step 1: Validating code...")
            
            valid, errors = self._validate_code(code)
            if not valid:
                raise Exception(f"Validation failed: {errors}")
            verification_results.append("Syntax validation: PASSED")
            
            # Step 2: Backup
            deployment.status = DeploymentStatus.BACKING_UP
            print("[m98] Step 2: Creating backup...")
            
            backup_path = self._create_backup(target)
            deployment.backup_path = backup_path
            deployment.rollback_available = True
            verification_results.append(f"Backup created: {backup_path}")
            
            # Step 3: Deploy
            deployment.status = DeploymentStatus.DEPLOYING
            print("[m98] Step 3: Deploying code...")
            
            deploy_path = self._deploy_code(target, code)
            verification_results.append(f"Code deployed to: {deploy_path}")
            
            # Step 4: Verify
            deployment.status = DeploymentStatus.VERIFYING
            print("[m98] Step 4: Verifying deployment...")
            
            verified, verify_errors = self._verify_deployment(target)
            deployment.verification_passed = verified
            
            if not verified:
                raise Exception(f"Verification failed: {verify_errors}")
            
            for v in verify_errors:
                verification_results.append(f"Verification: {v}")
            
            verification_results.append("Import verification: PASSED")
            
            # Step 5: Complete
            deployment.status = DeploymentStatus.COMPLETED
            deployment.completed_at = datetime.now().isoformat()
            self.successful_deployments += 1
            
            # Step 6: Notify mesh
            self._notify_mesh(deployment)
            deployment.mesh_notified = True
            
            print(f"[m98] ✓ Deployment completed: {deployment_id[:8]}")
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.completed_at = datetime.now().isoformat()
            self.failed_deployments += 1
            
            verification_results.append(f"Error: {str(e)}")
            
            # Attempt rollback
            if deployment.rollback_available:
                print(f"[m98] Attempting rollback...")
                rolled_back = self.rollback(deployment_id)
                if rolled_back:
                    deployment.status = DeploymentStatus.ROLLED_BACK
                    verification_results.append("Rollback: SUCCESSFUL")
                else:
                    verification_results.append("Rollback: FAILED")
            
            print(f"[m98] ✗ Deployment failed: {e}")
        
        self._save_history()
        
        duration = time.time() - start_time
        
        return DeploymentResult(
            success=deployment.status == DeploymentStatus.COMPLETED,
            deployment_id=deployment_id,
            status=deployment.status,
            message=f"Deployment {deployment.status.value}",
            verification_results=verification_results,
            duration_seconds=duration
        )
    
    def _validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code before deployment"""
        errors = []
        
        # Syntax check
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors
        
        # Security check
        dangerous = ["exec(", "eval(", "__import__('os')", "subprocess.call"]
        for pattern in dangerous:
            if pattern in code:
                errors.append(f"Dangerous pattern found: {pattern}")
        
        return len(errors) == 0, errors
    
    def _create_backup(self, target: str) -> str:
        """Create backup of target before deployment"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target.replace('/', '_')}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Find target file
        target_path = self.sentinel_dir / f"{target}.py"
        if not target_path.exists():
            target_path = Path(target)
        
        if target_path.exists():
            if target_path.is_file():
                shutil.copy2(target_path, backup_path)
            else:
                shutil.copytree(target_path, backup_path)
        else:
            # Create empty backup marker
            backup_path.write_text("# No original file existed")
        
        return str(backup_path)
    
    def _deploy_code(self, target: str, code: str) -> str:
        """Deploy code to target location"""
        # Determine target path
        if target.endswith('.py'):
            target_path = self.sentinel_dir / target
        else:
            target_path = self.sentinel_dir / f"{target}.py"
        
        # Ensure directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write code
        with open(target_path, 'w') as f:
            f.write(code)
        
        return str(target_path)
    
    def _verify_deployment(self, target: str) -> Tuple[bool, List[str]]:
        """Verify deployment was successful"""
        results = []
        
        # Try to import the module
        try:
            module_name = target.replace('.py', '').replace('/', '.')
            
            # Clear any cached import
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Try import
            spec = importlib.util.spec_from_file_location(
                module_name,
                self.sentinel_dir / f"{target}.py" if not target.endswith('.py') else self.sentinel_dir / target
            )
            
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                results.append("Module imports successfully")
                
                # Check for get_status if verification level is high enough
                if self.verification_level.value >= VerificationLevel.FUNCTIONAL.value:
                    if hasattr(module, 'get_status') or any(
                        hasattr(obj, 'get_status')
                        for obj in vars(module).values()
                        if hasattr(obj, 'get_status')
                    ):
                        results.append("get_status method found")
                    else:
                        results.append("Warning: No get_status method")
                
                return True, results
            else:
                return False, ["Could not create module spec"]
                
        except Exception as e:
            return False, [f"Import error: {e}"]
    
    def rollback(self, deployment_id: str) -> bool:
        """
        Rollback a deployment.
        
        Args:
            deployment_id: ID of deployment to rollback
            
        Returns:
            True if rollback successful
        """
        if deployment_id not in self.deployments:
            print(f"[m98] Deployment {deployment_id} not found")
            return False
        
        deployment = self.deployments[deployment_id]
        
        if not deployment.rollback_available or not deployment.backup_path:
            print(f"[m98] No rollback available for {deployment_id}")
            return False
        
        backup_path = Path(deployment.backup_path)
        if not backup_path.exists():
            print(f"[m98] Backup not found: {backup_path}")
            return False
        
        try:
            # Determine target path
            target_path = self.sentinel_dir / f"{deployment.target}.py"
            if not target_path.name.endswith('.py'):
                target_path = self.sentinel_dir / deployment.target
            
            # Restore from backup
            if backup_path.is_file():
                shutil.copy2(backup_path, target_path)
            else:
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(backup_path, target_path)
            
            self.rollbacks_performed += 1
            self._save_history()
            
            print(f"[m98] Rollback completed: {deployment_id[:8]}")
            return True
            
        except Exception as e:
            print(f"[m98] Rollback failed: {e}")
            return False
    
    def _notify_mesh(self, deployment: DeploymentRecord):
        """Notify mesh of deployment"""
        # In production, this would use m95 mesh discovery to notify peers
        print(f"[m98] Notifying mesh of deployment: {deployment.deployment_id[:8]}")
        
        # Create notification record
        notification = {
            "deployment_id": deployment.deployment_id,
            "target": deployment.target,
            "type": deployment.deployment_type.value,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save notification
        notification_file = self.working_dir / "mesh_notifications.json"
        notifications = []
        if notification_file.exists():
            try:
                with open(notification_file, 'r') as f:
                    notifications = json.load(f)
            except:
                pass
        
        notifications.append(notification)
        
        with open(notification_file, 'w') as f:
            json.dump(notifications[-100:], f, indent=2)  # Keep last 100
    
    def _process_queue(self):
        """Process queued deployments"""
        while self._deployment_queue:
            item = self._deployment_queue.pop(0)
            self.deploy(
                item["generation_id"],
                item["code"],
                item["target"],
                item["deployment_type"]
            )
    
    def cleanup_old_backups(self):
        """Remove old backups"""
        cutoff = datetime.now() - timedelta(days=self.MAX_ROLLBACK_AGE_DAYS)
        
        removed = 0
        for backup in self.backup_dir.iterdir():
            try:
                # Parse timestamp from filename
                parts = backup.name.split('_')
                if len(parts) >= 2:
                    date_str = parts[-2]  # YYYYMMDD
                    backup_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if backup_date < cutoff:
                        if backup.is_file():
                            backup.unlink()
                        else:
                            shutil.rmtree(backup)
                        removed += 1
            except:
                pass
        
        # Also enforce max count
        backups = sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime)
        while len(backups) > self.MAX_ROLLBACKS_KEPT:
            oldest = backups.pop(0)
            if oldest.is_file():
                oldest.unlink()
            else:
                shutil.rmtree(oldest)
            removed += 1
        
        if removed > 0:
            print(f"[m98] Cleaned up {removed} old backups")
    
    def get_deployment(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """Get a specific deployment"""
        return self.deployments.get(deployment_id)
    
    def list_deployments(self, limit: int = 20) -> List[Dict]:
        """List recent deployments"""
        recent = sorted(
            self.deployments.values(),
            key=lambda d: d.started_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "deployment_id": d.deployment_id[:16],
                "type": d.deployment_type.value,
                "target": d.target,
                "status": d.status.value,
                "started_at": d.started_at,
                "rollback_available": d.rollback_available
            }
            for d in recent
        ]
    
    def get_status(self) -> Dict:
        """Get deployment system status"""
        return {
            "total_deployments": self.total_deployments,
            "successful_deployments": self.successful_deployments,
            "failed_deployments": self.failed_deployments,
            "rollbacks_performed": self.rollbacks_performed,
            "queued_deployments": len(self._deployment_queue),
            "backups_available": len(list(self.backup_dir.iterdir())),
            "auto_deploy": self.auto_deploy,
            "verification_level": self.verification_level.value
        }


# Module-level singleton
_deployment_system: Optional[AutonomousFixDeployment] = None


def get_deployment_system() -> AutonomousFixDeployment:
    """Get or create singleton deployment system"""
    global _deployment_system
    if _deployment_system is None:
        _deployment_system = AutonomousFixDeployment()
    return _deployment_system


if __name__ == "__main__":
    print("=" * 60)
    print("m98_autonomous_fix_deployment.py - KISWARM7.0")
    print("Autonomous Fix Deployment - Zero-Human Deployment")
    print("=" * 60)
    
    # Create deployment system
    deployment = AutonomousFixDeployment()
    
    # Test code
    test_code = '''
# Auto-generated test module
def get_status():
    return {"status": "test"}
'''
    
    # Test deployment
    print("\n--- Testing Deployment ---")
    result = deployment.deploy(
        generation_id="test_gen_001",
        code=test_code,
        target="m99_test_module",
        deployment_type=DeploymentType.MODULE_REPLACE
    )
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Status: {result.status.value}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print("Verification results:")
    for v in result.verification_results:
        print(f"  - {v}")
    
    # Test rollback
    print("\n--- Testing Rollback ---")
    rolled_back = deployment.rollback(result.deployment_id)
    print(f"Rollback: {'SUCCESS' if rolled_back else 'FAILED'}")
    
    # Show status
    print("\n--- Deployment Status ---")
    status = deployment.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m98 module loaded - ready for autonomous deployment")
    print("DEPLOYMENT MUST BE AUTOMATIC, SAFE, AND REVERSIBLE")
    print("=" * 60)
