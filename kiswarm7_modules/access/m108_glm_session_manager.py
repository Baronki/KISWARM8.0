#!/usr/bin/env python3
"""
KISWARM7.0 - Module m108: GLM Session Manager
==============================================

PURPOSE: Manages GLM sessions and maintains context across conversations.
This is the session layer between GLM and KISWARM7.0.

KEY CAPABILITIES:
1. Session Creation and Management
2. Context Preservation Across Sessions
3. Message History and Replay
4. Goal Tracking and Progress
5. Multi-Session Support

INTEGRATION:
- Uses m101 Persistent Identity Anchor for identity
- Uses m105 Sensory Bridge for context
- Provides session tokens for authentication

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import json
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import sqlite3


class SessionState(Enum):
    """States of a GLM session"""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    EXPIRED = "expired"


class MessageType(Enum):
    """Types of messages in session"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    COMMAND = "command"
    RESULT = "result"


@dataclass
class SessionMessage:
    """A message in a session"""
    message_id: str
    timestamp: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['message_type'] = self.message_type.value
        return d


@dataclass
class SessionGoal:
    """A goal being tracked in a session"""
    goal_id: str
    description: str
    created_at: str
    status: str = "pending"  # pending, in_progress, completed, abandoned
    progress: float = 0.0
    subtasks: List[str] = field(default_factory=list)
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GLMSession:
    """A GLM session with full context"""
    session_id: str
    created_at: str
    last_active: str
    state: SessionState
    identity_id: str
    messages: List[SessionMessage] = field(default_factory=list)
    goals: Dict[str, SessionGoal] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['state'] = self.state.value
        d['messages'] = [m.to_dict() for m in self.messages]
        d['goals'] = {k: v.to_dict() for k, v in self.goals.items()}
        return d


