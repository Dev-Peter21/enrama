"""Render a complete shared HTML document; no client I/O or output lifecycle."""

from importlib import resources

from jinja2 import Environment, FunctionLoader, StrictUndefined, TemplateError

from enrama.config import EnramaConfig
from enrama.themes import icon_svg, theme_view

from ._render_context import image_paths
from ._render_errors import RenderError
from .assets import PreparedAssets

_BASE_TEMPLATE = "base.html"


def _load_template(name: str) -> str | None:
    # A fixed package resource prevents cwd/client/environment template discovery.
    # Unlike a loader that translates every OSError into TemplateNotFound, retain
    # real read failures so callers can distinguish operational I/O from defects.
    if name != _BASE_TEMPLATE:
        return None
    try:
        return (
            resources.files("enrama")
            .joinpath("_templates", name)
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return None


def _context(config: EnramaConfig, prepared: PreparedAssets) -> dict[str, object]:
    paths = image_paths(config, prepared)
    view = theme_view(config.theme)
    public_url = config.site.url
    if public_url is not None and not public_url.endswith("/"):
        public_url += "/"
    og_path = paths.get("site.og_image")
    return {
        "theme": config.theme.name,
        "stylesheet": view.stylesheet,
        "primary": view.primary,
        "background": view.background,
        "text": view.text,
        "on_primary": view.on_primary,
        "focus": view.focus,
        "title": str(config.site.title),
        "description": str(config.site.description),
        "language": str(config.site.language),
        "name": str(config.profile.name),
        "bio": str(config.profile.bio),
        "avatar": paths.get("profile.avatar"),
        "favicon": paths.get("site.favicon"),
        "public_url": public_url,
        "og_image": public_url + og_path if public_url and og_path else None,
        "links": tuple(
            {
                "title": str(link.title),
                "url": str(link.url),
                "icon": icon_svg(link.icon),
            }
            for link in config.links
            if link.enabled
        ),
        "socials": tuple(
            {
                "label": str(social.label),
                "url": str(social.url),
                "icon": icon_svg(social.icon, social=True),
            }
            for social in config.socials
            if social.enabled
        ),
    }


def render_html(config: EnramaConfig, prepared: PreparedAssets) -> str:
    """Return shared semantic HTML or raise RenderError; interrupts propagate.

    Both accepted theme names use this unstyled base. The caller must pair C01
    validation with matching G01 preparation and owns eventual filesystem output.
    """
    try:
        context = _context(config, prepared)
        environment = Environment(
            loader=FunctionLoader(_load_template),
            autoescape=True,
            undefined=StrictUndefined,
            newline_sequence="\n",
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            auto_reload=False,
        )
        html = environment.get_template(_BASE_TEMPLATE).render(context)
        # Jinja normalizes template source, not newlines interpolated from text.
        return html.replace("\r\n", "\n").replace("\r", "\n")
    except RenderError:
        raise
    except (TemplateError, UnicodeError):
        raise RenderError(
            "internal",
            "template_error",
            "The packaged HTML template could not be rendered",
            "Check the installed Enrama templates and report the package defect",
            template=_BASE_TEMPLATE,
        ) from None
    except OSError:
        raise RenderError(
            "operational",
            "resource_error",
            "The packaged HTML template could not be read",
            "Check access to the installed Enrama package and retry",
            template=_BASE_TEMPLATE,
        ) from None
    except Exception:
        raise RenderError(
            "internal",
            "internal_error",
            "An internal rendering error occurred",
            "Report the error with the installed Enrama version",
            template=_BASE_TEMPLATE,
        ) from None
