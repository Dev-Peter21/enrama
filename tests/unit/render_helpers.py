"""Small parsed-output helpers; no fixture depends on renderer internals."""

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from asset_helpers import image_bytes

from enrama.config import EnramaConfig
from enrama.core import PreparedAssets, prepare_assets


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None]
    children: list["Element"] = field(default_factory=list)
    text: str = ""

    def all(self, tag: str) -> list["Element"]:
        return [
            node
            for child in self.children
            for node in ([child] if child.tag == tag else []) + child.all(tag)
        ]


class Document(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("document", {})
        self.stack = [self.root]
        self.doctype = ""
        self.feed(html)
        self.close()
        assert len(self.stack) == 1, "Unclosed HTML element"

    def handle_decl(self, decl: str) -> None:
        self.doctype = decl.lower()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Element(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in {"meta", "link", "img", "br", "hr", "input", "source", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        assert self.stack[-1].tag == tag, f"Unexpected closing {tag}"
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        for node in self.stack:
            node.text += data

    def all(self, tag: str) -> list[Element]:
        return self.root.all(tag)

    def meta(self) -> dict[str | None, str | None]:
        return {
            n.attrs.get("property", n.attrs.get("name")): n.attrs.get("content")
            for n in self.all("meta")
        }


def rendering_inputs(
    tmp_path: Path, **updates: Any
) -> tuple[EnramaConfig, PreparedAssets]:
    data: dict[str, Any] = {
        "schema_version": 1,
        "site": {
            "title": "Document title",
            "description": "Description",
            "language": "ES-ar",
        },
        "profile": {"name": "Profile name"},
    }
    for key, value in updates.items():
        if key in ("site", "profile"):
            data[key].update(value)
        else:
            data[key] = value
    config = EnramaConfig.model_validate(data)
    for ref in (config.profile.avatar, config.site.favicon, config.site.og_image):
        if ref is not None:
            image = tmp_path / ref
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(image_bytes())
    return config, prepare_assets(config, source=tmp_path / "selected.yaml")
