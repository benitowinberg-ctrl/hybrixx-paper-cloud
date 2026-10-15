"""Repository-level baseline: block common secrets and unsafe publicly tracked files.

This is NOT authentication, WAF, or a guarantee against all leaked secrets.
This script prints only file names, line numbers, and rule names, never values.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DANGEROUS_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
TEXT_SUFFIXES = {".py", ".html", ".js", ".json", ".yaml", ".yml", ".md", ".txt", ".sh"}
RULES = {
    "github-classic-token": re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}"),
    "github-fine-grained-token": re.compile(r"github_pat_[A-Za-z0-9_]{35,}"),
    "google-api-key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "live-payment-key": re.compile(r"(?<![A-Za-z0-9])(?:sk_live_|rk_live_)[A-Za-z0-9]{16,}"),
    "plaintext-credential": re.compile(
        r"""(?i)\b(?:api[_-]?secret|api[_-]?key|password|secret[_-]?key)\s*[:=]\s*['"][A-Za-z0-9+/=_!@#%.:-]{14,}['"]"""
    ),
}
BLOCKED_FIELDS = {"password", "api_key", "api_secret", "secret_key", "access_token", "refresh_token", "private_key"}


def tracked_paths(root=ROOT):
    p = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    return [Path(raw.decode("utf-8")) for raw in p.stdout.split(b"\0") if raw]


def scan_tree(obj, location="state"):
    findings = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            current = f"{location}.{key}"
            if key.lower() in BLOCKED_FIELDS:
                findings.append((current, "private-state-field"))
            else:
                findings.extend(scan_tree(value, current))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            findings.extend(scan_tree(value, f"{location}[{index}]"))
    return findings


def check(root=ROOT):
    findings = []
    for relative in tracked_paths(root):
        path = root / relative
        if not path.is_file():
            continue
        name = relative.name.lower()
        if name.startswith(".env") or path.suffix.lower() in DANGEROUS_SUFFIXES:
            findings.append((str(relative), 0, "unsafe-tracked-file"))
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            data = path.read_text(encoding="utf-8", errors="replace")
            for rule_name, rule in RULES.items():
                for match in rule.finditer(data):
                    line = data.count("\n", 0, match.start()) + 1
                    findings.append((str(relative), line, rule_name))
    public_state = root / "state.json"
    if public_state.is_file():
        try:
            obj = json.loads(public_state.read_text(encoding="utf-8"))
            for location, name in scan_tree(obj):
                findings.append((location, 0, name))
        except (ValueError, OSError):
            findings.append(("state.json", 0, "unreadable-public-state"))
    return findings


def main():
    issues = check()
    if issues:
        for file, line, name in issues:
            print(f"SECURITY BLOCK: {file}:{line} [{name}]")
        raise SystemExit(1)
    print("HYBRIXX baseline security scan: PASS (not an authentication check)")


if __name__ == "__main__":
    main()
