# 🚀 QUICK START - Deploy Now!

Your credentials are saved in `deploy-my-assistant.ps1`

## Run This One Command:

```powershell
.\deploy-my-assistant.ps1
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

Verify ngrok URL is: `https://surveyable-natisha-unsacred.ngrok-free.dev`

If ngrok URL changed, update it in `deploy-my-assistant.ps1`

---

## After Deployment

1. Go to https://dashboard.vapi.ai
2. Open assistant: `320f76b1-140a-412c-b95f-252032911ca3`
3. Update system prompt:
   - Copy ALL of: `config\system-prompt-simplified.md`
   - Paste into system prompt field
   - Save

4. Test with a call!

---

## Your Credentials

**Assistant ID:** `320f76b1-140a-412c-b95f-252032911ca3`

**Webhook URL:** `https://surveyable-natisha-unsacred.ngrok-free.dev`

**API Key:** Saved in `deploy-my-assistant.ps1`

---

**Ready? Run: `.\deploy-my-assistant.ps1`** 🚀
