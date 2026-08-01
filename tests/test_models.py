from weatherlink_dashboard.models import history_series, parse_current

PAYLOAD = {
    "generated_at": 1700000100,
    "sensors": [
        {
            "data_structure_type": 10,
            "data": [
                {
                    "ts": 1700000000,
                    "temp": 68,
                    "hum": 55,
                    "wind_speed_last": 10,
                    "wind_dir_last": 225,
                }
            ],
        },
        {"data_structure_type": 19, "data": [{"ts": 1700000010, "bar_sea_level": 29.92}]},
    ],
}


def test_parse_current_merges_sensor_records():
    conditions = parse_current(PAYLOAD)
    assert conditions.timestamp == 1700000010
    assert conditions.temperature(True) == 20
    assert round(conditions.wind(True), 3) == 16.093
    assert round(conditions.pressure(True), 1) == 1013.2
    assert conditions.wind_direction == 225


def test_history_series_converts_units_and_sorts():
    payload = {"sensors": [{"data": [{"ts": 2, "temp_last": 50}, {"ts": 1, "temp_last": 32}]}]}
    series = history_series(payload, metric=True)
    assert series["temperature"] == [(1, 0.0), (2, 10.0)]
