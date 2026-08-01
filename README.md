# WeatherLink Dashboard

A modern, cross-platform Python desktop dashboard for Davis Instruments weather stations connected to WeatherLink. It presents live observations with gauges, a wind-direction dial, metric cards, and selectable history graphs.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB) ![License](https://img.shields.io/badge/license-MIT-22C55E)

## Features

- Live temperature, humidity, rainfall, solar radiation, and UV readings
- Wind-speed and barometric-pressure gauges plus a compass dial
- Selectable 24-hour charts for temperature, humidity, pressure, and wind
- Metric and imperial display modes
- Automatic first-station discovery or an explicit station ID
- Background network requests so the interface remains responsive
- Friendly handling when a WeatherLink plan does not include historical data
- Credentials loaded only from a local `.env` file, which Git ignores

## Setup

1. Install Python 3.10 or newer.
2. From [your WeatherLink account page](https://www.weatherlink.com/account), generate a v2 API key and secret.
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate       # macOS/Linux
   # .venv\Scripts\activate        # Windows PowerShell
   ```

4. Install the app:

   ```bash
   pip install -e .
   ```

5. Copy the configuration template and edit the new file:

   ```bash
   cp .env.example .env
   ```

   Set `WEATHERLINK_API_KEY` and `WEATHERLINK_API_SECRET`. Leave `WEATHERLINK_STATION_ID` blank to use the first station available to the account. The station ID is not the device ID; it may be an integer or UUID.

6. Launch:

   ```bash
   weatherlink-dashboard
   # or: python -m weatherlink_dashboard.app
   ```

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `WEATHERLINK_API_KEY` | Yes | — | WeatherLink v2 API key |
| `WEATHERLINK_API_SECRET` | Yes | — | WeatherLink v2 secret, sent only as a request header |
| `WEATHERLINK_STATION_ID` | No | First station | Integer station ID or UUID |
| `WEATHERLINK_REFRESH_SECONDS` | No | `60` | Refresh cadence; minimum 30 seconds |
| `WEATHERLINK_HISTORY_HOURS` | No | `24` | History window from 1–24 hours |
| `WEATHERLINK_UNITS` | No | `metric` | `metric` or `imperial` |

The `.env` file is excluded by `.gitignore`. Do not commit it, paste credentials into source code, or pass the API secret in a URL. If a secret is exposed, regenerate it from WeatherLink immediately.

## WeatherLink API notes

This project uses the official WeatherLink v2 endpoints `/stations`, `/current/{station-id}`, and `/historic/{station-id}`. API access and observation freshness depend on station ownership and the WeatherLink subscription. Historical access may not be available on Basic plans. The API currently limits historical request windows to 24 hours and applies account-level request limits, so the dashboard defaults to one refresh per minute.

Official references: [authentication](https://weatherlink.github.io/v2-api/authentication), [API reference](https://weatherlink.github.io/v2-api/api-reference), [data permissions](https://weatherlink.github.io/v2-api/data-permissions), and [rate limits](https://weatherlink.github.io/v2-api/rate-limits).

## Development

```bash
pip install -e '.[dev]'
pytest
ruff check .
```

Sensor models expose slightly different WeatherLink field names. The normalizer deliberately supports common WeatherLink Live, Console, EnviroMonitor, WeatherLinkIP, and Vantage Connect variants. Contributions with sanitized sample payloads are welcome.

## License

MIT. See [LICENSE](LICENSE).
