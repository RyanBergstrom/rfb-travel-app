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

export async function refreshWeather() {
  const { data } = await api.post('/refresh')
  return data
}
