"""Deterministic structural editor schema, derived from the validation models."""

import json

from .models import EnramaConfig


def generate_schema() -> bytes:
    """Return the local Draft 2020-12 artifact without reading/writing client files."""
    schema = EnramaConfig.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return (
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
