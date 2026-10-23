"""Stable public identifiers and presentation metadata; no SVG assets."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

PlatformName = Literal[
    "instagram",
    "facebook",
    "whatsapp",
    "youtube",
    "tiktok",
    "linkedin",
    "github",
    "x",
    "telegram",
]
LinkIcon = Literal[
    "link",
    "external-link",
    "message-circle",
    "mail",
    "phone",
    "shopping-bag",
    "calendar",
    "map-pin",
    "file-text",
    "download",
    "globe",
    "play",
]


@dataclass(frozen=True)
class PlatformPresentation:
    """Default accessible label and Bootstrap Icons asset identifier."""

    label: str
    icon: str


PLATFORMS = MappingProxyType(
    {
        "instagram": PlatformPresentation("Instagram", "instagram"),
        "facebook": PlatformPresentation("Facebook", "facebook"),
        "whatsapp": PlatformPresentation("WhatsApp", "whatsapp"),
        "youtube": PlatformPresentation("YouTube", "youtube"),
        "tiktok": PlatformPresentation("TikTok", "tiktok"),
        "linkedin": PlatformPresentation("LinkedIn", "linkedin"),
        "github": PlatformPresentation("GitHub", "github"),
        "x": PlatformPresentation("X", "twitter-x"),
        "telegram": PlatformPresentation("Telegram", "telegram"),
    }
)
