#!/usr/bin/env python3
"""Remove only known generated files and caches inside this SWT plugin."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from paths import PLUGIN_ROOT, RUNTIME_ROOT, TESTS_ROOT


CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEMP_TEST_DIRS = {TESTS_ROOT / ".tmp", TESTS_ROOT / "tmp"}


def _in_source(path: Path) -> bool:
    try:
        path.resolve().relative_to(PLUGIN_ROOT.resolve())
        return True
    except ValueError:
        return False


def _walk_source() -> list[Path]:
    found: list[Path] = []
    for base, dirs, files in os.walk(PLUGIN_ROOT, followlinks=False):
        dirs[:] = [name for name in dirs if name != ".git"]
        parent = Path(base)
        found.extend(parent / name for name in dirs)
        found.extend(parent / name for name in files)
    return found


def _remove(path: Path, removed: list[str]) -> None:
    if not _in_source(path) or path.is_symlink():
        return
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
    else:
        return
    removed.append(str(path.relative_to(PLUGIN_ROOT)))


def clean_cache(removed: list[str]) -> None:
    for path in sorted(_walk_source(), key=lambda item: len(item.parts), reverse=True):
        if path.name in CACHE_DIRS or path.name == ".DS_Store" or path.suffix in {".pyc", ".pyo"}:
            _remove(path, removed)


def clean_generated(removed: list[str]) -> None:
    if not RUNTIME_ROOT.is_dir():
        return
    for path in sorted(RUNTIME_ROOT.glob("*.md")):
        if not path.is_file() or path.is_symlink():
            continue
        content = path.read_text(encoding="utf-8")
        if "GENERATED FILE: DO NOT EDIT" in content and "Source maintenance:" in content:
            _remove(path, removed)


def clean_tests(removed: list[str]) -> None:
    for path in TEMP_TEST_DIRS:
        if path.exists():
            _remove(path, removed)
    for path in sorted(TESTS_ROOT.rglob("*.tmp")) if TESTS_ROOT.exists() else ():
        _remove(path, removed)


def prune_stale_plugin_cache(cache_root: Path, removed: list[str]) -> None:
    """Prune old versions only from an explicitly selected plugin cache directory."""
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    plugin_name = manifest["name"]
    source_version = str(manifest["version"]).split("+", 1)[0]
    selected = cache_root.expanduser().resolve()
    codex_cache_root = (Path.home() / ".codex" / "plugins" / "cache").resolve()
    if selected.name != plugin_name or selected.parents[1] != codex_cache_root:
        raise ValueError("--codex-plugin-cache must be this plugin's exact directory under ~/.codex/plugins/cache/<marketplace>/")
    if not selected.is_dir():
        return
    current = [p for p in selected.iterdir() if p.is_dir() and (p.name == source_version or p.name.startswith(source_version + "+"))]
    if not current:
        raise ValueError(f"no installed cache for source version {source_version}; install and verify it before pruning older versions")
    for path in selected.iterdir():
        if path.is_dir() and path not in current:
            _remove(path, removed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--cache", action="store_true", help="remove source-tree OS/Python caches")
    mode.add_argument("--generated", action="store_true", help="remove marked shared-runtime outputs")
    mode.add_argument("--tests", action="store_true", help="remove test temporary files")
    mode.add_argument("--all", action="store_true", help="remove source caches, generated outputs and test temps")
    parser.add_argument("--codex-plugin-cache", type=Path, help="prune stale versions under one explicitly named SWT plugin cache directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    removed: list[str] = []
    if args.cache or args.all:
        clean_cache(removed)
    if args.generated or args.all:
        clean_generated(removed)
    if args.tests or args.all:
        clean_tests(removed)
    if args.codex_plugin_cache:
        prune_stale_plugin_cache(args.codex_plugin_cache, removed)
    print("Removed:")
    if removed:
        for item in removed:
            print(f"- {item}")
    else:
        print("- nothing")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2) from error
