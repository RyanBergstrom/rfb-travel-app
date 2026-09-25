import json
import os
from typing import List, Optional

LOCATIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "locations.json")


def load_locations() -> List[dict]:
    with open(LOCATIONS_PATH, "r") as f:
        return json.load(f)


def get_enabled_locations() -> List[dict]:
    return [loc for loc in load_locations() if loc.get("enabled", True)]


def get_location_by_id(location_id: str) -> Optional[dict]:
    for loc in load_locations():
        if loc["id"] == location_id:
            return loc
    return None


def get_locations_by_region(region: str) -> List[dict]:
    return [loc for loc in get_enabled_locations() if loc["region"] == region]


def get_regions() -> List[str]:
    return sorted(set(loc["region"] for loc in get_enabled_locations()))
