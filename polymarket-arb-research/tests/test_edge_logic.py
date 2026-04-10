from __future__ import annotations

import unittest

from edge_logic import calculate_edges, decide_executable


class TestEdgeLogic(unittest.TestCase):
    def test_calculate_edges_positive_gross(self) -> None:
        result = calculate_edges(
            yes_ask=0.45,
            no_ask=0.50,
            fee_rate=0.01,
            slippage_buffer=0.005,
            latency_ms=250,
            one_leg_fill_risk=0.1,
        )
        self.assertGreater(result.gross_edge, 0)
        self.assertLess(result.net_edge, result.gross_edge)

    def test_decide_executable(self) -> None:
        edge = calculate_edges(0.45, 0.50, 0.001, 0.001, 100, 0.0)
        decision = decide_executable(edge, yes_size=100, no_size=100, min_trade_size=25, survives_latency=True)
        self.assertTrue(decision.executable)

    def test_decide_executable_fail_size(self) -> None:
        edge = calculate_edges(0.45, 0.50, 0.001, 0.001, 100, 0.0)
        decision = decide_executable(edge, yes_size=5, no_size=100, min_trade_size=25, survives_latency=True)
        self.assertFalse(decision.executable)
        self.assertEqual(decision.reason, "below_min_size")


if __name__ == "__main__":
    unittest.main()
