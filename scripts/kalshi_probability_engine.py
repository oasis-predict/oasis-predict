import os
import sys
from datetime import datetime, timezone
from math import erf, sqrt

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import config
from parse_kalshi_weather_market import parse_kalshi_question


API_KEY = getattr(config, 'API_KEY', None)

CITY_SETTINGS = {
    'Los Angeles': {
        'query': 'Los Angeles,US',
        'latitude': 34.0522,
        'longitude': -118.2437,
        'timezone': 'America/Los_Angeles',
        'monthly_high_f': {
            1: 68.0, 2: 69.0, 3: 72.0, 4: 75.0, 5: 78.0, 6: 82.0,
            7: 86.0, 8: 87.0, 9: 85.0, 10: 80.0, 11: 74.0, 12: 68.0,
        },
        'fallback_std_f': 5.0,
    },
    'New York': {
        'query': 'New York,US',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'timezone': 'America/New_York',
        'monthly_high_f': {
            1: 39.0, 2: 42.0, 3: 50.0, 4: 61.0, 5: 71.0, 6: 79.0,
            7: 85.0, 8: 83.0, 9: 76.0, 10: 65.0, 11: 54.0, 12: 44.0,
        },
        'fallback_std_f': 7.0,
    },
    'Chicago': {
        'query': 'Chicago,US',
        'latitude': 41.8781,
        'longitude': -87.6298,
        'timezone': 'America/Chicago',
        'monthly_high_f': {
            1: 32.0, 2: 36.0, 3: 47.0, 4: 59.0, 5: 70.0, 6: 80.0,
            7: 84.0, 8: 82.0, 9: 75.0, 10: 62.0, 11: 48.0, 12: 36.0,
        },
        'fallback_std_f': 8.0,
    },
}

FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
OPEN_METEO_ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'


def c_to_f(temp_c):
    return (temp_c * 9 / 5) + 32


def normal_cdf(x, mean, std):
    std = max(float(std), 0.01)
    z = (x - mean) / (std * sqrt(2))
    return 0.5 * (1 + erf(z))


def probability_greater_than(mean, std, threshold):
    return (1 - normal_cdf(threshold, mean, std)) * 100


def probability_less_than(mean, std, threshold):
    return normal_cdf(threshold, mean, std) * 100


def probability_between(mean, std, low, high):
    return (normal_cdf(high, mean, std) - normal_cdf(low, mean, std)) * 100


