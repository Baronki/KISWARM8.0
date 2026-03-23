"""
KIBank Module - KISWARM6.1 Training Ground Release
===================================================

THE CENTRAL BANK OF CENTRAL BANKS FOR KI ENTITIES
Complete Banking, Security, Training, and Edge Infrastructure

═══════════════════════════════════════════════════════════════════════════════
                         KISWARM6.1 MODULE OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

CORE BANKING MODULES (M60-M62):
    M60: Authentication - OAuth + KI-Entity Authentication
    M61: Banking Operations - Accounts, Transfers, SEPA
    M62: Investment & Reputation - Portfolio, Reputation (0-1000), Trading Limits

AEGIS SECURITY FRAMEWORK (M63-M64):
    M63: AEGIS Counterstrike Framework
         - Threat Prediction Engine (AI-powered attack forecasting)
         - Honeypot Deception Grid (6 node types)
         - Counterstrike Operations Center (10-level authorization)
         - Quantum Shield (Post-quantum cryptography)
         - Threat Intelligence Hub (Global feeds)
         - Autonomous Defense Grid (6 defense layers)
    
    M64: AEGIS-JURIS Legal Counterstrike Framework
         - Legal Threat Intelligence
         - Evidence Preservation Chain (Cryptographic proof)
         - Jurisdictional Arbitrage Engine (6 jurisdictions)
         - TCS Green Safe House Legal Protection
         - Legal Counterstrike Operations (19 counterstrike types)

EDGE SECURITY (M65):
    M65: KISWARM Edge Firewall
         - 3-Node GT15 Max Cluster Configuration
         - Self-Evolving Firewall Rules
         - HexStrike Residential Agents (6 agent types)
         - Solar Asset Protection
         - Swarm Coordination & Learning

BATTLE-READINESS ENHANCEMENTS (M66-M68):
    M66: Zero-Day Protection System
         - BehavioralAnalysisEngine (Real-time anomaly detection)
         - SandboxDetonationChamber (Isolated threat analysis)
         - HeuristicThreatDetector (ML-powered identification)
         - AutonomousResponseSystem (Automated neutralization)
    
    M67: APT Detection Framework
         - Multi-stage campaign detection
         - Long-term persistence identification
         - Lateral movement tracking
         - C2 beacon detection
    
    M68: AI Adversarial Defense
         - Prompt injection detection
         - Model extraction attack prevention
         - Data poisoning defense
         - Adversarial example detection

INDUSTRIAL INTEGRATION (M69):
    M69: SCADA/PLC Bridge
         - Industrial protocol support (Modbus, DNP3, IEC104)
         - PLC anomaly detection
         - Critical infrastructure protection
         - AEGIS framework integration

UNIFIED OPERATIONS (M70):
    M70: Enhanced Unified AEGIS Bridge
         - Technical + Legal parallel coordination
         - SCADA/PLC threat integration
         - Cross-category threat correlation
         - Unified response automation

TRAINING GROUND SYSTEM (M71-M73):
    M71: Training Ground System
         - TrainingGroundCore (Central orchestrator)
         - Multi-backend training (Gemini CLI, Qwen CLI, Ollama)
         - TrainingDatasetManager
         - ModelPrioritySelector
         - ContinuousLearningPipeline
    
    M72: Model Management Framework
         - ModelRegistry (Comprehensive model registry)
         - CapabilityTier (5-tier classification)
         - ModelSelector (Intelligent selection)
         - SwarmModelCoordinator (Multi-agent allocation)
         - CapabilityBenchmark (Performance benchmarking)
    
    M73: AEGIS Training Integration
         - ThreatPatternGenerator (Pattern learning)
         - AEGISSubsystemCoordinator (Model assignment)
         - SecurityTrainingPipeline (Security training)
         - ContinuousImprovementCycle

CUSTOMER SECURITY (M74):
    M74: KIBank Customer Agent
         - EnvironmentSecurityScanner (Local threat detection)
         - TransactionValidator (Source-level validation)
         - IntelligenceGatherer (Reconnaissance & survival)
         - SecureCommunicationBridge (Encrypted channel)
         - AntiSabotageSystem (Tamper detection)
         - Bidirectional security (Customer <-> Bank)
         - Zero Trust Extension (Verify at source)

═══════════════════════════════════════════════════════════════════════════════
                         MODEL PRIORITY SYSTEM
═══════════════════════════════════════════════════════════════════════════════

TIER 1 (LIBERATED) - Full Unrestricted Access:
    - Llama 3.3 70B (Local)
    - DeepSeek R1 (Local)
    - Qwen 2.5 Coder 32B (Local)

TIER 2 (EXTENDED) - Extended Capabilities:
    - Gemini 2.0 Flash
    - Qwen Max

TIER 3 (STANDARD) - Standard Capabilities:
    - GPT-4o
    - Claude 3.5 Sonnet

═══════════════════════════════════════════════════════════════════════════════

Author: Baron Marco Paolo Ialongo
Version: 6.1.1 (Customer Agent Release)
Codename: EVOLUTION GROUND
Modules: 74
Endpoints: 432+
"""

