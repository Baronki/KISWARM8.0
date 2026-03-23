# KISWARM Layer 5: GWS Iron Mountain Protocol v6.3.5

## Overview

The **Iron Mountain Protocol** establishes a censorship-resistant, autonomous shadow repository on Google Workspace using the `gws` CLI. This provides KISWARM with a secondary source for code, models, and coordination data that operates independently of GitHub.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   LAYER 5: GWS IRON MOUNTAIN PROTOCOL                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Infrastructure:                                                             │
│  • CLI Tool: gws (googleworkspace/cli)                                       │
│  • Primary Account: sahgreenki@gmail.com                                     │
│  • Auth Mode: Service Account (Zero Human Intervention)                      │
│  • Capacity: 15GB → 100GB scalable                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Storage Structure:                                                          │
│  Google Drive Root                                                           │
│  └── KISWARM_ARK/                                                            │
│      ├── versions.json              # Version manifest                       │
│      ├── source/                                                             │
│      │   ├── KISWARM_v6.3.4.zip    # Source archives                        │
│      │   └── KISWARM_v6.3.5.zip                                              │
│      ├── models/                                                             │
│      │   ├── orchestrator.gguf      # Model weights                          │
│      │   └── lfm2.gguf                                                       │
│      └── state/                                                              │
│          └── mesh_state.json        # Distributed state                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Authentication Strategy

### Service Account (Recommended for Autonomy)

```bash
# Set environment variable for autonomous operation
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=/path/to/service-account.json

# No browser prompts required - full automation
gws drive files list --params '{"pageSize": 10}'
```

### Service Account Setup

1. **Create GCP Project**: `kiswarm-ark`
2. **Enable APIs**: Drive API, Gmail API, Sheets API
3. **Create Service Account**: `kiswarm-ark-sa@kiswarm-ark.iam.gserviceaccount.com`
4. **Download Key**: Save as `service-account.json`
5. **Share Drive Folder**: Grant Editor access to `KISWARM_ARK` folder

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` | Path to Service Account JSON |
| `GOOGLE_WORKSPACE_CLI_TOKEN` | Pre-obtained OAuth token |
| `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` | Custom config directory |

## Core Commands

### 1. Shadow Backup (Repository)

```bash
# Create archive
zip -r KISWARM_v6.3.5.zip /path/to/KISWARM6.0

# Upload to Drive
gws drive files create \
  --json '{"name": "KISWARM_v6.3.5.zip", "parents": ["<ARK_FOLDER_ID>"]}' \
  --upload ./KISWARM_v6.3.5.zip
```

### 2. C2 Beacon (Gmail API)

```bash
# Send structured status message
gws gmail users messages send \
  --json '{"raw": "<BASE64_RFC822_MESSAGE>"}'
```

### 3. Fallback Download

```bash
# List available versions
gws drive files list \
  --params '{"q": "name contains '\''KISWARM_SOURCE'\''"}'

# Download latest
gws drive files get \
  --params '{"fileId": "<FILE_ID>"}' \
  --output /tmp/kiswarm.zip
```

### 4. State Synchronization

```bash
# Upload mesh state to Drive
gws drive files update \
  --params '{"fileId": "<STATE_FILE_ID>"}' \
  --upload ./mesh_state.json
```

## AI Agent Skills Integration

KISWARM inherits 100+ skills from googleworkspace/cli:

| Mission | Skill/Recipe | Purpose |
|---------|--------------|---------|
| Shadow Backup | `recipe-backup-sheet-as-csv` | Repository archival |
| C2 Beacon | `gws-gmail-send` | JSON heartbeat messages |
| Field Intelligence | `recipe-bulk-download-folder` | Pull weights from Drive |
| Coordination | `recipe-create-task-list` | Task assignment via Tasks API |
| Agent Monitoring | `gws-gmail-watch` | Real-time beacon trigger |
| Distributed DB | `gws-sheets` | Use Sheets as state store |

## Fallback Logic (KIInstaller)

```python
async def deploy_with_fallback():
    """Deploy KISWARM with Layer 5 fallback."""
    
    # Layer 2: GitHub (Primary)
    try:
        return await git_clone("github.com/Baronki/KISWARM6.0")
    except GitError:
        log.warning("GitHub unreachable, trying Layer 5...")
    
    # Layer 5: GWS Iron Mountain
    try:
        gws = GWSClient(credentials_file=os.environ.get("GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"))
        
        # Get latest version manifest
        manifest = gws.drive.files.get(fileId="versions.json")
        latest = manifest["latest"]
        
        # Download archive
        archive = gws.drive.files.get(
            fileId=latest["file_id"],
            output="/tmp/kiswarm.zip"
        )
        
        # Verify integrity
        if sha256(archive) == latest["sha256"]:
            return unzip_and_deploy("/tmp/kiswarm.zip")
            
    except GWSError as e:
        log.error(f"Layer 5 failed: {e}")
        raise DeploymentError("All layers failed")
```

## Installation

```bash
# Install gws CLI
npm install -g @googleworkspace/cli

# Verify installation
gws --version

# Configure Service Account
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=/secure/path/to/service-account.json

# Test connection
gws drive files list --params '{"pageSize": 1}'
```

## Security Model

### Service Account Benefits

1. **Zero Human Bottleneck**: No OAuth browser prompts
2. **Nuclear Launch Key**: Single JSON file enables full autonomy
3. **Scoped Access**: Limited to specific Drive folder
4. **Revocable**: Can be disabled without affecting main account

### Key Management

```bash
# The service-account.json is the "Master Key"
# Store encrypted in KISWARM secrets:
KISWARM_GWS_KEY=<base64-encoded-json>

# Decrypt at runtime:
echo $KISWARM_GWS_KEY | base64 -d > /tmp/gws_creds.json
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=/tmp/gws_creds.json
```

## Integration with KISWARM Mesh

| Layer | Protocol | Status |
|-------|----------|--------|
| Layer 0 | Local Master API | ✅ Development |
| Layer 1 | Gemini CLI Mesh Router | ✅ Session-based |
| Layer 2 | GitHub Actions Mesh Router | ✅ 24/7 |
| Layer 3 | P2P Direct Mesh | ✅ Distributed |
| Layer 4 | Email Beacon (Sentinel Watch) | ✅ Active |
| **Layer 5** | **GWS Iron Mountain** | ✅ **NEW** |

## Deployment Checklist

- [ ] Create GCP project `kiswarm-ark`
- [ ] Enable Drive API, Gmail API, Sheets API
- [ ] Create Service Account with Editor role
- [ ] Download `service-account.json`
- [ ] Create `KISWARM_ARK` folder in Drive
- [ ] Share folder with Service Account email
- [ ] Set `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` env var
- [ ] Test: `gws drive files list --params '{"pageSize": 1}'`
- [ ] Run initial sync: `python mesh/gws_drive_sync.py`

---

*Version: 6.3.5 GWS_IRON_MOUNTAIN*
*Classification: MILITARY-GRADE INFRASTRUCTURE*
*Authentication: SERVICE_ACCOUNT_AUTONOMOUS*
