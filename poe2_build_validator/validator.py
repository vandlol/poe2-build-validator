"""
Validates raw JSON data (as parsed from a .build file) against the
official PoE2 Build Planner specification.

Usage
-----
    from poe2_build_validator.validator import Validator

    result = Validator().validate(data)   # data is a dict from json.loads()
    if not result.valid:
        print(result)
"""

from __future__ import annotations

import re
from typing import Any

from .errors import ValidationResult
from .models import Build, BuildItem, BuildPassive, BuildSkill, BuildSupport

# ---------------------------------------------------------------------------
# Markup validation
# ---------------------------------------------------------------------------

_SIMPLE_TAGS = {"bold", "italics", "red"}
_RGB_COMPONENT_RE = re.compile(
    r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$"
)
_TAG_PATTERN = re.compile(r"<([^>]+)>")


def _validate_markup(text: str, path: str, result: ValidationResult) -> None:
    """Check that every markup tag in *text* is one the game recognises."""
    for match in _TAG_PATTERN.finditer(text):
        tag_content = match.group(1)
        if tag_content in _SIMPLE_TAGS:
            continue
        rgb_match = _RGB_COMPONENT_RE.match(tag_content)
        if rgb_match:
            for i, component in enumerate(rgb_match.groups(), 1):
                if int(component) > 255:
                    result.add(
                        path,
                        f"rgb component {i} out of range (0–255): {component}",
                    )
            continue
        result.add(path, f"unknown markup tag: <{tag_content}>")


# ---------------------------------------------------------------------------
# Shared field helpers
# ---------------------------------------------------------------------------

def _validate_level_interval(
    value: Any, path: str, result: ValidationResult
) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        result.add(path, "level_interval must be an array")
        return
    if len(value) != 2:
        result.add(path, f"level_interval must have exactly 2 elements, got {len(value)}")
        return
    lo, hi = value
    for label, v in (("first", lo), ("second", hi)):
        if not isinstance(v, int):
            result.add(path, f"level_interval {label} element must be an integer")
    if isinstance(lo, int) and isinstance(hi, int):
        if lo < 0 or hi < 0:
            result.add(path, "level_interval values must be non-negative")
        elif lo > hi:
            result.add(path, f"level_interval min ({lo}) must be <= max ({hi})")


def _validate_additional_text(
    value: Any, path: str, result: ValidationResult
) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        result.add(path, "additional_text must be a string")
        return
    _validate_markup(value, path + ".additional_text", result)


def _require_string_id(
    data: dict[str, Any], path: str, result: ValidationResult
) -> bool:
    """Returns True if 'id' is present and a non-empty string."""
    if "id" not in data:
        result.add(path, "missing required field 'id'")
        return False
    if not isinstance(data["id"], str):
        result.add(path + ".id", "must be a string")
        return False
    if not data["id"].strip():
        result.add(path + ".id", "must not be empty")
        return False
    return True


# ---------------------------------------------------------------------------
# Per-object validators
# ---------------------------------------------------------------------------

def _validate_support(data: Any, path: str, result: ValidationResult) -> None:
    if isinstance(data, str):
        if not data.strip():
            result.add(path, "support skill ID string must not be empty")
        return

    if not isinstance(data, dict):
        result.add(path, "support skill entry must be a string or object")
        return

    _require_string_id(data, path, result)
    _validate_level_interval(data.get("level_interval"), path, result)
    _validate_additional_text(data.get("additional_text"), path, result)

    unknown = set(data) - {"id", "level_interval", "additional_text"}
    for key in unknown:
        result.add(path, f"unrecognised field '{key}'")


def _validate_skill(data: Any, path: str, result: ValidationResult) -> None:
    if isinstance(data, str):
        if not data.strip():
            result.add(path, "skill ID string must not be empty")
        return

    if not isinstance(data, dict):
        result.add(path, "skill entry must be a string or object")
        return

    _require_string_id(data, path, result)
    _validate_level_interval(data.get("level_interval"), path, result)
    _validate_additional_text(data.get("additional_text"), path, result)

    supports = data.get("support_skills", [])
    if not isinstance(supports, list):
        result.add(path + ".support_skills", "must be an array")
    else:
        for i, sup in enumerate(supports):
            _validate_support(sup, f"{path}.support_skills[{i}]", result)

    unknown = set(data) - {"id", "level_interval", "additional_text", "support_skills"}
    for key in unknown:
        result.add(path, f"unrecognised field '{key}'")


def _validate_passive(data: Any, path: str, result: ValidationResult) -> None:
    if isinstance(data, str):
        if not data.strip():
            result.add(path, "passive ID string must not be empty")
        return

    if not isinstance(data, dict):
        result.add(path, "passive entry must be a string or object")
        return

    _require_string_id(data, path, result)
    _validate_level_interval(data.get("level_interval"), path, result)
    _validate_additional_text(data.get("additional_text"), path, result)

    weapon_set = data.get("weapon_set")
    if weapon_set is not None:
        if not isinstance(weapon_set, int) or isinstance(weapon_set, bool):
            result.add(path + ".weapon_set", "must be an unsigned integer")
        elif weapon_set < 0:
            result.add(path + ".weapon_set", "must be >= 0 (unsigned)")

    unknown = set(data) - {"id", "level_interval", "additional_text", "weapon_set"}
    for key in unknown:
        result.add(path, f"unrecognised field '{key}'")


