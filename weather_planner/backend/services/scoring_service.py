def calculate_hiking_score(
    temperature_f: float,
    wind_speed_mph: float,
    rain_probability: float,
    cloud_cover: float,
    visibility_m: float,
) -> int:
    score = 100.0

    score -= rain_probability * 0.40
    score -= wind_speed_mph * 1.50
    score -= cloud_cover * 0.15

    visibility_km = visibility_m / 1000.0
    if visibility_km > 25:
        score += 20
    elif visibility_km > 15:
        score += 10

    if 50 <= temperature_f <= 68:
        score += 10

    return max(0, min(100, int(round(score))))


def score_color(score: int) -> str:
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def score_label(score: int) -> str:
    if score >= 75:
        return "Excellent"
    if score >= 50:
        return "Acceptable"
    return "Poor"
