import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.eda import compute_summary


class EdaSummaryTest(unittest.TestCase):
    def test_summary_uses_explicit_weights_and_descriptive_correlations(self):
        frame = gpd.GeoDataFrame(
            {
                "adm1_name": ["A", "A", "B"],
                "avg_d_mbps": [10.0, 20.0, 30.0],
                "avg_u_mbps": [1.0, 2.0, 3.0],
                "avg_lat_ms": [30, 20, 10],
                "tests": [1, 3, 2],
                "devices": [1, 2, 1],
                "measurement_volume": ["low", "low", "low"],
                "loaded_latency_complete": [True, False, True],
            },
            geometry=[Point(0, 0), Point(1, 1), Point(2, 2)],
            crs="EPSG:4326",
        )
        summary = compute_summary(frame)
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["tests"], 6)
        self.assertAlmostEqual(summary["weighted_national"]["download_mbps"], 130 / 6)
        self.assertEqual(summary["counts"]["loaded_latency_incomplete"], 1)
        self.assertLess(summary["correlations"]["pearson_download_latency"], 0)


if __name__ == "__main__":
    unittest.main()
