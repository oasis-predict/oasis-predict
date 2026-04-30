import argparse
import csv
import os
from datetime import datetime

import requests

import config
from scripts.kalshi_daily_runner import main as run_daily_pipeline
from scripts.kalshi_system_evaluator import main as run_system_evaluator
from scripts.oasis_duc_haven_weather import main as run_oasis_weather


WEATHER_CSV_FILE = 'data/weather_data.csv'
WEATHER_HEADERS = [
    'timestamp',
    'city',
    'temperature',
    'humidity',
    'pressure',
    'wind_speed',
    'clouds',
    'visibility',
    'rain',
    'weather',
]


def ensure_weather_csv_exists(path=WEATHER_CSV_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        return

    with open(path, 'w', newline='', encoding='utf-8') as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(WEATHER_HEADERS)


def fetch_current_weather(city):
    if not config.API_KEY:
        raise RuntimeError('OPENWEATHER_API_KEY is missing. Add it to your .env file.')

    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': config.API_KEY,
        'units': 'metric',
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'city': city,
        'temperature': data['main']['temp'],
        'humidity': data['main']['humidity'],
        'pressure': data['main']['pressure'],
        'wind_speed': data['wind']['speed'],
        'clouds': data['clouds']['all'],
        'visibility': data.get('visibility', 0),
        'rain': data.get('rain', {}).get('1h', 0),
        'weather': data['weather'][0]['description'],
    }


def collect_weather_snapshot(cities=None):
    cities = cities or config.CITIES
    ensure_weather_csv_exists()

    rows = []
    for city in cities:
        snapshot = fetch_current_weather(city)
        rows.append(snapshot)
        print(city, snapshot['temperature'], snapshot['humidity'], snapshot['wind_speed'], snapshot['rain'])

    with open(WEATHER_CSV_FILE, 'a', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=WEATHER_HEADERS)
        writer.writerows(rows)

    print(f'Saved {len(rows)} weather row(s) to {WEATHER_CSV_FILE}')


def build_parser():
    parser = argparse.ArgumentParser(description='Weather AI Agent entrypoint')
    subparsers = parser.add_subparsers(dest='command')

    daily_parser = subparsers.add_parser('daily', help='Run the Kalshi trading daily pipeline')
    daily_parser.set_defaults(handler=lambda _args: run_daily_pipeline())

    weather_parser = subparsers.add_parser('collect-weather', help='Collect current weather snapshots')
    weather_parser.add_argument('--cities', nargs='*', help='Optional city list override')
    weather_parser.set_defaults(handler=lambda args: collect_weather_snapshot(args.cities))

    evaluate_parser = subparsers.add_parser('evaluate-system', help='Run the unified backtest/live system evaluation')
    evaluate_parser.set_defaults(handler=lambda _args: run_system_evaluator())

    oasis_parser = subparsers.add_parser('oasis-weather', help='Run Oasis__Duc_Haven_Weather high-temperature consensus')
    oasis_parser.add_argument('--city', choices=['LA', 'NYC', 'MIAMI'], help='City code: LA, NYC, or MIAMI')
    oasis_parser.add_argument('--date', help='Target date as YYYY-MM-DD')
    oasis_parser.add_argument('--question', help='Example: "Highest temperature in LA today?"')
    oasis_parser.add_argument('--json', action='store_true', help='Print raw JSON output')
    def run_oasis_from_args(args):
        oasis_args = []
        if args.city:
            oasis_args.extend(['--city', args.city])
        if args.date:
            oasis_args.extend(['--date', args.date])
        if args.question:
            oasis_args.extend(['--question', args.question])
        if args.json:
            oasis_args.append('--json')
        return run_oasis_weather(oasis_args)

    oasis_parser.set_defaults(handler=run_oasis_from_args)

    parser.set_defaults(handler=lambda _args: run_daily_pipeline())
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == '__main__':
    main()


