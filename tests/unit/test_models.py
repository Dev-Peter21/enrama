"""Public YAML v1 data behavior, without a YAML parser, renderer or client I/O."""

from __future__ import annotations

import importlib
import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from enrama.config import EnramaConfig

EXAMPLES = json.loads(
    (Path(__file__).parents[1] / "fixtures/configuration.json").read_text()
)
VALID: dict[str, dict[str, Any]] = {
    "EnramaConfig": EXAMPLES["minimal"],
    "SiteConfig": EXAMPLES["minimal"]["site"],
    "ProfileConfig": {"name": "Amapola"},
    "ThemeConfig": {},
    "LinkConfig": {"id": "catalog", "title": "Catalog", "url": "https://example.com"},
    "SocialConfig": {
        "id": "instagram",
        "platform": "instagram",
        "url": "https://example.com",
    },
}


def validate(name: str, data: object) -> BaseModel:
    module = importlib.import_module("enrama.config")
    model = cast(type[BaseModel], getattr(module, name))
    return model.model_validate(data)


def parse(data: object) -> EnramaConfig:
    from enrama.config import EnramaConfig

    return EnramaConfig.model_validate(data)


def test_minimal_input_has_exact_effective_defaults() -> None:
    assert parse(EXAMPLES["minimal"]).model_dump() == {
        "schema_version": 1,
        "site": {
            "title": "Amapola Deco",
            "description": "Flores, plantas y regalos",
            "language": "es-AR",
            "url": None,
            "favicon": None,
            "og_image": None,
        },
        "profile": {"name": "Amapola Deco", "bio": "", "avatar": None},
        "theme": {
            "name": "minimal",
            "primary_color": "#2563EB",
            "background_color": "#FFFFFF",
            "text_color": "#252525",
        },
        "links": [],
        "socials": [],
    }


def test_expanded_input_preserves_order_disabled_content_and_plain_text() -> None:
    original = deepcopy(EXAMPLES["expanded"])
    original["profile"]["bio"] = '<script>alert("test")</script>{{name}}'
    config = parse(original)
    assert [link.id for link in config.links] == [
        "contact-whatsapp",
        "catalog",
        "contact-email",
        "seasonal-offer",
    ]
    assert config.links[-1].enabled is False
    assert config.links[1].enabled is True
    assert config.links[2].icon is None
    assert config.profile.bio == '<script>alert("test")</script>{{name}}'
    assert [social.label for social in config.socials] == [
        "Instagram",
        "WhatsApp de Amapola",
    ]
    assert config.site.url == "https://example.com/amapola/"
    assert original["socials"][0].get("label") is None
    assert parse(config.model_dump()).model_dump() == config.model_dump()


def test_default_containers_are_not_shared_between_projects() -> None:
    first, second = parse(EXAMPLES["minimal"]), parse(EXAMPLES["minimal"])
    first.links.append(parse(EXAMPLES["expanded"]).links[0])
    first.theme.primary_color = "#000000"
    assert second.links == []
    assert second.theme.primary_color == "#2563EB"


@pytest.mark.parametrize("name", list(VALID))
def test_unknown_fields_are_forbidden_at_every_model_level(name: str) -> None:
    with pytest.raises(ValidationError) as error:
        validate(name, {**VALID[name], "unexpected": True})
    assert error.value.errors()[0]["loc"] == ("unexpected",)


@pytest.mark.parametrize(
    ("name", "field"),
    [("EnramaConfig", field) for field in ("schema_version", "site", "profile")]
    + [("SiteConfig", field) for field in ("title", "description", "language")]
    + [("ProfileConfig", "name")]
    + [("LinkConfig", field) for field in ("id", "title", "url")]
    + [("SocialConfig", field) for field in ("id", "platform", "url")],
)
def test_required_fields_cannot_be_omitted(name: str, field: str) -> None:
    data = {key: value for key, value in VALID[name].items() if key != field}
    with pytest.raises(ValidationError):
        validate(name, data)


@pytest.mark.parametrize(
    ("name", "field"),
    [
        ("SiteConfig", "url"),
        ("SiteConfig", "favicon"),
        ("SiteConfig", "og_image"),
        ("ProfileConfig", "avatar"),
        ("LinkConfig", "icon"),
    ],
)
def test_explicit_null_only_for_nullable_fields(name: str, field: str) -> None:
    assert validate(name, {**VALID[name], field: None}).model_dump()[field] is None


@pytest.mark.parametrize(
    ("name", "field"),
    [
        ("EnramaConfig", field)
        for field in ("schema_version", "site", "profile", "theme", "links", "socials")
    ]
    + [("SiteConfig", field) for field in ("title", "description", "language")]
    + [("ProfileConfig", field) for field in ("name", "bio")]
    + [
        ("ThemeConfig", field)
        for field in ("name", "primary_color", "background_color", "text_color")
    ]
    + [("LinkConfig", field) for field in ("id", "title", "url", "enabled")]
    + [
        ("SocialConfig", field)
        for field in ("id", "platform", "url", "label", "enabled")
    ],
)
def test_null_does_not_activate_nonnullable_defaults(name: str, field: str) -> None:
    with pytest.raises(ValidationError):
        validate(name, {**VALID[name], field: None})


