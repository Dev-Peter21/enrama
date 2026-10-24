"""Synthetic image bytes created locally; no client or third-party fixture data."""

import io
import struct
import zlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enrama.config import EnramaConfig

from PIL import Image


def image_bytes(
    fmt: str = "PNG", size: tuple[int, int] = (16, 16), color: str = "red"
) -> bytes:
    output = io.BytesIO()
    with Image.new("RGB", size, color) as image:
        image.save(output, format=fmt)
    return output.getvalue()


def ico_bytes(payloads: list[bytes], size: int = 16) -> bytes:
    offset = 6 + 16 * len(payloads)
    entries = []
    for payload in payloads:
        entries.append(
            struct.pack(
                "<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(payload), offset
            )
        )
        offset += len(payload)
    return struct.pack("<HHH", 0, 1, len(payloads)) + b"".join(entries + payloads)


def animated_png(frames: int = 1) -> bytes:
    output = io.BytesIO()
    images = [Image.new("RGB", (16, 16), color) for color in ("red", "blue")]
    try:
        images[0].save(
            output,
            format="PNG",
            save_all=True,
            append_images=images[1:frames],
            duration=100,
        )
    finally:
        for image in images:
            image.close()
    data = output.getvalue()
    if frames == 1 and b"acTL" not in data:
        # Pillow's single-frame saver may emit an ordinary PNG. Build a valid
        # one-frame APNG control sequence around its unchanged IDAT instead.
        def chunk(tag: bytes, payload: bytes) -> bytes:
            return (
                struct.pack(">I", len(payload))
                + tag
                + payload
                + struct.pack(">I", zlib.crc32(tag + payload))
            )

        control = chunk(b"acTL", struct.pack(">II", 1, 0))
        control += chunk(
            b"fcTL", struct.pack(">IIIIIHHBB", 0, 16, 16, 0, 0, 1, 10, 0, 0)
        )
        data = data[:33] + control + data[33:]
    return data


def riff_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        tag + struct.pack("<I", len(data)) + data + (b"\x00" if len(data) % 2 else b"")
    )


def animated_webp() -> bytes:
    # Valid one-frame animation: libwebp reports n_frames == 1, so inspect its container too.
    static = image_bytes("WEBP")
    frame = b"\x00" * 6 + b"\x0f\x00\x00" * 2 + b"\x64\x00\x00\x00" + static[12:]
    body = b"WEBP" + riff_chunk(b"VP8X", b"\x02\x00\x00\x00" + b"\x0f\x00\x00" * 2)
    body += riff_chunk(b"ANIM", b"\x00" * 6) + riff_chunk(b"ANMF", frame)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def client_config(
    avatar: str | None = None, favicon: str | None = None, og: str | None = None
) -> "EnramaConfig":
    from enrama.config import EnramaConfig

    return EnramaConfig.model_validate(
        {
            "schema_version": 1,
            "site": {
                "title": "Shop",
                "description": "Shop",
                "language": "en",
                "favicon": favicon,
                "og_image": og,
            },
            "profile": {"name": "Shop", "avatar": avatar},
        }
    )
