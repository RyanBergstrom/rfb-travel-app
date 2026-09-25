import axios from 'axios'

const api = axios.create({
  baseURL: '/api/weather',
  timeout: 30000,
})

export async function fetchLocations() {
  const { data } = await api.get('/locations')
  return data
}

export async function fetchForecast(locationId) {
  const params = locationId ? { location_id: locationId } : {}
  const { data } = await api.get('/forecast', { params })
  return data
}

export function subscribeForecastStream(onBatch, onDone) {
  const es = new EventSource('/api/weather/forecast/stream')
  es.addEventListener('forecast', (e) => {
    onBatch(JSON.parse(e.data))
  })
  es.addEventListener('done', (e) => {
    onDone(JSON.parse(e.data))
    es.close()
  })
  es.onerror = () => {
    es.close()
  }
  return () => es.close()
}

export async function refreshWeather() {
  const { data } = await api.post('/refresh')
  return data
}
