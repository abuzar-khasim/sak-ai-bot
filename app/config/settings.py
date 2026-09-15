from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_webhook_secret: str

    database_url: str
    admin_telegram_id: int
    webhook_base_url: str = ""

    admin_email: str
    resend_api_key: str

    groq_api_key: str
    gemini_api_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()