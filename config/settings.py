"""Environment-backed application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    model: str
    enable_web_search: bool
    ollama_timeout_seconds: int
    log_level: str

    @property
    def crewai_model(self) -> str:
        """Return CrewAI/LiteLLM's Ollama model identifier."""
        return self.model if self.model.startswith("ollama/") else f"ollama/{self.model}"


def _as_bool(value: str, default: bool = False) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings once per application process."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
    timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
    if timeout < 1 or timeout > 300:
        raise ValueError("OLLAMA_TIMEOUT_SECONDS must be between 1 and 300")
    return Settings(
        ollama_base_url=base_url,
        model=os.getenv("OLLAMA_MODEL", os.getenv("MODEL", "llama3.2")).strip() or "llama3.2",
        enable_web_search=_as_bool(os.getenv("ENABLE_WEB_SEARCH", "false")),
        ollama_timeout_seconds=timeout,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
