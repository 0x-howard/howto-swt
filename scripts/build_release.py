#!/usr/bin/env python3
"""Build a deterministic Free runtime ZIP and canonical public manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "tests", "__pycache__"}
SKIP_FILES = {".DS_Store", "runtime-manifest.json"}


def members():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.name in SKIP_FILES or path.suffix == ".pyc":
            continue
        yield path, relative


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "runtime-manifest.json")
    parser.add_argument("--released-at", help="ISO-8601 timestamp; defaults to current UTC time")
    parser.add_argument("--summary", default="Task, Context and Runtime architecture upgrade.")
    parser.add_argument("--asset-url")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"] != version:
        parser.error("VERSION and plugin.json disagree")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, relative in members():
            info = zipfile.ZipInfo(relative.as_posix(), timestamp)
            mode = source.stat().st_mode
            info.external_attr = ((0o755 if mode & stat.S_IXUSR else 0o644) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    released_at = args.released_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    asset_url = args.asset_url or f"https://github.com/0x-howard/howto-swt/releases/download/v{version}/howto-swt-{version}.zip"
    manifest = {"schema_version": 1, "product": "howto-swt", "version": version,
                "released_at": released_at, "summary": args.summary, "sha256": digest,
                "size": output.stat().st_size, "asset_url": asset_url}
    manifest_path = args.manifest.expanduser().resolve()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(output), "manifest": str(manifest_path), **manifest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
