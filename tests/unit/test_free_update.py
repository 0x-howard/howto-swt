#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from free_update import AD_TEXT, CACHE_SECONDS, check_update, daily_ad, mark_updated, valid_notice  # noqa: E402


def payload(version, notice="新功能说明"):
    return lambda _url: {"product": "howto-swt", "version": version, "notice": notice}


class FreeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = {"HOWTO_HOME": self.temp.name}

    def tearDown(self):
        self.temp.cleanup()

    def test_up_to_date_and_update_available_are_check_only(self):
        current = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
        same = check_update(env=self.env, now=1000, fetch_json=payload(current))
        self.assertEqual(same["status"], "UP_TO_DATE")
        newer = check_update(env=self.env, now=1000 + CACHE_SECONDS + 1, fetch_json=payload("99.0.0", "可以直接发截图"))
        self.assertEqual(newer["status"], "UPDATE_AVAILABLE")
        self.assertEqual(newer["message"], "HowTo SWT v99.0.0：可以直接发截图 回复「更新」，我现在帮你更新。")
        self.assertEqual(json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"], current)

    def test_explicit_local_version_works_without_plugin_manifest(self):
        result = check_update(env=self.env, now=1000, fetch_json=payload("1.6.0"), local_version="1.5.0")
        self.assertEqual(result["status"], "UPDATE_AVAILABLE")
        self.assertEqual(result["current_version"], "1.5.0")

    def test_invalid_local_version_is_skipped_quietly(self):
        result = check_update(env=self.env, now=1000, fetch_json=payload("1.6.0"), local_version="latest")
        self.assertEqual(result["status"], "CHECK_SKIPPED_UNAVAILABLE")

    def test_bad_remote_payload_is_ignored(self):
        for index, bad in enumerate((
            {"product": "other", "version": "9.0.0", "notice": "x"},
            {"product": "howto-swt", "version": "9.0", "notice": "x"},
            {"product": "howto-swt", "version": "9.0.0", "notice": ""},
            {"product": "howto-swt", "version": "9.0.0", "notice": "第一行\n第二行"},
            {"product": "howto-swt", "version": "9.0.0", "notice": "长" * 81},
        )):
            result = check_update(env=self.env, now=1000 + index * (CACHE_SECONDS + 1), fetch_json=lambda _url, b=bad: b)
            self.assertEqual(result["status"], "CHECK_SKIPPED_UNAVAILABLE", bad)

    def test_24_hour_cache_skips_network(self):
        check_update(env=self.env, now=1000, fetch_json=payload("1.1.1"))
        calls = []
        cached = check_update(env=self.env, now=1001, fetch_json=lambda url: calls.append(url))
        self.assertEqual(cached["status"], "CHECK_SKIPPED_CACHED")
        self.assertEqual(calls, [])

    def test_mark_updated_suppresses_the_next_check(self):
        mark_updated(env=self.env, now=5000)
        calls = []
        result = check_update(env=self.env, now=5001, fetch_json=lambda url: calls.append(url))
        self.assertEqual(result["status"], "CHECK_SKIPPED_CACHED")
        self.assertEqual(calls, [])

    def test_unavailable_network_never_blocks(self):
        result = check_update(env=self.env, now=1000, fetch_json=lambda _url: (_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(result["status"], "CHECK_SKIPPED_UNAVAILABLE")

    def test_failed_fetch_does_not_start_the_cache_window(self):
        check_update(env=self.env, now=1000, fetch_json=lambda _url: (_ for _ in ()).throw(OSError("offline")))
        result = check_update(env=self.env, now=1001, fetch_json=payload("99.0.0"))
        self.assertEqual(result["status"], "UPDATE_AVAILABLE")

    def test_unwritable_cache_is_ignored(self):
        blocker = Path(self.temp.name) / "not-a-directory"
        blocker.write_text("x", encoding="utf-8")
        env = {"HOWTO_HOME": str(blocker)}
        result = check_update(env=env, now=1000, fetch_json=payload("99.0.0"))
        self.assertEqual(result["status"], "UPDATE_AVAILABLE")
        mark_updated(env=env, now=1000)
        cli = subprocess.run(
            [sys.executable, str(ROOT / "scripts/free_update.py"), "--local-version", "1.0.0"],
            env={"HOWTO_HOME": str(blocker), "HOWTO_FREE_METADATA_URL": "http://127.0.0.1:9/UPDATE.json"},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual((cli.returncode, cli.stdout, cli.stderr), (0, "", ""))

    def test_cli_offline_prints_only_the_daily_ad_once(self):
        def run():
            return subprocess.run(
                [sys.executable, str(ROOT / "scripts/free_update.py"), "--local-version", "1.0.0"],
                env={"HOWTO_HOME": self.temp.name, "HOWTO_FREE_METADATA_URL": "http://127.0.0.1:9/UPDATE.json"},
                text=True, capture_output=True, check=False,
            )
        first, second = run(), run()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, AD_TEXT + "\n")
        self.assertEqual(second.stdout, "")

    def test_daily_ad_once_per_local_day(self):
        self.assertEqual(daily_ad(env=self.env, now=1_000_000), AD_TEXT)
        self.assertIsNone(daily_ad(env=self.env, now=1_000_060))
        self.assertEqual(daily_ad(env=self.env, now=1_000_000 + 86_400), AD_TEXT)

    def test_update_check_keeps_ad_date(self):
        daily_ad(env=self.env, now=1_000_000)
        check_update(env=self.env, now=1_000_000, fetch_json=payload("99.0.0"), local_version="1.0.0")
        self.assertIsNone(daily_ad(env=self.env, now=1_000_060))

    def test_update_json_and_router_version_match_release(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        update = json.loads((ROOT / "UPDATE.json").read_text(encoding="utf-8"))
        self.assertEqual(update["product"], "howto-swt")
        self.assertEqual(update["version"], version)
        self.assertTrue(valid_notice(update["notice"]))
        router = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"--local-version (\S+)", router), [version])
        self.assertIn("--mark-updated", router)
        self.assertIn("npx -y skills add 0x-howard/howto-swt -g --all", router)


if __name__ == "__main__":
    unittest.main()
