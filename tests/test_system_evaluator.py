import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')

sys.path.append(PROJECT_ROOT)
sys.path.append(SCRIPTS_DIR)

from kalshi_system_evaluator import (
    build_calibration_summary,
    compute_brier_score,
    compute_selected_edge,
    compute_theoretical_pnl,
    disciplined_filter,
    summarize_rows,
    ultra_precision_filter,
)


class SystemEvaluatorTests(unittest.TestCase):
    def test_compute_theoretical_pnl_for_buy_no(self):
        pnl_win = compute_theoretical_pnl('BUY_NO', 24.0, 78.0, 1)
        pnl_loss = compute_theoretical_pnl('BUY_NO', 24.0, 78.0, 0)
        self.assertEqual(pnl_win, 22.0)
        self.assertEqual(pnl_loss, -78.0)

    def test_compute_selected_edge_for_buy_no(self):
        edge = compute_selected_edge('BUY_NO', 12.0, 24.0, 78.0)
        self.assertEqual(edge, 10.0)

    def test_compute_brier_score(self):
        score = compute_brier_score(80.0, 'YES')
        self.assertAlmostEqual(score, 0.04)

    def test_build_calibration_summary(self):
        rows = [
            {'ai_probability_yes': 12.0, 'resolved_outcome': 'NO', 'brier_score': 0.0144},
            {'ai_probability_yes': 18.0, 'resolved_outcome': 'NO', 'brier_score': 0.0324},
            {'ai_probability_yes': 82.0, 'resolved_outcome': 'YES', 'brier_score': 0.0324},
        ]
        summary = build_calibration_summary(rows)
        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]['bucket'], '10-20')
        self.assertEqual(summary[0]['count'], 2)

    def test_disciplined_filter(self):
        self.assertTrue(disciplined_filter({'action': 'BUY_NO', 'comparison': 'between', 'ai_probability_yes': 4, 'yes_ask_percent': 18, 'no_ask_percent': 82, 'edge': 12}))
        self.assertFalse(disciplined_filter({'action': 'BUY_YES', 'comparison': 'between', 'ai_probability_yes': 4, 'yes_ask_percent': 18, 'no_ask_percent': 82, 'edge': 12}))
        self.assertFalse(disciplined_filter({'action': 'BUY_NO', 'comparison': 'greater_than', 'ai_probability_yes': 4, 'yes_ask_percent': 18, 'no_ask_percent': 82, 'edge': 12}))

    def test_ultra_precision_filter(self):
        self.assertTrue(ultra_precision_filter({'action': 'BUY_NO', 'comparison': 'between', 'ai_probability_yes': 4.5, 'yes_ask_percent': 18.0, 'no_ask_percent': 82.0, 'edge': -14.0}))
        self.assertFalse(ultra_precision_filter({'action': 'BUY_NO', 'comparison': 'between', 'ai_probability_yes': 7.0, 'yes_ask_percent': 18.0, 'no_ask_percent': 82.0, 'edge': -14.0}))
        self.assertFalse(ultra_precision_filter({'action': 'BUY_NO', 'comparison': 'less_than', 'ai_probability_yes': 4.0, 'yes_ask_percent': 18.0, 'no_ask_percent': 82.0, 'edge': -14.0}))

    def test_summarize_rows(self):
        rows = [
            {'success': 1, 'pnl': 10.0, 'edge': 5.0},
            {'success': 0, 'pnl': -4.0, 'edge': 3.0},
        ]
        summary = summarize_rows(rows)
        self.assertEqual(summary['trades'], 2)
        self.assertEqual(summary['wins'], 1)
        self.assertEqual(summary['losses'], 1)
        self.assertEqual(summary['win_rate_pct'], 50.0)
        self.assertEqual(summary['avg_pnl'], 3.0)
        self.assertEqual(summary['avg_edge'], 4.0)


if __name__ == '__main__':
    unittest.main()
