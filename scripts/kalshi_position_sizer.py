import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config


INPUT_FILE = 'data/kalshi_signals.csv'
OUTPUT_FILE = 'data/kalshi_sized_signals.csv'
BANKROLL_USD = getattr(config, 'STARTING_BANKROLL_USD', 1062.67)


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def should_keep_trade(row):
    action = (row.get('signal_action') or '').strip().upper()
    return action in ['BUY_YES', 'BUY_NO', 'BUY_YES_STRONG', 'BUY_NO_STRONG']


def get_risk_fraction(signal_action, confidence_label, edge):
    action = (signal_action or '').strip().upper()
    confidence = (confidence_label or '').strip().upper()
    edge_val = safe_float(edge)

    if edge_val is None:
        return 0.0

    abs_edge = abs(edge_val)

    if action in ['BUY_YES_STRONG', 'BUY_NO_STRONG']:
        return 3.0

    if confidence == 'HIGH' and abs_edge >= 10:
        return 2.0

    if confidence in ['HIGH', 'MEDIUM'] and abs_edge >= 5:
        return 1.0

    return 0.5


def calculate_recommended_notional(bankroll_usd, risk_fraction_percent):
    return round(bankroll_usd * (risk_fraction_percent / 100.0), 2)


def estimate_entry_cost(signal_action, recommended_notional_usd, yes_price_percent, no_price_percent):
    notional = safe_float(recommended_notional_usd)
    yes_price = safe_float(yes_price_percent)
    no_price = safe_float(no_price_percent)
    action = (signal_action or '').strip().upper()

    if notional is None:
        return None

    if action in ['BUY_YES', 'BUY_YES_STRONG'] and yes_price is not None:
        return round(notional * (yes_price / 100.0), 2)

    if action in ['BUY_NO', 'BUY_NO_STRONG'] and no_price is not None:
        return round(notional * (no_price / 100.0), 2)

    return None


def main():
    if not os.path.exists(INPUT_FILE):
        print('File not found:', INPUT_FILE)
        return

    rows_out = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as file_obj:
        reader = csv.DictReader(file_obj)

        for row in reader:
            if not should_keep_trade(row):
                continue

            signal_action = row.get('signal_action')
            confidence_label = row.get('confidence_label')
            edge = row.get('edge')

            risk_fraction = get_risk_fraction(signal_action, confidence_label, edge)
            recommended_notional_usd = calculate_recommended_notional(BANKROLL_USD, risk_fraction)
            estimated_entry_cost_usd = estimate_entry_cost(
                signal_action,
                recommended_notional_usd,
                row.get('yes_ask_percent'),
                row.get('no_ask_percent'),
            )

            rows_out.append({
                'ticker': row.get('ticker'),
                'title': row.get('title'),
                'comparison': row.get('comparison'),
                'threshold_low': row.get('threshold_low'),
                'threshold_high': row.get('threshold_high'),
                'predicted_temp_f': row.get('predicted_temp_f'),
                'std_dev': row.get('std_dev'),
                'consensus_temp_f': row.get('consensus_temp_f'),
                'consensus_spread_f': row.get('consensus_spread_f'),
                'consensus_ok': row.get('consensus_ok'),
                'yes_allowed': row.get('yes_allowed'),
                'range_center': row.get('range_center'),
                'distance_to_consensus': row.get('distance_to_consensus'),
                'openmeteo_temp': row.get('openmeteo_temp_f') or row.get('openmeteo_temp'),
                'noaa_temp': row.get('noaa_temp_f') or row.get('noaa_temp'),
                'nasa_monitor_temp': row.get('nasa_monitor_temp_f') or row.get('nasa_monitor_temp'),
                'signal_action': signal_action,
                'confidence_label': confidence_label,
                'ai_probability_yes': row.get('ai_probability_yes'),
                'yes_ask_percent': row.get('yes_ask_percent'),
                'no_ask_percent': row.get('no_ask_percent'),
                'edge': row.get('edge'),
                'risk_fraction_percent': risk_fraction,
                'recommended_stake_usd': recommended_notional_usd,
                'estimated_entry_cost_usd': estimated_entry_cost_usd,
            })

    rows_out.sort(
        key=lambda row: -(abs(safe_float(row['edge'])) if safe_float(row['edge']) is not None else 0.0)
    )

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as file_obj:
        fieldnames = [
            'ticker',
            'title',
            'comparison',
            'threshold_low',
            'threshold_high',
            'predicted_temp_f',
            'std_dev',
            'consensus_temp_f',
            'consensus_spread_f',
            'consensus_ok',
            'yes_allowed',
            'range_center',
            'distance_to_consensus',
            'openmeteo_temp',
            'noaa_temp',
            'nasa_monitor_temp',
            'signal_action',
            'confidence_label',
            'ai_probability_yes',
            'yes_ask_percent',
            'no_ask_percent',
            'edge',
            'risk_fraction_percent',
            'recommended_stake_usd',
            'estimated_entry_cost_usd',
        ]
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print('=' * 80)
    print('POSITION SIZING COMPLETE')
    print('=' * 80)
    print('Trades sized :', len(rows_out))
    print(f'Saved to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
