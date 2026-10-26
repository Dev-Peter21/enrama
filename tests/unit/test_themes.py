"""Packaged presentation, contrast and controlled-icon behavior."""

from pathlib import Path

import pytest
from render_helpers import Document, rendering_inputs


@pytest.mark.parametrize("name", ["minimal", "bold"])
def test_local_styles_and_controlled_icons(name: str, tmp_path: Path) -> None:
    from enrama.core import render_html
    from enrama.themes import theme_view

    config, assets = rendering_inputs(
        tmp_path,
        theme={"name": name},
        links=[
            {
                "id": "website",
                "title": "My work",
                "url": "https://example.com",
                "icon": "globe",
            }
        ],
        socials=[
            {
                "id": "social",
                "platform": "instagram",
                "url": "https://instagram.com/example",
            }
        ],
    )
    doc = Document(render_html(config, assets))
    view = theme_view(config.theme)
    styles = [n for n in doc.all("link") if n.attrs.get("rel") == "stylesheet"]
    assert len(styles) == 1 and styles[0].attrs["href"] == view.stylesheet
    assert view.stylesheet in view.assets
    assert b"prefers-reduced-motion" in view.assets[view.stylesheet]
    assert b":focus-visible" in view.assets[view.stylesheet]
    assert b"44px" in view.assets[view.stylesheet]
    assert len(doc.all("svg")) == 2
    assert all(
        n.attrs.get("aria-hidden") == "true" and n.attrs.get("focusable") == "false"
        for n in doc.all("svg")
    )
    assert [a.text for a in doc.all("a")] == ["My work", "Instagram"]
    assert "assets/theme/THIRD_PARTY_NOTICES.txt" in view.assets
    assert b"ISC License" in view.assets["assets/theme/THIRD_PARTY_NOTICES.txt"]
    assert b"MIT License" in view.assets["assets/theme/THIRD_PARTY_NOTICES.txt"]
    assert not doc.all("script")


def test_custom_low_contrast_uses_accessible_derived_colors_without_mutation(
    tmp_path: Path,
) -> None:
    from enrama.themes import contrast, theme_view

    config, _ = rendering_inputs(
        tmp_path,
        theme={
            "primary_color": "#EEEEEE",
            "background_color": "#FFFFFF",
            "text_color": "#FAFAFA",
        },
    )
    before = config.model_dump()
    view = theme_view(config.theme)
    assert contrast(view.text, view.background) >= 4.5
    assert contrast(view.on_primary, view.primary) >= 4.5
    assert contrast(view.focus, view.background) >= 3
    assert view.warnings and config.model_dump() == before


def test_every_catalog_icon_is_bundled_and_decorative() -> None:
    from typing import get_args

    from enrama.config.catalogs import PLATFORMS, LinkIcon
    from enrama.themes import icon_svg

    for name in get_args(LinkIcon):
        markup = str(icon_svg(name))
        assert "<svg" in markup and 'aria-hidden="true"' in markup
    for item in PLATFORMS.values():
        assert "<svg" in str(icon_svg(item.icon, social=True))
    with pytest.raises(ValueError):
        icon_svg("../secret")


def test_build_copies_styles_and_removes_obsolete_theme_css(tmp_path: Path) -> None:
    from enrama.core import build_site
    from enrama.project import init_project

    client = init_project(tmp_path / "client")
    source = client / "enrama.yaml"
    old = build_site(source)
    first = {n for n in old.files if n.endswith(".css")}
    assert len(first) == 1 and all((old.output / n).is_file() for n in first)
    source.write_text(source.read_text().replace('"minimal"', '"bold"'))
    new = build_site(source)
    second = {n for n in new.files if n.endswith(".css")}
    assert len(second) == 1 and first != second
    assert not any((new.output / n).exists() for n in first)


def test_theme_api_imports_independently_of_core() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from enrama.themes import theme_view; from enrama.config import ThemeConfig; assert theme_view(ThemeConfig()).stylesheet",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "background", ["#777777", "#757575", "#808080", "#000000", "#FFFFFF"]
)
def test_fallback_guarantees_text_contrast_at_midtones(
    background: str, tmp_path: Path
) -> None:
    from enrama.themes import contrast, theme_view

    config, _ = rendering_inputs(
        tmp_path,
        theme={
            "primary_color": background,
            "background_color": background,
            "text_color": background,
        },
    )
    view = theme_view(config.theme)
    assert contrast(view.text, background) >= 4.5
    assert contrast(view.on_primary, background) >= 4.5


def test_bundled_icon_bytes_match_pinned_upstream_provenance() -> None:
    import hashlib
    import json
    from importlib.resources import files

    root = files("enrama").joinpath("_icons")
    records = json.loads(root.joinpath("provenance.json").read_text())
    assert len(records) == 21
    for item in records:
        assert item["source"].startswith("https://raw.githubusercontent.com/")
        assert (
            hashlib.sha256(root.joinpath(item["file"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
