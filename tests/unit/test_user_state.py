import json
import os
import subprocess
import sys
import tempfile
import unittest
import stat
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from user_state import _validate_state, delete_state, load_state, save_state  # noqa: E402


class UserStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = {"USER_DATA_ROOT": self.temp.name}
        self.state = {
            "schema_version": "1.0.0", "updated_at": "2026-09-29T01:00:00Z",
            "profile": {"program_year": 2027, "school_name": "Example University", "major": "Hospitality", "target_profile": "host"},
            "stage": {"current": "05", "completed": ["00", "01"]},
            "offers": [{"role": "Cashier", "employer_name": "Example Store", "location": "Myrtle Beach, SC", "wage_summary": "$15/hour", "status": "offered"}],
            "arrival": {"arrival_window": "June 2027", "checkin_status": "not_started", "pending_tasks": ["Confirm airport pickup"]},
            "english": {"assessment_summary": {
                "profile": "host_generic", "readiness": "developing",
                "top_weaknesses": ["interaction_repair"], "assessed_at": "2026-09-28T10:00:00Z",
            }, "practice_summary": {
                "profile": "host_practice", "focus_dimensions": ["interaction_repair"],
                "session_improvements": ["Asked one clarifying question before responding"],
                "completed_at": "2026-09-29T01:00:00Z",
            }},
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_explicit_external_storage_round_trip(self):
        path = save_state(self.state, self.env)
        self.assertEqual(path.name, "swt-user-state.json")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(load_state(self.env), self.state)
        self.assertFalse((Path(__file__).resolve().parents[2] / "swt-user-state.json").exists())
        self.assertTrue(delete_state(self.env))
        self.assertFalse(delete_state(self.env))

    def test_explicit_cli_adapter_round_trip(self):
        script = Path(__file__).resolve().parents[2] / "scripts" / "user_state.py"
        save = subprocess.run(
            [sys.executable, str(script), "save"], env={**os.environ, **self.env},
            input=json.dumps(self.state), text=True, capture_output=True, check=False,
        )
        self.assertEqual(save.returncode, 0, save.stderr)
        load = subprocess.run(
            [sys.executable, str(script), "load"], env={**os.environ, **self.env},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(load.returncode, 0, load.stderr)
        self.assertEqual(json.loads(load.stdout), self.state)

    def test_unconfigured_or_relative_path_does_not_fallback(self):
        with self.assertRaises(ValueError):
            load_state({})
        with self.assertRaises(ValueError):
            save_state(self.state, {"USER_DATA_ROOT": "relative/path"})
        with patch.dict(os.environ, {"USER_DATA_ROOT": self.temp.name}):
            with self.assertRaises(ValueError):
                load_state({})

    def test_plugin_directory_is_rejected_as_user_data_root(self):
        plugin_root = str(Path(__file__).resolve().parents[2])
        with self.assertRaises(ValueError):
            save_state(self.state, {"USER_DATA_ROOT": plugin_root})

    def test_symlink_state_file_is_rejected(self):
        root = Path(self.temp.name)
        target = root / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = root / "swt-user-state.json"
        os.symlink(target, link)
        with self.assertRaises(ValueError):
            load_state(self.env)

    def test_sensitive_fields_and_unapproved_schema_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "passport_number": "123456789"})
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "program": {"position_summary": "Cashier, 123 Main Street"}})
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "profile": {"home_country": "+1 (555) 555-0123"}})
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "notes": "arbitrary raw transcript"})
        with self.assertRaises(ValueError):
            _validate_state({
                "schema_version": "1.0.0", "updated_at": "2026-09-29T01:00:00Z",
                "visa": {"verified_facts": [{"field": "sponsor_name", "value": "A", "status": "confirmed", "sevis_id": "N0000000000"}]},
            })

    def test_invalid_existing_stage_and_assessment_profile_are_rejected(self):
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "stage": {"current": "12"}})
        with self.assertRaises(ValueError):
            _validate_state({**self.state, "english": {"assessment_summary": {"profile": "made_up"}}})


if __name__ == "__main__":
    unittest.main()
