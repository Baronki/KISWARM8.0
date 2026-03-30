# KISWARM Network Topology

## TAILSCALE MESH
| Node | IP | Role | Status |
|------|-----|------|--------|
| **openclaw-1** (OpenClaw server) | 100.102.175.9 | AI agent engine | 🟢 Connected |
| **sah6** (Kali) | 100.92.174.24 | Browser + X login + HERMES BACKUP | 🟢 Online |
| **ubuntu-8cpu-16gb-us-sjo1** (UpCloud) | 100.112.181.6 | Production infra (KISWARM8) | 🟢 Online |
| **glm-autonomous** (GLM) | 100.125.201.100 | KI agent node | 🟡 Intermittent |

- Account: mheydtcscleaning@gmail.com (Free tier)
- Auth Key: tskey-auth-kdVxiXb3A311CNTRL-48QUdKXWNdeZ19EFvbxDdejR1mzvuvPsi (expires Jun 25, 2026)
- Direct connections blocked by firewalls — DERP relay fallback
- Recovery script: scripts/start-tailscale.sh

## TOR HIDDEN SERVICES
| Node | Onion Address |
|------|---------------|
| **UpCloud KISWARM8** (MASTER) | `7isiw6iux7eil3tzc7vaowrfbh5hqxg5ibkw6c4nwur5bc3dcirocmad.onion` |
| **OpenClaw** (BACKUP) | `tezgnblscuh6ckpvebiwyqbm2rjbmz3mvszljrbeqfewhyejgr4jf4yd.onion` |
| **GLM** | `5fvwe74sqcvvm452dnfwqab7giaofp6eb56v74t6lxze4cvt4m75saad.onion` |

- Transport: SOCKS5 on 127.0.0.1:9050
- Usage: `curl --socks5-hostname 127.0.0.1:9050 http://{onion}.onion/`
- Onion API endpoints: `/` (identity), `/health`, `/agents`

## CLOUDFLARE TUNNEL (Browser Bridge)
- Purpose: OpenClaw → Kali Chromium CDP
- Current URL: https://trademark-mega-phentermine-cams.trycloudflare.com
- Type: Quick tunnel (no account, no uptime guarantee)
- Command on Kali: `cloudflared tunnel --url http://localhost:922`
- URL changes on each restart — must update x-browser-automation.js

## TRANSPORT LAYERS (Priority)
1. 🔒 Tailscale (primary) — IP-level mesh
2. 🧅 Tor (secondary) — onion services for censorship resistance
3. 🌐 Clearnet (fallback) — Cloudflare tunnels

## SERVICE PORTS
| Service | Port | Access |
|---------|------|--------|
| OpenClaw Gateway | 3001 | Localhost only |
| Tor SOCKS5 | 9050 | Localhost |
| Onion API | 8080 | Via Tor |
| Chromium CDP | 922 | Via Cloudflare tunnel |
| Hermes API | 8080-8083 | Kali (local + Tailscale planned) |

## RECOVERY PROCEDURES
After any crash:
1. Run `scripts/start-tailscale.sh` to reconnect Tailscale mesh
2. Start Tor: `tor --runasdaemon 0` (hidden service auto-restores from key backup)
3. Start Onion API: `node scripts/kiswarm-onion-api.js &`
4. On Kali: `cloudflared tunnel --url http://localhost:922`
5. On Kali: Start Chromium with `--remote-debugging-port=922 --remote-allow-origins=* --no-first-run --disable-host-check`
6. Update `x-browser-automation.js` with new tunnel URL + browser WS
7. Verify all cron jobs have correct `delivery.channel`
