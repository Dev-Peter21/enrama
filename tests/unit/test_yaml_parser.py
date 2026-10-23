"""C02's parser subset and budgets, before C01 field validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from enrama.config._yaml import ParsedYaml
    from enrama.config.diagnostics import ConfigurationError


def parse(content: bytes) -> ParsedYaml:
    from enrama.config._yaml import parse_yaml

    return parse_yaml(content, Path("client/enrama.yaml"))


def rejected(content: bytes, category: str) -> ConfigurationError:
    from enrama.config.diagnostics import ConfigurationError

    with pytest.raises(ConfigurationError) as caught:
        parse(content)
    assert caught.value.diagnostics[0].category == category
    return caught.value


@pytest.mark.parametrize(
    ("scalar", "expected"),
    [
        ("true", True),
        ("false", False),
        ("null", None),
        ("~", None),
        ("", None),
        ("1", 1),
        ("-2", -2),
        ("0", 0),
        ("-0", 0),
        ("1.0", 1.0),
        ("1e2", 100.0),
        ("-1.2e-2", -0.012),
        ("on", "on"),
        ("off", "off"),
        ("yes", "yes"),
        ("no", "no"),
        ("True", "True"),
        ("False", "False"),
        ("NULL", "NULL"),
        ("2026-10-23", "2026-10-23"),
        ("01", "01"),
        ("0x12", "0x12"),
        ("+1", "+1"),
        (".inf", ".inf"),
        (".nan", ".nan"),
        ("1.", "1."),
        ('"true"', "true"),
        ("'1'", "1"),
        ("!!str 1", "1"),
        ('!!bool "false"', False),
        ('!!int "1"', 1),
        ('!!float "1e2"', 100.0),
    ],
)
def test_plain_data_scalar_resolution_is_explicit(
    scalar: str, expected: object
) -> None:
    value = parse(f"value: {scalar}\n".encode()).data["value"]
    assert value == expected
    assert type(value) is type(expected)


@pytest.mark.parametrize("prefix", [b"", b"\xef\xbb\xbf", b"---\n"])
def test_utf8_and_document_markers(prefix: bytes) -> None:
    assert parse(prefix + b'title: "Flores & * plantas <<"\n' + b"...\n").data == {
        "title": "Flores & * plantas <<"
    }


def test_block_flow_and_multiline_content() -> None:
    result = parse(
        b"a: [one, {two: three}]\nb: |\n  line one\n  line two\nc: >\n  hello\n  world\n"
    )
    assert result.data == {
        "a": ["one", {"two": "three"}],
        "b": "line one\nline two\n",
        "c": "hello world\n",
    }
    assert (
        result.positions[("a", 1, "two")].line,
        result.positions[("a", 1, "two")].column,
    ) == (1, 16)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"# comment\n",
        b"[]",
        b"null",
        b"hello",
        b"---\n",
        b"a: 1\n---\nb: 2\n",
        b"a: 1\n---\n",
    ],
)
def test_reject_empty_wrong_root_and_multiple_documents(content: bytes) -> None:
    rejected(content, "yaml_structure")


@pytest.mark.parametrize(
    "content", [b"\xff", b"\xff\xfea\x00", b"a: \x00", b"a: [1,\n"]
)
def test_invalid_encoding_and_yaml_syntax_are_distinct(content: bytes) -> None:
    rejected(
        content, "invalid_encoding" if content.startswith((b"\xff",)) else "yaml_syntax"
    )


@pytest.mark.parametrize(
    "content",
    [
        b"a: &x 1",
        b"a: *missing",
        b"a: &x [*x]",
        b"a: {<<: {b: 2}}",
        b"a: !custom thing",
        b"a: !!python/object/apply:os.system [echo]",
        b"a: !!timestamp 2026-10-23",
        b"a: !!binary YQ==",
        b"a: !!set {x: null}",
        b"a: !!bool yes",
        b"a: !!int 01",
        b"a: !!float .inf",
        b"a: !!seq 1",
        b"a: !!map []",
        b"1: value",
        b"[a,b]: value",
    ],
)
def test_reject_unsupported_constructs_and_key_types(content: bytes) -> None:
    rejected(content, "yaml_structure")


def test_duplicate_key_reports_both_key_marks() -> None:
    error = rejected(b'a: 1\n"a": 2\n', "yaml_structure")
    diagnostic = error.diagnostics[0]
    assert diagnostic.location == ("a",)
    assert diagnostic.position is not None
    assert (diagnostic.position.line, diagnostic.position.column) == (2, 1)
    assert [(mark.line, mark.column) for mark in diagnostic.related] == [(1, 1)]


def test_nested_quoted_duplicate_keys_are_not_overwritten() -> None:
    error = rejected(b'outer:\n  a: 1\n  "a": 2\n', "yaml_structure")
    assert error.diagnostics[0].location == ("outer", "a")


def test_byte_limit_includes_bom_and_comments() -> None:
    base = b"\xef\xbb\xbf{}\n#"
    content = base + b"a" * (1_048_576 - len(base))
    assert parse(content).data == {}
    rejected(content + b"a", "resource_limit")


def test_container_depth_counts_root_but_not_scalar() -> None:
    assert parse(("x: " + "[" * 31 + "0" + "]" * 31).encode()).data
    rejected(("x: " + "[" * 32 + "0" + "]" * 32).encode(), "resource_limit")
    rejected(("x: " + "[" * 5000 + "0" + "]" * 5000).encode(), "resource_limit")


def test_node_budget_counts_root_key_sequence_and_each_scalar() -> None:
    at_limit = b"x: [" + b",".join([b"0"] * 9997) + b"]"
    items = parse(at_limit).data["x"]
    assert isinstance(items, list)
    assert len(items) == 9997
    rejected(at_limit[:-1] + b",0]", "resource_limit")


@pytest.mark.parametrize(
    "scalar",
    [b"1e999", b"!!float 1e999", b"!!int " + b"1" * 5000],
    ids=["implicit-float", "explicit-float", "huge-integer"],
)
def test_numeric_overflow_is_expected_input_failure(scalar: bytes) -> None:
    rejected(b"x: " + scalar, "yaml_structure")


def test_safe_loader_globals_are_not_used_for_resolution_or_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import yaml

    def forbidden(*args: object) -> object:
        raise AssertionError("YAML constructor executed")

    monkeypatch.setattr(
        yaml.SafeLoader, "yaml_constructors", {"tag:yaml.org,2002:map": forbidden}
    )
    assert parse(b"a: on\nb: true").data == {"a": "on", "b": True}
    # A non-Enrama caller still uses its own ordinary YAML scalar rules.
    monkeypatch.undo()
    assert yaml.safe_load("a: on") == {"a": True}
