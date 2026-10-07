#!/usr/bin/env python3
"""Fail when VERSION, manifests, CHANGELOG, README, and release tag drift."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PORTABLE = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
CODEX = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
RUNTIME = json.loads((ROOT / "runtime-manifest.json").read_text(encoding="utf-8"))
CURRENT = VERSION
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")


def fail(reason: str) -> None:
    raise SystemExit(f"RELEASE_DOCS_CHECK_FAILED: {reason}")


parser = argparse.ArgumentParser()
parser.add_argument("--tag")
args = parser.parse_args()

if not (VERSION == PORTABLE == CODEX == RUNTIME.get("version")):
    fail(f"VERSION/plugin/codex/runtime manifest disagree: {VERSION}/{PORTABLE}/{CODEX}/{RUNTIME.get('version')}")
if RUNTIME.get("product") != "howto-swt" or not re.fullmatch(r"[0-9a-f]{64}", RUNTIME.get("sha256", "")):
    fail("runtime-manifest.json product or SHA-256 invalid")
if args.tag and args.tag != f"v{CURRENT}":
    fail(f"tag {args.tag} does not match v{CURRENT}")
if not re.search(rf"^## v{re.escape(CURRENT)}(?:\s|$)", CHANGELOG, re.MULTILINE):
    fail(f"v{CURRENT} missing from docs/CHANGELOG.md")

match = re.search(
    r"<!-- CHANGELOG_LATEST_START -->(.*?)<!-- CHANGELOG_LATEST_END -->",
    README,
    re.DOTALL,
)
if not match:
    fail("README recent-update markers missing")

versions = re.findall(r"\|\s*v(\d+(?:\.\d+)+)\s*\|", match.group(1))
if not versions or CURRENT not in versions:
    fail(f"README recent updates do not include v{CURRENT}")
if len(versions) > 5 or len(versions) != len(set(versions)):
    fail("README recent updates must contain 1-5 unique versions")

print(f"RELEASE_DOCS_CHECK_OK: v{CURRENT}; {len(versions)} recent versions")
