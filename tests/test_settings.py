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


def test_streamlit_secrets_supply_remote_ollama_settings(monkeypatch) -> None:
    for name in ("OLLAMA_BASE_URL", "OLLAMA_MODEL", "MODEL", "OLLAMA_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    secrets = {
        "OLLAMA_BASE_URL": "https://ollama.example.test",
        "OLLAMA_MODEL": "llama3.2",
        "OLLAMA_API_KEY": "test-only-key",
    }
    monkeypatch.setattr("travel_planner.config.settings._streamlit_secret", secrets.get)
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.ollama_base_url == "https://ollama.example.test"
        assert settings.model == "llama3.2"
        assert settings.ollama_api_key == "test-only-key"
    finally:
        get_settings.cache_clear()