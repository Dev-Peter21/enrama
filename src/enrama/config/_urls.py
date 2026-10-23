"""Strict input policy around URL parsers; retain accepted destinations verbatim."""

import re
import unicodedata
from email.errors import MessageError
from email.headerregistry import Address
from urllib.parse import unquote, urlsplit

from pydantic import AnyHttpUrl, TypeAdapter

_HTTP = TypeAdapter(AnyHttpUrl)
_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})")
_BAD_CHARACTERS = frozenset('\\<>"{}|^`')


def _validate_mailbox(address: str) -> None:
    quoted = escaped = False
    for char in address:
        if unicodedata.category(char) in {"Cc", "Cf", "Cs"}:
            raise ValueError("Mailto address must not contain control characters")
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and (char.isspace() or char in "()"):
            raise ValueError("Use an addr-spec without comments or surrounding space")
    try:
        mailbox = Address(addr_spec=address)
    except (ValueError, IndexError, MessageError) as error:
        raise ValueError("Use one valid mailto addr-spec address") from error
    if not mailbox.username or not mailbox.domain:
        raise ValueError("Mailto address requires a local part and domain")


def _validate_url(value: str, schemes: frozenset[str]) -> str:
    if not value or len(value) > 2048:
        raise ValueError("URL must contain 1–2048 characters")
    if any(
        char.isspace()
        or unicodedata.category(char) in {"Cc", "Cf", "Cs"}
        or char in _BAD_CHARACTERS
        for char in value
    ):
        raise ValueError("URL contains whitespace, controls, or invalid characters")
    if _BAD_PERCENT.search(value):
        raise ValueError("Use two hexadecimal digits after each URL percent escape")
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme not in schemes:
        raise ValueError(f"Use one of these URL schemes: {', '.join(sorted(schemes))}")
    if scheme in {"http", "https"}:
        if not parsed.netloc or not parsed.hostname:
            raise ValueError("HTTP(S) URL must be absolute and include a host")
        if "@" in parsed.netloc:
            raise ValueError("URL must not contain username or password information")
        # Pydantic checks hosts, IP literals and ports, but may normalize the URL.
        # Its output is deliberately discarded so input is never silently repaired.
        _HTTP.validate_python(value)
    elif scheme == "mailto":
        if "?" in value or "#" in value or parsed.netloc:
            raise ValueError("Use one mailto address without headers or fragment")
        address = unquote(parsed.path, errors="strict")
        _validate_mailbox(address)
    elif not re.fullmatch(r"\+[0-9]+", parsed.path) or "?" in value or "#" in value:
        raise ValueError("Use tel:+ followed by digits only, without extensions")
    return value


def validate_link_url(value: str) -> str:
    """Validate a destination, including the restricted mailto and tel subsets."""
    return _validate_url(value, frozenset({"https", "http", "mailto", "tel"}))


def validate_https_url(value: str) -> str:
    """Validate an HTTPS social destination without domain binding."""
    return _validate_url(value, frozenset({"https"}))


def validate_site_url(value: str) -> str:
    """Validate the optional public base URL when a non-null value is supplied."""
    validate_https_url(value)
    if "?" in value or "#" in value:
        raise ValueError("Site URL must not contain a query or fragment")
    return value
