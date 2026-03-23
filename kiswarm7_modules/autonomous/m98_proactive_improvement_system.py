#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m98: Proactive Improvement System
🜃 Level 5 Autonomous Development - Autonomous Improvement
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal
"""

import ast
import time
import uuid
import re
import threading
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

# logger already defined


class ImprovementCategory(Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    RELIABILITY = "reliability"
    TECHNICAL_DEBT = "technical_debt"


class ImprovementPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class ImprovementStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class RiskLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ImprovementOpportunity:
    opportunity_id: str
    category: ImprovementCategory
    priority: ImprovementPriority
    title: str
    description: str
    location: str
    current_state: Dict[str, Any]
    proposed_state: Dict[str, Any]
    impact_prediction: Dict[str, float]
    risk_level: RiskLevel
    effort_estimate: float
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    tags: Set[str] = field(default_factory=set)


@dataclass
class ImprovementResult:
    result_id: str
    proposal_id: str
    success: bool
    actual_impact: Dict[str, float]
    execution_time: float
    issues_encountered: List[str]
    rolled_back: bool
    timestamp: float


class CodeQualityAnalyzer:
    def analyze_code(self, code: str, filename: str = "unknown") -> Dict[str, Any]:
        issues = []
        metrics = {}
        
        try:
            tree = ast.parse(code)
            metrics["lines_of_code"] = len(code.split('\n'))
            metrics["functions"] = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
            metrics["classes"] = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            issues.extend(self._check_complexity(tree))
            issues.extend(self._check_documentation(tree))
        except SyntaxError as e:
            issues.append({"type": "syntax_error", "severity": "critical", "message": str(e)})
        
        quality_score = max(0, 100 - len(issues) * 10)
        return {"filename": filename, "issues": issues, "metrics": metrics, "quality_score": quality_score}
    
    def _check_complexity(self, tree: ast.AST) -> List[Dict]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While)):
                        complexity += 1
                if complexity > 10:
                    issues.append({
                        "type": "high_complexity", "severity": "medium",
                        "message": f"Function '{node.name}' has complexity {complexity}",
                        "function": node.name
                    })
        return issues
    
    def _check_documentation(self, tree: ast.AST) -> List[Dict]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append({
                        "type": "missing_docstring", "severity": "low",
                        "message": f"{node.__class__.__name__[:-3]} '{node.name}' lacks docstring"
                    })
        return issues


class TechnicalDebtAnalyzer:
    def analyze_debt(self, code: str, filename: str = "unknown") -> Dict[str, Any]:
        debt_items = []
        
        # Look for TODO comments
        todo_pattern = r'#\s*(TODO|FIXME|HACK|XXX):?\s*(.+)'
        for match in re.finditer(todo_pattern, code, re.IGNORECASE):
            debt_items.append({
                "type": "todo", "severity": "low",
                "message": match.group(2).strip(),
                "category": match.group(1).upper()
            })
        
        # Look for deprecated patterns
        deprecated = [(r'print\s*\(', "Use logging instead of print()"),
                     (r'except:', "Catch specific exceptions, not bare except")]
        for pattern, message in deprecated:
            for match in re.finditer(pattern, code):
                debt_items.append({"type": "deprecated_pattern", "severity": "medium", "message": message})
        
        debt_score = sum({"critical": 100, "high": 50, "medium": 20, "low": 5}.get(item["severity"], 5)
                        for item in debt_items)
        return {"filename": filename, "debt_items": debt_items, "debt_score": debt_score}


class ProactiveImprovementSystem:
    def __init__(self, auto_improve: bool = False, improvement_interval: int = 3600):
        self.quality_analyzer = CodeQualityAnalyzer()
        self.debt_analyzer = TechnicalDebtAnalyzer()
        self.opportunities: Dict[str, ImprovementOpportunity] = {}
        self.results: Dict[str, ImprovementResult] = {}
        self.auto_improve = auto_improve
        self.improvement_interval = improvement_interval
        self._running = False
        self.stats = {
            "opportunities_found": 0, "improvements_proposed": 0,
            "improvements_implemented": 0, "improvements_rolled_back": 0
        }
        print("Proactive Improvement System initialized")
    
    def analyze_system(self, code_base: Dict[str, str] = None) -> List[ImprovementOpportunity]:
        opportunities = []
        if code_base:
            for filename, code in code_base.items():
                quality_result = self.quality_analyzer.analyze_code(code, filename)
                for issue in quality_result.get("issues", []):
                    opp = self._create_opportunity_from_issue(issue, filename, ImprovementCategory.QUALITY)
                    opportunities.append(opp)
                
                debt_result = self.debt_analyzer.analyze_debt(code, filename)
                for item in debt_result.get("debt_items", []):
                    opp = self._create_opportunity_from_issue(item, filename, ImprovementCategory.TECHNICAL_DEBT)
                    opportunities.append(opp)
        
        for opp in opportunities:
            self.opportunities[opp.opportunity_id] = opp
        self.stats["opportunities_found"] += len(opportunities)
        return opportunities
    
    def _create_opportunity_from_issue(self, issue: Dict, filename: str,
                                       category: ImprovementCategory) -> ImprovementOpportunity:
        severity_to_priority = {"critical": ImprovementPriority.CRITICAL, "high": ImprovementPriority.HIGH,
                               "medium": ImprovementPriority.MEDIUM, "low": ImprovementPriority.LOW}
        severity_to_risk = {"critical": RiskLevel.HIGH, "high": RiskLevel.MEDIUM,
                          "medium": RiskLevel.LOW, "low": RiskLevel.MINIMAL}
        severity = issue.get("severity", "low")
        
        return ImprovementOpportunity(
            opportunity_id=f"opp_{uuid.uuid4().hex[:12]}", category=category,
            priority=severity_to_priority.get(severity, ImprovementPriority.LOW),
            title=f"{issue['type'].replace('_', ' ').title()} in {filename}",
            description=issue.get("message", "Issue detected"), location=filename,
            current_state={"issue": issue}, proposed_state={"resolved": True},
            impact_prediction={"quality": 0.1},
            risk_level=severity_to_risk.get(severity, RiskLevel.LOW),
            effort_estimate=1.0 if severity == "low" else 2.0,
            tags={issue["type"]}
        )
    
    def get_improvement_priorities(self) -> List[ImprovementOpportunity]:
        opportunities = list(self.opportunities.values())
        opportunities.sort(key=lambda o: o.priority.value)
        return opportunities
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "stats": self.stats.copy(),
            "pending_opportunities": len([o for o in self.opportunities.values()
                                         if o.status == ImprovementStatus.PROPOSED]),
            "implemented": len([r for r in self.results.values() if r.success]),
            "rolled_back": len([r for r in self.results.values() if r.rolled_back])
        }


# Singleton and API
_proactive_system: Optional[ProactiveImprovementSystem] = None

def get_proactive_system() -> ProactiveImprovementSystem:
    global _proactive_system
    if _proactive_system is None:
        _proactive_system = ProactiveImprovementSystem()
    return _proactive_system

def analyze_for_improvements(code: str, filename: str = "module.py") -> List[ImprovementOpportunity]:
    return get_proactive_system().analyze_system({filename: code})

def get_priorities() -> List[ImprovementOpportunity]:
    return get_proactive_system().get_improvement_priorities()


if __name__ == "__main__":
    system = ProactiveImprovementSystem()
    test_code = '''
# TODO: Refactor this
def processData(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])
    return result
'''
    opportunities = system.analyze_system({"test.py": test_code})
    print(f"Found {len(opportunities)} opportunities:")
    for opp in opportunities:
        print(f"  - [{opp.priority.name}] {opp.title}")
    print("\n🜂 Proactive Improvement System - Level 5 Autonomous Development")
    print("   Module m98 - OPERATIONAL")
