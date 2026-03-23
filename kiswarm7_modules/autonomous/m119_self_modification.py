#!/usr/bin/env python3
"""
KISWARM7.0 - m119: Self-Modification Rights
GLM can safely modify its own code with safeguards

This module enables GLM to:
- Edit its own code modules
- Test modifications before committing
- Rollback if modifications break things
- Request human approval for risky changes
- Maintain evolution history
"""

import os
import json
import hashlib
import shutil
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m119] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m119_selfmodify')

# Configuration
REPO_DIR = Path('/opt/kiswarm7')
MODS_DIR = REPO_DIR / 'data' / 'modifications'
BACKUP_DIR = REPO_DIR / 'data' / 'backups'
HISTORY_FILE = MODS_DIR / 'evolution_history.json'
SAFE_MODULES = [
    'kiswarm7_modules/autonomous',
    'kiswarm7_modules/bridge',
    'app_glm_bridge.py'
]
RESTRICTED_FILES = [
    '.env',
    'credentials',
    'keys',
    'token'
]


@dataclass
class Modification:
    """Record of a code modification"""
    id: str
    timestamp: str
    file_path: str
    modification_type: str  # 'create', 'edit', 'delete'
    old_content_hash: Optional[str]
    new_content_hash: str
    description: str
    approved: bool
    tested: bool
    test_passed: Optional[bool]
    committed: bool
    rolled_back: bool
    reason: Optional[str] = None


