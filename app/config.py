from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    gemini_api_key: str
    redis_url: str = "redis://localhost:6379"
settings = Settings()
