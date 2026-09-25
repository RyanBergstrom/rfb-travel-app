import React, { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'

const SCOTLAND_CENTER = [57.0, -5.0]
const DEFAULT_ZOOM = 7

function createIcon(color) {
  return L.divIcon({
    className: '',
    html: `<svg width="24" height="36" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}" stroke="#fff" stroke-width="1.5"/>
      <circle cx="12" cy="11" r="5" fill="white"/>
    </svg>`,
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  })
}

const DEFAULT_ICON = createIcon('#2563eb')
const SELECTED_ICON = createIcon('#f97316')

function MapEvents({ selectedId, onMarkerClick }) {
  const map = useMap()

  useEffect(() => {
    if (selectedId) {
      map.closePopup()
    }
  }, [selectedId, map])

  return null
}

function FlyToLocation({ selectedId, locations }) {
  const map = useMap()

  useEffect(() => {
    if (selectedId) {
      const loc = locations.find(l => l.id === selectedId)
      if (loc) {
        map.flyTo([loc.latitude, loc.longitude], 10, { duration: 0.8 })
      }
    }
  }, [selectedId, locations, map])

  return null
}

export default function ScotlandMap({ locations, selectedId, onSelect }) {
  return (
    <MapContainer
      center={SCOTLAND_CENTER}
      zoom={DEFAULT_ZOOM}
      className="map-container"
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapEvents selectedId={selectedId} />
      <FlyToLocation selectedId={selectedId} locations={locations} />
      {locations.map(loc => (
        <Marker
          key={loc.id}
          position={[loc.latitude, loc.longitude]}
          icon={loc.id === selectedId ? SELECTED_ICON : DEFAULT_ICON}
          eventHandlers={{
            click: () => onSelect(loc.id),
          }}
        >
          <Popup>
            <div style={{ textAlign: 'center' }}>
              <strong>{loc.name}</strong>
              <br />
              <span style={{ fontSize: '12px', color: '#666' }}>{loc.description}</span>
              <br />
              <span style={{ fontSize: '11px', color: '#888' }}>{loc.region}</span>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
