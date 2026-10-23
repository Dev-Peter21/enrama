"""Structured expected failures; no parser payloads, printing, or exit policy."""

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


class ConfigurationError(Exception):
    """An expected failure containing at most twenty actionable diagnostics."""

    def __init__(self, diagnostics: Iterable[Diagnostic]) -> None:
        items = tuple(diagnostics)
        if not items:
            raise ValueError("ConfigurationError requires a diagnostic")
        self.total_count = len(items)
        self.diagnostics = items[:20]
        self.omitted_count = max(0, self.total_count - 20)
        super().__init__("Configuration could not be loaded.")

    @property
    def category(self) -> Category:
        return self.diagnostics[0].category
