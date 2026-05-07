"""
Dataclass representations of every object in the PoE2 Build Planner spec.

All fields mirror the official developer documentation exactly.
Optional fields default to None so callers can omit them entirely.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Level interval helper
# ---------------------------------------------------------------------------

LevelInterval = tuple[int, int]  # [min_level, max_level], both inclusive


# ---------------------------------------------------------------------------
# Support gem inside a skill
# ---------------------------------------------------------------------------

@dataclass
class BuildSupport:
    id: str
    level_interval: LevelInterval | None = None
    additional_text: str | None = None


# ---------------------------------------------------------------------------
# Active skill gem
# ---------------------------------------------------------------------------

@dataclass
class BuildSkill:
    id: str
    level_interval: LevelInterval | None = None
    additional_text: str | None = None
    # Each entry is either a bare BaseItemTypes ID string or a BuildSupport
    support_skills: list[str | BuildSupport] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Passive skill tree node
# ---------------------------------------------------------------------------

@dataclass
class BuildPassive:
    id: str
    level_interval: LevelInterval | None = None
    weapon_set: int | None = None          # uint — must be >= 0
    additional_text: str | None = None


# ---------------------------------------------------------------------------
# Inventory item hint
# ---------------------------------------------------------------------------

@dataclass
class BuildItem:
    inventory_id: str
    slot_x: int | None = None
    slot_y: int | None = None
    level_interval: LevelInterval | None = None
    unique_name: str | None = None
    additional_text: str | None = None


# ---------------------------------------------------------------------------
# Root build object
# ---------------------------------------------------------------------------

@dataclass
class Build:
    name: str                                           # required
    description: str | None = None
    ascendancy: str | None = None
    # Each entry is either a bare PassiveSkills ID string or a BuildPassive
    passives: list[str | BuildPassive] = field(default_factory=list)
    # Each entry is either a bare BaseItemTypes ID string or a BuildSkill
    skills: list[str | BuildSkill] = field(default_factory=list)
    items: list[BuildItem] = field(default_factory=list)
