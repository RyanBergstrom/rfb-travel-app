import React, { useState, useCallback } from 'react'
import ScotlandMap from '../components/ScotlandMap'
import ForecastGrid from '../components/ForecastGrid'
import { useLocations, useForecast } from '../hooks/useForecasts'

export default function WeatherPlanner() {
  const [selectedId, setSelectedId] = useState(null)

  const { data: locations = [], isLoading: locationsLoading } = useLocations()
  const { data: forecastData, isLoading: forecastLoading } = useForecast()

  const forecasts = forecastData?.forecasts || []

  const handleSelect = useCallback((id) => {
    setSelectedId(prev => prev === id ? null : id)
  }, [])

  if (locationsLoading) {
    return (
      <div className="weather-planner">
        <div className="loading">
          <div className="spinner"></div>
          <span>Loading locations...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="weather-planner">
      <div className="map-section">
        <ScotlandMap
          locations={locations}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
      </div>

      <div className="grid-section">
        {forecastLoading ? (
          <div className="loading">
            <div className="spinner"></div>
            <span>Loading forecasts...</span>
          </div>
        ) : (
          <ForecastGrid
            forecasts={forecasts}
            locations={locations}
            selectedId={selectedId}
            onSelect={handleSelect}
          />
        )}
      </div>
    </div>
  )
}
