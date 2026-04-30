import csv
import os
from collections import defaultdict
from statistics import mean


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

BACKTEST_FILE = os.path.join(DATA_DIR, 'kalshi_backtest_directional.csv')
LIVE_TRACKER_FILE = os.path.join(DATA_DIR, 'kalshi_strategy_live_tracker.csv')
EXECUTED_TRADES_FILE = os.path.join(DATA_DIR, 'executed_trades.csv')
CALIBRATION_OUTPUT_FILE = os.path.join(DATA_DIR, 'kalshi_probability_calibration.csv')
SEGMENT_OUTPUT_FILE = os.path.join(DATA_DIR, 'kalshi_segment_performance.csv')
REPORT_OUTPUT_FILE = os.path.join(DATA_DIR, 'kalshi_system_eval_report.txt')

CALIBRATION_BUCKETS = [(start, start + 10) for start in range(0, 100, 10)]


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def load_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as file_obj:
        return list(csv.DictReader(file_obj))


def infer_city(row):
    city = (row.get('city') or '').strip()
    if city:
        return city
    title = (row.get('title') or '').upper()
    if 'LOS ANGELES' in title or ' IN LA' in title:
        return 'Los Angeles'
    if 'NYC' in title or 'NEW YORK' in title:
        return 'New York'
    if 'CHICAGO' in title:
        return 'Chicago'
    return 'Unknown'


def normalize_action(value):
    action = (value or '').strip().upper()
    return action or None


def normalize_backtest_action(row):
    direction = (row.get('predicted_direction') or '').strip().upper()
    if direction == 'YES':
        return 'BUY_YES'
    if direction == 'NO':
        return 'BUY_NO'
    return None


def normalize_success_from_result(value):
    result = (value or '').strip().upper()
    if result in ['WIN', 'WON']:
        return 1
    if result in ['LOSS', 'LOST']:
        return 0
    return None


def compute_brier_score(prob_yes_pct, resolved_outcome):
    prob = safe_float(prob_yes_pct)
    outcome = (resolved_outcome or '').strip().upper()
    if prob is None or outcome not in ['YES', 'NO']:
        return None
    observed = 1.0 if outcome == 'YES' else 0.0
    forecast = max(0.0, min(1.0, prob / 100.0))
    return (forecast - observed) ** 2


def compute_entry_cost(action, yes_ask_percent, no_ask_percent=None):
    action = normalize_action(action)
    yes_ask = safe_float(yes_ask_percent)
    no_ask = safe_float(no_ask_percent)
    if action is None:
        return None
    if action.startswith('BUY_YES'):
        return yes_ask
    if no_ask is not None:
        return no_ask
    if yes_ask is not None:
        return round(100.0 - yes_ask, 2)
    return None


def compute_theoretical_pnl(action, yes_ask_percent, no_ask_percent, success):
    entry_cost = compute_entry_cost(action, yes_ask_percent, no_ask_percent)
    if entry_cost is None or success is None:
        return None
    return round(100.0 - entry_cost, 2) if success == 1 else round(-entry_cost, 2)


def compute_selected_edge(action, ai_probability_yes, yes_ask_percent, no_ask_percent):
    action = normalize_action(action)
    ai_prob_yes = safe_float(ai_probability_yes)
    yes_ask = safe_float(yes_ask_percent)
    no_ask = safe_float(no_ask_percent)
    if action is None or ai_prob_yes is None:
        return None
    if action.startswith('BUY_YES') and yes_ask is not None:
        return round(ai_prob_yes - yes_ask, 2)
    if action.startswith('BUY_NO'):
        ai_prob_no = 100.0 - ai_prob_yes
        if no_ask is not None:
            return round(ai_prob_no - no_ask, 2)
        if yes_ask is not None:
            return round(ai_prob_no - (100.0 - yes_ask), 2)
    return None


def disciplined_filter(row):
    action = normalize_action(row.get('action'))
    comparison = (row.get('comparison') or '').strip().lower()
    return action in ['BUY_NO', 'BUY_NO_STRONG'] and comparison in ['between', 'less_than']


def ultra_precision_filter(row):
    action = normalize_action(row.get('action'))
    comparison = (row.get('comparison') or '').strip().lower()
    ai_probability_yes = safe_float(row.get('ai_probability_yes'))
    yes_ask_percent = safe_float(row.get('yes_ask_percent'))
    return (
        action in ['BUY_NO', 'BUY_NO_STRONG']
        and comparison == 'between'
        and ai_probability_yes is not None and ai_probability_yes <= 5.0
        and yes_ask_percent is not None and yes_ask_percent <= 20.0
    )


