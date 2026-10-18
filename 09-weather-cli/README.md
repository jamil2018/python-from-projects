# 09 · Weather CLI

Fetch real weather data from the internet and display current conditions and a forecast. This is your first project using a **third-party package** and an **external API**.

**Builds on 08:** argparse, JSON, error handling.

## Concepts
- Virtual environments (`python -m venv`)
- Installing packages with `pip`, and `requirements.txt`
- HTTP basics: requests, responses, status codes, query parameters
- The `requests` library (or `httpx`)
- Parsing nested JSON
- Timeouts, retries, and handling network failures
- File-based caching with expiry
- Environment variables (`os.environ`)

## Setup
```powershell
cd 09-weather-cli
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install requests
pip freeze > requirements.txt
```
Use the free [Open-Meteo API](https://open-meteo.com/en/docs). It needs no API key.
- Geocoding (city name to coordinates): `https://geocoding-api.open-meteo.com/v1/search?name=Dhaka&count=1`
- Forecast: `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min`

## Project layout
```
09-weather-cli/
  weather/
    __init__.py
    api.py        # HTTP calls only, returning plain dataclasses
    cache.py      # read/write cache with expiry
    display.py    # formatting output
  main.py         # argparse entry point
  tests/
  requirements.txt
```

## Core requirements
```
python main.py Dhaka
python main.py "New York" --days 5 --units imperial
python main.py London --no-cache
```
1. Look up the city's coordinates, then fetch the current weather and a daily forecast.
2. Convert numeric weather codes into descriptions ("Clear sky", "Light rain", ...) with a dict.
3. Show the current temperature and conditions, plus a table of the next N days (1–7).
4. Cache responses in `.cache/` as JSON for 10 minutes, so repeat calls within that window make no network request.
5. Handle failures gracefully:
   - unknown city: "City not found"
   - no internet or a timeout: a clear message and exit code 2
   - a non-200 response: show the status code
6. Every request has a timeout (for example 5 seconds).
7. Default units can be set with the `WEATHER_UNITS` environment variable.

## Done when
- [ ] `.venv` is excluded from anything you share (add a `.gitignore`)
- [ ] `requirements.txt` lets someone else install everything with `pip install -r requirements.txt`
- [ ] Unplugging the network gives a friendly error, not a traceback
- [ ] Tests for `display.py` and `cache.py` run **without** network access, using fake data

## Stretch goals
- Compare multiple cities side by side: `python main.py Dhaka London Tokyo`.
- Retry failed requests with exponential backoff.
- In tests, mock the HTTP layer with `unittest.mock.patch` so `api.py` can be tested offline too.
- Add ASCII icons for each weather condition.

## Automated checks
Write your own tests in `tests/`. The provided checks in `spec_tests/` never touch the real network: they pass in a fake HTTP session or replace `requests.get`. Install what they need in your venv with `pip install requests pytest`. They assume the following.

`weather/api.py`:
- Dataclasses:
  - `Location(name, country, latitude, longitude)`
  - `DayForecast(date, temp_max, temp_min, weather_code)`, where `date` is a `datetime.date`
  - `Forecast(current_temperature, current_code, days)`, where `days` is a `list[DayForecast]`
- `geocode(city, session=None) -> Location` and `get_forecast(location, days=3, units="metric", session=None) -> Forecast`.
- `session` is anything with a `.get(url, params=..., timeout=...)` method. When it's `None`, call `requests.get` (look it up at call time with `requests.get(...)`, not `from requests import get`).
- The daily request asks for `temperature_2m_max`, `temperature_2m_min`, and `weather_code`. It sends `forecast_days=<days>`, and sends `temperature_unit=fahrenheit` when `units == "imperial"`. `days` outside 1–7 raises `ValueError`.
- Errors are converted into your own exceptions, all subclasses of `WeatherError`:
  - `CityNotFoundError` when there are no results
  - `NetworkError` for connection errors and timeouts
  - `HTTPStatusError` for a non-200 response, with the code in a `status_code` attribute

`weather/display.py`:
- `describe_code(code) -> str` returns `"Unknown"` for codes you don't know. It must know at least these: 0 Clear sky, 1 Mainly clear, 2 Partly cloudy, 3 Overcast, 45 Fog, 61 Light rain, 63 Rain, 65 Heavy rain, 71 Light snow, 95 Thunderstorm.
- `format_forecast(location, forecast, units="metric") -> str` includes the city name, temperatures with 1 decimal and `°C` or `°F` (for example `30.5°C`), each day's ISO date, and the condition descriptions.

`weather/cache.py`:
- `Cache(directory, ttl_seconds=600, clock=time.time)` has `get(key)` and `set(key, data)`. Keys can be any string. `get` returns `None` when the entry is missing, expired, or corrupted. The `clock` parameter lets tests fake the passage of time.

`main.py`:
- `main(argv=None) -> int` returns the exit code: `0` on success, `1` for an unknown city (and prints `City not found`), and `2` for a network failure.
- It caches under `.cache/` in the current directory, with a cache key that includes the city, days, and units.

```powershell
python -m pytest spec_tests -v
```

## Reflect
Why does `api.py` return dataclasses instead of the raw JSON dict? What would change elsewhere in your code if Open-Meteo renamed a field?
