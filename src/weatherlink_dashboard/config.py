"""Configuration loaded exclusively from environment variables or a .env file."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_secret: str
    station_id: str | None = None
    refresh_seconds: int = 60
    history_hours: int = 24
    units: str = "metric"

    @classmethod
    def load(cls, env_file: str | Path | None = None) -> Settings:
        config_file = Path(env_file) if env_file is not None else find_config_file()
        if config_file is not None:
            load_dotenv(config_file, override=False)
        api_key = os.getenv("WEATHERLINK_API_KEY", "").strip()
        api_secret = os.getenv("WEATHERLINK_API_SECRET", "").strip()
        if not api_key or api_key == "your_api_key":
            raise ConfigurationError("WEATHERLINK_API_KEY is missing from .env")
        if not api_secret or api_secret == "your_api_secret":
            raise ConfigurationError("WEATHERLINK_API_SECRET is missing from .env")

        try:
            refresh = int(os.getenv("WEATHERLINK_REFRESH_SECONDS", "60"))
            history = int(os.getenv("WEATHERLINK_HISTORY_HOURS", "24"))
        except ValueError as exc:
            raise ConfigurationError("Refresh seconds and history hours must be integers") from exc
        if not 30 <= refresh <= 3600:
            raise ConfigurationError("WEATHERLINK_REFRESH_SECONDS must be between 30 and 3600")
        if not 1 <= history <= 24:
            raise ConfigurationError("WEATHERLINK_HISTORY_HOURS must be between 1 and 24")

        units = os.getenv("WEATHERLINK_UNITS", "metric").strip().lower()
        if units not in {"metric", "imperial"}:
            raise ConfigurationError("WEATHERLINK_UNITS must be metric or imperial")
        return cls(
            api_key=api_key,
            api_secret=api_secret,
            station_id=os.getenv("WEATHERLINK_STATION_ID", "").strip() or None,
            refresh_seconds=refresh,
            history_hours=history,
            units=units,
        )


def user_config_path() -> Path:
    """Return a stable, writable configuration path for the current platform."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
        return base / "WeatherLink Dashboard" / ".env"
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "WeatherLink Dashboard" / ".env"
    base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "weatherlink-dashboard" / ".env"


def find_config_file() -> Path | None:
    """Prefer an explicit/local file, then the platform application-data file."""
    explicit = os.getenv("WEATHERLINK_CONFIG_FILE", "").strip()
    candidates = [Path(explicit).expanduser()] if explicit else []
    candidates.extend((Path.cwd() / ".env", user_config_path()))
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def save_user_config(api_key: str, api_secret: str, station_id: str = "") -> Path:
    """Save credentials outside the application bundle with owner-only permissions."""
    values = (api_key.strip(), api_secret.strip(), station_id.strip())
    if any("\n" in value or "\r" in value for value in values):
        raise ValueError("Configuration values cannot contain line breaks.")
    api_key, api_secret, station_id = values
    path = user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"WEATHERLINK_API_KEY={api_key}\n"
        f"WEATHERLINK_API_SECRET={api_secret}\n"
        f"WEATHERLINK_STATION_ID={station_id}\n"
        "WEATHERLINK_REFRESH_SECONDS=60\n"
        "WEATHERLINK_HISTORY_HOURS=24\n"
        "WEATHERLINK_UNITS=metric\n"
    )
    temporary = path.with_suffix(".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)
    path.chmod(0o600)
    return path
