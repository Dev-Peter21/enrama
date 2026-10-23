"""Load the controlled YAML subset and reuse C01's semantic field policy."""

from pathlib import Path

from pydantic import ValidationError

from ._yaml import ParsedYaml, parse_yaml
from .diagnostics import ConfigurationError, Diagnostic, FieldLocation
from .models import EnramaConfig


def _explanation(code: str, location: FieldLocation) -> tuple[str, str]:
    field = location[-1] if location else None
    if code == "missing":
        return "Required field is missing.", "Add this field to its parent mapping."
    if code == "extra_forbidden":
        return (
            "Unknown configuration field.",
            "Remove this field or use a documented YAML v1 field.",
        )
    if code == "string_type":
        return "Expected text.", "Use text; quote numeric or boolean-looking text."
    if code == "bool_type":
        return "Expected a boolean.", "Use unquoted lowercase true or false."
    if code == "int_type":
        return "Expected an integer.", "Use the unquoted integer 1 for schema_version."
    if code in {"model_type", "dict_type"}:
        return "Expected a mapping.", "Use a YAML mapping with the documented fields."
    if code == "list_type":
        return (
            "Expected a list.",
            "Use a YAML list, or omit this field for an empty list.",
        )
    if code == "string_too_short":
        return (
            "Text is empty or too short.",
            "Use nonempty text within the documented field length.",
        )
    if code == "string_too_long":
        return (
            "Text exceeds the field length limit.",
            "Shorten the text to the limit in the YAML v1 field contract.",
        )
    if code == "too_long":
        return (
            "Collection exceeds its entry limit.",
            "Use at most 100 links or 20 socials.",
        )
    if field == "schema_version":
        return "Unsupported schema version.", "Use schema_version: 1."
    if field == "url":
        if location[:1] == ("links",):
            return (
                "Invalid link URL.",
                "Use a valid absolute URL with https, http, mailto or tel, following the YAML v1 URL rules.",
            )
        return (
            "Invalid HTTPS URL.",
            "Use a valid absolute HTTPS URL following the YAML v1 URL rules.",
        )
    if field == "language":
        return (
            "Invalid language tag.",
            "Use a registered BCP 47 language tag, such as en or es-AR.",
        )
    if field in {"avatar", "favicon", "og_image"}:
        return (
            "Invalid local asset reference.",
            "Use a local relative path outside dist/, without '..'.",
        )
    if field == "id":
        return (
            "Invalid entry ID.",
            "Use 1–64 lowercase letters, digits or hyphens, starting with a letter.",
        )
    if field in {"primary_color", "background_color", "text_color"}:
        return "Invalid color.", "Use a quoted #RRGGBB hexadecimal color."
    if field == "name" and location[:1] == ("theme",):
        return "Unknown theme.", "Choose minimal or bold."
    if field == "platform":
        return (
            "Unknown social platform.",
            "Choose a platform from the documented social platform catalog.",
        )
    if field == "icon":
        return (
            "Unknown link icon.",
            "Choose an icon from the documented icon catalog, or use null.",
        )
    if not location and code == "value_error":
        return (
            "Entry IDs must be unique across links and socials.",
            "Give every link and social entry its own stable ID.",
        )
    return (
        "Invalid configuration value.",
        "Use the type and constraints documented for this YAML v1 field.",
    )


def _diagnostic(
    code: str, location: FieldLocation, parsed: ParsedYaml, source: Path
) -> Diagnostic:
    message, hint = _explanation(code, location)
    position = None
    parent = False
    if location:
        if code == "missing":
            ancestor = location[:-1]
            while ancestor not in parsed.containers and ancestor:
                ancestor = ancestor[:-1]
            position = parsed.positions.get(ancestor)
            parent = position is not None
        else:
            position = parsed.positions.get(location)
    return Diagnostic(
        "model_validation", source, location, message, hint, position, parent
    )


def parse_config(content: bytes, *, source: str | Path = "enrama.yaml") -> EnramaConfig:
    """Validate UTF-8 YAML bytes; source labels diagnostics without reading a file."""
    selected = Path(source)
    parsed = parse_yaml(content, selected)
    try:
        return EnramaConfig.model_validate(parsed.data)
    except ValidationError as error:
        errors = error.errors(
            include_input=False, include_context=False, include_url=False
        )
        primary = [e for e in errors if e["type"] != "default_factory_not_called"]
        if not primary:
            raise  # A framework defect is not invalid client input.
        raise ConfigurationError(
            _diagnostic(e["type"], e["loc"], parsed, selected) for e in primary
        ) from None
