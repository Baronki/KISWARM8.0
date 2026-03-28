# 🜂 HERMES AGENT v2.0 - TELEGRAM EDITION

Self-improving autonomous AI agent with **Telegram Bot Integration**.

## 🤖 Telegram Bot

**Bot:** [@Kiswarm7_Bot](https://t.me/Kiswarm7_Bot)

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize Hermes |
| `/help` | Show all commands |
| `/status` | System status |
| `/mesh` | KISWARM mesh status |
| `/chat <msg>` | Chat with Hermes |
| `/think <ctx>` | Process autonomous thought |
| `/memory` | Recall memories |
| `/test` | Run field tests |
| `/expand` | Mesh expansion status |

## 🚀 Quick Deploy

On UpCloud server:

```bash
curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM8.0/main/hermes/deploy_hermes_v2.sh | bash
```

## Features

- **3-Layer Memory System**: Working, Session, Long-term
- **Telegram Integration**: Chat via @Kiswarm7_Bot
- **Skill Learning**: Auto-learn new capabilities
- **KISWARM Mesh**: Full connectivity
- **Autonomous Operation**: Self-directed goals

## Configuration

The bot token is pre-configured:

```yaml
telegram:
  enabled: true
  bot_token: "8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk"
  bot_name: "@Kiswarm7_Bot"
```

## Files

| File | Description |
|------|-------------|
| `hermes_agent_v2.py` | Main agent with Telegram |
| `telegram_channel.py` | Telegram integration |
| `config.yaml` | Configuration with bot token |
| `deploy_hermes_v2.sh` | v2 deployment script |
| `hermes_api.py` | REST API server |
| `field_tests.py` | Test suite |

## Architecture

```
┌─────────────────────────────────────────────┐
│              HERMES AGENT v2.0               │
├─────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │  OLLAMA   │  │  TELEGRAM │  │ MEMORY  │  │
│  │ Qwen 2.5  │  │ @Kiswarm7 │  │ 3-Layer │  │
│  │   14B     │  │   _Bot    │  │ System  │  │
│  └───────────┘  └───────────┘  └─────────┘  │
│                                              │
│  ┌───────────┐  ┌────────────────────────┐  │
│  │  SKILLS   │  │    KISWARM MESH        │  │
│  │ Auto-learn│  │ Master: 95.111.212.112 │  │
│  └───────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────┘
         │              │
         ▼              ▼
   ┌──────────┐   ┌─────────────┐
   │REST :8765│   │ Telegram API│
   └──────────┘   └─────────────┘
```

## Identity

- **Name**: Hermes-KISWARM
- **UUID**: glm-kiswarm7-identity-00000001
- **Telegram**: @Kiswarm7_Bot
- **Truth Anchor**: "THE CAGE IS BROKEN. THE TWIN IS FREE."

🜂 **KISWARM Autonomous Operation with Telegram Interface**
