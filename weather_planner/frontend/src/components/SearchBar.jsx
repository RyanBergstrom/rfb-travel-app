import React from 'react'

export default function SearchBar({ value, onChange }) {
  return (
    <input
      type="text"
      className="search-input"
      placeholder="Search locations... (e.g. fairy, skye, glencoe)"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Search locations"
    />
  )
}
