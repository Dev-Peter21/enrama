"""Strict data models for YAML v1; no loading, rendering, or client file access."""

from itertools import chain
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from ._language import validate_language
from ._paths import validate_asset_path
from ._urls import validate_https_url, validate_link_url, validate_site_url
from .catalogs import PLATFORMS, LinkIcon, PlatformName

ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)
]
Bio = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
EntryId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,63}$")]
Color = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]
LanguageTag = Annotated[str, AfterValidator(validate_language)]
AssetPath = Annotated[str, AfterValidator(validate_asset_path)]
LinkUrl = Annotated[str, AfterValidator(validate_link_url)]
HttpsUrl = Annotated[str, AfterValidator(validate_https_url)]
SiteUrl = Annotated[str, AfterValidator(validate_site_url)]


class _ConfigModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_default=True)


class SiteConfig(_ConfigModel):
    """Document metadata; a public base URL is optional for local work."""

    title: ShortText
    description: Description
    language: LanguageTag
    url: SiteUrl | None = None
    favicon: AssetPath | None = None
    og_image: AssetPath | None = None


class ProfileConfig(_ConfigModel):
    """Plain-text profile and optional client-local avatar."""

    name: ShortText
    bio: Bio = ""
    avatar: AssetPath | None = None


class ThemeConfig(_ConfigModel):
    """Both built-in themes share these color defaults."""

    name: Literal["minimal", "bold"] = "minimal"
    primary_color: Color = "#2563EB"
    background_color: Color = "#FFFFFF"
    text_color: Color = "#252525"


class LinkConfig(_ConfigModel):
    """Ordered call to action; disabled content remains fully validated."""

    id: EntryId
    title: ShortText
    url: LinkUrl
    icon: LinkIcon | None = None
    enabled: bool = True


def _social_label(data: dict[str, Any]) -> str:
    # Pydantic invokes a validated-data factory only after preceding fields pass.
    return PLATFORMS[data["platform"]].label


class SocialConfig(_ConfigModel):
    """Platform presentation is independent of the HTTPS destination domain."""

    id: EntryId
    platform: PlatformName
    url: HttpsUrl
    label: ShortText = Field(default_factory=_social_label)
    enabled: bool = True

    @property
    def icon(self) -> str:
        """Trusted catalog identifier; never a field accepting a YAML override."""
        return PLATFORMS[self.platform].icon


class EnramaConfig(_ConfigModel):
    """Version-1 configuration with stable IDs shared by both collections."""

    schema_version: Annotated[int, Field(ge=1, le=1)]
    site: SiteConfig
    profile: ProfileConfig
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    links: list[LinkConfig] = Field(default_factory=list, max_length=100)
    socials: list[SocialConfig] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def unique_entry_ids(self) -> Self:
        seen: set[str] = set()
        for entry in chain[LinkConfig | SocialConfig](self.links, self.socials):
            if entry.id in seen:
                raise ValueError(
                    f"IDs must be unique across links and socials: {entry.id}"
                )
            seen.add(entry.id)
        return self
