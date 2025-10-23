# Deployment Files

All deployment tools and guides for the simplified system.

## Quick Start

**Windows users (recommended):**
```powershell
# Run this one file - it has your credentials saved
.\deploy-my-assistant.ps1
```

Then update system prompt in VAPI dashboard (copy from `../config/system-prompt-simplified.md`)

**Or follow detailed guides:**

| File | Purpose |
|------|---------|
| **QUICK_START.md** | 5-minute deployment guide |
| **DEPLOYMENT_CHECKLIST.md** | Checklist format |
| **DEPLOYMENT_PRODUCTION.md** | Complete production guide (60+ steps) |
| **WINDOWS_DEPLOYMENT.md** | Windows-specific instructions |

## Deployment Scripts

| Script | Purpose |
|--------|---------|
| **deploy-vapi-tools.ps1** | Main PowerShell deployment script |
| **deploy-my-assistant.ps1** | Quick deploy with saved credentials (gitignored) |
| **setup-windows.ps1** | Windows environment setup |
| **start_production.sh** | Linux/Mac production startup |
| **upload_tools_to_vapi.py** | Python tool upload script |

## How to Deploy

### Option 1: Quick (Windows)

```powershell
.\setup-windows.ps1           # One-time setup
.\deploy-my-assistant.ps1     # Deploy tools to VAPI
```

### Option 2: Manual

```powershell
.\deploy-vapi-tools.ps1 -ApiKey "sk_..." -AssistantId "abc-123" -WebhookUrl "https://..."
```

### Option 3: Python

```bash
python upload_tools_to_vapi.py YOUR_API_KEY YOUR_WEBHOOK_URL
```

## After Deployment

1. Update system prompt in VAPI:
   - Copy: `../config/system-prompt-simplified.md`
   - Paste into VAPI dashboard → System Prompt

2. Test with a call:
   - "Chicken kebab meal with Coke please"
   - "Can you make the chips large?"
   - Should work in <5 seconds

## See Also

- `../config/` - Configuration files
- `../tests/` - Test the deployment
- `../docs/` - Full documentation
