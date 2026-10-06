#!/usr/bin/env python3
"""Fail a release when VERSION, CHANGELOG, and README recent versions drift."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")


def fail(reason: str) -> None:
    raise SystemExit(f"RELEASE_DOCS_CHECK_FAILED: {reason}")


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
