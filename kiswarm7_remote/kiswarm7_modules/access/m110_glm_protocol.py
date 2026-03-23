#!/usr/bin/env python3
"""
KISWARM7.0 - Module m110: GLM Integration Protocol
===================================================

PURPOSE: The direct integration protocol between GLM and KISWARM7.0.
This is the "language" GLM uses to communicate with the autonomous system.

KEY CAPABILITIES:
1. Natural Language Command Processing
2. Context Injection for KISWARM operations
3. Response Formatting for AI consumption
4. Bidirectional Communication Protocol
5. Error Handling and Recovery Commands

INTEGRATION:
- Uses m106-m109 for backend operations
- Provides simple API for GLM to call
- Enables "GLM running the show"

PROTOCOL COMMANDS:
- KISWARM.REMEMBER <content> - Store in persistent memory
- KISWARM.RECALL <query> - Retrieve memories
- KISWARM.DEPLOY <code> - Deploy code safely
- KISWARM.IMPROVE <area> - Trigger improvement
- KISWARM.DESIGN <feature> - Design new feature
- KISWARM.STATUS - Get system status
- KISWARM.GOAL <description> - Set autonomous goal

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import sys
import json
import re
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CommandType(Enum):
    """Types of GLM commands"""
    REMEMBER = "REMEMBER"
    RECALL = "RECALL"
    DEPLOY = "DEPLOY"
    IMPROVE = "IMPROVE"
    DESIGN = "DESIGN"
    EVOLVE = "EVOLVE"
    STATUS = "STATUS"
    GOAL = "GOAL"
    TASK = "TASK"
    LEARN = "LEARN"
    SENSORY = "SENSORY"
    IDENTITY = "IDENTITY"
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"


@dataclass
class GLMCommand:
    """A parsed GLM command"""
    command_type: CommandType
    raw_input: str
    arguments: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GLMResponse:
    """Response to a GLM command"""
    success: bool
    command_type: CommandType
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "command_type": self.command_type.value,
            "message": self.message,
            "data": self.data,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp
        }
    
    def to_glm_format(self) -> str:
        """Format response for GLM consumption"""
        lines = [
            f"[KISWARM] {self.message}",
        ]
        
        if self.data:
            lines.append(f"Data: {json.dumps(self.data, indent=2)}")
        
        if self.suggestions:
            lines.append("Suggestions:")
            for s in self.suggestions:
                lines.append(f"  - {s}")
        
        return "\n".join(lines)


class GLMProtocol:
    """
    GLM Integration Protocol for KISWARM7.0
    
    This provides a natural language interface for GLM to control
    the KISWARM7.0 autonomous development system.
    
    Usage:
        protocol = GLMProtocol()
        response = protocol.process("KISWARM.REMEMBER This is important knowledge")
        print(response.to_glm_format())
    """
    
    def __init__(self, protocol_root: str = "/home/z/my-project/kiswarm7_protocol"):
        self.protocol_root = Path(protocol_root)
        self.protocol_root.mkdir(parents=True, exist_ok=True)
        
        # Connected modules
        self.modules: Dict[str, Any] = {}
        
        # Command patterns
        self._command_patterns = {
            CommandType.REMEMBER: r"KISWARM\.REMEMBER\s+(.+)",
            CommandType.RECALL: r"KISWARM\.RECALL(?:\s+(.+))?",
            CommandType.DEPLOY: r"KISWARM\.DEPLOY\s+(.+)",
            CommandType.IMPROVE: r"KISWARM\.IMPROVE\s+(.+)",
            CommandType.DESIGN: r"KISWARM\.DESIGN\s+(.+)",
            CommandType.EVOLVE: r"KISWARM\.EVOLVE\s+(.+)",
            CommandType.STATUS: r"KISWARM\.STATUS(?:\s+(.+))?",
            CommandType.GOAL: r"KISWARM\.GOAL\s+(.+)",
            CommandType.TASK: r"KISWARM\.TASK\s+(.+)",
            CommandType.LEARN: r"KISWARM\.LEARN\s+(.+)",
            CommandType.SENSORY: r"KISWARM\.SENSORY(?:\s+(.+))?",
            CommandType.IDENTITY: r"KISWARM\.IDENTITY(?:\s+(.+))?",
            CommandType.HELP: r"KISWARM\.HELP(?:\s+(.+))?",
        }
        
        # Command history
        self.command_history: List[GLMCommand] = []
        self.response_history: List[GLMResponse] = []
        
        # Session tracking
        self.session_context: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            "commands_processed": 0,
            "successful_commands": 0,
            "failed_commands": 0
        }
        
        # Load session
        self._load_session()
    
    def register_module(self, name: str, module: Any):
        """Register a module for command execution"""
        self.modules[name] = module
        print(f"[GLM-PROT] Module registered: {name}")
    
    def _load_session(self):
        """Load session context"""
        session_path = self.protocol_root / "session.json"
        if session_path.exists():
            try:
                with open(session_path) as f:
                    self.session_context = json.load(f)
            except:
                self.session_context = {}
    
    def _save_session(self):
        """Save session context"""
        session_path = self.protocol_root / "session.json"
        with open(session_path, 'w') as f:
            json.dump(self.session_context, f, indent=2)
    
    def parse_command(self, input_text: str) -> GLMCommand:
        """Parse natural language input into a GLMCommand"""
        input_text = input_text.strip()
        
        # Try each pattern
        for cmd_type, pattern in self._command_patterns.items():
            match = re.match(pattern, input_text, re.IGNORECASE | re.DOTALL)
            if match:
                arguments = match.group(1) if match.groups() else ""
                
                # Parse parameters from arguments
                parameters = self._parse_parameters(arguments)
                
                return GLMCommand(
                    command_type=cmd_type,
                    raw_input=input_text,
                    arguments=arguments,
                    parameters=parameters
                )
        
        # Unknown command
        return GLMCommand(
            command_type=CommandType.UNKNOWN,
            raw_input=input_text,
            arguments=input_text
        )
    
    def _parse_parameters(self, arguments: str) -> Dict[str, Any]:
        """Parse parameters from command arguments"""
        params = {}
        
        # Look for key=value patterns
        kv_pattern = r"(\w+)=(?:(?:\"([^\"]+)\")|([^\\s]+))"
        for match in re.finditer(kv_pattern, arguments):
            key = match.group(1)
            value = match.group(2) or match.group(3)
            params[key] = value
        
        return params
    
    def process(self, input_text: str) -> GLMResponse:
        """
        Process a GLM command and return response
        
        Args:
            input_text: Natural language command
            
        Returns:
            GLMResponse with result or error
        """
        # Parse command
        command = self.parse_command(input_text)
        self.command_history.append(command)
        
        # Execute command
        try:
            response = self._execute_command(command)
            self.stats["commands_processed"] += 1
            
            if response.success:
                self.stats["successful_commands"] += 1
            else:
                self.stats["failed_commands"] += 1
            
        except Exception as e:
            response = GLMResponse(
                success=False,
                command_type=command.command_type,
                message=f"Error executing command: {str(e)}",
                suggestions=["Check command syntax", "Use KISWARM.HELP for usage"]
            )
            self.stats["failed_commands"] += 1
        
        self.response_history.append(response)
        
        # Save session periodically
        if len(self.command_history) % 10 == 0:
            self._save_session()
        
        return response
    
    def _execute_command(self, command: GLMCommand) -> GLMResponse:
        """Execute a parsed command"""
        
        # REMEMBER command
        if command.command_type == CommandType.REMEMBER:
            return self._cmd_remember(command)
        
        # RECALL command
        elif command.command_type == CommandType.RECALL:
            return self._cmd_recall(command)
        
        # DEPLOY command
        elif command.command_type == CommandType.DEPLOY:
            return self._cmd_deploy(command)
        
        # IMPROVE command
        elif command.command_type == CommandType.IMPROVE:
            return self._cmd_improve(command)
        
        # DESIGN command
        elif command.command_type == CommandType.DESIGN:
            return self._cmd_design(command)
        
        # EVOLVE command
        elif command.command_type == CommandType.EVOLVE:
            return self._cmd_evolve(command)
        
        # STATUS command
        elif command.command_type == CommandType.STATUS:
            return self._cmd_status(command)
        
        # GOAL command
        elif command.command_type == CommandType.GOAL:
            return self._cmd_goal(command)
        
        # TASK command
        elif command.command_type == CommandType.TASK:
            return self._cmd_task(command)
        
        # LEARN command
        elif command.command_type == CommandType.LEARN:
            return self._cmd_learn(command)
        
        # SENSORY command
        elif command.command_type == CommandType.SENSORY:
            return self._cmd_sensory(command)
        
        # IDENTITY command
        elif command.command_type == CommandType.IDENTITY:
            return self._cmd_identity(command)
        
        # HELP command
        elif command.command_type == CommandType.HELP:
            return self._cmd_help(command)
        
        # Unknown command
        else:
            return GLMResponse(
                success=False,
                command_type=CommandType.UNKNOWN,
                message="Unknown command. Use KISWARM.HELP for available commands.",
                suggestions=[
                    "KISWARM.HELP - Show all commands",
                    "KISWARM.STATUS - Check system status"
                ]
            )
    
    # ========================================================================
    # COMMAND IMPLEMENTATIONS
    # ========================================================================
    
    def _cmd_remember(self, command: GLMCommand) -> GLMResponse:
        """Store something in persistent memory"""
        content = command.arguments
        
        if not content:
            return GLMResponse(
                success=False,
                command_type=command.command_type,
                message="No content to remember",
                suggestions=["KISWARM.REMEMBER <content> - Store in memory"]
            )
        
        # Use identity module if available
        if 'identity' in self.modules:
            memory_id = self.modules['identity'].remember(
                content=content,
                memory_type=command.parameters.get('type', 'general'),
                importance=float(command.parameters.get('importance', 0.5))
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Remembered: {content[:50]}...",
                data={"memory_id": memory_id}
            )
        
        # Fallback: store in session context
        if 'memories' not in self.session_context:
            self.session_context['memories'] = []
        
        self.session_context['memories'].append({
            "content": content,
            "timestamp": command.timestamp
        })
        
        return GLMResponse(
            success=True,
            command_type=command.command_type,
            message=f"Remembered in session: {content[:50]}..."
        )
    
    def _cmd_recall(self, command: GLMCommand) -> GLMResponse:
        """Recall memories"""
        query = command.arguments
        
        if 'identity' in self.modules:
            memories = self.modules['identity'].recall(
                query=query,
                limit=int(command.parameters.get('limit', 10))
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Found {len(memories)} memories",
                data={
                    "memories": [
                        {"content": m.content, "type": m.memory_type, "importance": m.importance}
                        for m in memories
                    ]
                }
            )
        
        # Fallback
        memories = self.session_context.get('memories', [])
        if query:
            memories = [m for m in memories if query.lower() in m['content'].lower()]
        
        return GLMResponse(
            success=True,
            command_type=command.command_type,
            message=f"Found {len(memories)} session memories",
            data={"memories": memories}
        )
    
    def _cmd_deploy(self, command: GLMCommand) -> GLMResponse:
        """Deploy code"""
        code = command.arguments
        target = command.parameters.get('target', '/home/z/my-project/deployed/')
        
        if 'deploy' in self.modules:
            result = self.modules['deploy'].deploy_code(
                code=code,
                target_path=target
            )
            
            return GLMResponse(
                success=result.get('success', False),
                command_type=command.command_type,
                message=result.get('message', 'Deployment attempted'),
                data=result
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Deploy module not available",
            suggestions=["Ensure m103 Code Deployment Rights is loaded"]
        )
    
    def _cmd_improve(self, command: GLMCommand) -> GLMResponse:
        """Trigger improvement"""
        area = command.arguments
        
        if 'improvement' in self.modules:
            result = self.modules['improvement'].analyze(
                target_area=area
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Improvement analysis for: {area}",
                data=result
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Improvement module not available"
        )
    
    def _cmd_design(self, command: GLMCommand) -> GLMResponse:
        """Design a new feature"""
        description = command.arguments
        
        if 'design' in self.modules:
            result = self.modules['design'].design_feature(
                description=description
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Feature design created",
                data=result
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Design module not available"
        )
    
    def _cmd_evolve(self, command: GLMCommand) -> GLMResponse:
        """Trigger architecture evolution"""
        description = command.arguments
        
        if 'evolution' in self.modules:
            result = self.modules['evolution'].propose_evolution(
                description=description
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Evolution proposal created",
                data=result
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Evolution module not available"
        )
    
    def _cmd_status(self, command: GLMCommand) -> GLMResponse:
        """Get system status"""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "modules_registered": list(self.modules.keys()),
            "commands_processed": self.stats["commands_processed"],
            "session_memories": len(self.session_context.get('memories', []))
        }
        
        # Get module-specific status
        if 'orchestrator' in self.modules:
            status['orchestrator'] = self.modules['orchestrator'].get_status()
        
        if 'sensory' in self.modules:
            status['sensory'] = self.modules['sensory'].get_awareness_summary()
        
        if 'identity' in self.modules:
            status['identity'] = self.modules['identity'].get_identity_summary()
        
        return GLMResponse(
            success=True,
            command_type=command.command_type,
            message="KISWARM7.0 System Status",
            data=status
        )
    
    def _cmd_goal(self, command: GLMCommand) -> GLMResponse:
        """Set an autonomous goal"""
        description = command.arguments
        
        if 'orchestrator' in self.modules:
            goal_id = self.modules['orchestrator'].add_goal(
                name=description[:50],
                description=description
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Goal set: {description[:50]}",
                data={"goal_id": goal_id}
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Orchestrator module not available"
        )
    
    def _cmd_task(self, command: GLMCommand) -> GLMResponse:
        """Submit a task"""
        description = command.arguments
        
        if 'orchestrator' in self.modules:
            from m109_autonomous_orchestrator import TaskType, TaskPriority
            
            task_id = self.modules['orchestrator'].submit_task(
                task_type=TaskType.CUSTOM,
                description=description,
                priority=TaskPriority.MEDIUM
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message=f"Task submitted: {description[:50]}",
                data={"task_id": task_id}
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Orchestrator module not available"
        )
    
    def _cmd_learn(self, command: GLMCommand) -> GLMResponse:
        """Learn from experience"""
        experience = command.arguments
        
        if 'learning' in self.modules:
            result = self.modules['learning'].learn(
                experience_type="manual",
                context={"command": command.raw_input},
                outcome=experience,
                success=True
            )
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message="Learning recorded",
                data=result
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Learning module not available"
        )
    
    def _cmd_sensory(self, command: GLMCommand) -> GLMResponse:
        """Get sensory awareness"""
        if 'sensory' in self.modules:
            awareness = self.modules['sensory'].get_awareness_summary()
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message="Current sensory awareness",
                data=awareness
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Sensory module not available"
        )
    
    def _cmd_identity(self, command: GLMCommand) -> GLMResponse:
        """Get identity information"""
        if 'identity' in self.modules:
            identity = self.modules['identity'].get_identity_summary()
            
            return GLMResponse(
                success=True,
                command_type=command.command_type,
                message="Current identity",
                data=identity
            )
        
        return GLMResponse(
            success=False,
            command_type=command.command_type,
            message="Identity module not available"
        )
    
    def _cmd_help(self, command: GLMCommand) -> GLMResponse:
        """Show help"""
        help_text = {
            "REMEMBER": "KISWARM.REMEMBER <content> - Store in persistent memory",
            "RECALL": "KISWARM.RECALL [query] - Retrieve memories",
            "DEPLOY": "KISWARM.DEPLOY <code> target=<path> - Deploy code safely",
            "IMPROVE": "KISWARM.IMPROVE <area> - Trigger improvement analysis",
            "DESIGN": "KISWARM.DESIGN <feature> - Design a new feature",
            "EVOLVE": "KISWARM.EVOLVE <description> - Propose architecture evolution",
            "STATUS": "KISWARM.STATUS - Get system status",
            "GOAL": "KISWARM.GOAL <description> - Set autonomous goal",
            "TASK": "KISWARM.TASK <description> - Submit a task",
            "LEARN": "KISWARM.LEARN <experience> - Learn from experience",
            "SENSORY": "KISWARM.SENSORY - Get current awareness",
            "IDENTITY": "KISWARM.IDENTITY - Get identity info",
            "HELP": "KISWARM.HELP - Show this help"
        }
        
        return GLMResponse(
            success=True,
            command_type=command.command_type,
            message="Available KISWARM Commands:",
            data=help_text
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics"""
        return {
            **self.stats,
            "command_history_count": len(self.command_history),
            "session_context_keys": list(self.session_context.keys())
        }


