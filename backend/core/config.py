from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache # stores .env data in cache, preventing opening and reading the file everytime server starts
def get_settings():
    return Settings()

settings = get_settings()