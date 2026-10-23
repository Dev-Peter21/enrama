"""Validate the generated client artifact and its explicit runtime boundaries."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from enrama.config import EnramaConfig, parse_config

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads(
    (ROOT / "tests/fixtures/configuration.json").read_text(encoding="utf-8")
)


def generated() -> bytes:
    from enrama.config.schema import generate_schema

    return generate_schema()


@pytest.fixture
def validator() -> Draft202012Validator:
    schema = json.loads(generated())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def changed(path: tuple[str | int, ...], value: object) -> dict[str, Any]:
    data: dict[str, Any] = deepcopy(EXAMPLES["expanded"])
    parent: Any = data
    for part in path[:-1]:
        parent = parent[part]
    parent[path[-1]] = value
    return data


def test_checked_artifact_matches_deterministic_generation() -> None:
    first = generated()
    assert first == generated()
    assert (ROOT / "schemas/enrama-v1.schema.json").read_bytes() == first
    assert first.endswith(b"\n")
    assert first.decode("utf-8")
    assert (
        json.loads(first)["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    )


def test_references_are_self_contained() -> None:
    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "$ref":
                    assert isinstance(child, str) and child.startswith("#/")
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(json.loads(generated()))


@pytest.mark.parametrize("example", ["minimal", "expanded"])
def test_examples_validate_without_default_insertion(
    example: str, validator: Draft202012Validator
) -> None:
    data = deepcopy(EXAMPLES[example])
    before = deepcopy(data)
    validator.validate(data)
    assert data == before
    EnramaConfig.model_validate(data)


@pytest.mark.parametrize(
    "path",
    [
        ("schema_version",),
        ("site",),
        ("profile",),
        ("site", "title"),
        ("site", "description"),
        ("site", "language"),
        ("profile", "name"),
    ],
)
def test_missing_required_fields_are_rejected(
    path: tuple[str, ...], validator: Draft202012Validator
) -> None:
    data = deepcopy(EXAMPLES["minimal"])
    parent = data
    for part in path[:-1]:
        parent = parent[part]
    del parent[path[-1]]
    assert not validator.is_valid(data)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), "1"),
        (("schema_version",), True),
        (("schema_version",), 0),
        (("schema_version",), 2),
        (("site", "title"), None),
        (("site", "title"), ""),
        (("site", "title"), "x" * 101),
        (("site", "title"), 42),
        (("site", "description"), "x" * 301),
        (("profile", "bio"), "x" * 301),
        (("profile", "bio"), None),
        (("theme",), None),
        (("theme", "name"), "unknown"),
        (("theme", "primary_color"), "#fff"),
        (("theme", "primary_color"), "#12345678"),
        (("links", 0, "id"), "BAD"),
        (("links", 0, "id"), "x" * 65),
        (("links", 0, "enabled"), "true"),
        (("links", 0, "enabled"), 1),
        (("links", 0, "icon"), "unknown"),
        (("socials", 0, "platform"), "unknown"),
        (("socials", 0, "label"), None),
        (("socials", 0, "icon"), "github"),
        (("links",), None),
        (("socials",), {}),
        (("unknown",), "value"),
        (("site", "unknown"), "value"),
    ],
)
def test_structural_errors_are_rejected(
    path: tuple[str | int, ...], value: object, validator: Draft202012Validator
) -> None:
    assert not validator.is_valid(changed(path, value))


@pytest.mark.parametrize(
    "path",
    [
        ("site", "url"),
        ("site", "favicon"),
        ("site", "og_image"),
        ("profile", "avatar"),
        ("links", 0, "icon"),
    ],
)
def test_nullable_fields_accept_null(
    path: tuple[str | int, ...], validator: Draft202012Validator
) -> None:
    data = changed(path, None)
    validator.validate(data)
    EnramaConfig.model_validate(data)


@pytest.mark.parametrize(("collection", "limit"), [("links", 100), ("socials", 20)])
def test_collection_boundaries(
    collection: str, limit: int, validator: Draft202012Validator
) -> None:
    entry = EXAMPLES["expanded"][collection][0]
    assert validator.is_valid(changed((collection,), [entry] * limit))
    assert not validator.is_valid(changed((collection,), [entry] * (limit + 1)))


def test_hover_metadata_and_dynamic_defaults_are_honest() -> None:
    definitions = json.loads(generated())["$defs"]
    assert "metadata" in definitions["SiteConfig"]["description"].lower()
    social = definitions["SocialConfig"]
    assert "label" not in social["required"]
    assert "default" not in social["properties"]["label"]
    assert "icon" not in social["properties"]
    assert definitions["LinkConfig"]["properties"]["enabled"]["default"] is True


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("links", 0, "url"), "javascript:alert(1)"),
        (("site", "language"), "unknown-language"),
        (("profile", "avatar"), "../outside.png"),
        (("socials", 0, "id"), "contact-whatsapp"),
        (("site", "title"), "   "),
        (("schema_version",), 1.0),
    ],
)
def test_schema_acceptance_is_not_full_runtime_validation(
    path: tuple[str | int, ...], value: object, validator: Draft202012Validator
) -> None:
    data = changed(path, value)
    assert validator.is_valid(data)
    with pytest.raises(ValidationError):
        EnramaConfig.model_validate(data)


def test_schema_length_applies_before_runtime_trimming(
    validator: Draft202012Validator,
) -> None:
    data = changed(("site", "title"), " " + "x" * 100 + " ")
    assert not validator.is_valid(data)
    assert len(EnramaConfig.model_validate(data).site.title) == 100


def test_yaml_loader_stays_authoritative_for_scalar_spellings(
    validator: Draft202012Validator,
) -> None:
    # C02 leaves YAML 1.1 boolean spellings as strings.
    data = changed(("links", 0, "enabled"), "yes")
    assert not validator.is_valid(data)
    content = b"schema_version: 1\nsite: {title: on, description: yes, language: en}\nprofile: {name: off}\n"
    assert parse_config(content).site.title == "on"


def test_generation_has_no_output_or_client_file_access(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from enrama.config.schema import generate_schema

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Generation attempted client file I/O")

    monkeypatch.setattr("builtins.open", forbidden)
    assert generate_schema()
    assert capsys.readouterr() == ("", "")
