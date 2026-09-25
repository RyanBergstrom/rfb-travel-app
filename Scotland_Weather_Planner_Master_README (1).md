# Scotland Weather Planner
## Comprehensive Implementation Specification

---

# Overview

The Scotland Weather Planner is a weather intelligence module intended to integrate into the RFB Travel App.

Primary purpose:

> Which location in Scotland has the best weather for hiking, photography, sightseeing, scenic driving, or exploration over the next 7 days?

The planner combines:

- Interactive map
- Open-Meteo weather forecasts
- Hiking suitability scoring
- Scotland-wide location coverage
- Mobile responsive design
- Forecast comparison grid
- Fast daily planning

---

# Integration Requirements

This application will eventually be integrated into:

```text
RFB Travel App
```

Navigation:

```text
Home
Trips
Weather Planner
```

Suggested Route:

```text
/weather
```

Authentication:

```text
Out of Scope
```

This module should be fully standalone but easily embedded in another application.

---

# Technology Stack

## Backend

```text
Python
FastAPI
```

Reasons:

- Lightweight
- Fast
- Excellent API framework
- Auto Swagger documentation

---

## Frontend

```text
React
```

Recommended Libraries:

```text
React Query
Axios
Leaflet
```

---

## Map

```text
Leaflet
```

Map Provider:

```text
OpenStreetMap
```

Capabilities:

```text
Zoom
Pan
Touch support
Responsive
Marker clustering ready
```

---

## Weather Provider

```text
Open-Meteo
```

Benefits:

```text
No API key required
Hourly forecasts
Forecast and historical support
Free
Reliable
```

---

# High Level UI

```text
------------------------------------------------------------
|                                                          |
|                    Scotland Map                          |
|                                                          |
------------------------------------------------------------

------------------------------------------------------------
| Search | Filters | Weather Legend | Refresh             |
------------------------------------------------------------

------------------------------------------------------------
|                                                          |
|                    Forecast Grid                         |
|                                                          |
------------------------------------------------------------
```

Desktop:

```text
40% Map
60% Grid
```

Mobile:

```text
35vh Map
65vh Grid
```

---

# Project Structure

```text
weather-planner/

├── backend/
│
│   ├── app.py
│
│   ├── api/
│   │   ├── forecast.py
│   │   ├── locations.py
│   │   └── refresh.py
│
│   ├── services/
│   │   ├── weather_service.py
│   │   ├── location_service.py
│   │   ├── scoring_service.py
│   │   └── cache_service.py
│
│   ├── models/
│
│   ├── cache/
│
│   └── config/
│       └── locations.json
│
├── frontend/
│
│   ├── pages/
│   │   └── WeatherPlanner.jsx
│
│   ├── components/
│   │   ├── ScotlandMap.jsx
│   │   ├── ForecastGrid.jsx
│   │   ├── SearchBar.jsx
│   │   ├── WeatherLegend.jsx
│   │   ├── LocationFilter.jsx
│   │   └── Toolbar.jsx
│
│   ├── hooks/
│   │   └── useForecasts.js
│
│   ├── services/
│
│   └── styles/
│
└── docs/
```

---

# Location Configuration

All locations come from:

```text
backend/config/locations.json
```

No hardcoded locations.

Example:

```json
{
  "id": "fairy-pools",
  "name": "Fairy Pools",
  "description": "Waterfalls and pools",
  "region": "Isle of Skye",
  "latitude": 57.252,
  "longitude": -6.272,
  "priority": 1,
  "enabled": true,
  "tags": [
    "hike",
    "waterfall"
  ]
}
```

Future regions should automatically work without code changes:

```text
Scotland
Ireland
Iceland
Norway
Colorado
Utah
Maine
```

---

# Open-Meteo Data

Retrieve hourly data for:

```text
temperature_2m
apparent_temperature
precipitation_probability
precipitation
rain
wind_speed_10m
wind_gusts_10m
cloud_cover
visibility
weather_code
```

Store raw hourly values.

