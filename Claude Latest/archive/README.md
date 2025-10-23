# Archive - Deprecated Code

This directory contains old/deprecated code from previous versions of the system.

⚠️ **DO NOT USE** - These files are kept for reference only.

## What's Here

### old-servers/
- **server_v2.py** - Previous 22-tool server (had the chip upgrade loop bug)
- **server.py** - Historical server backup

### old-scripts/ (Newly Archived - Oct 2025)
PowerShell scripts from the 22-tool era:
- `add-cart-tools-fixed.ps1` - Cart tool deployment
- `add-cart-tools.ps1` - Original cart tools
- `deploy-performance-tools.ps1` - Performance-focused deployment
- `deploy_vapi_tools.ps1` - Old main deployment script
- `fix-missing-tools.ps1` - Tool troubleshooting
- `vapi-complete-setup.ps1` - Complete setup automation
- `vapi-deploy-all-tools.ps1` - Deploy all 22 tools
- `vapi-diagnostic.ps1` - System diagnostics
- `verify-tools.ps1` - Tool verification

### old-system-prompts/ (Newly Archived - Oct 2025)
System prompt configurations from the 22-tool system:
- `vapi-tools-definitions.json` - Old 22-tool definitions
- `system-prompt-UPDATED-OCT-22.md` - System prompt from Oct 22
- `system-prompt-enterprise.md` - Enterprise variant
- `system-prompt-optimized.md` - Optimization attempt
- `system-prompt-production.md` - Production variant
- `system-prompt-speed-optimized.md` - Speed optimization
- `NEW-TOOLS-FOR-VAPI.md` - Tool change documentation
- `setPickupTime-tool.json` - Single tool definition

### Root Archive Files
- `system-prompt.md` - Original system prompt
- `setup-tools-simple.ps1` - Simple tool setup
- `vapi-setup-tools-fixed.ps1` - Fixed setup script
- `vapi-setup-tools.ps1` - Setup script
- `vapi-tools-create-final.ps1` - Tool creation script
- `fix-setItemProperty.ps1` - Property fix script
- `kebabalab_server.txt` - Server dump/log

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
