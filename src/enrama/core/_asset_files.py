"""Confined regular-file snapshots; no image policy, publication or cleanup."""

import errno
import os
import stat
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path


class UnsafePathError(OSError):
    """An internal link, nonregular object or changed path was encountered."""


class FileLimitError(ValueError):
    """A bounded read found more bytes than permitted."""


def _linked(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_reparse_tag", 0))


def _directory(info: os.stat_result) -> None:
    if _linked(info) or not stat.S_ISDIR(info.st_mode):
        raise UnsafePathError("Expected a real directory")


def _regular(info: os.stat_result) -> None:
    if _linked(info) or not stat.S_ISREG(info.st_mode):
        raise UnsafePathError("Expected a regular file")


def _same(first: os.stat_result, second: os.stat_result) -> None:
    if (first.st_dev, first.st_ino) != (second.st_dev, second.st_ino):
        raise UnsafePathError("File identity changed")


def _stat(parent: int | None, path: Path) -> os.stat_result:
    if parent is not None:
        return os.stat(path.name, dir_fd=parent, follow_symlinks=False)
    return path.lstat()


@contextmanager
def parent_directory(
    root: Path, relative: Path, *, create: bool = False
) -> Iterator[tuple[int | None, Path]]:
    """Walk each internal component; anchor POSIX operations to directory fds."""
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise UnsafePathError("Expected a contained relative path")
    anchored = os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    checks: list[tuple[Path, os.stat_result]] = []
    with ExitStack() as stack:
        root_info = root.lstat()
        _directory(root_info)
        descriptor: int | None = None
        if anchored:
            descriptor = os.open(root, flags)
            stack.callback(os.close, descriptor)
            _same(root_info, os.fstat(descriptor))
        else:
            checks.append((root, root_info))
        current = root
        for component in relative.parts[:-1]:
            current = current / component
            try:
                info = _stat(descriptor, current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    if descriptor is None:
                        current.mkdir()
                    else:
                        os.mkdir(component, dir_fd=descriptor)
                except FileExistsError:
                    pass
                info = _stat(descriptor, current)
            _directory(info)
            if anchored:
                assert descriptor is not None
                descriptor = os.open(component, flags, dir_fd=descriptor)
                stack.callback(os.close, descriptor)
                _same(info, os.fstat(descriptor))
            else:
                checks.append((current, info))
        yield descriptor, root / relative
        # On Windows, reject reparse/identity changes around full-path opens.
        # This is not an adversarial-filesystem sandbox or a locking protocol.
        for directory, before in checks:
            after = directory.lstat()
            _directory(after)
            _same(before, after)


def read_source(root: Path, relative: Path, limit: int) -> bytes:
    """Read at most limit+1 bytes, without following internal source links."""
    try:
        with parent_directory(root, relative) as (parent, path):
            before = _stat(parent, path)
            _regular(before)
            flags = (
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_BINARY", 0)
            )
            descriptor = os.open(
                path if parent is None else path.name, flags, dir_fd=parent
            )
            try:
                opened = os.fstat(descriptor)
                _regular(opened)
                _same(before, opened)
                chunks: list[bytes] = []
                remaining = limit + 1
                while remaining:
                    chunk = os.read(descriptor, min(65536, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                data = b"".join(chunks)
                after = _stat(parent, path)
                _regular(after)
                _same(opened, after)
            finally:
                os.close(descriptor)
            if len(data) > limit:
                raise FileLimitError("Image exceeds byte limit")
            return data
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise UnsafePathError("Unsafe path component") from None
        raise


class DestinationConflictError(UnsafePathError):
    """An existing staging object cannot be replaced or safely reused."""


def write_snapshot(root: Path, relative: Path, data: bytes) -> None:
    """Create exclusively or verify identical bytes; never truncate a target."""
    try:
        with parent_directory(root, relative, create=True) as (parent, path):
            try:
                info = _stat(parent, path)
            except FileNotFoundError:
                info = None
            if info is not None:
                _regular(info)
                try:
                    current = read_source(root, relative, len(data))
                except FileLimitError:
                    raise DestinationConflictError("Existing content differs") from None
                if current != data:
                    raise DestinationConflictError("Existing content differs")
                return
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_BINARY", 0)
            )
            descriptor = os.open(
                path if parent is None else path.name, flags, 0o644, dir_fd=parent
            )
            try:
                opened = os.fstat(descriptor)
                _regular(opened)
                remaining = memoryview(data)
                while remaining:
                    written = os.write(descriptor, remaining)
                    if written <= 0:
                        raise OSError("Image write made no progress")
                    remaining = remaining[written:]
                after = _stat(parent, path)
                _regular(after)
                _same(opened, after)
            finally:
                os.close(descriptor)
    except FileExistsError:
        raise DestinationConflictError("Staging target appeared concurrently") from None
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise DestinationConflictError("Unsafe staging component") from None
        raise
