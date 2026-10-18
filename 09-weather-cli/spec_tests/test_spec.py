"""Checks for project 09. Run from the project folder: python -m pytest spec_tests -v

These checks never use the real network.
"""

from datetime import date
from urllib.parse import parse_qsl, urlsplit

import pytest
import requests

import main as weather_main
from weather import api, cache, display

GEOCODE_JSON = {
    "results": [{"name": "Dhaka", "country": "Bangladesh", "latitude": 23.81, "longitude": 90.41}]
}
FORECAST_JSON = {
    "current": {"temperature_2m": 30.5, "weather_code": 2},
    "daily": {
        "time": ["2026-10-18", "2026-10-19", "2026-10-20"],
        "temperature_2m_max": [31.0, 32.5, 29.0],
        "temperature_2m_min": [24.0, 25.1, 23.4],
        "weather_code": [2, 61, 0],
    },
}


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = str(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)


class FakeSession:
    """Stands in for `requests`. Records every call and answers based on the URL."""

    def __init__(self, geocode=GEOCODE_JSON, forecast=FORECAST_JSON, status_code=200, error=None):
        self.geocode = geocode
        self.forecast = forecast
        self.status_code = status_code
        self.error = error
        self.calls = []

    def get(self, url, params=None, timeout=None, **kwargs):
        query = dict(parse_qsl(urlsplit(url).query))
        query.update({k: str(v) for k, v in (params or {}).items()})
        self.calls.append({"url": url, "params": query, "timeout": timeout})
        if self.error:
            raise self.error
        data = self.geocode if "geocoding" in url else self.forecast
        return FakeResponse(data, self.status_code)

    def forecast_calls(self):
        return [c for c in self.calls if "geocoding" not in c["url"]]


DHAKA = api.Location("Dhaka", "Bangladesh", 23.81, 90.41)


class TestGeocode:
    def test_returns_a_location(self):
        session = FakeSession()
        location = api.geocode("Dhaka", session=session)
        assert location == DHAKA
        call = session.calls[0]
        assert "geocoding-api.open-meteo.com" in call["url"]
        assert call["params"]["name"] == "Dhaka"

    def test_uses_a_timeout(self):
        session = FakeSession()
        api.geocode("Dhaka", session=session)
        assert session.calls[0]["timeout"], "Every request needs a timeout"

    @pytest.mark.parametrize("response", [{}, {"results": []}])
    def test_city_not_found(self, response):
        with pytest.raises(api.CityNotFoundError):
            api.geocode("Atlantis", session=FakeSession(geocode=response))


class TestGetForecast:
    def test_parses_current_and_daily(self):
        forecast = api.get_forecast(DHAKA, days=3, session=FakeSession())
        assert forecast.current_temperature == 30.5
        assert forecast.current_code == 2
        assert len(forecast.days) == 3
        first = forecast.days[0]
        assert first.date == date(2026, 10, 18)
        assert (first.temp_max, first.temp_min, first.weather_code) == (31.0, 24.0, 2)

    def test_request_parameters(self):
        session = FakeSession()
        api.get_forecast(DHAKA, days=3, session=session)
        call = session.calls[0]
        assert "api.open-meteo.com" in call["url"]
        assert float(call["params"]["latitude"]) == 23.81
        assert float(call["params"]["longitude"]) == 90.41
        assert call["params"]["forecast_days"] == "3"
        for field in ["temperature_2m_max", "temperature_2m_min", "weather_code"]:
            assert field in call["params"]["daily"]
        assert call["params"].get("temperature_unit", "celsius") == "celsius"
        assert call["timeout"]

    def test_imperial_units(self):
        session = FakeSession()
        api.get_forecast(DHAKA, units="imperial", session=session)
        assert session.calls[0]["params"]["temperature_unit"] == "fahrenheit"

    @pytest.mark.parametrize("days", [0, 8])
    def test_days_must_be_1_to_7(self, days):
        with pytest.raises(ValueError):
            api.get_forecast(DHAKA, days=days, session=FakeSession())


class TestErrors:
    @pytest.mark.parametrize("error", [requests.ConnectionError("down"), requests.Timeout("slow")])
    def test_network_errors(self, error):
        with pytest.raises(api.NetworkError):
            api.geocode("Dhaka", session=FakeSession(error=error))
        with pytest.raises(api.NetworkError):
            api.get_forecast(DHAKA, session=FakeSession(error=error))

    def test_bad_status_code(self):
        with pytest.raises(api.HTTPStatusError) as info:
            api.get_forecast(DHAKA, session=FakeSession(status_code=500))
        assert info.value.status_code == 500

    def test_errors_share_a_base_class(self):
        for exc in (api.CityNotFoundError, api.NetworkError, api.HTTPStatusError):
            assert issubclass(exc, api.WeatherError)


