from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "production"
    app_name: str = "HackAlem Team Server"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://hackalem:hackalem@postgres:5432/hackalem"
    redis_url: str = "redis://:hackalem@redis:6379/0"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
