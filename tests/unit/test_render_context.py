"""Catch mismatched or unsafe snapshot bindings before they can become HTML."""

from dataclasses import replace
from pathlib import Path

import pytest
from asset_helpers import client_config, image_bytes

from enrama.core import AssetBinding, PreparedAsset, PreparedAssets, prepare_assets

PNG = "assets/client/" + "a" * 64 + ".png"


def test_no_images_need_no_bindings(tmp_path: Path) -> None:
    from enrama.core._render_context import image_paths

    config = client_config()
    assert image_paths(config, prepare_assets(config, source=tmp_path / "x.yaml")) == {}


def test_checked_bindings_reuse_snapshots_after_source_deletion(tmp_path: Path) -> None:
    from enrama.core._render_context import image_paths

    source = tmp_path / "logo.png"
    source.write_bytes(image_bytes())
    config = client_config("logo.png", "logo.png", "logo.png")
    prepared = prepare_assets(config, source=tmp_path / "x.yaml")
    source.unlink()
    paths = image_paths(config, prepared)
    assert set(paths) == {"profile.avatar", "site.favicon", "site.og_image"}
    assert len(set(paths.values())) == 1
    assert next(iter(paths.values())).startswith("assets/client/")


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "duplicate",
        "wrong-reference",
        "wrong-field",
        "missing-asset",
        "duplicate-asset",
    ],
)
def test_mismatched_preparation_is_internal(damage: str, tmp_path: Path) -> None:
    from enrama.core._render_context import image_paths
    from enrama.core._render_errors import RenderError

    config = client_config("logo.png")
    binding = AssetBinding(("profile", "avatar"), "logo.png", PNG)
    prepared = PreparedAssets(
        tmp_path,
        tmp_path / "x.yaml",
        (),
        (PreparedAsset(b"snapshot", PNG),),
        (binding,),
    )
    if damage == "missing":
        prepared = replace(prepared, bindings=())
    elif damage == "extra":
        prepared = replace(
            prepared, bindings=(binding, replace(binding, location=("site", "favicon")))
        )
    elif damage == "duplicate":
        prepared = replace(prepared, bindings=(binding, binding))
    elif damage == "wrong-reference":
        prepared = replace(
            prepared, bindings=(replace(binding, reference="other.png"),)
        )
    elif damage == "wrong-field":
        prepared = replace(
            prepared,
            bindings=(replace(binding, location=("profile", "private\x1b[31m")),),
        )
    elif damage == "missing-asset":
        prepared = replace(prepared, assets=())
    else:
        prepared = replace(prepared, assets=prepared.assets * 2)
    with pytest.raises(RenderError) as caught:
        image_paths(config, prepared)
    error = caught.value
    assert error.kind == "internal"
    assert error.category == "asset_mismatch"
    assert error.message and error.hint
    assert "other.png" not in str(error)
    assert "private" not in str(error)
    assert "\x1b" not in str(error)
    assert str(tmp_path) not in str(error)
    assert error.field in (None, "profile.avatar", "site.favicon")


@pytest.mark.parametrize(
    "public_path",
    [
        "../outside.png",
        "/assets/client/" + "a" * 64 + ".png",
        "assets/client/" + "A" * 64 + ".png",
        "assets/client/" + "a" * 63 + ".png",
        "assets/client/" + "a" * 64 + ".jpeg",
        PNG + "?query",
        PNG + "\n",
        PNG.replace("/", "\\"),
        "https://evil.example/image.png",
    ],
)
def test_unsafe_or_noncanonical_paths_never_reach_templates(
    public_path: str, tmp_path: Path
) -> None:
    from enrama.core._render_context import image_paths
    from enrama.core._render_errors import RenderError

    config = client_config("logo.png")
    prepared = PreparedAssets(
        tmp_path,
        tmp_path / "x.yaml",
        (),
        (PreparedAsset(b"snapshot", public_path),),
        (AssetBinding(("profile", "avatar"), "logo.png", public_path),),
    )
    with pytest.raises(RenderError) as caught:
        image_paths(config, prepared)
    assert caught.value.kind == "internal"
    assert caught.value.category == "asset_mismatch"
    assert public_path not in str(caught.value)


@pytest.mark.parametrize(
    ("field", "suffix"),
    [("avatar", "ico"), ("og_image", "ico"), ("favicon", "jpg"), ("favicon", "webp")],
)
def test_public_extension_must_match_role(
    field: str, suffix: str, tmp_path: Path
) -> None:
    from enrama.core._render_context import image_paths
    from enrama.core._render_errors import RenderError

    config = client_config(
        **{"avatar": "logo.png"}
        if field == "avatar"
        else {"favicon": "logo.png"}
        if field == "favicon"
        else {"og": "logo.png"}
    )
    section = "profile" if field == "avatar" else "site"
    public_path = PNG.removesuffix("png") + suffix
    prepared = PreparedAssets(
        tmp_path,
        tmp_path / "x.yaml",
        (),
        (PreparedAsset(b"snapshot", public_path),),
        (AssetBinding((section, field), "logo.png", public_path),),
    )
    with pytest.raises(RenderError) as caught:
        image_paths(config, prepared)
    assert caught.value.field == section + "." + field
