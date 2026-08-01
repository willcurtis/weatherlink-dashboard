"""Configuration loaded exclusively from environment variables or a .env file."""

from __future__ import annotations

import os
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
    def load(cls, env_file: str | Path = ".env") -> Settings:
        load_dotenv(Path(env_file), override=False)
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
