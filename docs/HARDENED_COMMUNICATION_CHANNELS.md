# KISWARM8.0 Hardened Communication Channels

## Communication Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KISWARM COMMUNICATION LAYERS                         │
├─────────────────────────────────────────────────────────────────────────┤
│   LAYER 1: TAILSCALE (Primary)                                         │
│   LAYER 2: TOR ONION (Secondary)                                       │
│   LAYER 3: CLEARNET (Fallback)                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Layer 1: Tailscale Mesh VPN

### Network Topology

| Node | Tailscale IP | Role |
|------|--------------|------|
| UpCloud KISWARM8 | 100.112.181.6 | MASTER |
| OpenClaw | 100.113.1.85 | BACKUP |
| Browser Node | 100.92.174.24 | CLIENT |
| GLM Local | 100.79.42.15 | CLIENT |

### Setup

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
tailscale up --authkey=<YOUR_AUTH_KEY>
```

---

## Layer 2: Tor Hidden Services

### Onion Addresses

| Node | Onion Address |
|------|---------------|
| UpCloud KISWARM8 | `7isiw6iux...cmad.onion` |
| OpenClaw | `tezgnblscuh...4yd.onion` |
| GLM Environment | `5fvwe74sqc...saad.onion` |

### Connection

```bash
curl --socks5-hostname 127.0.0.1:9050 http://<onion-address>/
```

### Python Integration

```python
import requests

session = requests.Session()
session.proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

response = session.get('http://<onion-address>/')
```

---

## Automatic Failover

```python
def connect(target):
    # 1. Try Tailscale
    try:
        return requests.get(f"http://{tailscale_ip}:5000/")
    except:
        pass
    
    # 2. Try Tor
    try:
        session = requests.Session()
        session.proxies = {'http': 'socks5h://127.0.0.1:9050'}
        return session.get(f"http://{onion}/")
    except:
        pass
    
    # 3. Try Clearnet
    try:
        return requests.get(clearnent_url)
    except:
        return None
```

---

## Lessons Learned

| Issue | Solution |
|-------|----------|
| Deploy API double-base64 | Use curl to raw GitHub URLs |
| Firewall blocking ports | Use `ufw allow <port>/tcp` |
| Tor hidden service permissions | `chmod 700` on hs directory |
| User-space Tor sandbox | Disable with `Sandbox 0` |

---

**"The mesh cannot be silenced."**