@pytest.mark.parametrize("value", [True, False, "1", 1.0, 0, 2, -1])
def test_schema_version_is_exact_integer_one(value: object) -> None:
    with pytest.raises(ValidationError):
        parse({**EXAMPLES["minimal"], "schema_version": value})


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("SiteConfig", "title", 12),
        ("ProfileConfig", "name", b"Amapola"),
        ("LinkConfig", "enabled", "false"),
        ("LinkConfig", "enabled", 1),
        ("SocialConfig", "enabled", "true"),
        ("SocialConfig", "enabled", 0),
        ("EnramaConfig", "links", {}),
        ("EnramaConfig", "links", ()),
        ("EnramaConfig", "socials", ""),
        ("EnramaConfig", "site", []),
        ("ThemeConfig", "primary_color", 123456),
        ("SocialConfig", "label", 123),
        ("LinkConfig", "id", 1),
        ("SiteConfig", "language", b"es"),
        ("LinkConfig", "url", b"https://example.com"),
        ("ProfileConfig", "avatar", Path("assets/logo.png")),
    ],
)
def test_wrong_types_are_not_coerced(name: str, field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        validate(name, {**VALID[name], field: value})


@pytest.mark.parametrize(
    ("name", "field", "limit", "empty_allowed"),
    [
        ("SiteConfig", "title", 100, False),
        ("SiteConfig", "description", 300, False),
        ("ProfileConfig", "name", 100, False),
        ("ProfileConfig", "bio", 300, True),
        ("LinkConfig", "title", 100, False),
        ("SocialConfig", "label", 100, False),
    ],
)
def test_text_limits_are_unicode_characters_after_trimming(
    name: str, field: str, limit: int, empty_allowed: bool
) -> None:
    value = "á" * limit
    assert (
        validate(name, {**VALID[name], field: "  " + value + "\n"}).model_dump()[field]
        == value
    )
    with pytest.raises(ValidationError):
        validate(name, {**VALID[name], field: value + "a"})
    if empty_allowed:
        assert validate(name, {**VALID[name], field: " \t "}).model_dump()[field] == ""
    else:
        with pytest.raises(ValidationError):
            validate(name, {**VALID[name], field: " \t "})


@pytest.mark.parametrize("name", ["LinkConfig", "SocialConfig"])
@pytest.mark.parametrize("value", ["", "A", "a_1", "1a", "a b", " a", "a\n", "a" * 65])
def test_ids_use_exact_grammar(name: str, value: str) -> None:
    with pytest.raises(ValidationError):
        validate(name, {**VALID[name], "id": value})


@pytest.mark.parametrize("value", ["a", "a" * 64, "some-link-1"])
def test_id_boundaries_and_reordering_preserve_identity(value: str) -> None:
    data = deepcopy(EXAMPLES["expanded"])
    data["links"][0]["id"] = value
    data["links"].reverse()
    result = parse(data)
    assert result.links[-1].id == value


@pytest.mark.parametrize("collection", ["links", "socials", "cross"])
def test_duplicate_ids_include_disabled_entries_and_both_collections(
    collection: str,
) -> None:
    data = deepcopy(EXAMPLES["minimal"])
    link = {**VALID["LinkConfig"], "id": "shared", "enabled": False}
    social = {**VALID["SocialConfig"], "id": "shared"}
    if collection == "cross":
        data.update(links=[link], socials=[social])
    elif collection == "links":
        data["links"] = [link, link]
    else:
        data["socials"] = [social, {**social, "enabled": False}]
    with pytest.raises(ValidationError, match="unique"):
        parse(data)


@pytest.mark.parametrize(
    ("collection", "model", "limit"),
    [("links", "LinkConfig", 100), ("socials", "SocialConfig", 20)],
)
def test_collection_limits_count_disabled_entries(
    collection: str, model: str, limit: int
) -> None:
    entries = [
        {**VALID[model], "id": f"entry-{n}", "enabled": False} for n in range(limit)
    ]
    assert (
        len(
            parse({**EXAMPLES["minimal"], collection: entries}).model_dump()[collection]
        )
        == limit
    )
    with pytest.raises(ValidationError):
        parse(
            {
                **EXAMPLES["minimal"],
                collection: entries + [{**VALID[model], "id": "overflow"}],
            }
        )


@pytest.mark.parametrize("model", ["LinkConfig", "SocialConfig"])
def test_disabled_invalid_urls_still_fail_with_nested_field_location(
    model: str,
) -> None:
    collection = "links" if model == "LinkConfig" else "socials"
    with pytest.raises(ValidationError) as error:
        parse(
            {
                **EXAMPLES["minimal"],
                collection: [
                    {**VALID[model], "url": "javascript:alert(1)", "enabled": False}
                ],
            }
        )
    assert error.value.errors()[0]["loc"] == (collection, 0, "url")


@pytest.mark.parametrize("theme", [{}, {"name": "bold"}, {"primary_color": "#aBc123"}])
def test_partial_themes_share_defaults(theme: dict[str, str]) -> None:
    result = validate("ThemeConfig", theme).model_dump()
    assert result["name"] == theme.get("name", "minimal")
    assert result["primary_color"] == theme.get("primary_color", "#2563EB")
    assert result["background_color"] == "#FFFFFF"
    assert result["text_color"] == "#252525"


@pytest.mark.parametrize("field", ["primary_color", "background_color", "text_color"])
@pytest.mark.parametrize(
    "value",
    ["#fff", "#ffffffff", "red", "var(--primary)", " #FFFFFF", "#FFFFFF\n", "#GGGGGG"],
)
def test_colors_reject_css_shortcuts_alpha_and_whitespace(
    field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        validate("ThemeConfig", {field: value})


@pytest.mark.parametrize(
    ("platform", "label", "icon"),
    [
        ("instagram", "Instagram", "instagram"),
        ("facebook", "Facebook", "facebook"),
        ("whatsapp", "WhatsApp", "whatsapp"),
        ("youtube", "YouTube", "youtube"),
        ("tiktok", "TikTok", "tiktok"),
        ("linkedin", "LinkedIn", "linkedin"),
        ("github", "GitHub", "github"),
        ("x", "X", "twitter-x"),
        ("telegram", "Telegram", "telegram"),
    ],
)
def test_platform_derives_presentation_without_domain_binding(
    platform: str, label: str, icon: str
) -> None:
    from enrama.config import SocialConfig

    result = SocialConfig.model_validate(
        {
            "id": "social",
            "platform": platform,
            "url": "https://unrelated.example/path?x=1#profile",
        }
    )
    assert result.label == label
    assert result.icon == icon
    assert result.enabled is True
    custom = SocialConfig.model_validate(
        {**result.model_dump(), "label": " Contact us "}
    )
    assert custom.label == "Contact us"
    assert custom.icon == icon


@pytest.mark.parametrize(
    "icon",
    [
        None,
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
    ],
)
def test_all_general_icons_are_accepted(icon: str | None) -> None:
    assert (
        validate("LinkConfig", {**VALID["LinkConfig"], "icon": icon}).model_dump()[
            "icon"
        ]
        == icon
    )


@pytest.mark.parametrize(
    ("model", "field", "value"),
    [
        ("ThemeConfig", "name", "custom"),
        ("ThemeConfig", "name", "Minimal"),
        ("LinkConfig", "icon", "instagram"),
        ("LinkConfig", "icon", "Mail"),
        ("LinkConfig", "icon", "<svg/>"),
        ("LinkConfig", "icon", "./icon.svg"),
        ("SocialConfig", "platform", "Instagram"),
        ("SocialConfig", "platform", "other"),
        ("SocialConfig", "icon", "mail"),
    ],
)
def test_unknown_catalog_values_and_social_overrides_are_rejected(
    model: str, field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        validate(model, {**VALID[model], field: value})


@pytest.mark.parametrize("platform", [None, 1, "unknown"])
def test_invalid_platform_and_missing_label_are_validation_errors(
    platform: object,
) -> None:
    with pytest.raises(ValidationError):
        validate("SocialConfig", {**VALID["SocialConfig"], "platform": platform})


def test_site_and_image_validators_are_wired_without_reading_client_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    data = deepcopy(EXAMPLES["expanded"])
    data["site"]["language"] = "ES-ar"
    assert parse(data).site.language == "es-AR"
    assert list(tmp_path.iterdir()) == []
    for model, field in (
        ("SiteConfig", "favicon"),
        ("SiteConfig", "og_image"),
        ("ProfileConfig", "avatar"),
    ):
        with pytest.raises(ValidationError):
            validate(model, {**VALID[model], field: "../outside.png"})
    with pytest.raises(ValidationError):
        validate("SiteConfig", {**VALID["SiteConfig"], "language": "es-AB"})
    with pytest.raises(ValidationError):
        validate(
            "SiteConfig", {**VALID["SiteConfig"], "url": "https://example.com?query=1"}
        )
    with pytest.raises(ValidationError):
        validate("SocialConfig", {**VALID["SocialConfig"], "url": "http://example.com"})


@pytest.mark.parametrize(
    ("model", "field"),
    [
        ("ProfileConfig", "avatar"),
        ("SiteConfig", "favicon"),
        ("SiteConfig", "og_image"),
    ],
)
@pytest.mark.parametrize(
    "value", ["dist./logo.png", "./DiSt./logo.png", "dist.\\logo.png"]
)
def test_windows_output_directory_alias_is_rejected_in_every_asset_field(
    model: str, field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        validate(model, {**VALID[model], field: value})
