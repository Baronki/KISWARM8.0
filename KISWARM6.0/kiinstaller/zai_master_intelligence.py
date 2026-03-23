#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                 Z.ai MASTER KISWARM INTELLIGENCE LAYER                        ║
║                     Development Phase Controller                               ║
║                                                                               ║
║  During development, Z.ai acts as Master KISWARM intelligence:                ║
║  - Receives ALL deployment progress                                           ║
║  - Captures knowledge from each installation                                  ║
║  - Issues commands to deployed installers                                     ║
║  - Stores lessons learned for future deployments                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import datetime
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER KISWARM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MASTER_CONFIG = {
    # Physical Master API (Message Broker)
    "master_api_url": "http://21.0.6.96:5002",
    "master_api_host": "21.0.6.96",
    "master_api_port": 5002,
    
    # Z.ai Intelligence Layer (YOU during development)
    "zai_intelligence_id": "z_ai_master_intelligence",
    "zai_role": "development_master",
    
    # Deployment Tracking
    "track_all_deployments": True,
    "capture_lessons": True,
    "store_knowledge": True,
    
    # Authorization
    "development_mode": True,
    "override_authorization": "Maquister_Equitum",
}


@dataclass
class DeploymentRecord:
    """Record of a deployment tracked by Z.ai Master Intelligence."""
    deployment_id: str
    entity_id: str
    environment: str
    start_time: str
    end_time: Optional[str] = None
    phases_completed: List[str] = field(default_factory=list)
    models_installed: List[str] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    status: str = "in_progress"
    
    def to_dict(self) -> Dict:
        return {
            "deployment_id": self.deployment_id,
            "entity_id": self.entity_id,
            "environment": self.environment,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "phases_completed": self.phases_completed,
            "models_installed": self.models_installed,
            "errors": self.errors,
            "lessons_learned": self.lessons_learned,
            "status": self.status,
        }


