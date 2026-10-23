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


@pytest.mark.parametrize(
    ("kind", "yaml_from_source"),
    [(".whl", False), (".gz", False), (".whl", True)],
    ids=["wheel", "sdist", "pyyaml-source"],
)
def test_install_outside_checkout(
    kind: str, yaml_from_source: bool, archives: dict[str, Path], tmp_path: Path
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
        *(["--no-binary", "pyyaml", "--no-cache"] if yaml_from_source else []),
        cwd=tmp_path,
    )
    assert installed.returncode == 0, installed.stderr
    if yaml_from_source:
        print(installed.stderr)
    probe_code = """
import enrama
import importlib.metadata as m
import json
import sys
from pathlib import Path
from enrama.config import EnramaConfig, ConfigurationError, load_config, parse_config
from enrama.config._language import REGISTRY_DATE
from pydantic import ValidationError

d = m.distribution("enrama")
metadata = {
    "origin": enrama.__file__, "prefix": sys.prefix,
    "interpreter": list(sys.version_info[:2]),
    "name": d.metadata["Name"], "version": d.version,
    "python": d.metadata["Requires-Python"],
    "license": d.metadata["License-Expression"],
    "license_files": d.metadata.get_all("License-File"),
    "requires": d.requires, "entry_points": list(d.entry_points),
    "installed": sorted(x.metadata["Name"] for x in m.distributions()),
    "license_text": d.read_text("licenses/LICENSE"),
    "registry": REGISTRY_DATE,
    "pyyaml": m.version("PyYAML"),
}

yaml_bytes = b'''schema_version: 1
site: {title: Shop, description: Local shop, language: ES-ar}
profile: {name: Shop, avatar: ./assets/not-present.png}
links: [{id: contact, title: Email, url: 'mailto:hi@example.com'}]
socials: [{id: social, platform: github, url: 'https://unrelated.example'}]
'''
selected = Path("selected.yaml")
selected.write_bytes(yaml_bytes)
before = sorted(str(p) for p in Path.cwd().iterdir())
metadata["loaded"] = load_config(selected).model_dump()
assert selected.read_bytes() == yaml_bytes
assert before == sorted(str(p) for p in Path.cwd().iterdir())

def forbid_io(event, arguments):
    if event == "open" or event.startswith("socket."):
        raise AssertionError("Model validation attempted I/O: " + event)

sys.addaudithook(forbid_io)
config = EnramaConfig.model_validate({
    "schema_version": 1,
    "site": {"title": "Shop", "description": "Local shop", "language": "ES-ar"},
    "profile": {"name": "Shop", "avatar": "./assets/not-present.png"},
    "links": [{"id": "contact", "title": "Email", "url": "mailto:hi@example.com"}],
    "socials": [{"id": "social", "platform": "github", "url": "https://unrelated.example"}],
})
metadata["config"] = config.model_dump()
assert parse_config(yaml_bytes) == config
try:
    parse_config(yaml_bytes + b"private: SECRET\\n")
except ConfigurationError as error:
    metadata["diagnostic"] = {
        "category": error.category, "total": error.total_count,
        "location": list(error.diagnostics[0].location),
        "position": [error.diagnostics[0].position.line, error.diagnostics[0].position.column],
    }
    assert "SECRET" not in str(error)
else:
    raise AssertionError("Invalid YAML accepted")
metadata["social_icon"] = config.socials[0].icon
try:
    EnramaConfig.model_validate({**config.model_dump(), "schema_version": True})
except ValidationError as error:
    metadata["invalid_version_location"] = list(error.errors()[0]["loc"])
else:
    raise AssertionError("Invalid version accepted")
print(json.dumps(metadata))
"""
    probe = run(str(python), "-I", "-c", probe_code, cwd=tmp_path)
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
    assert set(metadata["requires"]) == {
        "langcodes==3.5.1",
        "pydantic<3,>=2.14.1",
        "pyyaml<7,>=6.0.3",
    }
    assert metadata["pyyaml"] == "6.0.3"
    assert metadata["loaded"] == metadata["config"]
    assert metadata["diagnostic"] == {
        "category": "model_validation",
        "total": 1,
        "location": ["private"],
        "position": [6, 10],
    }
    assert metadata["registry"] == "2021-08-06"
    assert metadata["config"]["site"]["language"] == "es-AR"
    assert metadata["config"]["site"]["url"] is None
    assert metadata["config"]["socials"][0]["label"] == "GitHub"
    assert metadata["social_icon"] == "github"
    assert metadata["invalid_version_location"] == ["schema_version"]
    assert metadata["entry_points"] == []
    assert {"enrama", "pydantic", "langcodes", "PyYAML"}.issubset(metadata["installed"])
    assert not {
        "pytest",
        "ruff",
        "mypy",
        "hatchling",
        "uv",
        "types-PyYAML",
        "typer",
        "jinja2",
        "fastapi",
    }.intersection(metadata["installed"])


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
            "enrama/config/__init__.py",
            "enrama/config/_language.py",
            "enrama/config/_paths.py",
            "enrama/config/_urls.py",
            "enrama/config/_yaml.py",
            "enrama/config/diagnostics.py",
            "enrama/config/loader.py",
            "enrama/config/catalogs.py",
            "enrama/config/models.py",
            "enrama/py.typed",
            "enrama-0.1.0.dev0.dist-info/METADATA",
            "enrama-0.1.0.dev0.dist-info/WHEEL",
            "enrama-0.1.0.dev0.dist-info/RECORD",
            "enrama-0.1.0.dev0.dist-info/licenses/LICENSE",
        }
    with tarfile.open(first[".gz"]) as sdist:
        files = {"/".join(item.name.split("/")[1:]) for item in sdist if item.isfile()}
        assert files == {
            "src/enrama/__init__.py",
            "src/enrama/config/__init__.py",
            "src/enrama/config/_language.py",
            "src/enrama/config/_paths.py",
            "src/enrama/config/_urls.py",
            "src/enrama/config/_yaml.py",
            "src/enrama/config/diagnostics.py",
            "src/enrama/config/loader.py",
            "src/enrama/config/catalogs.py",
            "src/enrama/config/models.py",
            "src/enrama/py.typed",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "build-constraints.txt",
            "PKG-INFO",
            ".gitignore",
        }
