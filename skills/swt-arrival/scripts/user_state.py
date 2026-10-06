#!/usr/bin/env python3
"""Opt-in JSON state adapter. It never selects a fallback storage location."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from paths import PLUGIN_ROOT

STATE_FILENAME = "swt-user-state.json"
SENSITIVE_KEY = re.compile(r"password|passcode|otp|verification.?code|passport.?number|national.?id|sevis.?id|ds.?160.?number|confirmation.?number|bank.?account|signature|email|phone|address|transcript|document.?image", re.I)


def resolve_user_data_root(env: dict[str, str] | None = None) -> Path:
    source_env = os.environ if env is None else env
    value = source_env.get("USER_DATA_ROOT", "").strip()
    if not value:
        raise ValueError("USER_DATA_ROOT is not configured; persistence is unavailable")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise ValueError("USER_DATA_ROOT must be an absolute path")
    resolved = candidate.resolve()
    if resolved == PLUGIN_ROOT.resolve() or PLUGIN_ROOT.resolve() in resolved.parents:
        raise ValueError("USER_DATA_ROOT must be outside the plugin source tree")
    return resolved


def _state_path(env: dict[str, str] | None = None) -> Path:
    path = resolve_user_data_root(env) / STATE_FILENAME
    if path.is_symlink():
        raise ValueError("state file must not be a symbolic link")
    resolved = path.resolve()
    if resolved == PLUGIN_ROOT.resolve() or PLUGIN_ROOT.resolve() in resolved.parents:
        raise ValueError("state file must remain outside the plugin source tree")
    return path


def _check_sensitive_keys(value: Any, path: str = "state") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                raise ValueError(f"sensitive field is not allowed: {path}.{key}")
            _check_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_sensitive_keys(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if len(value) > 2000:
            raise ValueError(f"string exceeds length limit: {path}")
        private_patterns = (
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            r"(?<!\d)(?:\+?\d[\s().-]*){10,}(?!\d)",
            r"\b\d{9,}\b",
            r"\b\d{1,6}\s+[A-Z0-9.'-]+(?:\s+[A-Z0-9.'-]+){0,4}\s+(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|boulevard|blvd|highway|hwy)\b",
        )
        if any(re.search(pattern, value, re.I) for pattern in private_patterns):
            raise ValueError(f"possible private identifier in {path}")


def _validate_state(data: dict[str, Any]) -> None:
    schema = json.loads((PLUGIN_ROOT / "references" / "user-state.schema.json").read_text(encoding="utf-8"))
    _check_sensitive_keys(data)
    _validate_against_schema(data, schema, "state")


def _validate_against_schema(value: Any, schema: dict[str, Any], path: str) -> None:
    expected = schema.get("type")
    if expected is not None:
        accepted = expected if isinstance(expected, list) else [expected]
        python_types = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        if not any(python_types[kind](value) for kind in accepted):
            raise ValueError(f"{path} has an invalid type")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is not an allowed value")
    if isinstance(value, str):
        if len(value) > schema.get("maxLength", float("inf")):
            raise ValueError(f"{path} exceeds maxLength")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValueError(f"{path} does not match its required pattern")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(f"{path} must be an ISO date-time") from error
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")):
            raise ValueError(f"{path} is outside the allowed range")
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", float("inf")):
            raise ValueError(f"{path} exceeds maxItems")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ValueError(f"{path} items must be unique")
        item_schema = schema.get("items", {})
        for index, item in enumerate(value):
            _validate_against_schema(item, item_schema, f"{path}[{index}]")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        if required - set(value):
            raise ValueError(f"{path} is missing required fields: {sorted(required - set(value))}")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise ValueError(f"{path} contains unsupported fields: {sorted(set(value) - set(properties))}")
        for key, item in value.items():
            if key in properties:
                _validate_against_schema(item, properties[key], f"{path}.{key}")


def load_state(env: dict[str, str] | None = None) -> dict[str, Any] | None:
    path = _state_path(env)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    _validate_state(data)
    return data


def save_state(data: dict[str, Any], env: dict[str, str] | None = None) -> Path:
    root = resolve_user_data_root(env)
    path = _state_path(env)
    _validate_state(data)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=".swt-state-", suffix=".tmp", dir=root)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def delete_state(env: dict[str, str] | None = None) -> bool:
    path = _state_path(env)
    if not path.exists():
        return False
    path.unlink()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("load", "save", "delete"))
    args = parser.parse_args()
    if args.operation == "load":
        print(json.dumps(load_state(), ensure_ascii=False, indent=2))
    elif args.operation == "save":
        payload = json.load(sys.stdin)
        path = save_state(payload)
        print(f"User state saved to {path}")
    else:
        print("deleted" if delete_state() else "not found")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2) from error
