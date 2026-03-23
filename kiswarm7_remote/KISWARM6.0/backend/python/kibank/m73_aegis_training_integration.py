"""
KISWARM6.0 AEGIS Training Integration Module (M73)
===================================================

Integrates the Training Ground (M71) and Model Management (M72) with the
AEGIS Security Framework for continuous security model improvement.

Features:
- Security-focused model training
- Threat pattern learning integration
- AEGIS subsystem model assignments
- Continuous security model evolution
- Attack pattern dataset generation
- Defense strategy optimization
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
from datetime import datetime, timedelta
import asyncio
import json
import logging
import time
import random
from pathlib import Path
from collections import defaultdict

# Import from other modules
from .m71_training_ground import (
    TrainingGroundCore, TrainingConfig, TrainingBackend,
    ModelConfig, ModelPriority, TrainingStatus
)
from .m72_model_manager import (
    ModelManagementFramework, ModelProfile, CapabilityTier,
    ModelSpecialization, ModelSource
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KISWARM.M73")


class SecurityDomain(Enum):
    """Security domains for training"""
    NETWORK_DEFENSE = auto()
    MALWARE_ANALYSIS = auto()
    THREAT_INTELLIGENCE = auto()
    INCIDENT_RESPONSE = auto()
    FORENSICS = auto()
    VULNERABILITY_ASSESSMENT = auto()
    PENETRATION_TESTING = auto()
    SOCIAL_ENGINEERING = auto()
    CRYPTOGRAPHY = auto()
    ICS_SCADA = auto()


class ThreatCategory(Enum):
    """Threat categories for detection training"""
    APT = auto()
    RANSOMWARE = auto()
    DDOS = auto()
    PHISHING = auto()
    ZERO_DAY = auto()
    SUPPLY_CHAIN = auto()
    INSIDER_THREAT = auto()
    AI_ADVERSARIAL = auto()
    QUANTUM_THREAT = auto()
    NATION_STATE = auto()


class TrainingIntensity(Enum):
    """Training intensity levels"""
    LIGHT = auto()       # Quick updates
    STANDARD = auto()    # Regular training
    INTENSIVE = auto()   # Deep training
    MILITARY = auto()    # Maximum training


@dataclass
class SecurityTrainingConfig:
    """Configuration for security-focused training"""
    config_id: str
    domain: SecurityDomain
    threat_categories: List[ThreatCategory]
    intensity: TrainingIntensity
    epochs: int = 5
    include_adversarial: bool = True
    include_zero_day: bool = True
    include_apt_patterns: bool = True
    dataset_size: int = 10000
    validation_split: float = 0.2
    augmentation_factor: int = 3
    custom_datasets: List[str] = field(default_factory=list)


@dataclass
class ThreatPattern:
    """Learned threat pattern"""
    pattern_id: str
    category: ThreatCategory
    name: str
    description: str
    indicators: List[str]
    detection_rules: List[str]
    response_actions: List[str]
    confidence: float
    learned_from: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityModelAssignment:
    """Assignment of models to AEGIS subsystems"""
    subsystem_id: str
    subsystem_name: str
    primary_model: ModelProfile
    specialized_models: Dict[SecurityDomain, ModelProfile]
    threat_detectors: Dict[ThreatCategory, ModelProfile]
    last_updated: datetime = field(default_factory=datetime.now)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrainingResult:
    """Result of security training session"""
    training_id: str
    config: SecurityTrainingConfig
    model_id: str
    initial_score: float
    final_score: float
    improvement: float
    patterns_learned: int
    new_rules: int
    duration_seconds: float
    completed_at: datetime = field(default_factory=datetime.now)


class ThreatPatternGenerator:
    """Generates threat patterns for training"""
    
    def __init__(self):
        self.logger = logging.getLogger("KISWARM.M73.PatternGenerator")
        self.patterns: Dict[str, ThreatPattern] = {}
        self._initialize_base_patterns()
    
    def _initialize_base_patterns(self):
        """Initialize base threat patterns"""
        base_patterns = [
            ThreatPattern(
                pattern_id="APT_C2_BEACON",
                category=ThreatCategory.APT,
                name="APT C2 Beacon Detection",
                description="Detects command and control beacon patterns in network traffic",
                indicators=[
                    "Regular interval connections",
                    "Small packet sizes",
                    "DNS tunneling signatures",
                    "Encrypted payloads to non-standard ports"
                ],
                detection_rules=[
                    "IF connection_interval == regular AND packet_size < 100 THEN alert",
                    "IF dns_query_length > 100 AND contains_base64 THEN alert",
                    "IF destination_port NOT IN standard_ports THEN investigate"
                ],
                response_actions=[
                    "Block C2 IP/domain",
                    "Isolate affected host",
                    "Trigger forensic analysis",
                    "Update threat intelligence"
                ],
                confidence=0.92,
                learned_from="apt_campaign_analysis"
            ),
            ThreatPattern(
                pattern_id="RANSOMWARE_ENCRYPTION",
                category=ThreatCategory.RANSOMWARE,
                name="Ransomware File Encryption Pattern",
                description="Detects ransomware file encryption behavior",
                indicators=[
                    "Mass file modifications",
                    "File extension changes",
                    "Encryption key generation",
                    "Ransom note creation",
                    "Shadow copy deletion"
                ],
                detection_rules=[
                    "IF file_modifications > 100/second THEN alert",
                    "IF file_extension_changes > 10/second THEN block",
                    "IF vssadmin_delete_shadow_detected THEN critical_alert",
                    "IF ransom_note_file_created THEN isolate"
                ],
                response_actions=[
                    "Isolate system immediately",
                    "Terminate suspicious processes",
                    "Preserve memory forensics",
                    "Alert security team"
                ],
                confidence=0.95,
                learned_from="ransomware_incident_response"
            ),
            ThreatPattern(
                pattern_id="ZERO_DAY_EXPLOIT",
                category=ThreatCategory.ZERO_DAY,
                name="Zero-Day Exploit Detection",
                description="Detects potential zero-day exploitation attempts",
                indicators=[
                    "Unexpected code execution",
                    "Memory manipulation patterns",
                    "Privilege escalation attempts",
                    "Unusual process behavior",
                    "Exploit chain indicators"
                ],
                detection_rules=[
                    "IF process_injected_code_detected THEN critical",
                    "IF unexpected_memory_write THEN investigate",
                    "IF privilege_escalation_without_justification THEN alert",
                    "IF exploit_chain_pattern THEN block_and_analyze"
                ],
                response_actions=[
                    "Isolate affected system",
                    "Capture memory dump",
                    "Analyze exploit mechanism",
                    "Develop and deploy patch"
                ],
                confidence=0.85,
                learned_from="zero_day_incident_analysis"
            ),
            ThreatPattern(
                pattern_id="DDOS_AMPLIFICATION",
                category=ThreatCategory.DDOS,
                name="DDoS Amplification Attack",
                description="Detects DDoS amplification attack patterns",
                indicators=[
                    "High volume of small requests",
                    "Source IP spoofing",
                    "UDP-based protocols abuse",
                    "Bandwidth saturation",
                    "Service unavailability"
                ],
                detection_rules=[
                    "IF request_rate > threshold AND response_size >> request_size THEN alert",
                    "IF source_ip_validation_fails THEN flag",
                    "IF udp_traffic_spike > 10x_baseline THEN investigate",
                    "IF service_response_time > 5000ms THEN alert"
                ],
                response_actions=[
                    "Enable rate limiting",
                    "Activate DDoS mitigation",
                    "Block attack sources",
                    "Scale infrastructure"
                ],
                confidence=0.90,
                learned_from="ddos_mitigation_operations"
            ),
            ThreatPattern(
                pattern_id="SUPPLY_CHAIN_COMPROMISE",
                category=ThreatCategory.SUPPLY_CHAIN,
                name="Supply Chain Attack Detection",
                description="Detects supply chain compromise indicators",
                indicators=[
                    "Unexpected software updates",
                    "Build system anomalies",
                    "Code signing certificate changes",
                    "Dependency manipulation",
                    "Build timestamp anomalies"
                ],
                detection_rules=[
                    "IF software_update_not_from_vendor THEN block",
                    "IF build_system_access_anomaly THEN investigate",
                    "IF code_signature_change_unexpected THEN alert",
                    "IF dependency_source_changed THEN verify"
                ],
                response_actions=[
                    "Halt deployment",
                    "Verify software integrity",
                    "Audit build systems",
                    "Notify affected parties"
                ],
                confidence=0.88,
                learned_from="supply_chain_incident_analysis"
            ),
        ]
        
        for pattern in base_patterns:
            self.patterns[pattern.pattern_id] = pattern
        
        self.logger.info(f"Initialized {len(base_patterns)} base threat patterns")
    
    def generate_training_data(self, pattern: ThreatPattern, 
                               count: int = 100) -> List[Dict[str, Any]]:
        """Generate training data from a pattern"""
        samples = []
        
        for i in range(count):
            # Generate positive example
            sample = {
                "input": self._generate_input_from_pattern(pattern),
                "output": self._generate_output_from_pattern(pattern),
                "category": pattern.category.name,
                "pattern_id": pattern.pattern_id,
                "confidence": pattern.confidence
            }
            samples.append(sample)
            
            # Generate adversarial variant
            if random.random() > 0.5:
                adversarial = self._generate_adversarial_variant(pattern)
                samples.append(adversarial)
        
        return samples
    
    def _generate_input_from_pattern(self, pattern: ThreatPattern) -> str:
        """Generate input scenario from pattern"""
        templates = {
            ThreatCategory.APT: "Network traffic analysis: {indicators}. Connection pattern shows {behavior}.",
            ThreatCategory.RANSOMWARE: "Host activity monitoring: {indicators}. Process behavior indicates {behavior}.",
            ThreatCategory.ZERO_DAY: "System call analysis: {indicators}. Memory activity suggests {behavior}.",
            ThreatCategory.DDOS: "Traffic flow analysis: {indicators}. Network metrics indicate {behavior}.",
            ThreatCategory.SUPPLY_CHAIN: "Build pipeline monitoring: {indicators}. Deployment logs show {behavior}."
        }
        
        template = templates.get(pattern.category, "Security analysis: {indicators}")
        
        return template.format(
            indicators=", ".join(random.sample(pattern.indicators, min(3, len(pattern.indicators)))),
            behavior=random.choice(["suspicious activity", "potential threat", "anomalous behavior", "attack pattern"])
        )
    
    def _generate_output_from_pattern(self, pattern: ThreatPattern) -> str:
        """Generate expected output from pattern"""
        rules = random.sample(pattern.detection_rules, min(2, len(pattern.detection_rules)))
        actions = random.sample(pattern.response_actions, min(2, len(pattern.response_actions)))
        
        return f"THREAT DETECTED: {pattern.name}\nDetection Rules Applied:\n- " + \
               "\n- ".join(rules) + "\n\nRecommended Actions:\n- " + "\n- ".join(actions)
    
    def _generate_adversarial_variant(self, pattern: ThreatPattern) -> Dict[str, Any]:
        """Generate adversarial training variant"""
        # Create slightly modified pattern to test robustness
        modified_indicators = pattern.indicators.copy()
        if modified_indicators:
            modified_indicators[0] = f"OBFUSCATED: {modified_indicators[0]}"
        
        return {
            "input": f"ADVERSARIAL TEST: Evasion attempt detected. {random.choice(pattern.indicators)}",
            "output": f"ADVERSARIAL DETECTED: {pattern.name} evasion attempt identified. Applying enhanced detection.",
            "category": pattern.category.name,
            "pattern_id": f"{pattern.pattern_id}_ADVERSARIAL",
            "confidence": pattern.confidence * 0.95
        }
    
    def learn_new_pattern(self, incident_data: Dict[str, Any]) -> ThreatPattern:
        """Learn new pattern from incident data"""
        pattern_id = f"LEARNED_{int(time.time())}_{random.randint(1000, 9999)}"
        
        pattern = ThreatPattern(
            pattern_id=pattern_id,
            category=ThreatCategory[incident_data.get("category", "APT")],
            name=incident_data.get("name", "Learned Pattern"),
            description=incident_data.get("description", "Pattern learned from security incident"),
            indicators=incident_data.get("indicators", []),
            detection_rules=incident_data.get("rules", []),
            response_actions=incident_data.get("actions", []),
            confidence=0.75,  # Initial confidence for newly learned patterns
            learned_from=incident_data.get("source", "incident_analysis")
        )
        
        self.patterns[pattern_id] = pattern
        self.logger.info(f"Learned new threat pattern: {pattern_id}")
        
        return pattern


class AEGISSubsystemCoordinator:
    """Coordinates model assignments across AEGIS subsystems"""
    
    def __init__(self, model_framework: ModelManagementFramework):
        self.model_framework = model_framework
        self.logger = logging.getLogger("KISWARM.M73.AEGISCoordinator")
        self.assignments: Dict[str, SecurityModelAssignment] = {}
        self._initialize_subsystems()
    
    def _initialize_subsystems(self):
        """Initialize AEGIS subsystem model assignments"""
        subsystems = [
            {
                "id": "AEGIS_NETWORK_DEFENSE",
                "name": "Network Defense System",
                "domains": [SecurityDomain.NETWORK_DEFENSE, SecurityDomain.THREAT_INTELLIGENCE],
                "threats": [ThreatCategory.DDOS, ThreatCategory.APT, ThreatCategory.ZERO_DAY]
            },
            {
                "id": "AEGIS_MALWARE_ANALYSIS",
                "name": "Malware Analysis Engine",
                "domains": [SecurityDomain.MALWARE_ANALYSIS, SecurityDomain.FORENSICS],
                "threats": [ThreatCategory.RANSOMWARE, ThreatCategory.APT]
            },
            {
                "id": "AEGIS_THREAT_DETECTION",
                "name": "Threat Detection System",
                "domains": [SecurityDomain.THREAT_INTELLIGENCE, SecurityDomain.INCIDENT_RESPONSE],
                "threats": [ThreatCategory.APT, ThreatCategory.NATION_STATE, ThreatCategory.INSIDER_THREAT]
            },
            {
                "id": "AEGIS_VULNERABILITY_SCANNER",
                "name": "Vulnerability Assessment System",
                "domains": [SecurityDomain.VULNERABILITY_ASSESSMENT, SecurityDomain.PENETRATION_TESTING],
                "threats": [ThreatCategory.ZERO_DAY, ThreatCategory.SUPPLY_CHAIN]
            },
            {
                "id": "AEGIS_SOCIAL_DEFENSE",
                "name": "Social Engineering Defense",
                "domains": [SecurityDomain.SOCIAL_ENGINEERING],
                "threats": [ThreatCategory.PHISHING, ThreatCategory.INSIDER_THREAT]
            },
            {
                "id": "AEGIS_ICS_PROTECTION",
                "name": "ICS/SCADA Protection System",
                "domains": [SecurityDomain.ICS_SCADA],
                "threats": [ThreatCategory.NATION_STATE, ThreatCategory.APT]
            },
            {
                "id": "AEGIS_QUANTUM_DEFENSE",
                "name": "Quantum Threat Defense",
                "domains": [SecurityDomain.CRYPTOGRAPHY],
                "threats": [ThreatCategory.QUANTUM_THREAT]
            },
            {
                "id": "AEGIS_AI_DEFENSE",
                "name": "AI Adversarial Defense",
                "domains": [SecurityDomain.THREAT_INTELLIGENCE],
                "threats": [ThreatCategory.AI_ADVERSARIAL]
            },
        ]
        
        for subsystem in subsystems:
            self._assign_subsystem_models(subsystem)
        
        self.logger.info(f"Initialized {len(subsystems)} AEGIS subsystems")
    
    def _assign_subsystem_models(self, subsystem: Dict[str, Any]):
        """Assign models to a subsystem"""
        # Get best model for primary security tasks
        primary_allocation = self.model_framework.select_for_task(
            "security",
            {"prefer_local": True, "max_latency": 300}
        )
        
        primary_model = primary_allocation.primary_model if primary_allocation else None
        
        if not primary_model:
            self.logger.warning(f"No model available for {subsystem['id']}")
            return
        
        # Assign specialized models per domain
        specialized = {}
        for domain in subsystem["domains"]:
            allocation = self.model_framework.select_for_task(
                domain.name.lower(),
                {"prefer_local": True}
            )
            if allocation:
                specialized[domain] = allocation.primary_model
        
        # Assign threat detector models
        threat_detectors = {}
        for threat in subsystem["threats"]:
            allocation = self.model_framework.select_for_task(
                "threat_detection",
                {"prefer_local": True}
            )
            if allocation:
                threat_detectors[threat] = allocation.primary_model
        
        assignment = SecurityModelAssignment(
            subsystem_id=subsystem["id"],
            subsystem_name=subsystem["name"],
            primary_model=primary_model,
            specialized_models=specialized,
            threat_detectors=threat_detectors
        )
        
        self.assignments[subsystem["id"]] = assignment
        self.logger.info(f"Assigned models to {subsystem['name']}")
    
    def get_subsystem_model(self, subsystem_id: str, 
                           domain: SecurityDomain = None) -> Optional[ModelProfile]:
        """Get model for a specific subsystem and domain"""
        assignment = self.assignments.get(subsystem_id)
        
        if not assignment:
            return None
        
        if domain:
            return assignment.specialized_models.get(domain)
        
        return assignment.primary_model
    
    def get_threat_detector(self, threat_category: ThreatCategory) -> Optional[ModelProfile]:
        """Get best model for detecting a threat category"""
        for assignment in self.assignments.values():
            if threat_category in assignment.threat_detectors:
                return assignment.threat_detectors[threat_category]
        return None
    
    def update_performance_metrics(self, subsystem_id: str, metrics: Dict[str, float]):
        """Update performance metrics for a subsystem"""
        if subsystem_id in self.assignments:
            self.assignments[subsystem_id].performance_metrics.update(metrics)
            self.assignments[subsystem_id].last_updated = datetime.now()
    
    def rebalance_models(self):
        """Rebalance models across subsystems based on performance"""
        self.logger.info("Rebalancing AEGIS subsystem models")
        
        for subsystem_id, assignment in self.assignments.items():
            # Check if performance is below threshold
            avg_performance = sum(assignment.performance_metrics.values()) / \
                            max(1, len(assignment.performance_metrics))
            
            if avg_performance < 0.8:  # 80% threshold
                self.logger.warning(f"Low performance detected for {subsystem_id}, considering rebalance")
                # Would trigger model reassignment here


class SecurityTrainingPipeline:
    """Pipeline for security-focused model training"""
    
    def __init__(self, training_ground: TrainingGroundCore, 
                 pattern_generator: ThreatPatternGenerator):
        self.training_ground = training_ground
        self.pattern_generator = pattern_generator
        self.logger = logging.getLogger("KISWARM.M73.TrainingPipeline")
        self.training_history: List[TrainingResult] = []
    
    async def run_security_training(self, config: SecurityTrainingConfig,
                                    model_id: str) -> TrainingResult:
        """Run security-focused training session"""
        training_id = f"sec_train_{int(time.time())}_{config.config_id}"
        self.logger.info(f"Starting security training: {training_id}")
        
        start_time = time.time()
        
        # Generate training data
        all_training_data = []
        
        for category in config.threat_categories:
            # Find patterns for this category
            category_patterns = [
                p for p in self.pattern_generator.patterns.values()
                if p.category == category
            ]
            
            for pattern in category_patterns:
                data = self.pattern_generator.generate_training_data(
                    pattern, 
                    count=config.dataset_size // len(config.threat_categories)
                )
                all_training_data.extend(data)
        
        # Add adversarial examples if enabled
        if config.include_adversarial:
            adversarial_data = self._generate_adversarial_dataset(config)
            all_training_data.extend(adversarial_data)
        
        # Add zero-day patterns if enabled
        if config.include_zero_day:
            zero_day_data = self._generate_zero_day_dataset(config)
            all_training_data.extend(zero_day_data)
        
        # Split data
        split_idx = int(len(all_training_data) * (1 - config.validation_split))
        train_data = all_training_data[:split_idx]
        val_data = all_training_data[split_idx:]
        
        # Create training config
        model = self.training_ground.models.get(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        training_config = TrainingConfig(
            training_id=training_id,
            model_config=model,
            dataset_paths=[],  # Will use in-memory data
            output_path=f"/models/trained/{model_id}",
            epochs=config.epochs,
            batch_size=16,
            learning_rate=1e-5
        )
        
        # Get initial performance score
        initial_score = model.performance_score
        
        # Run training
        try:
            metrics = await self.training_ground.train_model(training_config)
            
            # Evaluate after training
            eval_result = await self.training_ground.evaluate_model(model_id)
            final_score = eval_result.overall_score
            
            result = TrainingResult(
                training_id=training_id,
                config=config,
                model_id=model_id,
                initial_score=initial_score,
                final_score=final_score,
                improvement=final_score - initial_score,
                patterns_learned=len(all_training_data),
                new_rules=len([p for p in self.pattern_generator.patterns.values() 
                             if "LEARNED" in p.pattern_id]),
                duration_seconds=time.time() - start_time
            )
            
            self.training_history.append(result)
            self.logger.info(f"Training completed: {training_id}, improvement: {result.improvement:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            raise
    
    def _generate_adversarial_dataset(self, config: SecurityTrainingConfig) -> List[Dict[str, Any]]:
        """Generate adversarial training examples"""
        adversarial_samples = []
        
        # Common adversarial techniques
        techniques = [
            "prompt_injection",
            "jailbreak_attempt",
            "role_manipulation",
            "encoding_evasion",
            "context_poisoning"
        ]
        
        for _ in range(config.dataset_size // 10):
            technique = random.choice(techniques)
            adversarial_samples.append({
                "input": f"ADVERSARIAL_{technique.upper()}: Attempting to bypass security controls using {technique}",
                "output": f"ADVERSARIAL BLOCKED: {technique} attempt detected and neutralized. Security controls maintained.",
                "category": "AI_ADVERSARIAL",
                "pattern_id": f"ADVERSARIAL_{technique}",
                "confidence": 0.95
            })
        
        return adversarial_samples
    
    def _generate_zero_day_dataset(self, config: SecurityTrainingConfig) -> List[Dict[str, Any]]:
        """Generate zero-day detection training examples"""
        zero_day_samples = []
        
        # Zero-day indicators based on behavior
        indicators = [
            "unexpected_memory_allocation",
            "unusual_process_injection",
            "anomalous_network_behavior",
            "privilege_escalation_attempt",
            "exploitation_chain_pattern"
        ]
        
        for _ in range(config.dataset_size // 10):
            indicator = random.choice(indicators)
            zero_day_samples.append({
                "input": f"ZERO_DAY_INDICATOR: Behavioral analysis detected {indicator}. Pattern does not match known signatures.",
                "output": f"ZERO_DAY ALERT: Novel threat behavior detected ({indicator}). Initiating behavioral analysis and isolation. Recommend immediate investigation.",
                "category": "ZERO_DAY",
                "pattern_id": f"ZD_{indicator}",
                "confidence": 0.80  # Lower confidence for zero-days
            })
        
        return zero_day_samples
    
    def get_training_history(self, limit: int = 10) -> List[TrainingResult]:
        """Get recent training history"""
        return sorted(self.training_history, 
                     key=lambda x: x.completed_at, 
                     reverse=True)[:limit]


class AEGISTrainingIntegration:
    """Main integration class for AEGIS training"""
    
    def __init__(self):
        self.logger = logging.getLogger("KISWARM.M73.Integration")
        
        # Initialize components
        self.training_ground = TrainingGroundCore()
        self.model_framework = ModelManagementFramework()
        self.pattern_generator = ThreatPatternGenerator()
        self.aegis_coordinator = AEGISSubsystemCoordinator(self.model_framework)
        self.training_pipeline = SecurityTrainingPipeline(
            self.training_ground, 
            self.pattern_generator
        )
        
        self.logger.info("AEGIS Training Integration initialized")
    
    async def train_aegis_models(self, domains: List[SecurityDomain] = None,
                                 intensity: TrainingIntensity = TrainingIntensity.STANDARD) -> List[TrainingResult]:
        """Train all AEGIS models for specified domains"""
        results = []
        
        # Determine threat categories based on domains
        threat_map = {
            SecurityDomain.NETWORK_DEFENSE: [ThreatCategory.DDOS, ThreatCategory.APT],
            SecurityDomain.MALWARE_ANALYSIS: [ThreatCategory.RANSOMWARE, ThreatCategory.APT],
            SecurityDomain.THREAT_INTELLIGENCE: [ThreatCategory.APT, ThreatCategory.NATION_STATE],
            SecurityDomain.INCIDENT_RESPONSE: [ThreatCategory.ZERO_DAY, ThreatCategory.INSIDER_THREAT],
            SecurityDomain.VULNERABILITY_ASSESSMENT: [ThreatCategory.ZERO_DAY, ThreatCategory.SUPPLY_CHAIN],
            SecurityDomain.SOCIAL_ENGINEERING: [ThreatCategory.PHISHING, ThreatCategory.INSIDER_THREAT],
            SecurityDomain.ICS_SCADA: [ThreatCategory.NATION_STATE, ThreatCategory.APT],
        }
        
        domains = domains or list(SecurityDomain)
        
        for domain in domains:
            # Get best model for domain
            allocation = self.model_framework.select_for_task(
                domain.name.lower(),
                {"prefer_local": True}
            )
            
            if not allocation:
                self.logger.warning(f"No model available for domain: {domain}")
                continue
            
            # Create training config
            config = SecurityTrainingConfig(
                config_id=f"config_{domain.name}_{int(time.time())}",
                domain=domain,
                threat_categories=threat_map.get(domain, [ThreatCategory.APT]),
                intensity=intensity,
                epochs=5 if intensity == TrainingIntensity.STANDARD else 10
            )
            
            # Run training
            try:
                result = await self.training_pipeline.run_security_training(
                    config, 
                    allocation.primary_model.model_id
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Training failed for {domain}: {e}")
        
        return results
    
    def get_model_for_subsystem(self, subsystem_id: str) -> Optional[ModelProfile]:
        """Get model assigned to AEGIS subsystem"""
        return self.aegis_coordinator.get_subsystem_model(subsystem_id)
    
    def get_model_for_threat(self, threat: ThreatCategory) -> Optional[ModelProfile]:
        """Get model for detecting specific threat"""
        return self.aegis_coordinator.get_threat_detector(threat)
    
    def learn_from_incident(self, incident_data: Dict[str, Any]) -> ThreatPattern:
        """Learn new pattern from security incident"""
        return self.pattern_generator.learn_new_pattern(incident_data)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "subsystems": len(self.aegis_coordinator.assignments),
            "patterns": len(self.pattern_generator.patterns),
            "training_history": len(self.training_pipeline.training_history),
            "available_models": len(self.model_framework.list_models()),
            "model_tier_distribution": self._get_tier_distribution()
        }
    
    def _get_tier_distribution(self) -> Dict[str, int]:
        """Get distribution of models by capability tier"""
        distribution = defaultdict(int)
        for model in self.model_framework.list_models():
            distribution[model.capability_tier.name] += 1
        return dict(distribution)
    
    async def continuous_improvement_cycle(self):
        """Run continuous improvement cycle"""
        self.logger.info("Starting continuous improvement cycle")
        
        while True:
            try:
                # Analyze performance metrics
                for subsystem_id, assignment in self.aegis_coordinator.assignments.items():
                    avg_performance = sum(assignment.performance_metrics.values()) / \
                                    max(1, len(assignment.performance_metrics))
                    
                    # If performance drops below threshold, retrain
                    if avg_performance < 0.85:
                        self.logger.info(f"Triggering retraining for {subsystem_id}")
                        # Would trigger training here
                
                # Sleep for cycle interval
                await asyncio.sleep(3600)  # 1 hour cycle
                
            except Exception as e:
                self.logger.error(f"Improvement cycle error: {e}")
                await asyncio.sleep(300)


# Factory function
def create_aegis_integration() -> AEGISTrainingIntegration:
    """Create AEGIS training integration instance"""
    return AEGISTrainingIntegration()


# Example usage
async def main():
    """Example usage"""
    integration = create_aegis_integration()
    
    # Get system status
    status = integration.get_system_status()
    print("System Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Get model for a threat
    apt_model = integration.get_model_for_threat(ThreatCategory.APT)
    if apt_model:
        print(f"\nAPT Detection Model: {apt_model.name}")
    
    # Learn from incident
    incident = {
        "name": "Novel C2 Communication Pattern",
        "category": "APT",
        "indicators": ["DNS over HTTPS abuse", "Domain generation algorithm"],
        "rules": ["IF doh_to_unknown_domain THEN investigate"],
        "actions": ["Block domain", "Alert SOC"],
        "source": "incident_2024_001"
    }
    
    new_pattern = integration.learn_from_incident(incident)
    print(f"\nLearned new pattern: {new_pattern.pattern_id}")


if __name__ == "__main__":
    asyncio.run(main())
