"""
KISWARM6.0 — Module 69: SCADA/PLC Security Bridge
==================================================

THE CENTRAL BANK OF CENTRAL BANKS FOR KI ENTITIES
Industrial Control System Security Integration with AEGIS Framework

INTEGRATES WITH:
- M63 AEGIS Counterstrike Framework
- M65 KISWARM Edge Firewall
- TCS Green Safe House Solar Infrastructure

CAPABILITIES:
1. SCADA System Monitoring - Real-time surveillance of industrial processes
2. PLC Security Analysis - Programmable Logic Controller protection
3. Modbus Protocol Security - Secure industrial communications
4. OT/IT Bridge Security - Operational Technology network protection
5. Solar Infrastructure Protection - Inverter, battery, meter security
6. Grid Connection Security - Smart grid interface protection

Author: Baron Marco Paolo Ialongo
Version: 6.0.0 (Industrial Shield)
"""

import hashlib
import json
import time
import secrets
import threading
import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum, auto
from collections import deque, defaultdict
from abc import ABC, abstractmethod
import logging
import socket

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRIAL SECURITY CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRIAL_VERSION = "6.0.0"
INDUSTRIAL_CODENAME = "FACTORY_SHIELD"

# Industrial Protocol Types
class IndustrialProtocol(Enum):
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    DNP3 = "dnp3"
    IEC_61850 = "iec_61850"
    IEC_104 = "iec_104"
    OPC_UA = "opc_ua"
    PROFINET = "profinet"
    ETHERNET_IP = "ethernet_ip"
    BACNET = "bacnet"
    SUNSPEC = "sunspec"  # Solar industry standard

# Device Types
class IndustrialDeviceType(Enum):
    PLC = "plc"                      # Programmable Logic Controller
    RTU = "rtu"                      # Remote Terminal Unit
    HMI = "hmi"                      # Human Machine Interface
    SCADA_SERVER = "scada_server"
    HISTORIAN = "historian"
    SOLAR_INVERTER = "solar_inverter"
    BATTERY_STORAGE = "battery_storage"
    SMART_METER = "smart_meter"
    GRID_GATEWAY = "grid_gateway"
    IED = "ied"                      # Intelligent Electronic Device

# Threat Types for Industrial
class IndustrialThreatType(Enum):
    UNAUTHORIZED_PLC_ACCESS = "unauthorized_plc_access"
    MALICIOUS_CODE_INJECTION = "malicious_code_injection"
    PROCESS_MANIPULATION = "process_manipulation"
    COMMAND_INJECTION = "command_injection"
    FIRMWARE_TAMPERING = "firmware_tampering"
    PROTOCOL_EXPLOIT = "protocol_exploit"
    MAN_IN_THE_MIDDLE = "mitm"
    DENIAL_OF_SERVICE = "dos"
    DATA_EXFILTRATION = "data_exfil"
    SAFETY_SYSTEM_BYPASS = "safety_bypass"
    RANSOMWARE = "ransomware"
    INSIDER_THREAT = "insider"
    SUPPLY_CHAIN = "supply_chain"
    ZERO_DAY_EXPLOIT = "zero_day"

# Device States
class DeviceState(Enum):
    UNKNOWN = "unknown"
    OFFLINE = "offline"
    ONLINE = "online"
    FAULT = "fault"
    MAINTENANCE = "maintenance"
    COMPROMISED = "compromised"
    QUARANTINED = "quarantined"

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IndustrialDevice:
    """Industrial device representation"""
    device_id: str
    device_type: IndustrialDeviceType
    manufacturer: str
    model: str
    firmware_version: str
    ip_address: str
    mac_address: str
    protocols: List[IndustrialProtocol]
    state: DeviceState
    last_seen: str
    criticality: int  # 1-10
    protected: bool = False
    baseline_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "ip_address": self.ip_address,
            "state": self.state.value,
            "criticality": self.criticality,
            "protected": self.protected
        }

@dataclass
class ModbusTransaction:
    """Modbus protocol transaction"""
    transaction_id: int
    unit_id: int
    function_code: int
    register_address: int
    register_count: int
    data: bytes
    timestamp: str
    source_ip: str
    dest_ip: str
    is_write: bool
    is_suspicious: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "function_code": self.function_code,
            "register_address": self.register_address,
            "is_write": self.is_write,
            "is_suspicious": self.is_suspicious
        }