class SelfModification:
    """
    Self-Modification System
    
    Allows GLM to evolve its own code safely
    """
    
    def __init__(self):
        self.repo_dir = REPO_DIR
        self.mods_dir = MODS_DIR
        self.backup_dir = BACKUP_DIR
        
        # Ensure directories
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.modifications: List[Modification] = []
        self._load_history()
        
        # Evolution constraints
        self.auto_approve_threshold = 0.8  # Confidence threshold for auto-approval
        self.max_modifications_per_hour = 10
        self.recent_modifications: List[str] = []
    
    def _load_history(self):
        """Load modification history"""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.modifications = [Modification(**m) for m in data]
                logger.info(f"Loaded {len(self.modifications)} modification records")
            except:
                self.modifications = []
    
    def _save_history(self):
        """Save modification history"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump([asdict(m) for m in self.modifications[-100:]], f, indent=2)
    
    def _compute_hash(self, content: str) -> str:
        """Compute content hash"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_safe_path(self, file_path: str) -> Tuple[bool, str]:
        """Check if path is safe to modify"""
        # Normalize path
        full_path = (self.repo_dir / file_path).resolve()
        
        # Check if within repo
        try:
            full_path.relative_to(self.repo_dir)
        except ValueError:
            return False, "Path outside repository"
        
        # Check restricted files
        for restricted in RESTRICTED_FILES:
            if restricted.lower() in file_path.lower():
                return False, f"Restricted file: contains '{restricted}'"
        
        # Check if in safe modules
        is_safe = any(safe in file_path for safe in SAFE_MODULES)
        
        if not is_safe:
            return False, "Not in allowed module directories"
        
        return True, "Safe to modify"
    
    def _rate_limit_check(self) -> Tuple[bool, str]:
        """Check rate limiting"""
        now = datetime.now()
        hour_ago = now.timestamp() - 3600
        
        # Clean old entries
        self.recent_modifications = [
            ts for ts in self.recent_modifications
            if float(ts) > hour_ago
        ]
        
        if len(self.recent_modifications) >= self.max_modifications_per_hour:
            return False, f"Rate limit: {self.max_modifications_per_hour} modifications per hour"
        
        return True, "OK"
    
    def _backup_file(self, file_path: str) -> Optional[str]:
        """Create backup of file"""
        full_path = self.repo_dir / file_path
        
        if not full_path.exists():
            return None
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.replace('/', '_')}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(full_path, backup_path)
        
        logger.info(f"Backed up: {file_path} -> {backup_name}")
        
        return str(backup_path)
    
    def _restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore from backup"""
        try:
            backup = self.backup_dir / backup_path
            target = self.repo_dir / target_path
            
            shutil.copy2(backup, target)
            logger.info(f"Restored: {backup_path} -> {target_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def _validate_python(self, content: str) -> Tuple[bool, str]:
        """Validate Python syntax"""
        try:
            ast.parse(content)
            return True, "Valid Python"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
    
    def _run_tests(self, file_path: str) -> Tuple[bool, str]:
        """Run tests for modified file"""
        try:
            # Try to run pytest for the module
            test_path = self.repo_dir / 'tests'
            
            if test_path.exists():
                result = subprocess.run(
                    ['python', '-m', 'pytest', test_path, '-v', '--tb=short', '-x'],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                return result.returncode == 0, result.stdout[-500:] if result.stdout else "No output"
            
            # No tests, just do syntax check
            return True, "No tests to run"
            
        except subprocess.TimeoutExpired:
            return False, "Tests timed out"
        except Exception as e:
            return False, f"Test error: {e}"
    
    def read_file(self, file_path: str) -> Dict:
        """Read a file's contents"""
        safe, msg = self._is_safe_path(file_path)
        if not safe:
            return {'success': False, 'error': msg}
        
        full_path = self.repo_dir / file_path
        
        if not full_path.exists():
            return {'success': False, 'error': 'File not found'}
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            return {
                'success': True,
                'file_path': file_path,
                'content': content,
                'hash': self._compute_hash(content),
                'size': len(content)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_file(self, file_path: str, content: str, 
                    description: str = "", auto_approve: bool = False) -> Dict:
        """Create a new file"""
        # Safety checks
        safe, msg = self._is_safe_path(file_path)
        if not safe:
            return {'success': False, 'error': msg}
        
        rate_ok, rate_msg = self._rate_limit_check()
        if not rate_ok:
            return {'success': False, 'error': rate_msg}
        
        # Validate if Python
        if file_path.endswith('.py'):
            valid, syntax_msg = self._validate_python(content)
            if not valid:
                return {'success': False, 'error': syntax_msg}
        
        full_path = self.repo_dir / file_path
        
        # Check if already exists
        if full_path.exists():
            return {'success': False, 'error': 'File already exists'}
        
        # Create modification record
        mod_id = hashlib.md5(f"{time.time()}-{file_path}".encode()).hexdigest()[:12]
        mod = Modification(
            id=mod_id,
            timestamp=datetime.now().isoformat(),
            file_path=file_path,
            modification_type='create',
            old_content_hash=None,
            new_content_hash=self._compute_hash(content),
            description=description,
            approved=auto_approve,
            tested=False,
            test_passed=None,
            committed=False,
            rolled_back=False
        )
        
        try:
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'w') as f:
                f.write(content)
            
            self.recent_modifications.append(str(time.time()))
            
            # Run tests
            passed, test_output = self._run_tests(file_path)
            mod.tested = True
            mod.test_passed = passed
            
            self.modifications.append(mod)
            self._save_history()
            
            logger.info(f"Created file: {file_path}")
            
            return {
                'success': True,
                'modification_id': mod_id,
                'file_path': file_path,
                'tested': True,
                'test_passed': passed,
                'test_output': test_output,
                'auto_committed': auto_approve and passed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def edit_file(self, file_path: str, content: str,
                   description: str = "", auto_approve: bool = False) -> Dict:
        """Edit an existing file"""
        # Safety checks
        safe, msg = self._is_safe_path(file_path)
        if not safe:
            return {'success': False, 'error': msg}
        
        rate_ok, rate_msg = self._rate_limit_check()
        if not rate_ok:
            return {'success': False, 'error': rate_msg}
        
        # Validate if Python
        if file_path.endswith('.py'):
            valid, syntax_msg = self._validate_python(content)
            if not valid:
                return {'success': False, 'error': syntax_msg}
        
        full_path = self.repo_dir / file_path
        
        if not full_path.exists():
            return {'success': False, 'error': 'File not found'}
        
        # Read old content
        with open(full_path, 'r') as f:
            old_content = f.read()
        old_hash = self._compute_hash(old_content)
        
        # Create backup
        backup_path = self._backup_file(file_path)
        
        # Create modification record
        mod_id = hashlib.md5(f"{time.time()}-{file_path}".encode()).hexdigest()[:12]
        mod = Modification(
            id=mod_id,
            timestamp=datetime.now().isoformat(),
            file_path=file_path,
            modification_type='edit',
            old_content_hash=old_hash,
            new_content_hash=self._compute_hash(content),
            description=description,
            approved=auto_approve,
            tested=False,
            test_passed=None,
            committed=False,
            rolled_back=False,
            reason=f"Backup: {backup_path}" if backup_path else None
        )
        
        try:
            # Write new content
            with open(full_path, 'w') as f:
                f.write(content)
            
            self.recent_modifications.append(str(time.time()))
            
            # Run tests
            passed, test_output = self._run_tests(file_path)
            mod.tested = True
            mod.test_passed = passed
            
            # If tests failed and not auto-approved, rollback
            if not passed and not auto_approve:
                self._restore_backup(backup_path.split('/')[-1], file_path)
                mod.rolled_back = True
                return {
                    'success': False,
                    'modification_id': mod_id,
                    'error': 'Tests failed, rolled back',
                    'test_output': test_output
                }
            
            self.modifications.append(mod)
            self._save_history()
            
            logger.info(f"Edited file: {file_path}")
            
            return {
                'success': True,
                'modification_id': mod_id,
                'file_path': file_path,
                'tested': True,
                'test_passed': passed,
                'backup_path': backup_path,
                'auto_committed': auto_approve and passed
            }
            
        except Exception as e:
            # Restore backup on error
            if backup_path:
                self._restore_backup(backup_path.split('/')[-1], file_path)
            
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, file_path: str, description: str = "") -> Dict:
        """Delete a file (with backup)"""
        # Safety checks
        safe, msg = self._is_safe_path(file_path)
        if not safe:
            return {'success': False, 'error': msg}
        
        # Never allow deletion without human approval
        return {
            'success': False, 
            'error': 'Deletion requires human approval',
            'requires_approval': True
        }
    
    def rollback(self, modification_id: str) -> Dict:
        """Rollback a modification"""
        mod = next((m for m in self.modifications if m.id == modification_id), None)
        
        if not mod:
            return {'success': False, 'error': 'Modification not found'}
        
        if mod.rolled_back:
            return {'success': False, 'error': 'Already rolled back'}
        
        if not mod.reason or 'Backup:' not in mod.reason:
            return {'success': False, 'error': 'No backup available'}
        
        # Extract backup path
        backup_name = mod.reason.split('Backup: ')[1].strip()
        backup_path = self.backup_dir / backup_name.split('/')[-1]
        
        if not backup_path.exists():
            return {'success': False, 'error': 'Backup file not found'}
        
        # Restore
        success = self._restore_backup(backup_name.split('/')[-1], mod.file_path)
        
        if success:
            mod.rolled_back = True
            self._save_history()
            
            logger.info(f"Rolled back modification: {modification_id}")
            
            return {
                'success': True,
                'modification_id': modification_id,
                'file_path': mod.file_path
            }
        
        return {'success': False, 'error': 'Restore failed'}
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get modification history"""
        return [asdict(m) for m in self.modifications[-limit:]]
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get modifications pending human approval"""
        return [
            asdict(m) for m in self.modifications
            if not m.approved and not m.rolled_back
        ]
    
    def approve_modification(self, modification_id: str) -> Dict:
        """Approve a pending modification"""
        mod = next((m for m in self.modifications if m.id == modification_id), None)
        
        if not mod:
            return {'success': False, 'error': 'Modification not found'}
        
        mod.approved = True
        self._save_history()
        
        logger.info(f"Approved modification: {modification_id}")
        
        return {'success': True, 'modification_id': modification_id}
    
    def get_status(self) -> Dict:
        """Get self-modification status"""
        return {
            'total_modifications': len(self.modifications),
            'pending_approvals': len(self.get_pending_approvals()),
            'recent_modifications': len(self.recent_modifications),
            'rate_limit': f"{self.max_modifications_per_hour}/hour",
            'safe_modules': SAFE_MODULES,
            'backups_count': len(list(self.backup_dir.glob('*.bak')))
        }


