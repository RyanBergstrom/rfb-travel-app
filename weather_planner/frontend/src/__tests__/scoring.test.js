import { describe, it, expect } from 'vitest'
import {
  calculateHikingScore,
  scoreColor,
  scoreLabel,
  celsiusToFahrenheit,
  kmToMiles,
} from '../services/scoring'

describe('calculateHikingScore', () => {
  it('returns 100 for perfect conditions', () => {
    const score = calculateHikingScore({
      temperatureF: 60,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 30000,
    })
    expect(score).toBe(100)
  })

  it('returns 0 for terrible conditions', () => {
    const score = calculateHikingScore({
      temperatureF: 100,
      windSpeedMph: 50,
      rainProbability: 100,
      cloudCover: 100,
      visibilityM: 100,
    })
    expect(score).toBe(0)
  })

  it('applies rain probability penalty correctly', () => {
    const noRain = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    const rain50 = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 0,
      rainProbability: 50,
      cloudCover: 0,
      visibilityM: 10000,
    })
    expect(noRain - rain50).toBe(20)
  })

  it('applies wind penalty correctly', () => {
    const noWind = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    const wind10 = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 10,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    expect(noWind - wind10).toBe(15)
  })

  it('applies cloud cover penalty correctly', () => {
    const clear = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    const cloudy = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 100,
      visibilityM: 10000,
    })
    expect(clear - cloudy).toBe(15)
  })

  it('gives +10 bonus for visibility > 15km', () => {
    const low = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 10000,
    })
    const high = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 20000,
    })
    expect(high - low).toBe(10)
  })

  it('gives +20 bonus for visibility > 25km', () => {
    const v15 = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 20000,
    })
    const v25 = calculateHikingScore({
      temperatureF: 80,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 30000,
    })
    expect(v25 - v15).toBe(10)
  })

  it('gives +10 bonus for temperature 50-68F', () => {
    const cold = calculateHikingScore({
      temperatureF: 40,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 10000,
    })
    const ideal = calculateHikingScore({
      temperatureF: 60,
      windSpeedMph: 20,
      rainProbability: 50,
      cloudCover: 50,
      visibilityM: 10000,
    })
    expect(ideal - cold).toBe(10)
  })

  it('no temperature bonus below 50F', () => {
    const score = calculateHikingScore({
      temperatureF: 49,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    expect(score).toBe(100)
  })

  it('no temperature bonus above 68F', () => {
    const score = calculateHikingScore({
      temperatureF: 69,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 10000,
    })
    expect(score).toBe(100)
  })

  it('clamps to minimum 0', () => {
    const score = calculateHikingScore({
      temperatureF: 100,
      windSpeedMph: 50,
      rainProbability: 100,
      cloudCover: 100,
      visibilityM: 100,
    })
    expect(score).toBe(0)
  })

  it('clamps to maximum 100', () => {
    const score = calculateHikingScore({
      temperatureF: 60,
      windSpeedMph: 0,
      rainProbability: 0,
      cloudCover: 0,
      visibilityM: 30000,
    })
    expect(score).toBe(100)
  })

  it('returns an integer', () => {
    const score = calculateHikingScore({
      temperatureF: 55,
      windSpeedMph: 7.3,
      rainProbability: 23.7,
      cloudCover: 45.2,
      visibilityM: 18500,
    })
    expect(Number.isInteger(score)).toBe(true)
  })

  it('calculates combined score correctly', () => {
    const score = calculateHikingScore({
      temperatureF: 58,
      windSpeedMph: 12,
      rainProbability: 20,
      cloudCover: 25,
      visibilityM: 20000,
    })
    // 100 - (20*0.40) - (12*1.50) - (25*0.15) + 10(vis>15km) + 10(temp in range)
    // = 100 - 8 - 18 - 3.75 + 10 + 10 = 90.25 -> 90
    const expected = Math.round(100 - (20 * 0.40) - (12 * 1.50) - (25 * 0.15) + 10 + 10)
    expect(score).toBe(expected)
  })
})

describe('scoreColor', () => {
  it('returns green for 75-100', () => {
    expect(scoreColor(75)).toBe('green')
    expect(scoreColor(100)).toBe('green')
  })

  it('returns yellow for 50-74', () => {
    expect(scoreColor(50)).toBe('yellow')
    expect(scoreColor(74)).toBe('yellow')
  })

  it('returns red for 0-49', () => {
    expect(scoreColor(0)).toBe('red')
    expect(scoreColor(49)).toBe('red')
  })
})

describe('scoreLabel', () => {
  it('returns Excellent for 75+', () => {
    expect(scoreLabel(85)).toBe('Excellent')
  })

  it('returns Acceptable for 50-74', () => {
    expect(scoreLabel(60)).toBe('Acceptable')
  })

  it('returns Poor for 0-49', () => {
    expect(scoreLabel(30)).toBe('Poor')
  })
})

describe('celsiusToFahrenheit', () => {
  it('converts 0C to 32F', () => {
    expect(celsiusToFahrenheit(0)).toBeCloseTo(32, 0)
  })

  it('converts 100C to 212F', () => {
    expect(celsiusToFahrenheit(100)).toBeCloseTo(212, 0)
  })

  it('converts 20C to 68F', () => {
    expect(celsiusToFahrenheit(20)).toBeCloseTo(68, 0)
  })
})

describe('kmToMiles', () => {
  it('converts 100km to ~62.1 miles', () => {
    expect(kmToMiles(100)).toBeCloseTo(62.1, 0)
  })

  it('converts 0km to 0 miles', () => {
    expect(kmToMiles(0)).toBe(0)
  })
})