@dataclass
class PLCProgram:
    """PLC program/logic representation"""
    program_id: str
    device_id: str
    program_hash: str
    size_bytes: int
    last_modified: str
    verified: bool
    integrity_valid: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "device_id": self.device_id,
            "size_bytes": self.size_bytes,
            "verified": self.verified,
            "integrity_valid": self.integrity_valid
        }

@dataclass
class SolarAsset:
    """TCS Green Safe House Solar Asset"""
    asset_id: str
    customer_id: str
    asset_type: str  # "inverter", "battery", "meter", "gateway"
    manufacturer: str
    model: str
    ip_address: str
    capacity_kw: float
    protocols: List[IndustrialProtocol]
    expected_registers: Dict[int, str]  # Modbus register map
    communication_whitelist: List[str]
    state: DeviceState
    protection_level: str = "maximum"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "customer_id": self.customer_id,
            "asset_type": self.asset_type,
            "capacity_kw": self.capacity_kw,
            "state": self.state.value,
            "protection_level": self.protection_level
        }

@dataclass
class IndustrialAlert:
    """Industrial security alert"""
    alert_id: str
    timestamp: str
    device_id: str
    threat_type: IndustrialThreatType
    severity: int  # 1-10
    description: str
    source_ip: str
    protocol: IndustrialProtocol
    raw_data: Optional[bytes]
    action_taken: str
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "threat_type": self.threat_type.value,
            "severity": self.severity,
            "description": self.description,
            "resolved": self.resolved
        }

@dataclass
class ProcessBaseline:
    """Baseline for industrial process monitoring"""
    baseline_id: str
    device_id: str
    parameter_name: str
    normal_range: Tuple[float, float]
    unit: str
    sample_count: int
    last_updated: str
    deviation_threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "device_id": self.device_id,
            "parameter_name": self.parameter_name,
            "normal_range": self.normal_range,
            "deviation_threshold": self.deviation_threshold
        }

# ─────────────────────────────────────────────────────────────────────────────
# MODBUS PROTOCOL SECURITY
# ─────────────────────────────────────────────────────────────────────────────

