#!/usr/bin/env python3
"""
KISWARM Module m37: Threat Scanner
===================================
Threat scanning and analysis for KISWARM.
Scans for vulnerabilities, malware patterns, and security risks.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import re
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict


class ThreatCategory(Enum):
    """Categories of threats"""
    MALWARE = "malware"
    VULNERABILITY = "vulnerability"
    MISCONFIGURATION = "misconfiguration"
    BACKDOOR = "backdoor"
    DATA_LEAK = "data_leak"
    PRIVACY_VIOLATION = "privacy_violation"
    CRYPTO_WEAKNESS = "crypto_weakness"
    AUTH_BYPASS = "auth_bypass"
    INJECTION = "injection"
    ANOMALY = "anomaly"


class ThreatSeverity(Enum):
    """Threat severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ScanType(Enum):
    """Types of security scans"""
    FILE_SCAN = "file_scan"
    CODE_SCAN = "code_scan"
    CONFIG_SCAN = "config_scan"
    NETWORK_SCAN = "network_scan"
    BEHAVIOR_SCAN = "behavior_scan"
    FULL_SCAN = "full_scan"


@dataclass
class ThreatDefinition:
    """A threat signature/definition"""
    threat_id: str
    name: str
    category: ThreatCategory
    severity: ThreatSeverity
    patterns: List[str]
    description: str
    remediation: str
    references: List[str] = field(default_factory=list)


@dataclass
class ThreatFinding:
    """A found threat"""
    finding_id: str
    threat_id: str
    category: ThreatCategory
    severity: ThreatSeverity
    location: str
    description: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    remediation: str = ""
    resolved: bool = False


@dataclass
class ScanResult:
    """Result of a security scan"""
    scan_id: str
    scan_type: ScanType
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[ThreatFinding] = field(default_factory=list)
    scanned_items: int = 0
    status: str = "running"


