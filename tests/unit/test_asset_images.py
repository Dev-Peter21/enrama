"""Real decoding, format policy, bounded containers and global decoder state."""

import importlib
import io
import struct
from types import ModuleType

import pytest
from asset_helpers import animated_png, animated_webp, ico_bytes, image_bytes
from PIL import Image, ImageFile


def api() -> ModuleType:
    return importlib.import_module("enrama.core._asset_images")


@pytest.mark.parametrize(
    ("fmt", "extension", "favicon"),
    [
        ("PNG", "png", False),
        ("JPEG", "jpg", False),
        ("JPEG", "jpeg", False),
        ("WEBP", "webp", False),
        ("PNG", "PNG", True),
        ("JPEG", "JPEG", False),
    ],
)
def test_supported_images(fmt: str, extension: str, favicon: bool) -> None:
    data = image_bytes(fmt)
    original = bytes(data)
    assert (
        api().validate_image(data, f"image.{extension}", favicon=favicon)
        == {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[fmt]
    )
    assert data == original


@pytest.mark.parametrize("bitmap", [False, True])
def test_ico_png_and_bitmap(bitmap: bool) -> None:
    if bitmap:
        stream = io.BytesIO()
        with Image.new("RGBA", (32, 32), "blue") as image:
            image.save(
                stream, format="ICO", bitmap_format="bmp", sizes=[(16, 16), (32, 32)]
            )
        data = stream.getvalue()
    else:
        data = ico_bytes([image_bytes(), image_bytes(color="blue")])
    assert api().validate_image(data, "favicon.ico", favicon=True) == "ico"


@pytest.mark.parametrize(
    ("data", "reference", "favicon", "category"),
    [
        (b"", "a.png", False, "invalid_image"),
        (b"plain text SECRET", "a.png", False, "invalid_image"),
        (image_bytes(), "a.jpg", False, "unsupported_format"),
        (image_bytes("JPEG"), "a.jpg", True, "unsupported_format"),
        (image_bytes("WEBP"), "a.webp", True, "unsupported_format"),
        (image_bytes(), "a.svg", False, "unsupported_format"),
        (image_bytes("GIF"), "a.png", False, "unsupported_format"),
        (image_bytes(), "no-extension", False, "unsupported_format"),
        (image_bytes()[:35], "a.png", False, "invalid_image"),
        (image_bytes("JPEG")[:-30], "a.jpg", False, "invalid_image"),
        (image_bytes("WEBP")[:25], "a.webp", False, "invalid_image"),
        (ico_bytes([b"broken"]), "a.ico", True, "invalid_image"),
        (ico_bytes([image_bytes(), b"broken"]), "a.ico", True, "invalid_image"),
        (
            ico_bytes([image_bytes(), image_bytes()[:-20]]),
            "a.ico",
            True,
            "invalid_image",
        ),
        (animated_png(), "a.png", False, "animation"),
        (animated_png(2), "a.png", False, "animation"),
        (animated_webp(), "a.webp", False, "animation"),
    ],
)
def test_invalid_images(
    data: bytes, reference: str, favicon: bool, category: str
) -> None:
    module = api()
    with pytest.raises(module.InvalidImage) as error:
        module.validate_image(data, reference, favicon=favicon)
    assert error.value.category == category
    assert "SECRET" not in str(error.value)


@pytest.mark.parametrize(
    ("size", "favicon", "accepted"),
    [
        ((8192, 1), False, True),
        ((8193, 1), False, False),
        ((1, 8192), False, True),
        ((1, 8193), False, False),
        ((8000, 2000), False, True),
        ((4001, 4000), False, False),
        ((1024, 1024), True, True),
        ((1025, 1), True, False),
        ((1, 1025), True, False),
    ],
)
def test_dimension_limits(size: tuple[int, int], favicon: bool, accepted: bool) -> None:
    module = api()
    data = image_bytes(size=size)
    if accepted:
        assert module.validate_image(data, "a.png", favicon=favicon) == "png"
    else:
        with pytest.raises(module.InvalidImage) as error:
            module.validate_image(data, "a.png", favicon=favicon)
        assert error.value.category == "resource_limit"


@pytest.mark.parametrize(("count", "accepted"), [(1, True), (16, True), (17, False)])
def test_actual_ico_entry_limit(count: int, accepted: bool) -> None:
    data = ico_bytes([image_bytes()] * count)
    module = api()
    if accepted:
        assert module.validate_image(data, "a.ico", favicon=True) == "ico"
    else:
        with pytest.raises(module.InvalidImage) as error:
            module.validate_image(data, "a.ico", favicon=True)
        assert error.value.category == "resource_limit"


def test_ico_embedded_dimensions_checked_before_decoding() -> None:
    # Directory says16; actual embedded PNG is257. A small claimed directory cannot bypass limits.
    module = api()
    with pytest.raises(module.InvalidImage) as error:
        module.validate_image(
            ico_bytes([image_bytes(size=(257, 1))]), "a.ico", favicon=True
        )
    assert error.value.category == "resource_limit"


def test_ico_largest_256_accepted() -> None:
    assert (
        api().validate_image(
            ico_bytes([image_bytes(size=(256, 256))], 256), "a.ico", favicon=True
        )
        == "ico"
    )


def test_ico_entry_offsets_and_truncation() -> None:
    module = api()
    data = bytearray(ico_bytes([image_bytes()]))
    struct.pack_into("<I", data, 18, len(data) + 1)
    with pytest.raises(module.InvalidImage):
        module.validate_image(bytes(data), "a.ico", favicon=True)


@pytest.mark.parametrize("favicon", [False, True])
def test_byte_bounds(favicon: bool) -> None:
    module = api()
    limit = 1048576 if favicon else 5242880
    data = image_bytes()
    data += b"\x00" * (limit - len(data))
    assert module.validate_image(data, "a.png", favicon=favicon) == "png"
    with pytest.raises(module.InvalidImage) as error:
        module.validate_image(data + b"\x00", "a.png", favicon=favicon)
    assert error.value.category == "resource_limit"


def test_single_frame_animation_fixture_is_real() -> None:
    # Negative control: rejecting this container must not depend on n_frames >1.
    with Image.open(io.BytesIO(animated_webp())) as image:
        image.load()
        assert getattr(image, "n_frames", 1) == 1
    with pytest.raises(api().InvalidImage):
        api().validate_image(animated_webp(), "a.webp", favicon=False)


def test_decoder_globals_not_modified() -> None:
    before = (ImageFile.LOAD_TRUNCATED_IMAGES, Image.MAX_IMAGE_PIXELS)
    api().validate_image(image_bytes(), "a.png", favicon=False)
    assert (ImageFile.LOAD_TRUNCATED_IMAGES, Image.MAX_IMAGE_PIXELS) == before


def test_permissive_external_decoder_state_fails_honestly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = api()
    monkeypatch.setattr(ImageFile, "LOAD_TRUNCATED_IMAGES", True)
    with pytest.raises(module.AssetEnvironmentError):
        module.validate_image(image_bytes(), "a.png", favicon=False)
    assert ImageFile.LOAD_TRUNCATED_IMAGES is True


def test_unexpected_and_interrupts_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
    module = api()

    def broken(*args: object, **kwargs: object) -> None:
        raise RuntimeError("injected defect")

    monkeypatch.setattr(Image, "open", broken)
    with pytest.raises(RuntimeError, match="injected defect"):
        module.validate_image(image_bytes(), "a.png", favicon=False)


def test_large_jpeg_header_does_not_emit_warning(
    recwarn: pytest.WarningsRecorder,
) -> None:
    data = bytearray(image_bytes("JPEG"))
    offset = data.index(b"\xff\xc0")
    struct.pack_into(">HH", data, offset + 5, 10000, 10000)
    module = api()
    with pytest.raises(module.InvalidImage) as error:
        module.validate_image(bytes(data), "a.jpg", favicon=False)
    assert error.value.category == "resource_limit"
    assert not recwarn.list


def test_missing_required_codec_is_environment_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PIL import features

    module = api()
    monkeypatch.setattr(features, "check_module", lambda name: False)
    with pytest.raises(module.AssetEnvironmentError):
        module.validate_image(image_bytes(), "a.png", favicon=False)


@pytest.mark.parametrize("container", ["animated", "extended", "lossy", "lossless"])
def test_webp_limits_precede_native_canvas_allocation(
    container: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from asset_helpers import riff_chunk
    from PIL import _webp

    if container == "animated":
        data = bytearray(animated_webp())
        pos = data.index(b"VP8X") + 12
        data[pos : pos + 6] = (9999).to_bytes(3, "little") * 2
    elif container == "extended":
        body = (
            b"WEBP"
            + riff_chunk(b"VP8X", b"\x00" * 4 + (9999).to_bytes(3, "little") * 2)
            + image_bytes("WEBP")[12:]
        )
        data = bytearray(b"RIFF" + struct.pack("<I", len(body)) + body)
    elif container == "lossy":
        data = bytearray(image_bytes("WEBP"))
        pos = data.index(b"\x9d\x01\x2a")
        struct.pack_into("<HH", data, pos + 3, 10000, 10000)
    else:
        stream = io.BytesIO()
        with Image.new("RGB", (16, 16), "red") as image:
            image.save(stream, format="WEBP", lossless=True)
        data = bytearray(stream.getvalue())
        pos = data.index(b"VP8L") + 9
        original = struct.unpack_from("<I", data, pos)[0]
        struct.pack_into("<I", data, pos, (original & 0xF0000000) | 9999 | (9999 << 14))

    def forbidden(*args: object) -> None:
        raise AssertionError("Native WebP canvas reached before policy checks")

    monkeypatch.setattr(_webp, "WebPAnimDecoder", forbidden)
    module = api()
    with pytest.raises(module.InvalidImage) as error:
        module.validate_image(bytes(data), "a.webp", favicon=False)
    assert error.value.category in {"resource_limit", "animation"}
