# Windows Deployment Guide

Quick guide for deploying on Windows using PowerShell.

## Prerequisites

- Windows PowerShell 5.1 or higher (or PowerShell 7)
- Python 3.8+ installed
- VAPI account with API key
- Your VAPI Assistant ID

## Step 1: Setup Environment

Run the setup script to create directories and install dependencies:

```powershell
.\setup-windows.ps1
```

This will:
- Create `data/`, `logs/`, `backups/`, `config/` directories
- Install Flask, flask-cors, python-dotenv
- Verify Python installation

## Step 2: Copy Menu File

Make sure `menu.json` is in the `data/` directory:

```powershell
# If menu.json is in the root
Copy-Item menu.json data\menu.json
```

## Step 3: Test Server Locally

```powershell
python server_simplified.py
```

Expected output:
```
==================================================
Kebabalab VAPI Server - SIMPLIFIED
==================================================
Database initialized
Menu loaded successfully
Loaded 15 tools:
  1. checkOpen
  2. getCallerSmartContext
  ...
Starting server on port 8000
```

Press `Ctrl+C` to stop.

## Step 4: Run Tests

```powershell
python test_chip_upgrade.py
```

Expected:
```
✓ TEST PASSED - Chip upgrade works in 1 call!
ALL TESTS PASSED!
```

## Step 5: Expose Server (Choose One)

### Option A: ngrok (for testing)

```powershell
# Download ngrok from https://ngrok.com/download
# Then run:
ngrok http 8000
```

Copy your ngrok URL: `https://abc123.ngrok-free.app`

### Option B: Production hosting

Deploy to Railway, Heroku, or your preferred hosting.

## Step 6: Deploy Tools to VAPI (Automated!)

This is the **magic step** - run this script to:
1. Remove ALL old tools from your assistant
2. Upload 15 new simplified tools
3. Attach them to your assistant

```powershell
.\deploy-vapi-tools.ps1 `
  -ApiKey "sk_live_your_api_key_here" `
  -AssistantId "your_assistant_id_here" `
  -WebhookUrl "https://your-webhook-url.com"
```

**Example:**
```powershell
.\deploy-vapi-tools.ps1 `
  -ApiKey "sk_live_abc123def456..." `
  -AssistantId "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6" `
  -WebhookUrl "https://abc123.ngrok-free.app"
```

The script will:
- ✓ Remove all 22 old tools
- ✓ Upload 15 new simplified tools
- ✓ Attach them to your assistant
- ✓ Save tool IDs to `config/vapi-tool-ids.json`

## Step 7: Update System Prompt (Manual)

1. Go to https://dashboard.vapi.ai
2. Open your assistant
3. Click "Edit"
4. Scroll to "System Prompt"
5. Open `config/system-prompt-simplified.md` in Notepad
6. Copy ALL contents
7. Paste into VAPI system prompt field
8. Click "Save"

## Step 8: Test!

Call your VAPI number and test:

**Critical Test:**
```
You: "Hi, chicken kebab meal with Coke please"
AI: [Creates order]
You: "Can you make the chips large?"
AI: [Updates in ~3 seconds] "Done! That's now $25 total"
```

**Expected:**
- ✅ Response within 5 seconds
- ✅ Price updates correctly
- ✅ NO long pauses
- ✅ NO looping

## Troubleshooting

### "Python not found"

Install Python from https://python.org

Make sure to check "Add Python to PATH" during installation.

### "unable to open database file"

Run the setup script:
```powershell
.\setup-windows.ps1
```

This creates the `data/` directory.

### "Module not found: flask"

Install manually:
```powershell
pip install flask flask-cors python-dotenv
```

### "API key invalid"

Get your API key:
1. Go to https://dashboard.vapi.ai
2. Click profile (top right)
3. Go to "API Keys"
4. Copy your private key (starts with `sk_`)

### "Assistant ID not found"

Get your Assistant ID:
1. Go to https://dashboard.vapi.ai
2. Click on your assistant
3. Copy the ID from the URL: `https://dashboard.vapi.ai/assistant/YOUR_ID_HERE`

### "Webhook URL unreachable"

Make sure:
- Server is running: `python server_simplified.py`
- ngrok is running (if using ngrok): `ngrok http 8000`
- Firewall allows connections on port 8000

## Common PowerShell Issues

### "Execution policy" error

If you get an error about execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running the script again.

### Line endings

If you cloned from Git and scripts don't work:

```powershell
# Fix line endings
(Get-Content .\deploy-vapi-tools.ps1) | Set-Content .\deploy-vapi-tools.ps1
```

## Success Checklist

- [x] `setup-windows.ps1` completed successfully
- [x] `python server_simplified.py` starts without errors
- [x] `python test_chip_upgrade.py` passes all tests
- [x] Server exposed via ngrok or production hosting
- [x] `deploy-vapi-tools.ps1` completed successfully
- [x] System prompt updated in VAPI dashboard
- [x] Test call successful
- [x] Chip upgrade works in 1 call

## Quick Commands Reference

```powershell
# Setup
.\setup-windows.ps1

# Test
python test_chip_upgrade.py

# Start server
python server_simplified.py

# Deploy to VAPI (in separate PowerShell window)
.\deploy-vapi-tools.ps1 -ApiKey "sk_..." -AssistantId "abc-123" -WebhookUrl "https://..."

# Check server health
Invoke-WebRequest -Uri http://localhost:8000/health

# View logs
Get-Content logs\kebabalab_simplified.log -Tail 50 -Wait

# Check database
sqlite3 data\orders.db "SELECT COUNT(*) FROM orders;"
```

## Getting Help

- **Setup issues:** See troubleshooting section above
- **VAPI issues:** Check https://docs.vapi.ai
- **Database issues:** Check `logs/kebabalab_simplified.log`
- **Tool deployment issues:** Re-run `deploy-vapi-tools.ps1` with `-Verbose`

---

**You're ready to deploy on Windows!** 🚀

The PowerShell script automates the hard part (removing old tools and uploading new ones).

Just run `.\deploy-vapi-tools.ps1` with your API key, Assistant ID, and webhook URL.