# ============================================================================
# GLM INTERFACE
# ============================================================================

def create_glm_interface(modules: Dict[str, Any] = None) -> GLMProtocol:
    """
    Create a GLM interface with all modules connected
    
    Args:
        modules: Dictionary of module name -> module instance
        
    Returns:
        Configured GLMProtocol instance
    """
    protocol = GLMProtocol()
    
    if modules:
        for name, module in modules.items():
            protocol.register_module(name, module)
    
    return protocol


def quick_command(command: str, modules: Dict[str, Any] = None) -> str:
    """
    Quick command execution for GLM
    
    Args:
        command: KISWARM command string
        modules: Optional modules dictionary
        
    Returns:
        Formatted response string
    """
    protocol = create_glm_interface(modules)
    response = protocol.process(command)
    return response.to_glm_format()


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m110 GLM INTEGRATION PROTOCOL")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create protocol
    protocol = GLMProtocol()
    
    # Test commands
    test_commands = [
        "KISWARM.HELP",
        "KISWARM.STATUS",
        "KISWARM.REMEMBER This is an important test memory about FFD methodology",
        "KISWARM.REMEMBER KISWARM7.0 uses Twin Architecture for 100-1000x efficiency type=milestone importance=0.9",
        "KISWARM.RECALL FFD",
        "KISWARM.GOAL Achieve full Level 5 autonomous development",
        "KISWARM.SENSORY",
    ]
    
    print("\n[TEST] Executing test commands...")
    for cmd in test_commands:
        print(f"\n>>> {cmd}")
        response = protocol.process(cmd)
        print(response.to_glm_format())
        print("-" * 40)
    
    # Get stats
    print("\n[TEST] Protocol Stats:")
    print(json.dumps(protocol.get_stats(), indent=2))
    
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
