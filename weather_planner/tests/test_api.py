import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'weather_planner'))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestLocationsEndpoint:
    def test_returns_locations(self):
        response = client.get("/api/locations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_location_has_required_fields(self):
        response = client.get("/api/locations")
        data = response.json()
        for loc in data:
            assert "id" in loc
            assert "name" in loc
            assert "region" in loc
            assert "latitude" in loc
            assert "longitude" in loc

    def test_only_enabled_locations(self):
        response = client.get("/api/locations")
        data = response.json()
        for loc in data:
            assert loc.get("enabled", True) is True

    def test_returns_39_locations(self):
        response = client.get("/api/locations")
        data = response.json()
        assert len(data) == 39


class TestRegionsEndpoint:
    def test_returns_regions(self):
        response = client.get("/api/regions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_regions_are_sorted(self):
        response = client.get("/api/regions")
        data = response.json()
        assert data == sorted(data)


class TestRefreshEndpoint:
    def test_refresh_returns_status(self):
        response = client.post("/api/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refreshed"
        assert "locationsRefreshed" in data
        assert "totalLocations" in data
