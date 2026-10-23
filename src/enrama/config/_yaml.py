"""Bound PyYAML's event stream before constructing Enrama's plain-data tree."""

import math
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import yaml
from yaml.error import MarkedYAMLError
from yaml.events import (
    AliasEvent,
    DocumentEndEvent,
    DocumentStartEvent,
    Event,
    MappingEndEvent,
    MappingStartEvent,
    NodeEvent,
    ScalarEvent,
    SequenceEndEvent,
    SequenceStartEvent,
    StreamEndEvent,
    StreamStartEvent,
)

from .diagnostics import (
    Category,
    ConfigurationError,
    Diagnostic,
    FieldLocation,
    SourcePosition,
)

MAX_BYTES = 1_048_576
_INTEGER = re.compile(r"-?(?:0|[1-9][0-9]*)", re.ASCII)
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", re.ASCII)
_PREFIX = "tag:yaml.org,2002:"


@dataclass(frozen=True)
class _Scalar:
    value: object
    position: SourcePosition


@dataclass(frozen=True)
class _Sequence:
    items: list["_Node"]
    position: SourcePosition


@dataclass(frozen=True)
class _Mapping:
    items: dict[str, "_Node"]
    position: SourcePosition


type _Node = _Scalar | _Sequence | _Mapping


@dataclass(frozen=True)
class ParsedYaml:
    data: dict[str, object]
    positions: dict[FieldLocation, SourcePosition]
    containers: frozenset[FieldLocation]


def _position(event: Event) -> SourcePosition:
    assert event.start_mark is not None
    return SourcePosition(event.start_mark.line + 1, event.start_mark.column + 1)


class _Reader:
    def __init__(self, events: Iterator[Event], source: Path) -> None:
        self.events = events
        self.source = source
        self.nodes = 0

    def fail(
        self,
        message: str,
        event: Event,
        location: FieldLocation = (),
        *,
        category: Category = "yaml_structure",
        related: tuple[SourcePosition, ...] = (),
    ) -> NoReturn:
        raise ConfigurationError(
            [
                Diagnostic(
                    category,
                    self.source,
                    location,
                    message,
                    "Use the supported YAML subset documented by Enrama.",
                    _position(event),
                    related=related,
                )
            ]
        )

    def scalar(self, event: ScalarEvent, location: FieldLocation) -> object:
        value = event.value
        kind = event.tag.removeprefix(_PREFIX) if event.tag else None
        if kind is None:
            if not event.implicit[0]:
                return value
            if value in {"true", "false"}:
                kind = "bool"
            elif value in {"null", "~", ""}:
                kind = "null"
            elif _INTEGER.fullmatch(value):
                kind = "int"
            elif _NUMBER.fullmatch(value):
                kind = "float"
            else:
                return value
        if event.tag and event.tag not in {
            _PREFIX + k for k in ("str", "null", "bool", "int", "float")
        }:
            self.fail("Unsupported YAML tag.", event, location)
        if kind == "str":
            return value
        if kind == "null" and value in {"null", "~", ""}:
            return None
        if kind == "bool" and value in {"true", "false"}:
            return value == "true"
        if kind == "int" and _INTEGER.fullmatch(value):
            try:
                return int(value)
            except ValueError:
                self.fail(
                    "Integer exceeds safe numeric conversion limits.", event, location
                )
        if kind == "float" and _NUMBER.fullmatch(value):
            number = float(value)
            if math.isfinite(number):
                return number
        self.fail("Invalid or non-finite scalar for its YAML type.", event, location)

    def node(self, event: Event, depth: int, location: FieldLocation) -> _Node:
        if isinstance(event, AliasEvent) or (
            isinstance(event, NodeEvent) and event.anchor is not None
        ):
            self.fail("YAML anchors and aliases are not supported.", event, location)
        self.nodes += 1
        if self.nodes > 10_000:
            self.fail(
                "YAML exceeds the 10,000-node limit.",
                event,
                location,
                category="resource_limit",
            )
        if isinstance(event, ScalarEvent):
            return _Scalar(self.scalar(event, location), _position(event))
        if not isinstance(event, (MappingStartEvent, SequenceStartEvent)):
            self.fail("Expected a YAML value.", event, location)
        depth += 1
        if depth > 32:
            self.fail(
                "YAML exceeds the 32-container depth limit.",
                event,
                location,
                category="resource_limit",
            )
        expected = "map" if isinstance(event, MappingStartEvent) else "seq"
        if event.tag not in {None, _PREFIX + expected}:
            self.fail("Unsupported YAML collection tag.", event, location)
        if isinstance(event, SequenceStartEvent):
            items: list[_Node] = []
            while not isinstance(child := next(self.events), SequenceEndEvent):
                items.append(self.node(child, depth, (*location, len(items))))
            return _Sequence(items, _position(event))
        mapping: dict[str, _Node] = {}
        keys: dict[str, SourcePosition] = {}
        while not isinstance(key_event := next(self.events), MappingEndEvent):
            key = self.node(key_event, depth, location)
            if not isinstance(key, _Scalar) or not isinstance(key.value, str):
                self.fail("Mapping keys must be strings.", key_event, location)
            field = (*location, key.value)
            if key.value == "<<":
                self.fail("YAML merge keys are not supported.", key_event, field)
            if key.value in keys:
                self.fail(
                    "Duplicate YAML mapping key.",
                    key_event,
                    field,
                    related=(keys[key.value],),
                )
            keys[key.value] = key.position
            mapping[key.value] = self.node(next(self.events), depth, field)
        return _Mapping(mapping, _position(event))


