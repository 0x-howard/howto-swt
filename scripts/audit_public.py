#!/usr/bin/env python3
"""Scan the Free public tree for private state and obvious credential material."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
FORBIDDEN_NAMES = {
    ".env", ".dev.vars", "auth.json", "offline-device-key.json",
    "members.csv", "update-state.json",
}
FORBIDDEN_SUFFIXES = {".zip", ".bundle", ".enc", ".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}
FORBIDDEN_PARTS = {"howto-swt-pro", "howto-cloud", "howto-admin", "howto-swt-pro-dist", "USER_DATA"}
PATTERNS = {
    "private key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "Resend API key": re.compile(r"(?<![A-Za-z0-9_])re_[A-Za-z0-9_]{20,}"),
    "secret assignment": re.compile(
        r"(?:OTP_PEPPER|CLOUDFLARE_(?:API_)?TOKEN|SESSION_TOKEN|ACTIVATION_TOKEN|RELEASE_KEY|SIGNING_PRIVATE_KEY)"
        r"\s*[:=]\s*[\"']?(?!replace|example|test)[A-Za-z0-9._-]{20,}",
        re.IGNORECASE,
    ),
}
TEXT_SUFFIXES = {".js", ".mjs", ".json", ".md", ".txt", ".py", ".toml", ".yaml", ".yml", ""}
findings = []

for path in ROOT.rglob("*"):
    if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
        findings.append(f"{relative}: forbidden local/private artifact")
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        findings.append(f"{relative}: private component embedded in Free")
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
