"""Small, testable client for the Davis WeatherLink v2 API."""

from __future__ import annotations

import time
from typing import Any

import requests


class WeatherLinkError(RuntimeError):
    """A friendly wrapper around WeatherLink and network errors."""


class WeatherLinkClient:
    BASE_URL = "https://api.weatherlink.com/v2"

    def __init__(self, api_key: str, api_secret: str, timeout: int = 20) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"X-Api-Secret": api_secret, "User-Agent": "weatherlink-dashboard/0.1"}
        )

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        params["api-key"] = self.api_key
        try:
            response = self.session.get(
                f"{self.BASE_URL}/{path.lstrip('/')}", params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            message = ""
            try:
                message = response.json().get("message", "")
            except (ValueError, AttributeError):
                message = response.text[:200]
            raise WeatherLinkError(
                f"WeatherLink returned HTTP {response.status_code}: {message or response.reason}"
            ) from exc
        except requests.RequestException as exc:
            raise WeatherLinkError(f"Could not reach WeatherLink: {exc}") from exc
        except ValueError as exc:
            raise WeatherLinkError("WeatherLink returned an invalid JSON response") from exc

    def stations(self) -> list[dict[str, Any]]:
        return self._get("stations").get("stations", [])

    def current(self, station_id: str | int) -> dict[str, Any]:
        return self._get(f"current/{station_id}")

    def historic(self, station_id: str | int, hours: int = 24) -> dict[str, Any]:
        end = int(time.time())
        start = end - min(max(hours, 1), 24) * 3600
        return self._get(
            f"historic/{station_id}", **{"start-timestamp": start, "end-timestamp": end}
        )
