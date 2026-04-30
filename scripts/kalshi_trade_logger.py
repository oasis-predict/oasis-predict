import csv
import os
from datetime import datetime


TRADE_SHEET_FILE = 'data/kalshi_trade_sheet.csv'
TRADE_LOG_FILE = 'data/executed_trades.csv'


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def ensure_trade_log_exists():
    if os.path.exists(TRADE_LOG_FILE):
        return

    with open(TRADE_LOG_FILE, 'w', newline='', encoding='utf-8') as file_obj:
        fieldnames = [
            'logged_at',
            'ticker',
            'title',
            'comparison',
            'signal_action',
            'priority',
            'ai_probability_yes',
            'yes_price_percent',
            'no_price_percent',
            'selected_side_price_percent',
            'edge',
            'recommended_stake_usd',
            'contracts_target',
            'estimated_entry_cost_usd',
            'execution_status',
            'real_fill_price_percent',
            'contracts_bought',
            'real_cost_usd',
            'settlement_status',
            'realized_pnl_usd',
            'notes',
        ]
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()


def load_trade_sheet():
    if not os.path.exists(TRADE_SHEET_FILE):
        print('File not found:', TRADE_SHEET_FILE)
        return []

    with open(TRADE_SHEET_FILE, 'r', encoding='utf-8') as file_obj:
        return list(csv.DictReader(file_obj))


def find_trade_by_ticker(rows, ticker):
    for row in rows:
        if (row.get('ticker') or '').strip().upper() == ticker.strip().upper():
            return row
    return None


def get_selected_side_price_percent(row):
    action = (row.get('signal_action') or '').strip().upper()

    if action in ['BUY_NO', 'BUY_NO_STRONG']:
        return safe_float(row.get('no_price_percent'))

    return safe_float(row.get('yes_price_percent'))


def append_trade_log(row):
    ensure_trade_log_exists()

    recommended_notional_usd = round(safe_float(row.get('recommended_stake_usd')), 2)
    estimated_entry_cost_usd = safe_float(
        row.get('estimated_entry_cost_usd') or row.get('estimated_trade_cost_usd')
    )
    selected_side_price_percent = round(get_selected_side_price_percent(row), 2)
    contracts_target = recommended_notional_usd

    out = {
        'logged_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ticker': row.get('ticker'),
        'title': row.get('title'),
        'comparison': row.get('comparison'),
        'signal_action': row.get('signal_action'),
        'priority': row.get('priority'),
        'ai_probability_yes': row.get('ai_probability_yes'),
        'yes_price_percent': row.get('yes_price_percent'),
        'no_price_percent': row.get('no_price_percent'),
        'selected_side_price_percent': selected_side_price_percent,
        'edge': row.get('edge'),
        'recommended_stake_usd': recommended_notional_usd,
        'contracts_target': contracts_target,
        'estimated_entry_cost_usd': round(estimated_entry_cost_usd, 2),
        'execution_status': 'PLANNED',
        'real_fill_price_percent': '',
        'contracts_bought': contracts_target,
        'real_cost_usd': round(estimated_entry_cost_usd, 2),
        'settlement_status': 'OPEN',
        'realized_pnl_usd': '',
        'notes': '',
    }

    with open(TRADE_LOG_FILE, 'a', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=out.keys())
        writer.writerow(out)


def main():
    rows = load_trade_sheet()
    if not rows:
        print('No trade sheet rows found.')
        return

    ticker = input('Ticker to log from trade sheet: ').strip()
    row = find_trade_by_ticker(rows, ticker)

    if row is None:
        print('Ticker not found in trade sheet.')
        return

    append_trade_log(row)
    print('Trade logged to', TRADE_LOG_FILE)


if __name__ == '__main__':
    main()
