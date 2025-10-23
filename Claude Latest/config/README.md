# Configuration Files

## Current Configuration (Simplified System)

| File | Purpose |
|------|---------|
| **vapi-tools-simplified.json** | 15 tool definitions for VAPI |
| **system-prompt-simplified.md** | AI system prompt for VAPI assistant |
| **.env.production.example** | Production environment variables template |

## Usage

### VAPI Tools

Upload to VAPI using deployment scripts:
```powershell
# Automated
..\deployment\deploy-my-assistant.ps1

# Manual
..\deployment\deploy-vapi-tools.ps1 -ApiKey "..." -AssistantId "..." -WebhookUrl "..."
```

### System Prompt

1. Open `system-prompt-simplified.md`
2. Copy ALL contents
3. Go to https://dashboard.vapi.ai
4. Open your assistant
5. Paste into "System Prompt" field
6. Save

### Environment Variables

```bash
cp .env.production.example ../.env.production
# Edit .env.production with your values
```

## Archive

Old configuration files from the 22-tool system are in `archive/`:

- `vapi-tools-definitions.json` - Old 22-tool definitions
- `system-prompt-*.md` - Previous system prompts
- `setPickupTime-tool.json` - Individual tool definitions
- `NEW-TOOLS-FOR-VAPI.md` - Tool addition instructions

These are kept for reference only. **Use the simplified versions above.**

## Key Differences

| Metric | Old (archive/) | New (current) |
|--------|---------------|--------------|
| Tools | 22 | 15 |
| System prompt | Multiple versions | One optimized version |
| Complexity | High (overlapping tools) | Low (focused tools) |
| Performance | Slow (25-30 calls/order) | Fast (8-10 calls/order) |

## See Also

- `../deployment/` - How to deploy these configs
- `../docs/SIMPLIFICATION_SUMMARY.md` - What changed
