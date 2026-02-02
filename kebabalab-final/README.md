# Kebabalab Final (Rebuilt)

A clean-room rebuild of the Kebabalab ordering system with an API-first design and integrations for Twilio, ElevenLabs, and Vapi.ai. The system is designed to be business-agnostic: supply a menu, business profile, and operational rules, and the assistant can adapt to a different business with new tools and voice configuration.

## Highlights
- **Business-agnostic**: configurable business profile + menu JSON.
- **Vapi.ai tool webhook**: a single webhook endpoint to handle tool calls reliably.
- **Twilio SMS**: send receipts, confirmations, or fallback notifications.
- **ElevenLabs**: optional TTS generation for custom prompts or previews.
- **SQLite storage**: orders + sessions with zero external dependencies.

## Quick start

1. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure env**
   ```bash
   cp .env.example .env
   # edit .env with your keys
   ```

4. **Run the API**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Expose webhook for Vapi** (optional)
   Use ngrok or a tunnel provider to point Vapi tools to:
   ```
   https://YOUR-NGROK-DOMAIN/webhook/vapi
   ```

## Structure
```
app/
  main.py            # FastAPI entrypoint
  config.py          # Env config
  models.py          # Pydantic models
  storage.py         # SQLite storage
  integrations/
    twilio_client.py
    elevenlabs_client.py
    vapi_webhook.py
  services/
    business_profile.py
    menu_service.py
    order_service.py
scripts/
  provision-vapi-tools.ps1
  provision-vapi-assistant.ps1
  set-env.ps1
```

## Notes on secrets
Do **not** commit real credentials to the repo. Put secrets in `.env` or environment variables.

## Vapi tool provisioning
Run the PowerShell scripts in `scripts/` to create tools and update the assistant config.

```powershell
./scripts/provision-vapi-tools.ps1 -WebhookUrl "https://your-domain/webhook/vapi" -Force
./scripts/provision-vapi-assistant.ps1 -AssistantId "your-assistant-id"
```

## API endpoints (core)
- `GET /health`
- `GET /menu`
- `POST /menu`
- `POST /orders`
- `GET /orders/{order_id}`
- `POST /webhook/vapi` (for Vapi tool calls)
- `POST /voice/elevenlabs/tts`

## Customization
Update `data/business_profile.json` and `data/menu.json` to adapt to a new business.
