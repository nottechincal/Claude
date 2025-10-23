# Archive - Deprecated Code

This directory contains old/deprecated code from previous versions of the system.

⚠️ **DO NOT USE** - These files are kept for reference only.

## What's Here

### old-servers/
- **server_v2.py** - Previous 22-tool server (had the chip upgrade loop bug)

### Old Scripts
- PowerShell scripts from previous deployment attempts
- Tool setup scripts for old system

### Old System Prompt
- `system-prompt.md` - Original system prompt

## Why These Were Replaced

The old system (server_v2.py with 22 tools) had:
- ❌ Tool overlap (editCartItem vs modifyCartItem)
- ❌ Infinite loops (20+ calls for chip upgrade)
- ❌ Slow performance (25-30 tool calls per order)
- ❌ Customer hang-ups due to wait time

## New System

The simplified system (server_simplified.py with 15 tools) has:
- ✅ Zero tool overlap
- ✅ One call per action
- ✅ 70% faster (8-10 tool calls per order)
- ✅ No loops, no bugs

## Migration Path

If you need to rollback (hopefully never):

1. Stop new server:
   ```bash
   pkill -f server_simplified.py
   ```

2. Start old server:
   ```bash
   python archive/old-servers/server_v2.py
   ```

3. Restore old VAPI tools:
   - Delete 15 new tools
   - Re-add 22 old tools from `../config/archive/vapi-tools-definitions.json`

See `../deployment/DEPLOYMENT_PRODUCTION.md` Section 10 for full rollback plan.

## See Also

- `../docs/SIMPLIFICATION_SUMMARY.md` - What changed and why
- `../docs/SIMPLIFICATION_DESIGN.md` - Design decisions
