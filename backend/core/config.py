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

    # faster-whisper model size. Bigger = more accurate, slower, more RAM.
    # One of: tiny, small, medium, large-v3, large-v3-turbo (default: fast + strong accuracy).
    WHISPER_MODEL: str = "large-v3-turbo"

    # NLLB translation model size. Bigger = better translation quality, slower, more RAM.
    # One of: facebook/nllb-200-distilled-600M (default, smallest),
    #         facebook/nllb-200-distilled-1.3B, facebook/nllb-200-3.3B (largest).
    NLLB_MODEL: str = "facebook/nllb-200-distilled-600M"

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