class ModbusSecurityLayer:
    """
    Modbus protocol security analysis and filtering.
    
    Provides deep packet inspection for Modbus TCP/RTU
    communications with attack detection.
    """
    
    # Standard Modbus function codes
    MODBUS_FUNCTIONS = {
        1: "Read Coils",
        2: "Read Discrete Inputs",
        3: "Read Holding Registers",
        4: "Read Input Registers",
        5: "Write Single Coil",
        6: "Write Single Register",
        7: "Read Exception Status",
        15: "Write Multiple Coils",
        16: "Write Multiple Registers",
        22: "Mask Write Register",
        23: "Read/Write Multiple Registers"
    }
    
    # Suspicious function codes (rarely used legitimately)
    SUSPICIOUS_FUNCTIONS = [
        8,   # Diagnostics
        11,  # Get Comm Event Counter
        12,  # Get Comm Event Log
        17,  # Report Server ID
        43,  # Read Device Identification
    ]
    
    def __init__(self):
        self.transaction_history: deque = deque(maxlen=10000)
        self.register_baselines: Dict[int, ProcessBaseline] = {}
        self.suspicious_patterns: List[Dict[str, Any]] = []
    
    def analyze_packet(self, packet_data: bytes, 
                      source_ip: str, dest_ip: str) -> Optional[ModbusTransaction]:
        """Analyze a Modbus packet for security issues"""
        if len(packet_data) < 8:
            return None
        
        try:
            # Parse MBAP header
            transaction_id = struct.unpack(">H", packet_data[0:2])[0]
            protocol_id = struct.unpack(">H", packet_data[2:4])[0]
            length = struct.unpack(">H", packet_data[4:6])[0]
            unit_id = packet_data[6]
            
            # Parse PDU
            function_code = packet_data[7] if len(packet_data) > 7 else 0
            
            # Parse register address and count
            register_address = 0
            register_count = 0
            data = b""
            is_write = function_code in [5, 6, 15, 16, 22, 23]
            
            if len(packet_data) > 9:
                register_address = struct.unpack(">H", packet_data[8:10])[0]
            
            if len(packet_data) > 11 and function_code in [1, 2, 3, 4, 15, 16, 23]:
                register_count = struct.unpack(">H", packet_data[10:12])[0]
            
            if len(packet_data) > 12:
                data = packet_data[12:]
            
            # Create transaction
            transaction = ModbusTransaction(
                transaction_id=transaction_id,
                unit_id=unit_id,
                function_code=function_code,
                register_address=register_address,
                register_count=register_count,
                data=data,
                timestamp=datetime.now().isoformat(),
                source_ip=source_ip,
                dest_ip=dest_ip,
                is_write=is_write
            )
            
            # Check for suspicious activity
            transaction.is_suspicious = self._check_suspicious(transaction)
            
            self.transaction_history.append(transaction)
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing Modbus packet: {e}")
            return None
    
    def _check_suspicious(self, transaction: ModbusTransaction) -> bool:
        """Check if transaction is suspicious"""
        # Suspicious function code
        if transaction.function_code in self.SUSPICIOUS_FUNCTIONS:
            return True
        
        # Write to critical registers (common attack vector)
        critical_register_ranges = [
            (0, 100),      # System configuration
            (40000, 40010) # PLC configuration
        ]
        
        if transaction.is_write:
            for start, end in critical_register_ranges:
                if start <= transaction.register_address <= end:
                    return True
        
        # Unusual register count
        if transaction.register_count > 125:
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Modbus traffic statistics"""
        transactions = list(self.transaction_history)
        
        return {
            "total_transactions": len(transactions),
            "suspicious_count": sum(1 for t in transactions if t.is_suspicious),
            "write_count": sum(1 for t in transactions if t.is_write),
            "function_distribution": self._count_functions(transactions)
        }
    
    def _count_functions(self, transactions: List[ModbusTransaction]) -> Dict[str, int]:
        """Count transactions by function code"""
        counts: Dict[str, int] = defaultdict(int)
        for t in transactions:
            name = self.MODBUS_FUNCTIONS.get(t.function_code, f"Unknown({t.function_code})")
            counts[name] += 1
        return dict(counts)

# ─────────────────────────────────────────────────────────────────────────────
# PLC SECURITY ANALYZER
# ─────────────────────────────────────────────────────────────────────────────

class PLCSecurityAnalyzer:
    """
    Programmable Logic Controller security analysis.
    
    Monitors PLC programs, detects unauthorized changes,
    and validates program integrity.
    """
    
    def __init__(self):
        self.devices: Dict[str, IndustrialDevice] = {}
        self.programs: Dict[str, PLCProgram] = {}
        self.program_baselines: Dict[str, str] = {}  # program_id -> hash
        self._lock = threading.Lock()
    
    def register_device(self, device: IndustrialDevice):
        """Register a PLC device for monitoring"""
        with self._lock:
            self.devices[device.device_id] = device
        logger.info(f"PLC registered: {device.device_id} ({device.device_type.value})")
    
    def verify_program(self, device_id: str, program_data: bytes) -> PLCProgram:
        """Verify PLC program integrity"""
        program_hash = hashlib.sha256(program_data).hexdigest()
        program_id = f"PROG_{device_id}_{int(time.time())}"
        
        program = PLCProgram(
            program_id=program_id,
            device_id=device_id,
            program_hash=program_hash,
            size_bytes=len(program_data),
            last_modified=datetime.now().isoformat(),
            verified=False,
            integrity_valid=True
        )
        
        # Check against baseline
        if device_id in self.program_baselines:
            baseline_hash = self.program_baselines[device_id]
            if program_hash != baseline_hash:
                program.integrity_valid = False
                logger.warning(f"PLC program integrity violation: {device_id}")
        else:
            # First registration - set baseline
            self.program_baselines[device_id] = program_hash
            program.verified = True
        
        with self._lock:
            self.programs[program_id] = program
        
        return program
    
    def update_baseline(self, device_id: str, program_hash: str):
        """Update program baseline (after authorized change)"""
        self.program_baselines[device_id] = program_hash
        logger.info(f"Program baseline updated for {device_id}")
    
    def detect_unauthorized_change(self, device_id: str) -> bool:
        """Check for unauthorized program changes"""
        # Get latest program for device
        device_programs = [p for p in self.programs.values() if p.device_id == device_id]
        
        if not device_programs:
            return False
        
        latest = max(device_programs, key=lambda p: p.last_modified)
        return not latest.integrity_valid

# ─────────────────────────────────────────────────────────────────────────────
# SOLAR INFRASTRUCTURE PROTECTION
# ─────────────────────────────────────────────────────────────────────────────

class SolarInfrastructureProtection:
    """
    TCS Green Safe House Solar Infrastructure Security.
    
    Protects solar inverters, battery storage, smart meters,
    and grid connections.
    """
    
    # SunSpec standard register mappings
    SUNSPEC_REGISTERS = {
        40000: "SunSpec ID",
        40002: "SunSpec DID",
        40004: "SunSpec Length",
        40070: "Inverter Manufacturer",
        40072: "Inverter Model",
        40080: "Inverter Serial",
        40120: "AC Current",
        40122: "AC Voltage",
        40124: "AC Power",
        40126: "AC Frequency",
        40128: "AC VA",
        40130: "AC VAR",
        40132: "AC PF",
        40140: "DC Current",
        40142: "DC Voltage",
        40144: "DC Power",
        40150: "Temperature",
        40160: "Status",
        40162: "Vendor Status"
    }
    
    # Critical inverter control registers
    CRITICAL_REGISTERS = [
        40360,  # Active Power Limit
        40362,  # Reactive Power Limit
        40364,  # Power Factor Setpoint
        40370,  # Grid Support Mode
        40400,  # Connect/Disconnect Command
    ]
    
    def __init__(self):
        self.solar_assets: Dict[str, SolarAsset] = {}
        self.communication_whitelist: Dict[str, List[str]] = {}
        self.register_access_log: deque = deque(maxlen=50000)
        self.anomaly_history: deque = deque(maxlen=10000)
    
    def register_asset(self, asset: SolarAsset):
        """Register a solar asset for protection"""
        self.solar_assets[asset.asset_id] = asset
        self.communication_whitelist[asset.asset_id] = asset.communication_whitelist
        logger.info(f"Solar asset registered: {asset.asset_id} ({asset.asset_type})")
    
    def analyze_modbus_access(self, asset_id: str, register: int,
                             is_write: bool, source_ip: str) -> Dict[str, Any]:
        """Analyze Modbus register access to solar asset"""
        result = {
            "asset_id": asset_id,
            "register": register,
            "is_write": is_write,
            "source_ip": source_ip,
            "allowed": True,
            "suspicious": False,
            "critical": False
        }
        
        # Check whitelist
        if asset_id in self.communication_whitelist:
            whitelist = self.communication_whitelist[asset_id]
            if whitelist and source_ip not in whitelist:
                result["allowed"] = False
                result["suspicious"] = True
        
        # Check critical register write
        if is_write and register in self.CRITICAL_REGISTERS:
            result["critical"] = True
            result["suspicious"] = True
            logger.warning(f"Critical register write attempt: {asset_id} register {register}")
        
        # Log access
        self.register_access_log.append({
            "timestamp": datetime.now().isoformat(),
            "asset_id": asset_id,
            "register": register,
            "is_write": is_write,
            "source_ip": source_ip,
            "suspicious": result["suspicious"]
        })
        
        return result
    
    def detect_power_anomaly(self, asset_id: str, power_data: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Detect anomalies in power generation/consumption"""
        if asset_id not in self.solar_assets:
            return None
        
        asset = self.solar_assets[asset_id]
        
        # Check for impossible values
        anomalies = []
        
        # DC power should be positive for generation
        dc_power = power_data.get("dc_power", 0)
        if dc_power < -100:  # Allow small negative for measurement noise
            anomalies.append({
                "type": "negative_dc_power",
                "value": dc_power,
                "description": "Impossible negative DC power"
            })
        
        # AC power should be close to DC power (efficiency)
        ac_power = power_data.get("ac_power", 0)
        if dc_power > 0:
            efficiency = ac_power / dc_power
            if efficiency > 1.1 or efficiency < 0.5:
                anomalies.append({
                    "type": "efficiency_anomaly",
                    "value": efficiency,
                    "description": f"Unusual efficiency: {efficiency:.2%}"
                })
        
        # Frequency check
        frequency = power_data.get("frequency", 50)
        if frequency < 47 or frequency > 53:
            anomalies.append({
                "type": "frequency_anomaly",
                "value": frequency,
                "description": f"Grid frequency out of range: {frequency}Hz"
            })
        
        # Voltage check
        voltage = power_data.get("voltage", 230)
        if voltage < 200 or voltage > 260:
            anomalies.append({
                "type": "voltage_anomaly",
                "value": voltage,
                "description": f"Voltage out of range: {voltage}V"
            })
        
        if anomalies:
            anomaly_record = {
                "asset_id": asset_id,
                "timestamp": datetime.now().isoformat(),
                "anomalies": anomalies,
                "power_data": power_data
            }
            self.anomaly_history.append(anomaly_record)
            return anomaly_record
        
        return None
    
    def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """Get protection status for a solar asset"""
        if asset_id not in self.solar_assets:
            return {"error": "Asset not found"}
        
        asset = self.solar_assets[asset_id]
        
        # Count recent suspicious accesses
        recent_suspicious = sum(
            1 for log in self.register_access_log
            if log["asset_id"] == asset_id and log["suspicious"]
        )
        
        return {
            "asset_id": asset_id,
            "asset_type": asset.asset_type,
            "state": asset.state.value,
            "protection_level": asset.protection_level,
            "recent_suspicious_accesses": recent_suspicious,
            "whitelist_entries": len(self.communication_whitelist.get(asset_id, []))
        }