Never store only aggregated values.

---

# Refresh Strategy

Refresh Weather:

```text
Application Startup

Every 6 Hours

Manual Refresh Button
```

Caching:

```text
Memory Cache
```

Expiration:

```text
6 Hours
```

---

# Time Period Aggregation

Hourly Open-Meteo data should be transformed into:

## Morning

```text
06:00 - 11:59
```

## Afternoon

```text
12:00 - 17:59
```

## Evening

```text
18:00 - 23:59
```

Calculate:

```text
Average Temperature

Average Wind Speed

Average Wind Gust

Average Rain Probability

Average Precipitation

Average Cloud Cover

Average Visibility
```

---

# Interactive Map Requirements

## Initial View

Map should load centered on Scotland.

Visible Regions:

```text
Glasgow
Loch Lomond
Glencoe
Fort William
Skye
Torridon
Assynt
Inverness
Cairngorms
Edinburgh
```

---

# Marker Behavior

Every configured location creates a marker.

Marker popup should display:

```text
Location Name

Description

Region
```

Example:

```text
Quiraing
Iconic ridge hike
Isle of Skye
```

---

# Marker States

Default:

```text
Blue Marker
```

Hover:

```text
Larger Marker
```

Selected:

```text
Orange Marker

Pulse Animation
```

---

# Map → Grid Synchronization

Click Marker:

```text
Highlight Marker

Scroll Grid Row Into View

Highlight Row

Select Location
```

---

# Grid → Map Synchronization

Click Grid Row:

```text
Center Map

Highlight Marker

Pulse Marker

Select Location
```

Only one selected location allowed.

---

# Forecast Grid

Rows:

```text
Location

Morning
Afternoon
Evening
```

Columns:

```text
Today
Tomorrow
Day 3
Day 4
Day 5
Day 6
Day 7
```

---

# Grid Features

Required:

```text
Sticky Header

Sticky Location Column

Sticky Time Period Column

Horizontal Scroll

Vertical Scroll

Touch Support

Keyboard Navigation

Selected Row Highlighting

Selected Cell Highlighting
```

---

# Weather Cell Layout

Each weather cell should resemble:

```text
58°

12 mph

15%

0.05"
```

or

```text
[58°]

[12 mph]

[15% | .05"]
```

Designed for rapid scanning.

---

# Weather Icons

Temperature:

```text
☀
```

Wind:

```text
🌀
```

Rain:

```text
☔
```

Cloud:

```text
☁
```

Visibility:

```text
👁
```

---

# Hiking Suitability Score

Purpose:

Evaluate:

```text
Hiking
Photography
Sightseeing
Scenic Driving
```

---

# Score Range

```text
0 - 100
```

---

# Score Formula

Start:

```text
100
```

Subtract:

```text
Rain Probability × 0.40

Wind Speed × 1.50

Cloud Cover × 0.15
```

Bonuses:

```text
Visibility > 15km  +10

Visibility > 25km  +20

Temperature Between 50F and 68F +10
```

Clamp:

```text
0-100
```

---

# Color Thresholds

Green:

```text
75 - 100
```

Meaning:

```text
Excellent
```

---

Yellow:

```text
50 - 74
```

Meaning:

```text
Acceptable
```

---

Red:

```text
0 - 49
```

Meaning:

```text
Poor
```

---

# Search

Provide live filtering.

Examples:

```text
fairy

skye

glencoe

quiraing
```

Filtering should happen without page reload.

---

# Sorting

Supported Sorts:

```text
Location

Region

Today's Score

Tomorrow's Score

Best Forecast Over Next 7 Days
```

---

# Backend APIs

## Locations

```http
GET /api/locations
```

Returns:

```json
[
  {
    "id":"fairy-pools",
    "name":"Fairy Pools",
    "region":"Isle of Skye",
    "latitude":57.252,
    "longitude":-6.272
  }
]
```

---

## Forecast

```http
GET /api/forecast
```

Returns Aggregated Forecast Data

---

## Refresh

