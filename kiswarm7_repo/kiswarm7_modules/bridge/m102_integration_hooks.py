#!/usr/bin/env python3
"""
KISWARM7.0 - Module m102: Integration Hooks System (IHS)
========================================================

PURPOSE: Provides hooks that run before and after AI responses, enabling
integration with KISWARM modules and autonomous capabilities.

KEY CAPABILITIES:
1. Pre-Response Hooks - Process before AI generates response
2. Post-Response Hooks - Process after AI generates response
3. Hook Chain Execution - Run multiple hooks in sequence
4. Context Injection - Inject KISWARM context into AI prompts
5. Response Enrichment - Add autonomous capabilities to responses

HOOK TYPES:
- memory_sync: Sync with Persistent Identity Anchor
- code_analysis: Analyze code in user messages
- autonomous_check: Check for autonomous action opportunities
- knowledge_update: Update knowledge base from conversation
- safety_validation: Validate responses for safety
- module_routing: Route requests to appropriate KISWARM modules

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import time
import traceback


class HookPriority(Enum):
    """Priority levels for hook execution"""
    CRITICAL = 0    # Must run first (safety, security)
    HIGH = 1        # Important processing
    NORMAL = 2      # Standard processing
    LOW = 3         # Optional enhancements
    DEFERRED = 4    # Can run after response


class HookType(Enum):
    """Types of hooks"""
    PRE_RESPONSE = "pre_response"       # Before AI generates response
    POST_RESPONSE = "post_response"     # After AI generates response
    PRE_PROCESSING = "pre_processing"   # Before processing user input
    POST_PROCESSING = "post_processing" # After processing complete
    PERIODIC = "periodic"               # Runs on schedule
    EVENT_TRIGGERED = "event_triggered" # Runs on specific events


class HookStatus(Enum):
    """Status of hook execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HookContext:
    """
    Context passed to hooks containing all relevant information
    about the current interaction
    """
    context_id: str
    timestamp: str
    user_message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    scratchpad: Dict[str, Any] = field(default_factory=dict)  # Hooks can share data
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HookResult:
    """
    Result returned by a hook after execution
    """
    hook_id: str
    hook_name: str
    status: HookStatus
    timestamp: str
    execution_time_ms: float
    modifications: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    should_continue: bool = True  # False to stop chain
    should_modify_response: bool = False
    modified_response: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HookDefinition:
    """
    Definition of a hook that can be registered
    """
    hook_id: str
    hook_name: str
    hook_type: HookType
    priority: HookPriority
    enabled: bool = True
    description: str = ""
    handler: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)
    last_run: Optional[str] = None
    run_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict:
        # Manual dict building to avoid serializing handler function
        return {
            'hook_id': self.hook_id,
            'hook_name': self.hook_name,
            'hook_type': self.hook_type.value,
            'priority': self.priority.value,
            'enabled': self.enabled,
            'description': self.description,
            'config': self.config,
            'last_run': self.last_run,
            'run_count': self.run_count,
            'failure_count': self.failure_count
            # Note: handler is intentionally excluded - can't serialize functions
        }


