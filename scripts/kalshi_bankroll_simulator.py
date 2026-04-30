import csv

FILE = "data/kalshi_strategy_live_tracker.csv"
INITIAL_BANKROLL = 1000.0

MAX_CONSECUTIVE_LOSSES = 3
DRAWDOWN_WARNING_PERCENT = 5.0
DRAWDOWN_STOP_PERCENT = 10.0


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def base_risk_fraction(action, confidence_label):
    action = (action or "").strip().upper()
    confidence_label = (confidence_label or "").strip().upper()

    if action in ["BUY_YES_STRONG", "BUY_NO_STRONG"] and confidence_label == "HIGH":
        return 0.03
    if confidence_label == "HIGH":
        return 0.02
    if confidence_label == "MEDIUM":
        return 0.01
    return 0.005


def adjusted_risk_fraction(base_risk, current_drawdown_percent):
    if current_drawdown_percent >= DRAWDOWN_STOP_PERCENT:
        return 0.0
    if current_drawdown_percent >= DRAWDOWN_WARNING_PERCENT:
        return base_risk * 0.5
    return base_risk


def calculate_pnl(action, yes_price, outcome, stake):
    yes_price = safe_float(yes_price)

    if yes_price is None:
        return 0.0

    action = (action or "").strip().upper()
    outcome = (outcome or "").strip().upper()

    if action in ["BUY_YES", "BUY_YES_STRONG"]:
        if outcome == "YES":
            return stake * ((100 - yes_price) / 100)
        if outcome == "NO":
            return -stake

    if action in ["BUY_NO", "BUY_NO_STRONG"]:
        no_price = 100 - yes_price
        if outcome == "NO":
            return stake * ((100 - no_price) / 100)
        if outcome == "YES":
            return -stake

    return 0.0


def main():
    bankroll = INITIAL_BANKROLL
    peak_bankroll = INITIAL_BANKROLL
    consecutive_losses = 0
    trades = 0

    print("=" * 80)
    print("BANKROLL SIMULATION V5 (CLEAN)")
    print("=" * 80)

    with open(FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            outcome = (r.get("resolved_outcome") or "").strip().upper()
            if outcome not in ["YES", "NO"]:
                continue

            if bankroll > peak_bankroll:
                peak_bankroll = bankroll

            current_drawdown = ((peak_bankroll - bankroll) / peak_bankroll) * 100 if peak_bankroll > 0 else 0.0

            if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                print("STOP: losing streak")
                break

            base_risk = base_risk_fraction(r.get("signal_action"), r.get("confidence_label"))
            risk = adjusted_risk_fraction(base_risk, current_drawdown)

            if risk == 0.0:
                print("STOP: drawdown limit reached BEFORE trade")
                break

            stake = bankroll * risk
            pnl = calculate_pnl(r.get("signal_action"), r.get("yes_ask_percent"), outcome, stake)

            bankroll += pnl
            trades += 1

            if pnl < 0:
                consecutive_losses += 1
            else:
                consecutive_losses = 0

            if bankroll > peak_bankroll:
                peak_bankroll = bankroll

            current_drawdown = ((peak_bankroll - bankroll) / peak_bankroll) * 100 if peak_bankroll > 0 else 0.0

            if current_drawdown >= DRAWDOWN_STOP_PERCENT:
                print("STOP: drawdown exceeded AFTER trade")
                print("Drawdown %:", round(current_drawdown, 2))
                break

            print("-" * 80)
            print("Ticker:", r.get("ticker"))
            print("PnL:", round(pnl, 2))
            print("Bankroll:", round(bankroll, 2))
            print("Drawdown %:", round(current_drawdown, 2))

    print("=" * 80)
    print("FINAL")
    print("=" * 80)
    print("Final bankroll:", round(bankroll, 2))
    print("Total trades:", trades)
    print("Max drawdown %:", round(((peak_bankroll - bankroll) / peak_bankroll) * 100, 2))


if __name__ == "__main__":
    main()
