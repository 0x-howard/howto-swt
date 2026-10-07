#!/usr/bin/env python3
"""Check the canonical public HowTo SWT metadata without applying updates."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA_URL = "https://raw.githubusercontent.com/0x-howard/howto-swt/main/plugin.json"
CACHE_SECONDS = 24 * 60 * 60
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"invalid semantic version: {value!r}")
    return tuple(map(int, match.groups()))


def _cache_path(env: dict[str, str]) -> Path:
    root = Path(env.get("HOWTO_HOME") or (Path.home() / ".howto")).expanduser().resolve()
    return root / "free-update-state.json"


def _read_cache(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write_cache(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=".free-update-", suffix=".tmp", dir=path.parent)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check_update(*, env: dict[str, str] | None = None, now: float | None = None,
                 fetch_json: Callable[[str], dict[str, Any]] | None = None,
                 metadata_url: str | None = None) -> dict[str, Any]:
    source_env = dict(os.environ if env is None else env)
    current = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    current_tuple = _version(current)
    moment = time.time() if now is None else now
    cache_path = _cache_path(source_env)
    cached = _read_cache(cache_path)
    last_checked = cached.get("last_checked_epoch")
    if isinstance(last_checked, (int, float)) and moment - last_checked < CACHE_SECONDS:
        return {"status": "CHECK_SKIPPED_CACHED", "product": "howto-swt", "current_version": current,
                "last_checked": cached.get("last_checked")}

    timestamp = datetime.fromtimestamp(moment, timezone.utc).isoformat().replace("+00:00", "Z")
    _write_cache(cache_path, {**cached, "last_checked_epoch": moment, "last_checked": timestamp})
    url = metadata_url or source_env.get("HOWTO_FREE_METADATA_URL") or DEFAULT_METADATA_URL
    try:
        if fetch_json is None:
            with urllib.request.urlopen(url, timeout=8) as response:  # nosec B310: fixed HTTPS canonical URL
                metadata = json.loads(response.read().decode("utf-8"))
        else:
            metadata = fetch_json(url)
        if metadata.get("name") != "howto-swt":
            raise ValueError("canonical metadata product mismatch")
        latest = metadata["version"]
        latest_tuple = _version(latest)
        _write_cache(cache_path, {
            "last_checked_epoch": moment, "last_checked": timestamp,
            "current_version": current, "latest_seen": latest,
        })
        if latest_tuple > current_tuple:
            return {"status": "UPDATE_AVAILABLE", "product": "howto-swt",
                    "current_version": current, "latest_version": latest}
        return {"status": "UP_TO_DATE", "product": "howto-swt",
                "current_version": current, "latest_version": latest}
    except Exception:
        return {"status": "CHECK_SKIPPED_UNAVAILABLE", "product": "howto-swt", "current_version": current}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check_update()
    if args.json or result["status"] == "UPDATE_AVAILABLE":
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
