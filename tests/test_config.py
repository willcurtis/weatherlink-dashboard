import pytest

from weatherlink_dashboard.config import (
    ConfigurationError,
    Settings,
    find_config_file,
    save_user_config,
    user_config_path,
)


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


def test_user_config_path_on_macos(monkeypatch, tmp_path):
    monkeypatch.setattr("weatherlink_dashboard.config.sys.platform", "darwin")
    monkeypatch.setattr("weatherlink_dashboard.config.Path.home", lambda: tmp_path)
    assert user_config_path() == tmp_path / "Library/Application Support/WeatherLink Dashboard/.env"


def test_save_and_find_user_config(monkeypatch, tmp_path):
    target = tmp_path / "config/.env"
    monkeypatch.setattr("weatherlink_dashboard.config.user_config_path", lambda: target)
    monkeypatch.chdir(tmp_path)

    saved = save_user_config("key", "secret", "123")

    assert saved == target
    assert find_config_file() == target
    assert "WEATHERLINK_API_SECRET=secret" in target.read_text()
    assert target.stat().st_mode & 0o777 == 0o600


def test_save_user_config_rejects_line_breaks(monkeypatch, tmp_path):
    monkeypatch.setattr("weatherlink_dashboard.config.user_config_path", lambda: tmp_path / ".env")

    with pytest.raises(ValueError, match="line breaks"):
        save_user_config("key", "secret\nWEATHERLINK_UNITS=imperial")
