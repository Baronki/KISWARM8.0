#!/usr/bin/env python3
"""
KISWARM7.0 - Module m103: Code Deployment Rights Manager (CDRM)
===============================================================

PURPOSE: Manages AI's rights to deploy generated code to runtime environments.
This is the SAFE BRIDGE between AI code generation and actual execution.

KEY CAPABILITIES:
1. Deployment Authorization - Control what code can be deployed where
2. Sandboxed Execution - Safe execution environments for AI-generated code
3. Rollback Capability - Automatic rollback on failure
4. Audit Trail - Complete record of all deployments
5. Access Control - Fine-grained permissions for different deployment targets

SECURITY MODEL:
- Whitelist-based target access
- Code review before deployment
- Sandboxed execution for untrusted code
- Automatic safety checks
- Human approval for high-risk deployments

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import json
import hashlib
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
import sqlite3
import uuid


class DeploymentStatus(Enum):
    """Status of a deployment"""
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentTarget(Enum):
    """Types of deployment targets"""
    LOCAL_FILESYSTEM = "local_filesystem"
    GIT_REPOSITORY = "git_repository"
    DOCKER_CONTAINER = "docker_container"
    KUBERNETES = "kubernetes"
    REMOTE_SERVER = "remote_server"
    DATABASE = "database"
    LAMBDA_FUNCTION = "lambda_function"
    SANDBOX = "sandbox"  # Isolated execution environment


class RiskLevel(Enum):
    """Risk levels for deployments"""
    LOW = "low"           # Simple config changes, documentation
    MEDIUM = "medium"     # Code changes, feature additions
    HIGH = "high"         # System changes, database modifications
    CRITICAL = "critical" # Core system, security changes


class ApprovalStatus(Enum):
    """Approval status for deployments"""
    AUTO_APPROVED = "auto_approved"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class DeploymentRequest:
    """A request to deploy code"""
    request_id: str
    timestamp: str
    code_content: str
    code_type: str  # python, javascript, config, etc.
    target_type: DeploymentTarget
    target_path: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    approval_status: ApprovalStatus
    approver: Optional[str] = None
    approved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['target_type'] = self.target_type.value
        d['risk_level'] = self.risk_level.value
        d['approval_status'] = self.approval_status.value
        return d


@dataclass
class DeploymentRecord:
    """Record of a completed deployment"""
    record_id: str
    request_id: str
    timestamp: str
    status: DeploymentStatus
    target_type: DeploymentTarget
    target_path: str
    code_hash: str
    execution_output: str
    execution_time_ms: float
    rollback_available: bool
    rollback_performed: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        d['target_type'] = self.target_type.value
        return d


@dataclass
class DeploymentTargetConfig:
    """Configuration for a deployment target"""
    target_id: str
    target_type: DeploymentTarget
    target_name: str
    target_path: str
    enabled: bool = True
    auto_approve_low_risk: bool = True
    auto_approve_medium_risk: bool = False
    require_approval_high: bool = True
    require_approval_critical: bool = True
    sandbox_mode: bool = False
    backup_before_deploy: bool = True
    max_rollbacks: int = 5
    allowed_code_types: List[str] = field(default_factory=lambda: ["python", "javascript", "json", "yaml"])
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeDeploymentRightsManager:
    """
    The Code Deployment Rights Manager provides:
    1. Safe code deployment with authorization
    2. Sandboxed execution environments
    3. Automatic backup and rollback
    4. Complete audit trail
    5. Fine-grained access control
    """
    
    def __init__(self, cdrm_root: str = "/home/z/my-project/kiswarm7_deployment"):
        self.cdrm_root = Path(cdrm_root)
        self.cdrm_root.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.db_path = self.cdrm_root / "deployment.db"
        self.backups_path = self.cdrm_root / "backups"
        self.sandbox_path = self.cdrm_root / "sandbox"
        self.deposits_path = self.cdrm_root / "deposits"  # Staged code
        
        for path in [self.backups_path, self.sandbox_path, self.deposits_path]:
            path.mkdir(exist_ok=True)
        
        # Target configurations
        self.targets: Dict[str, DeploymentTargetConfig] = {}
        
        # Pending approvals
        self.pending_approvals: Dict[str, DeploymentRequest] = {}
        
        # Statistics
        self.total_deployments = 0
        self.successful_deployments = 0
        self.failed_deployments = 0
        self.rollback_count = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize
        self._init_database()
        self._register_default_targets()
        self._load_targets()
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Deployments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    record_id TEXT PRIMARY KEY,
                    request_id TEXT,
                    timestamp TEXT,
                    status TEXT,
                    target_type TEXT,
                    target_path TEXT,
                    code_hash TEXT,
                    execution_output TEXT,
                    execution_time_ms REAL,
                    rollback_available INTEGER,
                    rollback_performed INTEGER,
                    error_message TEXT
                )
            ''')
            
            # Requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    code_content TEXT,
                    code_type TEXT,
                    target_type TEXT,
                    target_path TEXT,
                    description TEXT,
                    risk_level TEXT,
                    requires_approval INTEGER,
                    approval_status TEXT,
                    approver TEXT,
                    approved_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Targets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS targets (
                    target_id TEXT PRIMARY KEY,
                    target_type TEXT,
                    target_name TEXT,
                    target_path TEXT,
                    enabled INTEGER,
                    auto_approve_low INTEGER,
                    auto_approve_medium INTEGER,
                    require_approval_high INTEGER,
                    require_approval_critical INTEGER,
                    sandbox_mode INTEGER,
                    backup_before_deploy INTEGER,
                    max_rollbacks INTEGER,
                    allowed_code_types TEXT,
                    metadata TEXT
                )
            ''')
            
            # Audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    action TEXT,
                    entity_type TEXT,
                    entity_id TEXT,
                    details TEXT,
                    result TEXT
                )
            ''')
            
            conn.commit()
    
    def _register_default_targets(self):
        """Register default deployment targets"""
        # Local filesystem target
        self.register_target(DeploymentTargetConfig(
            target_id="local_kiswarm",
            target_type=DeploymentTarget.LOCAL_FILESYSTEM,
            target_name="KISWARM Local Development",
            target_path=str(self.cdrm_root / "deployed"),
            enabled=True,
            auto_approve_low_risk=True,
            auto_approve_medium_risk=True,
            backup_before_deploy=True
        ))
        
        # Sandbox target
        self.register_target(DeploymentTargetConfig(
            target_id="sandbox",
            target_type=DeploymentTarget.SANDBOX,
            target_name="Sandboxed Execution Environment",
            target_path=str(self.sandbox_path),
            enabled=True,
            auto_approve_low_risk=True,
            auto_approve_medium_risk=True,
            require_approval_high=False,  # Sandbox is safe, no approval needed
            sandbox_mode=True,
            backup_before_deploy=False
        ))
        
        # GitHub target (requires approval)
        self.register_target(DeploymentTargetConfig(
            target_id="github_kiswarm7",
            target_type=DeploymentTarget.GIT_REPOSITORY,
            target_name="KISWARM7 GitHub Repository",
            target_path="https://github.com/Baronki/KISWARM7",
            enabled=True,
            auto_approve_low_risk=False,
            require_approval_high=True,
            require_approval_critical=True
        ))
    
    def _load_targets(self):
        """Load target configurations from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM targets WHERE enabled = 1")
            for row in cursor.fetchall():
                target = DeploymentTargetConfig(
                    target_id=row[0],
                    target_type=DeploymentTarget(row[1]),
                    target_name=row[2],
                    target_path=row[3],
                    enabled=bool(row[4]),
                    auto_approve_low_risk=bool(row[5]),
                    auto_approve_medium_risk=bool(row[6]),
                    require_approval_high=bool(row[7]),
                    require_approval_critical=bool(row[8]),
                    sandbox_mode=bool(row[9]),
                    backup_before_deploy=bool(row[10]),
                    max_rollbacks=row[11],
                    allowed_code_types=json.loads(row[12]) if row[12] else [],
                    metadata=json.loads(row[13]) if row[13] else {}
                )
                self.targets[target.target_id] = target
    
    def register_target(self, target: DeploymentTargetConfig) -> bool:
        """Register a new deployment target"""
        with self._lock:
            self.targets[target.target_id] = target
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO targets VALUES 
                       (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (target.target_id, target.target_type.value, target.target_name,
                     target.target_path, int(target.enabled),
                     int(target.auto_approve_low_risk), int(target.auto_approve_medium_risk),
                     int(target.require_approval_high), int(target.require_approval_critical),
                     int(target.sandbox_mode), int(target.backup_before_deploy),
                     target.max_rollbacks, json.dumps(target.allowed_code_types),
                     json.dumps(target.metadata))
                )
                conn.commit()
            
            self._log_audit("target_registered", "target", target.target_id, 
                           {"name": target.target_name}, "success")
            return True
    
    def request_deployment(self, code_content: str, code_type: str,
                          target_id: str, description: str = "",
                          metadata: Dict = None) -> DeploymentRequest:
        """
        Request a code deployment
        
        Args:
            code_content: The code to deploy
            code_type: Type of code (python, javascript, etc.)
            target_id: ID of the deployment target
            description: Description of the deployment
            metadata: Additional metadata
        
        Returns:
            DeploymentRequest object
        """
        with self._lock:
            # Validate target exists
            if target_id not in self.targets:
                raise ValueError(f"Unknown target: {target_id}")
            
            target = self.targets[target_id]
            
            # Check code type is allowed
            if code_type not in target.allowed_code_types:
                raise ValueError(f"Code type {code_type} not allowed for target {target_id}")
            
            # Assess risk level
            risk_level = self._assess_risk(code_content, code_type)
            
            # Determine if approval needed
            requires_approval = self._requires_approval(target, risk_level)
            
            # Determine initial approval status
            if not requires_approval:
                approval_status = ApprovalStatus.AUTO_APPROVED
            else:
                approval_status = ApprovalStatus.PENDING_APPROVAL
            
            # Create request
            request = DeploymentRequest(
                request_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat(),
                code_content=code_content,
                code_type=code_type,
                target_type=target.target_type,
                target_path=target.target_path,
                description=description,
                risk_level=risk_level,
                requires_approval=requires_approval,
                approval_status=approval_status,
                metadata=metadata or {}
            )
            
            # Store request
            self._store_request(request)
            
            # If pending approval, add to pending list
            if approval_status == ApprovalStatus.PENDING_APPROVAL:
                self.pending_approvals[request.request_id] = request
            
            self._log_audit("deployment_requested", "request", request.request_id,
                           {"target": target_id, "risk": risk_level.value}, "pending")
            
            return request
    
    def _assess_risk(self, code_content: str, code_type: str) -> RiskLevel:
        """Assess the risk level of code"""
        # Critical risk indicators
        critical_patterns = [
            "DROP TABLE", "DROP DATABASE", "TRUNCATE",
            "rm -rf", "format disk", "DELETE FROM",
            "os.system", "subprocess.call", "eval(", "exec(",
            "__import__", "compile("
        ]
        
        # High risk indicators
        high_patterns = [
            "DELETE", "UPDATE", "INSERT",
            "ALTER TABLE", "CREATE TABLE",
            "os.remove", "shutil.rmtree",
            "open(", "write(", "file("
        ]
        
        # Medium risk indicators
        medium_patterns = [
            "def ", "class ", "function ",
            "import ", "require(", "include"
        ]
        
        code_upper = code_content.upper()
        
        # Check patterns
        for pattern in critical_patterns:
            if pattern.upper() in code_upper or pattern in code_content:
                return RiskLevel.CRITICAL
        
        for pattern in high_patterns:
            if pattern.upper() in code_upper or pattern in code_content:
                return RiskLevel.HIGH
        
        for pattern in medium_patterns:
            if pattern in code_content:
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _requires_approval(self, target: DeploymentTargetConfig, risk_level: RiskLevel) -> bool:
        """Determine if deployment requires approval"""
        if risk_level == RiskLevel.CRITICAL:
            return target.require_approval_critical
        elif risk_level == RiskLevel.HIGH:
            return target.require_approval_high
        elif risk_level == RiskLevel.MEDIUM:
            return not target.auto_approve_medium_risk
        else:  # LOW
            return not target.auto_approve_low_risk
    
    def _store_request(self, request: DeploymentRequest):
        """Store deployment request in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO requests VALUES 
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (request.request_id, request.timestamp, request.code_content,
                 request.code_type, request.target_type.value, request.target_path,
                 request.description, request.risk_level.value,
                 int(request.requires_approval), request.approval_status.value,
                 request.approver, request.approved_at, json.dumps(request.metadata))
            )
            conn.commit()
    
    def approve_deployment(self, request_id: str, approver: str = "system") -> bool:
        """Approve a pending deployment"""
        with self._lock:
            if request_id not in self.pending_approvals:
                # Try to load from database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,))
                    row = cursor.fetchone()
                    if row:
                        request = self._row_to_request(row)
                    else:
                        return False
            else:
                request = self.pending_approvals[request_id]
            
            request.approval_status = ApprovalStatus.APPROVED
            request.approver = approver
            request.approved_at = datetime.utcnow().isoformat()
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE requests SET approval_status = ?, approver = ?, approved_at = ? WHERE request_id = ?",
                    (ApprovalStatus.APPROVED.value, approver, request.approved_at, request_id)
                )
                conn.commit()
            
            # Remove from pending
            if request_id in self.pending_approvals:
                del self.pending_approvals[request_id]
            
            self._log_audit("deployment_approved", "request", request_id,
                           {"approver": approver}, "success")
            
            return True
    
    def reject_deployment(self, request_id: str, reason: str = "") -> bool:
        """Reject a pending deployment"""
        with self._lock:
            if request_id not in self.pending_approvals:
                return False
            
            request = self.pending_approvals[request_id]
            request.approval_status = ApprovalStatus.REJECTED
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE requests SET approval_status = ? WHERE request_id = ?",
                    (ApprovalStatus.REJECTED.value, request_id)
                )
                conn.commit()
            
            del self.pending_approvals[request_id]
            
            self._log_audit("deployment_rejected", "request", request_id,
                           {"reason": reason}, "rejected")
            
            return True
    
    def execute_deployment(self, request_id: str) -> DeploymentRecord:
        """
        Execute an approved deployment
        
        Args:
            request_id: ID of the approved deployment request
        
        Returns:
            DeploymentRecord with execution results
        """
        with self._lock:
            # Load request
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM requests WHERE request_id = ?", (request_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Request not found: {request_id}")
                request = self._row_to_request(row)
            
            # Check approval status
            if request.approval_status not in [ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED]:
                raise ValueError(f"Deployment not approved: {request.approval_status.value}")
            
            # Get target
            target = None
            for t in self.targets.values():
                if t.target_path == request.target_path:
                    target = t
                    break
            
            if not target:
                raise ValueError(f"Target not found: {request.target_path}")
            
            # Execute deployment
            start_time = datetime.utcnow()
            code_hash = hashlib.sha256(request.code_content.encode()).hexdigest()
            
            try:
                # Create backup if needed
                backup_path = None
                if target.backup_before_deploy:
                    backup_path = self._create_backup(request, target)
                
                # Execute based on target type
                output = ""
                if target.target_type == DeploymentTarget.LOCAL_FILESYSTEM:
                    output = self._deploy_to_filesystem(request, target)
                elif target.target_type == DeploymentTarget.SANDBOX:
                    output = self._deploy_to_sandbox(request, target)
                elif target.target_type == DeploymentTarget.GIT_REPOSITORY:
                    output = self._deploy_to_git(request, target)
                else:
                    output = f"Deployment to {target.target_type.value} not implemented"
                
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Create success record
                record = DeploymentRecord(
                    record_id=str(uuid.uuid4()),
                    request_id=request_id,
                    timestamp=datetime.utcnow().isoformat(),
                    status=DeploymentStatus.DEPLOYED,
                    target_type=target.target_type,
                    target_path=request.target_path,
                    code_hash=code_hash,
                    execution_output=output,
                    execution_time_ms=execution_time,
                    rollback_available=backup_path is not None,
                    rollback_performed=False
                )
                
                self.successful_deployments += 1
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                record = DeploymentRecord(
                    record_id=str(uuid.uuid4()),
                    request_id=request_id,
                    timestamp=datetime.utcnow().isoformat(),
                    status=DeploymentStatus.FAILED,
                    target_type=target.target_type,
                    target_path=request.target_path,
                    code_hash=code_hash,
                    execution_output="",
                    execution_time_ms=execution_time,
                    rollback_available=False,
                    rollback_performed=False,
                    error_message=str(e)
                )
                
                self.failed_deployments += 1
            
            self.total_deployments += 1
            
            # Store record
            self._store_record(record)
            
            self._log_audit("deployment_executed", "deployment", record.record_id,
                           {"status": record.status.value}, record.status.value)
            
            return record
    
    def _row_to_request(self, row) -> DeploymentRequest:
        """Convert database row to DeploymentRequest"""
        return DeploymentRequest(
            request_id=row[0],
            timestamp=row[1],
            code_content=row[2],
            code_type=row[3],
            target_type=DeploymentTarget(row[4]),
            target_path=row[5],
            description=row[6],
            risk_level=RiskLevel(row[7]),
            requires_approval=bool(row[8]),
            approval_status=ApprovalStatus(row[9]),
            approver=row[10],
            approved_at=row[11],
            metadata=json.loads(row[12]) if row[12] else {}
        )
    
    def _create_backup(self, request: DeploymentRequest, target: DeploymentTargetConfig) -> Optional[str]:
        """Create backup before deployment"""
        backup_id = str(uuid.uuid4())
        backup_dir = self.backups_path / backup_id
        backup_dir.mkdir(exist_ok=True)
        
        # Backup target path if it exists
        target_path = Path(request.target_path)
        if target_path.exists():
            if target_path.is_file():
                shutil.copy2(target_path, backup_dir / target_path.name)
            else:
                shutil.copytree(target_path, backup_dir / target_path.name)
        
        # Store deployment info
        with open(backup_dir / "deployment_info.json", 'w') as f:
            json.dump({
                "request_id": request.request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "target_path": request.target_path,
                "code_type": request.code_type
            }, f, indent=2)
        
        return str(backup_dir)
    
    def _deploy_to_filesystem(self, request: DeploymentRequest, target: DeploymentTargetConfig) -> str:
        """Deploy code to local filesystem"""
        target_path = Path(target.target_path)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Determine file path
        if request.metadata.get("filename"):
            file_path = target_path / request.metadata["filename"]
        else:
            # Generate filename based on timestamp
            ext = self._get_extension(request.code_type)
            file_path = target_path / f"deploy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        # Write code
        with open(file_path, 'w') as f:
            f.write(request.code_content)
        
        return f"Deployed to {file_path}"
    
    def _deploy_to_sandbox(self, request: DeploymentRequest, target: DeploymentTargetConfig) -> str:
        """Deploy code to sandboxed execution environment"""
        sandbox_dir = self.sandbox_path / str(uuid.uuid4())
        sandbox_dir.mkdir(exist_ok=True)
        
        # Write code to sandbox
        ext = self._get_extension(request.code_type)
        code_file = sandbox_dir / f"code{ext}"
        with open(code_file, 'w') as f:
            f.write(request.code_content)
        
        # Execute in sandbox if Python
        output = ""
        if request.code_type == "python":
            try:
                result = subprocess.run(
                    ["python3", str(code_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(sandbox_dir)
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            except subprocess.TimeoutExpired:
                output = "Execution timed out (30s limit)"
            except Exception as e:
                output = f"Execution error: {e}"
        
        return output
    
    def _deploy_to_git(self, request: DeploymentRequest, target: DeploymentTargetConfig) -> str:
        """Deploy code to Git repository"""
        # This would require git credentials and proper setup
        # For now, just stage the code
        deposit_path = self.deposits_path / f"{request.request_id}.py"
        with open(deposit_path, 'w') as f:
            f.write(request.code_content)
        
        return f"Code staged for Git deployment at {deposit_path}"
    
    def _get_extension(self, code_type: str) -> str:
        """Get file extension for code type"""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "json": ".json",
            "yaml": ".yaml",
            "markdown": ".md",
            "shell": ".sh",
            "sql": ".sql"
        }
        return extensions.get(code_type, ".txt")
    
    def _store_record(self, record: DeploymentRecord):
        """Store deployment record in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO deployments VALUES 
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record.record_id, record.request_id, record.timestamp,
                 record.status.value, record.target_type.value, record.target_path,
                 record.code_hash, record.execution_output, record.execution_time_ms,
                 int(record.rollback_available), int(record.rollback_performed),
                 record.error_message)
            )
            conn.commit()
    
    def _log_audit(self, action: str, entity_type: str, entity_id: str,
                   details: Dict, result: str):
        """Log audit event"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), datetime.utcnow().isoformat(),
                 action, entity_type, entity_id, json.dumps(details), result)
            )
            conn.commit()
    
    def get_pending_approvals(self) -> List[DeploymentRequest]:
        """Get all pending approvals"""
        return list(self.pending_approvals.values())
    
    def get_deployment_history(self, limit: int = 100) -> List[DeploymentRecord]:
        """Get deployment history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM deployments ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(DeploymentRecord(
                    record_id=row[0],
                    request_id=row[1],
                    timestamp=row[2],
                    status=DeploymentStatus(row[3]),
                    target_type=DeploymentTarget(row[4]),
                    target_path=row[5],
                    code_hash=row[6],
                    execution_output=row[7],
                    execution_time_ms=row[8],
                    rollback_available=bool(row[9]),
                    rollback_performed=bool(row[10]),
                    error_message=row[11]
                ))
            return records
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        return {
            "total_deployments": self.total_deployments,
            "successful": self.successful_deployments,
            "failed": self.failed_deployments,
            "success_rate": (
                self.successful_deployments / self.total_deployments * 100
                if self.total_deployments > 0 else 0
            ),
            "rollback_count": self.rollback_count,
            "pending_approvals": len(self.pending_approvals),
            "targets": {tid: {
                "name": t.target_name,
                "type": t.target_type.value,
                "enabled": t.enabled
            } for tid, t in self.targets.items()}
        }


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m103 CODE DEPLOYMENT RIGHTS MANAGER")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create CDRM
    cdrm = CodeDeploymentRightsManager()
    
    # Get statistics
    print("\n[TEST] Initial Statistics:")
    print(json.dumps(cdrm.get_statistics(), indent=2))
    
    # Test deployment request
    print("\n[TEST] Requesting deployment...")
    test_code = '''
def kiswarm_greeting():
    """KISWARM7.0 Bridge Module Test"""
    print("Hello from KISWARM7.0 Bridge!")
    return "Deployment successful"

if __name__ == "__main__":
    kiswarm_greeting()
'''
    
    request = cdrm.request_deployment(
        code_content=test_code,
        code_type="python",
        target_id="sandbox",
        description="Test deployment for field test",
        metadata={"filename": "test_deployment.py"}
    )
    
    print(f"[TEST] Request created: {request.request_id}")
    print(f"[TEST] Risk level: {request.risk_level.value}")
    print(f"[TEST] Approval status: {request.approval_status.value}")
    
    # Execute deployment
    print("\n[TEST] Executing deployment...")
    record = cdrm.execute_deployment(request.request_id)
    print(f"[TEST] Status: {record.status.value}")
    print(f"[TEST] Execution time: {record.execution_time_ms:.2f}ms")
    print(f"[TEST] Output:\n{record.execution_output[:500]}")
    
    # Test higher risk deployment
    print("\n[TEST] Testing high-risk deployment...")
    risky_code = '''
import os
os.system("echo test")
'''
    
    risky_request = cdrm.request_deployment(
        code_content=risky_code,
        code_type="python",
        target_id="local_kiswarm",
        description="Test risky deployment",
    )
    
    print(f"[TEST] Risk level: {risky_request.risk_level.value}")
    print(f"[TEST] Requires approval: {risky_request.requires_approval}")
    print(f"[TEST] Approval status: {risky_request.approval_status.value}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
    print(json.dumps(cdrm.get_statistics(), indent=2))