```http
POST /api/refresh
```

Forces Cache Refresh

---

# Future APIs

```http
GET /api/location/{id}

GET /api/sunrise-sunset

GET /api/history/{id}

GET /api/route-weather
```

---

# Data Models

## Location

```json
{
  "id": "",
  "name": "",
  "region": "",
  "description": "",
  "latitude": 0,
  "longitude": 0
}
```

---

## Hourly Weather

```json
{
  "timestamp": "",
  "temperature": 58,
  "windSpeed": 12,
  "windGust": 20,
  "rainProbability": 15,
  "precipitation": 0.05,
  "visibility": 20000,
  "cloudCover": 25
}
```

---

## Period Forecast

```json
{
  "locationId": "",
  "date": "",
  "period": "Morning",

  "temperature": 58,
  "wind": 12,
  "gust": 20,

  "rainProbability": 15,
  "rainAmount": 0.05,

  "visibility": 20000,
  "cloudCover": 25,

  "score": 84,
  "scoreColor": "green"
}
```

---

# Scotland Coverage Strategy

Locations are divided into:

```text
Tier 1 = Planned Hikes

Tier 2 = Major Hiking Destinations

Tier 3 = Regional Weather Coverage Points
```

---

# Tier 1: Planned Hikes

```json
[
  {
    "id":"fairy-pools",
    "name":"Fairy Pools",
    "region":"Isle of Skye",
    "latitude":57.252,
    "longitude":-6.272
  },
  {
    "id":"quiraing",
    "name":"Quiraing",
    "region":"Isle of Skye",
    "latitude":57.650,
    "longitude":-6.272
  },
  {
    "id":"old-man-of-storr",
    "name":"Old Man of Storr",
    "region":"Isle of Skye",
    "latitude":57.506,
    "longitude":-6.177
  },
  {
    "id":"neist-point",
    "name":"Neist Point",
    "region":"Isle of Skye",
    "latitude":57.423,
    "longitude":-6.787
  },
  {
    "id":"sligachan",
    "name":"Sligachan",
    "region":"Isle of Skye",
    "latitude":57.289,
    "longitude":-6.178
  },
  {
    "id":"fairy-glen",
    "name":"Fairy Glen",
    "region":"Isle of Skye",
    "latitude":57.580,
    "longitude":-6.356
  },
  {
    "id":"coral-beach",
    "name":"Coral Beach",
    "region":"Isle of Skye",
    "latitude":57.547,
    "longitude":-6.610
  }
]
```

---

# Tier 2: Major Hiking Destinations

```json
[
  {
    "id":"loch-lomond",
    "name":"Loch Lomond",
    "region":"Trossachs",
    "latitude":56.083,
    "longitude":-4.586
  },
  {
    "id":"conic-hill",
    "name":"Conic Hill",
    "region":"Trossachs",
    "latitude":56.090,
    "longitude":-4.533
  },
  {
    "id":"ben-aan",
    "name":"Ben Aan",
    "region":"Trossachs",
    "latitude":56.244,
    "longitude":-4.369
  },
  {
    "id":"three-sisters",
    "name":"Three Sisters",
    "region":"Glencoe",
    "latitude":56.676,
    "longitude":-5.021
  },
  {
    "id":"lost-valley",
    "name":"Lost Valley",
    "region":"Glencoe",
    "latitude":56.665,
    "longitude":-5.036
  },
  {
    "id":"buachaille-etive-mor",
    "name":"Buachaille Etive Mor",
    "region":"Glencoe",
    "latitude":56.638,
    "longitude":-4.983
  },
  {
    "id":"ben-nevis",
    "name":"Ben Nevis Visitor Area",
    "region":"Fort William",
    "latitude":56.796,
    "longitude":-5.004
  },
  {
    "id":"glenfinnan",
    "name":"Glenfinnan",
    "region":"Lochaber",
    "latitude":56.871,
    "longitude":-5.431
  },
  {
    "id":"beinn-eighe",
    "name":"Beinn Eighe",
    "region":"Torridon",
    "latitude":57.626,
    "longitude":-5.429
  },
  {
    "id":"liathach",
    "name":"Liathach",
    "region":"Torridon",
    "latitude":57.561,
    "longitude":-5.493
  },
  {
    "id":"stac-pollaidh",
    "name":"Stac Pollaidh",
    "region":"Assynt",
    "latitude":58.043,
    "longitude":-5.209
  },
  {
    "id":"suilven",
    "name":"Suilven",
    "region":"Assynt",
    "latitude":58.137,
    "longitude":-5.202
  },
  {
    "id":"quinag",
    "name":"Quinag Trailhead",
    "region":"Assynt",
    "latitude":58.209,
    "longitude":-5.053
  }
]
```