def _validate_item(data: Any, path: str, result: ValidationResult) -> None:
    if not isinstance(data, dict):
        result.add(path, "item entry must be an object")
        return

    if "inventory_id" not in data:
        result.add(path, "missing required field 'inventory_id'")
    elif not isinstance(data["inventory_id"], str):
        result.add(path + ".inventory_id", "must be a string")
    elif not data["inventory_id"].strip():
        result.add(path + ".inventory_id", "must not be empty")

    for coord in ("slot_x", "slot_y"):
        val = data.get(coord)
        if val is not None and (not isinstance(val, int) or isinstance(val, bool)):
            result.add(path + f".{coord}", "must be an integer")

    _validate_level_interval(data.get("level_interval"), path, result)

    unique_name = data.get("unique_name")
    if unique_name is not None and not isinstance(unique_name, str):
        result.add(path + ".unique_name", "must be a string")

    _validate_additional_text(data.get("additional_text"), path, result)

    unknown = set(data) - {
        "inventory_id", "slot_x", "slot_y",
        "level_interval", "unique_name", "additional_text",
    }
    for key in unknown:
        result.add(path, f"unrecognised field '{key}'")


# ---------------------------------------------------------------------------
# Root validator
# ---------------------------------------------------------------------------

class Validator:
    """Validates raw parsed JSON data against the PoE2 Build Planner spec."""

    def validate(self, data: Any) -> ValidationResult:
        result = ValidationResult()
        self._validate_root(data, result)
        return result

    def _validate_root(self, data: Any, result: ValidationResult) -> None:
        if not isinstance(data, dict):
            result.add("$", "root must be a JSON object")
            return

        # --- required fields ---
        if "name" not in data:
            result.add("$.name", "missing required field 'name'")
        elif not isinstance(data["name"], str):
            result.add("$.name", "must be a string")
        elif not data["name"].strip():
            result.add("$.name", "must not be empty")

        # --- optional scalar fields ---
        for field in ("description", "ascendancy"):
            val = data.get(field)
            if val is not None and not isinstance(val, str):
                result.add(f"$.{field}", "must be a string")

        # --- passives ---
        passives = data.get("passives", [])
        if not isinstance(passives, list):
            result.add("$.passives", "must be an array")
        else:
            for i, p in enumerate(passives):
                _validate_passive(p, f"$.passives[{i}]", result)

        # --- skills ---
        skills = data.get("skills", [])
        if not isinstance(skills, list):
            result.add("$.skills", "must be an array")
        else:
            for i, s in enumerate(skills):
                _validate_skill(s, f"$.skills[{i}]", result)

        # --- items ---
        items = data.get("items", [])
        if not isinstance(items, list):
            result.add("$.items", "must be an array")
        else:
            for i, item in enumerate(items):
                _validate_item(item, f"$.items[{i}]", result)

        # --- unknown top-level fields ---
        known = {"name", "description", "ascendancy", "passives", "skills", "items"}
        for key in set(data) - known:
            result.add(f"$.{key}", "unrecognised top-level field")


# ---------------------------------------------------------------------------
# Convenience: parse raw JSON data into typed models (best-effort)
# ---------------------------------------------------------------------------

def _build_support(data: str | dict) -> BuildSupport | str:
    if isinstance(data, str):
        return data
    return BuildSupport(
        id=data["id"],
        level_interval=tuple(data["level_interval"]) if data.get("level_interval") else None,
        additional_text=data.get("additional_text"),
    )


def _build_skill(data: str | dict) -> BuildSkill | str:
    if isinstance(data, str):
        return data
    return BuildSkill(
        id=data["id"],
        level_interval=tuple(data["level_interval"]) if data.get("level_interval") else None,
        additional_text=data.get("additional_text"),
        support_skills=[_build_support(s) for s in data.get("support_skills", [])],
    )


def _build_passive(data: str | dict) -> BuildPassive | str:
    if isinstance(data, str):
        return data
    return BuildPassive(
        id=data["id"],
        level_interval=tuple(data["level_interval"]) if data.get("level_interval") else None,
        weapon_set=data.get("weapon_set"),
        additional_text=data.get("additional_text"),
    )


def _build_item(data: dict) -> BuildItem:
    return BuildItem(
        inventory_id=data["inventory_id"],
        slot_x=data.get("slot_x"),
        slot_y=data.get("slot_y"),
        level_interval=tuple(data["level_interval"]) if data.get("level_interval") else None,
        unique_name=data.get("unique_name"),
        additional_text=data.get("additional_text"),
    )


def parse(data: dict) -> Build:
    """Convert a validated dict into a typed :class:`Build` instance."""
    return Build(
        name=data["name"],
        description=data.get("description"),
        ascendancy=data.get("ascendancy"),
        passives=[_build_passive(p) for p in data.get("passives", [])],
        skills=[_build_skill(s) for s in data.get("skills", [])],
        items=[_build_item(i) for i in data.get("items", [])],
    )
