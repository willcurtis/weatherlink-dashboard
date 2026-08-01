"""Normalize varying WeatherLink sensor records into dashboard-friendly values."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _first(record: dict[str, Any], names: Iterable[str]) -> float | None:
    for name in names:
        value = record.get(name)
        if isinstance(value, (int, float)):
            return float(value)
    return None


@dataclass
class Conditions:
    timestamp: int | None = None
    temperature_f: float | None = None
    feels_like_f: float | None = None
    humidity: float | None = None
    pressure_inhg: float | None = None
    wind_mph: float | None = None
    wind_gust_mph: float | None = None
    wind_direction: float | None = None
    rain_rate_in_h: float | None = None
    rain_day_in: float | None = None
    uv_index: float | None = None
    solar_wm2: float | None = None

    @property
    def observed_at(self) -> str:
        if not self.timestamp:
            return "Unknown"
        return datetime.fromtimestamp(self.timestamp).astimezone().strftime("%d %b %Y, %H:%M:%S")

    def temperature(self, metric: bool) -> float | None:
        return (
            None
            if self.temperature_f is None
            else (self.temperature_f - 32) * 5 / 9
            if metric
            else self.temperature_f
        )

    def feels_like(self, metric: bool) -> float | None:
        return (
            None
            if self.feels_like_f is None
            else (self.feels_like_f - 32) * 5 / 9
            if metric
            else self.feels_like_f
        )

    def wind(self, metric: bool) -> float | None:
        return (
            None if self.wind_mph is None else self.wind_mph * 1.609344 if metric else self.wind_mph
        )

    def gust(self, metric: bool) -> float | None:
        return (
            None
            if self.wind_gust_mph is None
            else self.wind_gust_mph * 1.609344
            if metric
            else self.wind_gust_mph
        )

    def pressure(self, metric: bool) -> float | None:
        return (
            None
            if self.pressure_inhg is None
            else self.pressure_inhg * 33.8638866667
            if metric
            else self.pressure_inhg
        )

    def rain_rate(self, metric: bool) -> float | None:
        return (
            None
            if self.rain_rate_in_h is None
            else self.rain_rate_in_h * 25.4
            if metric
            else self.rain_rate_in_h
        )

    def rain_day(self, metric: bool) -> float | None:
        return (
            None
            if self.rain_day_in is None
            else self.rain_day_in * 25.4
            if metric
            else self.rain_day_in
        )


def flatten_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for sensor in payload.get("sensors", []):
        for record in sensor.get("data", []):
            if isinstance(record, dict):
                records.append(record)
    return records


def parse_current(payload: dict[str, Any]) -> Conditions:
    records = flatten_records(payload)
    merged: dict[str, Any] = {}
    # Later records supplement earlier ones; timestamps are handled by max below.
    for record in records:
        for key, value in record.items():
            if value is not None:
                merged[key] = value
    timestamps = [r.get("ts") for r in records if isinstance(r.get("ts"), (int, float))]
    return Conditions(
        timestamp=int(max(timestamps)) if timestamps else payload.get("generated_at"),
        temperature_f=_first(merged, ("temp", "temp_out", "temp_last")),
        feels_like_f=_first(merged, ("heat_index", "wind_chill", "thw_index", "temp")),
        humidity=_first(merged, ("hum", "hum_out", "hum_last")),
        pressure_inhg=_first(merged, ("bar", "bar_sea_level", "pressure_last")),
        wind_mph=_first(merged, ("wind_speed_last", "wind_speed_avg_last_2_min", "wind_speed_avg")),
        wind_gust_mph=_first(
            merged, ("wind_speed_hi_last_10_min", "wind_speed_hi_last_2_min", "wind_speed_hi")
        ),
        wind_direction=_first(
            merged, ("wind_dir_last", "wind_dir_scalar_avg_last_10_min", "wind_dir_of_hi")
        ),
        rain_rate_in_h=_first(merged, ("rain_rate_last", "rain_rate_hi")),
        rain_day_in=_first(merged, ("rainfall_daily", "rain_day", "rainfall_last_24_hr")),
        uv_index=_first(merged, ("uv_index", "uv_index_avg", "uv_index_last")),
        solar_wm2=_first(merged, ("solar_rad", "solar_rad_avg", "solar_rad_last")),
    )


def history_series(payload: dict[str, Any], metric: bool) -> dict[str, list[tuple[int, float]]]:
    fields = {
        "temperature": ("temp_last", "temp_out", "temp"),
        "humidity": ("hum_last", "hum_out", "hum"),
        "pressure": ("bar", "bar_sea_level", "pressure_last"),
        "wind": ("wind_speed_avg", "wind_speed_last"),
    }
    series: dict[str, dict[int, float]] = {name: {} for name in fields}
    for record in flatten_records(payload):
        ts = record.get("ts")
        if not isinstance(ts, (int, float)):
            continue
        for name, candidates in fields.items():
            value = _first(record, candidates)
            if value is None:
                continue
            if metric and name == "temperature":
                value = (value - 32) * 5 / 9
            elif metric and name == "pressure":
                value *= 33.8638866667
            elif metric and name == "wind":
                value *= 1.609344
            series[name][int(ts)] = value
    return {name: sorted(points.items()) for name, points in series.items()}
