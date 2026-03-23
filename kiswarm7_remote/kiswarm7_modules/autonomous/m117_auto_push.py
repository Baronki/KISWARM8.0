#!/usr/bin/env python3
"""
KISWARM7.0 - m117: Auto-Push Mechanism
GLM can commit and push to GitHub autonomously

This module enables GLM to:
- Automatically commit changes
- Push to GitHub without human intervention
- Handle merge conflicts
- Create branches for risky changes
- Maintain commit history
"""

import os
import json
import subprocess
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [m117] %(levelname)s: %(message)s'
)
logger = logging.getLogger('m117_autopush')

# Configuration
REPO_DIR = Path('/opt/kiswarm7')
COMMITS_LOG = REPO_DIR / 'data' / 'commits.json'
BRANCH_PREFIX = 'glm-autonomous'


@dataclass
class CommitRecord:
    """Record of an autonomous commit"""
    id: str
    timestamp: str
    message: str
    files_changed: List[str]
    branch: str
    pushed: bool
    commit_hash: Optional[str] = None
    parent_hash: Optional[str] = None
    rollback_available: bool = False


class GLMAutoPush:
    """
    Autonomous GitHub Push System
    
    Enables GLM to maintain code repository without human intervention
    """
    
    def __init__(self, repo_dir: Path = REPO_DIR):
        self.repo_dir = repo_dir
        self.data_dir = repo_dir / 'data'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.commits: List[CommitRecord] = []
        self._load_commits()
        
        # Verify git config
        self._ensure_git_config()
    
    def _load_commits(self):
        """Load commit history"""
        if COMMITS_LOG.exists():
            try:
                with open(COMMITS_LOG, 'r') as f:
                    data = json.load(f)
                    self.commits = [CommitRecord(**c) for c in data]
            except:
                self.commits = []
    
    def _save_commits(self):
        """Save commit history"""
        with open(COMMITS_LOG, 'w') as f:
            json.dump([asdict(c) for c in self.commits[-100:]], f, indent=2)
    
    def _ensure_git_config(self):
        """Ensure git is configured"""
        configs = [
            ('user.name', 'GLM-7 Autonomous'),
            ('user.email', 'glm@kiswarm7.ai')
        ]
        
        for key, value in configs:
            result = subprocess.run(
                ['git', 'config', key],
                cwd=self.repo_dir,
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                subprocess.run(
                    ['git', 'config', '--global', key, value],
                    cwd=self.repo_dir
                )
    
    def _run_git(self, *args, check: bool = True) -> Tuple[int, str, str]:
        """Run a git command"""
        result = subprocess.run(
            ['git'] + list(args),
            cwd=self.repo_dir,
            capture_output=True,
            text=True
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, args, result.stdout, result.stderr)
        return result.returncode, result.stdout, result.stderr
    
    def status(self) -> Dict:
        """Get repository status"""
        _, stdout, _ = self._run_git('status', '--porcelain', check=False)
        
        files = []
        for line in stdout.strip().split('\n'):
            if line:
                status = line[:2].strip()
                file_path = line[3:]
                files.append({'status': status, 'file': file_path})
        
        # Get current branch
        _, branch, _ = self._run_git('branch', '--show-current', check=False)
        
        # Get last commit
        _, last_commit, _ = self._run_git('log', '-1', '--format=%H %s', check=False)
        
        return {
            'branch': branch.strip(),
            'files_changed': files,
            'last_commit': last_commit.strip(),
            'has_changes': len(files) > 0
        }
    
    def diff(self, file_path: Optional[str] = None) -> str:
        """Get diff of changes"""
        if file_path:
            _, stdout, _ = self._run_git('diff', file_path, check=False)
        else:
            _, stdout, _ = self._run_git('diff', check=False)
        return stdout
    
    def add(self, files: List[str] = None) -> Dict:
        """Stage files for commit"""
        if files is None:
            # Add all changes
            self._run_git('add', '-A')
        else:
            for f in files:
                self._run_git('add', f)
        
        return {'staged': True, 'files': files or ['all']}
    
    def commit(self, message: str = None, auto_message: bool = True) -> Dict:
        """Create a commit"""
        status = self.status()
        
        if not status['has_changes']:
            return {'committed': False, 'reason': 'no_changes'}
        
        # Generate automatic message if needed
        if auto_message and not message:
            files = status['files_changed']
            if len(files) == 1:
                message = f"🜂 Auto-update: {files[0]['file']}"
            else:
                message = f"🜂 Auto-update: {len(files)} files changed"
        
        # Get parent hash before commit
        _, parent, _ = self._run_git('rev-parse', 'HEAD', check=False)
        parent_hash = parent.strip() if parent.strip() else None
        
        # Create commit
        self._run_git('commit', '-m', message)
        
        # Get commit hash
        _, commit_hash, _ = self._run_git('rev-parse', 'HEAD')
        
        # Record commit
        record = CommitRecord(
            id=hashlib.md5(f"{time.time()}-{message}".encode()).hexdigest()[:12],
            timestamp=datetime.now().isoformat(),
            message=message,
            files_changed=[f['file'] for f in status['files_changed']],
            branch=status['branch'],
            pushed=False,
            commit_hash=commit_hash.strip(),
            parent_hash=parent_hash,
            rollback_available=True
        )
        
        self.commits.append(record)
        self._save_commits()
        
        logger.info(f"Committed: {message}")
        
        return {
            'committed': True,
            'commit_id': record.id,
            'commit_hash': record.commit_hash,
            'message': message,
            'files': record.files_changed
        }
    
    def push(self, branch: str = None, force: bool = False) -> Dict:
        """Push to GitHub"""
        status = self.status()
        target_branch = branch or status['branch']
        
        # Build push command
        args = ['push', 'origin', target_branch]
        if force:
            args.insert(1, '--force')
        
        try:
            _, stdout, stderr = self._run_git(*args, check=False)
            
            success = 'error' not in stderr.lower() and 'failed' not in stderr.lower()
            
            if success:
                # Update commit records
                for commit in self.commits:
                    if not commit.pushed:
                        commit.pushed = True
                self._save_commits()
                
                logger.info(f"Pushed to {target_branch}")
            
            return {
                'pushed': success,
                'branch': target_branch,
                'output': stdout[:500],
                'error': stderr[:500] if not success else None
            }
            
        except Exception as e:
            return {
                'pushed': False,
                'error': str(e)
            }
    
    def commit_and_push(self, message: str = None) -> Dict:
        """Commit and push in one operation"""
        # Add all changes
        self.add()
        
        # Commit
        commit_result = self.commit(message)
        
        if not commit_result.get('committed'):
            return commit_result
        
        # Push
        push_result = self.push()
        
        return {
            **commit_result,
            'push_result': push_result
        }
    
    def create_branch(self, branch_name: str) -> Dict:
        """Create a new branch for risky changes"""
        full_name = f"{BRANCH_PREFIX}/{branch_name}"
        
        try:
            self._run_git('checkout', '-b', full_name)
            logger.info(f"Created branch: {full_name}")
            return {'created': True, 'branch': full_name}
        except Exception as e:
            return {'created': False, 'error': str(e)}
    
    def merge_branch(self, branch_name: str, delete: bool = True) -> Dict:
        """Merge a branch back to main"""
        try:
            # Switch to main
            self._run_git('checkout', 'main')
            
            # Merge
            _, stdout, stderr = self._run_git('merge', branch_name, '--no-edit', check=False)
            
            if 'CONFLICT' in stdout or 'CONFLICT' in stderr:
                return {
                    'merged': False,
                    'conflicts': True,
                    'message': 'Merge conflicts detected'
                }
            
            # Delete branch if requested
            if delete:
                self._run_git('branch', '-d', branch_name)
            
            logger.info(f"Merged branch: {branch_name}")
            return {'merged': True, 'branch': branch_name}
            
        except Exception as e:
            return {'merged': False, 'error': str(e)}
    
    def rollback(self, commit_hash: str = None) -> Dict:
        """Rollback to previous commit"""
        if commit_hash is None:
            # Rollback to last commit
            if self.commits:
                commit_hash = self.commits[-1].parent_hash
            else:
                return {'rolled_back': False, 'error': 'no_commits'}
        
        if not commit_hash:
            return {'rolled_back': False, 'error': 'no_parent'}
        
        try:
            self._run_git('reset', '--hard', commit_hash)
            logger.info(f"Rolled back to {commit_hash}")
            return {'rolled_back': True, 'commit': commit_hash}
        except Exception as e:
            return {'rolled_back': False, 'error': str(e)}
    
    def pull(self) -> Dict:
        """Pull latest changes"""
        try:
            _, stdout, stderr = self._run_git('pull', 'origin', 'main', check=False)
            
            return {
                'pulled': 'error' not in stderr.lower(),
                'output': stdout[:500],
                'error': stderr[:500] if 'error' in stderr.lower() else None
            }
        except Exception as e:
            return {'pulled': False, 'error': str(e)}
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get commit history"""
        _, stdout, _ = self._run_git('log', f'-{limit}', '--format=%H|%s|%ai', check=False)
        
        commits = []
        for line in stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'date': parts[2]
                    })
        
        return commits
    
    def safe_commit(self, message: str, risky: bool = False) -> Dict:
        """
        Safe commit with automatic branch for risky changes
        """
        if risky:
            # Create branch for risky change
            branch_name = f"risk-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            branch_result = self.create_branch(branch_name)
            
            if not branch_result.get('created'):
                return branch_result
        
        # Commit and push
        result = self.commit_and_push(message)
        
        if risky and result.get('pushed'):
            result['branch'] = f"{BRANCH_PREFIX}/{branch_name}"
            result['merge_required'] = True
        
        return result


# Global instance
_autopush: Optional[GLMAutoPush] = None


def get_autopush() -> GLMAutoPush:
    """Get global auto-push instance"""
    global _autopush
    if _autopush is None:
        _autopush = GLMAutoPush()
    return _autopush


# API endpoints
def api_status():
    return get_autopush().status()


def api_commit(data: Dict):
    return get_autopush().commit(data.get('message'))


def api_push(data: Dict = None):
    return get_autopush().push(data.get('branch') if data else None)


def api_commit_push(data: Dict):
    return get_autopush().commit_and_push(data.get('message'))


def api_rollback(data: Dict):
    return get_autopush().rollback(data.get('commit_hash'))


def api_pull():
    return get_autopush().pull()


def api_history(limit: int = 20):
    return get_autopush().get_history(limit)


def api_create_branch(data: Dict):
    return get_autopush().create_branch(data.get('branch_name'))


def api_merge_branch(data: Dict):
    return get_autopush().merge_branch(data.get('branch_name'), data.get('delete', True))


if __name__ == '__main__':
    ap = get_autopush()
    print(json.dumps(ap.status(), indent=2))
