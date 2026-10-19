import unittest

import pandas as pd

from src.score import SCENARIOS, _percentile, add_components, score_scenarios


class ScoreTest(unittest.TestCase):
    def test_percentile_direction_and_endpoints(self):
        values = pd.Series([10.0, 20.0, 30.0])
        self.assertEqual(_percentile(values).tolist(), [0.0, 0.5, 1.0])
        self.assertEqual(_percentile(values, higher_is_higher=False).tolist(), [1.0, 0.5, 0.0])

    def test_weights_sum_to_one_and_persistence_is_zero(self):
        for weights in SCENARIOS.values():
            self.assertAlmostEqual(sum(weights.values()), 1.0)
            self.assertEqual(weights["persistence"], 0.0)

    def test_score_is_bounded_and_ranked(self):
        regions = pd.DataFrame(
            {
                "adm1_iso": ["A", "B", "C"],
                "adm1_name": ["A", "B", "C"],
                "tiles": [10, 10, 10],
                "tests": [100, 200, 300],
                "devices": [50, 100, 150],
                "weighted_download_mbps": [10.0, 20.0, 30.0],
                "weighted_upload_mbps": [2.0, 3.0, 4.0],
                "weighted_idle_latency_ms": [50.0, 30.0, 10.0],
                "low_volume_tile_share": [0.8, 0.7, 0.6],
                "high_volume_tile_share": [0.1, 0.2, 0.3],
                "loaded_latency_incomplete_share": [0.1, 0.1, 0.1],
            }
        )
        scored, scenarios = score_scenarios(regions)
        self.assertTrue(scored["base_score"].between(0, 100).all())
        self.assertEqual(set(scenarios["base"]["rank"]), {1, 2, 3})
        self.assertEqual(scored.iloc[0]["adm1_iso"], "A")

    def test_missing_required_input_fails_explicitly(self):
        regions = pd.DataFrame(
            {
                "weighted_download_mbps": [10.0],
                "weighted_upload_mbps": [2.0],
                "weighted_idle_latency_ms": [None],
                "tests": [100],
                "high_volume_tile_share": [0.1],
            }
        )
        with self.assertRaisesRegex(ValueError, "weighted_idle_latency_ms"):
            add_components(regions)


if __name__ == "__main__":
    unittest.main()
