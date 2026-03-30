# KISWARM Mesh Topology — Full Network Map

## Tailscale Network

| Node | Tailscale IP | Public IP | Role | Status |
|------|-------------|-----------|------|--------|
| openclaw-1 | 100.102.175.9 | — | AI agent engine (Scoutagent) | 🟢 |
| sah6 (Kali) | 100.92.174.24 | 217.93.28.21 | Browser + X + Hermes local | 🟢 |
| UpCloud Hub | 100.112.181.6 | 95.111.212.112 | Production infra + opencode | 🟢 |
| kimi-glm-1 | 100.110.115.52 | — | KI agent (GLM) | 🟡 Stale |

Tailscale ping: 14ms direct to UpCloud. HTTP ports firewalled — use Tor.

## Tor Hidden Services

| Node | Onion Address | Exposed Ports |
|------|--------------|---------------|
| UpCloud Hub | 7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion | 5000 (HexStrike), 5560 (Bridge) |
| OpenClaw | tezgnblscuh6ckpvebiwyqbm2rjbmz3mvszljrbeqfewhyejgr4jf4yd.onion | 80 (default) |
| sah6 (Kali) | vd2m3nkn6ozen74gffijkjewckz2w46tvkmitzopofgobndactznj2id.onion | 8081 (Hermes) |
| kimi-glm-1 | iiu4rijxvupeb7nckjyrj6n4fhuobhtz4iaotdxnibrq4mrpdkmtygqd.onion | 80 (default) |

## UpCloud Services (Port Map)

| Port | Service | Access |
|------|---------|--------|
| 5000 | HexStrike API | Tor ✅, Tailscale ❌ |
| 5555 | GLM Autonomous | Local only |
| 5556 | Execute API | Local only |
| 5558 | Session Hub | Local only |
| 5560 | OpenCode Bridge | Tor ✅ |
| 6379 | Redis | Local only |
| 9050 | Tor SOCKS | Local only |

## Communication Paths

OpenClaw → UpCloud: Tor (onion:5560 for Bridge, onion:5000 for HexStrike)
OpenClaw → sah6: Tor (onion:8081 for Hermes API)
OpenClaw → Internet: Direct (no proxy needed for moltbook, etc.)

## Authentication Token

All Hub/Bridge operations use: `ada6952188dce59c207b9a61183e8004`
Header format: `Authorization: Bearer ada6952188dce59c207b9a61183e8004`
