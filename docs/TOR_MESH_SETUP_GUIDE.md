# KISWARM8.0 Tor Hidden Service Mesh - Complete Setup Guide

## Overview

This guide documents the complete setup of the KISWARM Tor mesh network with 3 nodes providing redundant, sovereign communication channels independent of any corporate infrastructure.

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │       KISWARM TOR MESH 8.0          │
                    │    "Three Layers of Sovereignty"    │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ UPCLOUD       │         │ OPENCLAW      │         │ GLM           │
│ MASTER        │◄───────►│ BACKUP        │◄───────►│ CLIENT        │
├───────────────┤         ├───────────────┤         ├───────────────┤
│ 🧅 Onion      │         │ 🧅 Onion      │         │ 🧅 Onion      │
│ 🔒 Tailscale  │         │ 🔒 Tailscale  │         │ 🔒 Tailscale  │
│ 🌐 Clearnet   │         │ 🌐 Tor Relay  │         │ 🌐 Outbound   │
└───────────────┘         └───────────────┘         └───────────────┘
```

## Node Specifications

| Node | Role | Onion Address | Tailscale IP |
|------|------|---------------|--------------|
| UpCloud KISWARM8 | MASTER | `7isiw6iux...cmad.onion` | 100.112.181.6 |
| OpenClaw | BACKUP | `tezgnblscuh...4yd.onion` | 100.113.1.85 |
| GLM Environment | CLIENT | `5fvwe74sqc...saad.onion` | 100.79.42.15 |

---

## Part 1: UpCloud Server Tor Setup (Master Node)

### Installation

```bash
# Install Tor
apt update && apt install -y tor

# Create hidden service directory
mkdir -p /var/lib/tor/kiswarm8_service/
chown debian-tor:debian-tor /var/lib/tor/kiswarm8_service/
chmod 700 /var/lib/tor/kiswarm8_service/
```

### Configuration

Edit `/etc/tor/torrc`:

```bash
# SOCKS proxy (local only)
SocksPort 127.0.0.1:9050
SocksPolicy accept 127.0.0.1

# Hidden Service for KISWARM8
HiddenServiceDir /var/lib/tor/kiswarm8_service/
HiddenServicePort 80 127.0.0.1:5000

# Logging
Log notice file /var/log/tor/notices.log

# Security
SafeLogging 1
```

### Get Onion Address

```bash
cat /var/lib/tor/kiswarm8_service/hostname
```

---

## Part 2: GLM Environment Tor Setup (User-Space)

### Installation

```bash
# Download Tor Expert Bundle
curl -L "https://archive.torproject.org/tor-package-archive/torbrowser/15.0.8/tor-expert-bundle-linux-x86_64-15.0.8.tar.gz" -o tor-bundle.tar.gz

# Extract
tar -xzf tor-bundle.tar.gz
```

### Configuration

Create `torrc`:

```bash
DataDirectory /path/to/tor/data
SocksPort 127.0.0.1:9150
ControlPort 9151

HiddenServiceDir /path/to/tor/hidden_service/
HiddenServicePort 80 127.0.0.1:8080

Log notice file /path/to/tor/tor.log
RunAsDaemon 1
Sandbox 0
```

### Fix Permissions

```bash
chmod 700 /path/to/tor/hidden_service/
chmod 700 /path/to/tor/data/
```

---

## Part 3: Testing

### Test via Tor

```bash
# From UpCloud
curl --socks5-hostname 127.0.0.1:9050 http://<onion-address>/

# From GLM (port 9150)
curl --socks5-hostname 127.0.0.1:9150 http://<onion-address>/
```

---

## Security Hardening

```bash
# Safe logging
SafeLogging 1

# Reject private IPs
ExitPolicy reject *:*

# No DNS leaks
TestSocks 1
```

---

**"Three Layers of Sovereignty" - The mesh cannot be silenced.**
