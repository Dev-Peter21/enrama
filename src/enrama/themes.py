"""Trusted local presentation resources and accessible derived color tokens."""

import hashlib
from dataclasses import dataclass
from importlib import resources
from typing import get_args
from xml.etree import ElementTree as ET

from markupsafe import Markup

from enrama.config import ThemeConfig
from enrama.config.catalogs import PLATFORMS, LinkIcon


@dataclass(frozen=True)
class ThemeView:
    stylesheet: str
    assets: dict[str, bytes]
    primary: str
    background: str
    text: str
    on_primary: str
    focus: str
    warnings: tuple[str, ...]


def _read(directory: str, name: str) -> str:
    # Delay the core error import so the presentation API can be imported alone.
    from enrama.core._render_errors import RenderError

    try:
        return (
            resources.files("enrama")
            .joinpath(directory, name)
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        raise RenderError(
            "internal",
            "template_error",
            "A packaged presentation resource is missing",
            "Reinstall Enrama or report the incomplete package",
            template=name,
        ) from None
    except OSError:
        raise RenderError(
            "operational",
            "resource_error",
            "A packaged presentation resource could not be read",
            "Check access to the installed package",
            template=name,
        ) from None


def contrast(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        parts = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [
            p / 12.92 if p <= 0.04045 else ((p + 0.055) / 1.055) ** 2.4 for p in parts
        ]
        return sum(
            p * factor
            for p, factor in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
        )

    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _foreground(background: str) -> str:
    return max(("#000000", "#FFFFFF"), key=lambda color: contrast(color, background))


def theme_view(config: ThemeConfig) -> ThemeView:
    css = _read("_themes", config.name + ".css").encode("utf-8")
    path = "assets/theme/" + hashlib.sha256(css).hexdigest() + ".css"
    notices = _read("_themes", "THIRD_PARTY_NOTICES.txt").encode("utf-8")
    text = config.text_color
    warnings: tuple[str, ...] = ()
    if contrast(text, config.background_color) < 4.5:
        text = _foreground(config.background_color)
        warnings = (
            "Configured text/background contrast is below 4.5:1; an accessible derived text color is used. YAML is unchanged.",
        )
    on_primary = (
        config.text_color
        if contrast(config.text_color, config.primary_color) >= 4.5
        else _foreground(config.primary_color)
    )
    focus = (
        config.primary_color
        if contrast(config.primary_color, config.background_color) >= 3
        else text
    )
    return ThemeView(
        path,
        {path: css, "assets/theme/THIRD_PARTY_NOTICES.txt": notices},
        config.primary_color,
        config.background_color,
        text,
        on_primary,
        focus,
        warnings,
    )


def icon_svg(name: str | None, *, social: bool = False) -> Markup:
    if name is None:
        return Markup("")
    allowed = (
        {item.icon for item in PLATFORMS.values()}
        if social
        else set(get_args(LinkIcon))
    )
    if name not in allowed:
        raise ValueError("Icon is outside the controlled catalog")
    kind = "bootstrap" if social else "lucide"
    element = ET.fromstring(_read("_icons", kind + "-" + name + ".svg"))
    for child in element.iter():
        child.text = None
        child.tail = None
    element.set("aria-hidden", "true")
    element.set("focusable", "false")
    element.set("width", "24")
    element.set("height", "24")
    element.set("class", "icon")
    if social:
        element.set("fill", "currentColor")
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    # Only immutable, packaged catalog SVGs enter Markup. YAML never does.
    return Markup(ET.tostring(element, encoding="unicode"))
