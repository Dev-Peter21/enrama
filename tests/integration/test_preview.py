"""Actual foreground preview, ownership, exact ports and safe HTTP serving."""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest


def source(root: Path) -> Path:
    path = root / "enrama.yaml"
    path.write_text(
        "schema_version: 1\nsite: {title: Demo, description: Demo, language: en}\nprofile: {name: Demo}\n"
    )
    return path


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_busy_port_preserves_output(tmp_path: Path) -> None:
    selected = source(tmp_path)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        probe.listen()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "enrama",
                "preview",
                "--config",
                str(selected),
                "--port",
                str(probe.getsockname()[1]),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    assert result.returncode == 3, result.stderr
    assert not (tmp_path / "dist").exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGINT process lifecycle probe")
def test_foreground_preview_guard_http_safety_and_shutdown(tmp_path: Path) -> None:
    selected = source(tmp_path)
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "enrama",
            "preview",
            "--config",
            str(selected),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                with urlopen(url + "/", timeout=0.5) as response:
                    assert b"Demo" in response.read()
                break
            except (URLError, TimeoutError):
                if process.poll() is not None:
                    pytest.fail(str(process.communicate()))
                if time.monotonic() > deadline:
                    pytest.fail("Preview startup timed out")
                time.sleep(0.05)
        conflict = subprocess.run(
            [sys.executable, "-m", "enrama", "build", "--config", str(selected)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert conflict.returncode == 3
        valid = subprocess.run(
            [sys.executable, "-m", "enrama", "validate", "--config", str(selected)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert valid.returncode == 0
        secret = tmp_path / "private.txt"
        secret.write_text("DO NOT SERVE")
        for suffix in (
            "/../private.txt",
            "/%2e%2e/private.txt",
            "/enrama.yaml",
            "/.enrama-manifest.json",
            "/assets/",
            "/%5c..%5cprivate.txt",
        ):
            with pytest.raises(HTTPError) as error:
                urlopen(url + suffix, timeout=2)
            assert error.value.code == 404
        (tmp_path / "dist/index.html").unlink()
        (tmp_path / "dist/index.html").symlink_to(secret)
        with pytest.raises(HTTPError) as error:
            urlopen(url + "/", timeout=2)
        assert error.value.code == 404
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, (stdout, stderr)
        assert "http://127.0.0.1:" in stdout
        assert secret.read_text() == "DO NOT SERVE"
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
