import { useQuery, useMutation, useQueryClient } from 'react-query'
import { fetchLocations, fetchForecast, refreshWeather } from '../services/api'

export function useLocations() {
  return useQuery('locations', fetchLocations)
}

export function useForecast(locationId) {
  return useQuery({
    queryKey: ['forecast', locationId],
    queryFn: () => fetchForecast(locationId),
    enabled: true,
  })
}

export function useRefresh() {
  const queryClient = useQueryClient()
  return useMutation(refreshWeather, {
    onSuccess: () => {
      queryClient.invalidateQueries('forecast')
    },
  })
}
