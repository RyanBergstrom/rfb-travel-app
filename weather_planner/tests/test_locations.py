import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

from backend.services.location_service import (
    load_locations,
    get_enabled_locations,
    get_location_by_id,
    get_locations_by_region,
    get_regions,
)


class TestLoadLocations:
    def test_loads_locations(self):
        locations = load_locations()
        assert len(locations) > 0

    def test_returns_list(self):
        locations = load_locations()
        assert isinstance(locations, list)

    def test_locations_have_required_fields(self):
        locations = load_locations()
        for loc in locations:
            assert "id" in loc
            assert "name" in loc
            assert "region" in loc
            assert "latitude" in loc
            assert "longitude" in loc


class TestGetEnabledLocations:
    def test_filters_disabled(self):
        locations = get_enabled_locations()
        for loc in locations:
            assert loc.get("enabled", True) is True

    def test_count(self):
        locations = get_enabled_locations()
        assert len(locations) == 39


class TestGetLocationById:
    def test_finds_existing(self):
        loc = get_location_by_id("fairy-pools")
        assert loc is not None
        assert loc["name"] == "Fairy Pools"

    def test_returns_none_for_missing(self):
        loc = get_location_by_id("nonexistent")
        assert loc is None

    def test_all_ids_unique(self):
        locations = load_locations()
        ids = [loc["id"] for loc in locations]
        assert len(ids) == len(set(ids))


class TestGetLocationsByRegion:
    def test_finds_skye_locations(self):
        locations = get_locations_by_region("Isle of Skye")
        assert len(locations) == 7

    def test_returns_empty_for_unknown_region(self):
        locations = get_locations_by_region("Unknown Region")
        assert len(locations) == 0

    def test_all_skye_have_correct_region(self):
        locations = get_locations_by_region("Isle of Skye")
        for loc in locations:
            assert loc["region"] == "Isle of Skye"


class TestGetRegions:
    def test_returns_sorted_regions(self):
        regions = get_regions()
        assert regions == sorted(regions)

    def test_contains_expected_regions(self):
        regions = get_regions()
        assert "Isle of Skye" in regions
        assert "Glencoe" in regions
        assert "Cairngorms" in regions
        assert "Edinburgh" in regions or "Lothians" in regions

    def test_no_duplicates(self):
        regions = get_regions()
        assert len(regions) == len(set(regions))
