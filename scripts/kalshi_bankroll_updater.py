import csv
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config


TRADE_LOG_FILE = 'data/executed_trades.csv'
BANKROLL_FILE = 'data/bankroll.csv'
STARTING_BANKROLL = getattr(config, 'STARTING_BANKROLL_USD', 1062.67)
BANKROLL_FIELDS = [
    'timestamp',
    'starting_bankroll_usd',
    'open_notional_usd',
    'open_entry_cost_usd',
    'realized_pnl_usd',
    'available_bankroll_usd',
    'account_equity_usd',
    'current_bankroll_usd',
]
OLD_BANKROLL_FIELDS = [
    'timestamp',
    'starting_bankroll_usd',
    'open_trade_cost_usd',
    'realized_pnl_usd',
    'current_bankroll_usd',
]


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def load_trade_log():
    if not os.path.exists(TRADE_LOG_FILE):
        return []

    with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as file_obj:
        return list(csv.DictReader(file_obj))


def normalize_bankroll_file():
    if not os.path.exists(BANKROLL_FILE):
        return []

    with open(BANKROLL_FILE, 'r', encoding='utf-8') as file_obj:
        raw_rows = list(csv.reader(file_obj))

    if not raw_rows:
        return []

    header = raw_rows[0]
    data_rows = raw_rows[1:]
    normalized = []

    for row in data_rows:
        if not row:
            continue

        if len(row) >= len(BANKROLL_FIELDS):
            available_bankroll_usd = safe_float(row[5])
            open_entry_cost_usd = safe_float(row[3])
            normalized.append({
                'timestamp': row[0],
                'starting_bankroll_usd': round(safe_float(row[1]), 2),
                'open_notional_usd': round(safe_float(row[2]), 2),
                'open_entry_cost_usd': round(open_entry_cost_usd, 2),
                'realized_pnl_usd': round(safe_float(row[4]), 2),
                'available_bankroll_usd': round(available_bankroll_usd, 2),
                'account_equity_usd': round(safe_float(row[6]), 2),
                'current_bankroll_usd': round(safe_float(row[7]), 2),
            })
            continue

        if len(row) >= len(OLD_BANKROLL_FIELDS):
            open_entry_cost_usd = safe_float(row[2])
            realized_pnl_usd = safe_float(row[3])
            current_bankroll_usd = safe_float(row[4])
            normalized.append({
                'timestamp': row[0],
                'starting_bankroll_usd': round(safe_float(row[1]), 2),
                'open_notional_usd': 0.0,
                'open_entry_cost_usd': round(open_entry_cost_usd, 2),
                'realized_pnl_usd': round(realized_pnl_usd, 2),
                'available_bankroll_usd': round(current_bankroll_usd, 2),
                'account_equity_usd': round(current_bankroll_usd + open_entry_cost_usd, 2),
                'current_bankroll_usd': round(current_bankroll_usd, 2),
            })

    should_rewrite = header != BANKROLL_FIELDS or any(len(row) != len(BANKROLL_FIELDS) for row in data_rows if row)
    if should_rewrite:
        with open(BANKROLL_FILE, 'w', newline='', encoding='utf-8') as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=BANKROLL_FIELDS)
            writer.writeheader()
            writer.writerows(normalized)

    return normalized


def ensure_bankroll_file_exists():
    if os.path.exists(BANKROLL_FILE):
        normalize_bankroll_file()
        return

    with open(BANKROLL_FILE, 'w', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=BANKROLL_FIELDS)
        writer.writeheader()


def compute_bankroll_snapshot(trades):
    open_notional_usd = 0.0
    open_entry_cost_usd = 0.0
    realized_pnl_usd = 0.0

    for row in trades:
        settlement_status = (row.get('settlement_status') or '').strip().upper()
        recommended_notional = safe_float(row.get('recommended_stake_usd'))
        entry_cost = safe_float(row.get('real_cost_usd') or row.get('estimated_entry_cost_usd'))
        realized_pnl = safe_float(row.get('realized_pnl_usd'))

        if settlement_status == 'OPEN':
            open_notional_usd += recommended_notional
            open_entry_cost_usd += entry_cost
        elif settlement_status in ['WON', 'LOST', 'SETTLED']:
            realized_pnl_usd += realized_pnl

    available_bankroll_usd = STARTING_BANKROLL + realized_pnl_usd - open_entry_cost_usd
    account_equity_usd = STARTING_BANKROLL + realized_pnl_usd

    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'starting_bankroll_usd': round(STARTING_BANKROLL, 2),
        'open_notional_usd': round(open_notional_usd, 2),
        'open_entry_cost_usd': round(open_entry_cost_usd, 2),
        'realized_pnl_usd': round(realized_pnl_usd, 2),
        'available_bankroll_usd': round(available_bankroll_usd, 2),
        'account_equity_usd': round(account_equity_usd, 2),
        'current_bankroll_usd': round(available_bankroll_usd, 2),
    }


def append_bankroll_snapshot(snapshot):
    ensure_bankroll_file_exists()

    with open(BANKROLL_FILE, 'a', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=BANKROLL_FIELDS)
        writer.writerow(snapshot)


def main():
    trades = load_trade_log()
    snapshot = compute_bankroll_snapshot(trades)
    append_bankroll_snapshot(snapshot)

    print('=' * 80)
    print('BANKROLL UPDATED')
    print('=' * 80)
    print('Open notional     :', snapshot['open_notional_usd'])
    print('Open entry cost   :', snapshot['open_entry_cost_usd'])
    print('Realized PnL      :', snapshot['realized_pnl_usd'])
    print('Available bankroll:', snapshot['available_bankroll_usd'])
    print('Account equity    :', snapshot['account_equity_usd'])
    print(f'Saved to {BANKROLL_FILE}')


if __name__ == '__main__':
    main()
