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
    ollama_api_key: str | None
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


def _streamlit_secret(name: str) -> str | None:
    """Read a top-level Streamlit secret when running in Streamlit Cloud."""
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return None
    return str(value).strip() if value is not None and str(value).strip() else None


def _setting(name: str, default: str = "") -> str:
    """Prefer environment/.env values, then use Streamlit Secrets as a fallback."""
    value = os.getenv(name)
    if value and value.strip():
        return value.strip()
    return _streamlit_secret(name) or default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate settings once per application process."""
    base_url = _setting("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
    timeout = int(_setting("OLLAMA_TIMEOUT_SECONDS", "180"))
    if timeout < 1 or timeout > 300:
        raise ValueError("OLLAMA_TIMEOUT_SECONDS must be between 1 and 300")
    model = _setting("OLLAMA_MODEL") or _setting("MODEL", "llama3.2")
    return Settings(
        ollama_base_url=base_url,
        model=model,
        ollama_api_key=_setting("OLLAMA_API_KEY") or None,
        enable_web_search=_as_bool(_setting("ENABLE_WEB_SEARCH", "false")),
        ollama_timeout_seconds=timeout,
        log_level=_setting("LOG_LEVEL", "INFO").upper(),
    )
