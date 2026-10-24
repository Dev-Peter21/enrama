"""Read-only preparation, filesystem boundaries, snapshots and field errors."""

import importlib
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import ModuleType

import pytest
from asset_helpers import client_config, image_bytes


def api() -> ModuleType:
    return importlib.import_module("enrama.core.assets")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    folder = tmp_path / "client"
    folder.mkdir()
    return folder


def test_optional_images_need_no_asset_reads(root: Path) -> None:
    module = api()
    result = module.prepare_assets(client_config(), source=root / "selected.yaml")
    assert result.mapping == {}
    assert result.assets == () and result.bindings == ()
    assert list(root.iterdir()) == []


def test_prepare_snapshot_mapping_and_immutability(root: Path) -> None:
    module = api()
    data = image_bytes()
    (root / "portrait.PNG").write_bytes(data)
    before = list(root.iterdir())
    result = module.prepare_assets(
        client_config("portrait.PNG", "portrait.PNG", "./portrait.PNG"),
        source=root / "selected.yaml",
    )
    import hashlib

    path = f"assets/client/{hashlib.sha256(data).hexdigest()}.png"
    assert result.mapping == {
        "profile.avatar": path,
        "site.favicon": path,
        "site.og_image": path,
    }
    assert len(result.assets) == 1 and result.assets[0].data == data
    assert list(root.iterdir()) == before
    with pytest.raises(FrozenInstanceError):
        result.assets[0].data = b"changed"
    result.mapping.clear()
    assert len(result.mapping) == 3


def test_source_root_portable_separator_and_cwd(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = api()
    (root / "assets").mkdir()
    (root / "assets/pic.png").write_bytes(image_bytes())
    monkeypatch.chdir(tmp_path)
    result = module.prepare_assets(
        client_config(r".\assets\pic.png"), source=Path("client/custom.yaml")
    )
    assert result.root == root.resolve()
    assert result.mapping["profile.avatar"].startswith("assets/client/")
    assert Path.cwd() == tmp_path


@pytest.mark.parametrize("reference", ["missing.png", "nested/missing.png"])
def test_missing_source(root: Path, reference: str) -> None:
    module = api()
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(client_config(reference), source=root / "enrama.yaml")
    assert error.value.kind == "invalid_input"
    assert error.value.diagnostics[0].category == "missing_asset"
    assert error.value.diagnostics[0].location == ("profile", "avatar")


def test_shared_content_checks_each_role(root: Path) -> None:
    module = api()
    (root / "pic.jpg").write_bytes(image_bytes("JPEG"))
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("pic.jpg", "pic.jpg"), source=root / "enrama.yaml"
        )
    assert error.value.total_count == 1
    assert error.value.diagnostics[0].location == ("site", "favicon")


@pytest.mark.parametrize("size", [1048576, 1048577])
def test_favicon_byte_boundary(root: Path, size: int) -> None:
    module = api()
    data = image_bytes()
    data += b"\x00" * (size - len(data))
    (root / "pic.png").write_bytes(data)
    if size == 1048576:
        assert (
            module.prepare_assets(
                client_config(favicon="pic.png"), source=root / "enrama.yaml"
            )
            .assets[0]
            .data
            == data
        )
    else:
        with pytest.raises(module.AssetError) as error:
            module.prepare_assets(
                client_config(favicon="pic.png"), source=root / "enrama.yaml"
            )
        assert error.value.diagnostics[0].category == "resource_limit"


@pytest.mark.parametrize("extra", [0, 1])
def test_unique_total_budget(root: Path, extra: int) -> None:
    module = api()
    for name, color, length in [
        ("a.png", "red", 5242880),
        ("b.png", "blue", 5242880),
        ("f.png", "green", extra),
    ]:
        data = image_bytes(color=color)
        if name == "f.png" and not extra:
            continue
        if name == "f.png":
            # Reduce the second image so total with this valid favicon is max+1.
            other = (root / "b.png").read_bytes()
            (root / "b.png").write_bytes(other[: len(other) - len(data) + 1])
        else:
            data += b"\x00" * (length - len(data))
        (root / name).write_bytes(data)
    cfg = client_config("a.png", "f.png" if extra else None, "b.png")
    if extra:
        with pytest.raises(module.AssetError) as error:
            module.prepare_assets(cfg, source=root / "enrama.yaml")
        assert error.value.diagnostics[0].location == ()
        assert error.value.diagnostics[0].category == "resource_limit"
    else:
        assert len(module.prepare_assets(cfg, source=root / "enrama.yaml").assets) == 2


