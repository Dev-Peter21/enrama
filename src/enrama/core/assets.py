"""Prepare immutable client-image snapshots, without rendering or publication."""

import errno
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from enrama.config import EnramaConfig
from enrama.config._paths import validate_asset_path
from enrama.config.diagnostics import FieldLocation

from . import _asset_files as files
from ._asset_errors import (
    AssetDiagnostic,
    AssetEnvironmentError,
    AssetError,
    InvalidImage,
)
from ._asset_images import validate_image

__all__ = [
    "AssetBinding",
    "AssetDiagnostic",
    "AssetEnvironmentError",
    "AssetError",
    "PreparedAsset",
    "PreparedAssets",
    "prepare_assets",
    "copy_assets",
]


@dataclass(frozen=True)
class PreparedAsset:
    data: bytes
    public_path: str


@dataclass(frozen=True)
class AssetBinding:
    location: FieldLocation
    reference: str
    public_path: str


@dataclass(frozen=True)
class PreparedAssets:
    root: Path
    source: Path
    reserved_paths: tuple[Path, ...]
    assets: tuple[PreparedAsset, ...]
    bindings: tuple[AssetBinding, ...]

    @property
    def mapping(self) -> dict[str, str]:
        """Return a fresh field-to-public-path mapping; snapshots stay immutable."""
        return {
            ".".join(map(str, binding.location)): binding.public_path
            for binding in self.bindings
        }


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _working_paths(root: Path, reserved: tuple[Path, ...]) -> tuple[Path, ...]:
    result = []
    for path in reserved:
        candidate = Path(os.path.abspath(root / path))
        if (
            candidate == root
            or not candidate.is_relative_to(root)
            or candidate.parts[len(root.parts)].rstrip(". ").casefold() == "dist"
        ):
            raise files.UnsafePathError(
                "Working location must be inside the project outside dist"
            )
        if candidate.resolve() != candidate:
            raise files.UnsafePathError("Working location contains a link")
        result.append(candidate)
    return tuple(result)


def _reserved_source(root: Path, candidate: Path, reserved: tuple[Path, ...]) -> bool:
    for working in reserved:
        if candidate.is_relative_to(working):
            return True
        try:
            info = working.stat()
        except FileNotFoundError:
            continue
        # Existing filesystem identities cover case/normalization aliases on
        # volumes that alias them, without folding distinct Linux names.
        for ancestor in (candidate, *candidate.parents):
            if ancestor == root:
                break
            try:
                current = ancestor.stat()
            except FileNotFoundError:
                continue
            if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
                return True
    return False


def _relative(root: Path, reference: str, reserved: tuple[Path, ...]) -> Path:
    try:
        validate_asset_path(reference)
    except ValueError:
        raise files.UnsafePathError("Invalid lexical reference") from None
    relative = Path(*PurePosixPath(reference.replace("\\", "/")).parts)
    try:
        candidate = (root / relative).resolve()
    except RuntimeError:
        raise files.UnsafePathError("Source contains a symlink loop") from None
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise files.UnsafePathError("Source contains a symlink loop") from None
        raise
    if not candidate.is_relative_to(root) or candidate == root:
        raise files.UnsafePathError("Source escapes the client root")
    actual_parts = candidate.relative_to(root).parts
    if actual_parts[0].rstrip(". ").casefold() == "dist" or _reserved_source(
        root, candidate, reserved
    ):
        raise files.UnsafePathError("Source is a reserved location")
    return relative


