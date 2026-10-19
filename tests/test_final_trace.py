import unittest
from pathlib import Path

from src.final_trace import DEFAULT_QUADKEY, build_traces


class FinalTraceTest(unittest.TestCase):
    def test_real_tile_and_kpi_trace_reconcile(self):
        tile, kpi = build_traces(Path(".").resolve(), DEFAULT_QUADKEY)
        self.assertEqual(tile["quadkey"], DEFAULT_QUADKEY)
        self.assertEqual(tile["geographic_extraction"]["adm1_name"], "Dhaka")
        self.assertAlmostEqual(tile["cleaning"]["avg_d_mbps"], 28.63)
        self.assertTrue(kpi["automated_pass"])


if __name__ == "__main__":
    unittest.main()
