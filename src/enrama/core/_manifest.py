"""Bounded output inventories, whole-tree verification and owned cleanup."""

import hashlib
import json
import re
import stat
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from typing import Any

from . import _asset_files as files
from ._build_errors import BuildError

MANIFEST = ".enrama-manifest.json"
MAX_FILE = 16 * 1024 * 1024
MAX_MANIFEST = 1024 * 1024
_ALLOWED = re.compile(
    r"(?:index\.html|assets/client/[0-9a-f]{64}\.(?:png|jpg|webp|ico)|assets/theme/[0-9a-f]{64}\.css|assets/theme/THIRD_PARTY_NOTICES\.txt)"
)


def conflict() -> BuildError:
    return BuildError(
        "operational",
        "output_conflict",
        "The output is not an intact recognized Enrama site",
        "Inspect dist/ and deliberately move conflicting content before rebuilding",
    )


def canonical(data: object) -> bytes:
    return (
        json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def inventory(root: Path) -> tuple[set[str], set[str]]:
    files._directory(root.lstat())
    names: set[str] = set()
    directories: set[str] = set()

    def visit(directory: Path) -> None:
        for path in directory.iterdir():
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if files._linked(info):
                raise conflict()
            if stat.S_ISDIR(info.st_mode):
                directories.add(relative)
                if len(directories) > 256:
                    raise conflict()
                visit(path)
            elif stat.S_ISREG(info.st_mode):
                names.add(relative)
                if len(names) > 256:
                    raise conflict()
            else:
                raise conflict()

    visit(root)
    return names, directories


def parent_names(names: set[str]) -> set[str]:
    return {
        str(parent)
        for name in names
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }


def make_manifest(content: dict[str, bytes], schema: int = 1) -> bytes:
    if "index.html" not in content or any(not _ALLOWED.fullmatch(n) for n in content):
        raise BuildError(
            "internal",
            "inventory_error",
            "The generated inventory is invalid",
            "Report the internal build defect",
        )
    if sum(len(data) for data in content.values()) > MAX_FILE:
        raise BuildError(
            "internal",
            "output_limit",
            "Generated output exceeds the supported build limit",
            "Report the oversized internal output",
        )
    return canonical(
        {
            "format_version": 1,
            "generator": {"name": "enrama", "version": version("enrama")},
            "schema_version": schema,
            "files": [
                {
                    "path": name,
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
                for name, data in sorted(content.items())
            ],
        }
    )


def verify_output(root: Path) -> tuple[bytes, tuple[str, ...]]:
    try:
        raw = files.read_source(root, Path(MANIFEST), MAX_MANIFEST)
        data = json.loads(raw, object_pairs_hook=_unique)
        if not isinstance(data, dict) or set(data) != {
            "format_version",
            "generator",
            "schema_version",
            "files",
        }:
            raise conflict()
        if (
            type(data["format_version"]) is not int
            or data["format_version"] != 1
            or type(data["schema_version"]) is not int
            or data["schema_version"] != 1
        ):
            raise conflict()
        generator = data["generator"]
        if (
            not isinstance(generator, dict)
            or set(generator) != {"name", "version"}
            or generator["name"] != "enrama"
            or not isinstance(generator["version"], str)
            or not generator["version"]
            or len(generator["version"]) > 100
        ):
            raise conflict()
        entries = data["files"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 255:
            raise conflict()
        names: set[str] = set()
        total = 0
        for item in entries:
            if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
                raise conflict()
            name = item["path"]
            size = item["size"]
            digest = item["sha256"]
            if (
                not isinstance(name, str)
                or not _ALLOWED.fullmatch(name)
                or name in names
            ):
                raise conflict()
            if (
                type(size) is not int
                or not 0 <= size <= MAX_FILE
                or not isinstance(digest, str)
                or not re.fullmatch("[0-9a-f]{64}", digest)
            ):
                raise conflict()
            total += size
            if total > MAX_FILE:
                raise conflict()
            names.add(name)
            content = files.read_source(root, Path(name), MAX_FILE)
            if len(content) != size or hashlib.sha256(content).hexdigest() != digest:
                raise conflict()
        if "index.html" not in names:
            raise conflict()
        actual, dirs = inventory(root)
        if actual != names | {MANIFEST} or dirs != parent_names(names):
            raise conflict()
        return raw, tuple(sorted(names))
    except BuildError:
        raise
    except (OSError, ValueError, TypeError, RecursionError):
        raise conflict() from None


def remove_owned(root: Path, expected: set[str]) -> None:
    """Remove only known paths in this invocation's real tree; refuse additions."""
    actual, dirs = inventory(root)
    if not actual <= expected or not dirs <= parent_names(expected):
        raise BuildError(
            "operational",
            "cleanup_conflict",
            "Temporary build data contains unexpected content",
            "Preserve .enrama/ and inspect the recoverable staging or backup manually",
        )
    for name in sorted(actual):
        with files.parent_directory(root, Path(name)) as (parent, path):
            files._regular(path.lstat())
            if parent is None:
                path.unlink()
            else:
                import os

                os.unlink(path.name, dir_fd=parent)
    for name in sorted(dirs, key=lambda n: len(PurePosixPath(n).parts), reverse=True):
        with files.parent_directory(root, Path(name)) as (parent, path):
            if parent is None:
                path.rmdir()
            else:
                import os

                os.rmdir(path.name, dir_fd=parent)
    root.rmdir()
