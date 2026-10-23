"""Exercise safe YAML-to-model diagnostics through the public loader API."""

import json
from pathlib import Path

import pytest

from enrama.config import EnramaConfig
from enrama.config.diagnostics import ConfigurationError, Diagnostic, SourcePosition

MINIMAL = b"""schema_version: 1
site:
  title: Amapola Deco
  description: Flores, plantas y regalos
  language: es-AR
profile:
  name: Amapola Deco
"""


def parse(content: bytes, source: str = "enrama.yaml") -> EnramaConfig:
    from enrama.config import parse_config

    return parse_config(content, source=source)


def failure(content: bytes, source: str = "enrama.yaml") -> ConfigurationError:
    with pytest.raises(ConfigurationError) as caught:
        parse(content, source)
    return caught.value


@pytest.mark.parametrize("default_encoding", ["utf-8", "cp1252"])
def test_documented_examples_match_independent_model_fixtures(
    default_encoding: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_read = Path.read_text

    def locale_read(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        return original_read(path, encoding=encoding or default_encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", locale_read)
    fixtures = json.loads(
        (Path(__file__).parents[1] / "fixtures/configuration.json").read_text(
            encoding="utf-8"
        )
    )
    minimal = parse(MINIMAL)
    assert minimal == EnramaConfig.model_validate(fixtures["minimal"])
    # The expanded example is supplied as YAML, not through JSON coercion.
    expanded = (Path(__file__).parents[1] / "fixtures/expanded.yaml").read_bytes()
    assert parse(expanded) == EnramaConfig.model_validate(fixtures["expanded"])
    assert minimal.site.url is None
    assert minimal.links == []


@pytest.mark.parametrize(
    ("extra", "location", "hint"),
    [
        (b"schema_version: 2\n", ("schema_version",), "1"),
        (b"schema_version: true\n", ("schema_version",), "integer"),
        (b"schema_version: '1'\n", ("schema_version",), "integer"),
        (b"theme: null\n", ("theme",), "mapping"),
        (b"theme: {name: secret-theme}\n", ("theme", "name"), "minimal"),
        (
            b"theme: {primary_color: secret-color}\n",
            ("theme", "primary_color"),
            "#RRGGBB",
        ),
        (b"profile: {name: 123}\n", ("profile", "name"), "text"),
        (b"profile: {name: ''}\n", ("profile", "name"), "empty"),
        (
            b"profile: {name: Secret, avatar: '../secret'}\n",
            ("profile", "avatar"),
            "relative",
        ),
        (
            b"links: [{id: BAD, title: OK, url: 'https://example.com'}]\n",
            ("links", 0, "id"),
            "lowercase",
        ),
        (
            b"links: [{id: ok, title: OK, url: 'javascript:secret'}]\n",
            ("links", 0, "url"),
            "mailto",
        ),
        (
            b"links: [{id: ok, title: OK, url: 'http://example.com/%ZZ'}]\n",
            ("links", 0, "url"),
            "URL",
        ),
        (
            b"links: [{id: ok, title: OK, url: 'https://example.com', icon: secret}]\n",
            ("links", 0, "icon"),
            "catalog",
        ),
        (
            b"links: [{id: ok, title: OK, url: 'https://example.com', enabled: 'true'}]\n",
            ("links", 0, "enabled"),
            "true or false",
        ),
        (
            b"socials: [{id: ok, platform: github, url: 'http://example.com'}]\n",
            ("socials", 0, "url"),
            "HTTPS",
        ),
        (
            b"socials: [{id: ok, platform: secret-platform, url: 'https://example.com'}]\n",
            ("socials", 0, "platform"),
            "platform",
        ),
        (b"links: null\n", ("links",), "list"),
        (b"secret_field: secret-value\n", ("secret_field",), "Remove"),
        (
            b"site: {title: OK, description: OK, language: secret}\n",
            ("site", "language"),
            "BCP 47",
        ),
        (
            b"site: {title: OK, description: OK, language: en, url: 'http://secret'}\n",
            ("site", "url"),
            "HTTPS",
        ),
    ],
)
def test_c01_failures_have_actionable_static_hints(
    extra: bytes, location: tuple[str | int, ...], hint: str
) -> None:
    # Replace an existing top-level field instead of triggering duplicate-key policy.
    key = extra.split(b":", 1)[0] + b":"
    lines = MINIMAL.splitlines(keepends=True)
    kept: list[bytes] = []
    skip = False
    for line in lines:
        if not line.startswith(b" "):
            skip = line.startswith(key)
        if not skip:
            kept.append(line)
    error = failure(b"".join(kept) + extra)
    diagnostic = next(d for d in error.diagnostics if d.location == location)
    assert diagnostic.category == "model_validation"
    assert hint.lower() in diagnostic.hint.lower()
    assert diagnostic.position is not None
    assert "secret-value" not in str(error)
    assert "secret-platform" not in str(error)
    assert "javascript:secret" not in repr(error)


def test_value_marks_distinguish_repeated_values() -> None:
    error = failure(
        MINIMAL
        + b"""links:
  - id: first
    title: Same
    url: javascript:secret
  - id: second
    title: Same
    url: javascript:secret
"""
    )
    assert [d.location for d in error.diagnostics] == [
        ("links", 0, "url"),
        ("links", 1, "url"),
    ]
    assert [d.position for d in error.diagnostics] == [
        SourcePosition(11, 10),
        SourcePosition(14, 10),
    ]
    assert all(not d.parent for d in error.diagnostics)
    assert "secret" not in str(error)


def test_missing_fields_use_nearest_container_and_parent_annotation() -> None:
    error = failure(b"schema_version: 1\nsite: {}\nprofile: {}\n")
    assert error.total_count == 4
    assert error.diagnostics[0].location == ("site", "description")
    assert error.diagnostics[0].position == SourcePosition(2, 7)
    assert all(d.parent for d in error.diagnostics)
    assert "parent" in str(error)
    root = failure(b"{}")
    assert all(
        d.position == SourcePosition(1, 1) and d.parent for d in root.diagnostics
    )


def test_global_unique_ids_remain_honestly_unlocated() -> None:
    error = failure(
        MINIMAL
        + b"""links:
  - {id: secret-id, title: First, url: 'https://example.com'}
socials:
  - {id: secret-id, platform: github, url: 'https://example.com'}
"""
    )
    (diagnostic,) = error.diagnostics
    assert diagnostic.location == ()
    assert diagnostic.position is None
    assert "unique" in diagnostic.message
    assert "secret-id" not in str(error)
    assert " — $" in str(error)


@pytest.mark.parametrize("count", [20, 21, 27])
def test_diagnostic_cap_counts_all_primary_errors_in_source_order(count: int) -> None:
    extra = b"".join(f"unknown_{i}: SECRET-{i}\n".encode() for i in range(count))
    error = failure(MINIMAL + extra)
    assert error.total_count == count
    assert error.omitted_count == count - 20
    assert [d.location for d in error.diagnostics] == [
        (f"unknown_{i}",) for i in range(20)
    ]
    assert "SECRET" not in str(error)
    assert ("Showing 20 of" in str(error)) == (count > 20)


def test_dependent_default_bookkeeping_is_not_counted() -> None:
    error = failure(
        MINIMAL
        + b"socials: [{id: ok, platform: invalid, url: 'https://example.com'}]\n"
    )
    assert error.total_count == 1
    assert error.diagnostics[0].location == ("socials", 0, "platform")
    assert "factory" not in str(error)


def test_numeric_indexes_and_mixed_locations_sort_stably() -> None:
    locations: list[tuple[str | int, ...]] = [("x", 10), ("x", 2), ("x", "2"), ()]
    diagnostics = [
        Diagnostic("model_validation", Path("a"), loc, "Invalid.", "Fix.")
        for loc in locations
    ]
    assert [d.location for d in ConfigurationError(diagnostics).diagnostics] == [
        (),
        ("x", 2),
        ("x", 10),
        ("x", "2"),
    ]


def test_display_escapes_untrusted_paths_and_unusual_keys() -> None:
    from enrama.config import format_diagnostic

    error = failure(
        MINIMAL + b'"a.b\\n\\u001b[31m": SECRET\n', "bad\n\x1b[31m\u202e.yaml"
    )
    output = format_diagnostic(error.diagnostics[0])
    assert '["a.b\\n\\u001b[31m"]' in output
    assert "bad\\n\\u001b[31m\\u202e.yaml" in output
    assert "\x1b" not in output and "\u202e" not in output
    assert "SECRET" not in output
    assert "Hint:" in output


def test_parser_errors_share_safe_public_diagnostics() -> None:
    error = failure(b'"a": SECRET\na: OTHER\n')
    assert error.category == "yaml_structure"
    assert error.total_count == 1
    assert "first" in str(error).lower()
    assert "1:1" in str(error)
    assert "SECRET" not in str(error)
    syntax = failure(b"secret: [SECRET\n")
    assert syntax.category == "yaml_syntax"
    assert "SECRET" not in str(syntax)


def test_no_printing_or_model_validation_on_yaml_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden(*args: object, **kwargs: object) -> EnramaConfig:
        raise AssertionError("Partial data reached validation")

    monkeypatch.setattr(EnramaConfig, "model_validate", forbidden)
    failure(b"x: [\n")
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("exception", [KeyboardInterrupt, RuntimeError])
def test_unexpected_validation_defects_propagate(
    monkeypatch: pytest.MonkeyPatch, exception: type[BaseException]
) -> None:
    def broken(*args: object, **kwargs: object) -> EnramaConfig:
        raise exception("Internal defect")

    monkeypatch.setattr(EnramaConfig, "model_validate", broken)
    with pytest.raises(exception):
        parse(MINIMAL)
