import React, { useRef, useCallback, useEffect } from 'react'

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (date.getTime() === today.getTime()) return 'Today'
  if (date.getTime() === tomorrow.getTime()) return 'Tomorrow'

  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function WeatherCell({ data }) {
  if (!data) return <div className="grid-cell">--</div>

  return (
    <div className={`grid-cell score-${data.scoreColor}`}>
      <div className="weather-cell">
        <span className="temp"><span className="sun-icon">☀</span> {Math.round(data.temperature)}°</span>
        <span className="wind">🌀 {Math.round(data.wind)} mph</span>
        <span className="rain">💧 {Math.round(data.rainProbability)}% - {data.rainAmount}"</span>
      </div>
    </div>
  )
}

export default function ForecastGrid({ forecasts, locations, selectedId, onSelect }) {
  const gridRef = useRef(null)
  const locationRefs = useRef({})

  const groupedByLocation = React.useMemo(() => {
    const groups = {}
    forecasts.forEach(f => {
      if (!groups[f.locationId]) {
        groups[f.locationId] = []
      }
      groups[f.locationId].push(f)
    })
    return groups
  }, [forecasts])

  const sortedLocations = React.useMemo(() => {
    return [...locations].sort((a, b) => a.name.localeCompare(b.name))
  }, [locations])

  const dates = React.useMemo(() => {
    const allDates = [...new Set(forecasts.map(f => f.date))].sort()
    return allDates.slice(0, 7)
  }, [forecasts])

  const periods = ['Morning', 'Afternoon', 'Evening']
  const periodIcons = { Morning: '🌅', Afternoon: '☀️', Evening: '🌇' }

  useEffect(() => {
    if (selectedId && locationRefs.current[selectedId]) {
      locationRefs.current[selectedId].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest',
      })
    }
  }, [selectedId])

  const handleRowClick = useCallback((locId) => {
    onSelect(locId)
  }, [onSelect])

  const handleKeyDown = useCallback((e, locId) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSelect(locId)
    }
  }, [onSelect])

  if (forecasts.length === 0) {
    return (
      <div className="forecast-grid-wrapper">
        <div className="empty-state">
          <div className="icon">🗺</div>
          <div>Loading forecast data...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="forecast-grid-wrapper" ref={gridRef}>
      <div
        className="forecast-grid"
        style={{
          gridTemplateColumns: `80px 36px repeat(${dates.length}, minmax(100px, 1fr))`,
        }}
        role="grid"
        aria-label="Weather forecast grid"
      >
        <div className="grid-cell header location-header" role="columnheader">
          Location
        </div>
        <div className="grid-cell header period-header" role="columnheader">
          Period
        </div>
        {dates.map(d => (
          <div key={d} className="grid-cell header" role="columnheader">
            {formatDate(d)}
          </div>
        ))}

        {sortedLocations.map(loc => {
          const locForecasts = groupedByLocation[loc.id] || []
          const isSelected = loc.id === selectedId

          return periods.map((period, pIdx) => {
            const periodData = locForecasts.filter(f => f.period === period)
            const rowKey = `${loc.id}-${period}`

            return (
              <React.Fragment key={rowKey}>
                {pIdx === 0 && (
                  <div
                    ref={el => { locationRefs.current[loc.id] = el }}
                    className={`grid-cell location-col location-row ${isSelected ? 'selected' : ''}`}
                    style={{ gridRow: `span ${periods.length}` }}
                    onClick={() => handleRowClick(loc.id)}
                    onKeyDown={(e) => handleKeyDown(e, loc.id)}
                    role="row"
                    tabIndex={0}
                    aria-label={`${loc.name}, ${loc.region}`}
                  >
                    <div className="loc-name">{loc.name.split(' ').map((w, i) => <div key={i}>{w}</div>)}</div>
                    <div className="loc-region">{loc.region}</div>
                  </div>
                )}
                <div
                  className={`grid-cell period-col ${isSelected ? 'selected' : ''}`}
                  role="rowheader"
                >
                  <span title={period}>{periodIcons[period]}</span>
                </div>
                {dates.map(d => {
                  const data = periodData.find(f => f.date === d)
                  return (
                    <WeatherCell key={`${loc.id}-${period}-${d}`} data={data} />
                  )
                })}
              </React.Fragment>
            )
          })
        })}
      </div>
    </div>
  )
}
