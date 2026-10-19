import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from src.extract import _assign_regions


class RegionAssignmentTest(unittest.TestCase):
    def setUp(self):
        self.boundaries = gpd.GeoDataFrame(
            {
                "shapeName": ["West", "East"],
                "shapeISO": ["BD-A", "BD-B"],
            },
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
            ],
            crs="EPSG:4326",
        )

    def test_assigns_interior_centroids(self):
        candidates = pd.DataFrame(
            {"quadkey": ["a", "b"], "tile_x": [0.5, 1.5], "tile_y": [0.5, 0.5]}
        )
        retained, audit = _assign_regions(candidates, self.boundaries)
        self.assertEqual(dict(zip(retained.quadkey, retained.adm1_iso)), {"a": "BD-A", "b": "BD-B"})
        self.assertEqual(audit["ambiguous_boundary_centroids"], 0)

    def test_boundary_tie_is_flagged_and_deterministic(self):
        candidates = pd.DataFrame({"quadkey": ["edge"], "tile_x": [1.0], "tile_y": [0.5]})
        retained, audit = _assign_regions(candidates, self.boundaries)
        self.assertEqual(retained.iloc[0]["adm1_iso"], "BD-A")
        self.assertTrue(retained.iloc[0]["boundary_ambiguous"])
        self.assertEqual(audit["ambiguous_boundary_centroids"], 1)

    def test_unmatched_candidate_is_reported(self):
        candidates = pd.DataFrame({"quadkey": ["outside"], "tile_x": [3.0], "tile_y": [3.0]})
        retained, audit = _assign_regions(candidates, self.boundaries)
        self.assertTrue(retained.empty)
        self.assertEqual(audit["unmatched_bbox_candidates"], 1)


if __name__ == "__main__":
    unittest.main()
