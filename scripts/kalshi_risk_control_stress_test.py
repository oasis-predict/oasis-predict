INITIAL_BANKROLL = 1000.0

MAX_CONSECUTIVE_LOSSES = 3
DRAWDOWN_WARNING_PERCENT = 5.0
DRAWDOWN_STOP_PERCENT = 10.0

TEST_TRADES = [
    {"ticker": "TEST-1", "action": "BUY_YES", "confidence": "HIGH", "yes_price": 40, "outcome": "NO"},
    {"ticker": "TEST-2", "action": "BUY_NO", "confidence": "HIGH", "yes_price": 30, "outcome": "YES"},
    {"ticker": "TEST-3", "action": "BUY_YES_STRONG", "confidence": "HIGH", "yes_price": 50, "outcome": "NO"},
    {"ticker": "TEST-4", "action": "BUY_NO", "confidence": "MEDIUM", "yes_price": 20, "outcome": "YES"},
    {"ticker": "TEST-5", "action": "BUY_NO_STRONG", "confidence": "HIGH", "yes_price": 35, "outcome": "YES"},
    {"ticker": "TEST-6", "action": "BUY_YES", "confidence": "HIGH", "yes_price": 25, "outcome": "YES"},
]


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

    print("=" * 80)
    print("RISK CONTROL STRESS TEST")
    print("=" * 80)

    for trade in TEST_TRADES:
        if bankroll > peak_bankroll:
            peak_bankroll = bankroll

        drawdown_pct = ((peak_bankroll - bankroll) / peak_bankroll) * 100 if peak_bankroll > 0 else 0.0

        if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            print("-" * 80)
            print("STOP: paused by losing streak")
            print("Consecutive losses:", consecutive_losses)
            break

        base_risk = base_risk_fraction(trade["action"], trade["confidence"])
        risk = adjusted_risk_fraction(base_risk, drawdown_pct)

        if risk == 0.0:
            print("-" * 80)
            print("STOP: max drawdown reached")
            print("Drawdown %:", round(drawdown_pct, 2))
            break

        stake = bankroll * risk
        pnl = calculate_pnl(trade["action"], trade["yes_price"], trade["outcome"], stake)
        bankroll += pnl

        if pnl < 0:
            consecutive_losses += 1
        else:
            consecutive_losses = 0

        if bankroll > peak_bankroll:
            peak_bankroll = bankroll

        drawdown_pct = ((peak_bankroll - bankroll) / peak_bankroll) * 100 if peak_bankroll > 0 else 0.0

        print("-" * 80)
        print("Ticker             :", trade["ticker"])
        print("Action             :", trade["action"])
        print("Confidence         :", trade["confidence"])
        print("Base risk %        :", round(base_risk * 100, 2))
        print("Adjusted risk %    :", round(risk * 100, 2))
        print("Stake              :", round(stake, 2))
        print("Outcome            :", trade["outcome"])
        print("PnL                :", round(pnl, 2))
        print("Bankroll           :", round(bankroll, 2))
        print("Drawdown %         :", round(drawdown_pct, 2))
        print("Consecutive losses :", consecutive_losses)

        print("=" * 80)
    print("FINAL STRESS TEST SUMMARY")
    print("=" * 80)
    print("Initial bankroll :", INITIAL_BANKROLL)
    print("Final bankroll   :", round(bankroll, 2))
    print("Peak bankroll    :", round(peak_bankroll, 2))
    print("Drawdown %       :", round(((peak_bankroll - bankroll) / peak_bankroll) * 100, 2) if peak_bankroll > 0 else 0.0)
    print("Loss streak      :", consecutive_losses)


if __name__ == "__main__":
    main()
