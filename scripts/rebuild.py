#!/usr/bin/env python3
"""Clean safe local artifacts, regenerate shared runtime and run plugin checks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from paths import PLUGIN_ROOT, TESTS_ROOT


def run(label: str, *args: str) -> None:
    print(f"\n== {label} ==", flush=True)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run([sys.executable, *args], cwd=PLUGIN_ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-clean", action="store_true", help="do not remove local caches, test temps or generated runtime first")
    args = parser.parse_args()

    if not args.skip_clean:
        run("Clean safe source artifacts", "scripts/clean.py", "--all")
    run("Regenerate shared runtime", "scripts/sync_shared.py")
    run("Validate plugin, Skills, generated files and eval references", "scripts/validate.py")
    run("Unit tests", "-m", "unittest", "discover", "-s", str(TESTS_ROOT / "unit"), "-v")
    run("Integration tests", "-m", "unittest", "discover", "-s", str(TESTS_ROOT / "integration"), "-v")
    run("Eval contract", "-m", "unittest", "discover", "-s", str(TESTS_ROOT / "integration"), "-p", "test_package.py", "-k", "test_behavior_contract_has_all_required_cases", "-v")
    print("\nRebuild complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"FAILED: {error.cmd} (exit {error.returncode})", file=sys.stderr)
        raise SystemExit(error.returncode or 1) from error
