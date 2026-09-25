import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

from backend.services.scoring_service import calculate_hiking_score, score_color, score_label


class TestCalculateHikingScore:
    def test_perfect_conditions(self):
        score = calculate_hiking_score(
            temperature_f=60,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=30000,
        )
        assert score == 100

    def test_all_penalties(self):
        score = calculate_hiking_score(
            temperature_f=100,
            wind_speed_mph=50,
            rain_probability=100,
            cloud_cover=100,
            visibility_m=100,
        )
        assert score == 0

    def test_rain_probability_penalty(self):
        # Use no visibility bonus and no temp bonus as control
        score_no_rain = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        score_50_rain = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=0,
            rain_probability=50,
            cloud_cover=0,
            visibility_m=10000,
        )
        assert score_no_rain - score_50_rain == 20

    def test_wind_penalty(self):
        score_no_wind = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        score_10_wind = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=10,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        assert score_no_wind - score_10_wind == 15

    def test_cloud_cover_penalty(self):
        score_clear = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        score_cloudy = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=100,
            visibility_m=10000,
        )
        assert score_clear - score_cloudy == 15

    def test_visibility_bonus_15km(self):
        # Use penalties to avoid clamping at 100
        score_low = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        score_high = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=20000,
        )
        assert score_high - score_low == 10

    def test_visibility_bonus_25km(self):
        score_15 = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=20000,
        )
        score_25 = calculate_hiking_score(
            temperature_f=80,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=30000,
        )
        assert score_25 - score_15 == 10

    def test_temperature_bonus(self):
        score_cold = calculate_hiking_score(
            temperature_f=40,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        score_ideal = calculate_hiking_score(
            temperature_f=60,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        assert score_ideal - score_cold == 10

    def test_temperature_bonus_boundary_low(self):
        # With some penalties to avoid clamping
        score_no_bonus = calculate_hiking_score(
            temperature_f=49,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        score_with_bonus = calculate_hiking_score(
            temperature_f=50,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        assert score_with_bonus - score_no_bonus == 10

    def test_temperature_bonus_boundary_high(self):
        score_no_bonus = calculate_hiking_score(
            temperature_f=69,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        score_with_bonus = calculate_hiking_score(
            temperature_f=68,
            wind_speed_mph=20,
            rain_probability=50,
            cloud_cover=50,
            visibility_m=10000,
        )
        assert score_with_bonus - score_no_bonus == 10

    def test_temperature_no_bonus_below_range(self):
        score = calculate_hiking_score(
            temperature_f=49,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        assert score == 100

    def test_temperature_no_bonus_above_range(self):
        score = calculate_hiking_score(
            temperature_f=69,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=10000,
        )
        assert score == 100

    def test_clamp_minimum(self):
        score = calculate_hiking_score(
            temperature_f=100,
            wind_speed_mph=50,
            rain_probability=100,
            cloud_cover=100,
            visibility_m=100,
        )
        assert score == 0

    def test_clamp_maximum(self):
        score = calculate_hiking_score(
            temperature_f=60,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=30000,
        )
        assert score == 100

    def test_returns_integer(self):
        score = calculate_hiking_score(
            temperature_f=55,
            wind_speed_mph=7.3,
            rain_probability=23.7,
            cloud_cover=45.2,
            visibility_m=18500,
        )
        assert isinstance(score, int)

    def test_combined_score(self):
        score = calculate_hiking_score(
            temperature_f=58,
            wind_speed_mph=12,
            rain_probability=20,
            cloud_cover=25,
            visibility_m=20000,
        )
        # 100 - (20*0.40) - (12*1.50) - (25*0.15) + 10(vis>15km) + 10(temp in range)
        # = 100 - 8 - 18 - 3.75 + 10 + 10 = 90.25
        expected = 100 - (20 * 0.40) - (12 * 1.50) - (25 * 0.15) + 10 + 10
        assert score == int(round(expected))

    def test_clamps_after_bonuses(self):
        score = calculate_hiking_score(
            temperature_f=60,
            wind_speed_mph=0,
            rain_probability=0,
            cloud_cover=0,
            visibility_m=30000,
        )
        # Would be 100 + 20(vis) + 10(temp) = 130, clamped to 100
        assert score == 100


class TestScoreColor:
    def test_green(self):
        assert score_color(75) == "green"
        assert score_color(100) == "green"

    def test_yellow(self):
        assert score_color(50) == "yellow"
        assert score_color(74) == "yellow"

    def test_red(self):
        assert score_color(0) == "red"
        assert score_color(49) == "red"

    def test_boundary_75(self):
        assert score_color(75) == "green"

    def test_boundary_50(self):
        assert score_color(50) == "yellow"

    def test_boundary_49(self):
        assert score_color(49) == "red"


class TestScoreLabel:
    def test_excellent(self):
        assert score_label(85) == "Excellent"

    def test_acceptable(self):
        assert score_label(60) == "Acceptable"

    def test_poor(self):
        assert score_label(30) == "Poor"
