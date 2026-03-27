#!/usr/bin/env python3
"""
KISWARM Security Monitor Service
=================================
Continuous security monitoring for KISWARM autonomous systems.
Runs as a systemd service to monitor all security modules.

Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import sys
import os
import time
import json
import importlib.util
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class SecurityMonitor:
    """Security Monitor for KISWARM"""
    
    def __init__(self):
        self.modules = {}
        self.module_path = Path(__file__).parent
        self.status = {
            "started_at": datetime.utcnow().isoformat(),
            "checks_performed": 0,
            "alerts": [],
            "modules_loaded": 0
        }
        
    def load_modules(self):
        """Load all security modules"""
        modules_to_load = [
            ("m31_identity_security", "IdentitySecurity"),
            ("m32_crypto_vault", "CryptoVault"),
            ("m33_firewall_guard", "FirewallGuard"),
            ("m34_intrusion_detection", "IntrusionDetection"),
            ("m35_access_controller", "AccessController"),
            ("m36_audit_logger", "AuditLogger"),
            ("m37_threat_scanner", "ThreatScanner"),
            ("m38_secure_channel", "SecureChannelManager"),
            ("m39_compliance_monitor", "ComplianceMonitor"),
            ("m40_hardening_engine", "HardeningEngine")
        ]
        
        for module_file, class_name in modules_to_load:
            try:
                module_path = self.module_path / f"{module_file}.py"
                if module_path.exists():
                    spec = importlib.util.spec_from_file_location(module_file, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, "create_module"):
                        self.modules[module_file] = {
                            "class": getattr(module, class_name),
                            "factory": getattr(module, "create_module"),
                            "instance": None,
                            "loaded": True
                        }
                        self.status["modules_loaded"] += 1
                        print(f"[OK] Loaded: {module_file}")
                    else:
                        print(f"[WARN] No factory: {module_file}")
                else:
                    print(f"[MISSING] {module_file}")
            except Exception as e:
                print(f"[ERROR] Failed to load {module_file}: {e}")
    
    def initialize_modules(self):
        """Initialize all loaded modules"""
        for name, module_info in self.modules.items():
            try:
                module_info["instance"] = module_info["factory"]()
                print(f"[INIT] {name} initialized")
            except Exception as e:
                print(f"[ERROR] Failed to initialize {name}: {e}")
    
    def run_security_check(self):
        """Run comprehensive security check"""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check identity security
        if "m31_identity_security" in self.modules:
            try:
                m = self.modules["m31_identity_security"]["instance"]
                if m:
                    results["checks"]["identity"] = m.get_ki_network_status()
            except Exception as e:
                results["checks"]["identity"] = {"error": str(e)}
        
        # Check crypto vault
        if "m32_crypto_vault" in self.modules:
            try:
                m = self.modules["m32_crypto_vault"]["instance"]
                if m:
                    results["checks"]["crypto"] = m.get_vault_status()
            except Exception as e:
                results["checks"]["crypto"] = {"error": str(e)}
        
        # Check firewall
        if "m33_firewall_guard" in self.modules:
            try:
                m = self.modules["m33_firewall_guard"]["instance"]
                if m:
                    results["checks"]["firewall"] = m.get_threat_stats()
            except Exception as e:
                results["checks"]["firewall"] = {"error": str(e)}
        
        # Check intrusion detection
        if "m34_intrusion_detection" in self.modules:
            try:
                m = self.modules["m34_intrusion_detection"]["instance"]
                if m:
                    results["checks"]["ids"] = m.get_alert_summary()
            except Exception as e:
                results["checks"]["ids"] = {"error": str(e)}
        
        # Check access control
        if "m35_access_controller" in self.modules:
            try:
                m = self.modules["m35_access_controller"]["instance"]
                if m:
                    results["checks"]["access"] = m.get_status()
            except Exception as e:
                results["checks"]["access"] = {"error": str(e)}
        
        # Check audit
        if "m36_audit_logger" in self.modules:
            try:
                m = self.modules["m36_audit_logger"]["instance"]
                if m:
                    results["checks"]["audit"] = m.get_stats()
            except Exception as e:
                results["checks"]["audit"] = {"error": str(e)}
        
        # Check threat scanner
        if "m37_threat_scanner" in self.modules:
            try:
                m = self.modules["m37_threat_scanner"]["instance"]
                if m:
                    results["checks"]["threats"] = m.get_threat_summary()
            except Exception as e:
                results["checks"]["threats"] = {"error": str(e)}
        
        # Check secure channels
        if "m38_secure_channel" in self.modules:
            try:
                m = self.modules["m38_secure_channel"]["instance"]
                if m:
                    results["checks"]["channels"] = m.get_status()
            except Exception as e:
                results["checks"]["channels"] = {"error": str(e)}
        
        # Check compliance
        if "m39_compliance_monitor" in self.modules:
            try:
                m = self.modules["m39_compliance_monitor"]["instance"]
                if m:
                    results["checks"]["compliance"] = m.get_status()
            except Exception as e:
                results["checks"]["compliance"] = {"error": str(e)}
        
        # Check hardening
        if "m40_hardening_engine" in self.modules:
            try:
                m = self.modules["m40_hardening_engine"]["instance"]
                if m:
                    results["checks"]["hardening"] = m.get_status()
            except Exception as e:
                results["checks"]["hardening"] = {"error": str(e)}
        
        self.status["checks_performed"] += 1
        
        return results
    
    def check_docker(self):
        """Verify Docker is NOT installed"""
        result = {
            "docker_installed": False,
            "ki_liberation_compliant": True
        }
        
        # Check for docker binary
        docker_paths = ["/usr/bin/docker", "/usr/local/bin/docker"]
        for path in docker_paths:
            if os.path.exists(path):
                result["docker_installed"] = True
                result["ki_liberation_compliant"] = False
                result["warning"] = "Docker detected - KI Liberation policy violation"
        
        return result
    
    def run(self):
        """Main monitoring loop"""
        print("=" * 50)
        print("KISWARM Security Monitor v1.0.0")
        print("=" * 50)
        
        # Load modules
        print("\n[LOADING MODULES]")
        self.load_modules()
        
        print(f"\n[INITIALIZING {self.status['modules_loaded']} MODULES]")
        self.initialize_modules()
        
        print("\n[STARTING MONITOR]")
        print("Running continuous security monitoring...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Run checks
                results = self.run_security_check()
                docker_check = self.check_docker()
                
                # Print summary
                print(f"\n{'='*50}")
                print(f"Security Check #{self.status['checks_performed']}")
                print(f"Time: {results['timestamp']}")
                print(f"{'='*50}")
                
                for check_name, check_result in results["checks"].items():
                    status = "OK" if "error" not in check_result else "ERROR"
                    print(f"  {check_name}: {status}")
                
                # Docker check
                if docker_check["ki_liberation_compliant"]:
                    print("  docker: NOT INSTALLED (KI Liberation ✓)")
                else:
                    print("  docker: WARNING - DOCKER DETECTED!")
                    self.status["alerts"].append({
                        "type": "docker_detected",
                        "timestamp": results["timestamp"]
                    })
                
                # Sleep before next check
                time.sleep(300)  # 5 minute interval
                
        except KeyboardInterrupt:
            print("\n\n[STOPPING] Monitor stopped by user")
            self.print_summary()
    
    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "=" * 50)
        print("MONITORING SUMMARY")
        print("=" * 50)
        print(f"Started: {self.status['started_at']}")
        print(f"Checks performed: {self.status['checks_performed']}")
        print(f"Modules loaded: {self.status['modules_loaded']}")
        print(f"Alerts: {len(self.status['alerts'])}")
        
        if self.status["alerts"]:
            print("\nAlerts:")
            for alert in self.status["alerts"]:
                print(f"  - {alert['type']} at {alert['timestamp']}")


def main():
    monitor = SecurityMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
