# 🚀 QUICK START - Deploy Now!

**First Time Setup:**
1. Copy `.env.example` to `.env`
2. Fill in your VAPI credentials in `.env`
3. Run the deployment script

## Run This One Command:

```powershell
.\deployment\deploy-my-assistant.ps1
```

That's it! This will:
1. ✅ Remove all 22 old tools from VAPI
2. ✅ Upload 15 new simplified tools
3. ✅ Attach them to your assistant
4. ✅ Configure webhook URL: https://surveyable-natisha-unsacred.ngrok-free.dev

---

## Before You Run

Make sure your server is running:

```powershell
# Terminal 1: Start server
python server_simplified.py

# Terminal 2: Start ngrok
ngrok http 8000
```

Verify your ngrok URL matches what's in your `.env` file (NGROK_URL variable).

If ngrok URL changed, update it in `.env` file.

---

## After Deployment

1. Go to https://dashboard.vapi.ai
2. Open your assistant (Assistant ID from your `.env` file)
3. Update system prompt:
   - Copy ALL of: `config\system-prompt-simplified.md`
   - Paste into system prompt field
   - Save

4. Test with a call!

---

## Configuration

All credentials are stored in `.env` file:
- **VAPI_ASSISTANT_ID** - Your VAPI assistant ID
- **NGROK_URL** - Your ngrok webhook URL
- **VAPI_API_KEY** - Your VAPI API key

**SECURITY:** Never commit `.env` to version control! See `.env.example` for template.

---

**Ready? Run: `.\deployment\deploy-my-assistant.ps1`** 🚀
