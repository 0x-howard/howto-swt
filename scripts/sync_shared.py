#!/usr/bin/env python3
"""Build canonical shared runtime references and optional flat deployments."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from paths import PLUGIN_ROOT, REFERENCES_ROOT, RUNTIME_ROOT, SHARED_ROOT, SKILLS_ROOT


CURRENT_VERSION = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]

COMMON_SOURCES = (
    "interaction-protocol.md",
    "answer-framework.md",
    "editorial-policy.md",
    "creator-attribution.md",
    "risk-policy.md",
    "evidence-policy.md",
    "state-schema.md",
    "decision-model.md",
    "handoff-contract.md",
    "executor-state-machines.md",
    "persistence-contract.md",
)

SOURCES_BY_SKILL = {
    "swt": COMMON_SOURCES + ("routing-policy.md", "stage-model.md"),
    "swt-application": COMMON_SOURCES,
    "swt-position": COMMON_SOURCES,
    "swt-english": COMMON_SOURCES,
    "swt-visa": COMMON_SOURCES + ("official-sources.md",),
    "swt-arrival": COMMON_SOURCES + ("official-sources.md",),
}

DOMAIN_REFERENCES_BY_SKILL = {
    "swt": (),
    "swt-application": ("agency-sponsor.md", "application-materials.md"),
    "swt-position": ("location-offer.md", "budget-method.md", "tax-estimation.md", "state-income-tax.md", "default-assumptions.json"),
    "swt-english": (
        "english-practice.md", "english-assessment.md", "english-rubric.md",
        "english-profiles.md", "english-question-bank.md",
    ),
    "swt-visa": ("visa-ds2019.md",),
    "swt-arrival": ("predeparture-program.md",),
}

COMMON_PORTABLE_SCRIPTS = ("decision_model.py", "orchestration.py", "paths.py", "user_state.py")
PORTABLE_SCRIPTS_BY_SKILL = {
    "swt": COMMON_PORTABLE_SCRIPTS,
    "swt-application": COMMON_PORTABLE_SCRIPTS,
    "swt-position": COMMON_PORTABLE_SCRIPTS + (
        "budget.py", "compare_budget.py", "location_context.py", "state_context.py", "swt_market.py",
    ),
    "swt-english": COMMON_PORTABLE_SCRIPTS + ("speaking_score.py",),
    "swt-visa": COMMON_PORTABLE_SCRIPTS,
    "swt-arrival": COMMON_PORTABLE_SCRIPTS,
}
PORTABLE_ASSETS_BY_SKILL = {
    "swt-position": (
        "budget-example.json", "net-income-example.json", "position-overview-example.json",
    ),
}


def render(skill: str, sources: tuple[str, ...]) -> str:
    chunks: list[str] = []
    digest = hashlib.sha256()
    for filename in sources:
        path = SHARED_ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing shared source: {path}")
        body = path.read_text(encoding="utf-8").strip()
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        digest.update(body.encode("utf-8"))
        chunks.append(f"<!-- source: shared/{filename} -->\n\n{body}")

    merged_body = "\n\n---\n\n".join(chunks)
    # Source-relative Markdown links point into shared/; generated runtime files
    # live under references/shared-runtime/ and resolve internal sections instead.
    merged_body = merged_body.replace(
        "[decision-model.md](decision-model.md)",
        "[decision model](#structured-decision-architecture)",
    )
    merged_body = merged_body.replace(
        "[persistence-contract.md](persistence-contract.md)",
        "[persistence contract](#user-data-and-persistence-contract)",
    )
    merged_body = merged_body.replace(
        "[Handoff Contract](handoff-contract.md)",
        "[Handoff Contract](#skill-to-skill-handoff-contract)",
    )
    merged_body = merged_body.replace(
        "[Domain Executor State Machines](executor-state-machines.md)",
        "[Domain Executor State Machines](#domain-executor-state-machines)",
    )
    merged_body = merged_body.replace(
        "[user-state.schema.json](../references/user-state.schema.json)",
        "[user state schema](../user-state.schema.json)",
    )

    checksum = digest.hexdigest()
    source_list = ", ".join(f"shared/{filename}" for filename in sources)
    header = (
        "# Generated Shared Runtime\n\n"
        "<!-- GENERATED FILE: DO NOT EDIT. -->\n"
        f"<!-- Source: {source_list} -->\n"
        f"<!-- runtime-version: {CURRENT_VERSION} -->\n"
        "<!-- Regenerate with: python3 scripts/sync_shared.py -->\n"
        f"<!-- skill: {skill}; source-sha256: {checksum} -->"
    )
    return header + "\n\n" + merged_body + "\n"


def sync(check: bool) -> list[str]:
    stale: list[str] = []
    for skill, sources in SOURCES_BY_SKILL.items():
        skill_root = SKILLS_ROOT / skill
        if not (skill_root / "SKILL.md").is_file():
            raise FileNotFoundError(f"missing Skill: {skill_root / 'SKILL.md'}")
        output = RUNTIME_ROOT / f"{skill}.md"
        expected = render(skill, sources)
        if check:
            if not output.is_file() or output.read_text(encoding="utf-8") != expected:
                stale.append(str(output.relative_to(PLUGIN_ROOT)))
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8")
    if check:
        stale.extend(check_portable_bundles())
    else:
        write_portable_bundles()
    return stale


def portable_sources(skill: str) -> dict[Path, Path]:
    """Map each installable Skill's local runtime paths to canonical sources."""
    sources: dict[Path, Path] = {
        Path("references") / "shared-runtime" / f"{skill}.md": RUNTIME_ROOT / f"{skill}.md",
        Path("references") / "user-state.schema.json": REFERENCES_ROOT / "user-state.schema.json",
    }
    for filename in DOMAIN_REFERENCES_BY_SKILL[skill]:
        sources[Path("references") / filename] = REFERENCES_ROOT / filename
    if skill == "swt-position":
        for directory in ("state_context", "swt_market"):
            canonical = REFERENCES_ROOT / "knowledge" / directory
            for path in canonical.rglob("*"):
                if path.is_file():
                    sources[Path("references") / "knowledge" / directory / path.relative_to(canonical)] = path
    for filename in PORTABLE_SCRIPTS_BY_SKILL[skill]:
        sources[Path("scripts") / filename] = PLUGIN_ROOT / "scripts" / filename
    for filename in PORTABLE_ASSETS_BY_SKILL.get(skill, ()):
        sources[Path("assets") / filename] = PLUGIN_ROOT / "assets" / filename
    return sources


