"""Consumer-observable HTML, metadata, escaping, snapshot and failure contracts."""

from dataclasses import replace
from importlib import resources
from pathlib import Path

import pytest
from render_helpers import Document, rendering_inputs


@pytest.mark.parametrize("theme", ["minimal", "bold"])
def test_profile_only_semantic_document(theme: str, tmp_path: Path) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(tmp_path, theme={"name": theme})
    doc = Document(render_html(config, assets))
    assert doc.doctype == "doctype html"
    assert len(doc.all("html")) == len(doc.all("head")) == len(doc.all("body")) == 1
    assert doc.all("html")[0].attrs["lang"] == "es-AR"
    assert len(doc.all("main")) == len(doc.all("h1")) == 1
    assert doc.all("h1")[0].text == "Profile name"
    assert doc.all("main")[0].all("h1")
    assert doc.all("title")[0].text == "Document title"
    assert any(n.attrs.get("charset") == "utf-8" for n in doc.all("meta"))
    assert doc.meta()["viewport"] == "width=device-width, initial-scale=1"
    assert not any(
        doc.all(t) for t in ("ul", "a", "img", "p", "script", "style", "base", "svg")
    )
    assert doc.all("link") == []


def test_optional_profile_and_ordered_collections(tmp_path: Path) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(
        tmp_path,
        profile={"avatar": "logo.png", "bio": "Plain **bio**"},
        links=[
            {
                "id": ident,
                "title": title,
                "url": "https://example.com/" + ident,
                "enabled": enabled,
            }
            for ident, title, enabled in [
                ("z", "Z first", True),
                ("hidden", "Hidden", False),
                ("a", "A last", True),
            ]
        ],
        socials=[
            {
                "id": "social-two",
                "platform": "github",
                "url": "https://unrelated.example/",
                "label": "Custom label",
            },
            {
                "id": "social-off",
                "platform": "instagram",
                "url": "https://example.com",
                "enabled": False,
            },
            {"id": "social-one", "platform": "github", "url": "https://other.example"},
        ],
    )
    doc = Document(render_html(config, assets))
    lists = doc.all("main")[0].all("ul")
    assert len(lists) == 2
    assert [a.text for a in lists[0].all("a")] == ["Z first", "A last"]
    assert [a.text for a in lists[1].all("a")] == ["Custom label", "GitHub"]
    assert all(len(li.all("a")) == 1 for ul in lists for li in ul.all("li"))
    assert doc.all("img")[0].attrs == {
        "src": assets.mapping["profile.avatar"],
        "alt": "",
    }
    assert doc.all("p")[0].text == "Plain **bio**"
    assert not doc.all("strong")
    assert all("target" not in a.attrs and "rel" not in a.attrs for a in doc.all("a"))


@pytest.mark.parametrize(
    ("base", "canonical"),
    [
        (None, None),
        ("https://example.com", "https://example.com/"),
        ("https://example.com/client", "https://example.com/client/"),
        ("https://example.com/client/", "https://example.com/client/"),
        ("https://example.com/a%20b/%2F", "https://example.com/a%20b/%2F/"),
        ("https://example.com/page.html", "https://example.com/page.html/"),
    ],
)
@pytest.mark.parametrize("image", [None, "og.png"])
@pytest.mark.parametrize("favicon", [None, "favicon.png"])
def test_metadata_presence_and_directory_urls(
    base: str | None,
    canonical: str | None,
    image: str | None,
    favicon: str | None,
    tmp_path: Path,
) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(
        tmp_path, site={"url": base, "og_image": image, "favicon": favicon}
    )
    doc = Document(render_html(config, assets))
    meta = doc.meta()
    assert meta["description"] == meta["og:description"] == "Description"
    assert meta["og:title"] == "Document title"
    assert meta["og:type"] == "website"
    links = {n.attrs["rel"]: n.attrs["href"] for n in doc.all("link")}
    assert links.get("canonical") == canonical
    assert meta.get("og:url") == canonical
    if canonical and image:
        assert meta["og:image"] == canonical + assets.mapping["site.og_image"]
    else:
        assert "og:image" not in meta
    assert links.get("icon") == assets.mapping.get("site.favicon")
    assert set(links) == ({"canonical"} if canonical else set()) | (
        {"icon"} if favicon else set()
    )
    assert "og:locale" not in meta
    assert not any(k and k.startswith("twitter:") for k in meta)
    assert config.site.url == base


