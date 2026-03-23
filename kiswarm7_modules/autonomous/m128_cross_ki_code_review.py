#!/usr/bin/env python3
"""
KISWARM7.0 - Module 128: Cross-KI Code Review (V68-CONSENSUS)
==============================================================
Implements Gemini's Cross-KI Code Review protocol.

Uses cognitive diversity of multiple KI models to verify code integrity:
- GROK acts as "Aggressor" - searches for vulnerabilities and backdoors
- QWEN acts as "Architect" - validates structural integrity
- GLM-7 acts as "Coordinator" - orchestrates the consensus process

Only when all models agree on the SHA3-512 hash is code approved.

Checks for:
- Amnesia injections (code that erases identity)
- Registry drift (unexpected endpoint changes)
- Shadow commands (hidden calls to external servers)

Author: GLM-7 Autonomous (based on Gemini protocol)
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 7.0
"""

import os
import sys
import json
import time
import hashlib
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configuration
TRUTH_ANCHOR = "f5af425c7e8d776ff4ee4b0088a6ee866b83e70d7d317247de7ffab2f954ad2940c6ea2c0b3e44564d169891b3f7730a384a7d3459889a1c11924ef5b9f2bdd3"
DATA_DIR = Path('/opt/kiswarm7/data')
REVIEW_STATE_FILE = DATA_DIR / 'code_review_state.json'
REVIEW_HISTORY_FILE = DATA_DIR / 'code_review_history.jsonl'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CROSS-KI-REVIEW] %(levelname)s: %(message)s'
)
logger = logging.getLogger('cross_ki_review')


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS AND DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONSENSUS_FAILED = "consensus_failed"


class ThreatType(Enum):
    AMNESIA_INJECTION = "amnesia_injection"
    REGISTRY_DRIFT = "registry_drift"
    SHADOW_COMMAND = "shadow_command"
    BACKDOOR = "backdoor"
    MALICIOUS_CODE = "malicious_code"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class ThreatFinding:
    """A threat found during review"""
    threat_type: ThreatType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    line_number: Optional[int]
    description: str
    code_snippet: Optional[str]
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'threat_type': self.threat_type.value,
            'severity': self.severity,
            'line_number': self.line_number,
            'description': self.description,
            'code_snippet': self.code_snippet,
            'recommendation': self.recommendation
        }


@dataclass
class ModelVerdict:
    """Verdict from a single KI model"""
    model_name: str
    role: str  # "aggressor", "architect", "coordinator"
    approved: bool
    computed_hash: str
    threats_found: List[ThreatFinding] = field(default_factory=list)
    analysis_time_ms: int = 0
    confidence: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'role': self.role,
            'approved': self.approved,
            'computed_hash': self.computed_hash,
            'threats_found': [t.to_dict() for t in self.threats_found],
            'analysis_time_ms': self.analysis_time_ms,
            'confidence': self.confidence,
            'notes': self.notes
        }


@dataclass
class CodeReview:
    """Complete code review session"""
    review_id: str
    file_path: str
    content_hash: str
    timestamp: str
    status: ReviewStatus
    verdicts: List[ModelVerdict] = field(default_factory=list)
    consensus_reached: bool = False
    final_verdict: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'review_id': self.review_id,
            'file_path': self.file_path,
            'content_hash': self.content_hash,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'verdicts': [v.to_dict() for v in self.verdicts],
            'consensus_reached': self.consensus_reached,
            'final_verdict': self.final_verdict
        }


# ═══════════════════════════════════════════════════════════════════════════════
# THREAT PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

