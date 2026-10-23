"""Collect CI evidence and reject missing or misleading verification results."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def write_evidence(name: str, data: object) -> None:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    rendered = json.dumps(data, indent=2, sort_keys=True)
    (reports / f"{name}.json").write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def environment() -> None:
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"
    if actual != os.environ.get("EXPECTED_PYTHON"):
        raise ValueError(f"Unexpected interpreter {actual}; expected EXPECTED_PYTHON")
    version = subprocess.run(
        ["uv", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if version.split()[1] != "0.13.5":
        raise ValueError(f"Unexpected uv version: {version}")
    write_evidence(
        "environment",
        {
            "python_minor": actual,
            "python": sys.version,
            "executable": sys.executable,
            "uv": version,
            "os": platform.platform(),
            "architecture": platform.machine(),
            "runner_os": os.environ.get("RUNNER_OS"),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
            "revision": os.environ.get("GITHUB_SHA"),
            "event": os.environ.get("GITHUB_EVENT_NAME"),
            "tools": {
                name: importlib.metadata.version(name)
                for name in ("enrama", "pytest", "ruff", "mypy")
            },
        },
    )


def report() -> None:
    root = ET.parse("reports/pytest.xml").getroot()
    cases = list(root.iter("testcase"))
    skipped = sum(case.find("skipped") is not None for case in cases)
    if list(root.iter("failure")) or list(root.iter("error")):
        raise ValueError("Test report contains failures or errors")
    passed = len(cases) - skipped
    if passed <= 0:
        raise ValueError("Test report contains no passed/executed tests")
    write_evidence("tests", {"passed": passed, "skipped": skipped, "total": len(cases)})


def artifacts() -> None:
    files = sorted(Path("dist").glob("*"))
    wheels = [path for path in files if path.suffix == ".whl"]
    sdists = [path for path in files if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("Expected exactly one wheel and one source distribution")
    write_evidence(
        "artifacts",
        [
            {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in wheels + sdists
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("environment", "report", "artifacts"))
    args = parser.parse_args()
    try:
        {"environment": environment, "report": report, "artifacts": artifacts}[
            args.command
        ]()
    except (ValueError, OSError, ET.ParseError) as error:
        parser.exit(1, f"CI evidence check failed: {error}\n")


if __name__ == "__main__":
    main()