def test_equal_content_files_count_once(root: Path) -> None:
    module = api()
    data = image_bytes()
    data += b"\x00" * (5242880 - len(data))
    (root / "a.png").write_bytes(data)
    (root / "b.png").write_bytes(data)
    result = module.prepare_assets(
        client_config("a.png", og="b.png"), source=root / "enrama.yaml"
    )
    assert len(result.assets) == 1


@pytest.mark.parametrize("kind", ["file", "internal", "directory", "broken"])
def test_all_internal_symlinks_rejected(root: Path, tmp_path: Path, kind: str) -> None:
    module = api()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pic.png").write_bytes(image_bytes())
    (root / "original.png").write_bytes(image_bytes())
    target = root / "link.png"
    try:
        if kind == "directory":
            (root / "linked").symlink_to(outside, target_is_directory=True)
            reference = "linked/pic.png"
        else:
            target.symlink_to(
                root / "original.png"
                if kind == "internal"
                else outside / "pic.png"
                if kind == "file"
                else outside / "missing.png"
            )
            reference = "link.png"
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(client_config(reference), source=root / "enrama.yaml")
    assert error.value.diagnostics[0].category == "unsafe_path"
    assert (outside / "pic.png").read_bytes() == image_bytes()


def test_source_directory_rejected(root: Path) -> None:
    module = api()
    (root / "dir.png").mkdir()
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(client_config("dir.png"), source=root / "enrama.yaml")
    assert error.value.diagnostics[0].category == "unsafe_path"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO required")
