import unittest

from src.export_tableau import FIELD_DICTIONARY


class TableauExportTest(unittest.TestCase):
    def test_dictionary_has_unique_fields_and_core_geography(self):
        fields = [row[0] for row in FIELD_DICTIONARY]
        self.assertEqual(len(fields), len(set(fields)))
        self.assertIn("quadkey", fields)
        self.assertIn("longitude", fields)
        self.assertIn("latitude", fields)
        self.assertIn("base_score", fields)


if __name__ == "__main__":
    unittest.main()
