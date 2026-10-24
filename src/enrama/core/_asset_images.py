"""Bounded image policy over original bytes; Pillow decodes but never rewrites."""

import io
import struct
import warnings
from pathlib import PurePosixPath

from PIL import Image, ImageFile, features

from ._asset_errors import AssetEnvironmentError, InvalidImage

_EXTENSIONS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
    ".ico": "ICO",
}
_CANONICAL = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "ICO": "ico"}
_PNG = b"\x89PNG\r\n\x1a\n"


def _invalid() -> InvalidImage:
    return InvalidImage(
        "invalid_image",
        "The image is empty, damaged or cannot be decoded.",
        "Export a valid supported image and update the reference.",
    )


def _dimensions(width: int, height: int, side: int, pixels: int) -> None:
    if width <= 0 or height <= 0:
        raise _invalid()
    if width > side or height > side or width * height > pixels:
        raise InvalidImage(
            "resource_limit",
            f"The image exceeds {side} pixels per side or the {pixels:,}-pixel limit.",
            "Export a smaller image and update the referenced file.",
        )


def _animation() -> InvalidImage:
    return InvalidImage(
        "animation",
        "Animated image containers are not supported.",
        "Export a static PNG, JPEG or WebP suitable for this field.",
    )


def _png_header(data: bytes, side: int, pixels: int) -> tuple[int, int]:
    if len(data) < 33 or data[:8] != _PNG or data[8:16] != b"\x00\x00\x00\rIHDR":
        raise _invalid()
    width, height = struct.unpack_from(">II", data, 16)
    size = (int(width), int(height))
    _dimensions(*size, side, pixels)
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        tag = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise _invalid()
        if tag == b"acTL":
            raise _animation()
        if tag == b"IEND":
            return size
        offset = end
    raise _invalid()


def _webp_container(data: bytes) -> None:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise _invalid()
    end = struct.unpack_from("<I", data, 4)[0] + 8
    if end > len(data):
        raise _invalid()
    offset = 12
    while offset < end:
        if offset + 8 > end:
            raise _invalid()
        tag = data[offset : offset + 4]
        length = struct.unpack_from("<I", data, offset + 4)[0]
        next_offset = offset + 8 + length + (length % 2)
        if next_offset > end:
            raise _invalid()
        if tag in {b"ANIM", b"ANMF"} or (
            tag == b"VP8X" and length and data[offset + 8] & 2
        ):
            raise _animation()
        offset = next_offset


def _decode(data: bytes, expected: str, side: int, pixels: int) -> None:
    with Image.open(io.BytesIO(data), formats=[expected]) as image:
        if image.format != expected:
            raise _invalid()
        _dimensions(*image.size, side, pixels)
        if getattr(image, "is_animated", False) or getattr(image, "n_frames", 1) > 1:
            raise _animation()
        image.verify()
    with Image.open(io.BytesIO(data), formats=[expected]) as image:
        image.load()


def _ico(data: bytes) -> None:
    if len(data) < 6 or data[:4] != b"\x00\x00\x01\x00":
        raise _invalid()
    count = struct.unpack_from("<H", data, 4)[0]
    if count > 16:
        raise InvalidImage(
            "resource_limit",
            "The ICO exceeds 16 image entries.",
            "Export an ICO with at most 16 entries.",
        )
    directory_end = 6 + count * 16
    if count == 0 or directory_end > len(data):
        raise _invalid()
    for index in range(count):
        entry = data[6 + index * 16 : 22 + index * 16]
        declared = (entry[0] or 256, entry[1] or 256)
        length, offset = struct.unpack_from("<II", entry, 8)
        if offset < directory_end or not length or offset + length > len(data):
            raise _invalid()
        payload = data[offset : offset + length]
        if payload.startswith(_PNG):
            actual = _png_header(payload, 256, 65536)
            if actual != declared:
                raise _invalid()
            _decode(payload, "PNG", 256, 65536)
        else:
            if len(payload) < 12:
                raise _invalid()
            header = struct.unpack_from("<I", payload)[0]
            if header == 12:
                width, full_height = struct.unpack_from("<HH", payload, 4)
            elif header in {40, 52, 56, 64, 108, 124} and len(payload) >= header:
                width, full_height = struct.unpack_from("<ii", payload, 4)
            else:
                raise _invalid()
            if full_height % 2:
                raise _invalid()
            actual = (width, abs(full_height) // 2)
            _dimensions(*actual, 256, 65536)
            if actual != declared:
                raise _invalid()
        # Isolate each raw directory entry, including entries sharing a size.
        # Pillow's ordinary ICO loader selects only one image; it eagerly loads
        # DIB entries, so embedded dimensions must be bounded before this call.
        single = (
            b"\x00\x00\x01\x00\x01\x00" + entry[:12] + struct.pack("<I", 22) + payload
        )
        _decode(single, "ICO", 256, 65536)


def validate_image(data: bytes, reference: str, *, favicon: bool) -> str:
    """Return the canonical extension for a valid unchanged snapshot."""
    limit = 1048576 if favicon else 5242880
    if len(data) > limit:
        raise InvalidImage(
            "resource_limit",
            f"The image exceeds {limit:,} bytes.",
            "Export a smaller image and update the reference.",
        )
    if not data:
        raise _invalid()
    expected = _EXTENSIONS.get(
        PurePosixPath(reference.replace("\\", "/")).suffix.lower()
    )
    allowed = {"PNG", "ICO"} if favicon else {"PNG", "JPEG", "WEBP"}
    if expected not in allowed:
        raise InvalidImage(
            "unsupported_format",
            "The extension is not supported for this field.",
            "Use PNG/ICO for favicon or PNG/JPEG/static WebP for avatar and Open Graph.",
        )
    assert expected is not None
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        raise AssetEnvironmentError(
            "Strict image decoding requires LOAD_TRUNCATED_IMAGES=False."
        )
    if not (
        features.check_codec("jpg")
        and features.check_codec("zlib")
        and features.check_module("webp")
    ):
        raise AssetEnvironmentError(
            "Required PNG, JPEG or WebP decoder capability is unavailable."
        )
    try:
        # Determine format without letting ICO's eager loader allocate pixels.
        actual = (
            "ICO"
            if data[:4] == b"\x00\x00\x01\x00"
            else ("PNG" if data.startswith(_PNG) else None)
        )
        if actual is None:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(
                    io.BytesIO(data), formats=["PNG", "JPEG", "WEBP", "GIF"]
                ) as image:
                    actual = image.format
        if actual != expected:
            raise InvalidImage(
                "unsupported_format",
                "The detected format does not match the extension or field.",
                "Use an allowed image with its matching extension.",
            )
        side, pixels = (1024, 1048576) if favicon else (8192, 16000000)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            if expected == "ICO":
                _ico(data)
            else:
                if expected == "PNG":
                    _png_header(data, side, pixels)
                elif expected == "WEBP":
                    _webp_container(data)
                _decode(data, expected, side, pixels)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise InvalidImage(
            "resource_limit",
            "The image exceeds safe decoding limits.",
            "Export a smaller image.",
        ) from None
    except InvalidImage:
        raise
    except (OSError, SyntaxError, ValueError, EOFError, struct.error):
        raise _invalid() from None
    return _CANONICAL[expected]
