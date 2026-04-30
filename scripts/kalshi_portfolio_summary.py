import csv
import os


TRADE_LOG_FILE = 'data/executed_trades.csv'
BANKROLL_FILE = 'data/bankroll.csv'


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def load_csv_rows(path):
    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8') as file_obj:
        return list(csv.DictReader(file_obj))


def get_latest_bankroll(rows):
    if not rows:
        return None
    return rows[-1]


def main():
    trade_rows = load_csv_rows(TRADE_LOG_FILE)
    bankroll_rows = load_csv_rows(BANKROLL_FILE)

    if not trade_rows:
        print('No executed trades found.')
        return

    open_count = 0
    won_count = 0
    lost_count = 0
    settled_count = 0

    realized_pnl_total = 0.0
    open_notional_total = 0.0
    open_entry_cost_total = 0.0

    for row in trade_rows:
        settlement_status = (row.get('settlement_status') or '').strip().upper()
        recommended_notional = safe_float(row.get('recommended_stake_usd'))
        entry_cost = safe_float(row.get('real_cost_usd') or row.get('estimated_entry_cost_usd'))
        realized_pnl = safe_float(row.get('realized_pnl_usd'))

        if settlement_status == 'OPEN':
            open_count += 1
            open_notional_total += recommended_notional
            open_entry_cost_total += entry_cost
        elif settlement_status == 'WON':
            won_count += 1
            settled_count += 1
            realized_pnl_total += realized_pnl
        elif settlement_status == 'LOST':
            lost_count += 1
            settled_count += 1
            realized_pnl_total += realized_pnl
        elif settlement_status == 'SETTLED':
            settled_count += 1
            realized_pnl_total += realized_pnl

    total_logged = len(trade_rows)
    win_rate = (won_count / settled_count * 100.0) if settled_count > 0 else 0.0

    latest_bankroll = get_latest_bankroll(bankroll_rows)
    available_bankroll = None
    account_equity = None

    if latest_bankroll:
        available_bankroll = safe_float(
            latest_bankroll.get('available_bankroll_usd') or latest_bankroll.get('current_bankroll_usd')
        )
        account_equity = safe_float(latest_bankroll.get('account_equity_usd'))
        if account_equity == 0.0 and available_bankroll is not None:
            account_equity = available_bankroll + open_entry_cost_total

    print('=' * 80)
    print('KALSHI PORTFOLIO SUMMARY')
    print('=' * 80)
    print('Total logged trades    :', total_logged)
    print('Open trades            :', open_count)
    print('Won trades             :', won_count)
    print('Lost trades            :', lost_count)
    print('Settled trades         :', settled_count)
    print('Win rate %             :', round(win_rate, 2))
    print('Realized PnL total $   :', round(realized_pnl_total, 2))
    print('Open notional total $  :', round(open_notional_total, 2))
    print('Open entry cost total $:', round(open_entry_cost_total, 2))

    if available_bankroll is not None:
        print('Available bankroll $   :', round(available_bankroll, 2))
    else:
        print('Available bankroll $   : N/A')

    if account_equity is not None:
        print('Account equity $       :', round(account_equity, 2))
    else:
        print('Account equity $       : N/A')

    print('=' * 80)


if __name__ == '__main__':
    main()
