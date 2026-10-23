"""Exercise the distributions that users install, outside the source checkout."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", "UV_PROJECT_ENVIRONMENT"):
        env.pop(key, None)
    return subprocess.run(
        args, cwd=cwd, env=env, capture_output=True, text=True, timeout=180
    )


def uv() -> str:
    executable = shutil.which("uv")
    assert executable is not None, "Install the documented uv version first"
    return executable


def build(source: Path, output: Path) -> dict[str, Path]:
    result = run(
        uv(),
        "build",
        str(source),
        "--no-create-gitignore",
        "--out-dir",
        str(output),
        "--python",
        sys.executable,
        "--build-constraint",
        str(source / "build-constraints.txt"),
        "--require-build-hashes",
        cwd=source,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    archives = {path.suffix: path for path in output.iterdir() if path.is_file()}
    assert set(archives) == {".whl", ".gz"}
    return archives


@pytest.fixture(scope="session")
def archives(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build(ROOT, tmp_path_factory.mktemp("artifacts"))


@pytest.mark.parametrize("kind", [".whl", ".gz"], ids=["wheel", "sdist"])
def test_install_outside_checkout(
    kind: str, archives: dict[str, Path], tmp_path: Path
) -> None:
    environment = tmp_path / "consumer"
    created = run(
        uv(), "venv", str(environment), "--python", sys.executable, cwd=tmp_path
    )
    assert created.returncode == 0, created.stderr
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = run(
        uv(),
        "pip",
        "install",
        "--python",
        str(python),
        str(archives[kind]),
        "--build-constraint",
        str(ROOT / "build-constraints.txt"),
        "--require-build-hashes",
        cwd=tmp_path,
    )
    assert installed.returncode == 0, installed.stderr
    probe = run(
        str(python),
        "-I",
        "-c",
        "import enrama, importlib.metadata as m, json; "
        "d=m.distribution('enrama'); "
        "print(json.dumps({'origin': enrama.__file__, 'prefix': __import__('sys').prefix, "
        "'interpreter': list(__import__('sys').version_info[:2]), "
        "'name': d.metadata['Name'], 'version': d.version, "
        "'python': d.metadata['Requires-Python'], "
        "'license': d.metadata['License-Expression'], "
        "'license_files': d.metadata.get_all('License-File'), "
        "'requires': d.requires, 'entry_points': list(d.entry_points), "
        "'installed': sorted(x.metadata['Name'] for x in m.distributions()), "
        "'license_text': d.read_text('licenses/LICENSE')}))",
        cwd=tmp_path,
    )
    assert probe.returncode == 0, probe.stderr
    print(probe.stdout)
    metadata = json.loads(probe.stdout)
    assert Path(metadata["origin"]).is_relative_to(Path(metadata["prefix"]))
    assert not Path(metadata["origin"]).is_relative_to(ROOT)
    assert "site-packages" in Path(metadata["origin"]).parts
    assert metadata.get("interpreter") == list(sys.version_info[:2])
    assert metadata["name"] == "enrama"
    assert metadata["version"] == "0.1.0.dev0"
    assert metadata["python"] == ">=3.12"
    assert metadata["license"] == "MIT"
    assert metadata["license_files"] == ["LICENSE"]
    assert "Permission is hereby granted" in metadata["license_text"]
    assert not metadata["requires"]
    assert metadata["entry_points"] == []
    assert metadata["installed"] == ["enrama"]


def test_explicit_contents_and_repeatable_build(tmp_path: Path) -> None:
    source = tmp_path / "checkout"
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".superpowers",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
        ),
    )
    for name in (
        ".env",
        ".venv/secret",
        "clients/private.yaml",
        "src/enrama/secret.txt",
    ):
        decoy = source / name
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text("SYNTHETIC PRIVATE DATA", encoding="utf-8")
    first = build(source, tmp_path / "first")
    second = build(source, tmp_path / "second")
    for kind in first:
        assert (
            hashlib.sha256(first[kind].read_bytes()).digest()
            == hashlib.sha256(second[kind].read_bytes()).digest()
        )
    with zipfile.ZipFile(first[".whl"]) as wheel:
        assert set(wheel.namelist()) == {
            "enrama/__init__.py",
            "enrama-0.1.0.dev0.dist-info/METADATA",
            "enrama-0.1.0.dev0.dist-info/WHEEL",
            "enrama-0.1.0.dev0.dist-info/RECORD",
            "enrama-0.1.0.dev0.dist-info/licenses/LICENSE",
        }
    with tarfile.open(first[".gz"]) as sdist:
        files = {"/".join(item.name.split("/")[1:]) for item in sdist if item.isfile()}
        assert files == {
            "src/enrama/__init__.py",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "build-constraints.txt",
            "PKG-INFO",
            ".gitignore",
        }