---

# Tier 3: Scotland Weather Coverage Network

```json
[
  {"id":"glasgow","name":"Glasgow","region":"Central Belt","latitude":55.864,"longitude":-4.251},
  {"id":"stirling","name":"Stirling","region":"Central Scotland","latitude":56.116,"longitude":-3.936},
  {"id":"oban","name":"Oban","region":"Argyll","latitude":56.412,"longitude":-5.471},
  {"id":"fort-william","name":"Fort William","region":"West Highlands","latitude":56.819,"longitude":-5.105},
  {"id":"portree","name":"Portree","region":"Skye","latitude":57.413,"longitude":-6.194},
  {"id":"gairloch","name":"Gairloch","region":"Northwest Highlands","latitude":57.726,"longitude":-5.690},
  {"id":"applecross","name":"Applecross","region":"Wester Ross","latitude":57.433,"longitude":-5.812},
  {"id":"torridon","name":"Torridon","region":"Wester Ross","latitude":57.548,"longitude":-5.504},
  {"id":"ullapool","name":"Ullapool","region":"Northwest Highlands","latitude":57.899,"longitude":-5.160},
  {"id":"lochinver","name":"Lochinver","region":"Assynt","latitude":58.148,"longitude":-5.240},
  {"id":"durness","name":"Durness","region":"Far North","latitude":58.568,"longitude":-4.746},
  {"id":"tongue","name":"Tongue","region":"Far North","latitude":58.492,"longitude":-4.418},
  {"id":"john-o-groats","name":"John O Groats","region":"Caithness","latitude":58.637,"longitude":-3.068},
  {"id":"inverness","name":"Inverness","region":"Highlands","latitude":57.477,"longitude":-4.224},
  {"id":"aviemore","name":"Aviemore","region":"Cairngorms","latitude":57.195,"longitude":-3.828},
  {"id":"loch-morlich","name":"Loch Morlich","region":"Cairngorms","latitude":57.183,"longitude":-3.751},
  {"id":"cairngorm-mountain","name":"Cairngorm Mountain","region":"Cairngorms","latitude":57.117,"longitude":-3.644},
  {"id":"pitlochry","name":"Pitlochry","region":"Perthshire","latitude":56.702,"longitude":-3.735},
  {"id":"edinburgh","name":"Edinburgh","region":"Lothians","latitude":55.953,"longitude":-3.189}
]
```

---

# Future Enhancements

```text
Driving Time

Distance From Current Location

Camping Score

Photography Score

Sunrise/Sunset

Moon Phase

Weather History

Weather Trends

Forecast Confidence

Route Optimization

Favorites

Export To Excel

Offline Cache

Dark Mode

Regional Presets

Trip-Specific Location Collections
```

---

# Success Criteria

A traveler should be able to:

1. Open the Weather Planner
2. View every major hiking region in Scotland
3. Click a map location
4. Instantly view a 7-day weather forecast
5. Compare morning, afternoon and evening conditions
6. Use color-coded scoring to identify the best destination
7. Make a travel decision in under 30 seconds

The Weather Planner should feel like a combination of:

- Interactive GIS map
- Weather dashboard
- Hiking conditions report
- Travel planning spreadsheet

optimized specifically for Scotland adventure travel.

