"""Turn current observations into practical activity guidance."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from .models import Conditions


class WindowStatus(str, Enum):
    """Traffic-light states shown by the Weather Window panel."""

    GOOD = "good"
    CAUTION = "caution"
    AVOID = "avoid"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ActivityAssessment:
    """A single activity rating and its most important reason."""

    activity: str
    status: WindowStatus
    reason: str


@dataclass(frozen=True)
class _Issue:
    status: WindowStatus
    reason: str


ACTIVITY_NAMES = (
    "Walking",
    "Cycling",
    "Gardening",
    "Outdoor dining",
    "Drying laundry",
)

_SEVERITY = {
    WindowStatus.UNKNOWN: -1,
    WindowStatus.GOOD: 0,
    WindowStatus.CAUTION: 1,
    WindowStatus.AVOID: 2,
}


def _speed(mph: float, metric: bool) -> str:
    value = mph * 1.609344 if metric else mph
    unit = "km/h" if metric else "mph"
    return f"{value:.0f} {unit}"


def _temperature(fahrenheit: float, metric: bool) -> str:
    value = (fahrenheit - 32) * 5 / 9 if metric else fahrenheit
    unit = "°C" if metric else "°F"
    return f"{value:.0f} {unit}"


def _rain_rate(inches_per_hour: float, metric: bool) -> str:
    value = inches_per_hour * 25.4 if metric else inches_per_hour
    unit = "mm/h" if metric else "in/h"
    decimals = 1 if metric else 2
    return f"{value:.{decimals}f} {unit}"


def _result(activity: str, available: int, issues: list[_Issue]) -> ActivityAssessment:
    if not available:
        return ActivityAssessment(activity, WindowStatus.UNKNOWN, "Readings unavailable")
    if issues:
        issue = max(issues, key=lambda candidate: _SEVERITY[candidate.status])
        return ActivityAssessment(activity, issue.status, issue.reason)
    return ActivityAssessment(activity, WindowStatus.GOOD, "No concerns detected")


def _rain_issue(
    rain_rate: float | None,
    metric: bool,
    caution_at: float,
    avoid_at: float,
) -> _Issue | None:
    if rain_rate is None or rain_rate < caution_at:
        return None
    label = "Heavy rain" if rain_rate >= avoid_at else "Rain falling"
    status = WindowStatus.AVOID if rain_rate >= avoid_at else WindowStatus.CAUTION
    return _Issue(status, f"{label} • {_rain_rate(rain_rate, metric)}")


def _wind_issue(
    wind_mph: float | None,
    metric: bool,
    caution_at: float,
    avoid_at: float,
) -> _Issue | None:
    if wind_mph is None or wind_mph < caution_at:
        return None
    status = WindowStatus.AVOID if wind_mph >= avoid_at else WindowStatus.CAUTION
    return _Issue(status, f"Strong gusts • {_speed(wind_mph, metric)}")


def _effective_wind(conditions: Conditions) -> float | None:
    readings = [
        reading
        for reading in (conditions.wind_mph, conditions.wind_gust_mph)
        if reading is not None
    ]
    return max(readings) if readings else None


def _temperature_issue(
    temperature_f: float | None,
    metric: bool,
    caution_range: tuple[float, float],
    avoid_range: tuple[float, float],
) -> _Issue | None:
    if temperature_f is None:
        return None
    if temperature_f <= avoid_range[0] or temperature_f >= avoid_range[1]:
        return _Issue(WindowStatus.AVOID, f"Feels like • {_temperature(temperature_f, metric)}")
    if temperature_f <= caution_range[0] or temperature_f >= caution_range[1]:
        return _Issue(WindowStatus.CAUTION, f"Feels like • {_temperature(temperature_f, metric)}")
    return None


def _uv_issue(uv_index: float | None, caution_at: float, avoid_at: float) -> _Issue | None:
    if uv_index is None or uv_index < caution_at:
        return None
    status = WindowStatus.AVOID if uv_index >= avoid_at else WindowStatus.CAUTION
    label = "Extreme UV" if status is WindowStatus.AVOID else "High UV"
    return _Issue(status, f"{label} • index {uv_index:.1f}")


def _assess_outdoor_activity(
    activity: str,
    conditions: Conditions,
    metric: bool,
    *,
    rain_thresholds: tuple[float, float],
    wind_thresholds: tuple[float, float],
    temperature_ranges: tuple[tuple[float, float], tuple[float, float]],
    uv_thresholds: tuple[float, float] | None,
) -> ActivityAssessment:
    rain = conditions.rain_rate_in_h
    wind = _effective_wind(conditions)
    temperature = (
        conditions.feels_like_f if conditions.feels_like_f is not None else conditions.temperature_f
    )
    values = (rain, wind, temperature, conditions.uv_index if uv_thresholds else None)
    available = sum(value is not None for value in values)
    issues = [
        _rain_issue(rain, metric, *rain_thresholds),
        _wind_issue(wind, metric, *wind_thresholds),
        _temperature_issue(temperature, metric, *temperature_ranges),
    ]
    if uv_thresholds:
        issues.append(_uv_issue(conditions.uv_index, *uv_thresholds))
    return _result(activity, available, [issue for issue in issues if issue is not None])


def _assess_laundry(conditions: Conditions, metric: bool) -> ActivityAssessment:
    rain = conditions.rain_rate_in_h
    wind = _effective_wind(conditions)
    available = sum(
        value is not None for value in (rain, wind, conditions.humidity, conditions.solar_wm2)
    )
    issues: list[_Issue] = []
    rain_issue = _rain_issue(rain, metric, 0.001, 0.02)
    wind_issue = _wind_issue(wind, metric, 25, 35)
    if rain_issue:
        issues.append(rain_issue)
    if wind_issue:
        issues.append(wind_issue)
    if conditions.humidity is not None:
        if conditions.humidity >= 95:
            issues.append(_Issue(WindowStatus.AVOID, f"Humidity • {conditions.humidity:.0f}%"))
        elif conditions.humidity >= 75:
            issues.append(_Issue(WindowStatus.CAUTION, f"Humidity • {conditions.humidity:.0f}%"))
    if conditions.solar_wm2 is not None and conditions.solar_wm2 < 75:
        issues.append(_Issue(WindowStatus.CAUTION, "Very little solar energy"))
    return _result("Drying laundry", available, issues)


def evaluate_weather_window(
    conditions: Conditions,
    metric: bool,
    *,
    now: int | None = None,
) -> tuple[ActivityAssessment, ...]:
    """Rate common outdoor activities using current, not forecast, conditions."""

    current_time = int(time.time()) if now is None else now
    if conditions.timestamp is not None and current_time - conditions.timestamp > 30 * 60:
        minutes = max(0, (current_time - conditions.timestamp) // 60)
        reason = f"Observations are {minutes} min old"
        return tuple(
            ActivityAssessment(activity, WindowStatus.UNKNOWN, reason)
            for activity in ACTIVITY_NAMES
        )

    assessments = (
        _assess_outdoor_activity(
            "Walking",
            conditions,
            metric,
            rain_thresholds=(0.001, 0.20),
            wind_thresholds=(25, 35),
            temperature_ranges=((35, 90), (20, 100)),
            uv_thresholds=(8, 11),
        ),
        _assess_outdoor_activity(
            "Cycling",
            conditions,
            metric,
            rain_thresholds=(0.001, 0.10),
            wind_thresholds=(20, 30),
            temperature_ranges=((40, 90), (25, 100)),
            uv_thresholds=(8, 11),
        ),
        _assess_outdoor_activity(
            "Gardening",
            conditions,
            metric,
            rain_thresholds=(0.05, 0.25),
            wind_thresholds=(22, 35),
            temperature_ranges=((40, 88), (28, 100)),
            uv_thresholds=(6, 11),
        ),
        _assess_outdoor_activity(
            "Outdoor dining",
            conditions,
            metric,
            rain_thresholds=(0.001, 0.10),
            wind_thresholds=(20, 30),
            temperature_ranges=((50, 90), (35, 100)),
            uv_thresholds=(8, 11),
        ),
        _assess_laundry(conditions, metric),
    )
    return assessments
