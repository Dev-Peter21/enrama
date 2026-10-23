"""The repository helper generates/checks only its own artifact from any cwd."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from enrama.config.schema import generate_schema

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def helper(tmp_path: Path) -> Path:
    script = tmp_path / "checkout/scripts/schema.py"
    script.parent.mkdir(parents=True)
    assert (ROOT / "scripts/schema.py").is_file(), "Schema helper is not implemented"
    shutil.copyfile(ROOT / "scripts/schema.py", script)
    return script


def invoke(helper: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(helper), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=20,
    )


def artifact(helper: Path) -> Path:
    return helper.parents[1] / "schemas/enrama-v1.schema.json"


def test_generate_from_unrelated_cwd_is_repeatable(
    helper: Path, tmp_path: Path
) -> None:
    before = sorted(tmp_path.iterdir())
    first = invoke(helper, tmp_path)
    assert first.returncode == 0, first.stderr
    expected = generate_schema()
    assert artifact(helper).read_bytes() == expected
    assert invoke(helper, tmp_path).returncode == 0
    assert artifact(helper).read_bytes() == expected
    assert sorted(tmp_path.iterdir()) == before
    assert not (tmp_path / "schemas").exists()


@pytest.mark.parametrize("content", [None, b"", b"{}\n", b"not JSON"])
def test_check_rejects_missing_or_stale_without_writing(
    helper: Path,
    tmp_path: Path,
    content: bytes | None,
) -> None:
    output = artifact(helper)
    if content is not None:
        output.parent.mkdir()
        output.write_bytes(content)
    before = {p: p.read_bytes() for p in helper.parents[1].rglob("*") if p.is_file()}
    result = invoke(helper, tmp_path, "--check")
    assert result.returncode == 1
    assert "schema" in result.stderr.lower()
    after = {p: p.read_bytes() for p in helper.parents[1].rglob("*") if p.is_file()}
    assert after == before


def test_check_current_schema_does_not_rewrite(helper: Path, tmp_path: Path) -> None:
    output = artifact(helper)
    output.parent.mkdir()
    output.write_bytes(generate_schema())
    before = output.stat().st_mtime_ns
    result = invoke(helper, tmp_path, "--check")
    assert result.returncode == 0, result.stderr
    assert output.stat().st_mtime_ns == before


@pytest.mark.parametrize("check", [False, True])
def test_nonregular_artifact_is_operational_failure(
    helper: Path,
    tmp_path: Path,
    check: bool,
) -> None:
    output = artifact(helper)
    output.mkdir(parents=True)
    result = invoke(helper, tmp_path, *(["--check"] if check else []))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert output.is_dir()


@pytest.mark.parametrize("target", ["directory", "file"])
@pytest.mark.parametrize("check", [False, True])
def test_symlinks_never_replace_outside_data(
    helper: Path,
    tmp_path: Path,
    target: str,
    check: bool,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "enrama-v1.schema.json"
    secret.write_bytes(b"preserve")
    output = artifact(helper)
    try:
        if target == "directory":
            output.parent.symlink_to(outside, target_is_directory=True)
        else:
            output.parent.mkdir()
            output.symlink_to(secret)
    except OSError:
        pytest.skip("OS does not permit creating test symlinks")
    result = invoke(helper, tmp_path, *(["--check"] if check else []))
    assert result.returncode == 1
    assert secret.read_bytes() == b"preserve"
    assert "Traceback" not in result.stderr


def test_invalid_argument_is_usage_failure(helper: Path, tmp_path: Path) -> None:
    result = invoke(helper, tmp_path, "--output", "other.json")
    assert result.returncode == 2
    assert not artifact(helper).exists()


@pytest.mark.skipif(
    not hasattr(os, "mkfifo"), reason="FIFOs are unavailable on Windows"
)
@pytest.mark.parametrize("check", [False, True])
def test_fifo_artifact_fails_without_waiting_for_a_peer(
    helper: Path, tmp_path: Path, check: bool
) -> None:
    output = artifact(helper)
    output.parent.mkdir()
    os.mkfifo(output)
    result = subprocess.run(
        [sys.executable, "-I", str(helper), *(["--check"] if check else [])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_git_checkout_preserves_schema_bytes_with_autocrlf(tmp_path: Path) -> None:
    checkout = tmp_path / "git-checkout"
    checkout.mkdir()
    output = checkout / "schemas/enrama-v1.schema.json"
    output.parent.mkdir()
    output.write_bytes(generate_schema())
    attributes = ROOT / ".gitattributes"
    if attributes.exists():
        shutil.copyfile(attributes, checkout / ".gitattributes")
    git = shutil.which("git")
    assert git is not None
    for args in (("init", "--quiet"), ("add", ".")):
        subprocess.run(
            [git, "-c", "core.autocrlf=true", *args],
            cwd=checkout,
            check=True,
            capture_output=True,
        )
    output.unlink()
    subprocess.run(
        [git, "-c", "core.autocrlf=true", "checkout-index", "--all", "--force"],
        cwd=checkout,
        check=True,
        capture_output=True,
    )
    assert output.read_bytes() == generate_schema()
