import csv
from datetime import datetime

LEARNING_FILE = "learning.md"
LESSONS_FILE = "lessons.md"
MISTAKES_FILE = "mistakes.md"
SIGNALS_FILE = "data/kalshi_signals.csv"


def count_signals():
    try:
        with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            cities = set()
            types = {"greater_than": 0, "less_than": 0, "between": 0}

            for r in rows:
                city = r.get("city")
                comparison = r.get("comparison")

                if city:
                    cities.add(city)

                if comparison in types:
                    types[comparison] += 1

            return len(rows), sorted(list(cities)), types

    except:
        return 0, [], {"greater_than": 0, "less_than": 0, "between": 0}


def append_learning_log():
    total_signals, cities, types = count_signals()
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""
----------------------------------------
DATE: {today}

SIGNALS GENERATED: {total_signals}

CITIES: {", ".join(cities)}

MARKET TYPES:
- greater_than: {types.get("greater_than", 0)}
- less_than: {types.get("less_than", 0)}
- between: {types.get("between", 0)}

AUTO NOTES:
- System running in learning mode
- Multi-city active
- Data collection in progress
"""

    with open(LEARNING_FILE, "a", encoding="utf-8") as f:
        f.write(text)

    print("=" * 80)
    print("SELF IMPROVE LOG ADDED")
    print("=" * 80)


def update_lessons():
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""
----------------------------------------
LESSON UPDATE: {today}

- Multi-city active → more opportunities
- Learning mode collecting more data
- System exploring all market types
"""

    with open(LESSONS_FILE, "a", encoding="utf-8") as f:
        f.write(text)

    print("LESSONS UPDATED")


def update_mistakes():
    total_signals, cities, types = count_signals()
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [f"\n----------------------------------------\nMISTAKE UPDATE: {today}\n"]

    if total_signals == 0:
        lines.append("- No signals generated → possible over-filtering")

    if len(cities) <= 1:
        lines.append("- System too concentrated on one city")

    if types.get("greater_than", 0) == 0:
        lines.append("- No greater_than signals detected")

    if types.get("between", 0) == 0:
        lines.append("- No between signals detected")

    with open(MISTAKES_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("MISTAKES UPDATED")


if __name__ == "__main__":
    append_learning_log()
    update_lessons()
    update_mistakes()
