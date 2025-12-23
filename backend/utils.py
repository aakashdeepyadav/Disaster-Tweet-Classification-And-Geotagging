import re

DISASTER_KEYWORDS = {
    "Flood": ["flood", "flooding", "waterlogging", "overflow"],
    "Earthquake": ["earthquake", "quake", "tremor", "tremors"],
    "Fire": ["fire", "burning", "blaze", "wildfire", "inferno"],
    "Accident": ["accident", "crash", "collision", "pileup"],
    "Storm": ["storm", "cyclone", "hurricane", "typhoon", "tornado"],
    "Landslide": ["landslide", "mudslide", "rockslide"],
    "Explosion": ["explosion", "blast", "bomb", "detonation", "exploded"],
}

def infer_category(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in DISASTER_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "Unknown"

def infer_severity(text: str) -> str:
    text_lower = text.lower()

    high_words = ["massive", "major", "severe", "devastating", "catastrophic"]
    medium_words = ["moderate", "significant", "large", "serious"]
    low_words = ["minor", "small", "light"]

    numbers = [int(x) for x in re.findall(r"\b\d+\b", text_lower)]

    if any(w in text_lower for w in high_words) or any(n >= 50 for n in numbers):
        return "High"
    if any(w in text_lower for w in medium_words) or any(10 <= n < 50 for n in numbers):
        return "Medium"
    if any(w in text_lower for w in low_words):
        return "Low"

    if numbers:
        max_n = max(numbers)
        if max_n >= 50:
            return "High"
        elif max_n >= 10:
            return "Medium"
        else:
            return "Low"

    return "Medium"

