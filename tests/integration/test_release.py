#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ReleaseBuildTests(unittest.TestCase):
    def test_release_zip_is_deterministic_and_manifest_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            archives = []
            for number in (1, 2):
                archive = output / f"free-{number}.zip"
                manifest = output / f"manifest-{number}.json"
                result = subprocess.run([sys.executable, str(ROOT / "scripts/build_release.py"),
                    "--output", str(archive), "--manifest", str(manifest),
                    "--released-at", "2026-10-07T00:00:00Z"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                metadata = json.loads(manifest.read_text())
                self.assertEqual(metadata["version"], "1.3.0")
                self.assertEqual(metadata["sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
                archives.append(archive.read_bytes())
                with zipfile.ZipFile(archive) as package:
                    names = set(package.namelist())
                    self.assertIn("skills/swt/SKILL.md", names)
                    self.assertNotIn("runtime-manifest.json", names)
                    self.assertFalse(any(name.startswith((".git/", "tests/")) for name in names))
            self.assertEqual(archives[0], archives[1])


if __name__ == "__main__":
    unittest.main()
