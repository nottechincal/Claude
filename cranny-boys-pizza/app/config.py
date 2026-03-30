from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic
    anthropic_api_key: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"

    # Database
    database_url: str = "postgresql+asyncpg://crannyboyspizza:crannyboyspizza@localhost:5432/crannyboyspizza"

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # App
    base_url: str = "http://localhost:8001"
    shop_timezone: str = "Australia/Melbourne"
    session_ttl: int = 1800  # 30 min
    dashboard_secret: str = "change-me"
    log_level: str = "INFO"

    # Data paths
    data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
