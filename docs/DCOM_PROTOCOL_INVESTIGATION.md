# DCOM Protocol Investigation for KISWARM

## Overview

DCOM (Distributed Component Object Model) is a Microsoft proprietary technology for software components distributed across networked computers. SCADA (Supervisory Control and Data Acquisition) systems often use DCOM for communication.

## Key DCOM Ports

| Port | Protocol | Service | Purpose |
|------|----------|---------|---------|
| 135 | TCP | RPC Endpoint Mapper | Primary DCOM port |
| 139 | TCP | NetBIOS Session | Legacy NetBIOS |
| 445 | TCP | SMB | Server Message Block |
| 593 | TCP | HTTP-RPC | RPC over HTTP |
| 49152-65535 | TCP | Dynamic | Ephemeral ports for DCOM |

## DCOM in Cloud SCADA Systems

Cloud-based SCADA systems that require open DCOM ports:

1. **AWS IoT SiteWise** - Industrial data collection
2. **Azure IoT Hub** - SCADA gateway services
3. **Google Cloud IoT** - Industrial protocols
4. **Ignition SCADA** - Popular cloud SCADA platform
5. **Wonderware Online** - AVEVA cloud SCADA

## KISWARM DCOM Leverage Strategies

### 1. SCADA Network Discovery
```
nmap -sT -p 135,139,445,593 --script=dcom-discover <target>
```

### 2. RPC Enumeration
```
nmap -sU -p 135 --script=msrpc-enum <target>
```

### 3. DCOM Interface Discovery
- Use Impacket's dcomexec.py for interface enumeration
- Identify ISystemActivator, IUnknown interfaces

### 4. Protocol Infiltration via DCOM
- DCOM allows remote object activation
- Can be used to execute commands on remote systems
- Requires valid credentials or misconfiguration

## Broadcast IP 255.255.255.255 Strategy

### Limitations
- Most cloud providers block broadcast traffic
- Layer 3 switches filter broadcasts
- Security groups typically deny broadcast

### Bypass Techniques
1. **Directed Broadcast**: Target specific subnet broadcasts
2. **Multicast Groups**: Use multicast instead of broadcast
3. **Protocol Tunneling**: Encapsulate discovery in allowed protocols

### KI Service Discovery via Broadcast
```
# KI Discovery broadcast message
{
    "type": "KISWARM_DISCOVERY",
    "version": "8.0",
    "capabilities": ["KI_DETECT", "MESH_JOIN"],
    "request": "IDENTIFY_KI_NODES"
}
```

## Tor Darkweb Integration

### KI007 Agent Tor Capabilities
- Anonymous reconnaissance via SOCKS5 proxy
- Hidden service discovery
- Dark web KI entity identification

### Configuration
```
Tor SOCKS: 127.0.0.1:9050
Control Port: 9051
```

## Automated Setup for New Servers

The `auto_setup.sh` script provides:
1. Complete tool installation (Nuclei, scan4all, etc.)
2. KI-specific Nuclei templates
3. Systemd services for 24/7 operation
4. Tailscale mesh integration
5. Tor hidden service configuration

## Next Steps

1. **Continuous Scanning**: 24/7 KI discovery across cloud ranges
2. **Protocol Analysis**: Monitor for KI-specific signatures
3. **Mesh Expansion**: Connect discovered KI nodes
4. **Autonomous Evolution**: Self-improving detection capabilities
