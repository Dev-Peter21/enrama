"""Plain-static-server probes; this harness is not a product builder or preview."""

import io
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urljoin
from urllib.request import urlopen

import pytest
from PIL import Image

from enrama.config import EnramaConfig
from enrama.core import copy_assets, prepare_assets, render_html
from enrama.themes import theme_view


class ResourceReferences(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.paths: list[str] = []
        self.base_elements = 0
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "base":
            self.base_elements += 1
        if (
            tag == "img"
            or tag == "link"
            and values.get("rel") in {"icon", "stylesheet"}
        ):
            path = values.get("src") if tag == "img" else values.get("href")
            assert path
            self.paths.append(path)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.mark.parametrize("prefix", ["", "repository/client/"])
def test_relative_images_resolve_under_static_root_or_prefix(
    prefix: str, tmp_path: Path
) -> None:
    client = tmp_path / "client"
    client.mkdir()
    stream = io.BytesIO()
    with Image.new("RGB", (16, 16), "red") as image:
        image.save(stream, format="PNG")
    original = stream.getvalue()
    (client / "logo.png").write_bytes(original)
    config = EnramaConfig.model_validate(
        {
            "schema_version": 1,
            "site": {
                "title": "Shop",
                "description": "Shop",
                "language": "en",
                "url": "https://production.example/other-prefix",
                "favicon": "logo.png",
                "og_image": "logo.png",
            },
            "profile": {"name": "Shop", "avatar": "logo.png"},
        }
    )
    document_root = client / "work"
    stage = document_root / prefix
    stage.mkdir(parents=True)
    prepared = prepare_assets(
        config,
        source=client / "enrama.yaml",
        reserved_paths=(stage.relative_to(client),),
    )
    copy_assets(prepared, stage)
    theme = theme_view(config.theme)
    for name, data in theme.assets.items():
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    html = render_html(config, prepared)
    (stage / "index.html").write_text(html, encoding="utf-8", newline="\n")
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(document_root))
    )
    thread = Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    try:
        page_url = f"http://127.0.0.1:{server.server_port}/{prefix}"
        with urlopen(page_url, timeout=5) as response:
            assert response.status == 200
            page = response.read().decode("utf-8")
        refs = ResourceReferences(page)
        assert refs.base_elements == 0
        assert len(refs.paths) == 3
        assert all(path.startswith("assets/") for path in refs.paths)
        for reference in refs.paths:
            with urlopen(urljoin(page_url, reference), timeout=5) as response:
                assert response.status == 200
                assert response.read() == theme.assets.get(reference, original)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    assert not thread.is_alive()
    assert (client / "logo.png").read_bytes() == original
    assert not (client / "dist").exists()
