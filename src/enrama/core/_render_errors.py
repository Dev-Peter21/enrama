"""Structured render failures; presentation and process exits belong to callers."""

from typing import Literal

RenderKind = Literal["internal", "operational"]
RenderCategory = Literal[
    "asset_mismatch", "template_error", "resource_error", "internal_error"
]


class RenderError(Exception):
    """One render failure with safe, static English context and no partial output."""

    def __init__(
        self,
        kind: RenderKind,
        category: RenderCategory,
        message: str,
        hint: str,
        *,
        field: str | None = None,
        template: str | None = None,
    ) -> None:
        self.kind = kind
        self.category = category
        self.message = message
        self.hint = hint
        self.field = field
        self.template = template
        super().__init__(message)

    def __str__(self) -> str:
        context = self.field or self.template
        return (
            f"{self.message} ({context}). {self.hint}"
            if context
            else f"{self.message}. {self.hint}"
        )
