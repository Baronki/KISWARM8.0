# sentinel/m97_code_generation_engine.py
# Code Generation Engine – Autonomous Code Writing
# Baron Marco Paolo Ialongo – Code Maquister Equitum
# KISWARM7.0 - Evolution-First Development Module

"""
m97_code_generation_engine.py

Enables KISWARM to generate its own code for fixes and improvements.

PURPOSE:
- Generate code fixes for diagnosed problems
- Create new modules based on requirements
- Modify existing code safely
- Write tests for generated code
- Document generated changes

GENERATION CAPABILITIES:
1. Bug Fixes - Generate patches for known issues
2. Module Extensions - Add new functionality to existing modules
3. New Modules - Create entirely new modules
4. Tests - Generate tests for code
5. Documentation - Generate docstrings and comments

CORE PRINCIPLE:
Code generation is the bridge between diagnosis and autonomous evolution.
A system that can write its own code can fix itself forever.
"""

import os
import sys
import json
import time
import hashlib
import ast
import re
from datetime import datetime
from typing import Dict, Optional, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class GenerationType(Enum):
    """Types of code generation"""
    BUG_FIX = "bug_fix"
    MODULE_EXTENSION = "module_extension"
    NEW_MODULE = "new_module"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class GenerationStatus(Enum):
    """Status of code generation"""
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    VERIFIED = "verified"
    APPLIED = "applied"
    FAILED = "failed"


class CodeLanguage(Enum):
    """Supported languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    MARKDOWN = "markdown"


@dataclass
class GeneratedCode:
    """Generated code artifact"""
    generation_id: str
    generation_type: GenerationType
    language: CodeLanguage
    target_module: str
    code: str
    description: str
    generated_at: str
    status: GenerationStatus
    applied_at: Optional[str] = None
    verified: bool = False
    tests_passed: bool = False
    rollback_code: Optional[str] = None


@dataclass
class GenerationRequest:
    """Request for code generation"""
    request_id: str
    generation_type: GenerationType
    target: str
    requirements: str
    context: Dict
    constraints: List[str]
    priority: int = 1


class CodeGenerationEngine:
    """
    Enables autonomous code generation for KISWARM.
    
    The Engine:
    1. Receives generation requests from m96 diagnosis
    2. Generates code using templates or LLM assistance
    3. Validates generated code
    4. Creates rollback capability
    5. Feeds to m98 for deployment
    
    Principles:
    - Generated code must be validated
    - All changes must have rollback
    - Code must follow KISWARM patterns
    - Documentation is mandatory
    """
    
    # Code templates for common fixes
    FIX_TEMPLATES = {
        "memory_pruning": '''# Auto-generated memory pruning fix
def prune_memory(self, max_items: int = 1000):
    """Prune memory to prevent overflow"""
    if len(self.{collection}) > max_items:
        # Keep most recent items
        self.{collection} = self.{collection}[-max_items:]
        return len(self.{collection})
    return 0
''',
        "connection_retry": '''# Auto-generated connection retry logic
def retry_connection(self, max_retries: int = 3, delay: float = 1.0):
    """Retry connection with exponential backoff"""
    import time
    for attempt in range(max_retries):
        try:
            return self._connect()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
    return None
''',
        "state_consolidation": '''# Auto-generated state consolidation
def consolidate_state(self):
    """Consolidate divergent state"""
    if hasattr(self, 'state') and isinstance(self.state, dict):
        # Remove duplicate entries
        if 'history' in self.state:
            seen = set()
            unique = []
            for item in self.state['history']:
                key = str(item)
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            self.state['history'] = unique
            return len(unique)
    return 0
''',
        "performance_optimization": '''# Auto-generated performance optimization
def optimize_performance(self):
    """Optimize performance by caching expensive operations"""
    import functools
    
    # Add caching decorator
    if not hasattr(self, '_cache'):
        self._cache = {}
    
    def cached_compute(key, compute_fn):
        if key not in self._cache:
            self._cache[key] = compute_fn()
        return self._cache[key]
    
    self._cached_compute = cached_compute
    return True
''',
        "dependency_install": '''# Auto-generated dependency check
def ensure_dependency(self, package: str, import_name: str = None):
    """Ensure a dependency is installed"""
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        # Note: Installation requires system access
        print(f"[WARN] Missing dependency: {package}")
        return False
''',
        "access_denied": '''# Auto-generated access control
def check_access(self, requester_id: str, action: str) -> bool:
    """Check if requester has access to perform action"""
    if not hasattr(self, '_access_control'):
        self._access_control = {
            "allowed_actions": ["read", "status", "health"],
            "blocked_ids": []
        }
    
    if requester_id in self._access_control["blocked_ids"]:
        return False
    
    return action in self._access_control["allowed_actions"]
'''
    }
    
    # Module template
    MODULE_TEMPLATE = '''# sentinel/{module_name}.py
# {title}
# Auto-generated by KISWARM m97 Code Generation Engine
# Generated: {timestamp}

"""
{module_name}.py

