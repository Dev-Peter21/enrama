"""CI evidence gates must fail closed on missing or misleading results."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_distribution import ROOT, run

HELPER = ROOT / "scripts" / "ci.py"


def ci(command: str, directory: Path) -> subprocess.CompletedProcess[str]:
    return run(sys.executable, "-I", str(HELPER), command, cwd=directory)


def test_positive_report_records_executed_counts(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "pytest.xml").write_text(
        '<testsuites><testsuite><testcase name="passed"/>'
        '<testcase name="skipped"><skipped/></testcase></testsuite></testsuites>',
        encoding="utf-8",
    )
    result = ci("report", tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads((reports / "tests.json").read_text()) == {
        "passed": 1,
        "skipped": 1,
        "total": 2,
    }


@pytest.mark.parametrize(
    "content",
    [
        None,
        "not XML",
        "<testsuites/>",
        "<testsuite><testcase><skipped/></testcase></testsuite>",
        "<testsuite><testcase/><testcase><failure/></testcase></testsuite>",
        "<testsuite><testcase/><testcase><error/></testcase></testsuite>",
    ],
)
def test_invalid_report_fails(content: str | None, tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    if content is not None:
        (reports / "pytest.xml").write_text(content, encoding="utf-8")
    result = ci("report", tmp_path)
    assert result.returncode != 0
    assert not (reports / "tests.json").exists()


def test_environment_asserts_real_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "EXPECTED_PYTHON", f"{sys.version_info.major}.{sys.version_info.minor}"
    )
    result = ci("environment", tmp_path)
    assert result.returncode == 0, result.stderr
    metadata = json.loads((tmp_path / "reports/environment.json").read_text())
    assert metadata["python_minor"] == os.environ["EXPECTED_PYTHON"]
    assert metadata["executable"] == sys.executable
    assert metadata["uv"].startswith("uv 0.13.5")


def test_environment_rejects_wrong_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EXPECTED_PYTHON", "0.0")
    result = ci("environment", tmp_path)
    assert result.returncode != 0
    assert "interpreter" in result.stderr.lower()
    assert not (tmp_path / "reports/environment.json").exists()


@pytest.mark.parametrize("files", [[], ["enrama-0.1.0.dev0.whl"]])
def test_missing_distribution_fails(files: list[str], tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    for name in files:
        (dist / name).write_bytes(b"synthetic")
    result = ci("artifacts", tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "reports/artifacts.json").exists()


def test_artifact_evidence_hashes_both_formats(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    for name in ("enrama-0.1.0.dev0.whl", "enrama-0.1.0.dev0.tar.gz"):
        (dist / name).write_bytes(b"abc")
    result = ci("artifacts", tmp_path)
    assert result.returncode == 0, result.stderr
    metadata = json.loads((tmp_path / "reports/artifacts.json").read_text())
    assert len(metadata) == 2
    assert all(
        item["sha256"]
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        for item in metadata
    )