def _portable_stale(skill: str) -> list[str]:
    skill_root = SKILLS_ROOT / skill
    sources = portable_sources(skill)
    expected_paths = set(sources)
    stale: list[str] = []
    allowed_root_entries = {"SKILL.md", "references", "scripts", "assets"}
    for path in skill_root.iterdir():
        if path.name not in allowed_root_entries:
            stale.append(f"{path.relative_to(PLUGIN_ROOT)} (unexpected package entry)")
    for relative, source in sources.items():
        output = skill_root / relative
        if not output.is_file() or output.read_bytes() != source.read_bytes():
            stale.append(str(output.relative_to(PLUGIN_ROOT)))
    for group in ("references", "scripts", "assets"):
        root = skill_root / group
        if root.is_dir():
            for path in root.rglob("*"):
                if path.is_file() and path.relative_to(skill_root) not in expected_paths:
                    stale.append(f"{path.relative_to(PLUGIN_ROOT)} (unexpected bundled file)")
    return stale


def check_portable_bundles() -> list[str]:
    stale: list[str] = []
    for skill in SOURCES_BY_SKILL:
        stale.extend(_portable_stale(skill))
    return stale


def write_portable_bundles() -> None:
    for skill in SOURCES_BY_SKILL:
        skill_root = SKILLS_ROOT / skill
        for relative, source in portable_sources(skill).items():
            output = skill_root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)


def map_runtime(runtime_root: Path) -> None:
    """Copy each self-contained Skill into the selected per-Skill deployment root."""
    destination = runtime_root.expanduser().resolve()
    if destination == PLUGIN_ROOT or PLUGIN_ROOT in destination.parents:
        raise ValueError("--runtime-root must be outside the source plugin root")
    if not RUNTIME_ROOT.exists():
        sync(check=False)
    for skill in DOMAIN_REFERENCES_BY_SKILL:
        skill_destination = destination / skill
        shutil.copytree(SKILLS_ROOT / skill, skill_destination, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when generated references are stale")
    parser.add_argument(
        "--runtime-root",
        type=Path,
        help="also materialize a flat per-Skill runtime under this deployment directory",
    )
    args = parser.parse_args()
    if args.check and args.runtime_root:
        parser.error("--check and --runtime-root cannot be combined")
    stale = sync(args.check)
    if stale:
        print("stale generated references:")
        for path in stale:
            print(f"- {path}")
        return 1
    if args.runtime_root:
        map_runtime(args.runtime_root)
        print(f"flat Skill runtime mapped to {args.runtime_root}")
    else:
        print("shared runtime references are current" if args.check else "shared runtime references updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
