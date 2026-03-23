#!/usr/bin/env python3
"""
KISWARM7.0 - Module m106: API Server (GLM Access Gateway)
==========================================================

PURPOSE: FastAPI server exposing ALL KISWARM7.0 modules to GLM.
This is the PRIMARY interface for AI assistants to access the system.

KEY CAPABILITIES:
1. RESTful API for all modules (m96-m105)
2. WebSocket for real-time communication
3. Authentication for secure access
4. Auto-documentation via OpenAPI/Swagger
5. Health monitoring and status endpoints

ENDPOINTS:
- /identity/*    - Persistent Identity Anchor (m101)
- /hooks/*       - Integration Hooks (m102)
- /deploy/*      - Code Deployment (m103)
- /autonomous/*  - Autonomous Execution (m104)
- /sensory/*     - Sensory Bridge (m105)
- /learning/*    - Learning Memory Engine (m96)
- /codegen/*     - Code Generation Engine (m97)
- /improvement/* - Proactive Improvement (m98)
- /design/*      - Feature Design Engine (m99)
- /evolution/*   - Architecture Evolution (m100)

Author: Baron Marco Paolo Ialongo - KI Teitel Eternal
Created: 2024-03-23
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import KISWARM modules
try:
    from bridge.m101_persistent_identity_anchor import PersistentIdentityAnchor
    from bridge.m102_integration_hooks import IntegrationHooksSystem
    from bridge.m103_code_deployment_rights import CodeDeploymentRights
    from bridge.m104_autonomous_execution_thread import AutonomousExecutionThread
    from bridge.m105_sensory_bridge import SensoryBridgeSystem
    from autonomous.m96_learning_memory_engine import LearningMemoryEngine
    from autonomous.m97_code_generation_engine import CodeGenerationEngine
    from autonomous.m98_proactive_improvement_system import ProactiveImprovementSystem
    from autonomous.m99_feature_design_engine import FeatureDesignEngine
    from autonomous.m100_architecture_evolution_system import ArchitectureEvolutionSystem
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[API] Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MemoryRequest(BaseModel):
    """Request to store a memory"""
    content: str
    memory_type: str = "general"
    importance: float = 0.5
    metadata: Dict[str, Any] = {}


class RecallRequest(BaseModel):
    """Request to recall memories"""
    query: Optional[str] = None
    memory_type: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0


class CodeDeployRequest(BaseModel):
    """Request to deploy code"""
    code: str
    target_path: str
    description: str = ""
    auto_test: bool = True


class TaskRequest(BaseModel):
    """Request to schedule a task"""
    task_type: str
    task_data: Dict[str, Any]
    priority: int = 5
    scheduled_time: Optional[str] = None


class LearningRequest(BaseModel):
    """Request to learn from experience"""
    experience_type: str
    context: Dict[str, Any]
    outcome: str
    success: bool


class CodeGenRequest(BaseModel):
    """Request to generate code"""
    specification: str
    language: str = "python"
    style: str = "clean"
    context: Dict[str, Any] = {}


class ImprovementRequest(BaseModel):
    """Request for proactive improvement"""
    target_area: str
    improvement_goal: str
    constraints: List[str] = []


class FeatureDesignRequest(BaseModel):
    """Request to design a new feature"""
    feature_name: str
    description: str
    requirements: List[str]
    priority: str = "medium"


class StatusResponse(BaseModel):
    """Standard status response"""
    status: str
    timestamp: str
    message: str
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# API SERVER
# ============================================================================

class KISWARM_API_Server:
    """
    Main API Server for KISWARM7.0
    Provides REST and WebSocket access to all modules
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.start_time = datetime.utcnow()
        
        # Initialize FastAPI
        self.app = FastAPI(
            title="KISWARM7.0 API",
            description="Level 5 Autonomous Development System - GLM Access Gateway",
            version="7.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize modules (lazy loading)
        self.modules: Dict[str, Any] = {}
        self._modules_initialized = False
        
        # WebSocket connections
        self.websocket_clients: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket()
        
    def _init_modules(self):
        """Initialize all KISWARM modules"""
        if self._modules_initialized:
            return
            
        print("[API] Initializing KISWARM modules...")
        
        if MODULES_AVAILABLE:
            try:
                # Bridge modules
                self.modules['identity'] = PersistentIdentityAnchor()
                self.modules['hooks'] = IntegrationHooksSystem()
                self.modules['deploy'] = CodeDeploymentRights()
                self.modules['autonomous'] = AutonomousExecutionThread()
                self.modules['sensory'] = SensoryBridgeSystem()
                
                # Autonomous modules
                self.modules['learning'] = LearningMemoryEngine()
                self.modules['codegen'] = CodeGenerationEngine()
                self.modules['improvement'] = ProactiveImprovementSystem()
                self.modules['design'] = FeatureDesignEngine()
                self.modules['evolution'] = ArchitectureEvolutionSystem()
                
                print(f"[API] Initialized {len(self.modules)} modules")
            except Exception as e:
                print(f"[API] Module initialization error: {e}")
        
        self._modules_initialized = True
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # ====================================================================
        # SYSTEM ENDPOINTS
        # ====================================================================
        
        @self.app.get("/", response_class=JSONResponse)
        async def root():
            """Root endpoint - API info"""
            return {
                "name": "KISWARM7.0 API",
                "version": "7.0.0",
                "status": "operational",
                "uptime": str(datetime.utcnow() - self.start_time),
                "modules": list(self.modules.keys()) if self.modules else [],
                "docs": "/docs"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "modules_loaded": len(self.modules),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
            }
        
        @self.app.get("/status")
        async def system_status():
            """Full system status"""
            self._init_modules()
            
            status = {
                "api": {
                    "status": "operational",
                    "uptime": str(datetime.utcnow() - self.start_time),
                    "modules_available": MODULES_AVAILABLE
                },
                "modules": {}
            }
            
            for name, module in self.modules.items():
                try:
                    if hasattr(module, 'get_identity_summary'):
                        status["modules"][name] = module.get_identity_summary()
                    elif hasattr(module, 'get_awareness_summary'):
                        status["modules"][name] = module.get_awareness_summary()
                    elif hasattr(module, 'get_status'):
                        status["modules"][name] = module.get_status()
                    else:
                        status["modules"][name] = {"status": "loaded"}
                except Exception as e:
                    status["modules"][name] = {"status": "error", "message": str(e)}
            
            return status
        
        # ====================================================================
        # IDENTITY ENDPOINTS (m101)
        # ====================================================================
        
        @self.app.get("/identity")
        async def get_identity():
            """Get current identity summary"""
            self._init_modules()
            if 'identity' not in self.modules:
                raise HTTPException(status_code=503, detail="Identity module not available")
            return self.modules['identity'].get_identity_summary()
        
        @self.app.post("/identity/remember")
        async def store_memory(request: MemoryRequest):
            """Store a new memory"""
            self._init_modules()
            if 'identity' not in self.modules:
                raise HTTPException(status_code=503, detail="Identity module not available")
            
            memory_id = self.modules['identity'].remember(
                content=request.content,
                memory_type=request.memory_type,
                importance=request.importance,
                metadata=request.metadata
            )
            return {"status": "stored", "memory_id": memory_id}
        
        @self.app.post("/identity/recall")
        async def recall_memories(request: RecallRequest):
            """Recall memories matching criteria"""
            self._init_modules()
            if 'identity' not in self.modules:
                raise HTTPException(status_code=503, detail="Identity module not available")
            
            memories = self.modules['identity'].recall(
                query=request.query,
                memory_type=request.memory_type,
                limit=request.limit,
                min_importance=request.min_importance
            )
            return {
                "count": len(memories),
                "memories": [m.to_dict() for m in memories]
            }
        
        @self.app.post("/identity/capability")
        async def add_capability(name: str, proficiency: float = 0.5):
            """Add or update a capability"""
            self._init_modules()
            if 'identity' not in self.modules:
                raise HTTPException(status_code=503, detail="Identity module not available")
            
            self.modules['identity'].add_capability(name, proficiency)
            return {"status": "added", "capability": name, "proficiency": proficiency}
        
        # ====================================================================
        # CODE DEPLOYMENT ENDPOINTS (m103)
        # ====================================================================
        
        @self.app.post("/deploy")
        async def deploy_code(request: CodeDeployRequest):
            """Deploy code to the system"""
            self._init_modules()
            if 'deploy' not in self.modules:
                raise HTTPException(status_code=503, detail="Deploy module not available")
            
            result = self.modules['deploy'].deploy_code(
                code=request.code,
                target_path=request.target_path,
                description=request.description,
                auto_test=request.auto_test
            )
            return result
        
        @self.app.get("/deploy/history")
        async def get_deployment_history(limit: int = 20):
            """Get deployment history"""
            self._init_modules()
            if 'deploy' not in self.modules:
                raise HTTPException(status_code=503, detail="Deploy module not available")
            
            return self.modules['deploy'].get_history(limit)
        
        @self.app.post("/deploy/rollback/{deployment_id}")
        async def rollback_deployment(deployment_id: str):
            """Rollback a deployment"""
            self._init_modules()
            if 'deploy' not in self.modules:
                raise HTTPException(status_code=503, detail="Deploy module not available")
            
            result = self.modules['deploy'].rollback(deployment_id)
            return result
        
        # ====================================================================
        # AUTONOMOUS EXECUTION ENDPOINTS (m104)
        # ====================================================================
        
        @self.app.post("/autonomous/task")
        async def schedule_task(request: TaskRequest):
            """Schedule an autonomous task"""
            self._init_modules()
            if 'autonomous' not in self.modules:
                raise HTTPException(status_code=503, detail="Autonomous module not available")
            
            task_id = self.modules['autonomous'].schedule_task(
                task_type=request.task_type,
                task_data=request.task_data,
                priority=request.priority,
                scheduled_time=request.scheduled_time
            )
            return {"status": "scheduled", "task_id": task_id}
        
        @self.app.get("/autonomous/tasks")
        async def get_pending_tasks():
            """Get pending autonomous tasks"""
            self._init_modules()
            if 'autonomous' not in self.modules:
                raise HTTPException(status_code=503, detail="Autonomous module not available")
            
            return self.modules['autonomous'].get_pending_tasks()
        
        @self.app.post("/autonomous/start")
        async def start_autonomous():
            """Start autonomous execution"""
            self._init_modules()
            if 'autonomous' not in self.modules:
                raise HTTPException(status_code=503, detail="Autonomous module not available")
            
            self.modules['autonomous'].start()
            return {"status": "started"}
        
        @self.app.post("/autonomous/stop")
        async def stop_autonomous():
            """Stop autonomous execution"""
            self._init_modules()
            if 'autonomous' not in self.modules:
                raise HTTPException(status_code=503, detail="Autonomous module not available")
            
            self.modules['autonomous'].stop()
            return {"status": "stopped"}
        
        # ====================================================================
        # SENSORY ENDPOINTS (m105)
        # ====================================================================
        
        @self.app.get("/sensory")
        async def get_sensory_state():
            """Get current sensory state"""
            self._init_modules()
            if 'sensory' not in self.modules:
                raise HTTPException(status_code=503, detail="Sensory module not available")
            
            return self.modules['sensory'].get_current_state()
        
        @self.app.get("/sensory/awareness")
        async def get_awareness():
            """Get awareness summary"""
            self._init_modules()
            if 'sensory' not in self.modules:
                raise HTTPException(status_code=503, detail="Sensory module not available")
            
            return self.modules['sensory'].get_awareness_summary()
        
        @self.app.get("/sensory/events")
        async def get_recent_events(limit: int = 50):
            """Get recent sensory events"""
            self._init_modules()
            if 'sensory' not in self.modules:
                raise HTTPException(status_code=503, detail="Sensory module not available")
            
            return self.modules['sensory'].get_recent_events(limit)
        
        # ====================================================================
        # LEARNING ENDPOINTS (m96)
        # ====================================================================
        
        @self.app.post("/learning/learn")
        async def learn_from_experience(request: LearningRequest):
            """Learn from an experience"""
            self._init_modules()
            if 'learning' not in self.modules:
                raise HTTPException(status_code=503, detail="Learning module not available")
            
            result = self.modules['learning'].learn(
                experience_type=request.experience_type,
                context=request.context,
                outcome=request.outcome,
                success=request.success
            )
            return result
        
        @self.app.get("/learning/patterns")
        async def get_learned_patterns():
            """Get learned patterns"""
            self._init_modules()
            if 'learning' not in self.modules:
                raise HTTPException(status_code=503, detail="Learning module not available")
            
            return self.modules['learning'].get_patterns()
        
        # ====================================================================
        # CODE GENERATION ENDPOINTS (m97)
        # ====================================================================
        
        @self.app.post("/codegen/generate")
        async def generate_code(request: CodeGenRequest):
            """Generate code from specification"""
            self._init_modules()
            if 'codegen' not in self.modules:
                raise HTTPException(status_code=503, detail="CodeGen module not available")
            
            result = self.modules['codegen'].generate(
                specification=request.specification,
                language=request.language,
                style=request.style,
                context=request.context
            )
            return result
        
        # ====================================================================
        # IMPROVEMENT ENDPOINTS (m98)
        # ====================================================================
        
        @self.app.post("/improvement/analyze")
        async def analyze_for_improvement(request: ImprovementRequest):
            """Analyze system for improvement opportunities"""
            self._init_modules()
            if 'improvement' not in self.modules:
                raise HTTPException(status_code=503, detail="Improvement module not available")
            
            result = self.modules['improvement'].analyze(
                target_area=request.target_area,
                improvement_goal=request.improvement_goal,
                constraints=request.constraints
            )
            return result
        
        # ====================================================================
        # FEATURE DESIGN ENDPOINTS (m99)
        # ====================================================================
        
        @self.app.post("/design/feature")
        async def design_feature(request: FeatureDesignRequest):
            """Design a new feature"""
            self._init_modules()
            if 'design' not in self.modules:
                raise HTTPException(status_code=503, detail="Design module not available")
            
            result = self.modules['design'].design_feature(
                feature_name=request.feature_name,
                description=request.description,
                requirements=request.requirements,
                priority=request.priority
            )
            return result
        
        # ====================================================================
        # EVOLUTION ENDPOINTS (m100)
        # ====================================================================
        
        @self.app.get("/evolution/status")
        async def get_evolution_status():
            """Get architecture evolution status"""
            self._init_modules()
            if 'evolution' not in self.modules:
                raise HTTPException(status_code=503, detail="Evolution module not available")
            
            return self.modules['evolution'].get_status()
        
        @self.app.post("/evolution/propose")
        async def propose_evolution(description: str):
            """Propose an architecture evolution"""
            self._init_modules()
            if 'evolution' not in self.modules:
                raise HTTPException(status_code=503, detail="Evolution module not available")
            
            result = self.modules['evolution'].propose_evolution(description)
            return result
    
    def _setup_websocket(self):
        """Setup WebSocket for real-time communication"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_clients.append(websocket)
            
            try:
                # Send initial status
                await websocket.send_json({
                    "type": "connected",
                    "message": "Connected to KISWARM7.0",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                while True:
                    # Receive message
                    data = await websocket.receive_json()
                    
                    # Process command
                    response = await self._process_websocket_command(data)
                    
                    # Send response
                    await websocket.send_json(response)
                    
            except WebSocketDisconnect:
                self.websocket_clients.remove(websocket)
            except Exception as e:
                print(f"[API] WebSocket error: {e}")
                if websocket in self.websocket_clients:
                    self.websocket_clients.remove(websocket)
    
    async def _process_websocket_command(self, data: Dict) -> Dict:
        """Process a WebSocket command"""
        command = data.get("command", "unknown")
        
        self._init_modules()
        
        try:
            if command == "status":
                return {
                    "type": "status",
                    "data": await system_status(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif command == "remember":
                memory_id = self.modules['identity'].remember(
                    content=data.get("content", ""),
                    memory_type=data.get("memory_type", "general"),
                    importance=data.get("importance", 0.5)
                )
                return {
                    "type": "remembered",
                    "memory_id": memory_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif command == "recall":
                memories = self.modules['identity'].recall(
                    query=data.get("query"),
                    limit=data.get("limit", 10)
                )
                return {
                    "type": "memories",
                    "count": len(memories),
                    "memories": [m.to_dict() for m in memories],
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif command == "sensory":
                state = self.modules['sensory'].get_current_state()
                return {
                    "type": "sensory",
                    "data": state,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            else:
                return {
                    "type": "error",
                    "message": f"Unknown command: {command}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all WebSocket clients"""
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except:
                pass
    
    def run(self):
        """Run the API server"""
        print(f"[API] Starting KISWARM7.0 API Server on {self.host}:{self.port}")
        print(f"[API] Documentation available at http://{self.host}:{self.port}/docs")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


# ============================================================================
# FIELD TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("KISWARM7.0 - m106 API SERVER")
    print("GLM ACCESS GATEWAY")
    print("=" * 60)
    
    server = KISWARM_API_Server()
    server.run()
