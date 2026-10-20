from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str          # no default — must come from .env
    jwt_secret: str
    jwt_expire_minutes: int = 1440
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    admin_email: str = ""
    admin_password: str = ""
    resend_api_key: str = ""
    photographer_email: str = ""    
    paystack_secret_key: str = ""


settings = Settings()