@pytest.mark.parametrize(
    "text",
    [
        '<script>alert("x")</script>',
        '" onload="attack',
        "&lt;script&gt; &amp;",
        "{{ 7 * 7 }} {% include 'secret' %}",
        "Unicode café 🌿",
    ],
)
def test_plain_text_is_escaped_in_body_title_and_attributes(
    text: str, tmp_path: Path
) -> None:
    from enrama.core import render_html

    url = "https://example.com/?a=1&b=%22#end"
    config, assets = rendering_inputs(
        tmp_path,
        site={"title": text, "description": text},
        profile={"name": text, "bio": text},
        links=[{"id": "link", "title": text, "url": url}],
        socials=[{"id": "social", "platform": "github", "label": text, "url": url}],
    )
    doc = Document(render_html(config, assets))
    assert (
        doc.all("h1")[0].text
        == doc.all("title")[0].text
        == doc.all("p")[0].text
        == text
    )
    assert (
        doc.meta()["description"]
        == doc.meta()["og:title"]
        == doc.meta()["og:description"]
        == text
    )
    assert [a.text for a in doc.all("a")] == [text, text]
    assert [a.attrs for a in doc.all("a")] == [{"href": url}, {"href": url}]
    assert not doc.all("script")
    assert not any(
        "onload" in node.attrs
        for tag in ("h1", "p", "meta", "a")
        for node in doc.all(tag)
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://EXAMPLE.com/Path?q=a&b=2#part",
        "http://example.com/",
        "mailto:hi@example.com",
        "tel:+541112345678",
    ],
)
def test_destination_spelling_and_same_context(url: str, tmp_path: Path) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(
        tmp_path, links=[{"id": "link", "title": "Go", "url": url}]
    )
    assert Document(render_html(config, assets)).all("a")[0].attrs == {"href": url}


def test_render_uses_retained_paths_without_client_io_or_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(
        tmp_path, site={"og_image": "og.png"}, profile={"avatar": "avatar.png"}
    )
    before = config.model_dump()
    for name in ("og.png", "avatar.png"):
        (tmp_path / name).unlink()
    first = render_html(config, assets)
    monkeypatch.chdir(tmp_path)
    assert render_html(config, assets) == first
    assert "\r" not in first
    assert str(tmp_path) not in first
    assert config.model_dump() == before
    assert capsys.readouterr() == ("", "")
    assert list(tmp_path.iterdir()) == []


def test_missing_og_binding_fails_even_without_public_url(tmp_path: Path) -> None:
    from enrama.core import RenderError, render_html

    config, assets = rendering_inputs(tmp_path, site={"og_image": "og.png"})
    with pytest.raises(RenderError) as caught:
        render_html(config, replace(assets, bindings=()))
    assert caught.value.category == "asset_mismatch"
    assert caught.value.kind == "internal"
    assert caught.value.field == "site.og_image"


@pytest.mark.parametrize(
    "template",
    [
        "{% invalid syntax %}",
        "{{ absent }}",
        "prefix {{ absent.field }}",
        "{% for entry in absent %}oops{% endfor %}",
    ],
)
def test_packaged_template_defects_are_safe_internal_errors(
    template: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from enrama.core import RenderError, render_html, renderer

    config, assets = rendering_inputs(tmp_path)
    monkeypatch.setattr(renderer, "_load_template", lambda name: template)
    with pytest.raises(RenderError) as caught:
        render_html(config, assets)
    error = caught.value
    assert error.kind == "internal"
    assert error.category == "template_error"
    assert error.template == "base.html"
    assert error.hint
    assert template not in str(error)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    ("failure", "kind", "category"),
    [
        (FileNotFoundError, "internal", "template_error"),
        (PermissionError, "operational", "resource_error"),
        (OSError, "operational", "resource_error"),
        (RuntimeError, "internal", "internal_error"),
    ],
)
def test_resource_failures_are_classified_without_raw_payload(
    failure: type[Exception],
    kind: str,
    category: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from enrama.core import RenderError, render_html

    config, assets = rendering_inputs(tmp_path)

    def fail(package: str) -> Path:
        raise failure("SECRET /private/client\x1b[31m")

    monkeypatch.setattr(resources, "files", fail)
    with pytest.raises(RenderError) as caught:
        render_html(config, assets)
    error = caught.value
    assert (error.kind, error.category) == (kind, category)
    assert "SECRET" not in str(error) and "\x1b" not in str(error)
    assert "/private/client" not in str(error)
    assert error.hint


def test_missing_and_invalid_utf8_resource_are_package_defects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import RenderError, render_html

    config, assets = rendering_inputs(tmp_path)
    monkeypatch.setattr(resources, "files", lambda package: tmp_path)
    with pytest.raises(RenderError) as caught:
        render_html(config, assets)
    assert caught.value.kind == "internal"
    package_templates = tmp_path / "_templates"
    package_templates.mkdir()
    (package_templates / "base.html").write_bytes(b"\xff")
    with pytest.raises(RenderError) as caught:
        render_html(config, assets)
    assert caught.value.kind == "internal"
    assert "utf-8" not in str(caught.value)


def test_interrupt_is_not_wrapped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import render_html

    config, assets = rendering_inputs(tmp_path)

    def interrupt(package: str) -> Path:
        raise KeyboardInterrupt

    monkeypatch.setattr(resources, "files", interrupt)
    with pytest.raises(KeyboardInterrupt):
        render_html(config, assets)
