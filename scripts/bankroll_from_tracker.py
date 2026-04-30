import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config


TRACK_FILE = 'data/kalshi_strategy_live_tracker.csv'
SIZED_SIGNALS_FILE = 'data/kalshi_sized_signals.csv'
SIGNALS_FILE = 'data/kalshi_signals.csv'
TRACKER_BANKROLL_SNAPSHOT_FILE = 'data/tracker_bankroll_snapshot.csv'

DEFAULT_STARTING_BANKROLL = getattr(config, 'STARTING_BANKROLL_USD', 1000.0)
LEGACY_FIELDS = [
    'date',
    'ticker',
    'title',
    'comparison',
    'signal_action',
    'city',
    'trade_decision',
    'trade_result',
]


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def load_csv_dict(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8', newline='') as file_obj:
        return list(csv.DictReader(file_obj))


def env_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def load_tracker_rows(path):
    if not os.path.exists(path):
        print('File not found:', path)
        return None, []

    with open(path, 'r', encoding='utf-8', newline='') as file_obj:
        sample = file_obj.read(2048)
        file_obj.seek(0)
        has_header = csv.Sniffer().has_header(sample) if sample.strip() else False

        if has_header:
            rows = list(csv.DictReader(file_obj))
            rows = [row for row in rows if any((value or '').strip() for value in row.values())]
            return 'modern', rows

        rows = []
        for raw_row in csv.reader(file_obj):
            if not raw_row:
                continue
            if len(raw_row) < len(LEGACY_FIELDS):
                continue
            rows.append(dict(zip(LEGACY_FIELDS, raw_row[: len(LEGACY_FIELDS)])))
        return 'legacy', rows


def lookup_by_ticker(rows):
    data = {}
    for row in rows:
        ticker = (row.get('ticker') or '').strip().upper()
        if ticker:
            data[ticker] = row
    return data


def selected_side(action):
    action = (action or '').strip().upper()
    if action.startswith('BUY_NO'):
        return 'NO'
    if action.startswith('BUY_YES'):
        return 'YES'
    return ''


def selected_side_price_percent(action, yes_price_percent, no_price_percent):
    action = (action or '').strip().upper()
    yes_price = safe_float(yes_price_percent)
    no_price = safe_float(no_price_percent)

    if action.startswith('BUY_NO'):
        if no_price is not None:
            return no_price
        if yes_price is not None:
            return round(100.0 - yes_price, 2)
        return None

    if action.startswith('BUY_YES'):
        return yes_price

    return None


def compute_entry_cost(notional_usd, price_percent):
    notional = safe_float(notional_usd)
    price = safe_float(price_percent)
    if notional is None or price is None:
        return None
    return round(notional * (price / 100.0), 2)


def compute_realized_pnl(notional_usd, fill_price_percent, trade_result):
    notional = safe_float(notional_usd)
    fill_price = safe_float(fill_price_percent)
    result = (trade_result or '').strip().upper()

    if notional is None or fill_price is None or result not in ['WIN', 'LOSS']:
        return None

    cost = notional * (fill_price / 100.0)
    if result == 'WIN':
        return round(notional - cost, 2)
    return round(-cost, 2)


def enrich_legacy_row(row, sized_lookup, signals_lookup):
    ticker = (row.get('ticker') or '').strip().upper()
    sized = sized_lookup.get(ticker, {})
    signal = signals_lookup.get(ticker, {})

    action = row.get('signal_action') or sized.get('signal_action') or signal.get('signal_action')
    yes_price = sized.get('yes_ask_percent') or signal.get('yes_ask_percent')
    no_price = sized.get('no_ask_percent') or signal.get('no_ask_percent')
    notional = sized.get('recommended_stake_usd')
    side_price = selected_side_price_percent(action, yes_price, no_price)
    estimated_entry_cost = compute_entry_cost(notional, side_price)
    trade_result = row.get('trade_result')
    realized_pnl = compute_realized_pnl(notional, side_price, trade_result)

    return {
        'timestamp': row.get('date'),
        'ticker': row.get('ticker'),
        'title': row.get('title'),
        'comparison': row.get('comparison'),
        'signal_action': action,
        'city': row.get('city'),
        'selected_side': row.get('trade_decision') or selected_side(action),
        'yes_price_percent': yes_price,
        'no_price_percent': no_price,
        'selected_side_price_percent': side_price,
        'ai_probability_yes': sized.get('ai_probability_yes') or signal.get('ai_probability_yes'),
        'edge': sized.get('edge') or signal.get('edge'),
        'recommended_stake_usd': notional,
        'estimated_entry_cost_usd': estimated_entry_cost,
        'real_fill_price_percent': '',
        'real_entry_cost_usd': '',
        'trade_result': trade_result,
        'resolved_outcome': '',
        'realized_pnl_usd': realized_pnl,
    }


def normalize_modern_row(row):
    action = row.get('signal_action')
    yes_price = row.get('yes_price_percent') or row.get('yes_ask_percent')
    no_price = row.get('no_price_percent') or row.get('no_ask_percent')
    side_price = row.get('selected_side_price_percent') or selected_side_price_percent(action, yes_price, no_price)
    notional = row.get('recommended_stake_usd') or row.get('contracts_target')
    estimated_entry_cost = row.get('estimated_entry_cost_usd') or compute_entry_cost(notional, side_price)
    real_fill = row.get('real_fill_price_percent') or side_price
    real_entry_cost = row.get('real_entry_cost_usd') or compute_entry_cost(notional, real_fill)
    realized_pnl = row.get('realized_pnl_usd') or compute_realized_pnl(notional, real_fill, row.get('trade_result'))

    return {
        'timestamp': row.get('timestamp') or row.get('date'),
        'ticker': row.get('ticker'),
        'title': row.get('title'),
        'comparison': row.get('comparison'),
        'signal_action': action,
        'city': row.get('city'),
        'selected_side': row.get('selected_side') or selected_side(action),
        'yes_price_percent': yes_price,
        'no_price_percent': no_price,
        'selected_side_price_percent': side_price,
        'ai_probability_yes': row.get('ai_probability_yes'),
        'edge': row.get('edge'),
        'recommended_stake_usd': notional,
        'estimated_entry_cost_usd': estimated_entry_cost,
        'real_fill_price_percent': row.get('real_fill_price_percent') or '',
        'real_entry_cost_usd': real_entry_cost,
        'trade_result': row.get('trade_result'),
        'resolved_outcome': row.get('resolved_outcome') or '',
        'realized_pnl_usd': realized_pnl,
    }


def settled_result(result):
    result = (result or '').strip().upper()
    if result in ['WIN', 'LOSS']:
        return result
    return None


def summarize_rows(rows, starting_bankroll):
    open_count = 0
    wins = 0
    losses = 0
    realized_pnl_usd = 0.0
    open_entry_cost_usd = 0.0
    open_notional_usd = 0.0
    missing_cost_rows = 0

    for row in rows:
        result = settled_result(row.get('trade_result'))
        notional = safe_float(row.get('recommended_stake_usd')) or 0.0
        entry_cost = safe_float(row.get('real_entry_cost_usd'))
        if entry_cost is None:
            entry_cost = safe_float(row.get('estimated_entry_cost_usd'))
        realized_pnl = safe_float(row.get('realized_pnl_usd'))

        if result == 'WIN':
            wins += 1
            realized_pnl_usd += realized_pnl or 0.0
        elif result == 'LOSS':
            losses += 1
            realized_pnl_usd += realized_pnl or 0.0
        else:
            open_count += 1
            open_notional_usd += notional
            if entry_cost is not None:
                open_entry_cost_usd += entry_cost
            else:
                missing_cost_rows += 1

    available_bankroll = starting_bankroll + realized_pnl_usd - open_entry_cost_usd
    account_equity = starting_bankroll + realized_pnl_usd

    return {
        'starting_bankroll_usd': round(starting_bankroll, 2),
        'open_positions': open_count,
        'wins': wins,
        'losses': losses,
        'settled_trades': wins + losses,
        'open_notional_usd': round(open_notional_usd, 2),
        'open_entry_cost_usd': round(open_entry_cost_usd, 2),
        'realized_pnl_usd': round(realized_pnl_usd, 2),
        'available_bankroll_usd': round(available_bankroll, 2),
        'account_equity_usd': round(account_equity, 2),
        'missing_cost_rows': missing_cost_rows,
    }


def write_snapshot(summary):
    fieldnames = [
        'starting_bankroll_usd',
        'open_positions',
        'wins',
        'losses',
        'settled_trades',
        'open_notional_usd',
        'open_entry_cost_usd',
        'realized_pnl_usd',
        'available_bankroll_usd',
        'account_equity_usd',
        'missing_cost_rows',
    ]
    with open(TRACKER_BANKROLL_SNAPSHOT_FILE, 'w', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(summary)


def main():
    mode, tracker_rows = load_tracker_rows(TRACK_FILE)
    if mode is None:
        return

    starting_bankroll = env_float('TRACKER_STARTING_BANKROLL_USD', DEFAULT_STARTING_BANKROLL)
    sized_lookup = lookup_by_ticker(load_csv_dict(SIZED_SIGNALS_FILE))
    signals_lookup = lookup_by_ticker(load_csv_dict(SIGNALS_FILE))

    if mode == 'legacy':
        normalized_rows = [enrich_legacy_row(row, sized_lookup, signals_lookup) for row in tracker_rows]
    else:
        normalized_rows = [normalize_modern_row(row) for row in tracker_rows]

    summary = summarize_rows(normalized_rows, starting_bankroll)
    write_snapshot(summary)

    print('=' * 76)
    print('TRACKER BANKROLL')
    print('=' * 76)
    print('Tracker file          :', TRACK_FILE)
    print('Tracker mode          :', mode)
    print('Starting bankroll     :', summary['starting_bankroll_usd'])
    print('Open positions        :', summary['open_positions'])
    print('Settled trades        :', summary['settled_trades'])
    print('Wins                  :', summary['wins'])
    print('Losses                :', summary['losses'])
    print('Open notional USD     :', summary['open_notional_usd'])
    print('Open entry cost USD   :', summary['open_entry_cost_usd'])
    print('Realized PnL USD      :', summary['realized_pnl_usd'])
    print('Available bankroll    :', summary['available_bankroll_usd'])
    print('Account equity        :', summary['account_equity_usd'])
    print('Snapshot saved to     :', TRACKER_BANKROLL_SNAPSHOT_FILE)
    if summary['missing_cost_rows']:
        print('Rows without price data:', summary['missing_cost_rows'])
    print('=' * 76)


if __name__ == '__main__':
    main()
