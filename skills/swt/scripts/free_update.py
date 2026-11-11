#!/usr/bin/env python3
"""Check the public HowTo SWT UPDATE.json and print one reminder line when a newer version exists."""

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
DEFAULT_METADATA_URL = "https://raw.githubusercontent.com/0x-howard/howto-swt/main/UPDATE.json"
CACHE_SECONDS = 24 * 60 * 60
NOTICE_MAX_CHARS = 80
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _version(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(f"invalid semantic version: {value!r}")
    return tuple(map(int, match.groups()))


def valid_notice(value: Any) -> bool:
    return (isinstance(value, str) and 1 <= len(value.strip()) <= NOTICE_MAX_CHARS
            and not any(ch in value for ch in "\r\n\t"))


def reminder(version: str, notice: str) -> str:
    return f"HowTo SWT v{version}：{notice.strip()} 回复 1，我现在帮你更新。"


def _local_version(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    manifest = ROOT / "plugin.json"
    if manifest.is_file():
        return json.loads(manifest.read_text(encoding="utf-8")).get("version")
    return None


def _cache_path(env: dict[str, str]) -> Path:
    root = Path(env.get("HOWTO_HOME") or (Path.home() / ".howto")).expanduser().resolve()
    return root / "free-update-state.json"


def _read_cache(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write_cache(path: Path, value: dict[str, Any]) -> None:
    try:
        _write_cache_file(path, value)
    except OSError:
        pass


def _write_cache_file(path: Path, value: dict[str, Any]) -> None:
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


def _timestamp(moment: float) -> str:
    return datetime.fromtimestamp(moment, timezone.utc).isoformat().replace("+00:00", "Z")


def mark_updated(*, env: dict[str, str] | None = None, now: float | None = None) -> None:
    source_env = dict(os.environ if env is None else env)
    moment = time.time() if now is None else now
    path = _cache_path(source_env)
    _write_cache(path, {**_read_cache(path), "last_checked_epoch": moment, "last_checked": _timestamp(moment)})


def check_update(*, env: dict[str, str] | None = None, now: float | None = None,
                 fetch_json: Callable[[str], dict[str, Any]] | None = None,
                 metadata_url: str | None = None, local_version: str | None = None) -> dict[str, Any]:
    source_env = dict(os.environ if env is None else env)
    try:
        current = _local_version(local_version)
        current_tuple = _version(current)
    except (ValueError, OSError, json.JSONDecodeError):
        return {"status": "CHECK_SKIPPED_UNAVAILABLE", "product": "howto-swt", "current_version": None}

    moment = time.time() if now is None else now
    cache_path = _cache_path(source_env)
    cached = _read_cache(cache_path)
    last_checked = cached.get("last_checked_epoch")
    if isinstance(last_checked, (int, float)) and 0 <= moment - last_checked < CACHE_SECONDS:
        return {"status": "CHECK_SKIPPED_CACHED", "product": "howto-swt", "current_version": current,
                "last_checked": cached.get("last_checked")}

    timestamp = _timestamp(moment)
    url = metadata_url or source_env.get("HOWTO_FREE_METADATA_URL") or DEFAULT_METADATA_URL
    try:
        if fetch_json is None:
            with urllib.request.urlopen(url, timeout=8) as response:  # nosec B310: fixed HTTPS URL
                metadata = json.loads(response.read().decode("utf-8"))
        else:
            metadata = fetch_json(url)
        if metadata.get("product") != "howto-swt":
            raise ValueError("product mismatch")
        latest = metadata["version"]
        latest_tuple = _version(latest)
        notice = metadata.get("notice")
        if not valid_notice(notice):
            raise ValueError("invalid notice")
        _write_cache(cache_path, {
            "last_checked_epoch": moment, "last_checked": timestamp,
            "current_version": current, "latest_seen": latest,
        })
        if latest_tuple > current_tuple:
            return {"status": "UPDATE_AVAILABLE", "product": "howto-swt", "current_version": current,
                    "latest_version": latest, "message": reminder(latest, notice)}
        return {"status": "UP_TO_DATE", "product": "howto-swt",
                "current_version": current, "latest_version": latest}
    except Exception:
        return {"status": "CHECK_SKIPPED_UNAVAILABLE", "product": "howto-swt", "current_version": current}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-version", help="installed version, written in skills/swt/SKILL.md")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mark-updated", action="store_true", help="record a successful update; prints nothing")
    args = parser.parse_args()
    if args.mark_updated:
        mark_updated()
        return 0
    result = check_update(local_version=args.local_version)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif result["status"] == "UPDATE_AVAILABLE":
        print(result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
