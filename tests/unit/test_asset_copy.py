"""Only prepared bytes enter explicit caller-owned staging; no publication."""

import importlib
import os
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from asset_helpers import client_config, image_bytes


def api() -> ModuleType:
    return importlib.import_module("enrama.core.assets")


@pytest.fixture
def prepared(tmp_path: Path) -> tuple[Any, Path]:
    module = api()
    root = tmp_path / "client"
    root.mkdir()
    (root / "pic.png").write_bytes(image_bytes())
    stage = root / "work"
    value = module.prepare_assets(
        client_config("pic.png", og="pic.png"),
        source=root / "enrama.yaml",
        reserved_paths=(stage,),
    )
    stage.mkdir()
    return value, stage


def test_copy_exact_snapshot_and_reuse(
    prepared: tuple[Any, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    value, stage = prepared
    module = api()
    module.copy_assets(value, stage)
    output = stage / value.mapping["profile.avatar"]
    assert output.read_bytes() == image_bytes()
    stamp = output.stat().st_mtime_ns
    module.copy_assets(value, stage)
    assert output.stat().st_mtime_ns == stamp
    assert len(list((stage / "assets/client").iterdir())) == 1
    assert (value.root / "pic.png").read_bytes() == image_bytes()
    assert not (value.root / "dist").exists()
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_copy_uses_validated_bytes_after_source_change(
    prepared: tuple[Any, Path], change: str
) -> None:
    value, stage = prepared
    source = value.root / "pic.png"
    if change == "edit":
        source.write_bytes(b"not an image anymore")
    else:
        source.unlink()
    api().copy_assets(value, stage)
    assert (stage / value.mapping["profile.avatar"]).read_bytes() == image_bytes()
    if change == "edit":
        assert source.read_bytes() == b"not an image anymore"


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "fifo"])
def test_existing_conflict_preserved(prepared: tuple[Any, Path], kind: str) -> None:
    value, stage = prepared
    module = api()
    output = stage / value.mapping["profile.avatar"]
    output.parent.mkdir(parents=True)
    if kind == "file":
        output.write_bytes(b"PRESERVE")
    elif kind == "directory":
        output.mkdir()
    elif kind == "fifo":
        if not hasattr(os, "mkfifo"):
            pytest.skip("POSIX FIFO required")
        os.mkfifo(output)
    else:
        try:
            output.symlink_to(value.root / "pic.png")
        except OSError:
            pytest.skip("symlink creation unavailable")
    with pytest.raises(module.AssetError) as error:
        module.copy_assets(value, stage)
    assert error.value.kind == "operational"
    assert error.value.diagnostics[0].category == "destination_conflict"
    if kind == "file":
        assert output.read_bytes() == b"PRESERVE"
    assert (value.root / "pic.png").read_bytes() == image_bytes()


@pytest.mark.parametrize("component", ["assets", "assets/client"])
def test_staging_component_symlink_rejected(
    prepared: tuple[Any, Path], tmp_path: Path, component: str
) -> None:
    value, stage = prepared
    module = api()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = stage / component
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(module.AssetError) as error:
        module.copy_assets(value, stage)
    assert error.value.kind == "operational" and list(outside.iterdir()) == []


@pytest.mark.parametrize(
    "destination", ["root", "dist", "unreserved", "outside", "missing"]
)
def test_only_exact_existing_reserved_staging_is_allowed(
    prepared: tuple[Any, Path], tmp_path: Path, destination: str
) -> None:
    value, stage = prepared
    module = api()
    folder = {
        "root": value.root,
        "dist": value.root / "dist",
        "unreserved": value.root / "other",
        "outside": tmp_path / "outside",
        "missing": stage / "missing",
    }[destination]
    if destination not in {"root", "missing"}:
        folder.mkdir()
    before = {p.relative_to(value.root) for p in value.root.rglob("*")}
    with pytest.raises(module.AssetError) as error:
        module.copy_assets(value, folder)
    assert error.value.kind == "operational"
    assert {p.relative_to(value.root) for p in value.root.rglob("*")} == before


def test_stage_replaced_by_internal_link(prepared: tuple[Any, Path]) -> None:
    value, stage = prepared
    module = api()
    target = value.root / "originals"
    target.mkdir()
    stage.rmdir()
    try:
        stage.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(module.AssetError):
        module.copy_assets(value, stage)
    assert list(target.iterdir()) == []


def test_relative_stage_and_unrelated_cwd(
    prepared: tuple[Any, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value, stage = prepared
    monkeypatch.chdir(tmp_path)
    api().copy_assets(value, Path("work"))
    assert (stage / value.mapping["profile.avatar"]).read_bytes() == image_bytes()


def test_protected_hardlink_cannot_modify_original(prepared: tuple[Any, Path]) -> None:
    value, stage = prepared
    output = stage / value.mapping["profile.avatar"]
    output.parent.mkdir(parents=True)
    original = value.root / "pic.png"
    original.write_bytes(b"CHANGED ORIGINAL")
    try:
        os.link(original, output)
    except OSError:
        pytest.skip("hardlink creation unavailable")
    with pytest.raises(api().AssetError):
        api().copy_assets(value, stage)
    assert (
        original.read_bytes() == b"CHANGED ORIGINAL"
        and output.read_bytes() == b"CHANGED ORIGINAL"
    )


@pytest.mark.parametrize(
    "path", ["../../escape.png", "assets/client/wrong.png", "assets/theme/file.png"]
)
def test_forged_prepared_paths_are_rejected_before_writes(
    prepared: tuple[Any, Path], path: str
) -> None:
    value, stage = prepared
    forged = replace(value, assets=(replace(value.assets[0], public_path=path),))
    with pytest.raises(ValueError):
        api().copy_assets(forged, stage)
    assert list(stage.iterdir()) == []


def test_operational_copy_failure_is_safe(
    prepared: tuple[Any, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    value, stage = prepared
    module = api()
    files = importlib.import_module("enrama.core._asset_files")

    def denied(*args: object, **kwargs: object) -> None:
        raise PermissionError("PRIVATE raw OS payload")

    monkeypatch.setattr(files, "write_snapshot", denied)
    with pytest.raises(module.AssetError) as error:
        module.copy_assets(value, stage)
    assert (
        error.value.kind == "operational"
        and error.value.diagnostics[0].category == "write_error"
    )
    assert "PRIVATE" not in str(error.value)
    assert (value.root / "pic.png").read_bytes() == image_bytes()


def test_empty_preparation_creates_no_namespace(prepared: tuple[Any, Path]) -> None:
    value, stage = prepared
    module = api()
    empty = module.prepare_assets(
        client_config(), source=value.source, reserved_paths=(stage,)
    )
    module.copy_assets(empty, stage)
    assert list(stage.iterdir()) == []


def test_removed_staging_is_not_recreated(
    prepared: tuple[Any, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    value, stage = prepared
    module = api()
    files = importlib.import_module("enrama.core._asset_files")
    original = files.write_snapshot

    def removed(root: Path, relative: Path, data: bytes, **kwargs: object) -> None:
        stage.rmdir()
        original(root, relative, data, **kwargs)

    monkeypatch.setattr(files, "write_snapshot", removed)
    with pytest.raises(module.AssetError) as error:
        module.copy_assets(value, stage)
    assert error.value.kind == "operational" and not stage.exists()
