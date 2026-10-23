"""Version-1 models and safe configuration loading, independent of rendering."""

from .diagnostics import (
    ConfigurationError,
    Diagnostic,
    SourcePosition,
    format_diagnostic,
)
from .loader import load_config, parse_config
from .models import (
    EnramaConfig,
    LinkConfig,
    ProfileConfig,
    SiteConfig,
    SocialConfig,
    ThemeConfig,
)

__all__ = [
    "ConfigurationError",
    "Diagnostic",
    "SourcePosition",
    "format_diagnostic",
    "load_config",
    "parse_config",
    "EnramaConfig",
    "LinkConfig",
    "ProfileConfig",
    "SiteConfig",
    "SocialConfig",
    "ThemeConfig",
]
