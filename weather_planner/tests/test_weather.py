import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

from backend.services.weather_service import (
    c_to_f,
    km_to_miles,
    aggregate_period,
    aggregate_forecast,
)


class TestConversions:
    def test_c_to_f_freezing(self):
        assert c_to_f(0) == 32.0

    def test_c_to_f_boiling(self):
        assert c_to_f(100) == 212.0

    def test_c_to_f_room_temp(self):
        assert c_to_f(20) == 68.0

    def test_c_to_f_negative(self):
        assert c_to_f(-10) == 14.0

    def test_km_to_miles(self):
        assert km_to_miles(100) == 62.1

    def test_km_to_miles_zero(self):
        assert km_to_miles(0) == 0.0


class TestAggregatePeriod:
    def _make_hourly_data(self, hours_data):
        times = []
        temps = []
        winds = []
        gusts = []
        rain_prob = []
        precip = []
        visibility = []
        cloud = []

        for hour, temp in hours_data:
            times.append(f"2026-09-24T{hour:02d}:00")
            temps.append(temp)
            winds.append(10.0)
            gusts.append(15.0)
            rain_prob.append(20.0)
            precip.append(0.5)
            visibility.append(20000.0)
            cloud.append(30.0)

        return {
            "time": times,
            "temperature_2m": temps,
            "apparent_temperature": temps,
            "precipitation_probability": rain_prob,
            "precipitation": precip,
            "rain": precip,
            "wind_speed_10m": winds,
            "wind_gusts_10m": gusts,
            "cloud_cover": cloud,
            "visibility": visibility,
            "weather_code": [0] * len(times),
        }

    def test_morning_aggregation(self):
        data = self._make_hourly_data([(6, 15), (8, 18), (10, 20), (11, 22)])
        result = aggregate_period(data, "2026-09-24", "Morning")
        assert result is not None
        assert result["temperature"] == c_to_f((15 + 18 + 20 + 22) / 4)

    def test_afternoon_aggregation(self):
        data = self._make_hourly_data([(12, 22), (14, 25), (16, 23), (17, 20)])
        result = aggregate_period(data, "2026-09-24", "Afternoon")
        assert result is not None
        assert result["temperature"] == c_to_f((22 + 25 + 23 + 20) / 4)

    def test_evening_aggregation(self):
        data = self._make_hourly_data([(18, 18), (20, 15), (22, 12)])
        result = aggregate_period(data, "2026-09-24", "Evening")
        assert result is not None
        assert result["temperature"] == c_to_f((18 + 15 + 12) / 3)

    def test_no_data_returns_none(self):
        data = self._make_hourly_data([])
        result = aggregate_period(data, "2026-09-24", "Morning")
        assert result is None

    def test_score_in_result(self):
        data = self._make_hourly_data([(8, 18), (10, 20)])
        result = aggregate_period(data, "2026-09-24", "Morning")
        assert "score" in result
        assert "scoreColor" in result
        assert isinstance(result["score"], int)

    def test_wind_in_mph(self):
        data = self._make_hourly_data([(8, 18)])
        result = aggregate_period(data, "2026-09-24", "Morning")
        assert result["wind"] == km_to_miles(10.0)

    def test_rain_amount_in_inches(self):
        data = self._make_hourly_data([(8, 18)])
        result = aggregate_period(data, "2026-09-24", "Morning")
        assert result["rainAmount"] == round(0.5 / 25.4, 2)


class TestAggregateForecast:
    def _make_raw_forecast(self):
        times = []
        temps = []
        for day in range(7):
            for hour in range(24):
                times.append(f"2026-09-{24 + day:02d}T{hour:02d}:00")
                temps.append(15.0 + (hour % 6))

        return {
            "hourly": {
                "time": times,
                "temperature_2m": temps,
                "apparent_temperature": temps,
                "precipitation_probability": [20.0] * len(times),
                "precipitation": [0.5] * len(times),
                "rain": [0.5] * len(times),
                "wind_speed_10m": [10.0] * len(times),
                "wind_gusts_10m": [15.0] * len(times),
                "cloud_cover": [30.0] * len(times),
                "visibility": [20000.0] * len(times),
                "weather_code": [0] * len(times),
            }
        }

    def test_creates_21_entries(self):
        raw = self._make_raw_forecast()
        results = aggregate_forecast(raw, "test-location")
        assert len(results) == 21

    def test_each_entry_has_required_fields(self):
        raw = self._make_raw_forecast()
        results = aggregate_forecast(raw, "test-location")
        for r in results:
            assert "locationId" in r
            assert "date" in r
            assert "period" in r
            assert "temperature" in r
            assert "wind" in r
            assert "rainProbability" in r
            assert "rainAmount" in r
            assert "score" in r
            assert "scoreColor" in r

    def test_location_id_set(self):
        raw = self._make_raw_forecast()
        results = aggregate_forecast(raw, "my-loc")
        for r in results:
            assert r["locationId"] == "my-loc"

    def test_empty_forecast(self):
        results = aggregate_forecast(None, "test")
        assert results == []

    def test_missing_hourly(self):
        results = aggregate_forecast({"time": []}, "test")
        assert results == []

    def test_periods_correct(self):
        raw = self._make_raw_forecast()
        results = aggregate_forecast(raw, "test")
        periods = set(r["period"] for r in results)
        assert periods == {"Morning", "Afternoon", "Evening"}
