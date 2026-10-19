import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.clean import clean_frame
from src.validate import validate_processed


def sample_frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "quadkey": ["a", "b", "c"],
            "tile": ["tile-a", "tile-b", "tile-c"],
            "tile_x": [90.0, 90.1, 90.2],
            "tile_y": [23.0, 23.1, 23.2],
            "avg_d_kbps": [1000, 0, -1],
            "avg_u_kbps": [500, 1, 50],
            "avg_lat_ms": [20, 0, 30],
            "avg_lat_down_ms": [None, 10, 20],
            "avg_lat_up_ms": [None, 15, 25],
            "tests": [1, 5, 2],
            "devices": [1, 2, 1],
            "adm1_name": ["Dhaka"] * 3,
            "adm1_iso": ["BD-C"] * 3,
            "period_start": [pd.Timestamp("2024-10-01")] * 3,
            "year": [2024] * 3,
            "quarter": [4] * 3,
            "source_layer": ["performance_mobile_tiles"] * 3,
        },
        geometry=[Point(90.0, 23.0), Point(90.1, 23.1), Point(90.2, 23.2)],
        crs="EPSG:4326",
    )


class CleaningTest(unittest.TestCase):
    def test_converts_units_and_preserves_zero(self):
        clean, audit = clean_frame(sample_frame())
        self.assertEqual(len(clean), 2)
        self.assertEqual(clean.loc[clean.quadkey == "a", "avg_d_mbps"].iloc[0], 1.0)
        self.assertEqual(clean.loc[clean.quadkey == "b", "avg_d_mbps"].iloc[0], 0.0)
        self.assertEqual(audit["zero_idle_latency_rows_preserved"], 1)

    def test_preserves_loaded_latency_nulls(self):
        clean, _ = clean_frame(sample_frame())
        row = clean.loc[clean.quadkey == "a"].iloc[0]
        self.assertTrue(pd.isna(row.avg_lat_down_ms))
        self.assertEqual(row.quality_note, "low_volume;missing_loaded_latency")

    def test_removes_negative_measurement(self):
        clean, audit = clean_frame(sample_frame())
        self.assertNotIn("c", set(clean.quadkey))
        self.assertEqual(audit["removal_counts_by_reason"]["negative_performance"], 1)

    def test_volume_categories_are_descriptive(self):
        clean, _ = clean_frame(sample_frame())
        self.assertEqual(dict(zip(clean.quadkey, clean.measurement_volume)), {"a": "low", "b": "medium"})

    def test_clean_sample_passes_processed_validation(self):
        clean, _ = clean_frame(sample_frame())
        # The fixture has one ADM1, so override only the production coverage check.
        result = validate_processed(clean)
        self.assertTrue(all(value for key, value in result["checks"].items() if key != "all_eight_adm1_present"))


if __name__ == "__main__":
    unittest.main()
