from weatherlink_dashboard.models import Conditions
from weatherlink_dashboard.weather_window import (
    WindowStatus,
    evaluate_weather_window,
)

NOW = 2_000_000_000


def assessments_for(conditions: Conditions, *, metric: bool = True):
    return {
        result.activity: result
        for result in evaluate_weather_window(conditions, metric=metric, now=NOW)
    }


def test_comfortable_conditions_are_good_for_every_activity():
    results = assessments_for(
        Conditions(
            timestamp=NOW,
            temperature_f=68,
            feels_like_f=68,
            humidity=55,
            wind_mph=5,
            wind_gust_mph=8,
            rain_rate_in_h=0,
            uv_index=3,
            solar_wm2=300,
        )
    )

    assert {result.status for result in results.values()} == {WindowStatus.GOOD}


def test_heavy_rain_takes_priority_and_uses_metric_units():
    results = assessments_for(
        Conditions(
            timestamp=NOW,
            temperature_f=68,
            wind_mph=5,
            rain_rate_in_h=0.25,
        )
    )

    assert results["Walking"].status is WindowStatus.AVOID
    assert results["Walking"].reason == "Heavy rain • 6.3 mm/h"
    assert results["Gardening"].status is WindowStatus.AVOID
    assert results["Drying laundry"].status is WindowStatus.AVOID


def test_cycling_is_more_sensitive_to_gusts_than_walking():
    results = assessments_for(
        Conditions(timestamp=NOW, temperature_f=68, wind_gust_mph=22, rain_rate_in_h=0)
    )

    assert results["Walking"].status is WindowStatus.GOOD
    assert results["Cycling"].status is WindowStatus.CAUTION
    assert results["Cycling"].reason == "Strong gusts • 35 km/h"


def test_missing_readings_are_not_reported_as_good():
    results = assessments_for(Conditions(timestamp=NOW))

    assert {result.status for result in results.values()} == {WindowStatus.UNKNOWN}
    assert {result.reason for result in results.values()} == {"Readings unavailable"}


def test_stale_observations_suspend_all_guidance():
    results = assessments_for(
        Conditions(timestamp=NOW - 31 * 60, temperature_f=68, rain_rate_in_h=0)
    )

    assert {result.status for result in results.values()} == {WindowStatus.UNKNOWN}
    assert {result.reason for result in results.values()} == {"Observations are 31 min old"}


def test_very_high_uv_warns_for_gardening_before_other_activities():
    results = assessments_for(
        Conditions(timestamp=NOW, temperature_f=70, wind_mph=4, rain_rate_in_h=0, uv_index=7)
    )

    assert results["Gardening"].status is WindowStatus.CAUTION
    assert results["Gardening"].reason == "High UV • index 7.0"
    assert results["Walking"].status is WindowStatus.GOOD
