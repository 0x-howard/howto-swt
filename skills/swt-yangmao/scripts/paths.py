"""Canonical paths for the source plugin package and its data layers."""

import os
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = PLUGIN_ROOT / "shared"
SKILLS_ROOT = PLUGIN_ROOT / "skills"
REFERENCES_ROOT = PLUGIN_ROOT / "references"
RUNTIME_ROOT = REFERENCES_ROOT / "shared-runtime"
ASSETS_ROOT = PLUGIN_ROOT / "assets"
TESTS_ROOT = PLUGIN_ROOT / "tests"
SOURCE_DATA_ROOT = Path(
    os.environ.get(
        "HOWTO_SWT_SOURCE_DATA_ROOT",
        str(PLUGIN_ROOT.parent / "workspace-docs" / "source-data" / "swt-data-source"),
    )
).expanduser().resolve()
SWT_MAP_SOURCE_ROOT = SOURCE_DATA_ROOT / "SWT_MAP_DATA"
DEFAULT_ASSUMPTIONS_PATH = REFERENCES_ROOT / "default-assumptions.json"
