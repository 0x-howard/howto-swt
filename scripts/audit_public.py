#!/usr/bin/env python3
"""Scan the publishable Free tree for Pro files, private state and credential material."""

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
PRO_DIRS = {"context-engine", "content-data"}
FORBIDDEN_NAMES = {".env", ".dev.vars", "swt-user-state.json", "howto-swt-pro-context.json"}
FORBIDDEN_SUFFIXES = {".zip", ".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}
FORBIDDEN_PARTS = {"USER_DATA"}
PATTERNS = {
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "secret assignment": re.compile(
        r"(?:API_KEY|API_TOKEN|SECRET_KEY|ACCESS_TOKEN|PRIVATE_KEY)"
        r"\s*[:=]\s*[\"']?(?!replace|example|test)[A-Za-z0-9._-]{20,}",
        re.IGNORECASE,
    ),
}
TEXT_SUFFIXES = {".js", ".mjs", ".json", ".md", ".txt", ".py", ".toml", ".yaml", ".yml", ""}


def publishable_files() -> list[Path]:
    """Files Git would publish: tracked plus untracked-but-not-ignored."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout.decode("utf-8").split("\0")
        return [Path(name) for name in listed if name and (ROOT / name).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [
            path.relative_to(ROOT) for path in ROOT.rglob("*")
            if path.is_file() and not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)
            and path.relative_to(ROOT).parts[0] not in PRO_DIRS
        ]


findings = []
for relative in publishable_files():
    path = ROOT / relative
    if relative.parts[0] in PRO_DIRS:
        findings.append(f"{relative}: Pro file would be published")
    if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
        findings.append(f"{relative}: forbidden local/private artifact")
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        findings.append(f"{relative}: private user data embedded in Free")
    if path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            findings.append(f"{relative}: {label}")
    for email in re.findall(r"[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})", text, re.IGNORECASE):
        if email.lower() not in {"example.com", "example.org", "example.net", "example.invalid"}:
            findings.append(f"{relative}: non-example email address")

if findings:
    raise SystemExit("PUBLIC_AUDIT_FAILED\n" + "\n".join(sorted(set(findings))))
print("PUBLIC_AUDIT_OK")
