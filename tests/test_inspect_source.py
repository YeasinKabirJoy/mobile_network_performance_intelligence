import unittest

from src.inspect_source import _feature_contains, _inside_polygon, _inside_ring


class GeometryChecksTest(unittest.TestCase):
    def setUp(self):
        self.square = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]

    def test_ring_contains_interior_point(self):
        self.assertTrue(_inside_ring(1, 1, self.square))

    def test_ring_rejects_exterior_point(self):
        self.assertFalse(_inside_ring(3, 1, self.square))

    def test_polygon_hole_is_excluded(self):
        hole = [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]
        self.assertFalse(_inside_polygon(1, 1, [self.square, hole]))

    def test_multipolygon_feature(self):
        feature = {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[self.square]],
            }
        }
        self.assertTrue(_feature_contains(feature, 1, 1))


if __name__ == "__main__":
    unittest.main()