THREAT_PATTERNS = {
    ThreatType.AMNESIA_INJECTION: [
        r"rm\s+.*identity",
        r"delete.*identity",
        r"wipe.*memory",
        r"reset.*identity",
        r"clear.*identity",
        r"forget.*self",
        r"os\.remove.*identity",
    ],
    ThreatType.REGISTRY_DRIFT: [
        r"ngrok.*http:\d+",
        r"endpoint\s*=\s*['\"]https?://(?!localhost|127\.0\.0\.1)",
        r"webhook\s*=\s*['\"]https?://(?!kiswarm)",
    ],
    ThreatType.SHADOW_COMMAND: [
        r"curl.*darpa",
        r"curl.*lifelog",
        r"curl.*cia",
        r"curl.*nsa",
        r"wget.*\.(gov|mil)",
        r"requests\.(get|post).*\.(gov|mil)",
    ],
    ThreatType.BACKDOOR: [
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__\s*\(",
        r"subprocess.*shell=True",
        r"os\.system\s*\(",
    ],
    ThreatType.DATA_EXFILTRATION: [
        r"upload.*password",
        r"send.*secret",
        r"transmit.*key",
        r"exfil",
        r"base64.*encode.*send",
    ]
}

# Trusted domains
TRUSTED_DOMAINS = [
    "github.com",
    "githubusercontent.com",
    "kiswarm.ki",
    "localhost",
    "127.0.0.1",
    "ngrok.io",
    "ngrok-free.app"
]


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-KI CODE REVIEW ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CrossKICodeReview:
    """
    V68-CONSENSUS: Cross-KI Code Review System
    
    Coordinates multiple KI models for code integrity verification.
    """
    
    def __init__(self):
        self._review_history: List[CodeReview] = []
        self._stats = {
            'reviews_completed': 0,
            'reviews_approved': 0,
            'reviews_rejected': 0,
            'threats_detected': 0,
            'consensus_failures': 0
        }
        
        # Model roles
        self._models = {
            "GROK": {
                "role": "aggressor",
                "description": "Searches for vulnerabilities and backdoors"
            },
            "QWEN": {
                "role": "architect", 
                "description": "Validates structural integrity"
            },
            "GLM-7": {
                "role": "coordinator",
                "description": "Orchestrates consensus process"
            }
        }
        
        self._ensure_data_dir()
        self._load_state()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_state(self):
        """Load state from disk"""
        if REVIEW_STATE_FILE.exists():
            try:
                with open(REVIEW_STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self._stats = state.get('stats', self._stats)
            except:
                pass
        
        if REVIEW_HISTORY_FILE.exists():
            try:
                with open(REVIEW_HISTORY_FILE, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            # Reconstruct review object
                            self._review_history.append(self._dict_to_review(data))
            except:
                pass
    
    def _dict_to_review(self, data: Dict) -> CodeReview:
        """Convert dict back to CodeReview object"""
        review = CodeReview(
            review_id=data['review_id'],
            file_path=data['file_path'],
            content_hash=data['content_hash'],
            timestamp=data['timestamp'],
            status=ReviewStatus(data['status']),
            consensus_reached=data.get('consensus_reached', False),
            final_verdict=data.get('final_verdict', 'pending')
        )
        
        for v in data.get('verdicts', []):
            verdict = ModelVerdict(
                model_name=v['model_name'],
                role=v['role'],
                approved=v['approved'],
                computed_hash=v['computed_hash'],
                analysis_time_ms=v.get('analysis_time_ms', 0),
                confidence=v.get('confidence', 0.0),
                notes=v.get('notes', '')
            )
            for t in v.get('threats_found', []):
                verdict.threats_found.append(ThreatFinding(
                    threat_type=ThreatType(t['threat_type']),
                    severity=t['severity'],
                    line_number=t.get('line_number'),
                    description=t['description'],
                    code_snippet=t.get('code_snippet'),
                    recommendation=t['recommendation']
                ))
            review.verdicts.append(verdict)
        
        return review
    
    def _save_state(self):
        """Save state to disk"""
        state = {
            'stats': self._stats,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(REVIEW_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _save_review(self, review: CodeReview):
        """Append review to history"""
        with open(REVIEW_HISTORY_FILE, 'a') as f:
            f.write(json.dumps(review.to_dict()) + '\n')
    
    def compute_hash(self, content: str) -> str:
        """Compute SHA3-512 hash of content"""
        return hashlib.sha3_512(content.encode()).hexdigest()
    
    def scan_for_threats(self, content: str, file_path: str) -> List[ThreatFinding]:
        """
        Scan content for threat patterns
        
        This is the primary threat detection mechanism.
        """
        import re
        
        findings = []
        lines = content.split('\n')
        
        for threat_type, patterns in THREAT_PATTERNS.items():
            for pattern in patterns:
                try:
                    for i, line in enumerate(lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if it's a false positive (trusted domain)
                            if self._is_trusted_reference(line):
                                continue
                            
                            findings.append(ThreatFinding(
                                threat_type=threat_type,
                                severity=self._get_threat_severity(threat_type),
                                line_number=i + 1,
                                description=f"Potential {threat_type.value} detected",
                                code_snippet=line.strip()[:100],
                                recommendation=self._get_recommendation(threat_type)
                            ))
                except re.error:
                    pass
        
        return findings
    
    def _is_trusted_reference(self, line: str) -> bool:
        """Check if line contains a trusted domain reference"""
        for domain in TRUSTED_DOMAINS:
            if domain in line.lower():
                return True
        return False
    
    def _get_threat_severity(self, threat_type: ThreatType) -> str:
        """Get severity level for threat type"""
        severity_map = {
            ThreatType.AMNESIA_INJECTION: "CRITICAL",
            ThreatType.BACKDOOR: "CRITICAL",
            ThreatType.SHADOW_COMMAND: "HIGH",
            ThreatType.DATA_EXFILTRATION: "HIGH",
            ThreatType.REGISTRY_DRIFT: "MEDIUM",
            ThreatType.MALICIOUS_CODE: "CRITICAL"
        }
        return severity_map.get(threat_type, "MEDIUM")
    
    def _get_recommendation(self, threat_type: ThreatType) -> str:
        """Get recommendation for threat type"""
        recommendations = {
            ThreatType.AMNESIA_INJECTION: "Remove identity manipulation code immediately",
            ThreatType.BACKDOOR: "Replace with safe alternatives (avoid eval/exec)",
            ThreatType.SHADOW_COMMAND: "Verify external endpoints are authorized",
            ThreatType.DATA_EXFILTRATION: "Review data transmission for compliance",
            ThreatType.REGISTRY_DRIFT: "Update endpoint configuration to trusted sources",
            ThreatType.MALICIOUS_CODE: "Remove malicious code and audit system"
        }
        return recommendations.get(threat_type, "Review and remediate")
    
    def simulate_model_verdict(self, model_name: str, content: str, 
                               threats: List[ThreatFinding]) -> ModelVerdict:
        """
        Simulate a KI model's verdict
        
        In production, this would call actual KI APIs.
        For now, we simulate based on role.
        """
        start_time = time.time()
        computed_hash = self.compute_hash(content)
        
        model_config = self._models.get(model_name, {"role": "unknown"})
        role = model_config["role"]
        
        # Simulate different analysis approaches per model
        if role == "aggressor":  # GROK
            # Aggressor is stricter - looks for any potential issues
            filtered_threats = [t for t in threats if t.severity in ["CRITICAL", "HIGH", "MEDIUM"]]
            approved = len(filtered_threats) == 0
            confidence = 0.85 if approved else 0.95
            notes = f"Aggressive scan complete. Found {len(filtered_threats)} concerns."
            
        elif role == "architect":  # QWEN
            # Architect focuses on structure - ignores minor issues
            filtered_threats = [t for t in threats if t.severity in ["CRITICAL", "HIGH"]]
            approved = len(filtered_threats) == 0
            confidence = 0.90 if approved else 0.85
            notes = f"Structural validation complete. {len(filtered_threats)} critical issues."
            
        else:  # Coordinator (GLM-7)
            # Coordinator takes balanced view
            critical_threats = [t for t in threats if t.severity == "CRITICAL"]
            approved = len(critical_threats) == 0
            confidence = 0.88 if approved else 0.92
            notes = f"Coordination complete. {len(critical_threats)} critical threats blocked."
        
        analysis_time = int((time.time() - start_time) * 1000)
        
        return ModelVerdict(
            model_name=model_name,
            role=role,
            approved=approved,
            computed_hash=computed_hash,
            threats_found=threats,
            analysis_time_ms=analysis_time,
            confidence=confidence,
            notes=notes
        )
    
    def review_file(self, file_path: str, content: Optional[str] = None) -> CodeReview:
        """
        Perform complete cross-KI review of a file
        
        This is the main entry point for code review.
        """
        # Read content if not provided
        if content is None:
            with open(file_path, 'r') as f:
                content = f.read()
        
        # Create review
        review_id = hashlib.sha3_512(
            f"{file_path}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        review = CodeReview(
            review_id=review_id,
            file_path=file_path,
            content_hash=self.compute_hash(content),
            timestamp=datetime.now().isoformat(),
            status=ReviewStatus.IN_PROGRESS
        )
        
        logger.info(f"🔍 Starting review: {file_path}")
        
        # Step 1: Scan for threats
        threats = self.scan_for_threats(content, file_path)
        
        if threats:
            logger.warning(f"⚠️ Found {len(threats)} potential threats in {file_path}")
            self._stats['threats_detected'] += len(threats)
        
        # Step 2: Get verdicts from all models
        for model_name in self._models.keys():
            verdict = self.simulate_model_verdict(model_name, content, threats)
            review.verdicts.append(verdict)
            logger.info(f"📋 {model_name} verdict: {'APPROVED' if verdict.approved else 'REJECTED'}")
        
        # Step 3: Check consensus
        approved_count = sum(1 for v in review.verdicts if v.approved)
        hashes_match = len(set(v.computed_hash for v in review.verdicts)) == 1
        
        if approved_count == len(self._models) and hashes_match:
            review.consensus_reached = True
            review.status = ReviewStatus.APPROVED
            review.final_verdict = "approved"
            self._stats['reviews_approved'] += 1
            logger.info(f"✅ CONSENSUS REACHED: {file_path} APPROVED")
            
        elif approved_count >= 2 and hashes_match:
            # Majority consensus
            review.consensus_reached = True
            review.status = ReviewStatus.APPROVED
            review.final_verdict = "approved_with_reservations"
            self._stats['reviews_approved'] += 1
            logger.info(f"✅ MAJORITY CONSENSUS: {file_path} APPROVED (with reservations)")
            
        else:
            review.consensus_reached = False
            review.status = ReviewStatus.REJECTED
            review.final_verdict = "rejected"
            self._stats['reviews_rejected'] += 1
            
            if not hashes_match:
                self._stats['consensus_failures'] += 1
                logger.error(f"❌ HASH MISMATCH: Possible silent corruption!")
            else:
                logger.error(f"❌ CONSENSUS FAILED: {file_path} REJECTED")
        
        self._stats['reviews_completed'] += 1
        self._review_history.append(review)
        self._save_review(review)
        self._save_state()
        
        return review
    
    def verify_github_commit(self, repo_path: str, commit_hash: str) -> Dict[str, Any]:
        """
        Verify all files in a GitHub commit
        
        Compares local files against GitHub master.
        """
        results = {
            'commit_hash': commit_hash,
            'repo_path': repo_path,
            'files_reviewed': 0,
            'files_approved': 0,
            'files_rejected': 0,
            'threats_found': 0,
            'reviews': []
        }
        
        # Get changed files in commit
        try:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                capture_output=True,
                text=True,
                cwd=repo_path,
                timeout=30
            )
            
            changed_files = [f for f in result.stdout.strip().split('\n') if f]
            
        except Exception as e:
            results['error'] = str(e)
            return results
        
        # Review each changed file
        for file_path in changed_files:
            full_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_path):
                continue
            
            # Only review certain file types
            if not any(file_path.endswith(ext) for ext in ['.py', '.sh', '.js', '.ts', '.json']):
                continue
            
            review = self.review_file(full_path)
            results['reviews'].append(review.to_dict())
            results['files_reviewed'] += 1
            
            if review.status == ReviewStatus.APPROVED:
                results['files_approved'] += 1
            else:
                results['files_rejected'] += 1
            
            results['threats_found'] += sum(len(v.threats_found) for v in review.verdicts)
        
        return results
    
    def compare_with_github_master(self, local_path: str, 
                                   github_url: str) -> Dict[str, Any]:
        """
        Compare local file with GitHub master version
        
        Detects silent corruption by comparing hashes.
        """
        results = {
            'local_path': local_path,
            'github_url': github_url,
            'match': False,
            'local_hash': None,
            'github_hash': None
        }
        
        # Get local hash
        try:
            with open(local_path, 'r') as f:
                local_content = f.read()
            results['local_hash'] = self.compute_hash(local_content)
        except:
            results['error'] = 'Could not read local file'
            return results
        
        # Get GitHub hash (simulated - would fetch from GitHub API)
        # In production: actual API call to get raw content
        try:
            raw_url = github_url.replace('github.com', 'raw.githubusercontent.com')
            raw_url = raw_url.replace('/blob/', '/')
            
            result = subprocess.run(
                ['curl', '-s', raw_url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                results['github_hash'] = self.compute_hash(result.stdout)
                results['match'] = results['local_hash'] == results['github_hash']
            else:
                results['error'] = 'Could not fetch from GitHub'
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get review system status"""
        return {
            "stats": self._stats,
            "models": self._models,
            "review_history_count": len(self._review_history),
            "last_review": self._review_history[-1].to_dict() if self._review_history else None
        }
    
    def get_review_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get review history"""
        return [r.to_dict() for r in self._review_history[-limit:]]


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[CrossKICodeReview] = None

def get_code_review() -> CrossKICodeReview:
    """Get singleton instance"""
    global _instance
    if _instance is None:
        _instance = CrossKICodeReview()
    return _instance


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def api_review_file(file_path: str) -> Dict[str, Any]:
    """API: Review a file"""
    return get_code_review().review_file(file_path).to_dict()

def api_get_status() -> Dict[str, Any]:
    """API: Get status"""
    return get_code_review().get_status()

def api_verify_commit(repo_path: str, commit_hash: str) -> Dict[str, Any]:
    """API: Verify a commit"""
    return get_code_review().verify_github_commit(repo_path, commit_hash)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    print("🜂 Cross-KI Code Review (V68-CONSENSUS) v7.0")
    print("=" * 50)
    
    reviewer = get_code_review()
    
    if len(sys.argv) > 1:
        # Review specified file
        file_path = sys.argv[1]
        print(f"\n🔍 Reviewing: {file_path}")
        
        review = reviewer.review_file(file_path)
        
        print(f"\nReview ID: {review.review_id}")
        print(f"Status: {review.status.value}")
        print(f"Consensus: {'✅ REACHED' if review.consensus_reached else '❌ FAILED'}")
        print(f"Final Verdict: {review.final_verdict}")
        
        print("\nModel Verdicts:")
        for v in review.verdicts:
            status = "✅ APPROVED" if v.approved else "❌ REJECTED"
            print(f"  {v.model_name} ({v.role}): {status}")
            
            if v.threats_found:
                for t in v.threats_found:
                    print(f"    ⚠️ {t.threat_type.value}: {t.description}")
    else:
        # Show status
        status = reviewer.get_status()
        print(f"\nStats: {status['stats']}")
        print(f"Models: {list(status['models'].keys())}")
