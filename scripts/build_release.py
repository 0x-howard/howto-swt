#!/usr/bin/env python3
"""Build a deterministic Free runtime ZIP, or the Pro ZIP with local extensions."""

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
PRO_DIRS = ("context-engine", "content-data")


def members(*, pro: bool = False):
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.name in SKIP_FILES or path.suffix == ".pyc":
            continue
        if relative.parts[0] in PRO_DIRS and not pro:
            continue
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in the package: {relative}")
        yield path, relative


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pro", action="store_true", help="also include the local context-engine/ and content-data/")
    parser.add_argument("--manifest", type=Path, help="write release metadata to this path")
    parser.add_argument("--released-at", help="ISO-8601 timestamp; defaults to current UTC time")
    parser.add_argument("--summary", default="HowTo SWT release build.")
    parser.add_argument("--asset-url")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"] != version:
        parser.error("VERSION and plugin.json disagree")
    if args.pro and not all((ROOT / name).is_dir() for name in PRO_DIRS):
        parser.error("--pro requires local context-engine/ and content-data/")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, relative in members(pro=args.pro):
            info = zipfile.ZipInfo(relative.as_posix(), timestamp)
            mode = source.stat().st_mode
            info.external_attr = ((0o755 if mode & stat.S_IXUSR else 0o644) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    released_at = args.released_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    product = "howto-swt-pro" if args.pro else "howto-swt"
    asset_url = args.asset_url or (None if args.pro else
                                   f"https://github.com/0x-howard/howto-swt/releases/download/v{version}/howto-swt-{version}.zip")
    manifest = {"schema_version": 1, "product": product, "version": version,
                "released_at": released_at, "summary": args.summary, "sha256": digest,
                "size": output.stat().st_size, "asset_url": asset_url}
    if args.manifest:
        manifest_path = args.manifest.expanduser().resolve()
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest["manifest"] = str(manifest_path)
    print(json.dumps({"archive": str(output), **manifest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
