from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    # Spec Kit manifests contain SHA-256 file digests that trigger entropy-based false positives.
    excluded = (
        r"(^|[\\/])(\.git|\.venv|__pycache__|\.pytest_cache|\.ruff_cache|htmlcov)([\\/]|$)"
        r"|(^|[\\/])\.specify[\\/](integrations[\\/].*\.manifest\.json"
        r"|memory[\\/]\.constitution-template\.json)$"
    )
    scanner = shutil.which("detect-secrets")
    if scanner is None:
        executable = "detect-secrets.exe" if os.name == "nt" else "detect-secrets"
        scanner = str(Path(sys.executable).parent / executable)
    result = subprocess.run(
        [
            scanner,
            "scan",
            "--all-files",
            "--exclude-files",
            excluded,
            str(root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        return result.returncode

    scan: dict[str, Any] = json.loads(result.stdout)
    findings = scan.get("results", {})
    if findings:
        for filename, matches in findings.items():
            print(f"Potential secret finding: {filename} ({len(matches)} match(es))")
        return 1

    print("No secrets detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
