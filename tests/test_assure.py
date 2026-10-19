import unittest
from pathlib import Path

from src.assure import _read_json


class AssuranceTest(unittest.TestCase):
    def test_json_reader_preserves_reconciliation_boolean(self):
        path = Path("reports/generated/tableau_reconciliation.json")
        self.assertTrue(_read_json(path)["all_pass"])


if __name__ == "__main__":
    unittest.main()
