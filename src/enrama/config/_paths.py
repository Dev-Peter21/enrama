"""Portable lexical asset checks; existence and symlink checks belong to G01."""

import re
from pathlib import PurePosixPath, PureWindowsPath


def validate_asset_path(value: str) -> str:
    """Accept a local relative reference without reading or expanding it."""
    windows = PureWindowsPath(value)
    portable = value.replace("\\", "/")
    parts = PurePosixPath(portable).parts
    if (
        not value
        or "\x00" in value
        or windows.drive
        or windows.root
        or portable.startswith("/")
        or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", value)
        or ".." in parts
        or (parts and parts[0].casefold() == "dist")
    ):
        raise ValueError("Use a local relative asset path outside dist/, without '..'")
    return value
