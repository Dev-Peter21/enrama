"""Check prepared image relationships in memory, without source or decoder I/O."""

import re
from typing import NoReturn

from enrama.config import EnramaConfig

from ._render_errors import RenderError
from .assets import PreparedAssets

_PUBLIC_PATH = re.compile(r"assets/client/[0-9a-f]{64}\.(png|jpg|webp|ico)")


def _mismatch(field: str | None = None) -> NoReturn:
    raise RenderError(
        "internal",
        "asset_mismatch",
        "Prepared images do not match the rendering configuration",
        "Prepare assets from the same configuration before rendering",
        field=field,
    )


def image_paths(config: EnramaConfig, prepared: PreparedAssets) -> dict[str, str]:
    """Return checked field paths; do not authenticate or revalidate image bytes."""
    fields = {
        ("profile", "avatar"): config.profile.avatar,
        ("site", "favicon"): config.site.favicon,
        ("site", "og_image"): config.site.og_image,
    }
    expected = {location: ref for location, ref in fields.items() if ref is not None}
    available: set[str] = set()
    for asset in prepared.assets:
        if (
            not _PUBLIC_PATH.fullmatch(asset.public_path)
            or asset.public_path in available
        ):
            _mismatch()
        available.add(asset.public_path)
    result: dict[str, str] = {}
    for binding in prepared.bindings:
        if binding.location not in expected:
            _mismatch(
                ".".join(binding.location) if binding.location in fields else None
            )
        field = ".".join(binding.location)
        match = _PUBLIC_PATH.fullmatch(binding.public_path)
        if (
            field in result
            or binding.reference != expected[binding.location]
            or match is None
            or binding.public_path not in available
        ):
            _mismatch(field)
        extension = match.group(1)
        if extension not in (
            ("png", "ico") if field == "site.favicon" else ("png", "jpg", "webp")
        ):
            _mismatch(field)
        result[field] = binding.public_path
    for location in expected:
        field = ".".join(location)
        if field not in result:
            _mismatch(field)
    return result
