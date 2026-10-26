"""Coordinate existing services through a guarded, recoverable output swap."""

import os
from dataclasses import dataclass
from pathlib import Path

from enrama.config import load_config
from enrama.themes import theme_view

from . import _asset_files as files
from ._build_errors import BuildError
from ._manifest import (
    MANIFEST,
    MAX_FILE,
    canonical,
    make_manifest,
    remove_owned,
    verify_output,
)
from ._project import ProjectSession, source_path
from .assets import copy_assets, prepare_assets
from .renderer import render_html


@dataclass(frozen=True)
class BuildResult:
    output: Path
    files: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def build_site(
    source: str | Path = "enrama.yaml", *, session: ProjectSession | None = None
) -> BuildResult:
    if session is None:
        with ProjectSession(source) as owned:
            return _build(owned)
    if not session.active or source_path(source) != session.source:
        raise BuildError(
            "internal",
            "session_mismatch",
            "Build ownership does not match the selected project",
            "Use the active session for the same configuration",
        )
    return _build(session)


def _build(session: ProjectSession) -> BuildResult:
    session.check()
    output = session.root / "dist"
    stage = session.work / "staging"
    backup = session.work / "backup"
    transaction = session.work / "transaction.json"
    old: tuple[bytes, tuple[str, ...]] | None = None
    if output.exists() or output.is_symlink():
        old = verify_output(output)
    config = load_config(session.source)
    prepared = prepare_assets(
        config,
        source=session.source,
        reserved_paths=(
            Path(".enrama"),
            Path(".enrama/staging"),
            Path(".enrama/backup"),
        ),
    )
    html = render_html(config, prepared).encode("utf-8")
    content = {asset.public_path: asset.data for asset in prepared.assets}
    view = theme_view(config.theme)
    content.update(view.assets)
    content["index.html"] = html
    manifest = make_manifest(content, config.schema_version)
    owned_paths: set[str] = set()
    published = False
    started = False
    stage_created = False
    stage_identity: tuple[int, int] | None = None
    try:
        session.check()
        with transaction.open("xb") as f:
            started = True
            f.write(
                canonical(
                    {
                        "format_version": 1,
                        "output": "dist",
                        "staging": "staging",
                        "backup": "backup",
                    }
                )
            )
        stage.mkdir()
        stage_created = True
        info = stage.lstat()
        stage_identity = (info.st_dev, info.st_ino)
        copy_assets(prepared, stage)
        owned_paths.update(asset.public_path for asset in prepared.assets)
        for name, data in content.items():
            if name not in prepared.mapping.values():
                files.write_snapshot(
                    session.root,
                    (stage / name).relative_to(session.root),
                    data,
                    staging=stage,
                )
                owned_paths.add(name)
        with (stage / MANIFEST).open("xb") as f:
            owned_paths.add(MANIFEST)
            f.write(manifest)
        _check_stage(stage, stage_identity)
        if verify_output(stage) != (manifest, tuple(sorted(content))):
            raise BuildError(
                "operational",
                "staging_changed",
                "Staging changed during generation",
                "Preserve the transaction and inspect its staging data",
            )
        session.check()
        if old is not None:
            if verify_output(output) != old:
                raise BuildError(
                    "operational",
                    "output_changed",
                    "Output changed during generation",
                    "Preserve dist/ and inspect manual changes",
                )
        elif output.exists() or output.is_symlink():
            raise BuildError(
                "operational",
                "output_changed",
                "Output appeared during generation",
                "Preserve dist/ and inspect it before retrying",
            )
        if backup.exists() or backup.is_symlink():
            raise BuildError(
                "operational",
                "workspace_changed",
                "A backup location appeared during generation",
                "Preserve .enrama/ and inspect the conflicting data",
            )
        if old is not None:
            os.rename(output, backup)
        os.rename(stage, output)
        published = True
        if old is not None:
            verify_output(backup)
            remove_owned(backup, set(old[1]) | {MANIFEST})
        transaction.unlink()
        return BuildResult(output, tuple(sorted(content)), view.warnings)
    except BaseException as original:
        if started:
            try:
                session.check()
                if not published and (backup.exists() or backup.is_symlink()):
                    verify_output(backup)
                    if output.exists() or output.is_symlink():
                        raise OSError("Cannot restore output")
                    os.rename(backup, output)
                if stage.exists() or stage.is_symlink():
                    if not stage_created:
                        raise OSError("Staging was not created by this invocation")
                    _check_stage(stage, stage_identity)
                    for name in owned_paths:
                        path = stage / name
                        if path.exists() or path.is_symlink():
                            expected_data = (
                                manifest if name == MANIFEST else content[name]
                            )
                            if (
                                files.read_source(stage, Path(name), MAX_FILE)
                                != expected_data
                            ):
                                raise OSError("Owned staging content changed")
                    remove_owned(stage, owned_paths)
                if published and (backup.exists() or backup.is_symlink()):
                    raise OSError("Preserve remaining backup after commit")
                if transaction.exists():
                    transaction.unlink()
            except (OSError, BuildError, files.FileLimitError):
                raise BuildError(
                    "operational",
                    "recovery_required",
                    "Build cleanup or restoration could not complete",
                    "Preserve dist/ and all .enrama/ transaction data; inspect recovery locations manually",
                ) from None
        if isinstance(original, OSError):
            raise BuildError(
                "operational",
                "build_io",
                "The site could not be generated or published",
                "Check filesystem access and storage; previous output was preserved or restored",
            ) from None
        raise


def _check_stage(stage: Path, identity: tuple[int, int] | None) -> None:
    info = stage.lstat()
    files._directory(info)
    if identity != (info.st_dev, info.st_ino):
        raise OSError("Staging identity changed")
