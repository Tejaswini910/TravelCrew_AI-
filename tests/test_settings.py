from travel_planner.config.settings import get_settings


def test_ollama_model_setting_is_preferred(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:latest")
    monkeypatch.setenv("MODEL", "ignored-model")
    get_settings.cache_clear()
    try:
        assert get_settings().model == "llama3.2:latest"
    finally:
        get_settings.cache_clear()


def test_legacy_model_setting_remains_supported(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setenv("MODEL", "llama3.2")
    get_settings.cache_clear()
    try:
        assert get_settings().model == "llama3.2"
    finally:
        get_settings.cache_clear()