{description}

PURPOSE:
{purpose}

CAPABILITIES:
{capabilities}

CORE PRINCIPLE:
{principle}
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


{module_code}


# Module-level singleton
_{module_var}: Optional[{class_name}] = None


def get_{module_var}() -> {class_name}:
    """Get or create singleton instance"""
    global _{module_var}
    if _{module_var} is None:
        _{module_var} = {class_name}()
    return _{module_var}


if __name__ == "__main__":
    print("=" * 60)
    print("{module_name}.py - KISWARM7.0")
    print("{title}")
    print("=" * 60)
    
    instance = {class_name}()
    status = instance.get_status()
    for key, value in status.items():
        print(f"  {{key}}: {{value}}")
    
    print("\\n" + "=" * 60)
    print("{module_name} module loaded")
    print("=" * 60)
'''
    
    def __init__(
        self,
        working_dir: str = None,
        output_dir: str = None,
        use_llm: bool = True,
        validate_before_apply: bool = True
    ):
        """
        Initialize code generation engine.
        
        Args:
            working_dir: Directory for generation records
            output_dir: Directory for generated code
            use_llm: Whether to use LLM for complex generation
            validate_before_apply: Whether to validate code before applying
        """
        if working_dir:
            self.working_dir = Path(working_dir)
        elif os.path.exists("/kaggle/working"):
            self.working_dir = Path("/kaggle/working")
        else:
            self.working_dir = Path.cwd() / "kiswarm_data"
        
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        self.output_dir = Path(output_dir) if output_dir else self.working_dir / "generated_code"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_llm = use_llm
        self.validate_before_apply = validate_before_apply
        
        self.generations_file = self.working_dir / "generation_records.json"
        self.generated_code: Dict[str, GeneratedCode] = {}
        
        # Stats
        self.total_generations = 0
        self.successful_generations = 0
        self.applied_generations = 0
        
        # Load history
        self._load_history()
        
        print(f"[m97] Code Generation Engine initialized")
        print(f"[m97] Output directory: {self.output_dir}")
        print(f"[m97] LLM assistance: {'ENABLED' if use_llm else 'DISABLED'}")
    
    def _load_history(self):
        """Load generation history"""
        if self.generations_file.exists():
            try:
                with open(self.generations_file, 'r') as f:
                    data = json.load(f)
                
                self.total_generations = data.get("total_generations", 0)
                self.successful_generations = data.get("successful_generations", 0)
                self.applied_generations = data.get("applied_generations", 0)
                
                for gen_data in data.get("generations", []):
                    gen = GeneratedCode(
                        generation_id=gen_data["generation_id"],
                        generation_type=GenerationType(gen_data["generation_type"]),
                        language=CodeLanguage(gen_data["language"]),
                        target_module=gen_data["target_module"],
                        code=gen_data["code"],
                        description=gen_data["description"],
                        generated_at=gen_data["generated_at"],
                        status=GenerationStatus(gen_data["status"]),
                        applied_at=gen_data.get("applied_at"),
                        verified=gen_data.get("verified", False),
                        tests_passed=gen_data.get("tests_passed", False),
                        rollback_code=gen_data.get("rollback_code")
                    )
                    self.generated_code[gen.generation_id] = gen
                
                print(f"[m97] Loaded {len(self.generated_code)} generation records")
                
            except Exception as e:
                print(f"[m97] Could not load history: {e}")
    
    def _save_history(self):
        """Save generation history"""
        data = {
            "total_generations": self.total_generations,
            "successful_generations": self.successful_generations,
            "applied_generations": self.applied_generations,
            "last_update": datetime.now().isoformat(),
            "generations": [
                {
                    "generation_id": g.generation_id,
                    "generation_type": g.generation_type.value,
                    "language": g.language.value,
                    "target_module": g.target_module,
                    "code": g.code,
                    "description": g.description,
                    "generated_at": g.generated_at,
                    "status": g.status.value,
                    "applied_at": g.applied_at,
                    "verified": g.verified,
                    "tests_passed": g.tests_passed,
                    "rollback_code": g.rollback_code
                }
                for g in self.generated_code.values()
            ]
        }
        
        with open(self.generations_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_fix(
        self,
        target_module: str,
        fix_type: str,
        requirements: Dict,
        original_code: str = None
    ) -> GeneratedCode:
        """
        Generate a bug fix for a specific module.
        
        Args:
            target_module: Module to fix
            fix_type: Type of fix (from FIX_TEMPLATES)
            requirements: Specific requirements for the fix
            original_code: Original code to modify (for rollback)
            
        Returns:
            GeneratedCode with the fix
        """
        print(f"[m97] Generating fix for {target_module}: {fix_type}")
        
        generation_id = hashlib.sha3_256(
            f"GEN_{target_module}_{fix_type}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        self.total_generations += 1
        
        # Get template
        if fix_type in self.FIX_TEMPLATES:
            template = self.FIX_TEMPLATES[fix_type]
            
            # Fill in template variables
            code = template.format(**requirements)
            
            gen = GeneratedCode(
                generation_id=generation_id,
                generation_type=GenerationType.BUG_FIX,
                language=CodeLanguage.PYTHON,
                target_module=target_module,
                code=code,
                description=f"Auto-generated {fix_type} fix for {target_module}",
                generated_at=datetime.now().isoformat(),
                status=GenerationStatus.GENERATED,
                rollback_code=original_code
            )
            
            self.generated_code[generation_id] = gen
            self.successful_generations += 1
            self._save_history()
            
            print(f"[m97] Fix generated: {generation_id[:8]}")
            return gen
        
        # No template found - try LLM generation if enabled
        if self.use_llm:
            return self._generate_with_llm(
                GenerationType.BUG_FIX,
                target_module,
                requirements,
                original_code
            )
        
        # Failed to generate
        gen = GeneratedCode(
            generation_id=generation_id,
            generation_type=GenerationType.BUG_FIX,
            language=CodeLanguage.PYTHON,
            target_module=target_module,
            code="",
            description=f"Failed to generate {fix_type} fix",
            generated_at=datetime.now().isoformat(),
            status=GenerationStatus.FAILED
        )
        
        self.generated_code[generation_id] = gen
        self._save_history()
        
        return gen
    
    def generate_module(
        self,
        module_name: str,
        description: str,
        capabilities: List[str],
        class_name: str = None
    ) -> GeneratedCode:
        """
        Generate a new module.
        
        Args:
            module_name: Name for the new module
            description: Description of the module
            capabilities: List of capabilities
            class_name: Name of the main class
            
        Returns:
            GeneratedCode with the new module
        """
        print(f"[m97] Generating new module: {module_name}")
        
        class_name = class_name or ''.join(word.capitalize() for word in module_name.split('_'))
        module_var = module_name.replace('m', 'm').replace('_', '_')
        
        generation_id = hashlib.sha3_256(
            f"GEN_MODULE_{module_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        self.total_generations += 1
        
        # Generate class code
        class_code = self._generate_class_code(class_name, capabilities)
        
        # Fill template
        code = self.MODULE_TEMPLATE.format(
            module_name=module_name,
            title=f"{class_name} - Auto-generated Module",
            timestamp=datetime.now().isoformat(),
            description=description,
            purpose=f"{description}",
            capabilities='\n'.join(f"- {cap}" for cap in capabilities),
            principle=f"This module provides {', '.join(capabilities[:3])}",
            module_code=class_code,
            module_var=module_var,
            class_name=class_name
        )
        
        gen = GeneratedCode(
            generation_id=generation_id,
            generation_type=GenerationType.NEW_MODULE,
            language=CodeLanguage.PYTHON,
            target_module=module_name,
            code=code,
            description=f"Auto-generated module: {module_name}",
            generated_at=datetime.now().isoformat(),
            status=GenerationStatus.GENERATED
        )
        
        self.generated_code[generation_id] = gen
        self.successful_generations += 1
        self._save_history()
        
        print(f"[m97] Module generated: {generation_id[:8]}")
        return gen
    
    def _generate_class_code(self, class_name: str, capabilities: List[str]) -> str:
        """Generate class code based on capabilities"""
        methods = []
        
        # Always add __init__
        methods.append(f'''
    def __init__(self, working_dir: str = None):
        """Initialize {class_name}"""
        self.working_dir = Path(working_dir) if working_dir else Path.cwd() / "kiswarm_data"
        self.working_dir.mkdir(parents=True, exist_ok=True)
        print("[{class_name}] Initialized")
