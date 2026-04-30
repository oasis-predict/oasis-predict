import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / '.env'


DEFAULT_COLLECTION_CITIES = [
    'New York,US',
    'Seattle,US',
    'Chicago,US',
    'Dallas,US',
    'Tokyo,JP',
    'Toronto,CA',
    'Singapore,SG',
    'London,GB',
    'Seoul,KR',
    'Paris,FR',
]

TRADING_CITIES = [
    'Los Angeles',
    'New York',
    'Miami',
]

VALID_TRADE_SELECTION_MODES = {'balanced', 'high_precision'}


def load_dotenv(path=ENV_FILE):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()

        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"\'')

        if key and key not in os.environ:
            os.environ[key] = value


def get_env_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_env_list(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    return [item.strip() for item in value.split(',') if item.strip()]


def get_trade_selection_mode(default='balanced'):
    value = (os.getenv('TRADE_SELECTION_MODE') or default).strip().lower()
    if value not in VALID_TRADE_SELECTION_MODES:
        return default
    return value


load_dotenv()

API_KEY = os.getenv('OPENWEATHER_API_KEY') or os.getenv('API_KEY')
STARTING_BANKROLL_USD = get_env_float('STARTING_BANKROLL_USD', 1062.67)
CITIES = get_env_list('WEATHER_COLLECTION_CITIES', DEFAULT_COLLECTION_CITIES)
TRADE_SELECTION_MODE = get_trade_selection_mode()

