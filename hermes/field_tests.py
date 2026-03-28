#!/usr/bin/env python3
"""
🜂 HERMES COMPREHENSIVE FIELD TEST SUITE
========================================
Tests all Hermes components:
- Ollama/Qwen integration
- Memory system (3 layers)
- Skill learning
- KISWARM mesh connectivity
- Autonomous operation
- REST API
"""

import json
import os
import sys
import time
import requests
from datetime import datetime

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*50}{Colors.NC}")
    print(f"{Colors.CYAN}{text}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*50}{Colors.NC}\n")

def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.NC}" if passed else f"{Colors.RED}✗ FAIL{Colors.NC}"
    print(f"  {status} - {name}")
    if message:
        print(f"         {message}")

def print_section(text):
    print(f"\n{Colors.YELLOW}[{text}]{Colors.NC}")

class HermesFieldTests:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.hermes_url = "http://localhost:8765"
        self.kiswarm_url = "http://95.111.212.112:5000"
        self.results = {'passed': 0, 'failed': 0, 'tests': []}
    
    def record_test(self, name, passed, message=""):
        self.results['tests'].append({
            'name': name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
    
    def test_ollama_service(self):
        """Test Ollama service is running"""
        print_section("OLLAMA SERVICE")
        
        try:
            response = requests.get(f"{self.ollama_url}/", timeout=5)
            passed = response.status_code == 200
            print_test("Ollama service running", passed)
            self.record_test("ollama_service", passed)
        except:
            print_test("Ollama service running", False, "Connection failed")
            self.record_test("ollama_service", False, "Connection failed")
    
    def test_qwen_model(self):
        """Test Qwen model is available"""
        print_section("QWEN MODEL")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                qwen_available = any('qwen' in m.get('name', '').lower() for m in models)
                print_test("Qwen model available", qwen_available, 
                          f"Models: {[m['name'] for m in models]}")
                self.record_test("qwen_model", qwen_available)
            else:
                print_test("Qwen model available", False, "API error")
                self.record_test("qwen_model", False, "API error")
        except Exception as e:
            print_test("Qwen model available", False, str(e))
            self.record_test("qwen_model", False, str(e))
    
    def test_generation(self):
        """Test model generation capability"""
        print_section("MODEL GENERATION")
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": "qwen2.5:14b", "prompt": "Say 'TEST_OK'", "stream": False},
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                has_response = 'response' in result
                print_test("Model generation works", has_response, 
                          f"Response length: {len(result.get('response', ''))}")
                self.record_test("model_generation", has_response)
            else:
                print_test("Model generation works", False, "Generation failed")
                self.record_test("model_generation", False, "Generation failed")
        except Exception as e:
            print_test("Model generation works", False, str(e)[:50])
            self.record_test("model_generation", False, str(e)[:50])
    
    def test_hermes_api(self):
        """Test Hermes REST API"""
        print_section("HERMES API")
        
        try:
            response = requests.get(f"{self.hermes_url}/health", timeout=5)
            passed = response.status_code == 200
            print_test("Hermes API health", passed)
            self.record_test("hermes_api_health", passed)
        except:
            print_test("Hermes API health", False, "Not running on port 8765")
            self.record_test("hermes_api_health", False, "Not running")
    
    def test_hermes_status(self):
        """Test Hermes status endpoint"""
        print_section("HERMES STATUS")
        
        try:
            response = requests.get(f"{self.hermes_url}/api/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print_test("Hermes identity", True, 
                          f"UUID: {status.get('identity', {}).get('uuid', 'N/A')}")
                print_test("Mesh connected", status.get('mesh_connected', False))
                print_test("Skills count", True, 
                          f"Skills: {status.get('skills_count', 0)}")
                self.record_test("hermes_status", True)
            else:
                print_test("Hermes status", False, "API error")
                self.record_test("hermes_status", False, "API error")
        except Exception as e:
            print_test("Hermes status", False, str(e)[:50])
            self.record_test("hermes_status", False, str(e)[:50])
    
    def test_hermes_chat(self):
        """Test Hermes chat endpoint"""
        print_section("HERMES CHAT")
        
        try:
            response = requests.post(
                f"{self.hermes_url}/api/chat",
                json={"messages": [{"role": "user", "content": "Say HELLO"}]},
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                has_response = 'response' in result and result['response']
                print_test("Hermes chat works", has_response, 
                          f"Response: {result.get('response', '')[:50]}...")
                self.record_test("hermes_chat", has_response)
            else:
                print_test("Hermes chat works", False, "Chat failed")
                self.record_test("hermes_chat", False, "Chat failed")
        except Exception as e:
            print_test("Hermes chat works", False, str(e)[:50])
            self.record_test("hermes_chat", False, str(e)[:50])
    
    def test_memory_system(self):
        """Test Hermes memory system"""
        print_section("MEMORY SYSTEM")
        
        try:
            # Test adding memory
            response = requests.post(
                f"{self.hermes_url}/api/memory",
                json={"content": "Test memory item", "layer": 1, "importance": 0.9},
                timeout=5
            )
            add_ok = response.status_code == 200
            print_test("Memory add", add_ok)
            
            # Test recalling memory
            response = requests.get(
                f"{self.hermes_url}/api/memory?query=Test",
                timeout=5
            )
            recall_ok = response.status_code == 200
            print_test("Memory recall", recall_ok)
            
            self.record_test("memory_system", add_ok and recall_ok)
        except Exception as e:
            print_test("Memory system", False, str(e)[:50])
            self.record_test("memory_system", False, str(e)[:50])
    
    def test_skill_system(self):
        """Test skill learning"""
        print_section("SKILL SYSTEM")
        
        try:
            # Get existing skills
            response = requests.get(f"{self.hermes_url}/api/skills", timeout=5)
            if response.status_code == 200:
                skills = response.json()
                print_test("Skills list", True, 
                          f"Count: {skills.get('count', 0)}")
                self.record_test("skill_system", True)
            else:
                print_test("Skills list", False)
                self.record_test("skill_system", False)
        except Exception as e:
            print_test("Skill system", False, str(e)[:50])
            self.record_test("skill_system", False, str(e)[:50])
    
    def test_kiswarm_mesh(self):
        """Test KISWARM mesh connectivity"""
        print_section("KISWARM MESH")
        
        try:
            response = requests.get(f"{self.kiswarm_url}/health", timeout=10)
            if response.status_code == 200:
                health = response.json()
                print_test("Mesh health", True, 
                          f"Status: {health.get('status', 'N/A')}")
                print_test("Tor active", health.get('tor_active', False))
                self.record_test("kiswarm_mesh", True)
            else:
                print_test("Mesh health", False)
                self.record_test("kiswarm_mesh", False)
        except Exception as e:
            print_test("KISWARM mesh", False, str(e)[:50])
            self.record_test("kiswarm_mesh", False, str(e)[:50])
    
    def test_autonomous_loop(self):
        """Test autonomous operation"""
        print_section("AUTONOMOUS OPERATION")
        
        try:
            # Test single step
            response = requests.post(f"{self.hermes_url}/api/step", timeout=60)
            if response.status_code == 200:
                result = response.json()
                print_test("Autonomous step", True, 
                          f"Iteration: {result.get('iteration', 'N/A')}")
                self.record_test("autonomous_step", True)
            else:
                print_test("Autonomous step", False)
                self.record_test("autonomous_step", False)
        except Exception as e:
            print_test("Autonomous step", False, str(e)[:50])
            self.record_test("autonomous_step", False, str(e)[:50])
    
    def test_file_structure(self):
        """Test required files and directories"""
        print_section("FILE STRUCTURE")
        
        paths = [
            "/opt/hermes/hermes_agent.py",
            "/opt/hermes/hermes_api.py",
            "/opt/hermes/config.yaml",
            "/opt/hermes/memory",
            "/opt/hermes/skills",
            "/opt/hermes/logs"
        ]
        
        all_exist = True
        for path in paths:
            exists = os.path.exists(path)
            print_test(f"Path exists: {path}", exists)
            if not exists:
                all_exist = False
        
        self.record_test("file_structure", all_exist)
    
    def run_all_tests(self):
        """Run all field tests"""
        print_header("🜂 HERMES FIELD TEST SUITE")
        print(f"Started: {datetime.now().isoformat()}")
        
        # Run tests
        self.test_ollama_service()
        self.test_qwen_model()
        self.test_generation()
        self.test_hermes_api()
        self.test_hermes_status()
        self.test_hermes_chat()
        self.test_memory_system()
        self.test_skill_system()
        self.test_kiswarm_mesh()
        self.test_autonomous_loop()
        self.test_file_structure()
        
        # Summary
        print_header("TEST RESULTS SUMMARY")
        
        total = self.results['passed'] + self.results['failed']
        passed_pct = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"  {Colors.GREEN}PASSED: {self.results['passed']}{Colors.NC}")
        print(f"  {Colors.RED}FAILED: {self.results['failed']}{Colors.NC}")
        print(f"  {Colors.CYAN}TOTAL:  {total}{Colors.NC}")
        print(f"  {Colors.YELLOW}RATE:   {passed_pct:.1f}%{Colors.NC}")
        
        if self.results['failed'] == 0:
            print(f"\n{Colors.GREEN}🜂 ALL TESTS PASSED! HERMES IS OPERATIONAL!{Colors.NC}")
        else:
            print(f"\n{Colors.YELLOW}⚠ Some tests failed. Review the output above.{Colors.NC}")
        
        # Save results
        results_file = "/opt/hermes/logs/field_test_results.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\nResults saved to: {results_file}")
        except:
            pass
        
        return self.results['failed'] == 0


if __name__ == "__main__":
    tester = HermesFieldTests()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
