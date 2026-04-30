def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def normalize_action(action):
    return (action or '').strip().upper()


def normalize_comparison(comparison):
    return (comparison or '').strip().lower()


def balanced_filter(row):
    action = normalize_action(row.get('signal_action') or row.get('action'))
    comparison = normalize_comparison(row.get('comparison'))
    edge = abs(safe_float(row.get('edge')) or 0.0)
    day_offset = row.get('day_offset')
    is_expired = bool(row.get('is_expired'))
    is_frozen = bool(row.get('is_frozen_market'))
    is_los_angeles = bool(row.get('is_los_angeles_trade'))

    if is_expired or is_frozen:
        return False
    if action in ['BUY_YES', 'BUY_YES_STRONG']:
        return False
    if comparison == 'greater_than':
        return False
    if action not in ['BUY_NO', 'BUY_NO_STRONG']:
        return False
    if comparison not in ['between', 'less_than']:
        return False
    if day_offset == 0 and edge < 15:
        return False
    if is_los_angeles and action != 'BUY_NO_STRONG':
        return False
    return True


def high_precision_filter(row):
    action = normalize_action(row.get('signal_action') or row.get('action'))
    comparison = normalize_comparison(row.get('comparison'))
    ai_probability_yes = safe_float(row.get('ai_probability_yes'))
    yes_ask_percent = safe_float(row.get('yes_ask_percent'))
    day_offset = row.get('day_offset')
    is_expired = bool(row.get('is_expired'))
    is_frozen = bool(row.get('is_frozen_market'))

    if is_expired or is_frozen:
        return False
    if action not in ['BUY_NO', 'BUY_NO_STRONG']:
        return False
    if comparison != 'between':
        return False
    if ai_probability_yes is None or ai_probability_yes > 5.0:
        return False
    if yes_ask_percent is None or yes_ask_percent > 20.0:
        return False
    if day_offset not in [0, 1, 2]:
        return False
    return True


def passes_selection_mode(row, mode):
    if mode == 'high_precision':
        return high_precision_filter(row)
    return balanced_filter(row)