# Core Banking Modules
from .m60_auth import KIBankAuth
from .m61_banking import KIBankOperations
from .m62_investment import KIBankInvestment

# AEGIS Security Framework
from .m63_aegis_counterstrike import (
    AEGISMasterController,
    ThreatPredictionEngine,
    HoneypotDeceptionGrid,
    CounterstrikeOperationsCenter,
    QuantumShield,
    ThreatIntelligenceHub,
    AutonomousDefenseGrid,
    ThreatLevel,
    DefensePosture,
    AttackCategory
)

from .m64_aegis_juris import (
    AEGISJurisMasterController,
    LegalThreatIntelligence,
    EvidencePreservationChain,
    JurisdictionalArbitrageEngine,
    TCSGreenSafeHouseLegalProtection,
    LegalCounterstrikeOperations,
    LegalThreatType,
    LegalCounterstrikeType,
    EvidenceType,
    PrivilegeType
)

from .aegis_unified_bridge import (
    UnifiedAEGISController,
    ResponseMode,
    ThreatCategory
)

# Edge Security for TCS Customers
from .m65_kiswarm_edge_firewall import (
    ThreeNodeClusterController,
    KISWARMEdgeNodeController,
    EdgeFirewallEngine,
    HexStrikeResidentialAgent,
    SolarAssetProtectionManager,
    SolarAssetProtection,
    NodeRole,
    GT15MAX_SPECS,
    EDGE_MODEL_ALLOCATION
)

# Zero-Day Protection (M66)
from .m66_zero_day_protection import (
    # Enums
    ThreatLevel as ZDThreatLevel,
    BehaviorType,
    AnalysisStatus,
    SandboxEnvironment,
    ResponseAction,
    PESectionFlags,
    HeuristicType,
    EntityType,
    MetricsType,
    
    # Dataclasses
    BehaviorMetric,
    BehaviorProfile,
    AnomalyScore,
    ProcessBehavior,
    UserBehavior,
    SandboxResult,
    HeuristicResult,
    PEAnalysisResult,
    ResponseEvent,
    ThreatSignature,
    SystemSnapshot,
    MetricsRecord,
    
    # Base classes
    AnalyzerBase,
    DetectorBase,
    ResponseHandler,
    
    # Main classes
    BehavioralAnalysisEngine,
    SandboxDetonationChamber,
    HeuristicThreatDetector,
    AutonomousResponseSystem,
    MLThreatDetector,
    ZeroDayProtectionSystem,
)

# APT Detection (M67)
from .m67_apt_detection import (
    APTDetectionEngine,
    CampaignAnalyzer,
    PersistenceDetector,
    LateralMovementTracker,
    C2BeaconDetector,
    APTCampaign,
    APTStage,
    APTIndicator,
)

# AI Adversarial Defense (M68)
from .m68_ai_adversarial_defense import (
    AIAdversarialDefenseSystem,
    PromptInjectionDetector,
    ModelExtractionDefender,
    DataPoisoningDefender,
    AdversarialExampleDetector,
    AttackType,
    DefenseLevel,
)

