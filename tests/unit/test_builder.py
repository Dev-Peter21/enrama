"""End-to-end build preservation, integrity and coordination behavior."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from asset_helpers import image_bytes

from enrama.core import render_html
from enrama.core._manifest import remove_owned


def client(root: Path, avatar: bool = True) -> Path:
    root.mkdir(exist_ok=True)
    source = root / "selected.yaml"
    source.write_text(
        "schema_version: 1\nsite: {title: Shop, description: Shop, language: en}\nprofile: {name: Shop"
        + (", avatar: logo.png" if avatar else "")
        + "}\n",
        encoding="utf-8",
    )
    if avatar:
        (root / "logo.png").write_bytes(image_bytes())
    return source


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


def test_complete_repeatable_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core.builder import build_site

    source = client(tmp_path / "client")
    monkeypatch.chdir(tmp_path)
    result = build_site(source)
    assert result.output == source.parent / "dist"
    first = snapshot(result.output)
    manifest = json.loads(first[".enrama-manifest.json"])
    assert manifest["format_version"] == 1 and manifest["generator"]["name"] == "enrama"
    assert manifest["schema_version"] == 1
    assert any(i["path"] == "index.html" for i in manifest["files"])
    for item in manifest["files"]:
        assert item["sha256"] == hashlib.sha256(first[item["path"]]).hexdigest()
        assert item["size"] == len(first[item["path"]])
    assert str(tmp_path).encode() not in first[".enrama-manifest.json"]
    assert b"\r" not in first["index.html"]
    build_site(source)
    assert snapshot(result.output) == first
    assert not any(
        (source.parent / ".enrama" / n).exists()
        for n in ("staging", "backup", "transaction.json")
    )


def test_stale_assets_removed_original_preserved(tmp_path: Path) -> None:
    from enrama.core.builder import build_site

    source = client(tmp_path)
    old = set(build_site(source).files)
    source.write_text(source.read_text().replace(", avatar: logo.png", ""))
    result = build_site(source)
    assert old - set(result.files)
    assert (tmp_path / "logo.png").read_bytes() == image_bytes()
    assert not list((tmp_path / "dist").glob("assets/client/*"))


@pytest.mark.parametrize(
    "damage",
    [
        "edited",
        "missing",
        "extra",
        "empty-dir",
        "no-manifest",
        "broken-manifest",
        "unsafe-inventory",
        "extra-key",
    ],
)
def test_modified_output_preserved(damage: str, tmp_path: Path) -> None:
    from enrama.core._build_errors import BuildError
    from enrama.core.builder import build_site

    source = client(tmp_path)
    build_site(source)
    output = tmp_path / "dist"
    if damage == "edited":
        (output / "index.html").write_text("MANUAL CONTENT")
    elif damage == "missing":
        (output / "index.html").unlink()
    elif damage == "extra":
        (output / "user.txt").write_text("MANUAL CONTENT")
    elif damage == "empty-dir":
        (output / "empty").mkdir()
    elif damage == "no-manifest":
        (output / ".enrama-manifest.json").unlink()
    elif damage == "broken-manifest":
        (output / ".enrama-manifest.json").write_text("{bad")
    else:
        path = output / ".enrama-manifest.json"
        data = json.loads(path.read_text())
        if damage == "unsafe-inventory":
            data["files"][0]["path"] = "../selected.yaml"
        else:
            data["private"] = "MANUAL CONTENT"
        path.write_text(json.dumps(data))
    before = snapshot(tmp_path)
    with pytest.raises(BuildError) as caught:
        build_site(source)
    assert caught.value.kind == "operational"
    assert snapshot(tmp_path) == before
    assert "MANUAL CONTENT" not in str(caught.value)


def test_empty_dist_protected(tmp_path: Path) -> None:
    from enrama.core._build_errors import BuildError
    from enrama.core.builder import build_site

    source = client(tmp_path)
    (tmp_path / "dist").mkdir()
    with pytest.raises(BuildError):
        build_site(source)
    assert list((tmp_path / "dist").iterdir()) == []


def test_unknown_workspace_and_incomplete_transaction_preserved(tmp_path: Path) -> None:
    from enrama.core._build_errors import BuildError
    from enrama.core.builder import build_site

    source = client(tmp_path)
    work = tmp_path / ".enrama"
    work.mkdir()
    (work / "precious").write_text("mine")
    with pytest.raises(BuildError):
        build_site(source)
    assert (work / "precious").read_text() == "mine"
    (work / "precious").unlink()
    work.rmdir()
    build_site(source)
    (work / "transaction.json").write_text('{"format_version":1}')
    (work / "backup").mkdir()
    (work / "backup/precious").write_text("recoverable")
    before = snapshot(tmp_path)
    with pytest.raises(BuildError) as caught:
        build_site(source)
    assert (
        caught.value.category == "incomplete_operation" and snapshot(tmp_path) == before
    )


def test_validate_no_writes_even_with_active_session(tmp_path: Path) -> None:
    from enrama.core._project import ProjectSession, validate_project

    source = client(tmp_path)
    before = snapshot(tmp_path)
    validate_project(source)
    assert snapshot(tmp_path) == before and not (tmp_path / ".enrama").exists()
    with ProjectSession(source):
        before = snapshot(tmp_path)
        validate_project(source)
        assert snapshot(tmp_path) == before


def test_nonblocking_cross_process_guard(tmp_path: Path) -> None:
    from enrama.core._project import ProjectSession

    source = client(tmp_path)
    code = "from enrama.core._project import ProjectSession\nfrom enrama.core._build_errors import BuildError\nimport sys\ntry:\n with ProjectSession(sys.argv[1]): pass\nexcept BuildError as e:\n print(e.kind);sys.exit(3)"
    with ProjectSession(source):
        result = subprocess.run(
            [sys.executable, "-c", code, str(source)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    assert result.returncode == 3 and "operational" in result.stdout
    with ProjectSession(source):
        pass


@pytest.mark.parametrize("target", ["dist", "workspace", "output-file"])
def test_symlinks_never_followed(target: str, tmp_path: Path) -> None:
    from enrama.core._build_errors import BuildError
    from enrama.core.builder import build_site

    source = client(tmp_path / "client")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret").write_text("precious")
    root = source.parent
    try:
        if target == "dist":
            (root / "dist").symlink_to(outside, target_is_directory=True)
        elif target == "workspace":
            (root / ".enrama").symlink_to(outside, target_is_directory=True)
        else:
            build_site(source)
            (root / "dist/index.html").unlink()
            (root / "dist/index.html").symlink_to(outside / "secret")
    except OSError:
        pytest.skip("Symlinks unavailable")
    with pytest.raises(BuildError):
        build_site(source)
    assert (outside / "secret").read_text() == "precious"


def test_failed_publication_restores_old_site(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    before = snapshot(tmp_path / "dist")
    real = os.rename

    def fail_stage(
        src: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        dst: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    ) -> None:
        if Path(os.fsdecode(src)).name == "staging":
            raise PermissionError("INJECTED SECRET")
        real(src, dst)

    monkeypatch.setattr(os, "rename", fail_stage)
    with pytest.raises(BuildError):
        builder.build_site(source)
    assert snapshot(tmp_path / "dist") == before
    assert not (tmp_path / ".enrama/transaction.json").exists()


def test_invalid_input_preserves_old_site(tmp_path: Path) -> None:
    from enrama.config import ConfigurationError
    from enrama.core.builder import build_site

    source = client(tmp_path)
    build_site(source)
    before = snapshot(tmp_path / "dist")
    source.write_text("schema_version: wrong")
    with pytest.raises(ConfigurationError):
        build_site(source)
    assert (
        snapshot(tmp_path / "dist") == before
        and not (tmp_path / ".enrama/transaction.json").exists()
    )


def test_new_manual_edits_during_generation_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    real = render_html

    def edit(config: object, prepared: object) -> str:
        (tmp_path / "dist/index.html").write_text("NEW MANUAL CONTENT")
        return real(config, prepared)  # type: ignore[arg-type]

    monkeypatch.setattr(builder, "render_html", edit)
    with pytest.raises(BuildError):
        builder.build_site(source)
    assert (tmp_path / "dist/index.html").read_text() == "NEW MANUAL CONTENT"


def test_unknown_staging_content_survives_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    old = snapshot(tmp_path / "dist")

    def add_unknown(prepared: object, stage: Path) -> None:
        (stage / "precious.txt").write_text("RECOVER ME")
        raise OSError("simulated copy failure")

    monkeypatch.setattr(builder, "copy_assets", add_unknown)
    with pytest.raises(BuildError) as error:
        builder.build_site(source)
    assert error.value.category == "recovery_required"
    assert snapshot(tmp_path / "dist") == old
    assert (tmp_path / ".enrama/staging/precious.txt").read_text() == "RECOVER ME"
    assert (tmp_path / ".enrama/transaction.json").exists()


def test_failed_rollback_preserves_both_recoverable_trees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    old = snapshot(tmp_path / "dist")
    real = os.rename

    def fail(
        src: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        dst: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    ) -> None:
        if Path(os.fsdecode(src)).name in {"staging", "backup"}:
            raise PermissionError("simulated")
        real(src, dst)

    monkeypatch.setattr(os, "rename", fail)
    with pytest.raises(BuildError) as error:
        builder.build_site(source)
    assert error.value.category == "recovery_required"
    assert snapshot(tmp_path / ".enrama/backup") == old
    assert (tmp_path / ".enrama/staging/index.html").exists()
    assert (tmp_path / ".enrama/transaction.json").exists()
    with pytest.raises(BuildError):
        builder.build_site(source)


def test_cleanup_failure_keeps_new_complete_site_and_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    old = snapshot(tmp_path / "dist")
    real = remove_owned

    def fail(root: Path, expected: set[str]) -> None:
        if root.name == "backup":
            raise PermissionError("simulated")
        real(root, expected)

    monkeypatch.setattr(builder, "remove_owned", fail)
    with pytest.raises(BuildError) as error:
        builder.build_site(source)
    assert error.value.kind == "operational"
    assert (
        snapshot(tmp_path / "dist") == old
        and snapshot(tmp_path / ".enrama/backup") == old
    )
    assert (tmp_path / ".enrama/transaction.json").exists()


def test_unowned_stage_collision_never_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    real = Path.mkdir

    def collide(
        path: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        if path.name == "staging":
            real(path)
            (path / "index.html").write_text("SOMEONE ELSE CREATED THIS")
        real(path, mode, parents, exist_ok)

    monkeypatch.setattr(Path, "mkdir", collide)
    with pytest.raises(BuildError):
        builder.build_site(source)
    assert (
        tmp_path / ".enrama/staging/index.html"
    ).read_text() == "SOMEONE ELSE CREATED THIS"


def test_unowned_empty_backup_never_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from enrama.core import builder
    from enrama.core._build_errors import BuildError

    source = client(tmp_path)
    builder.build_site(source)
    real = render_html

    def collide(config: object, prepared: object) -> str:
        (tmp_path / ".enrama/backup").mkdir()
        return real(config, prepared)  # type: ignore[arg-type]

    monkeypatch.setattr(builder, "render_html", collide)
    with pytest.raises(BuildError):
        builder.build_site(source)
    assert (tmp_path / ".enrama/backup").is_dir()
    assert (tmp_path / "dist/index.html").exists()