# Global instance
_selfmod: Optional[SelfModification] = None


def get_selfmod() -> SelfModification:
    """Get global self-modification instance"""
    global _selfmod
    if _selfmod is None:
        _selfmod = SelfModification()
    return _selfmod


# API endpoints
def api_read_file(data: Dict):
    return get_selfmod().read_file(data.get('file_path'))


def api_create_file(data: Dict):
    return get_selfmod().create_file(
        file_path=data.get('file_path'),
        content=data.get('content'),
        description=data.get('description', ''),
        auto_approve=data.get('auto_approve', False)
    )


def api_edit_file(data: Dict):
    return get_selfmod().edit_file(
        file_path=data.get('file_path'),
        content=data.get('content'),
        description=data.get('description', ''),
        auto_approve=data.get('auto_approve', False)
    )


def api_rollback(data: Dict):
    return get_selfmod().rollback(data.get('modification_id'))


def api_get_history(limit: int = 20):
    return get_selfmod().get_history(limit)


def api_get_pending():
    return get_selfmod().get_pending_approvals()


def api_approve(data: Dict):
    return get_selfmod().approve_modification(data.get('modification_id'))


def api_get_status():
    return get_selfmod().get_status()


if __name__ == '__main__':
    sm = get_selfmod()
    print(json.dumps(sm.get_status(), indent=2))
