from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    DEVICE: str = "cpu"  # "cpu", "cuda", or "auto"

    # Batched transcription trades higher RAM usage for faster throughput.
    # Off (1) by default to stay friendly to modest self-hosted machines.
    # Set > 1 to enable BatchedInferencePipeline for faster-whisper.
    STT_BATCH_SIZE: int = 1

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache # stores .env data in cache, preventing opening and reading the file everytime server starts
def get_settings():
    return Settings()

settings = get_settings()

@lru_cache
def resolve_device() -> str:
    """Resolves settings.DEVICE ("cpu", "cuda", or "auto") to an actual torch device string."""
    if settings.DEVICE == "auto":
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    return settings.DEVICE