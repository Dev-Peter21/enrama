"""Structured expected failures; no parser payloads, printing, or exit policy."""

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FieldLocation = tuple[str | int, ...]
Category = Literal[
    "missing_file",
    "read_error",
    "invalid_encoding",
    "yaml_syntax",
    "yaml_structure",
    "resource_limit",
    "model_validation",
]


@dataclass(frozen=True, order=True)
class SourcePosition:
    line: int
    column: int


@dataclass(frozen=True)
class Diagnostic:
    category: Category
    source: Path
    location: FieldLocation
    message: str
    hint: str
    position: SourcePosition | None = None
    parent: bool = False
    related: tuple[SourcePosition, ...] = ()


def _order(diagnostic: Diagnostic) -> tuple[object, ...]:
    # Tag components so mixed string/integer locations never compare unlike types.
    position = diagnostic.position
    return (
        (0, position.line, position.column) if position else (1, 0, 0),
        tuple((0, p) if isinstance(p, int) else (1, p) for p in diagnostic.location),
        diagnostic.category,
    )


def _field(location: FieldLocation) -> str:
    result = ""
    for part in location:
        if isinstance(part, int):
            result += f"[{part}]"
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
            result += ("." if result else "") + part
        else:
            result += "[" + json.dumps(part, ensure_ascii=True) + "]"
    return result or "$"


def format_diagnostic(diagnostic: Diagnostic) -> str:
    """Return safe English text, without terminal I/O or process policy."""
    source = json.dumps(str(diagnostic.source), ensure_ascii=True)[1:-1]
    if position := diagnostic.position:
        source += f":{position.line}:{position.column}"
    parent = " (parent position)" if diagnostic.parent else ""
    text = f"{source} — {_field(diagnostic.location)}{parent}\n"
    text += diagnostic.message + "\nHint: " + diagnostic.hint
    for position in diagnostic.related:
        text += f"\nFirst occurrence: {position.line}:{position.column}."
    return text


class ConfigurationError(Exception):
    """An expected failure containing at most twenty actionable diagnostics."""

    def __init__(self, diagnostics: Iterable[Diagnostic]) -> None:
        items = tuple(sorted(diagnostics, key=_order))
        if not items:
            raise ValueError("ConfigurationError requires a diagnostic")
        self.total_count = len(items)
        self.diagnostics = items[:20]
        self.omitted_count = max(0, self.total_count - 20)
        text = "\n\n".join(map(format_diagnostic, self.diagnostics))
        if self.omitted_count:
            text += f"\nShowing 20 of {self.total_count} errors."
        super().__init__(text)

    @property
    def category(self) -> Category:
        return self.diagnostics[0].category
