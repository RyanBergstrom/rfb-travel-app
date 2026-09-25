export function calculateHikingScore({
  temperatureF,
  windSpeedMph,
  rainProbability,
  cloudCover,
  visibilityM,
}) {
  let score = 100;

  score -= rainProbability * 0.40;
  score -= windSpeedMph * 1.50;
  score -= cloudCover * 0.15;

  const visibilityKm = visibilityM / 1000;
  if (visibilityKm > 25) {
    score += 20;
  } else if (visibilityKm > 15) {
    score += 10;
  }

  if (temperatureF >= 50 && temperatureF <= 68) {
    score += 10;
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

export function scoreColor(score) {
  if (score >= 75) return 'green';
  if (score >= 50) return 'yellow';
  return 'red';
}

export function scoreLabel(score) {
  if (score >= 75) return 'Excellent';
  if (score >= 50) return 'Acceptable';
  return 'Poor';
}

export function celsiusToFahrenheit(celsius) {
  return Math.round((celsius * 9 / 5 + 32) * 10) / 10;
}

export function kmToMiles(km) {
  return Math.round(km * 0.621371 * 10) / 10;
}
