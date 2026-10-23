"""Validate the v1 language subset against a fixed, installed IANA snapshot."""

import re
from importlib.resources import files

_TAG = re.compile(
    r"(?P<language>[a-z]{2,8})(?:-(?P<script>[a-z]{4}))?"
    r"(?:-(?P<region>[a-z]{2}|[0-9]{3}))?"
    r"(?P<variants>(?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*)",
    re.IGNORECASE | re.ASCII,
)


def _load_registry() -> tuple[str, dict[str, frozenset[str]]]:
    # Read trusted dependency data once, never a client file or remote service.
    snapshot = (
        files("langcodes")
        .joinpath("data/language-subtag-registry.txt")
        .read_text(encoding="utf-8")
    )
    registry: dict[str, set[str]] = {
        kind: set() for kind in ("language", "script", "region", "variant")
    }
    for block in snapshot.split("%%")[1:]:
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        kind, subtag = fields.get("Type", ""), fields.get("Subtag", "")
        # Private-use ranges are not enumerated into supported codes.
        if kind in registry and subtag and ".." not in subtag:
            if fields.get("Description", "").lower() != "private use":
                registry[kind].add(subtag.lower())
    return snapshot.splitlines()[0].removeprefix("File-Date: "), {
        kind: frozenset(values) for kind, values in registry.items()
    }


REGISTRY_DATE, _REGISTRY = _load_registry()


def validate_language(value: str) -> str:
    """Return case-normalized registered subtags, without alias replacement."""
    match = _TAG.fullmatch(value)
    if match is None:
        raise ValueError("Use language[-Script][-REGION][-variant], with hyphens")
    language, script, region = match.group("language", "script", "region")
    variants = match.group("variants").lower().split("-")[1:]
    for kind, subtag in (
        ("language", language),
        ("script", script),
        ("region", region),
    ):
        if subtag and subtag.lower() not in _REGISTRY[kind]:
            raise ValueError(f"Unknown or unsupported {kind} subtag: {subtag}")
    if len(set(variants)) != len(variants):
        raise ValueError("Language variants must not repeat")
    if any(variant not in _REGISTRY["variant"] for variant in variants):
        raise ValueError("Use registered language variants")
    return "-".join(
        [language.lower()]
        + ([script.title()] if script else [])
        + ([region.upper()] if region else [])
        + variants
    )