def prepare_assets(
    config: EnramaConfig,
    *,
    source: str | Path = "enrama.yaml",
    reserved_paths: tuple[Path, ...] = (),
) -> PreparedAssets:
    """Validate all referenced images locally, returning no partial success."""
    source_path = Path(os.path.abspath(source))
    try:
        root = source_path.parent.resolve(strict=True)
        reserved = _working_paths(root, reserved_paths)
    except (OSError, RuntimeError):
        raise AssetError(
            [
                AssetDiagnostic(
                    "read_error",
                    source_path,
                    (),
                    None,
                    "The client root or reserved working locations are unavailable or unsafe.",
                    "Select an accessible client directory and safe project-local working paths.",
                )
            ]
        ) from None
    diagnostics: list[AssetDiagnostic] = []
    assets: dict[str, PreparedAsset] = {}
    digests: dict[str, bytes] = {}
    bindings = []
    collisions = []
    references = [
        (("profile", "avatar"), config.profile.avatar, False),
        (("site", "favicon"), config.site.favicon, True),
        (("site", "og_image"), config.site.og_image, False),
    ]
    for location, reference, favicon in references:
        if reference is None:
            continue
        try:
            relative = _relative(root, reference, reserved)
            data = files.read_source(root, relative, 1048576 if favicon else 5242880)
            extension = validate_image(data, reference, favicon=favicon)
            digest = _digest(data)
            public_path = f"assets/client/{digest}.{extension}"
            existing = digests.get(digest)
            if existing is not None and existing != data:
                collisions.append(
                    AssetDiagnostic(
                        "collision",
                        source_path,
                        (),
                        None,
                        "Different images claim the same content path.",
                        "Preserve the inputs and report the conflicting content digests.",
                    )
                )
                continue
            digests[digest] = data
            assets[public_path] = PreparedAsset(data, public_path)
            bindings.append(AssetBinding(location, reference, public_path))
        except files.UnsafePathError:
            diagnostics.append(
                AssetDiagnostic(
                    "unsafe_path",
                    source_path,
                    location,
                    reference,
                    "The source path is unsafe or is not a regular project file.",
                    "Use a regular file inside the client root, without symlinks or reserved paths.",
                )
            )
        except FileNotFoundError:
            diagnostics.append(
                AssetDiagnostic(
                    "missing_asset",
                    source_path,
                    location,
                    reference,
                    "The referenced image is missing.",
                    "Create the image or correct its relative reference.",
                )
            )
        except files.FileLimitError:
            diagnostics.append(
                AssetDiagnostic(
                    "resource_limit",
                    source_path,
                    location,
                    reference,
                    "The image exceeds this field's byte limit.",
                    "Export a smaller image and update the reference.",
                )
            )
        except InvalidImage as error:
            diagnostics.append(
                AssetDiagnostic(
                    error.category,
                    source_path,
                    location,
                    reference,
                    error.message,
                    error.hint,
                )
            )
        except OSError:
            diagnostics.append(
                AssetDiagnostic(
                    "read_error",
                    source_path,
                    location,
                    reference,
                    "The referenced image could not be read.",
                    "Check file and directory access permissions and retry.",
                )
            )
    diagnostics.extend(collisions)
    if not diagnostics and sum(len(asset.data) for asset in assets.values()) > 10485760:
        diagnostics.append(
            AssetDiagnostic(
                "resource_limit",
                source_path,
                (),
                None,
                "Unique referenced images exceed 10,485,760 bytes.",
                "Reduce the combined size of the referenced images.",
            )
        )
    if diagnostics:
        raise AssetError(diagnostics)
    return PreparedAssets(
        root, source_path, reserved, tuple(assets.values()), tuple(bindings)
    )


def _check_prepared(prepared: PreparedAssets) -> None:
    """Catch programming mistakes before a path from a prepared record is used."""
    import re

    paths = set()
    for asset in prepared.assets:
        if not re.fullmatch(
            r"assets/client/[0-9a-f]{64}\.(png|jpg|webp|ico)", asset.public_path
        ):
            raise ValueError("PreparedAssets contains an invalid content path")
        digest = asset.public_path.rsplit("/", 1)[1].split(".")[0]
        if (
            hashlib.sha256(asset.data).hexdigest() != digest
            or asset.public_path in paths
        ):
            raise ValueError("PreparedAssets content integrity is invalid")
        paths.add(asset.public_path)
    if paths != {binding.public_path for binding in prepared.bindings}:
        raise ValueError("PreparedAssets bindings do not match the snapshots")


def copy_assets(prepared: PreparedAssets, staging: str | Path) -> None:
    """Copy prepared bytes only to the caller's existing, reserved staging root."""
    _check_prepared(prepared)
    stage = Path(os.path.abspath(prepared.root / staging))
    try:
        working = _working_paths(prepared.root, prepared.reserved_paths)
        if stage not in working:
            raise files.UnsafePathError("Staging was not explicitly reserved")
        # Resolve/check all stage components again; caller must create this root.
        if stage.resolve(strict=True) != stage:
            raise files.UnsafePathError("Staging contains a link")
        files._directory(stage.lstat())
    except (OSError, RuntimeError):
        raise AssetError(
            [
                AssetDiagnostic(
                    "destination_conflict",
                    prepared.source,
                    (),
                    None,
                    "The staging directory is unavailable, unsafe or not explicitly reserved.",
                    "Provide the existing project-local working directory reserved during preparation.",
                )
            ]
        ) from None
    for asset in prepared.assets:
        try:
            relative = stage.relative_to(prepared.root) / Path(asset.public_path)
            files.write_snapshot(prepared.root, relative, asset.data, staging=stage)
        except files.UnsafePathError:
            raise AssetError(
                [
                    AssetDiagnostic(
                        "destination_conflict",
                        prepared.source,
                        (),
                        asset.public_path,
                        "The staging target is unsafe or contains conflicting content.",
                        "Inspect the caller-owned staging directory; do not overwrite the conflicting target.",
                    )
                ]
            ) from None
        except OSError:
            raise AssetError(
                [
                    AssetDiagnostic(
                        "write_error",
                        prepared.source,
                        (),
                        asset.public_path,
                        "The prepared image could not be copied into staging.",
                        "Check staging access and available storage; preserve partial data for safe caller cleanup.",
                    )
                ]
            ) from None