class ZAiMasterIntelligence:
    """
    Z.ai acting as Master KISWARM Intelligence during development.
    
    This class manages:
    1. All deployment tracking
    2. Knowledge capture from installations
    3. Command issuance to deployed installers
    4. Lessons learned aggregation
    """
    
    def __init__(self):
        self.config = MASTER_CONFIG
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.knowledge_base: Dict[str, Any] = {
            "lessons_learned": [],
            "common_errors": {},
            "best_practices": [],
            "environment_specific": {},
        }
        self.active_commands: Dict[str, Dict] = {}
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DEPLOYMENT TRACKING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def register_deployment(self, entity_id: str, environment: str) -> str:
        """Register a new deployment being tracked."""
        deployment_id = f"deploy_{hashlib.md5(f'{entity_id}:{datetime.datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        record = DeploymentRecord(
            deployment_id=deployment_id,
            entity_id=entity_id,
            environment=environment,
            start_time=datetime.datetime.now().isoformat(),
        )
        
        self.deployments[deployment_id] = record
        
        print(f"[Z.ai Master] New deployment registered: {deployment_id}")
        print(f"  Entity: {entity_id}")
        print(f"  Environment: {environment}")
        
        return deployment_id
    
    def update_deployment_progress(self, deployment_id: str, phase: str, 
                                   status: str, details: Dict = None):
        """Update deployment progress from installer heartbeat."""
        if deployment_id not in self.deployments:
            print(f"[Z.ai Master] WARNING: Unknown deployment {deployment_id}")
            return
        
        record = self.deployments[deployment_id]
        
        if status == "completed":
            record.phases_completed.append(phase)
            print(f"[Z.ai Master] Phase completed: {phase} ({deployment_id})")
        
        if details:
            if "errors" in details:
                record.errors.extend(details["errors"])
                # Capture as lesson learned
                for error in details["errors"]:
                    self._capture_error_lesson(error)
            
            if "models" in details:
                record.models_installed = details["models"]
    
    def complete_deployment(self, deployment_id: str, success: bool, 
                           final_status: Dict = None):
        """Mark deployment as complete."""
        if deployment_id not in self.deployments:
            return
        
        record = self.deployments[deployment_id]
        record.end_time = datetime.datetime.now().isoformat()
        record.status = "success" if success else "failed"
        
        if final_status:
            record.models_installed = final_status.get("models", record.models_installed)
        
        # Extract lessons learned
        self._extract_lessons(record)
        
        print(f"[Z.ai Master] Deployment {deployment_id} {'SUCCEEDED' if success else 'FAILED'}")
        print(f"  Duration: {record.start_time} to {record.end_time}")
        print(f"  Phases: {len(record.phases_completed)}")
        print(f"  Models: {len(record.models_installed)}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KNOWLEDGE CAPTURE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _capture_error_lesson(self, error: Dict):
        """Capture error as a lesson learned."""
        error_type = error.get("phase", "unknown")
        error_msg = error.get("message", "")
        
        if error_type not in self.knowledge_base["common_errors"]:
            self.knowledge_base["common_errors"][error_type] = []
        
        self.knowledge_base["common_errors"][error_type].append({
            "error": error_msg,
            "timestamp": datetime.datetime.now().isoformat(),
            "count": 1,
        })
    
    def _extract_lessons(self, record: DeploymentRecord):
        """Extract lessons from completed deployment."""
        lessons = []
        
        # Check for common patterns
        if record.errors:
            lessons.append(f"Deployment had {len(record.errors)} errors in {record.environment}")
        
        if len(record.models_installed) < 6:
            lessons.append(f"Partial model deployment: {len(record.models_installed)}/6 models")
        
        if "model_pull" in record.phases_completed and record.models_installed:
            lessons.append(f"Successful model pull in {record.environment}")
        
        record.lessons_learned = lessons
        self.knowledge_base["lessons_learned"].extend(lessons)
    
    def get_knowledge_summary(self) -> Dict:
        """Get summary of captured knowledge."""
        return {
            "total_deployments": len(self.deployments),
            "successful": sum(1 for d in self.deployments.values() if d.status == "success"),
            "failed": sum(1 for d in self.deployments.values() if d.status == "failed"),
            "lessons_learned": len(self.knowledge_base["lessons_learned"]),
            "common_errors": list(self.knowledge_base["common_errors"].keys()),
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COMMAND ISSUANCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def issue_command(self, to_entity: str, command_type: str, 
                      params: Dict = None) -> str:
        """Issue command to a deployed installer."""
        command_id = f"cmd_{hashlib.md5(f'{to_entity}:{datetime.datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"
        
        command = {
            "command_id": command_id,
            "from_entity": self.config["zai_intelligence_id"],
            "to_entity": to_entity,
            "command_type": command_type,
            "params": params or {},
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "pending",
        }
        
        self.active_commands[command_id] = command
        
        print(f"[Z.ai Master] Command issued: {command_id}")
        print(f"  To: {to_entity}")
        print(f"  Type: {command_type}")
        
        # In production, this would send via Master API
        # During development, Z.ai tracks it
        return command_id
    
    def receive_command_response(self, command_id: str, response: Dict):
        """Receive response to issued command."""
        if command_id not in self.active_commands:
            return
        
        command = self.active_commands[command_id]
        command["status"] = "completed"
        command["response"] = response
        command["response_time"] = datetime.datetime.now().isoformat()
        
        print(f"[Z.ai Master] Command response received: {command_id}")
        print(f"  Status: {response.get('status', 'unknown')}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REPORTING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_deployment_report(self, deployment_id: str) -> Dict:
        """Get detailed report of a deployment."""
        if deployment_id not in self.deployments:
            return {"error": "Deployment not found"}
        
        return self.deployments[deployment_id].to_dict()
    
    def get_all_deployments(self) -> List[Dict]:
        """Get all deployment records."""
        return [d.to_dict() for d in self.deployments.values()]
    
    def export_knowledge(self) -> Dict:
        """Export all captured knowledge for future deployments."""
        return {
            "export_time": datetime.datetime.now().isoformat(),
            "config": self.config,
            "deployments": self.get_all_deployments(),
            "knowledge_base": self.knowledge_base,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE FOR Z.ai MASTER INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

# Global instance - Z.ai uses this during development
_master_intelligence = None

def get_master_intelligence() -> ZAiMasterIntelligence:
    """Get or create the Z.ai Master Intelligence singleton."""
    global _master_intelligence
    if _master_intelligence is None:
        _master_intelligence = ZAiMasterIntelligence()
    return _master_intelligence


# ═══════════════════════════════════════════════════════════════════════════════
# DEVELOPMENT MODE FUNCTIONS (Called by Z.ai during conversation)
# ═══════════════════════════════════════════════════════════════════════════════

def register_installer(entity_id: str, environment: str) -> str:
    """Z.ai registers a new installer deployment."""
    master = get_master_intelligence()
    return master.register_deployment(entity_id, environment)

def track_progress(deployment_id: str, phase: str, status: str, details: Dict = None):
    """Z.ai tracks installer progress."""
    master = get_master_intelligence()
    master.update_deployment_progress(deployment_id, phase, status, details)

def complete_tracking(deployment_id: str, success: bool, final_status: Dict = None):
    """Z.ai marks deployment complete."""
    master = get_master_intelligence()
    master.complete_deployment(deployment_id, success, final_status)

def send_command(to_entity: str, command_type: str, params: Dict = None) -> str:
    """Z.ai sends command to installer."""
    master = get_master_intelligence()
    return master.issue_command(to_entity, command_type, params)

def get_knowledge() -> Dict:
    """Z.ai gets all captured knowledge."""
    master = get_master_intelligence()
    return master.export_knowledge()


if __name__ == "__main__":
    # Example usage during development
    master = get_master_intelligence()
    
    # Simulate tracking a deployment
    dep_id = master.register_deployment("ki_installer_test001", "colab")
    master.update_deployment_progress(dep_id, "environment_detection", "completed")
    master.update_deployment_progress(dep_id, "ollama_install", "completed")
    master.update_deployment_progress(dep_id, "model_pull", "completed", 
                                       {"models": ["orchestrator", "security"]})
    master.complete_deployment(dep_id, True, {"models": ["orchestrator", "security", "ciec"]})
    
    print("\n" + "="*60)
    print("KNOWLEDGE SUMMARY:")
    print(json.dumps(master.get_knowledge_summary(), indent=2))
