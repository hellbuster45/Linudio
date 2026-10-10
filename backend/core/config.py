from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Where downloaded videos, generated audio and the default SQLite database live.
    # Anchored to backend/ so it doesn't depend on the directory uvicorn was started from.
    STORAGE_DIR: str = str(BACKEND_DIR / "storage")

    # Defaults to a local SQLite file inside STORAGE_DIR (zero setup). Set DATABASE_URL to
    # use Postgres instead; see backend/postgres/README.md.
    DATABASE_URL: str | None = None

    # Browser origins allowed to call the API, comma-separated.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

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

    # Unknown keys in .env (e.g. leftovers from older versions) are ignored, not errors.
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    @model_validator(mode="after")
    def _default_database_url(self):
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite:///{(Path(self.STORAGE_DIR) / 'linudio.db').as_posix()}"
        return self

    @property
    def videos_dir(self) -> Path:
        return Path(self.STORAGE_DIR) / "videos"

    @property
    def cookies_file(self) -> Path:
        return Path(self.STORAGE_DIR) / "cookies.txt"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

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