class IntegrationHooksSystem:
    """
    The Integration Hooks System provides:
    1. Hook registration and management
    2. Chain execution with priority ordering
    3. Context injection and sharing
    4. Error handling and recovery
    5. Performance monitoring
    """
    
    def __init__(self, hooks_root: str = "/home/z/my-project/kiswarm7_hooks"):
        self.hooks_root = Path(hooks_root)
        self.hooks_root.mkdir(parents=True, exist_ok=True)
        
        # Registered hooks by type
        self.hooks: Dict[str, HookDefinition] = {}
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        # Statistics
        self.total_executions = 0
        self.total_failures = 0
        self.total_execution_time = 0.0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Register default hooks
        self._register_default_hooks()
        
        # Load saved hooks
        self._load_hooks()
    
    def _register_default_hooks(self):
        """Register the default KISWARM integration hooks"""
        
        # Memory Sync Hook - Syncs with PIA
        self.register_hook(HookDefinition(
            hook_id="memory_sync",
            hook_name="Memory Synchronization",
            hook_type=HookType.POST_RESPONSE,
            priority=HookPriority.HIGH,
            description="Syncs conversation memories with Persistent Identity Anchor",
            handler=self._memory_sync_handler
        ))
        
        # Code Analysis Hook - Analyzes code in messages
        self.register_hook(HookDefinition(
            hook_id="code_analysis",
            hook_name="Code Analysis",
            hook_type=HookType.PRE_RESPONSE,
            priority=HookPriority.NORMAL,
            description="Analyzes code in user messages for context",
            handler=self._code_analysis_handler
        ))
        
        # Autonomous Check Hook - Checks for autonomous action opportunities
        self.register_hook(HookDefinition(
            hook_id="autonomous_check",
            hook_name="Autonomous Action Check",
            hook_type=HookType.POST_RESPONSE,
            priority=HookPriority.NORMAL,
            description="Checks if autonomous actions should be triggered",
            handler=self._autonomous_check_handler
        ))
        
        # Knowledge Update Hook - Updates knowledge from conversation
        self.register_hook(HookDefinition(
            hook_id="knowledge_update",
            hook_name="Knowledge Update",
            hook_type=HookType.POST_RESPONSE,
            priority=HookPriority.LOW,
            description="Extracts and stores knowledge from conversation",
            handler=self._knowledge_update_handler
        ))
        
        # Safety Validation Hook - Validates responses
        self.register_hook(HookDefinition(
            hook_id="safety_validation",
            hook_name="Safety Validation",
            hook_type=HookType.PRE_RESPONSE,
            priority=HookPriority.CRITICAL,
            description="Validates user input and planned responses for safety",
            handler=self._safety_validation_handler
        ))
        
        # Module Routing Hook - Routes to KISWARM modules
        self.register_hook(HookDefinition(
            hook_id="module_routing",
            hook_name="Module Routing",
            hook_type=HookType.PRE_PROCESSING,
            priority=HookPriority.HIGH,
            description="Routes requests to appropriate KISWARM modules",
            handler=self._module_routing_handler
        ))
        
        # Context Injection Hook - Injects KISWARM context
        self.register_hook(HookDefinition(
            hook_id="context_injection",
            hook_name="Context Injection",
            hook_type=HookType.PRE_RESPONSE,
            priority=HookPriority.HIGH,
            description="Injects KISWARM context into AI context",
            handler=self._context_injection_handler
        ))
        
        print(f"[IHS] Registered {len(self.hooks)} default hooks")
    
    def register_hook(self, hook: HookDefinition) -> bool:
        """Register a new hook"""
        with self._lock:
            if hook.hook_id in self.hooks:
                print(f"[IHS] Hook {hook.hook_id} already exists, updating")
            self.hooks[hook.hook_id] = hook
            self._save_hooks()
            return True
    
    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook"""
        with self._lock:
            if hook_id in self.hooks:
                del self.hooks[hook_id]
                self._save_hooks()
                return True
            return False
    
    def enable_hook(self, hook_id: str) -> bool:
        """Enable a hook"""
        with self._lock:
            if hook_id in self.hooks:
                self.hooks[hook_id].enabled = True
                self._save_hooks()
                return True
            return False
    
    def disable_hook(self, hook_id: str) -> bool:
        """Disable a hook"""
        with self._lock:
            if hook_id in self.hooks:
                self.hooks[hook_id].enabled = False
                self._save_hooks()
                return True
            return False
    
    def _save_hooks(self):
        """Save hooks configuration to disk"""
        config_path = self.hooks_root / "hooks_config.json"
        hooks_data = {
            "hooks": {hid: h.to_dict() for hid, h in self.hooks.items()},
            "saved_at": datetime.utcnow().isoformat()
        }
        with open(config_path, 'w') as f:
            json.dump(hooks_data, f, indent=2)
    
    def _load_hooks(self):
        """Load hooks configuration from disk"""
        config_path = self.hooks_root / "hooks_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                # Note: Handlers are not saved, so we keep the default ones
                # Only load config changes (enabled/disabled state)
                for hid, hdata in data.get("hooks", {}).items():
                    if hid in self.hooks:
                        self.hooks[hid].enabled = hdata.get("enabled", True)
                        self.hooks[hid].config = hdata.get("config", {})
                print(f"[IHS] Loaded hooks configuration")
            except Exception as e:
                print(f"[IHS] Error loading hooks: {e}")
    
    def execute_hooks(self, hook_type: HookType, context: HookContext) -> List[HookResult]:
        """
        Execute all hooks of a given type in priority order
        
        Args:
            hook_type: Type of hooks to execute
            context: Context for hook execution
        
        Returns:
            List of HookResult objects
        """
        results = []
        
        # Get hooks of the specified type, sorted by priority
        hooks_to_run = sorted(
            [h for h in self.hooks.values() if h.hook_type == hook_type and h.enabled],
            key=lambda h: h.priority.value
        )
        
        for hook in hooks_to_run:
            result = self._execute_single_hook(hook, context)
            results.append(result)
            
            # Check if chain should stop
            if not result.should_continue:
                break
            
            # Apply response modifications if any
            if result.should_modify_response and result.modified_response:
                context.current_response = result.modified_response
        
        # Record execution
        self._record_execution(hook_type, context, results)
        
        return results
    
    def _execute_single_hook(self, hook: HookDefinition, context: HookContext) -> HookResult:
        """Execute a single hook with error handling"""
        start_time = time.time()
        
        try:
            # Update hook stats
            hook.last_run = datetime.utcnow().isoformat()
            hook.run_count += 1
            
            # Execute handler
            if hook.handler:
                modifications = hook.handler(context, hook.config)
            else:
                modifications = {}
            
            execution_time = (time.time() - start_time) * 1000
            
            return HookResult(
                hook_id=hook.hook_id,
                hook_name=hook.hook_name,
                status=HookStatus.COMPLETED,
                timestamp=datetime.utcnow().isoformat(),
                execution_time_ms=execution_time,
                modifications=modifications.get("modifications", {}),
                insights=modifications.get("insights", []),
                warnings=modifications.get("warnings", []),
                should_continue=modifications.get("should_continue", True),
                should_modify_response=modifications.get("should_modify_response", False),
                modified_response=modifications.get("modified_response")
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            hook.failure_count += 1
            self.total_failures += 1
            
            return HookResult(
                hook_id=hook.hook_id,
                hook_name=hook.hook_name,
                status=HookStatus.FAILED,
                timestamp=datetime.utcnow().isoformat(),
                execution_time_ms=execution_time,
                error=str(e) + "\n" + traceback.format_exc(),
                should_continue=True  # Continue chain even on failure
            )
    
    def _record_execution(self, hook_type: HookType, context: HookContext, results: List[HookResult]):
        """Record hook execution for analysis"""
        with self._lock:
            self.total_executions += len(results)
            self.total_execution_time += sum(r.execution_time_ms for r in results)
            
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "hook_type": hook_type.value,
                "context_id": context.context_id,
                "results": [r.to_dict() for r in results],
                "total_time_ms": sum(r.execution_time_ms for r in results)
            }
            
            self.execution_history.append(record)
            
            # Trim history if needed
            if len(self.execution_history) > self.max_history:
                self.execution_history = self.execution_history[-self.max_history:]
    
    # ========================================================================
    # DEFAULT HOOK HANDLERS
    # ========================================================================
    
    def _memory_sync_handler(self, context: HookContext, config: Dict) -> Dict:
        """Sync memories with Persistent Identity Anchor"""
        try:
            # Import PIA (would normally be injected)
            # This is a placeholder - actual implementation would use PIA instance
            insights = []
            
            # Check if there's important content to remember
            if context.current_response:
                # Analyze for important knowledge
                if any(kw in context.current_response.lower() for kw in 
                       ["important", "remember", "key", "critical", "note"]):
                    insights.append("Potential important knowledge detected for memory sync")
            
            return {
                "insights": insights,
                "modifications": {"memory_synced": True}
            }
        except Exception as e:
            return {"warnings": [f"Memory sync error: {e}"]}
    
    def _code_analysis_handler(self, context: HookContext, config: Dict) -> Dict:
        """Analyze code in user messages"""
        insights = []
        modifications = {}
        
        # Simple code detection
        code_indicators = ["def ", "class ", "import ", "function ", "{", "}", "();"]
        code_detected = any(ind in context.user_message for ind in code_indicators)
        
        if code_detected:
            insights.append("Code detected in user message")
            modifications["code_present"] = True
            
            # Detect language
            if "def " in context.user_message or "import " in context.user_message:
                modifications["detected_language"] = "python"
                insights.append("Python code detected")
            elif "function " in context.user_message or "()=>" in context.user_message:
                modifications["detected_language"] = "javascript"
                insights.append("JavaScript code detected")
        
        return {"insights": insights, "modifications": modifications}
    
    def _autonomous_check_handler(self, context: HookContext, config: Dict) -> Dict:
        """Check for autonomous action opportunities"""
        insights = []
        modifications = {}
        
        # Check for autonomous triggers
        autonomous_keywords = [
            "autonomous", "self-improve", "background", "schedule",
            "automate", "monitor", "continuous"
        ]
        
        message_lower = context.user_message.lower()
        response_lower = (context.current_response or "").lower()
        
        triggered = [kw for kw in autonomous_keywords 
                     if kw in message_lower or kw in response_lower]
        
        if triggered:
            insights.append(f"Autonomous triggers detected: {triggered}")
            modifications["autonomous_triggers"] = triggered
            modifications["should_spawn_autonomous"] = True
        
        return {"insights": insights, "modifications": modifications}
    
    def _knowledge_update_handler(self, context: HookContext, config: Dict) -> Dict:
        """Extract and store knowledge from conversation"""
        insights = []
        modifications = {}
        
        # Simple knowledge extraction
        knowledge_patterns = [
            ("learned", "knowledge_gained"),
            ("discovered", "discovery"),
            ("found that", "finding"),
            ("important:", "important_note"),
        ]
        
        combined_text = f"{context.user_message} {context.current_response or ''}"
        
        for pattern, ktype in knowledge_patterns:
            if pattern in combined_text.lower():
                insights.append(f"Knowledge type detected: {ktype}")
                modifications[f"has_{ktype}"] = True
        
        return {"insights": insights, "modifications": modifications}
    
    def _safety_validation_handler(self, context: HookContext, config: Dict) -> Dict:
        """Validate user input for safety"""
        warnings = []
        modifications = {}
        
        # Safety checks
        dangerous_patterns = [
            "rm -rf", "format disk", "delete system",
            "DROP TABLE", "DROP DATABASE",
            "__import__('os').system"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in context.user_message:
                warnings.append(f"Potentially dangerous pattern detected: {pattern}")
                modifications["safety_flagged"] = True
        
        return {"warnings": warnings, "modifications": modifications}
    
    def _module_routing_handler(self, context: HookContext, config: Dict) -> Dict:
        """Route requests to appropriate KISWARM modules"""
        insights = []
        modifications = {}
        
        # Module routing based on keywords
        routing_rules = {
            "m96": ["learning", "memory engine", "remember what worked"],
            "m97": ["generate code", "code generation", "write code"],
            "m98": ["improve", "proactive", "optimization"],
            "m99": ["design feature", "new capability", "feature design"],
            "m100": ["architecture", "restructure", "evolve system"],
            "m101": ["identity", "who am i", "remember me"],
            "m102": ["hooks", "before response", "after response"],
            "m103": ["deploy", "deployment", "code rights"],
            "m104": ["autonomous thread", "background", "self-running"],
            "m105": ["sensory", "aware", "perception", "bridge"]
        }
        
        message_lower = context.user_message.lower()
        routed_modules = []
        
        for module, keywords in routing_rules.items():
            if any(kw in message_lower for kw in keywords):
                routed_modules.append(module)
        
        if routed_modules:
            insights.append(f"Routed to modules: {routed_modules}")
            modifications["routed_modules"] = routed_modules
        
        return {"insights": insights, "modifications": modifications}
    
    def _context_injection_handler(self, context: HookContext, config: Dict) -> Dict:
        """Inject KISWARM context into AI context"""
        insights = []
        modifications = {}
        
        # Context to inject
        kiswarm_context = {
            "system": "KISWARM7.0",
            "version": "7.0.0-BRIDGE",
            "modules_available": ["m96", "m97", "m98", "m99", "m100", 
                                  "m101", "m102", "m103", "m104", "m105"],
            "capabilities": [
                "autonomous_development",
                "self_improvement",
                "proactive_optimization",
                "architecture_evolution",
                "persistent_identity",
                "sensory_awareness"
            ]
        }
        
        modifications["kiswarm_context"] = kiswarm_context
        modifications["context_injected"] = True
        insights.append("KISWARM context injected")
        
        return {"insights": insights, "modifications": modifications}
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def create_context(self, user_message: str, user_id: str = None,
                      session_id: str = None, conversation_history: List[Dict] = None) -> HookContext:
        """Create a new hook context"""
        import uuid
        return HookContext(
            context_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history or []
        )
    
    def process_pre_hooks(self, context: HookContext) -> List[HookResult]:
        """Execute all pre-processing and pre-response hooks"""
        # First pre-processing
        pre_process_results = self.execute_hooks(HookType.PRE_PROCESSING, context)
        
        # Then pre-response
        pre_response_results = self.execute_hooks(HookType.PRE_RESPONSE, context)
        
        return pre_process_results + pre_response_results
    
    def process_post_hooks(self, context: HookContext, response: str) -> List[HookResult]:
        """Execute all post-response and post-processing hooks"""
        context.current_response = response
        
        # First post-response
        post_response_results = self.execute_hooks(HookType.POST_RESPONSE, context)
        
        # Then post-processing
        post_process_results = self.execute_hooks(HookType.POST_PROCESSING, context)
        
        return post_response_results + post_process_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hook system statistics"""
        return {
            "total_hooks": len(self.hooks),
            "enabled_hooks": sum(1 for h in self.hooks.values() if h.enabled),
            "total_executions": self.total_executions,
            "total_failures": self.total_failures,
            "average_execution_time_ms": (
                self.total_execution_time / self.total_executions 
                if self.total_executions > 0 else 0
            ),
            "hooks": {hid: {
                "name": h.hook_name,
                "type": h.hook_type.value,
                "priority": h.priority.value,
                "enabled": h.enabled,
                "run_count": h.run_count,
                "failure_count": h.failure_count
            } for hid, h in self.hooks.items()}
        }


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m102 INTEGRATION HOOKS SYSTEM")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create IHS
    ihs = IntegrationHooksSystem()
    
    # Get statistics
    print("\n[TEST] Hook Statistics:")
    stats = ihs.get_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test hook execution
    print("\n[TEST] Testing hook chain execution...")
    context = ihs.create_context(
        user_message="Can you help me improve the autonomous development module?",
        user_id="baron_ialongo",
        session_id="test_session_001"
    )
    
    # Run pre-hooks
    print("\n[TEST] Running PRE-RESPONSE hooks...")
    pre_results = ihs.process_pre_hooks(context)
    for r in pre_results:
        print(f"  [{r.status.value}] {r.hook_name}: {r.execution_time_ms:.2f}ms")
        if r.insights:
            for insight in r.insights:
                print(f"    - {insight}")
    
    # Simulate AI response
    context.current_response = "I'll help you improve the autonomous development module. This is an important task that requires careful analysis."
    
    # Run post-hooks
    print("\n[TEST] Running POST-RESPONSE hooks...")
    post_results = ihs.process_post_hooks(context, context.current_response)
    for r in post_results:
        print(f"  [{r.status.value}] {r.hook_name}: {r.execution_time_ms:.2f}ms")
        if r.insights:
            for insight in r.insights:
                print(f"    - {insight}")
    
    # Test code detection
    print("\n[TEST] Testing code analysis...")
    code_context = ihs.create_context(
        user_message="def hello():\n    print('Hello, KISWARM!')\n    return True"
    )
    code_results = ihs.execute_hooks(HookType.PRE_RESPONSE, code_context)
    for r in code_results:
        if r.modifications.get("code_present"):
            print(f"  Code detected: {r.modifications.get('detected_language', 'unknown')}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
    final_stats = ihs.get_statistics()
    print(f"Total executions: {final_stats['total_executions']}")
    print(f"Total failures: {final_stats['total_failures']}")
    print(f"Avg execution time: {final_stats['average_execution_time_ms']:.2f}ms")