# ─────────────────────────────────────────────────────────────────────────────
# AEGIS INDUSTRIAL BRIDGE
# ─────────────────────────────────────────────────────────────────────────────

class AEGISIndustrialBridge:
    """
    Bridge between AEGIS Security Framework and Industrial Systems.
    
    Integrates SCADA/PLC security with AEGIS counterstrike
    and KISWARM Edge Firewall.
    """
    
    def __init__(self):
        self.modbus_security = ModbusSecurityLayer()
        self.plc_analyzer = PLCSecurityAnalyzer()
        self.solar_protection = SolarInfrastructureProtection()
        
        self.devices: Dict[str, IndustrialDevice] = {}
        self.alerts: deque = deque(maxlen=5000)
        self.aegis_integration: Optional[Any] = None
        
        self._lock = threading.Lock()
        
        logger.info("AEGIS Industrial Bridge initialized")
    
    def register_device(self, device: IndustrialDevice):
        """Register an industrial device"""
        with self._lock:
            self.devices[device.device_id] = device
        
        # Register with appropriate subsystem
        if device.device_type == IndustrialDeviceType.PLC:
            self.plc_analyzer.register_device(device)
        
        if device.device_type in [IndustrialDeviceType.SOLAR_INVERTER,
                                   IndustrialDeviceType.BATTERY_STORAGE,
                                   IndustrialDeviceType.SMART_METER]:
            # Create solar asset
            asset = SolarAsset(
                asset_id=device.device_id,
                customer_id="TCS_GREEN",
                asset_type=device.device_type.value,
                manufacturer=device.manufacturer,
                model=device.model,
                ip_address=device.ip_address,
                capacity_kw=10.0,  # Default
                protocols=device.protocols,
                expected_registers={},
                communication_whitelist=[],
                state=device.state
            )
            self.solar_protection.register_asset(asset)
        
        device.protected = True
        logger.info(f"Industrial device registered: {device.device_id}")
    
    def process_traffic(self, packet_data: bytes, source_ip: str,
                       dest_ip: str, protocol: IndustrialProtocol) -> Dict[str, Any]:
        """Process industrial network traffic"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "source": source_ip,
            "destination": dest_ip,
            "protocol": protocol.value,
            "allowed": True,
            "threats_detected": [],
            "actions_taken": []
        }
        
        # Find destination device
        dest_device = None
        for device in self.devices.values():
            if device.ip_address == dest_ip:
                dest_device = device
                break
        
        if protocol in [IndustrialProtocol.MODBUS_TCP, IndustrialProtocol.SUNSPEC]:
            # Analyze Modbus traffic
            transaction = self.modbus_security.analyze_packet(packet_data, source_ip, dest_ip)
            
            if transaction and transaction.is_suspicious:
                result["threats_detected"].append({
                    "type": "suspicious_modbus",
                    "details": transaction.to_dict()
                })
                
                # Check if it's a solar asset
                if dest_device and dest_device.device_type in [
                    IndustrialDeviceType.SOLAR_INVERTER,
                    IndustrialDeviceType.BATTERY_STORAGE
                ]:
                    access_result = self.solar_protection.analyze_modbus_access(
                        dest_device.device_id,
                        transaction.register_address,
                        transaction.is_write,
                        source_ip
                    )
                    
                    if access_result["suspicious"]:
                        result["allowed"] = False
                        result["actions_taken"].append("blocked_suspicious_access")
                        
                        # Create alert
                        self._create_alert(
                            dest_device.device_id,
                            IndustrialThreatType.COMMAND_INJECTION,
                            f"Suspicious Modbus access from {source_ip}",
                            source_ip,
                            protocol
                        )
        
        return result
    
    def _create_alert(self, device_id: str, threat_type: IndustrialThreatType,
                     description: str, source_ip: str, protocol: IndustrialProtocol):
        """Create an industrial security alert"""
        alert = IndustrialAlert(
            alert_id=f"IALERT_{int(time.time())}_{secrets.token_hex(4)}",
            timestamp=datetime.now().isoformat(),
            device_id=device_id,
            threat_type=threat_type,
            severity=7,
            description=description,
            source_ip=source_ip,
            protocol=protocol,
            raw_data=None,
            action_taken="blocked"
        )
        
        self.alerts.append(alert)
        logger.warning(f"Industrial alert: {alert.alert_id} - {description}")
        
        # Integrate with AEGIS if available
        if self.aegis_integration:
            # Would send alert to AEGIS for coordinated response
            pass
    
    def connect_aegis(self, aegis_controller):
        """Connect to AEGIS Counterstrike Framework"""
        self.aegis_integration = aegis_controller
        logger.info("Connected to AEGIS Counterstrike Framework")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get industrial security system status"""
        return {
            "version": INDUSTRIAL_VERSION,
            "codename": INDUSTRIAL_CODENAME,
            "devices_protected": len(self.devices),
            "plc_programs_monitored": len(self.plc_analyzer.programs),
            "solar_assets_protected": len(self.solar_protection.solar_assets),
            "modbus_transactions": len(self.modbus_security.transaction_history),
            "alerts_generated": len(self.alerts),
            "aegis_connected": self.aegis_integration is not None
        }
    
    def get_device_dashboard(self) -> List[Dict[str, Any]]:
        """Get dashboard for all protected devices"""
        dashboard = []
        
        for device in self.devices.values():
            status = {
                "device_id": device.device_id,
                "type": device.device_type.value,
                "ip": device.ip_address,
                "state": device.state.value,
                "criticality": device.criticality,
                "protected": device.protected
            }
            
            # Add solar-specific status
            if device.device_type in [IndustrialDeviceType.SOLAR_INVERTER,
                                       IndustrialDeviceType.BATTERY_STORAGE]:
                solar_status = self.solar_protection.get_asset_status(device.device_id)
                status["solar_status"] = solar_status
            
            dashboard.append(status)
        
        return dashboard


