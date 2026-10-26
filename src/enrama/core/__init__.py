"""Reusable asset and HTML services, independent of application interfaces."""

from ._build_errors import BuildError
from ._project import ProjectSession, validate_project
from ._render_errors import RenderError
from .assets import (
    AssetBinding,
    AssetDiagnostic,
    AssetEnvironmentError,
    AssetError,
    PreparedAsset,
    PreparedAssets,
    copy_assets,
    prepare_assets,
)
from .builder import BuildResult, build_site
from .renderer import render_html

__all__ = [
    "AssetBinding",
    "AssetDiagnostic",
    "AssetEnvironmentError",
    "AssetError",
    "PreparedAsset",
    "PreparedAssets",
    "prepare_assets",
    "copy_assets",
    "RenderError",
    "render_html",
    "BuildError",
    "BuildResult",
    "ProjectSession",
    "build_site",
    "validate_project",
]
