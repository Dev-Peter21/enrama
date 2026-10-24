"""Expected asset failures with safe field context; no process or terminal I/O."""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from enrama.config.diagnostics import Diagnostic, FieldLocation, format_diagnostic

Category = Literal[
    "missing_asset",
    "unsafe_path",
    "read_error",
    "unsupported_format",
    "invalid_image",
    "resource_limit",
    "animation",
    "collision",
    "destination_conflict",
    "write_error",
]


class AssetEnvironmentError(RuntimeError):
    """Required installed decoder capabilities/settings are unavailable."""


class InvalidImage(ValueError):
    """A snapshot violates the image policy, without exposing decoder payloads."""

    def __init__(self, category: Category, message: str, hint: str) -> None:
        self.category = category
        self.message = message
        self.hint = hint
        super().__init__(message)


@dataclass(frozen=True)
class AssetDiagnostic:
    category: Category
    source: Path
    location: FieldLocation
    reference: str | None
    message: str
    hint: str

    def __str__(self) -> str:
        message = self.message
        if self.reference is not None:
            message += "\nAsset: " + json.dumps(self.reference, ensure_ascii=True)
        return format_diagnostic(
            Diagnostic(
                category="model_validation",
                source=self.source,
                location=self.location,
                message=message,
                hint=self.hint,
            )
        )


class AssetError(Exception):
    """At most twenty diagnostics, in stable field/global order."""

    def __init__(self, diagnostics: Iterable[AssetDiagnostic]) -> None:
        items = tuple(diagnostics)
        if not items:
            raise ValueError("AssetError requires a diagnostic")
        self.kind: Literal["invalid_input", "operational"] = (
            "operational"
            if any(
                d.category in {"read_error", "write_error", "destination_conflict"}
                for d in items
            )
            else "invalid_input"
        )
        self.total_count = len(items)
        self.diagnostics = items[:20]
        self.omitted_count = max(0, len(items) - 20)
        message = "\n\n".join(map(str, self.diagnostics))
        if self.omitted_count:
            message += f"\nShowing 20 of {self.total_count} errors."
        super().__init__(message)
