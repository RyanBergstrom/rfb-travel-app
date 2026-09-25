import React from 'react'
import SearchBar from './SearchBar'
import WeatherLegend from './WeatherLegend'

export default function Toolbar({
  searchQuery,
  onSearchChange,
  sortBy,
  onSortChange,
  onRefresh,
  isRefreshing,
}) {
  return (
    <div className="toolbar">
      <SearchBar value={searchQuery} onChange={onSearchChange} />

      <select
        className="sort-select"
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        aria-label="Sort by"
      >
        <option value="location">Sort: Location</option>
        <option value="region">Sort: Region</option>
      </select>

      <WeatherLegend />

      <button
        className="refresh-btn"
        onClick={onRefresh}
        disabled={isRefreshing}
      >
        {isRefreshing ? 'Refreshing...' : 'Refresh'}
      </button>
    </div>
  )
}