def _construct(root: _Mapping) -> ParsedYaml:
    positions: dict[FieldLocation, SourcePosition] = {}
    containers: set[FieldLocation] = set()

    def visit(node: _Node, path: FieldLocation) -> object:
        positions[path] = node.position
        if isinstance(node, _Scalar):
            return node.value
        containers.add(path)
        if isinstance(node, _Sequence):
            return [
                visit(child, (*path, index)) for index, child in enumerate(node.items)
            ]
        return {key: visit(child, (*path, key)) for key, child in node.items.items()}

    data = {key: visit(child, (key,)) for key, child in root.items.items()}
    positions[()] = root.position
    containers.add(())
    return ParsedYaml(data, positions, frozenset(containers))


def parse_yaml(content: bytes, source: Path) -> ParsedYaml:
    """Check bytes, syntax and representation budgets before plain construction."""
    if len(content) > MAX_BYTES:
        raise ConfigurationError(
            [
                Diagnostic(
                    "resource_limit",
                    source,
                    (),
                    "Configuration exceeds the 1 MiB byte limit.",
                    "Reduce the configuration to at most 1,048,576 bytes.",
                )
            ]
        )
    try:
        text = content.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        raise ConfigurationError(
            [
                Diagnostic(
                    "invalid_encoding",
                    source,
                    (),
                    "Configuration is not valid UTF-8.",
                    "Save the file as UTF-8, optionally with a BOM.",
                )
            ]
        ) from None
    events = yaml.parse(text, Loader=yaml.SafeLoader)
    reader = _Reader(events, source)
    try:
        assert isinstance(next(events), StreamStartEvent)
        first = next(events)
        if not isinstance(first, DocumentStartEvent):
            reader.fail("Expected one nonempty mapping document.", first)
        root = reader.node(next(events), 0, ())
        if not isinstance(root, _Mapping):
            reader.fail("Configuration root must be a mapping.", first)
        assert isinstance(next(events), DocumentEndEvent)
        last = next(events)
        if not isinstance(last, StreamEndEvent):
            reader.fail("Exactly one YAML document is supported.", last)
    except yaml.YAMLError as error:
        mark = error.problem_mark if isinstance(error, MarkedYAMLError) else None
        position = SourcePosition(mark.line + 1, mark.column + 1) if mark else None
        raise ConfigurationError(
            [
                Diagnostic(
                    "yaml_syntax",
                    source,
                    (),
                    "Invalid YAML syntax.",
                    "Check indentation, quoting, and collection delimiters.",
                    position,
                )
            ]
        ) from None
    finally:
        events.close()
    return _construct(root)