def to_metric_row(source, raw_row, action, success, pnl_usd, ai_probability_yes=None, yes_ask_percent=None, no_ask_percent=None):
    metric = {
        'source': source,
        'ticker': raw_row.get('ticker'),
        'title': raw_row.get('title'),
        'city': infer_city(raw_row),
        'comparison': (raw_row.get('comparison') or '').strip().lower() or 'unknown',
        'action': action,
        'success': success,
        'pnl': pnl_usd,
        'ai_probability_yes': safe_float(ai_probability_yes),
        'yes_ask_percent': safe_float(yes_ask_percent),
        'no_ask_percent': safe_float(no_ask_percent),
    }
    metric['edge'] = compute_selected_edge(action, ai_probability_yes, yes_ask_percent, no_ask_percent)
    return metric


def build_backtest_metrics(rows):
    metrics, calibration_rows = [], []
    for row in rows:
        action = normalize_backtest_action(row)
        success = normalize_success_from_result(row.get('result'))
        metrics.append(to_metric_row('backtest', row, action, success, compute_theoretical_pnl(action, row.get('yes_ask_percent'), row.get('no_ask_percent'), success), row.get('ai_probability_yes'), row.get('yes_ask_percent'), row.get('no_ask_percent')))
        calibration_rows.append({'ticker': row.get('ticker'), 'city': infer_city(row), 'comparison': (row.get('comparison') or '').strip().lower() or 'unknown', 'ai_probability_yes': safe_float(row.get('ai_probability_yes')), 'resolved_outcome': (row.get('resolved_outcome') or '').strip().upper(), 'brier_score': compute_brier_score(row.get('ai_probability_yes'), row.get('resolved_outcome'))})
    return metrics, calibration_rows


def build_live_tracker_metrics(rows):
    return [to_metric_row('live_tracker', row, row.get('signal_action'), normalize_success_from_result(row.get('trade_result')), safe_float(row.get('pnl_amount'))) for row in rows]


def build_executed_trade_metrics(rows):
    metrics = []
    for row in rows:
        status = (row.get('settlement_status') or '').strip().upper()
        if status not in ['WON', 'LOST']:
            continue
        metrics.append(to_metric_row('executed_trades', row, row.get('signal_action'), 1 if status == 'WON' else 0, safe_float(row.get('realized_pnl_usd')), row.get('ai_probability_yes'), row.get('yes_price_percent'), row.get('no_price_percent')))
    return metrics


def summarize_rows(rows):
    resolved = [row for row in rows if row.get('success') is not None]
    pnl_values = [row['pnl'] for row in resolved if row.get('pnl') is not None]
    edges = [row['edge'] for row in resolved if row.get('edge') is not None]
    wins = sum(1 for row in resolved if row['success'] == 1)
    losses = sum(1 for row in resolved if row['success'] == 0)
    total = len(resolved)
    return {'trades': total, 'wins': wins, 'losses': losses, 'win_rate_pct': round((wins / total) * 100.0, 2) if total else None, 'avg_pnl': round(mean(pnl_values), 2) if pnl_values else None, 'total_pnl': round(sum(pnl_values), 2) if pnl_values else None, 'avg_edge': round(mean(edges), 2) if edges else None}


def calibration_bucket_label(probability):
    if probability is None:
        return None
    for start, end in CALIBRATION_BUCKETS:
        if start <= probability < end or (end == 100 and probability <= 100):
            return f'{start:02d}-{end:02d}'
    return None


def build_calibration_summary(rows):
    bucket_map = defaultdict(list)
    for row in rows:
        probability = row.get('ai_probability_yes')
        brier_score = row.get('brier_score')
        outcome = row.get('resolved_outcome')
        if probability is None or outcome not in ['YES', 'NO']:
            continue
        bucket_map[calibration_bucket_label(probability)].append((probability, outcome, brier_score))
    summary_rows = []
    for bucket in sorted(bucket_map.keys()):
        values = bucket_map[bucket]
        avg_forecast_yes = mean(prob for prob, _, _ in values)
        realized_yes_rate = mean(1.0 if outcome == 'YES' else 0.0 for _, outcome, _ in values) * 100.0
        avg_brier = mean(score for _, _, score in values if score is not None)
        summary_rows.append({'bucket': bucket, 'count': len(values), 'avg_forecast_yes_pct': round(avg_forecast_yes, 2), 'realized_yes_rate_pct': round(realized_yes_rate, 2), 'calibration_gap_pct': round(avg_forecast_yes - realized_yes_rate, 2), 'avg_brier_score': round(avg_brier, 4)})
    return summary_rows


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_segment_rows(source_name, rows):
    segment_rows = []
    segment_definitions = {'all': lambda row: True, 'disciplined': disciplined_filter, 'high_precision': ultra_precision_filter}
    groupers = {'overall': lambda row: 'ALL', 'city': lambda row: row.get('city') or 'Unknown', 'comparison': lambda row: row.get('comparison') or 'unknown', 'action': lambda row: row.get('action') or 'UNKNOWN'}
    for segment_name, segment_filter in segment_definitions.items():
        filtered = [row for row in rows if segment_filter(row) and row.get('success') is not None]
        for group_name, grouper in groupers.items():
            grouped = defaultdict(list)
            for row in filtered:
                grouped[grouper(row)].append(row)
            for key, group_rows in grouped.items():
                segment_rows.append({'source': source_name, 'segment': segment_name, 'group_type': group_name, 'group_key': key, **summarize_rows(group_rows)})
    return segment_rows


