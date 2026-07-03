"""Minimal, dependency-free JSON Schema validator.

Supports only the subset of (draft-04) keywords used by ``tdm_schedule_schema.json``:
``type``, ``required``, ``enum``, ``properties``, ``items``, ``additionalProperties`` (false),
``minItems``, ``minimum`` and the draft-04 boolean ``exclusiveMinimum``. Metadata keywords
(``$schema``, ``$id``, ``title``, ``description``) are ignored.

This exists so the generator runs on a vanilla Python install with no third-party libraries
(i.e. no ``jsonschema``). It is deliberately not a general-purpose validator.
"""

from __future__ import annotations

from typing import Any, List


def _join(path: str, key) -> str:
    """Append a property name or array index to a JSON path."""
    if isinstance(key, int):
        return f"{path}[{key}]"
    return f"{path}.{key}" if path else key


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if value is None:
        return "null"
    return type(value).__name__


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        # JSON booleans are not numbers even though Python bools subclass int.
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    # Unknown type keyword: don't block.
    return True


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _at(path: str) -> str:
    return path if path else "<root>"


def _validate(instance: Any, schema: dict, path: str, errors: List[str]) -> None:
    # type: if it fails we cannot meaningfully descend, so stop here for this node.
    expected = schema.get("type")
    if expected is not None and not _type_ok(instance, expected):
        errors.append(
            f"{_at(path)}: expected type '{expected}', got '{_type_name(instance)}'"
        )
        return

    if "enum" in schema and instance not in schema["enum"]:
        allowed = ", ".join(repr(v) for v in schema["enum"])
        errors.append(f"{_at(path)}: {instance!r} is not one of [{allowed}]")

    if "minimum" in schema and _is_number(instance):
        minimum = schema["minimum"]
        if schema.get("exclusiveMinimum") is True:
            if not instance > minimum:
                errors.append(f"{_at(path)}: {instance} must be > {minimum}")
        elif instance < minimum:
            errors.append(f"{_at(path)}: {instance} must be >= {minimum}")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})

        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{_at(path)}: missing required property '{key}'")

        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{_at(path)}: unexpected property '{key}'")

        for key, subschema in properties.items():
            if key in instance:
                _validate(instance[key], subschema, _join(path, key), errors)

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(
                f"{_at(path)}: expected at least {min_items} item(s), got {len(instance)}"
            )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, element in enumerate(instance):
                _validate(element, item_schema, _join(path, index), errors)


def validate_schema(instance: Any, schema: dict) -> List[str]:
    """Validate ``instance`` against ``schema``; return a list of error messages (empty if valid)."""
    errors: List[str] = []
    _validate(instance, schema, "", errors)
    return errors
