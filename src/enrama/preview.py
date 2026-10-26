"""Foreground loopback preview of allowlisted output, never source directories."""

import mimetypes
import socket
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote_to_bytes, urlsplit

from .core import BuildError, ProjectSession, build_site
from .core import _asset_files as files
from .core._manifest import MAX_FILE


class _Handler(BaseHTTPRequestHandler):
    def __init__(
        self,
        request: socket.socket,
        client_address: tuple[str, int],
        server: "PreviewServer",
    ) -> None:
        self.preview = server
        super().__init__(request, client_address, server)

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        self._send(True)

    def do_HEAD(self) -> None:
        self._send(False)

    def _send(self, body: bool) -> None:
        try:
            path = unquote_to_bytes(urlsplit(self.path).path).decode("utf-8")
            if (
                not path.startswith("/")
                or "\\" in path
                or any(ord(c) < 32 for c in path)
            ):
                raise ValueError("Unsafe path")
            name = path[1:] or "index.html"
            if (
                any(part in {".", "..", ""} for part in name.split("/"))
                or name not in self.preview.allowed
            ):
                raise ValueError("Not public")
            data = files.read_source(self.preview.output, Path(name), MAX_FILE)
        except (OSError, ValueError):
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if content_type in {"text/html", "text/css", "text/plain"}:
            content_type += "; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if body:
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass


class PreviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, output: Path, port: int) -> None:
        self.output = output
        self.allowed: set[str] = set()

        super().__init__(("127.0.0.1", port), _Handler)


def run_preview(
    source: str | Path,
    port: int,
    on_ready: Callable[[str], None],
    on_warning: Callable[[str], None] | None = None,
) -> None:
    with ProjectSession(source) as session:
        try:
            server = PreviewServer(session.root / "dist", port)
        except OSError:
            raise BuildError(
                "operational",
                "port_unavailable",
                "The requested loopback port is unavailable",
                "Stop the process using that port or choose an explicit different --port",
            ) from None
        with server:
            result = build_site(source, session=session)
            server.allowed = set(result.files)
            if on_warning is not None:
                for warning in result.warnings:
                    on_warning(warning)
            on_ready(f"http://127.0.0.1:{server.server_port}/")
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                return
