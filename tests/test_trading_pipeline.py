import os
import sys
import unittest
from datetime import datetime
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
sys.path.append(PROJECT_ROOT)
sys.path.append(SCRIPTS_DIR)

from parse_kalshi_weather_market import parse_kalshi_question
from kalshi_probability_engine import estimate_probability_from_question, historical_fallback
from kalshi_trade_logger import get_selected_side_price_percent
from kalshi_bankroll_updater import compute_bankroll_snapshot
from kalshi_selection_rules import high_precision_filter


class TradingPipelineTests(unittest.TestCase):
    def test_parser_understands_supported_trading_cities(self):
        self.assertEqual(parse_kalshi_question('Will the high temp in LA be >80° on Apr 12, 2026?')['city'], 'Los Angeles')
        self.assertEqual(parse_kalshi_question('Will the high temp in New York be <65° on Apr 12, 2026?')['city'], 'New York')
        chicago = parse_kalshi_question('Will the high temp in Chicago be 60-61° on Apr 12, 2026?')
        self.assertEqual(chicago['city'], 'Chicago')
        self.assertEqual(chicago['comparison'], 'between')

    def test_probability_engine_supports_all_trading_cities(self):
        fake_distribution = {'mean_f': 70.0, 'max_f': 75.0, 'min_f': 61.0, 'std_f': 4.5, 'source': 'test_fixture'}
        questions = [
            'Will the high temp in LA be >80° on Apr 12, 2026?',
            'Will the high temp in New York be <65° on Apr 12, 2026?',
            'Will the high temp in Chicago be 60-61° on Apr 12, 2026?',
        ]
        with patch('kalshi_probability_engine.get_distribution', return_value=fake_distribution):
            for question in questions:
                result = estimate_probability_from_question(question)
                self.assertIsNotNone(result['predicted_temp'])
                self.assertIsNotNone(result['std_dev'])
                self.assertGreaterEqual(result['ai_probability_yes'], 0.0)
                self.assertLessEqual(result['ai_probability_yes'], 100.0)

    def test_historical_fallback_is_city_specific(self):
        dt_obj = datetime(2026, 4, 12)
        la = historical_fallback('Los Angeles', dt_obj)
        ny = historical_fallback('New York', dt_obj)
        chi = historical_fallback('Chicago', dt_obj)
        self.assertNotEqual(la['max_f'], ny['max_f'])
        self.assertNotEqual(ny['max_f'], chi['max_f'])

    def test_trade_logger_uses_no_price_for_buy_no(self):
        row = {'signal_action': 'BUY_NO_STRONG', 'yes_price_percent': '24.0', 'no_price_percent': '78.0'}
        self.assertEqual(get_selected_side_price_percent(row), 78.0)

    def test_bankroll_snapshot_uses_entry_cost_for_open_positions(self):
        trades = [
            {'recommended_stake_usd': '30', 'real_cost_usd': '21', 'realized_pnl_usd': '', 'settlement_status': 'OPEN'},
            {'recommended_stake_usd': '20', 'real_cost_usd': '0', 'realized_pnl_usd': '12.5', 'settlement_status': 'WON'},
        ]
        snapshot = compute_bankroll_snapshot(trades)
        self.assertEqual(snapshot['open_notional_usd'], 30.0)
        self.assertEqual(snapshot['open_entry_cost_usd'], 21.0)
        self.assertEqual(snapshot['realized_pnl_usd'], 12.5)

    def test_high_precision_filter_is_strict(self):
        good = {'signal_action': 'BUY_NO', 'comparison': 'between', 'ai_probability_yes': 4.5, 'yes_ask_percent': 18.0, 'day_offset': 1, 'is_expired': False, 'is_frozen_market': False}
        bad = {'signal_action': 'BUY_NO', 'comparison': 'between', 'ai_probability_yes': 6.0, 'yes_ask_percent': 18.0, 'day_offset': 1, 'is_expired': False, 'is_frozen_market': False}
        self.assertTrue(high_precision_filter(good))
        self.assertFalse(high_precision_filter(bad))


if __name__ == '__main__':
    unittest.main()
