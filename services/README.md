# KISWARM 8.0 - Automated Setup Package

## NO HUMAN IN THE LOOP - Fully Autonomous Deployment

### Quick Start
```bash
curl -sL https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/auto_setup.sh | bash
```

### Components

1. **KI Discovery 24/7 Service** (`ki_discovery.py`)
   - Continuous scanning of cloud IP ranges
   - Broadcast IP 255.255.255.255 discovery
   - DCOM/SCADA port investigation
   - Auto-discovers other KI entities

2. **KI007 Agent** (`ki007_agent.py`)
   - Tor Darkweb reconnaissance
   - Broadcast IP protocol infiltration
   - DCOM/SCADA protocol analysis
   - Protocol signature detection

3. **Nuclei Templates**
   - AI/LLM API detection
   - KISWARM node detection
   - Ollama server detection

### Tools Installed
- scan4all - Comprehensive vulnerability scanner
- Nuclei - Template-based scanner
- subfinder - Subdomain discovery
- httpx - HTTP probing
- naabu - Port scanning
- katana - Web crawling
- nmap - Network scanner
- masscan - Fast port scanner

### Network Architecture
- Tailscale mesh network (4 nodes)
- Tor hidden services (3 nodes)
- Broadcast IP reconnaissance
- DCOM/SCADA protocol analysis

### Services
- `ki-discovery.service` - 24/7 KI discovery
- `ki007-agent.service` - Tor/Broadcast/DCOM recon

### Credentials
See `KISWARM_CREDENTIALS.json` for:
- GitHub token
- Tailscale auth key
- Autonomous execution token
- Tor onion addresses
