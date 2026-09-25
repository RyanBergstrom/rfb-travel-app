import React, { useState, useCallback, useEffect, useRef } from 'react'
import ScotlandMap from '../components/ScotlandMap'
import ForecastGrid from '../components/ForecastGrid'
import { useLocations } from '../hooks/useForecasts'
import { subscribeForecastStream } from '../services/api'

export default function WeatherPlanner() {
  const [selectedId, setSelectedId] = useState(null)
  const [forecasts, setForecasts] = useState([])
  const [progress, setProgress] = useState(0)
  const [streamStatus, setStreamStatus] = useState('loading')
  const loadedRef = useRef(0)

  const { data: locations = [], isLoading: locationsLoading } = useLocations()

  useEffect(() => {
    setForecasts([])
    setProgress(0)
    setStreamStatus('loading')
    loadedRef.current = 0

    const unsub = subscribeForecastStream(
      (batch) => {
        setForecasts(prev => [...prev, ...batch.forecasts])
        setProgress(batch.progress)
        loadedRef.current = batch.loaded
      },
      () => {
        setStreamStatus('done')
        setProgress(100)
      }
    )

    return unsub
  }, [])

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
        {streamStatus === 'loading' && forecasts.length === 0 ? (
          <div className="loading">
            <div className="spinner"></div>
            <span>Loading forecasts...</span>
          </div>
        ) : (
          <>
            {progress < 100 && (
              <div className="stream-progress">
                <div className="progress-bar" style={{ width: `${progress}%` }} />
                <span className="progress-text">{progress}% loaded</span>
              </div>
            )}
            <ForecastGrid
              forecasts={forecasts}
              locations={locations}
              selectedId={selectedId}
              onSelect={handleSelect}
            />
          </>
        )}
      </div>
    </div>
  )
}
