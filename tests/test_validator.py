"""Tests for poe2_build_validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from poe2_build_validator import load_build_file, validate
from poe2_build_validator.validator import parse

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def fixture(name: str):
    return load_build_file(FIXTURES / name)


# ---------------------------------------------------------------------------
# Valid builds
# ---------------------------------------------------------------------------

class TestValidBuilds:
    def test_minimal_build(self):
        result = fixture("valid_minimal.build")
        assert result.valid, str(result)

    def test_full_build(self):
        result = fixture("valid_full.build")
        assert result.valid, str(result)

    def test_bare_string_passives_and_skills(self):
        data = {
            "name": "String Arrays",
            "passives": ["Node1", "Node2"],
            "skills": ["Gem1", "Gem2"],
        }
        assert validate(data).valid

    def test_empty_arrays(self):
        data = {"name": "No Content", "passives": [], "skills": [], "items": []}
        assert validate(data).valid

    def test_level_interval_same_value(self):
        data = {
            "name": "Same Interval",
            "passives": [{"id": "Node", "level_interval": [10, 10]}],
        }
        assert validate(data).valid

    def test_markup_bold_italics_red(self):
        data = {
            "name": "Markup",
            "passives": [{
                "id": "Node",
                "additional_text": "<bold>{ strong } and <italics>{ em } and <red>{ danger }",
            }],
        }
        assert validate(data).valid

    def test_markup_rgb(self):
        data = {
            "name": "RGB",
            "passives": [{"id": "Node", "additional_text": "<rgb(128, 0, 255)>{ text }"}],
        }
        assert validate(data).valid

    def test_support_as_string(self):
        data = {
            "name": "Supports",
            "skills": [{"id": "Gem", "support_skills": ["Support1", "Support2"]}],
        }
        assert validate(data).valid


# ---------------------------------------------------------------------------
# Invalid builds – root level
# ---------------------------------------------------------------------------

class TestInvalidRoot:
    def test_missing_name(self):
        result = fixture("invalid_missing_name.build")
        assert not result.valid
        paths = [e.path for e in result.errors]
        assert "$.name" in paths

    def test_not_an_object(self):
        result = validate([1, 2, 3])
        assert not result.valid
        assert result.errors[0].path == "$"

    def test_name_wrong_type(self):
        result = validate({"name": 99})
        assert not result.valid
        assert any(e.path == "$.name" for e in result.errors)

    def test_empty_name(self):
        result = validate({"name": "   "})
        assert not result.valid

    def test_description_wrong_type(self):
        result = validate({"name": "X", "description": 42})
        assert not result.valid

    def test_unknown_top_level_field(self):
        result = validate({"name": "X", "totally_unknown": True})
        assert not result.valid
        assert any("totally_unknown" in e.path for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid passives
# ---------------------------------------------------------------------------

class TestInvalidPassives:
    def test_passives_not_array(self):
        result = validate({"name": "X", "passives": "oops"})
        assert not result.valid

    def test_passive_wrong_type(self):
        result = validate({"name": "X", "passives": [12345]})
        assert not result.valid

    def test_passive_missing_id(self):
        result = validate({"name": "X", "passives": [{"weapon_set": 0}]})
        assert not result.valid
        assert any("id" in e.message for e in result.errors)

    def test_passive_empty_id(self):
        result = validate({"name": "X", "passives": [{"id": ""}]})
        assert not result.valid

    def test_passive_negative_weapon_set(self):
        result = validate({"name": "X", "passives": [{"id": "N", "weapon_set": -1}]})
        assert not result.valid

    def test_passive_bad_level_interval_order(self):
        result = validate({"name": "X", "passives": [{"id": "N", "level_interval": [50, 10]}]})
        assert not result.valid

    def test_passive_level_interval_wrong_length(self):
        result = validate({"name": "X", "passives": [{"id": "N", "level_interval": [10]}]})
        assert not result.valid

    def test_passive_unknown_field(self):
        result = validate({"name": "X", "passives": [{"id": "N", "mystery": True}]})
        assert not result.valid


# ---------------------------------------------------------------------------
# Invalid skills
# ---------------------------------------------------------------------------

class TestInvalidSkills:
    def test_skill_not_array(self):
        result = validate({"name": "X", "skills": {}})
        assert not result.valid

    def test_skill_wrong_type(self):
        result = validate({"name": "X", "skills": [False]})
        assert not result.valid

    def test_skill_missing_id(self):
        result = validate({"name": "X", "skills": [{"additional_text": "hi"}]})
        assert not result.valid

    def test_support_unknown_tag_in_additional_text(self):
        data = {
            "name": "X",
            "skills": [{
                "id": "Gem",
                "support_skills": [{"id": "Sup", "additional_text": "<unknowntag>{ text }"}],
            }],
        }
        result = validate(data)
        assert not result.valid
        assert any("unknown markup tag" in e.message for e in result.errors)

    def test_support_rgb_out_of_range(self):
        data = {
            "name": "X",
            "skills": [{
                "id": "Gem",
                "support_skills": [{"id": "Sup", "additional_text": "<rgb(300, 0, 0)>{ x }"}],
            }],
        }
        result = validate(data)
        assert not result.valid


# ---------------------------------------------------------------------------
# Invalid items
# ---------------------------------------------------------------------------

class TestInvalidItems:
    def test_items_not_array(self):
        result = validate({"name": "X", "items": "bad"})
        assert not result.valid

    def test_item_missing_inventory_id(self):
        result = validate({"name": "X", "items": [{"slot_x": 0}]})
        assert not result.valid
        assert any("inventory_id" in e.message for e in result.errors)

    def test_item_slot_x_wrong_type(self):
        result = validate({"name": "X", "items": [{"inventory_id": "Helm", "slot_x": "left"}]})
        assert not result.valid

    def test_item_level_interval_negative(self):
        result = validate({
            "name": "X",
            "items": [{"inventory_id": "Helm", "level_interval": [-1, 10]}],
        })
        assert not result.valid


# ---------------------------------------------------------------------------
# File-level errors
# ---------------------------------------------------------------------------

class TestFileErrors:
    def test_bad_fields_fixture(self):
        result = fixture("invalid_bad_fields.build")
        assert not result.valid
        # should catch multiple distinct errors
        assert len(result.errors) >= 4

    def test_nonexistent_file(self):
        result = load_build_file("does_not_exist.build")
        assert not result.valid
        assert any("cannot read file" in e.message for e in result.errors)

    def test_invalid_json(self, tmp_path):
        bad = tmp_path / "broken.build"
        bad.write_text("{name: oops}", encoding="utf-8")
        result = load_build_file(bad)
        assert not result.valid
        assert any("invalid JSON" in e.message for e in result.errors)


# ---------------------------------------------------------------------------
# parse() helper
# ---------------------------------------------------------------------------

class TestParse:
    def test_parse_minimal(self):
        build = parse({"name": "Quick"})
        assert build.name == "Quick"
        assert build.passives == []
        assert build.skills == []
        assert build.items == []

    def test_parse_full(self):
        import json
        data = json.loads((FIXTURES / "valid_full.build").read_text(encoding="utf-8"))
        build = parse(data)
        assert build.name == "Full Example Build"
        assert len(build.passives) == 2
        assert len(build.skills) == 2
        assert len(build.items) == 2
