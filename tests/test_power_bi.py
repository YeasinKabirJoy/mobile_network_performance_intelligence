import unittest

import pandas as pd

from src.export_power_bi import calculate_kpis


class PowerBIExportTest(unittest.TestCase):
    def test_kpis_use_explicit_test_weighting(self):
        frame = pd.DataFrame(
            {
                "avg_d_mbps": [20.0, 40.0],
                "avg_u_mbps": [5.0, 15.0],
                "avg_lat_ms": [50.0, 10.0],
                "tests": [10, 30],
                "devices": [4, 12],
            }
        )
        result = calculate_kpis(frame)
        self.assertEqual(result["tiles"], 2)
        self.assertEqual(result["tests"], 40)
        self.assertAlmostEqual(result["weighted_download_mbps"], 35.0)
        self.assertAlmostEqual(result["weighted_upload_mbps"], 12.5)
        self.assertAlmostEqual(result["weighted_idle_latency_ms"], 20.0)


if __name__ == "__main__":
    unittest.main()
