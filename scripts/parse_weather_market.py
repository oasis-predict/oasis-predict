import re
from datetime import datetime, timedelta

# Date de référence actuelle
TODAY = datetime(2026, 3, 18)

KNOWN_CITIES = [
    "Shanghai",
    "Paris",
    "London",
    "Seoul",
    "Tokyo",
    "New York",
    "Toronto",
    "Singapore",
    "Chicago",
    "Dallas",
    "Seattle",
    "Munich",
    "Berlin",
    "Madrid",
    "Rome",
    "Luxembourg"
]


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_city(question: str):
    for city in sorted(KNOWN_CITIES, key=len, reverse=True):
        pattern = r"\b" + re.escape(city) + r"\b"
        if re.search(pattern, question, flags=re.IGNORECASE):
            return city
    return None


def parse_date(question: str):
    q = question.lower()

    if "today" in q:
        return TODAY.strftime("%Y-%m-%d")

    if "tomorrow" in q:
        return (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    if "yesterday" in q:
        return (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")

    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    # Exemples:
    # on March 18
    # by March 21, 2026
    # March 18
    pattern = re.search(
        r"\b("
        + "|".join(month_map.keys())
        + r")\s+(\d{1,2})(?:,\s*(\d{4}))?\b",
        q,
    )

    if pattern:
        month_name = pattern.group(1)
        day = int(pattern.group(2))
        year = int(pattern.group(3)) if pattern.group(3) else TODAY.year
        month = month_map[month_name]

        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def parse_threshold(question: str):
    q = question.lower()

    patterns = [
        r"(?:exceed|above|over|greater than|higher than)\s*(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)?",
        r"(?:below|under|less than|lower than)\s*(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)?",
        r"(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

    return None


def detect_market_type(question: str):
    q = question.lower()

    if "highest temperature" in q or "high temperature" in q or "max temperature" in q:
        return "daily_high_temperature"

    if "lowest temperature" in q or "low temperature" in q or "min temperature" in q:
        return "daily_low_temperature"

    if "rain" in q or "precipitation" in q:
        return "rain_event"

    if "snow" in q:
        return "snow_event"

    if "wind" in q:
        return "wind_event"

    if "humidity" in q:
        return "humidity_event"

    if "temperature" in q or "temp" in q:
        return "temperature_event"

    return "unknown"


def detect_comparison(question: str):
    q = question.lower()

    if any(x in q for x in ["exceed", "above", "over", "greater than", "higher than"]):
        return "greater_than"

    if any(x in q for x in ["below", "under", "less than", "lower than"]):
        return "less_than"

    if "between" in q:
        return "between"

    return None


def detect_market_mode(question: str, outcomes=None):
    q = question.lower()
    outcomes = outcomes or []

    # Si on a explicitement Yes/No
    outcomes_lower = [str(x).lower() for x in outcomes]
    if "yes" in outcomes_lower and "no" in outcomes_lower:
        return "binary"

    # Heuristique texte
    if q.startswith("will "):
        return "binary"

    if "highest temperature" in q or "lowest temperature" in q:
        # souvent multi-outcome en tranches, mais pas toujours
        if len(outcomes) > 2:
            return "multi_outcome"
        return "temperature_range_or_binary"

    if len(outcomes) > 2:
        return "multi_outcome"

    return "unknown"


def parse_question(question: str, outcomes=None):
    question = normalize_spaces(question)

    result = {
        "raw_question": question,
        "city": parse_city(question),
        "date": parse_date(question),
        "market_type": detect_market_type(question),
        "comparison": detect_comparison(question),
        "threshold": parse_threshold(question),
        "mode": detect_market_mode(question, outcomes),
        "outcomes": outcomes or []
    }

    return result


def pretty_print(parsed: dict):
    print("=" * 70)
    print("RAW QUESTION :", parsed["raw_question"])
    print("CITY         :", parsed["city"])
    print("DATE         :", parsed["date"])
    print("MARKET TYPE  :", parsed["market_type"])
    print("COMPARISON   :", parsed["comparison"])
    print("THRESHOLD    :", parsed["threshold"])
    print("MODE         :", parsed["mode"])
    print("OUTCOMES     :", parsed["outcomes"])


if __name__ == "__main__":
    examples = [
        {
            "question": "Highest temperature in Shanghai on March 18?",
            "outcomes": ["Below 10°C", "10-14°C", "15-19°C", "20°C or higher"]
        },
        {
            "question": "Will it rain in Paris tomorrow?",
            "outcomes": ["Yes", "No"]
        },
        {
            "question": "Will London exceed 18°C on March 21?",
            "outcomes": ["Yes", "No"]
        },
        {
            "question": "Lowest temperature in Munich on March 21?",
            "outcomes": ["Below 0°C", "0-4°C", "5-9°C", "10°C or higher"]
        },
        {
            "question": "Will it snow in Toronto today?",
            "outcomes": ["Yes", "No"]
        }
    ]

    for example in examples:
        parsed = parse_question(example["question"], example["outcomes"])
        pretty_print(parsed)
