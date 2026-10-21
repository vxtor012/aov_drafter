import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import crawler_system
from scripts.validate_data import validate_database, main as validate_snapshot

ROOT = Path(__file__).resolve().parents[1]


class DataTests(unittest.TestCase):
    def setUp(self):
        self.heroes = json.loads((ROOT / "data" / "crawled_heroes.json").read_text(encoding="utf-8"))

    def test_snapshot_is_valid_and_synchronized(self):
        validate_snapshot()

    def test_duplicate_and_dangling_counters_are_rejected(self):
        broken = copy.deepcopy(self.heroes)
        broken[0]["counters"].append({"id": "missinghero", "reason": "test"})
        with self.assertRaises(ValueError):
            validate_database(broken)
        with self.assertRaises(ValueError):
            validate_database(self.heroes + [self.heroes[0]])

    def test_non_finite_rates_are_rejected(self):
        self.heroes[0]["win_rate"] = float("nan")
        with self.assertRaises(ValueError):
            validate_database(self.heroes)

    def test_nested_nextjs_pointers(self):
        tiers = {"S": [{"hero": {"name_en": "Airi"}}, {"hero": "$7:props:data:tiers:S:0:hero"}]}
        self.assertEqual(crawler_system.resolve_nextjs_pointer("$7:props:data:tiers:S:1:hero", tiers), {"name_en": "Airi"})
        self.assertIsNone(crawler_system.resolve_nextjs_pointer("$7:props:data:tiers:S:99:hero", tiers))

    def test_network_failure_does_not_modify_snapshot(self):
        paths = [ROOT / name for name in ("public/assets/js/app.js", "data/crawled_heroes.json", "data/data_update_report.json")]
        before = [p.read_bytes() for p in paths]
        with patch.object(crawler_system.requests, "get", side_effect=RuntimeError("offline")):
            with self.assertRaises(RuntimeError):
                crawler_system.main()
        self.assertEqual(before, [p.read_bytes() for p in paths])


if __name__ == "__main__":
    unittest.main()