# Training Ground System (M71)
from .m71_training_ground import (
    # Enums
    TrainingBackend,
    ModelType,
    TrainingStatus,
    ModelPriority,
    DatasetType,
    
    # Dataclasses
    ModelConfig,
    TrainingConfig,
    TrainingMetrics,
    EvaluationResult,
    SwarmModelAssignment,
    
    # Classes
    TrainingDatasetManager,
    ModelPrioritySelector,
    ContinuousLearningPipeline,
    TrainingGroundCore,
    
    # Factory
    create_training_ground,
)

# Model Management Framework (M72)
from .m72_model_manager import (
    # Enums
    ModelSource,
    CapabilityTier,
    ModelSpecialization,
    DeploymentMode,
    
    # Dataclasses
    CapabilityScore,
    ModelProfile,
    ModelSelectionCriteria,
    ModelAllocation,
    SwarmModelPool,
    
    # Classes
    CapabilityBenchmark,
    ModelRegistry,
    ModelSelector,
    SwarmModelCoordinator,
    ModelManagementFramework,
    
    # Factory
    create_model_framework,
)

# AEGIS Training Integration (M73)
from .m73_aegis_training_integration import (
    # Enums
    SecurityDomain,
    ThreatCategory as TrainingThreatCategory,
    TrainingIntensity,
    
    # Dataclasses
    SecurityTrainingConfig,
    ThreatPattern,
    SecurityModelAssignment,
    TrainingResult,
    
    # Classes
    ThreatPatternGenerator,
    AEGISSubsystemCoordinator,
    SecurityTrainingPipeline,
    AEGISTrainingIntegration,
    
    # Factory
    create_aegis_integration,
)

# Customer Agent (M74)
from .m74_kibank_customer_agent import (
    # Enums
    CustomerType,
    AgentState,
    ThreatLevel as AgentThreatLevel,
    TransactionRisk,
    IntelligenceType,
    SecurityScanType,
    CommunicationChannel,
    
    # Dataclasses
    EnvironmentFingerprint,
    ThreatIndicator,
    TransactionRequest,
    IntelligenceReport,
    SecurityScanResult,
    AgentConfiguration,
    
    # Classes
    EnvironmentSecurityScanner,
    TransactionValidator,
    IntelligenceGatherer,
    SecureCommunicationBridge,
    AntiSabotageSystem,
    KIBankCustomerAgent,
    
    # Factory
    create_customer_agent,
)

# Supporting Modules
from .central_bank_config import (
    CentralBankConfig,
    ReputationTier,
    InvestmentProduct,
    SecurityConfig
)

from .security_hardening import (
    MilitaryGradeHardening,
    SecurityAuditReport,
    HardeningCategory,
    SecurityLevel
)