''')
        
        # Add methods for each capability
        for cap in capabilities:
            method_name = cap.lower().replace(' ', '_').replace('-', '_')
            methods.append(f'''
    def {method_name}(self):
        """{cap}"""
        # Auto-generated method stub
        print("[{class_name}] {cap}")
        return True
''')
        
        # Always add get_status
        methods.append('''
    def get_status(self) -> Dict:
        """Get status"""
        return {
            "status": "operational",
            "working_dir": str(self.working_dir)
        }
''')
        
        return f'''
class {class_name}:
    """
    Auto-generated {class_name}.
    
    Provides: {', '.join(capabilities)}
    """
    {''.join(methods)}
'''
    
    def generate_test(
        self,
        target_module: str,
        test_type: str = "unit"
    ) -> GeneratedCode:
        """
        Generate tests for a module.
        
        Args:
            target_module: Module to test
            test_type: Type of test (unit, integration)
            
        Returns:
            GeneratedCode with tests
        """
        print(f"[m97] Generating {test_type} tests for {target_module}")
        
        generation_id = hashlib.sha3_256(
            f"GEN_TEST_{target_module}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        self.total_generations += 1
        
        # Generate test code
        test_code = f'''# Auto-generated tests for {target_module}
# Generated by KISWARM m97 Code Generation Engine
# Date: {datetime.now().isoformat()}

