"""Bounded transports for the manual release controller; no stored credentials."""

import json
import subprocess
from typing import Any
from urllib.error import HTTPError
from urllib.request import urlopen

REPOSITORY = "Dev-Peter21/enrama"
LIMIT = 64 * 1024 * 1024


def command(*args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["gh", *args], input=data, capture_output=True, timeout=120, check=True
    )
    if len(result.stdout) > LIMIT:
        raise ValueError("Remote response exceeds the release limit")
    return result.stdout


def gh(
    path: str, *, method: str = "GET", data: Any = None, missing: bool = False
) -> Any:
    args = ["api", "--method", method, f"repos/{REPOSITORY}/{path}"]
    if data is not None:
        args += ["--input", "-"]
    try:
        raw = command(
            *args, data=json.dumps(data).encode() if data is not None else None
        )
    except subprocess.CalledProcessError as error:
        if missing and b"(HTTP 404)" in (error.stderr or b""):
            return None
        raise
    return json.loads(raw)


def gh_bytes(path: str) -> bytes:
    return command(
        "api", f"repos/{REPOSITORY}/{path}", "-H", "Accept: application/octet-stream"
    )


def public_bytes(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:
        data = response.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Public response exceeds the release limit")
    return bytes(data)


def public_json(url: str) -> Any:
    try:
        return json.loads(public_bytes(url))
    except HTTPError as error:
        if error.code == 404:
            return None
        raise
