#!/usr/bin/env python3

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from free_update import CACHE_SECONDS, check_update  # noqa: E402


class FreeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = {"HOWTO_HOME": self.temp.name}

    def tearDown(self):
        self.temp.cleanup()

    def test_up_to_date_and_update_available_are_check_only(self):
        current = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
        same = check_update(env=self.env, now=1000, fetch_json=lambda _url: {"name": "howto-swt", "version": current})
        self.assertEqual(same["status"], "UP_TO_DATE")
        newer = check_update(env=self.env, now=1000 + CACHE_SECONDS + 1,
                             fetch_json=lambda _url: {"name": "howto-swt", "version": "99.0.0"})
        self.assertEqual(newer["status"], "UPDATE_AVAILABLE")
        self.assertEqual(json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"], current)

    def test_24_hour_cache_skips_network(self):
        check_update(env=self.env, now=1000, fetch_json=lambda _url: {"name": "howto-swt", "version": "1.1.1"})
        calls = []
        cached = check_update(env=self.env, now=1001, fetch_json=lambda url: calls.append(url))
        self.assertEqual(cached["status"], "CHECK_SKIPPED_CACHED")
        self.assertEqual(calls, [])

    def test_unavailable_network_never_blocks(self):
        result = check_update(env=self.env, now=1000, fetch_json=lambda _url: (_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(result["status"], "CHECK_SKIPPED_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
