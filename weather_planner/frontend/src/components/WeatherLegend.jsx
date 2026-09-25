import React from 'react'

export default function WeatherLegend() {
  return (
    <div className="legend">
      <div className="legend-item">
        <div className="legend-dot green"></div>
        <span>75-100 Excellent</span>
      </div>
      <div className="legend-item">
        <div className="legend-dot yellow"></div>
        <span>50-74 Acceptable</span>
      </div>
      <div className="legend-item">
        <div className="legend-dot red"></div>
        <span>0-49 Poor</span>
      </div>
    </div>
  )
}