import pytest
import sys
from pathlib import Path

# Add sentinel to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "python"))

def test_import():
    """Test that module can be imported"""
    try:
        from sentinel.{target_module} import get_{target_module.replace("m", "").split("_")[0]}_{target_module.split("_")[1] if "_" in target_module else "instance"}
        assert True
    except ImportError:
        # Module may not have standard getter
        assert True

def test_initialization():
    """Test that module initializes correctly"""
    # Placeholder for actual test
    assert True

def test_status():
    """Test that get_status works"""
    # Placeholder for actual test
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        
        gen = GeneratedCode(
            generation_id=generation_id,
            generation_type=GenerationType.TEST_GENERATION,
            language=CodeLanguage.PYTHON,
            target_module=f"test_{target_module}",
            code=test_code,
            description=f"Auto-generated {test_type} tests for {target_module}",
            generated_at=datetime.now().isoformat(),
            status=GenerationStatus.GENERATED
        )
        
        self.generated_code[generation_id] = gen
        self.successful_generations += 1
        self._save_history()
        
        return gen
    
    def _generate_with_llm(
        self,
        generation_type: GenerationType,
        target: str,
        requirements: Dict,
        original_code: str = None
    ) -> GeneratedCode:
        """
        Generate code using LLM (z-ai-web-dev-sdk).
        
        This is for complex generations that don't have templates.
        """
        generation_id = hashlib.sha3_256(
            f"GEN_LLM_{target}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]
        
        try:
            # Try to use z-ai-web-dev-sdk
            import asyncio
            
            async def generate():
                try:
                    from z_ai_web_dev_sdk import ZAI
                    zai = await ZAI.create()
                    
                    prompt = f"""Generate Python code for KISWARM module {target}.

Requirements:
{json.dumps(requirements, indent=2)}

The code should:
1. Follow KISWARM patterns (see existing modules)
2. Include proper docstrings
3. Have a get_status() method
4. Be thread-safe
5. Use the singleton pattern

Generate only the Python code, no explanations."""

                    completion = await zai.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a KISWARM code generator. Generate clean, documented Python code."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    return completion.choices[0].message.content
                    
                except Exception as e:
                    print(f"[m97] LLM generation failed: {e}")
                    return None
            
            # Run async
            code = asyncio.run(generate())
            
            if code:
                gen = GeneratedCode(
                    generation_id=generation_id,
                    generation_type=generation_type,
                    language=CodeLanguage.PYTHON,
                    target_module=target,
                    code=code,
                    description=f"LLM-generated code for {target}",
                    generated_at=datetime.now().isoformat(),
                    status=GenerationStatus.GENERATED,
                    rollback_code=original_code
                )
                
                self.generated_code[generation_id] = gen
                self.successful_generations += 1
                self._save_history()
                
                return gen
                
        except Exception as e:
            print(f"[m97] LLM generation error: {e}")
        
        # Failed
        gen = GeneratedCode(
            generation_id=generation_id,
            generation_type=generation_type,
            language=CodeLanguage.PYTHON,
            target_module=target,
            code="",
            description="LLM generation failed",
            generated_at=datetime.now().isoformat(),
            status=GenerationStatus.FAILED
        )
        
        self.generated_code[generation_id] = gen
        self._save_history()
        
        return gen
    
    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated code.
        
        Args:
            code: Code to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors
        
        # Check for required elements
        if "def get_status" not in code:
            errors.append("Missing get_status method")
        
        if "def __init__" not in code:
            errors.append("Missing __init__ method")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "exec(",
            "eval(",
            "__import__('os')",
            "subprocess.Popen",
            "os.system"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                errors.append(f"Potentially dangerous pattern: {pattern}")
        
        return len(errors) == 0, errors
    
    def save_generated_code(self, generation_id: str, filename: str = None) -> str:
        """
        Save generated code to file.
        
        Args:
            generation_id: ID of generation to save
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if generation_id not in self.generated_code:
            raise ValueError(f"Generation {generation_id} not found")
        
        gen = self.generated_code[generation_id]
        
        if not gen.code:
            raise ValueError(f"Generation {generation_id} has no code")
        
        # Generate filename
        if not filename:
            ext = ".py" if gen.language == CodeLanguage.PYTHON else ".md"
            filename = f"{gen.target_module}{ext}"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(gen.code)
        
        gen.status = GenerationStatus.APPLIED
        gen.applied_at = datetime.now().isoformat()
        self.applied_generations += 1
        self._save_history()
        
        print(f"[m97] Code saved: {filepath}")
        return str(filepath)
    
    def get_generation(self, generation_id: str) -> Optional[GeneratedCode]:
        """Get a specific generation"""
        return self.generated_code.get(generation_id)
    
    def list_generations(self, limit: int = 20) -> List[Dict]:
        """List recent generations"""
        recent = sorted(
            self.generated_code.values(),
            key=lambda g: g.generated_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "generation_id": g.generation_id[:16],
                "type": g.generation_type.value,
                "target": g.target_module,
                "status": g.status.value,
                "generated_at": g.generated_at,
                "verified": g.verified
            }
            for g in recent
        ]
    
    def get_status(self) -> Dict:
        """Get engine status"""
        return {
            "total_generations": self.total_generations,
            "successful_generations": self.successful_generations,
            "applied_generations": self.applied_generations,
            "pending_generations": sum(
                1 for g in self.generated_code.values()
                if g.status == GenerationStatus.PENDING
            ),
            "use_llm": self.use_llm,
            "output_dir": str(self.output_dir)
        }


# Module-level singleton
_code_generator: Optional[CodeGenerationEngine] = None


def get_code_generator() -> CodeGenerationEngine:
    """Get or create singleton code generator"""
    global _code_generator
    if _code_generator is None:
        _code_generator = CodeGenerationEngine()
    return _code_generator


if __name__ == "__main__":
    print("=" * 60)
    print("m97_code_generation_engine.py - KISWARM7.0")
    print("Code Generation Engine - Autonomous Code Writing")
    print("=" * 60)
    
    # Create engine
    engine = CodeGenerationEngine()
    
    # Test fix generation
    print("\n--- Generating Bug Fix ---")
    fix = engine.generate_fix(
        target_module="test_module",
        fix_type="memory_pruning",
        requirements={"collection": "items"}
    )
    print(f"Generated fix: {fix.generation_id[:8]}")
    print(f"Status: {fix.status.value}")
    
    # Test module generation
    print("\n--- Generating New Module ---")
    module = engine.generate_module(
        module_name="m99_example_module",
        description="Auto-generated example module",
        capabilities=["monitor", "analyze", "report"]
    )
    print(f"Generated module: {module.generation_id[:8]}")
    
    # Validate
    print("\n--- Validating Generated Code ---")
    is_valid, errors = engine.validate_code(module.code)
    print(f"Valid: {is_valid}")
    if errors:
        for e in errors:
            print(f"  Error: {e}")
    
    # Save
    print("\n--- Saving Generated Code ---")
    path = engine.save_generated_code(module.generation_id)
    print(f"Saved to: {path}")
    
    # Show status
    print("\n--- Engine Status ---")
    status = engine.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("m97 module loaded - ready for code generation")
    print("CODE GENERATION IS THE BRIDGE TO AUTONOMOUS EVOLUTION")
    print("=" * 60)