class TestDisplay:
    @pytest.mark.parametrize(
        "code, text",
        [(0, "Clear sky"), (2, "Partly cloudy"), (3, "Overcast"), (61, "Light rain"), (95, "Thunderstorm"), (12345, "Unknown")],
    )
    def test_describe_code(self, code, text):
        assert display.describe_code(code) == text

    def test_format_forecast_metric(self):
        forecast = api.get_forecast(DHAKA, session=FakeSession())
        text = display.format_forecast(DHAKA, forecast)
        for expected in ["Dhaka", "30.5°C", "Partly cloudy", "Light rain", "2026-10-18", "2026-10-20", "32.5°C"]:
            assert expected in text

    def test_format_forecast_imperial(self):
        forecast = api.get_forecast(DHAKA, session=FakeSession())
        text = display.format_forecast(DHAKA, forecast, units="imperial")
        assert "30.5°F" in text and "°C" not in text


class FakeClock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


class TestCache:
    @pytest.fixture
    def clock(self):
        return FakeClock()

    @pytest.fixture
    def store(self, tmp_path, clock):
        return cache.Cache(tmp_path / ".cache", ttl_seconds=600, clock=clock)

    def test_missing_key(self, store):
        assert store.get("nothing") is None

    def test_set_then_get(self, store):
        store.set("Dhaka|3|metric", FORECAST_JSON)
        assert store.get("Dhaka|3|metric") == FORECAST_JSON

    def test_keys_are_independent(self, store):
        store.set("a", {"x": 1})
        store.set("b", {"x": 2})
        assert store.get("a") == {"x": 1}
        assert store.get("b") == {"x": 2}

    def test_awkward_keys(self, store):
        key = 'New York?units=imperial&days=5 / "quoted"'
        store.set(key, [1, 2, 3])
        assert store.get(key) == [1, 2, 3]

    def test_entries_expire(self, store, clock):
        store.set("k", {"x": 1})
        clock.now += 599
        assert store.get("k") == {"x": 1}
        clock.now += 2
        assert store.get("k") is None

    def test_survives_a_new_cache_object(self, tmp_path, clock):
        cache.Cache(tmp_path / ".cache", clock=clock).set("k", {"x": 1})
        assert cache.Cache(tmp_path / ".cache", clock=clock).get("k") == {"x": 1}

    def test_corrupted_file_counts_as_missing(self, store, tmp_path):
        store.set("k", {"x": 1})
        for path in (tmp_path / ".cache").rglob("*"):
            if path.is_file():
                path.write_text("{ not json", encoding="utf-8")
        assert store.get("k") is None


class TestMain:
    @pytest.fixture
    def fake(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("WEATHER_UNITS", raising=False)
        session = FakeSession()
        monkeypatch.setattr(requests, "get", session.get)
        return session

    def test_success(self, fake, capsys):
        assert weather_main.main(["Dhaka"]) == 0
        assert "Dhaka" in capsys.readouterr().out

    def test_second_call_uses_the_cache(self, fake):
        weather_main.main(["Dhaka"])
        calls = len(fake.calls)
        assert calls > 0
        weather_main.main(["Dhaka"])
        assert len(fake.calls) == calls, "The second call should be answered from .cache/"

    def test_no_cache_flag(self, fake):
        weather_main.main(["Dhaka"])
        calls = len(fake.calls)
        weather_main.main(["Dhaka", "--no-cache"])
        assert len(fake.calls) > calls

    def test_days_option(self, fake):
        weather_main.main(["Dhaka", "--days", "5", "--no-cache"])
        assert fake.forecast_calls()[-1]["params"]["forecast_days"] == "5"

    def test_units_from_environment(self, fake, monkeypatch):
        monkeypatch.setenv("WEATHER_UNITS", "imperial")
        weather_main.main(["Dhaka", "--no-cache"])
        assert fake.forecast_calls()[-1]["params"]["temperature_unit"] == "fahrenheit"

    def test_units_flag_beats_environment(self, fake, monkeypatch):
        monkeypatch.setenv("WEATHER_UNITS", "imperial")
        weather_main.main(["Dhaka", "--units", "metric", "--no-cache"])
        params = fake.forecast_calls()[-1]["params"]
        assert params.get("temperature_unit", "celsius") == "celsius"

    def test_unknown_city(self, fake, capsys):
        fake.geocode = {}
        assert weather_main.main(["Atlantis", "--no-cache"]) == 1
        captured = capsys.readouterr()
        assert "city not found" in (captured.out + captured.err).lower()

    def test_network_failure(self, fake, capsys):
        fake.error = requests.ConnectionError("no internet")
        assert weather_main.main(["Dhaka", "--no-cache"]) == 2
        assert "Traceback" not in capsys.readouterr().err