def test_fifo_rejected_without_blocking(root: Path) -> None:
    os.mkfifo(root / "pipe.png")
    code = """from enrama.config import EnramaConfig
from enrama.core.assets import prepare_assets,AssetError
from pathlib import Path
import sys
config=EnramaConfig.model_validate({"schema_version":1,"site":{"title":"x","description":"x","language":"en"},"profile":{"name":"x","avatar":"pipe.png"}})
try: prepare_assets(config,source=Path(sys.argv[1])/"enrama.yaml")
except AssetError as e: assert e.diagnostics[0].category=="unsafe_path"
else: raise AssertionError("FIFO accepted")
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(root)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr


def test_reserved_working_source(root: Path) -> None:
    module = api()
    stage = root / "work"
    stage.mkdir()
    (stage / "pic.png").write_bytes(image_bytes())
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("work/pic.png"),
            source=root / "enrama.yaml",
            reserved_paths=(stage,),
        )
    assert error.value.diagnostics[0].category == "unsafe_path"


@pytest.mark.parametrize(
    "reference",
    [
        "../out.png",
        "/out.png",
        r"C:\out.png",
        "dist/pic.png",
        "DIST./pic.png",
        "https://example.com/pic.png",
    ],
)
def test_defensive_lexical_policy(root: Path, reference: str) -> None:
    module = api()
    config = client_config()
    config = config.model_copy(
        update={"profile": config.profile.model_copy(update={"avatar": reference})}
    )
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(config, source=root / "enrama.yaml")
    assert error.value.diagnostics[0].category == "unsafe_path"


def test_expected_multi_field_order_and_safe_text(root: Path) -> None:
    module = api()
    cfg = client_config("a\x1b.png", "f.png", "o.png")
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(cfg, source=root / "enrama.yaml")
    assert [d.location for d in error.value.diagnostics] == [
        ("profile", "avatar"),
        ("site", "favicon"),
        ("site", "og_image"),
    ]
    assert error.value.total_count == 3 and error.value.omitted_count == 0
    assert "\x1b" not in str(error.value) and "\\u001b" in str(error.value)
    assert ":1:" not in str(error.value)


def test_mixed_operational_errors_not_selected_by_first_field(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = api()
    files = importlib.import_module("enrama.core._asset_files")
    (root / "blocked.png").write_bytes(image_bytes())
    original = files.read_source

    def read(folder: Path, relative: Path, limit: int) -> bytes:
        if relative.name == "blocked.png":
            raise PermissionError("PRIVATE raw operating system payload")
        return original(folder, relative, limit)  # type: ignore[no-any-return]

    monkeypatch.setattr(files, "read_source", read)
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("missing.png", "blocked.png"), source=root / "enrama.yaml"
        )
    assert error.value.kind == "operational" and error.value.total_count == 2
    assert error.value.diagnostics[0].category == "missing_asset"
    assert "PRIVATE" not in str(error.value)


def test_forced_hash_collision_is_not_deduplicated(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = api()
    (root / "a.png").write_bytes(image_bytes())
    (root / "b.png").write_bytes(image_bytes(color="blue"))
    monkeypatch.setattr(module, "_digest", lambda data: "0" * 64)
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("a.png", og="b.png"), source=root / "enrama.yaml"
        )
    assert (
        error.value.diagnostics[-1].category == "collision"
        and error.value.kind == "invalid_input"
    )


@pytest.mark.parametrize("failure", [RuntimeError("defect"), KeyboardInterrupt()])
def test_unexpected_failures_propagate(
    root: Path, monkeypatch: pytest.MonkeyPatch, failure: BaseException
) -> None:
    module = api()
    files = importlib.import_module("enrama.core._asset_files")

    def broken(*args: object) -> bytes:
        raise failure

    monkeypatch.setattr(files, "read_source", broken)
    with pytest.raises(type(failure)):
        module.prepare_assets(client_config("a.png"), source=root / "enrama.yaml")


def test_symlink_loop_is_invalid_input(root: Path) -> None:
    module = api()
    try:
        (root / "loop.png").symlink_to("loop.png")
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(client_config("loop.png"), source=root / "enrama.yaml")
    assert error.value.kind == "invalid_input"
    assert error.value.diagnostics[0].category == "unsafe_path"


def test_parent_replaced_after_inspection(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = api()
    files = importlib.import_module("enrama.core._asset_files")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "pic.png").write_bytes(image_bytes(color="blue"))
    folder = root / "folder"
    folder.mkdir()
    (folder / "pic.png").write_bytes(image_bytes())
    original = files._stat

    def replacing(parent: int | None, path: Path) -> os.stat_result:
        info = original(parent, path)
        if path == folder:
            folder.rename(root / "saved")
            try:
                folder.symlink_to(outside, target_is_directory=True)
            except OSError:
                pytest.skip("symlink creation unavailable")
        return info  # type: ignore[no-any-return]

    monkeypatch.setattr(files, "_stat", replacing)
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("folder/pic.png"), source=root / "enrama.yaml"
        )
    assert error.value.diagnostics[0].category == "unsafe_path"
    assert (outside / "pic.png").read_bytes() == image_bytes(color="blue")


def test_os_symlink_loop_is_also_invalid_input(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import errno

    module = api()
    original = Path.resolve

    def resolve(path: Path, strict: bool = False) -> Path:
        if path.name == "loop.png":
            raise OSError(errno.ELOOP, "loop")
        return original(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(client_config("loop.png"), source=root / "enrama.yaml")
    assert error.value.diagnostics[0].category == "unsafe_path"
    assert error.value.kind == "invalid_input"


@pytest.mark.parametrize("alias", ["uppercase", "unicode"])
def test_filesystem_alias_cannot_bypass_reserved_root(root: Path, alias: str) -> None:
    import unicodedata

    module = api()
    name = "work" if alias == "uppercase" else "caf\u00e9"
    other = "WORK" if alias == "uppercase" else unicodedata.normalize("NFD", name)
    reserved = root / name
    reserved.mkdir()
    (reserved / "pic.png").write_bytes(image_bytes())
    if not (root / other / "pic.png").exists():
        pytest.skip("filesystem does not alias these names")
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config(f"{other}/pic.png"),
            source=root / "enrama.yaml",
            reserved_paths=(reserved,),
        )
    assert error.value.diagnostics[0].category == "unsafe_path"


def test_digest_collision_across_formats_is_explicit(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = api()
    (root / "a.png").write_bytes(image_bytes())
    (root / "b.jpg").write_bytes(image_bytes("JPEG"))
    monkeypatch.setattr(module, "_digest", lambda data: "0" * 64)
    with pytest.raises(module.AssetError) as error:
        module.prepare_assets(
            client_config("a.png", og="b.jpg"), source=root / "enrama.yaml"
        )
    assert error.value.diagnostics[-1].category == "collision"
