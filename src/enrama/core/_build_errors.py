"""Safe expected build failures; terminal formatting and exits belong to CLI."""

from typing import Literal


class BuildError(Exception):
    def __init__(
        self,
        kind: Literal["invalid_input", "operational", "internal"],
        category: str,
        message: str,
        hint: str,
    ) -> None:
        self.kind = kind
        self.category = category
        self.message = message
        self.hint = hint
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.message}. {self.hint}"
