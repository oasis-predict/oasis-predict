from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import csv
import os
import re

app = FastAPI(
    title="OASIS PREDICT API",
    description="Weather intelligence API for probabilistic weather market analysis.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT= Path(__file__).resolve().parents[1]
TRADE_SHEET = PROJECT_ROOT /"data" / "kalshi_trade_sheet.csv"


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def parse_bool(value):
    if value is None:
        return None

    value = str(value).strip().lower()

    if value == "true":
        return True
    if value == "false":
        return False

    return None


def infer_city(ticker, title):
    text = f"{ticker or ''} {title or ''}".lower()

    if "lax" in text or "los angeles" in text:
        return "LA"
    if "ny" in text or "nyc" in text or "new york" in text:
        return "NYC"
    if "chi" in text or "chicago" in text:
        return "Chicago"

    return "Unknown"


def risk_label(distance):
    if distance is None:
        return "UNKNOWN"
    if distance < 2:
        return "HIGH"
    if distance < 4:
        return "MEDIUM"
    return "LOW"


def extract_date_from_ticker(ticker):
    """
    Example:
    KXHIGHLAX-26APR26-B66.5 -> 2026-04-26
    """
    if not ticker:
        return None

    m = re.search(
        r"-(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})-",
        ticker,
    )

    if not m:
        return None

    year = int("20" + m.group(1))
    month_str = m.group(2)
    day = int(m.group(3))

    months = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12,
    }

    month = months[month_str]

    return f"{year:04d}-{month:02d}-{day:02d}"


def is_today_or_future(signal):
    ticker_date_str = extract_date_from_ticker(signal.get("ticker"))

    if not ticker_date_str:
        return True

    try:
        ticker_date = datetime.strptime(ticker_date_str, "%Y-%m-%d").date()
        today = datetime.utcnow().date()

        print("DEBUG:", signal.get("ticker"), ticker_date, today)

        return ticker_date >= today

    except Exception as e:
        print("DATE ERROR:", e)
        return True

def load_signals():
    if not TRADE_SHEET.exists():
        return []

    signals = []

    with TRADE_SHEET. open ("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            distance = safe_float(row.get("distance_to_center"))
            spread = safe_float(
                row.get("consensus_spread_f")
                or row.get("consensus_spread")
                or row.get("spread")
            )

            signal = {
                "ticker": row.get("ticker"),
                "date": extract_date_from_ticker(row.get("ticker")),
                "title": row.get("title"),
                "city": infer_city(row.get("ticker"), row.get("title")),
                "comparison": row.get("comparison"),
                "action": row.get("signal_action"),
                "confidence": row.get("confidence_label"),
                "priority": row.get("priority"),
                "selection_mode": row.get("selection_mode"),

                "ai_probability_yes": safe_float(row.get("ai_probability_yes")),
                "yes_price_percent": safe_float(row.get("yes_price_percent")),
                "no_price_percent": safe_float(row.get("no_price_percent")),
                "edge": safe_float(row.get("edge")),

                "predicted_temp_f": safe_float(row.get("predicted_temp_f")),
                "std_dev": safe_float(row.get("std_dev")),
                "threshold_low": safe_float(row.get("threshold_low")),
                "threshold_high": safe_float(row.get("threshold_high")),
                "range_center": safe_float(row.get("range_center")),
                "distance_to_center": distance,

                "openmeteo_temp_f": safe_float(row.get("openmeteo_temp")),
                "noaa_temp_f": safe_float(row.get("noaa_temp")),
                "nasa_monitor_temp_f": safe_float(row.get("nasa_monitor_temp")),
                "consensus_temp_f": safe_float(
                    row.get("consensus_temp_f")
                    or row.get("consensus_temp")
                ),
                "consensus_spread_f": spread,
                "consensus_ok": parse_bool(row.get("consensus_ok")),
                "yes_allowed": parse_bool(row.get("yes_allowed")),

                "risk": risk_label(distance),

                "recommended_stake_usd": safe_float(row.get("recommended_stake_usd")),
                "estimated_entry_cost_usd": safe_float(row.get("estimated_entry_cost_usd")),
                "estimated_trade_cost_usd": safe_float(
                    row.get("estimated_trade_cost_usd")
                    or row.get("trade_cost_usd")
                    or row.get("estimate")
                ),
            }

            signals.append(signal)

    return signals


@app.get("/")
def root():
    return {
        "app": "OASIS PREDICT",
        "status": "online",
        "message": "Weather intelligence API is running.",
    }


@app.get("/signals")
def get_signals():
    signals = load_signals()

    return {
        "app": "OASIS PREDICT",
        "count": len(signals),
        "signals": signals,
    }


@app.get("/signals/today")
def get_today_signals():
    signals = load_signals()
    filtered = [s for s in signals if is_today_or_future(s)]

    return {
        "app": "OASIS PREDICT",
        "filter": "today_or_future",
        "count": len(filtered),
        "signals": filtered,
    }


@app.get("/signals/{city}")
def get_signals_by_city(city: str):
    city = city.lower()
    signals = load_signals()

    filtered = [
        s for s in signals
        if s.get("city", "").lower() == city
    ]

    return {
        "city": city.upper(),
        "count": len(filtered),
        "signals": filtered,
    }


@app.get("/summary")
def get_summary():
    signals = load_signals()

    by_city = {}
    by_action = {}
    by_risk = {}

    for s in signals:
        city = s.get("city") or "Unknown"
        action = s.get("action") or "Unknown"
        risk = s.get("risk") or "Unknown"

        by_city[city] = by_city.get(city, 0) + 1
        by_action[action] = by_action.get(action, 0) + 1
        by_risk[risk] = by_risk.get(risk, 0) + 1

    return {
        "app": "OASIS PREDICT",
        "total_signals": len(signals),
        "by_city": by_city,
        "by_action": by_action,
        "by_risk": by_risk,
    }


@app.get("/disclaimer")
def disclaimer():
    return {
        "title": "Disclaimer",
        "text": (
            "OASIS PREDICT is a weather data intelligence tool. "
            "It provides statistical weather analysis, model comparisons, "
            "probability indicators, and weather-based risk insights for informational purposes only. "
            "It does not provide financial advice, trading advice, or investment recommendations. "
            "Users are solely responsible for their own decisions."
        ),
    }
