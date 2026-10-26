"""Project-local advisory ownership and a read-only validation entry point."""

import os
import sys
from pathlib import Path
from types import TracebackType

from enrama.config import EnramaConfig, load_config

from . import _asset_files as files
from ._build_errors import BuildError
from ._manifest import canonical
from .assets import prepare_assets

_MARKER = canonical({"format_version": 1, "generator": "enrama"})


def source_path(source: str | Path) -> Path:
    selected = Path(os.path.abspath(source))
    try:
        root = selected.parent.resolve(strict=True)
    except FileNotFoundError:
        raise BuildError(
            "invalid_input",
            "missing_source",
            "The configuration directory does not exist",
            "Select an existing client configuration",
        ) from None
    except OSError:
        raise BuildError(
            "operational",
            "source_access",
            "The client directory is unavailable",
            "Check directory permissions",
        ) from None
    # Never interpret an output/working directory as a fresh client root.
    if any(
        p.name.rstrip(". ").casefold() in {"dist", ".enrama"}
        for p in (root, *root.parents)
    ):
        raise BuildError(
            "invalid_input",
            "reserved_source",
            "Configuration cannot come from output or internal working locations",
            "Select the client source YAML outside dist/ and .enrama/",
        )
    try:
        if files._linked(selected.lstat()):
            raise BuildError(
                "invalid_input",
                "unsafe_source",
                "The selected configuration is a link",
                "Select a regular source YAML file",
            )
    except FileNotFoundError:
        pass  # C02 supplies its missing-file diagnostic.
    except OSError:
        raise BuildError(
            "operational",
            "source_access",
            "The configuration cannot be inspected",
            "Check file and directory permissions",
        ) from None
    return root / selected.name


def validate_project(source: str | Path = "enrama.yaml") -> EnramaConfig:
    selected = source_path(source)
    config = load_config(selected)
    prepare_assets(config, source=selected, reserved_paths=(Path(".enrama"),))
    return config


class ProjectSession:
    """Nonblocking ownership, reusable for a full foreground preview lifetime."""

    def __init__(self, source: str | Path = "enrama.yaml") -> None:
        self.source = source_path(source)
        self.root = self.source.parent
        self.work = self.root / ".enrama"
        self.fd: int | None = None
        self.active = False
        self.identity: tuple[int, int] | None = None

    def check(self) -> None:
        info = self.work.lstat()
        files._directory(info)
        if self.identity != (info.st_dev, info.st_ino):
            raise BuildError(
                "operational",
                "workspace_changed",
                "The internal working directory changed",
                "Preserve .enrama/ and inspect it before retrying",
            )

    def __enter__(self) -> "ProjectSession":
        try:
            try:
                self.work.mkdir(mode=0o700)
            except FileExistsError:
                files._directory(self.work.lstat())
                if (
                    files.read_source(self.work, Path("workspace.json"), 1024)
                    != _MARKER
                ):
                    raise OSError("Unrecognized workspace") from None
            else:
                with (self.work / "workspace.json").open("xb") as f:
                    f.write(_MARKER)
                with (self.work / "guard").open("xb") as f:
                    f.write(b"\0")
            info = self.work.lstat()
            self.identity = (info.st_dev, info.st_ino)
            self.check()
            before = (self.work / "guard").lstat()
            files._regular(before)
            if before.st_size != 1:
                raise OSError("Invalid guard")
            self.fd = os.open(
                self.work / "guard",
                os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
            )
            files._same(before, os.fstat(self.fd))
            try:
                if sys.platform == "win32":
                    import msvcrt

                    os.lseek(self.fd, 0, os.SEEK_SET)
                    msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise BuildError(
                    "operational",
                    "project_busy",
                    "Another build or preview owns this project",
                    "Stop the active operation before retrying",
                ) from None
            self.active = True
            entries = {p.name for p in self.work.iterdir()}
            if entries - {"workspace.json", "guard"}:
                raise BuildError(
                    "operational",
                    "incomplete_operation",
                    "The internal workspace contains an incomplete or unrecognized operation",
                    "Preserve .enrama/staging, .enrama/backup and transaction.json; inspect or move them manually before retrying",
                )
            return self
        except BaseException as error:
            self.close()
            if isinstance(error, OSError):
                raise BuildError(
                    "operational",
                    "workspace_conflict",
                    "The internal workspace is unavailable or unrecognized",
                    "Preserve .enrama/ and inspect its contents and permissions",
                ) from None
            raise

    def close(self) -> None:
        if self.fd is not None:
            # Closing the descriptor releases an advisory OS lock. Never unlink
            # the guard inode while another process could be opening it.
            os.close(self.fd)
            self.fd = None
        self.active = False

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