def format_summary_line(label, summary):
    if summary['trades'] == 0:
        return f'{label}: no resolved rows'
    return f"{label}: trades={summary['trades']}, win_rate={summary['win_rate_pct']}%, avg_pnl={summary['avg_pnl']}, total_pnl={summary['total_pnl']}, avg_edge={summary['avg_edge']}"


def build_verdict(backtest_all, backtest_disciplined, backtest_precision, live_all):
    notes = []
    notes.append('Le backtest brut est positif.' if (backtest_all['avg_pnl'] or 0) > 0 else 'Le backtest brut n est pas encore convaincant.')
    if backtest_precision['trades']:
        notes.append(f"Le mode high_precision monte le win rate backtest a {backtest_precision['win_rate_pct']}% sur {backtest_precision['trades']} trades.")
    else:
        notes.append('Le mode high_precision est trop strict pour produire des trades dans cet echantillon.')
    if backtest_disciplined['trades'] and backtest_all['trades']:
        better = (backtest_disciplined['avg_pnl'] or -999) >= (backtest_all['avg_pnl'] or -999)
        notes.append('Le filtre discipline semble ameliorer ou au moins preserver la qualite moyenne des signaux.' if better else 'Le filtre discipline degrade les resultats moyens dans les donnees actuelles.')
    notes.append('Le live disponible est positif, mais l echantillon reste petit.' if (live_all['total_pnl'] or 0) > 0 else 'Le live disponible n est pas encore positif ou manque de taille d echantillon.')
    return notes


def main():
    backtest_rows = load_csv_rows(BACKTEST_FILE)
    live_tracker_rows = load_csv_rows(LIVE_TRACKER_FILE)
    executed_trade_rows = load_csv_rows(EXECUTED_TRADES_FILE)
    backtest_metrics, calibration_rows = build_backtest_metrics(backtest_rows)
    live_tracker_metrics = build_live_tracker_metrics(live_tracker_rows)
    executed_trade_metrics = build_executed_trade_metrics(executed_trade_rows)
    calibration_summary = build_calibration_summary(calibration_rows)
    segment_rows = build_segment_rows('backtest', backtest_metrics) + build_segment_rows('live_tracker', live_tracker_metrics) + build_segment_rows('executed_trades', executed_trade_metrics)
    write_csv(CALIBRATION_OUTPUT_FILE, calibration_summary, ['bucket', 'count', 'avg_forecast_yes_pct', 'realized_yes_rate_pct', 'calibration_gap_pct', 'avg_brier_score'])
    write_csv(SEGMENT_OUTPUT_FILE, segment_rows, ['source', 'segment', 'group_type', 'group_key', 'trades', 'wins', 'losses', 'win_rate_pct', 'avg_pnl', 'total_pnl', 'avg_edge'])
    backtest_all = summarize_rows([row for row in backtest_metrics if row.get('success') is not None])
    backtest_disciplined = summarize_rows([row for row in backtest_metrics if disciplined_filter(row) and row.get('success') is not None])
    backtest_precision = summarize_rows([row for row in backtest_metrics if ultra_precision_filter(row) and row.get('success') is not None])
    live_tracker_all = summarize_rows([row for row in live_tracker_metrics if row.get('success') is not None])
    executed_trades_all = summarize_rows([row for row in executed_trade_metrics if row.get('success') is not None])
    avg_brier = round(mean([row['avg_brier_score'] for row in calibration_summary]), 4) if calibration_summary else None
    avg_abs_gap = round(mean([abs(row['calibration_gap_pct']) for row in calibration_summary]), 2) if calibration_summary else None
    report_lines = ['KALSHI SYSTEM EVALUATION', '=' * 80, format_summary_line('Backtest all', backtest_all), format_summary_line('Backtest disciplined', backtest_disciplined), format_summary_line('Backtest high_precision', backtest_precision), format_summary_line('Live tracker', live_tracker_all), format_summary_line('Executed trades', executed_trades_all), '', f'Calibration buckets: {len(calibration_summary)}', f'Average brier score: {avg_brier}', f'Average absolute calibration gap: {avg_abs_gap}', '', 'Verdict:']
    report_lines.extend(f'- {note}' for note in build_verdict(backtest_all, backtest_disciplined, backtest_precision, executed_trades_all))
    with open(REPORT_OUTPUT_FILE, 'w', encoding='utf-8') as file_obj:
        file_obj.write('\n'.join(report_lines) + '\n')
    print('\n'.join(report_lines))
    print('')
    print(f'Calibration report saved to {CALIBRATION_OUTPUT_FILE}')
    print(f'Segment report saved to {SEGMENT_OUTPUT_FILE}')
    print(f'Summary report saved to {REPORT_OUTPUT_FILE}')


if __name__ == '__main__':
    main()