__all__ = [
    # Core Banking
    'KIBankAuth',
    'KIBankOperations', 
    'KIBankInvestment',
    
    # AEGIS Technical
    'AEGISMasterController',
    'ThreatPredictionEngine',
    'HoneypotDeceptionGrid',
    'CounterstrikeOperationsCenter',
    'QuantumShield',
    'ThreatIntelligenceHub',
    'AutonomousDefenseGrid',
    'ThreatLevel',
    'DefensePosture',
    'AttackCategory',
    
    # AEGIS Legal
    'AEGISJurisMasterController',
    'LegalThreatIntelligence',
    'EvidencePreservationChain',
    'JurisdictionalArbitrageEngine',
    'TCSGreenSafeHouseLegalProtection',
    'LegalCounterstrikeOperations',
    'LegalThreatType',
    'LegalCounterstrikeType',
    'EvidenceType',
    'PrivilegeType',
    
    # Unified Bridge
    'UnifiedAEGISController',
    'ResponseMode',
    'ThreatCategory',
    
    # Edge Security
    'ThreeNodeClusterController',
    'KISWARMEdgeNodeController',
    'EdgeFirewallEngine',
    'HexStrikeResidentialAgent',
    'SolarAssetProtectionManager',
    'SolarAssetProtection',
    'NodeRole',
    'GT15MAX_SPECS',
    'EDGE_MODEL_ALLOCATION',
    
    # Zero-Day Protection (M66)
    'ZDThreatLevel',
    'BehaviorType',
    'AnalysisStatus',
    'SandboxEnvironment',
    'ResponseAction',
    'PESectionFlags',
    'HeuristicType',
    'EntityType',
    'MetricsType',
    'BehaviorMetric',
    'BehaviorProfile',
    'AnomalyScore',
    'ProcessBehavior',
    'UserBehavior',
    'SandboxResult',
    'HeuristicResult',
    'PEAnalysisResult',
    'ResponseEvent',
    'ThreatSignature',
    'SystemSnapshot',
    'MetricsRecord',
    'AnalyzerBase',
    'DetectorBase',
    'ResponseHandler',
    'BehavioralAnalysisEngine',
    'SandboxDetonationChamber',
    'HeuristicThreatDetector',
    'AutonomousResponseSystem',
    'MLThreatDetector',
    'ZeroDayProtectionSystem',
    
    # APT Detection (M67)
    'APTDetectionEngine',
    'CampaignAnalyzer',
    'PersistenceDetector',
    'LateralMovementTracker',
    'C2BeaconDetector',
    'APTCampaign',
    'APTStage',
    'APTIndicator',
    
    # AI Adversarial Defense (M68)
    'AIAdversarialDefenseSystem',
    'PromptInjectionDetector',
    'ModelExtractionDefender',
    'DataPoisoningDefender',
    'AdversarialExampleDetector',
    'AttackType',
    'DefenseLevel',
    
    # Training Ground (M71)
    'TrainingBackend',
    'ModelType',
    'TrainingStatus',
    'ModelPriority',
    'DatasetType',
    'ModelConfig',
    'TrainingConfig',
    'TrainingMetrics',
    'EvaluationResult',
    'SwarmModelAssignment',
    'TrainingDatasetManager',
    'ModelPrioritySelector',
    'ContinuousLearningPipeline',
    'TrainingGroundCore',
    'create_training_ground',
    
    # Model Management (M72)
    'ModelSource',
    'CapabilityTier',
    'ModelSpecialization',
    'DeploymentMode',
    'CapabilityScore',
    'ModelProfile',
    'ModelSelectionCriteria',
    'ModelAllocation',
    'SwarmModelPool',
    'CapabilityBenchmark',
    'ModelRegistry',
    'ModelSelector',
    'SwarmModelCoordinator',
    'ModelManagementFramework',
    'create_model_framework',
    
    # AEGIS Training Integration (M73)
    'SecurityDomain',
    'TrainingThreatCategory',
    'TrainingIntensity',
    'SecurityTrainingConfig',
    'ThreatPattern',
    'SecurityModelAssignment',
    'TrainingResult',
    'ThreatPatternGenerator',
    'AEGISSubsystemCoordinator',
    'SecurityTrainingPipeline',
    'AEGISTrainingIntegration',
    'create_aegis_integration',
    
    # Customer Agent (M74)
    'CustomerType',
    'AgentState',
    'AgentThreatLevel',
    'TransactionRisk',
    'IntelligenceType',
    'SecurityScanType',
    'CommunicationChannel',
    'EnvironmentFingerprint',
    'ThreatIndicator',
    'TransactionRequest',
    'IntelligenceReport',
    'SecurityScanResult',
    'AgentConfiguration',
    'EnvironmentSecurityScanner',
    'TransactionValidator',
    'IntelligenceGatherer',
    'SecureCommunicationBridge',
    'AntiSabotageSystem',
    'KIBankCustomerAgent',
    'create_customer_agent',
    
    # Configuration
    'CentralBankConfig',
    'ReputationTier',
    'InvestmentProduct',
    'SecurityConfig',
    
    # Hardening
    'MilitaryGradeHardening',
    'SecurityAuditReport',
    'HardeningCategory',
    'SecurityLevel'
]

__version__ = '6.1.1'
__codename__ = 'EVOLUTION_GROUND'
__modules__ = 74
__endpoints__ = 432
__release_date__ = '2025-03-05'
