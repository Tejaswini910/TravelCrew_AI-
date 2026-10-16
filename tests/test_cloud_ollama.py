import json
from io import BytesIO

import pytest

from travel_planner.agents import _common
from travel_planner.config.settings import Settings
from travel_planner.services import planner
from travel_planner.services.planner import OllamaUnavailableError


def make_settings(base_url: str, api_key: str | None, model: str = "gemma4:31b") -> Settings:
    return Settings(
        ollama_base_url=base_url,
        model=model,
        ollama_api_key=api_key,
        enable_web_search=False,
        ollama_timeout_seconds=5,
        log_level="INFO",
    )


def test_cloud_preflight_uses_v1_models_and_bearer_key(monkeypatch) -> None:
    settings = make_settings("https://ollama.com/v1", "test-only-key")
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return BytesIO(json.dumps({"data": [{"id": "gemma4:31b"}]}).encode())

    monkeypatch.setattr(planner, "get_settings", lambda: settings)
    monkeypatch.setattr(planner, "urlopen", fake_urlopen)

    planner.check_ollama()

    assert requests[0].full_url == "https://ollama.com/v1/models"
    assert requests[0].get_header("Authorization") == "Bearer test-only-key"


def test_local_preflight_uses_local_tags_without_cloud_auth(monkeypatch) -> None:
    settings = make_settings("http://localhost:11434", None, "llama3.2")
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return BytesIO(json.dumps({"models": [{"name": "llama3.2:latest"}]}).encode())

    monkeypatch.setattr(planner, "get_settings", lambda: settings)
    monkeypatch.setattr(planner, "urlopen", fake_urlopen)

    planner.check_ollama()

    assert requests[0].full_url == "http://localhost:11434/api/tags"
    assert requests[0].get_header("Authorization") is None


def test_remote_cloud_requires_key_without_calling_local_host(monkeypatch) -> None:
    settings = make_settings("https://ollama.com/v1", None)
    monkeypatch.setattr(planner, "get_settings", lambda: settings)
    monkeypatch.setattr(planner, "urlopen", lambda *args, **kwargs: pytest.fail("unexpected network call"))

    with pytest.raises(OllamaUnavailableError, match="requires OLLAMA_API_KEY"):
        planner.check_ollama()


def test_llm_client_receives_cloud_key_and_logs_only_presence(monkeypatch, caplog) -> None:
    settings = make_settings("https://ollama.com/v1", "test-only-key")
    captured = {}
    caplog.set_level("INFO", logger="travel_planner.agents._common")

    class FakeLLM:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(_common, "get_settings", lambda: settings)
    monkeypatch.setattr(_common, "LLM", FakeLLM)

    _common.local_llm()

    assert captured["base_url"] == "https://ollama.com/v1"
    assert captured["api_key"] == "test-only-key"
    assert "api_key_loaded=True" in caplog.text
    assert "test-only-key" not in caplog.text