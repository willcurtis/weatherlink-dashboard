import pytest

from weatherlink_dashboard.config import ConfigurationError, Settings


def test_settings_require_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("WEATHERLINK_API_KEY", raising=False)
    monkeypatch.delenv("WEATHERLINK_API_SECRET", raising=False)
    with pytest.raises(ConfigurationError):
        Settings.load(tmp_path / "missing.env")


def test_settings_load(monkeypatch, tmp_path):
    monkeypatch.setenv("WEATHERLINK_API_KEY", "key")
    monkeypatch.setenv("WEATHERLINK_API_SECRET", "secret")
    monkeypatch.setenv("WEATHERLINK_UNITS", "imperial")
    settings = Settings.load(tmp_path / "missing.env")
    assert settings.units == "imperial"
    assert settings.refresh_seconds == 60
