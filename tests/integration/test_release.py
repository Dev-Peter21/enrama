"""Release preparation must preserve identity, archive bytes and existing data."""

import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/release.py"
WHEEL = "enrama-0.1.0-py3-none-any.whl"
SDIST = "enrama-0.1.0.tar.gz"
SCHEMA = "enrama-v1.schema.json"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def candidate(tmp_path: Path) -> tuple[Path, Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    project = '[project]\nname = "enrama"\nversion = "0.1.0"\n'
    (source / "pyproject.toml").write_text(project)
    (source / "schemas").mkdir()
    schema = (
        b'{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}\n'
    )
    (source / "schemas" / SCHEMA).write_bytes(schema)
    git(source, "init", "-q")
    git(source, "add", ".")
    git(
        source,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.com",
        "commit",
        "-qm",
        "fixture",
    )
    archives = tmp_path / "archives"
    archives.mkdir()
    metadata = b"Metadata-Version: 2.4\nName: enrama\nVersion: 0.1.0\nRequires-Python: >=3.12\nLicense-Expression: MIT\n\n"
    with zipfile.ZipFile(archives / WHEEL, "w") as z:
        z.writestr("enrama-0.1.0.dist-info/METADATA", metadata)
    with tarfile.open(archives / SDIST, "w:gz") as t:
        for name, data in {
            "PKG-INFO": metadata,
            "pyproject.toml": project.encode(),
            "schemas/" + SCHEMA: schema,
        }.items():
            item = tarfile.TarInfo("enrama-0.1.0/" + name)
            item.size = len(data)
            t.addfile(item, io.BytesIO(data))
    return source, archives, git(source, "rev-parse", "HEAD")


def release(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "-I", str(HELPER), *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode:
        assert (
            result.returncode == 1 and "Release preparation failed:" in result.stderr
        ), result.stderr
    return result


def bundle(
    candidate: tuple[Path, Path, str], output: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    source, archives, sha = candidate
    return release(
        "bundle",
        "--source",
        str(source),
        "--archives",
        str(archives),
        "--output",
        str(output),
        "--expected-sha",
        sha,
        "--expected-version",
        "0.1.0",
        *extra,
    )


def verify(output: Path, sha: str) -> subprocess.CompletedProcess[str]:
    return release(
        "verify",
        "--bundle",
        str(output),
        "--expected-sha",
        sha,
        "--expected-version",
        "0.1.0",
    )


def test_explicit_invalid_bundle_never_falls_back_to_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ENRAMA_RELEASE_BUNDLE", str(tmp_path / "missing"))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(ROOT / "tests/integration/test_distribution.py")
            + "::test_install_outside_checkout[wheel]",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Explicit release bundle failed verification" in result.stdout


def test_bundle_copies_exact_bytes_and_verifies(
    candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    source, archives, sha = candidate
    output = tmp_path / "bundle"
    result = bundle(candidate, output)
    assert result.returncode == 0, result.stderr
    assert {p.name for p in output.iterdir()} == {
        WHEEL,
        SDIST,
        SCHEMA,
        "release.json",
        "SHA256SUMS",
    }
    assert (output / WHEEL).read_bytes() == (archives / WHEEL).read_bytes()
    assert (output / SDIST).read_bytes() == (archives / SDIST).read_bytes()
    assert (output / SCHEMA).read_bytes() == (source / "schemas" / SCHEMA).read_bytes()
    record = json.loads((output / "release.json").read_text())
    assert record["source_sha"] == sha and record["version"] == "0.1.0"
    assert record["tag"] == "v0.1.0" and record["publication_authorized"] is False
    assert record["source_ci"] is None
    for line in (output / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ")
        assert digest == hashlib.sha256((output / name).read_bytes()).hexdigest()
    assert verify(output, sha).returncode == 0


@pytest.mark.parametrize(
    "fault", ["wrong-sha", "malformed-sha", "wrong-version", "dirty"]
)
def test_source_identity_failures_leave_no_bundle(
    fault: str, candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    source, archives, sha = candidate
    if fault == "dirty":
        (source / "unreviewed.txt").write_text("unreviewed")
    result = release(
        "bundle",
        "--source",
        str(source),
        "--archives",
        str(archives),
        "--output",
        str(tmp_path / "bundle"),
        "--expected-sha",
        "broken"
        if fault == "malformed-sha"
        else "0" * 40
        if fault == "wrong-sha"
        else sha,
        "--expected-version",
        "0.1.1" if fault == "wrong-version" else "0.1.0",
    )
    assert result.returncode != 0
    assert not (tmp_path / "bundle").exists()


@pytest.mark.parametrize("fault", ["ref", "repository", "sha"])
def test_main_gate_rejects_wrong_dispatch(
    fault: str, candidate: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _, sha = candidate
    values = {
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "Dev-Peter21/enrama",
        "GITHUB_SHA": sha,
    }
    values[
        {"ref": "GITHUB_REF", "repository": "GITHUB_REPOSITORY", "sha": "GITHUB_SHA"}[
            fault
        ]
    ] = "wrong"
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    result = release(
        "check-source",
        "--source",
        str(source),
        "--expected-sha",
        sha,
        "--expected-version",
        "0.1.0",
        "--require-main",
    )
    assert result.returncode != 0


def test_main_bundle_requires_successful_exact_source_ci(
    candidate: tuple[Path, Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, sha = candidate
    for key, value in {
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "Dev-Peter21/enrama",
        "GITHUB_SHA": sha,
    }.items():
        monkeypatch.setenv(key, value)
    assert bundle(candidate, tmp_path / "missing", "--require-main").returncode != 0
    report = tmp_path / "ci.json"
    report.write_text(
        json.dumps(
            [
                {
                    "databaseId": 42,
                    "headSha": sha,
                    "headBranch": "main",
                    "event": "push",
                    "workflowName": "CI",
                    "status": "completed",
                    "conclusion": "success",
                }
            ]
        )
    )
    result = bundle(
        candidate, tmp_path / "bundle", "--require-main", "--ci-report", str(report)
    )
    assert result.returncode == 0, result.stderr
    assert (
        json.loads((tmp_path / "bundle/release.json").read_text())["source_ci"][
            "databaseId"
        ]
        == 42
    )


@pytest.mark.parametrize("fault", ["empty", "failed", "wrong-source"])
def test_ci_gate_fails_closed(
    fault: str, candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    _, _, sha = candidate
    report = tmp_path / "ci.json"
    data = [
        {
            "databaseId": 42,
            "headSha": sha,
            "headBranch": "main",
            "event": "push",
            "workflowName": "CI",
            "status": "completed",
            "conclusion": "success",
        }
    ]
    if fault == "empty":
        data = []
    else:
        data[0]["conclusion" if fault == "failed" else "headSha"] = (
            "failure" if fault == "failed" else "0" * 40
        )
    report.write_text(json.dumps(data))
    assert (
        bundle(candidate, tmp_path / "bundle", "--ci-report", str(report)).returncode
        != 0
    )
    assert not (tmp_path / "bundle").exists()


def test_existing_output_is_never_overwritten(
    candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    output = tmp_path / "bundle"
    output.mkdir()
    (output / "mine").write_bytes(b"KEEP")
    assert bundle(candidate, output).returncode != 0
    assert (output / "mine").read_bytes() == b"KEEP"


@pytest.mark.parametrize("fault", ["missing", "extra", "metadata", "link"])
def test_invalid_archives_fail_before_output(
    fault: str, candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    _, archives, _ = candidate
    if fault == "missing":
        (archives / WHEEL).unlink()
    elif fault == "extra":
        (archives / "unreviewed.whl").write_bytes(b"bad")
    elif fault == "metadata":
        with zipfile.ZipFile(archives / WHEEL, "w") as z:
            z.writestr(
                "enrama-0.1.0.dist-info/METADATA", "Name: other\nVersion: 0.1.0\n"
            )
    else:
        original = archives / WHEEL
        target = tmp_path / "original.whl"
        original.rename(target)
        try:
            original.symlink_to(target)
        except OSError:
            pytest.skip("File symlinks unavailable")
    assert bundle(candidate, tmp_path / "bundle").returncode != 0
    assert not (tmp_path / "bundle").exists()


@pytest.mark.parametrize(
    "fault", ["payload", "manifest", "checksum", "extra", "missing", "link"]
)
def test_downloaded_bundle_tampering_is_rejected(
    fault: str, candidate: tuple[Path, Path, str], tmp_path: Path
) -> None:
    output = tmp_path / "bundle"
    prepared = bundle(candidate, output)
    assert prepared.returncode == 0, prepared.stderr
    if fault in {"payload", "manifest", "checksum"}:
        name = {"payload": WHEEL, "manifest": "release.json", "checksum": "SHA256SUMS"}[
            fault
        ]
        with (output / name).open("ab") as f:
            f.write(b"tampered")
    elif fault == "extra":
        (output / "unreviewed").mkdir()
    elif fault == "missing":
        (output / SCHEMA).unlink()
    else:
        (output / WHEEL).unlink()
        try:
            (output / WHEEL).symlink_to(candidate[1] / WHEEL)
        except OSError:
            pytest.skip("File symlinks unavailable")
    assert verify(output, candidate[2]).returncode != 0