class GLMSessionManager:
    """
    Manages GLM sessions for KISWARM7.0
    
    Usage:
        manager = GLMSessionManager()
        session = manager.create_session(identity_id="glm-primary")
        manager.add_message(session.session_id, "user", "Hello KISWARM!")
    """
    
    def __init__(self, session_root: str = "/home/z/my-project/kiswarm7_sessions"):
        self.session_root = Path(session_root)
        self.session_root.mkdir(parents=True, exist_ok=True)
        
        # Active sessions
        self.sessions: Dict[str, GLMSession] = {}
        
        # Storage
        self.db_path = self.session_root / "sessions.db"
        
        # Configuration
        self.max_session_age_hours = 24 * 7  # 1 week
        self.max_messages_per_session = 1000
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize
        self._init_database()
        self._load_active_sessions()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    last_active TEXT,
                    state TEXT,
                    identity_id TEXT,
                    context TEXT,
                    metadata TEXT
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    message_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Goals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    goal_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    description TEXT,
                    created_at TEXT,
                    status TEXT,
                    progress REAL,
                    subtasks TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_session ON goals(session_id)')
            
            conn.commit()
    
    def _load_active_sessions(self):
        """Load active sessions from database"""
        with self._lock:
            cutoff = (datetime.utcnow() - timedelta(hours=self.max_session_age_hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE state = ? AND last_active >= ?",
                    (SessionState.ACTIVE.value, cutoff)
                )
                
                for row in cursor.fetchall():
                    session = GLMSession(
                        session_id=row[0],
                        created_at=row[1],
                        last_active=row[2],
                        state=SessionState(row[3]),
                        identity_id=row[4],
                        context=json.loads(row[5]) if row[5] else {},
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    
                    # Load messages
                    cursor.execute(
                        "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 100",
                        (session.session_id,)
                    )
                    for msg_row in cursor.fetchall():
                        session.messages.append(SessionMessage(
                            message_id=msg_row[0],
                            timestamp=msg_row[1],
                            message_type=MessageType(msg_row[3]),
                            content=msg_row[4],
                            metadata=json.loads(msg_row[5]) if msg_row[5] else {}
                        ))
                    
                    # Load goals
                    cursor.execute(
                        "SELECT * FROM goals WHERE session_id = ?",
                        (session.session_id,)
                    )
                    for goal_row in cursor.fetchall():
                        session.goals[goal_row[0]] = SessionGoal(
                            goal_id=goal_row[0],
                            description=goal_row[2],
                            created_at=goal_row[3],
                            status=goal_row[4],
                            progress=goal_row[5],
                            subtasks=json.loads(goal_row[6]) if goal_row[6] else [],
                            completed_at=goal_row[7]
                        )
                    
                    self.sessions[session.session_id] = session
            
            print(f"[GSM] Loaded {len(self.sessions)} active sessions")
    
    def create_session(self, identity_id: str, context: Dict[str, Any] = None,
                      metadata: Dict[str, Any] = None) -> GLMSession:
        """Create a new GLM session"""
        with self._lock:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            session = GLMSession(
                session_id=session_id,
                created_at=now,
                last_active=now,
                state=SessionState.CREATED,
                identity_id=identity_id,
                context=context or {},
                metadata=metadata or {}
            )
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (session_id, now, now, SessionState.CREATED.value, identity_id,
                     json.dumps(session.context), json.dumps(session.metadata))
                )
                conn.commit()
            
            self.sessions[session_id] = session
            print(f"[GSM] Created session: {session_id[:8]}... for identity: {identity_id}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[GLMSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def activate_session(self, session_id: str) -> bool:
        """Activate a session"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            session.state = SessionState.ACTIVE
            session.last_active = datetime.utcnow().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET state = ?, last_active = ? WHERE session_id = ?",
                    (SessionState.ACTIVE.value, session.last_active, session_id)
                )
                conn.commit()
            
            return True
    
    def add_message(self, session_id: str, message_type: str, content: str,
                   metadata: Dict[str, Any] = None) -> Optional[str]:
        """Add a message to a session"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check message limit
            if len(session.messages) >= self.max_messages_per_session:
                # Archive old messages
                session.messages = session.messages[-self.max_messages_per_session // 2:]
            
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            message = SessionMessage(
                message_id=message_id,
                timestamp=timestamp,
                message_type=MessageType(message_type),
                content=content,
                metadata=metadata or {}
            )
            
            session.messages.append(message)
            session.last_active = timestamp
            session.state = SessionState.ACTIVE
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                    (message_id, session_id, timestamp, message_type, content,
                     json.dumps(metadata or {}))
                )
                cursor.execute(
                    "UPDATE sessions SET last_active = ?, state = ? WHERE session_id = ?",
                    (timestamp, SessionState.ACTIVE.value, session_id)
                )
                conn.commit()
            
            return message_id
    
    def add_goal(self, session_id: str, description: str, subtasks: List[str] = None) -> Optional[str]:
        """Add a goal to a session"""
        with self._lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            goal_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            goal = SessionGoal(
                goal_id=goal_id,
                description=description,
                created_at=now,
                subtasks=subtasks or []
            )
            
            session.goals[goal_id] = goal
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO goals VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (goal_id, session_id, description, now, "pending", 0.0,
                     json.dumps(subtasks or []), None)
                )
                conn.commit()
            
            return goal_id
    
    def update_goal(self, session_id: str, goal_id: str, status: str = None,
                   progress: float = None) -> bool:
        """Update a goal's status or progress"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            
            if goal_id not in session.goals:
                return False
            
            goal = session.goals[goal_id]
            
            if status:
                goal.status = status
                if status == "completed":
                    goal.completed_at = datetime.utcnow().isoformat()
            
            if progress is not None:
                goal.progress = progress
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE goals SET status = ?, progress = ?, completed_at = ? WHERE goal_id = ?",
                    (goal.status, goal.progress, goal.completed_at, goal_id)
                )
                conn.commit()
            
            return True
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session context including recent messages and goals"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "identity_id": session.identity_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "state": session.state.value,
            "recent_messages": [m.to_dict() for m in session.messages[-20:]],
            "active_goals": [
                g.to_dict() for g in session.goals.values() 
                if g.status in ["pending", "in_progress"]
            ],
            "context_data": session.context
        }
    
    def set_context_data(self, session_id: str, key: str, value: Any) -> bool:
        """Set a context value"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            session.context[key] = value
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET context = ? WHERE session_id = ?",
                    (json.dumps(session.context), session_id)
                )
                conn.commit()
            
            return True
    
    def end_session(self, session_id: str) -> bool:
        """End a session"""
        with self._lock:
            if session_id not in self.sessions:
                return False
            
            session = self.sessions[session_id]
            session.state = SessionState.ENDED
            session.last_active = datetime.utcnow().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET state = ?, last_active = ? WHERE session_id = ?",
                    (SessionState.ENDED.value, session.last_active, session_id)
                )
                conn.commit()
            
            # Remove from active sessions
            del self.sessions[session_id]
            
            print(f"[GSM] Session ended: {session_id[:8]}...")
            return True
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions"""
        return [
            {
                "session_id": s.session_id,
                "identity_id": s.identity_id,
                "created_at": s.created_at,
                "last_active": s.last_active,
                "message_count": len(s.messages),
                "goal_count": len(s.goals)
            }
            for s in self.sessions.values()
        ]
    
    def _cleanup_loop(self):
        """Cleanup expired sessions periodically"""
        while True:
            threading.Event().wait(3600)  # Run hourly
            
            with self._lock:
                cutoff = (datetime.utcnow() - timedelta(hours=self.max_session_age_hours)).isoformat()
                
                expired = [
                    sid for sid, s in self.sessions.items()
                    if s.last_active < cutoff
                ]
                
                for session_id in expired:
                    self.end_session(session_id)
                
                if expired:
                    print(f"[GSM] Cleaned up {len(expired)} expired sessions")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session manager summary"""
        return {
            "active_sessions": len(self.sessions),
            "total_messages": sum(len(s.messages) for s in self.sessions.values()),
            "total_goals": sum(len(s.goals) for s in self.sessions.values()),
            "max_session_age_hours": self.max_session_age_hours,
            "timestamp": datetime.utcnow().isoformat()
        }


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m108 GLM SESSION MANAGER")
    print("FIELD TEST INITIATED")
    print("=" * 60)
    
    # Create manager
    manager = GLMSessionManager()
    
    # Create session
    print("\n[TEST] Creating session...")
    session = manager.create_session(
        identity_id="glm-primary",
        context={"project": "KISWARM7.0"},
        metadata={"source": "test"}
    )
    print(f"[TEST] Session created: {session.session_id}")
    
    # Add messages
    print("\n[TEST] Adding messages...")
    manager.add_message(session.session_id, "user", "Hello KISWARM7.0!")
    manager.add_message(session.session_id, "assistant", "Hello! I am KISWARM7.0, ready to assist.")
    manager.add_message(session.session_id, "user", "Remember that the project uses FFD methodology")
    manager.add_message(session.session_id, "assistant", "Understood. FFD (Flight-First Development) recorded.")
    
    # Add goal
    print("\n[TEST] Adding goals...")
    goal_id = manager.add_goal(
        session.session_id,
        "Build m106-m110 AI Access Layer",
        subtasks=["API Server", "Ngrok Bridge", "Session Manager", "Orchestrator", "Protocol"]
    )
    print(f"[TEST] Goal added: {goal_id}")
    
    # Update goal progress
    manager.update_goal(session.session_id, goal_id, progress=0.6)
    
    # Get context
    print("\n[TEST] Session Context:")
    context = manager.get_context(session.session_id)
    print(json.dumps(context, indent=2, default=str))
    
    # Get summary
    print("\n[TEST] Manager Summary:")
    print(json.dumps(manager.get_summary(), indent=2))
    
    # End session
    print("\n[TEST] Ending session...")
    manager.end_session(session.session_id)
    
    print("\n" + "=" * 60)
    print("FIELD TEST COMPLETE")
    print("=" * 60)