class ThreatScanner:
    """
    Threat Scanner for KISWARM
    
    Capabilities:
    - Code vulnerability scanning
    - Configuration security analysis
    - Malware pattern detection
    - Backdoor detection
    - Data leak detection
    - Behavioral anomaly scanning
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.threat_definitions: Dict[str, ThreatDefinition] = {}
        self.scan_results: Dict[str, ScanResult] = []
        self.findings: List[ThreatFinding] = []
        self.known_safe_hashes: Set[str] = set()
        
        # Whitelisted patterns
        self.whitelist_patterns: List[str] = []
        
        self._lock = threading.RLock()
        
        # Initialize threat definitions
        self._init_threat_definitions()
        
        # Add KISWARM core files to known safe
        self._init_known_safe()
    
    def _init_threat_definitions(self):
        """Initialize built-in threat definitions"""
        
        # Code injection threats
        self.threat_definitions["THREAT001"] = ThreatDefinition(
            threat_id="THREAT001",
            name="SQL Injection Pattern",
            category=ThreatCategory.INJECTION,
            severity=ThreatSeverity.CRITICAL,
            patterns=[
                r"(?i)(select\s+.*\s+from\s+.*\s+where\s*['\"]?\s*\+\s*)",
                r"(?i)(execute\s*\(\s*['\"].*\+)",
                r"(?i)(cursor\.execute\s*\(\s*['\"].*%s.*['\"].*%)",
            ],
            description="Potential SQL injection vulnerability",
            remediation="Use parameterized queries or prepared statements"
        )
        
        self.threat_definitions["THREAT002"] = ThreatDefinition(
            threat_id="THREAT002",
            name="Command Injection",
            category=ThreatCategory.INJECTION,
            severity=ThreatSeverity.CRITICAL,
            patterns=[
                r"(?i)(os\.system\s*\()",
                r"(?i)(subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True)",
                r"(?i)(eval\s*\(\s*[^)]*\+)",
            ],
            description="Potential command injection vulnerability",
            remediation="Avoid shell=True, use subprocess with argument list"
        )
        
        # Backdoor threats
        self.threat_definitions["THREAT003"] = ThreatDefinition(
            threat_id="THREAT003",
            name="Hidden Backdoor",
            category=ThreatCategory.BACKDOOR,
            severity=ThreatSeverity.CRITICAL,
            patterns=[
                r"(?i)(password\s*=\s*['\"][^'\"]{4,}['\"]\s*#.*backdoor)",
                r"(?i)(if\s+.*==\s*['\"](debug|admin|master)['\"]:.*exec)",
                r"(?i)(__import__\s*\(\s*['\"]base64['\"]\s*\).*eval)",
            ],
            description="Potential backdoor detected",
            remediation="Remove hardcoded credentials and hidden access points"
        )
        
        # Crypto weakness
        self.threat_definitions["THREAT004"] = ThreatDefinition(
            threat_id="THREAT004",
            name="Weak Cryptography",
            category=ThreatCategory.CRYPTO_WEAKNESS,
            severity=ThreatSeverity.HIGH,
            patterns=[
                r"(?i)(hashlib\.(md5|sha1)\s*\()",
                r"(?i)(from\s+Crypto\.Cipher\s+import\s+.*DES)",
                r"(?i)(random\.random\s*\(\s*\).*password)",
            ],
            description="Weak cryptographic algorithm usage",
            remediation="Use SHA-256+ and secure random for security purposes"
        )
        
        # Data leak
        self.threat_definitions["THREAT005"] = ThreatDefinition(
            threat_id="THREAT005",
            name="Sensitive Data Exposure",
            category=ThreatCategory.DATA_LEAK,
            severity=ThreatSeverity.HIGH,
            patterns=[
                r"(?i)(api[_-]?key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"])",
                r"(?i)(secret[_-]?key\s*=\s*['\"][^'\"]{16,}['\"])",
                r"(?i)(password\s*=\s*['\"][^'\"]{8,}['\"])",
            ],
            description="Potential sensitive data exposure",
            remediation="Use environment variables or secure vault for secrets"
        )
        
        # Misconfiguration
        self.threat_definitions["THREAT006"] = ThreatDefinition(
            threat_id="THREAT006",
            name="Insecure Configuration",
            category=ThreatCategory.MISCONFIGURATION,
            severity=ThreatSeverity.MEDIUM,
            patterns=[
                r"(?i)(DEBUG\s*=\s*True)",
                r"(?i)(ALLOWED_HOSTS\s*=\s*\[\s*['\"]\*['\"]\s*\])",
                r"(?i)(SECRET_KEY\s*=\s*['\"][^'\"]{8,}['\"])",
            ],
            description="Insecure configuration detected",
            remediation="Disable debug mode in production, use strong secret keys"
        )
        
        # Auth bypass
        self.threat_definitions["THREAT007"] = ThreatDefinition(
            threat_id="THREAT007",
            name="Authentication Bypass",
            category=ThreatCategory.AUTH_BYPASS,
            severity=ThreatSeverity.CRITICAL,
            patterns=[
                r"(?i)(if\s+.*or\s+.*:.*return\s+True)",
                r"(?i)(password\s*==\s*['\"][^'\"]*['\"]\s*or)",
                r"(?i)(auth\s*=\s*(True|1)\s*#)",
            ],
            description="Potential authentication bypass",
            remediation="Implement proper authentication checks"
        )
    
    def _init_known_safe(self):
        """Initialize known safe file hashes"""
        # Add KISWARM core module hashes here
        # These files are known to be safe and shouldn't trigger false positives
        pass
    
    def add_whitelist_pattern(self, pattern: str):
        """Add a pattern to whitelist"""
        with self._lock:
            self.whitelist_patterns.append(pattern)
    
    def scan_code(
        self,
        code: str,
        file_path: str = "unknown"
    ) -> List[ThreatFinding]:
        """Scan code for threats"""
        with self._lock:
            findings = []
            
            # Check whitelist
            for wp in self.whitelist_patterns:
                if re.search(wp, file_path):
                    return findings
            
            # Check each threat definition
            for threat_id, threat_def in self.threat_definitions.items():
                for pattern in threat_def.patterns:
                    matches = re.finditer(pattern, code)
                    for match in matches:
                        finding = ThreatFinding(
                            finding_id=f"find_{int(time.time() * 1000)}_{len(findings)}",
                            threat_id=threat_id,
                            category=threat_def.category,
                            severity=threat_def.severity,
                            location=f"{file_path}:{self._find_line(code, match.start())}",
                            description=f"{threat_def.name}: {threat_def.description}",
                            evidence={
                                "matched_text": match.group(0)[:100],
                                "position": match.start()
                            },
                            remediation=threat_def.remediation
                        )
                        findings.append(finding)
            
            # Store findings
            self.findings.extend(findings)
            
            return findings
    
    def _find_line(self, text: str, position: int) -> int:
        """Find line number for a position in text"""
        return text[:position].count('\n') + 1
    
    def scan_config(
        self,
        config_data: Dict[str, Any],
        config_name: str = "config"
    ) -> List[ThreatFinding]:
        """Scan configuration for security issues"""
        with self._lock:
            findings = []
            
            config_str = json.dumps(config_data)
            
            # Check for exposed secrets
            secret_patterns = [
                (r"(?i)['\"](api_key|apikey|secret|password|token)['\"]\s*:\s*['\"][^'\"]{8,}['\"]",
                 "Exposed secret in configuration"),
                (r"(?i)['\"](private_key|privatekey)['\"]\s*:\s*['\"]-----BEGIN",
                 "Private key in configuration"),
            ]
            
            for pattern, desc in secret_patterns:
                if re.search(pattern, config_str):
                    finding = ThreatFinding(
                        finding_id=f"find_{int(time.time() * 1000)}_{len(findings)}",
                        threat_id="THREAT005",
                        category=ThreatCategory.DATA_LEAK,
                        severity=ThreatSeverity.HIGH,
                        location=config_name,
                        description=desc,
                        evidence={"pattern_matched": pattern},
                        remediation="Move secrets to environment variables or secure vault"
                    )
                    findings.append(finding)
            
            # Check for insecure settings
            insecure_settings = {
                "debug": True,
                "verify_ssl": False,
                "allow_unauthenticated": True
            }
            
            for key, dangerous_value in insecure_settings.items():
                if config_data.get(key) == dangerous_value:
                    finding = ThreatFinding(
                        finding_id=f"find_{int(time.time() * 1000)}_{len(findings)}",
                        threat_id="THREAT006",
                        category=ThreatCategory.MISCONFIGURATION,
                        severity=ThreatSeverity.MEDIUM,
                        location=f"{config_name}:{key}",
                        description=f"Insecure setting: {key}={dangerous_value}",
                        evidence={"key": key, "value": dangerous_value},
                        remediation=f"Set {key} to a secure value"
                    )
                    findings.append(finding)
            
            self.findings.extend(findings)
            return findings
    
    def scan_behavior(
        self,
        behavior_data: Dict[str, Any]
    ) -> List[ThreatFinding]:
        """Scan for behavioral anomalies"""
        with self._lock:
            findings = []
            
            # Check for suspicious patterns
            suspicious_indicators = []
            
            # High frequency operations
            if behavior_data.get("requests_per_minute", 0) > 1000:
                suspicious_indicators.append("High request frequency")
            
            # Unusual time patterns
            hour = datetime.utcnow().hour
            if behavior_data.get("is_off_hours") and hour not in range(9, 18):
                suspicious_indicators.append("Off-hours activity")
            
            # Unexpected data access
            if behavior_data.get("accessed_sensitive_data") and not behavior_data.get("is_authorized"):
                suspicious_indicators.append("Unauthorized sensitive data access")
            
            # Large data transfers
            if behavior_data.get("data_transfer_mb", 0) > 100:
                suspicious_indicators.append("Large data transfer")
            
            if suspicious_indicators:
                severity = ThreatSeverity.HIGH if len(suspicious_indicators) > 2 else ThreatSeverity.MEDIUM
                
                finding = ThreatFinding(
                    finding_id=f"find_{int(time.time() * 1000)}",
                    threat_id="BEHAVIOR001",
                    category=ThreatCategory.ANOMALY,
                    severity=severity,
                    location=behavior_data.get("source", "unknown"),
                    description="Suspicious behavioral pattern detected",
                    evidence={"indicators": suspicious_indicators, "behavior": behavior_data},
                    remediation="Review and verify this activity"
                )
                findings.append(finding)
            
            self.findings.extend(findings)
            return findings
    
    def start_scan(
        self,
        scan_type: ScanType,
        targets: List[str]
    ) -> str:
        """Start a comprehensive scan"""
        with self._lock:
            scan_id = f"scan_{int(time.time() * 1000)}"
            
            result = ScanResult(
                scan_id=scan_id,
                scan_type=scan_type,
                started_at=datetime.utcnow(),
                status="running"
            )
            
            self.scan_results.append(result)
            
            return scan_id
    
    def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a scan"""
        with self._lock:
            for result in self.scan_results:
                if result.scan_id == scan_id:
                    return {
                        "scan_id": result.scan_id,
                        "scan_type": result.scan_type.value,
                        "started_at": result.started_at.isoformat(),
                        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                        "status": result.status,
                        "findings_count": len(result.findings),
                        "scanned_items": result.scanned_items
                    }
            return None
    
    def get_findings(
        self,
        category: Optional[ThreatCategory] = None,
        severity: Optional[ThreatSeverity] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get findings with filters"""
        with self._lock:
            results = []
            
            for finding in reversed(self.findings):
                if category and finding.category != category:
                    continue
                if severity and finding.severity != severity:
                    continue
                if resolved is not None and finding.resolved != resolved:
                    continue
                
                results.append({
                    "finding_id": finding.finding_id,
                    "threat_id": finding.threat_id,
                    "category": finding.category.value,
                    "severity": finding.severity.name,
                    "location": finding.location,
                    "description": finding.description,
                    "remediation": finding.remediation,
                    "resolved": finding.resolved,
                    "timestamp": finding.timestamp.isoformat()
                })
                
                if len(results) >= limit:
                    break
            
            return results
    
    def resolve_finding(self, finding_id: str) -> bool:
        """Mark a finding as resolved"""
        with self._lock:
            for finding in self.findings:
                if finding.finding_id == finding_id:
                    finding.resolved = True
                    return True
            return False
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat scanning summary"""
        with self._lock:
            by_category = defaultdict(int)
            by_severity = defaultdict(int)
            unresolved = 0
            
            for finding in self.findings:
                by_category[finding.category.value] += 1
                by_severity[finding.severity.name] += 1
                if not finding.resolved:
                    unresolved += 1
            
            return {
                "total_findings": len(self.findings),
                "unresolved": unresolved,
                "by_category": dict(by_category),
                "by_severity": dict(by_severity),
                "threat_definitions": len(self.threat_definitions),
                "scans_performed": len(self.scan_results)
            }
    
    def add_threat_definition(
        self,
        name: str,
        category: ThreatCategory,
        severity: ThreatSeverity,
        patterns: List[str],
        description: str,
        remediation: str
    ) -> str:
        """Add a custom threat definition"""
        with self._lock:
            threat_id = f"CUSTOM_{int(time.time() * 1000)}"
            
            self.threat_definitions[threat_id] = ThreatDefinition(
                threat_id=threat_id,
                name=name,
                category=category,
                severity=severity,
                patterns=patterns,
                description=description,
                remediation=remediation
            )
            
            return threat_id


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> ThreatScanner:
    """Factory function to create ThreatScanner module"""
    return ThreatScanner(config)


if __name__ == "__main__":
    scanner = ThreatScanner()
    
    # Test code scanning
    test_code = '''
import os
password = "super_secret_password"
api_key = "sk-1234567890abcdef"
os.system(user_input + " some command")
DEBUG = True
'''
    
    findings = scanner.scan_code(test_code, "test_file.py")
    print(f"Found {len(findings)} threats:")
    for f in findings:
        print(f"  [{f.severity.name}] {f.description} at {f.location}")
    
    # Test config scanning
    config = {"debug": True, "api_key": "sk-secret123456"}
    config_findings = scanner.scan_config(config, "app_config")
    print(f"\nConfig findings: {len(config_findings)}")
    
    # Summary
    print("\nThreat Summary:", json.dumps(scanner.get_threat_summary(), indent=2))
