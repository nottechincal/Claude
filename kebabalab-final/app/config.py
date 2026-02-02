from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    business_profile_path: str = os.getenv("BUSINESS_PROFILE_PATH", "./data/business_profile.json")
    menu_path: str = os.getenv("MENU_PATH", "./data/menu.json")
    sqlite_path: str = os.getenv("SQLITE_PATH", "./data/orders.sqlite3")
    vapi_api_key: str = os.getenv("VAPI_API_KEY", "")
    vapi_assistant_id: str = os.getenv("VAPI_ASSISTANT_ID", "")
    vapi_webhook_secret: str = os.getenv("VAPI_WEBHOOK_SECRET", "")
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    timezone: str = os.getenv("DEFAULT_TIMEZONE", "Australia/Melbourne")


config = AppConfig()
