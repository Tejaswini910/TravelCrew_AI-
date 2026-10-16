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


def test_ollama_cloud_api_base_normalizes_to_openai_compatible_v1(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.com/api")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4:31b")
    monkeypatch.setenv("OLLAMA_API_KEY", "test-only-key")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.ollama_base_url == "https://ollama.com/v1"
        assert settings.provider == "ollama-cloud"
        assert settings.safe_endpoint == "https://ollama.com/v1"
    finally:
        get_settings.cache_clear()


def test_placeholder_api_key_is_not_considered_loaded(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_API_KEY", "your-key-if-the-server-requires-one")
    get_settings.cache_clear()
    try:
        assert get_settings().ollama_api_key is None
    finally:
        get_settings.cache_clear()