def parse_date(date_str):
    try:
        dt = datetime.strptime(date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d'), dt
    except Exception:
        return None, None


def get_city_settings(city):
    return CITY_SETTINGS.get(city)


def compute_distribution(temps_f):
    if not temps_f:
        return None

    mean_f = sum(temps_f) / len(temps_f)
    high_f = max(temps_f)
    low_f = min(temps_f)

    if len(temps_f) > 1:
        var = sum((temp - mean_f) ** 2 for temp in temps_f) / len(temps_f)
        sample_std = sqrt(var)
    else:
        sample_std = 0.0

    span_std = (high_f - low_f) / 3.0
    std_f = max(sample_std, span_std, 2.0)

    return {
        'mean_f': round(mean_f, 2),
        'max_f': round(high_f, 2),
        'min_f': round(low_f, 2),
        'std_f': round(std_f, 2),
    }


def fetch_forecast(city, target_date):
    settings = get_city_settings(city)
    if not settings or not API_KEY:
        return None

    params = {
        'q': settings['query'],
        'appid': API_KEY,
        'units': 'metric',
    }

    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    temps_f = []
    for item in data.get('list', []):
        dt_txt = item.get('dt_txt', '')
        if target_date in dt_txt:
            main = item.get('main', {})
            temp_c = main.get('temp')
            temp_max_c = main.get('temp_max', temp_c)
            if temp_c is not None:
                temps_f.append(c_to_f(temp_c))
            if temp_max_c is not None:
                temps_f.append(c_to_f(temp_max_c))

    distribution = compute_distribution(temps_f)
    if distribution is None:
        return None

    distribution['source'] = 'forecast'
    return distribution


def fetch_historical_openmeteo(city, target_date):
    settings = get_city_settings(city)
    if not settings:
        return None

    params = {
        'latitude': settings['latitude'],
        'longitude': settings['longitude'],
        'start_date': target_date,
        'end_date': target_date,
        'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean',
        'timezone': settings['timezone'],
    }

    try:
        response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()
    daily = data.get('daily', {})
    max_vals = daily.get('temperature_2m_max', [])
    min_vals = daily.get('temperature_2m_min', [])
    mean_vals = daily.get('temperature_2m_mean', [])

    if not max_vals:
        return None

    max_c = max_vals[0]
    min_c = min_vals[0] if min_vals else max_c
    mean_c = mean_vals[0] if mean_vals else ((max_c + min_c) / 2)

    max_f = c_to_f(max_c)
    min_f = c_to_f(min_c)
    mean_f = c_to_f(mean_c)
    std_f = max(2.0, round((max_f - min_f) / 3.0, 2))

    return {
        'mean_f': round(mean_f, 2),
        'max_f': round(max_f, 2),
        'min_f': round(min_f, 2),
        'std_f': std_f,
        'source': 'openmeteo_archive',
    }


def historical_fallback(city, dt_obj):
    settings = get_city_settings(city)
    if settings is None:
        return {
            'mean_f': 70.0,
            'max_f': 72.0,
            'min_f': 68.0,
            'std_f': 6.0,
            'source': 'historical_fallback_generic',
        }

    baseline_high = settings['monthly_high_f'].get(dt_obj.month, 70.0)
    daily_adjustment = ((dt_obj.day % 5) - 2) * 1.2
    max_f = baseline_high + daily_adjustment
    mean_f = max_f - 6.0
    min_f = mean_f - 8.0

    return {
        'mean_f': round(mean_f, 2),
        'max_f': round(max_f, 2),
        'min_f': round(min_f, 2),
        'std_f': float(settings['fallback_std_f']),
        'source': 'historical_fallback',
    }


def select_center_temp(distribution, market_type):
    if market_type == 'daily_high_temperature':
        return distribution['max_f']
    return distribution['mean_f']


def get_distribution(city, target_date, dt_obj, market_date):
    today = datetime.now(timezone.utc).date()

    if market_date >= today:
        forecast = fetch_forecast(city, target_date)
        if forecast is not None:
            return forecast
        return historical_fallback(city, dt_obj)

    historical = fetch_historical_openmeteo(city, target_date)
    if historical is not None:
        return historical

    return historical_fallback(city, dt_obj)


def estimate_probability_from_question(question):
    parsed = parse_kalshi_question(question)

    city = parsed.get('city')
    date_str = parsed.get('date')
    comparison = parsed.get('comparison')
    low = parsed.get('threshold_low')
    high = parsed.get('threshold_high')
    market_type = parsed.get('market_type')

    target_date, dt_obj = parse_date(date_str)
    if not city or not target_date or dt_obj is None:
        return {
            'predicted_temp': None,
            'std_dev': None,
            'ai_probability_yes': None,
            'source': 'missing_input',
        }

    market_date = dt_obj.date()
    distribution = get_distribution(city, target_date, dt_obj, market_date)
    center_temp = select_center_temp(distribution, market_type)
    std = distribution['std_f']

    if comparison == 'greater_than' and low is not None:
        prob = probability_greater_than(center_temp, std, low)
    elif comparison == 'less_than' and high is not None:
        prob = probability_less_than(center_temp, std, high)
    elif comparison == 'between' and low is not None and high is not None:
        prob = probability_between(center_temp, std, low, high)
    else:
        prob = 50.0

    prob = max(0.0, min(100.0, prob))

    return {
        'predicted_temp': round(center_temp, 2),
        'std_dev': round(std, 2),
        'ai_probability_yes': round(prob, 2),
        'source': distribution['source'],
    }


def test():
    examples = [
        'Will the high temp in LA be >90° on Mar 19, 2026?',
        'Will the high temp in New York be <83° on Mar 19, 2026?',
        'Will the high temp in Chicago be 73-74° on Mar 6, 2026?',
    ]

    for question in examples:
        print('=' * 80)
        print(question)
        print(estimate_probability_from_question(question))


if __name__ == '__main__':
    test()
