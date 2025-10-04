from marketlens.config import load_settings, Settings


def test_default_settings_loads():
    settings = load_settings()
    assert isinstance(settings, Settings)
    assert settings.database.type in ("duckdb", "postgres")
