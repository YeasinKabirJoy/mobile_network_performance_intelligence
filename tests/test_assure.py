import unittest
from pathlib import Path

from src.assure import _read_json


class AssuranceTest(unittest.TestCase):
    def test_json_reader_preserves_reconciliation_boolean(self):
        path = Path("reports/generated/tableau_reconciliation.json")
        self.assertTrue(_read_json(path)["all_pass"])

    def test_desktop_dashboard_status_verified(self):
        from src.assure import build_assurance
        audit = build_assurance(Path("."))
        self.assertTrue(audit["phase9_automated_checks_pass"])
        self.assertIn("present", audit["desktop_dashboard_status"]["power_bi"])
        self.assertIn("present", audit["desktop_dashboard_status"]["tableau"])


if __name__ == "__main__":
    unittest.main()
