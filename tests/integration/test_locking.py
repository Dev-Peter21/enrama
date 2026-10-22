"""Locked verification must reject drift rather than repair project inputs."""

import shutil
from pathlib import Path

import pytest
from test_distribution import ROOT, run, uv


@pytest.mark.parametrize("drift", ["missing", "stale"])
def test_locked_sync_rejects_drift(drift: str, tmp_path: Path) -> None:
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copy2(ROOT / name, tmp_path / name)
    lock = tmp_path / "uv.lock"
    if drift == "missing":
        lock.unlink()
    else:
        project = tmp_path / "pyproject.toml"
        project.write_text(
            project.read_text().replace(
                'version = "0.1.0.dev0"', 'version = "0.1.0.dev1"'
            )
        )
    before = lock.read_bytes() if lock.exists() else None
    result = run(uv(), "sync", "--locked", "--no-install-project", cwd=tmp_path)
    assert result.returncode != 0
    assert "lockfile" in result.stderr.lower(), result.stderr
    assert (lock.read_bytes() if lock.exists() else None) == before
