"""
poe2_build_validator
~~~~~~~~~~~~~~~~~~~~
Validate Path of Exile 2 .build files against the official spec.

Quick start::

    import json
    from poe2_build_validator import validate, load_build_file

    # from a file
    result = load_build_file("MyBuild.build")
    print(result)           # human-readable summary

    # from already-parsed data
    data = json.loads(raw_text)
    result = validate(data)
    if not result.valid:
        for err in result.errors:
            print(err)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ValidationError, ValidationResult
from .models import Build, BuildItem, BuildPassive, BuildSkill, BuildSupport
from .validator import Validator, parse

__all__ = [
    # core API
    "validate",
    "load_build_file",
    # models
    "Build",
    "BuildItem",
    "BuildPassive",
    "BuildSkill",
    "BuildSupport",
    # error types
    "ValidationResult",
    "ValidationError",
]

_validator = Validator()


def validate(data: Any) -> ValidationResult:
    """Validate *data* (a dict from ``json.loads``) and return a :class:`ValidationResult`."""
    return _validator.validate(data)


def load_build_file(path: str | Path) -> ValidationResult:
    """
    Read *path*, parse it as JSON, validate it, and return a :class:`ValidationResult`.

    The ``ValidationResult.errors`` list is empty when the file is valid.
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        result = ValidationResult()
        result.add("$", f"cannot read file: {exc}")
        return result

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        result = ValidationResult()
        result.add("$", f"invalid JSON: {exc}")
        return result

    return validate(data)
