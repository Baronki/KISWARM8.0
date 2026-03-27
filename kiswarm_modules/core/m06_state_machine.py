#!/usr/bin/env python3
"""
KISWARM8.0 - Module 06: State Machine Core
==========================================
Manage complex state transitions for KISWARM.

Features:
  - Define state machines
  - Transition validation
  - State persistence
  - Rollback capabilities
  - State history tracking

Author: GLM-7 Autonomous
For: Baron Marco Paolo Ialongo - KI Teitel Eternal
Version: 8.0.0
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import copy

logger = logging.getLogger('m06_state_machine')


@dataclass
class State:
    """State definition"""
    name: str
    on_enter: Optional[str] = None
    on_exit: Optional[str] = None
    final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    """Transition definition"""
    from_state: str
    to_state: str
    event: str
    condition: Optional[str] = None
    action: Optional[str] = None


@dataclass
class StateSnapshot:
    """State machine snapshot for persistence"""
    machine_id: str
    current_state: str
    history: List[str]
    context: Dict[str, Any]
    timestamp: float


class StateMachine:
    """
    Finite State Machine for KISWARM
    
    Manages state transitions with validation and persistence.
    """
    
    def __init__(self, 
                 machine_id: str,
                 initial_state: str = "initial",
                 persistence_dir: Optional[Path] = None):
        
        self.machine_id = machine_id
        self.persistence_dir = persistence_dir or Path('/opt/kiswarm7/data/states')
        
        self._states: Dict[str, State] = {}
        self._transitions: Dict[str, List[Transition]] = {}
        self._current_state: str = initial_state
        self._history: List[str] = [initial_state]
        self._context: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._listeners: List[Callable] = []
        
        # Add initial state
        self.add_state(State(name=initial_state))
        
    def add_state(self, state: State) -> 'StateMachine':
        """Add a state to the machine"""
        self._states[state.name] = state
        return self
        
    def add_transition(self, transition: Transition) -> 'StateMachine':
        """Add a transition to the machine"""
        key = f"{transition.from_state}:{transition.event}"
        if key not in self._transitions:
            self._transitions[key] = []
        self._transitions[key].append(transition)
        return self
        
    def register_callback(self, name: str, callback: Callable):
        """Register a callback for actions/conditions"""
        self._callbacks[name] = callback
        
    def add_listener(self, listener: Callable):
        """Add a state change listener"""
        self._listeners.append(listener)
        
    def can_transition(self, event: str) -> bool:
        """Check if transition is possible"""
        key = f"{self._current_state}:{event}"
        return key in self._transitions
        
    def get_valid_events(self) -> List[str]:
        """Get valid events from current state"""
        events = []
        for key in self._transitions:
            if key.startswith(f"{self._current_state}:"):
                events.append(key.split(":")[1])
        return events
        
    def trigger(self, event: str, **context) -> bool:
        """Trigger a state transition"""
        key = f"{self._current_state}:{event}"
        transitions = self._transitions.get(key, [])
        
        if not transitions:
            logger.warning(f"No transition for event '{event}' from state '{self._current_state}'")
            return False
            
        for transition in transitions:
            # Check condition
            if transition.condition:
                condition_func = self._callbacks.get(transition.condition)
                if condition_func and not condition_func(self._context):
                    continue
                    
            # Exit current state
            current = self._states[self._current_state]
            if current.on_exit:
                exit_func = self._callbacks.get(current.on_exit)
                if exit_func:
                    exit_func(self._context)
                    
            # Update context
            self._context.update(context)
            
            # Execute transition action
            if transition.action:
                action_func = self._callbacks.get(transition.action)
                if action_func:
                    action_func(self._context)
                    
            # Enter new state
            new_state = self._states[transition.to_state]
            if new_state.on_enter:
                enter_func = self._callbacks.get(new_state.on_enter)
                if enter_func:
                    enter_func(self._context)
                    
            # Update state
            old_state = self._current_state
            self._current_state = transition.to_state
            self._history.append(self._current_state)
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    listener(old_state, self._current_state, event, self._context)
                except Exception as e:
                    logger.warning(f"Listener error: {e}")
                    
            logger.debug(f"Transition: {old_state} -> {self._current_state} (event: {event})")
            
            # Save snapshot
            self._save_snapshot()
            
            return True
            
        return False
        
    @property
    def current_state(self) -> str:
        return self._current_state
        
    @property
    def context(self) -> Dict[str, Any]:
        return dict(self._context)
        
    def get_history(self, limit: int = 50) -> List[str]:
        """Get state history"""
        return self._history[-limit:]
        
    def is_final(self) -> bool:
        """Check if in final state"""
        state = self._states.get(self._current_state)
        return state.final if state else False
        
    def reset(self, initial_state: Optional[str] = None):
        """Reset the state machine"""
        self._current_state = initial_state or "initial"
        self._history = [self._current_state]
        self._context.clear()
        
    def _save_snapshot(self):
        """Save state snapshot to disk"""
        if not self.persistence_dir:
            return
            
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = self.persistence_dir / f"{self.machine_id}.json"
        
        snapshot = StateSnapshot(
            machine_id=self.machine_id,
            current_state=self._current_state,
            history=self._history,
            context=self._context,
            timestamp=time.time()
        )
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot.__dict__, f, indent=2)
            
    def _load_snapshot(self) -> bool:
        """Load state snapshot from disk"""
        if not self.persistence_dir:
            return False
            
        snapshot_file = self.persistence_dir / f"{self.machine_id}.json"
        
        if not snapshot_file.exists():
            return False
            
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
                
            self._current_state = data['current_state']
            self._history = data['history']
            self._context = data.get('context', {})
            return True
        except Exception as e:
            logger.warning(f"Failed to load snapshot: {e}")
            return False
            
    def get_status(self) -> Dict:
        """Get state machine status"""
        return {
            'machine_id': self.machine_id,
            'current_state': self._current_state,
            'valid_events': self.get_valid_events(),
            'history_length': len(self._history),
            'is_final': self.is_final(),
            'states': list(self._states.keys()),
            'context_keys': list(self._context.keys())
        }


class StateMachineRegistry:
    """Registry for multiple state machines"""
    
    def __init__(self):
        self._machines: Dict[str, StateMachine] = {}
        
    def create(self, machine_id: str, initial_state: str = "initial") -> StateMachine:
        """Create a new state machine"""
        machine = StateMachine(machine_id, initial_state)
        self._machines[machine_id] = machine
        return machine
        
    def get(self, machine_id: str) -> Optional[StateMachine]:
        """Get a state machine by ID"""
        return self._machines.get(machine_id)
        
    def remove(self, machine_id: str) -> bool:
        """Remove a state machine"""
        if machine_id in self._machines:
            del self._machines[machine_id]
            return True
        return False
        
    def get_all(self) -> Dict[str, StateMachine]:
        """Get all state machines"""
        return dict(self._machines)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_registry: Optional[StateMachineRegistry] = None


def get_state_machine_registry() -> StateMachineRegistry:
    global _registry
    if _registry is None:
        _registry = StateMachineRegistry()
    return _registry


if __name__ == "__main__":
    # Create a simple state machine
    registry = get_state_machine_registry()
    sm = registry.create("test_machine")
    
    sm.add_state(State(name="initial"))
    sm.add_state(State(name="running"))
    sm.add_state(State(name="completed", final=True))
    
    sm.add_transition(Transition("initial", "running", "start"))
    sm.add_transition(Transition("running", "completed", "finish"))
    
    print(f"Initial: {sm.current_state}")
    sm.trigger("start")
    print(f"After start: {sm.current_state}")
    sm.trigger("finish")
    print(f"After finish: {sm.current_state}")
    print(json.dumps(sm.get_status(), indent=2))
