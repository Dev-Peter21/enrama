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
from enrama.config.schema import generate_schema
from pydantic import ValidationError

d = m.distribution("enrama")
metadata = {
    "origin": enrama.__file__, "prefix": sys.prefix,
    "interpreter": list(sys.version_info[:2]),
    "name": d.metadata["Name"], "version": d.version,
    "python": d.metadata["Requires-Python"],
    "license": d.metadata["License-Expression"],
    "license_files": d.metadata.get_all("License-File"),
    "requires": d.requires, "entry_points": [{"name": e.name, "value": e.value, "group": e.group} for e in d.entry_points],
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

generated_schema = json.loads(generate_schema())
metadata["schema_dialect"] = generated_schema["$schema"]
metadata["schema_required"] = generated_schema["required"]


# Real image preparation/copy from the installed distribution, not the checkout.
import io
from PIL import Image, features
from enrama.core import prepare_assets, copy_assets
metadata["pillow"] = m.version("Pillow")
metadata["asset_codecs"] = {
    "jpeg": features.check_codec("jpg"), "png": features.check_codec("zlib"),
    "webp": features.check_module("webp"),
}
assert all(metadata["asset_codecs"].values())
client = Path("asset-client")
client.mkdir()
stage = client / "work"
stage.mkdir()
metadata["asset_formats"] = {}
for fmt, suffix in [("PNG", "png"), ("JPEG", "jpg"), ("WEBP", "webp"), ("ICO", "ico")]:
    stream = io.BytesIO()
    with Image.new("RGB", (16, 16), "red") as im:
        im.save(stream, format=fmt)
    original = stream.getvalue()
    image_file = client / ("image." + suffix)
    image_file.write_bytes(original)
    config_data = {
        "schema_version": 1,
        "site": {"title": "Assets", "description": "Assets", "language": "en"},
        "profile": {"name": "Assets"},
    }
    field = "favicon" if fmt == "ICO" else "avatar"
    section = "site" if fmt == "ICO" else "profile"
    config_data[section][field] = image_file.name
    asset_config = EnramaConfig.model_validate(config_data)
    before_assets = sorted(stage.rglob("*"))
    snapshots = prepare_assets(asset_config, source=client / "selected.yaml", reserved_paths=(Path("work"),))
    assert sorted(stage.rglob("*")) == before_assets
    copy_assets(snapshots, stage.resolve())
    public_path = snapshots.mapping[section + "." + field]
    assert (stage / public_path).read_bytes() == original
    assert image_file.read_bytes() == original
    assert not (client / "dist").exists()
    metadata["asset_formats"][fmt] = public_path.rsplit(".", 1)[1]

# Shared template must load from the installed package, independent of cwd.
from html.parser import HTMLParser
from importlib.resources import files
from enrama.core import render_html
class RenderedDocument(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

plain = '<script>alert(1)</script> & "quoted" {{7*7}}'
render_data = {
    "schema_version": 1,
    "site": {"title": plain, "description": plain, "language": "en", "url": "https://example.com/client", "favicon": "image.ico", "og_image": "image.png"},
    "profile": {"name": plain, "avatar": "image.png"},
    "links": [{"id": "go", "title": plain, "url": "https://other.example/?a=1&b=2", "icon": "globe"}],
}
metadata["jinja2"] = m.version("Jinja2")
metadata["markupsafe"] = m.version("MarkupSafe")
resource = files("enrama").joinpath("_templates", "base.html")
assert "site-packages" in str(resource)
metadata["rendered_themes"] = []
for theme in ("minimal", "bold"):
    render_config = EnramaConfig.model_validate({**render_data, "theme": {"name": theme}})
    render_assets = prepare_assets(render_config, source=client / "selected.yaml")
    html = render_html(render_config, render_assets)
    document = RenderedDocument(html)
    assert not any(tag in ("script", "style", "base") for tag, attrs in document.elements)
    assert sum(tag == "svg" for tag, attrs in document.elements) == 1
    assert all(attrs.get("aria-hidden") == "true" for tag, attrs in document.elements if tag == "svg")
    assert sum(tag == "main" for tag, attrs in document.elements) == 1
    assert "&lt;script&gt;" in html and "{{7*7}}" in html
    anchors = [attrs for tag, attrs in document.elements if tag == "a"]
    assert anchors == [{"href": "https://other.example/?a=1&b=2"}]
    metas = {attrs.get("property", attrs.get("name")): attrs.get("content") for tag, attrs in document.elements if tag == "meta"}
    assert metas["og:title"] == plain
    assert metas["og:url"] == "https://example.com/client/"
    assert metas["og:image"] == "https://example.com/client/" + render_assets.mapping["site.og_image"]
    metadata["rendered_themes"].append(theme)

# Rendering may read only its fixed installed template, never client files/network.
original_config = render_config.model_dump()
original_assets = render_assets
expected_html = render_html(render_config, render_assets)
allowed_render_reads = {str(files("enrama").joinpath(str(path).split("enrama/", 1)[1])) for path in d.files if str(path).startswith(("enrama/_templates/", "enrama/_themes/", "enrama/_icons/"))}
def restrict_render_io(event, arguments):
    if event == "open" and arguments[0] not in allowed_render_reads:
        raise AssertionError("Renderer opened an unexpected resource")
    if event.startswith("socket."):
        raise AssertionError("Renderer attempted network I/O")
sys.addaudithook(restrict_render_io)
assert render_html(render_config, render_assets) == expected_html
assert render_config.model_dump() == original_config and render_assets == original_assets
metadata["render_io_restricted"] = True

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
        "pillow==13.0.0",
        "jinja2<4,>=3.1.6",
        "typer<1,>=0.20",
    }
    assert metadata["jinja2"]
    assert metadata["markupsafe"]
    assert metadata["rendered_themes"] == ["minimal", "bold"]
    assert metadata["render_io_restricted"] is True
    assert metadata["pillow"] == "13.0.0"
    assert metadata["asset_codecs"] == {"jpeg": True, "png": True, "webp": True}
    assert metadata["asset_formats"] == {
        "PNG": "png",
        "JPEG": "jpg",
        "WEBP": "webp",
        "ICO": "ico",
    }
    assert metadata["pyyaml"] == "6.0.3"
    assert metadata["loaded"] == metadata["config"]
    assert metadata["diagnostic"] == {
        "category": "model_validation",
        "total": 1,
        "location": ["private"],
        "position": [6, 10],
    }
    assert metadata["schema_dialect"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(metadata["schema_required"]) == {"schema_version", "site", "profile"}
    assert metadata["registry"] == "2021-08-06"
    assert metadata["config"]["site"]["language"] == "es-AR"
    assert metadata["config"]["site"]["url"] is None
    assert metadata["config"]["socials"][0]["label"] == "GitHub"
    assert metadata["social_icon"] == "github"
    assert metadata["invalid_version_location"] == ["schema_version"]
    assert metadata["entry_points"] == [
        {"name": "enrama", "value": "enrama.cli:app", "group": "console_scripts"}
    ]
    assert {"enrama", "pydantic", "langcodes", "PyYAML"}.issubset(metadata["installed"])
    assert not {
        "pytest",
        "ruff",
        "mypy",
        "hatchling",
        "uv",
        "types-PyYAML",
        "jsonschema",
        "types-jsonschema",
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
            "enrama/__main__.py",
            "enrama/cli.py",
            "enrama/project.py",
            "enrama/preview.py",
            "enrama/config/__init__.py",
            "enrama/config/_language.py",
            "enrama/config/_paths.py",
            "enrama/config/_urls.py",
            "enrama/config/_yaml.py",
            "enrama/config/diagnostics.py",
            "enrama/config/loader.py",
            "enrama/config/catalogs.py",
            "enrama/config/models.py",
            "enrama/config/schema.py",
            "enrama/core/__init__.py",
            "enrama/core/assets.py",
            "enrama/core/_asset_files.py",
            "enrama/core/_asset_images.py",
            "enrama/core/_asset_errors.py",
            "enrama/core/_render_context.py",
            "enrama/core/_render_errors.py",
            "enrama/core/renderer.py",
            "enrama/core/_build_errors.py",
            "enrama/core/_manifest.py",
            "enrama/core/_project.py",
            "enrama/core/builder.py",
            "enrama/_templates/base.html",
            "enrama/themes.py",
            "enrama/_themes/minimal.css",
            "enrama/_themes/bold.css",
            "enrama/_themes/THIRD_PARTY_NOTICES.txt",
            "enrama/_icons/provenance.json",
            "enrama/_icons/bootstrap-facebook.svg",
            "enrama/_icons/bootstrap-github.svg",
            "enrama/_icons/bootstrap-instagram.svg",
            "enrama/_icons/bootstrap-linkedin.svg",
            "enrama/_icons/bootstrap-telegram.svg",
            "enrama/_icons/bootstrap-tiktok.svg",
            "enrama/_icons/bootstrap-twitter-x.svg",
            "enrama/_icons/bootstrap-whatsapp.svg",
            "enrama/_icons/bootstrap-youtube.svg",
            "enrama/_icons/lucide-calendar.svg",
            "enrama/_icons/lucide-download.svg",
            "enrama/_icons/lucide-external-link.svg",
            "enrama/_icons/lucide-file-text.svg",
            "enrama/_icons/lucide-globe.svg",
            "enrama/_icons/lucide-link.svg",
            "enrama/_icons/lucide-mail.svg",
            "enrama/_icons/lucide-map-pin.svg",
            "enrama/_icons/lucide-message-circle.svg",
            "enrama/_icons/lucide-phone.svg",
            "enrama/_icons/lucide-play.svg",
            "enrama/_icons/lucide-shopping-bag.svg",
            "enrama/py.typed",
            "enrama-0.1.0.dev0.dist-info/METADATA",
            "enrama-0.1.0.dev0.dist-info/WHEEL",
            "enrama-0.1.0.dev0.dist-info/entry_points.txt",
            "enrama-0.1.0.dev0.dist-info/RECORD",
            "enrama-0.1.0.dev0.dist-info/licenses/LICENSE",
        }
    with tarfile.open(first[".gz"]) as sdist:
        files = {"/".join(item.name.split("/")[1:]) for item in sdist if item.isfile()}
        assert files == {
            "src/enrama/__init__.py",
            "src/enrama/__main__.py",
            "src/enrama/cli.py",
            "src/enrama/project.py",
            "src/enrama/preview.py",
            "src/enrama/config/__init__.py",
            "src/enrama/config/_language.py",
            "src/enrama/config/_paths.py",
            "src/enrama/config/_urls.py",
            "src/enrama/config/_yaml.py",
            "src/enrama/config/diagnostics.py",
            "src/enrama/config/loader.py",
            "src/enrama/config/catalogs.py",
            "src/enrama/config/models.py",
            "src/enrama/config/schema.py",
            "schemas/enrama-v1.schema.json",
            "src/enrama/core/__init__.py",
            "src/enrama/core/assets.py",
            "src/enrama/core/_asset_files.py",
            "src/enrama/core/_asset_images.py",
            "src/enrama/core/_asset_errors.py",
            "src/enrama/core/_render_context.py",
            "src/enrama/core/_render_errors.py",
            "src/enrama/core/renderer.py",
            "src/enrama/core/_build_errors.py",
            "src/enrama/core/_manifest.py",
            "src/enrama/core/_project.py",
            "src/enrama/core/builder.py",
            "src/enrama/_templates/base.html",
            "src/enrama/themes.py",
            "src/enrama/_themes/minimal.css",
            "src/enrama/_themes/bold.css",
            "src/enrama/_themes/THIRD_PARTY_NOTICES.txt",
            "src/enrama/_icons/provenance.json",
            "src/enrama/_icons/bootstrap-facebook.svg",
            "src/enrama/_icons/bootstrap-github.svg",
            "src/enrama/_icons/bootstrap-instagram.svg",
            "src/enrama/_icons/bootstrap-linkedin.svg",
            "src/enrama/_icons/bootstrap-telegram.svg",
            "src/enrama/_icons/bootstrap-tiktok.svg",
            "src/enrama/_icons/bootstrap-twitter-x.svg",
            "src/enrama/_icons/bootstrap-whatsapp.svg",
            "src/enrama/_icons/bootstrap-youtube.svg",
            "src/enrama/_icons/lucide-calendar.svg",
            "src/enrama/_icons/lucide-download.svg",
            "src/enrama/_icons/lucide-external-link.svg",
            "src/enrama/_icons/lucide-file-text.svg",
            "src/enrama/_icons/lucide-globe.svg",
            "src/enrama/_icons/lucide-link.svg",
            "src/enrama/_icons/lucide-mail.svg",
            "src/enrama/_icons/lucide-map-pin.svg",
            "src/enrama/_icons/lucide-message-circle.svg",
            "src/enrama/_icons/lucide-phone.svg",
            "src/enrama/_icons/lucide-play.svg",
            "src/enrama/_icons/lucide-shopping-bag.svg",
            "src/enrama/py.typed",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "build-constraints.txt",
            "PKG-INFO",
            ".gitignore",
        }