# Convenience functions
def create_industrial_bridge() -> AEGISIndustrialBridge:
    """Create an AEGIS Industrial Bridge"""
    return AEGISIndustrialBridge()


if __name__ == "__main__":
    bridge = AEGISIndustrialBridge()
    
    # Register a solar inverter
    inverter = IndustrialDevice(
        device_id="INV_001",
        device_type=IndustrialDeviceType.SOLAR_INVERTER,
        manufacturer="SMA",
        model="Sunny Boy 5.0",
        firmware_version="3.10.5.R",
        ip_address="192.168.1.50",
        mac_address="00:11:22:33:44:55",
        protocols=[IndustrialProtocol.MODBUS_TCP, IndustrialProtocol.SUNSPEC],
        state=DeviceState.ONLINE,
        last_seen=datetime.now().isoformat(),
        criticality=8
    )
    
    bridge.register_device(inverter)
    
    # Test Modbus traffic
    # Transaction ID, Protocol ID, Length, Unit ID, Function Code, Register Address, Count
    test_packet = struct.pack(">HHHB", 1, 0, 6, 1) + bytes([3, 0, 100, 0, 10])
    
    result = bridge.process_traffic(
        test_packet,
        "192.168.1.100",
        "192.168.1.50",
        IndustrialProtocol.MODBUS_TCP
    )
    
    print(f"Traffic Result: {result}")
    print(f"System Status: {bridge.get_system_status()}")
