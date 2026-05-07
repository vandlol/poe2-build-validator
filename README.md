# poe2-build-validator

Validates Path of Exile 2 `.build` files against the [official Build Planner spec](https://www.pathofexile.com/developer/docs/game#buildplanner).

## Installation

```bash
pip install -e .
```

No external dependencies — stdlib only, Python 3.10+.

## Usage

### From Python

```python
from poe2_build_validator import load_build_file, validate

# Validate a file on disk
result = load_build_file("MyBuild.build")
if result.valid:
    print("Build is valid.")
else:
    print(result)  # lists every error with its JSON-path location

# Validate already-parsed data
import json
data = json.loads(raw_text)
result = validate(data)
for error in result.errors:
    print(f"{error.path}: {error.message}")
```

### Parse into typed models

Call `parse()` after validation passes to get a fully typed `Build` object:

```python
from poe2_build_validator.validator import parse

if result.valid:
    build = parse(data)
    print(build.name)
    print(build.passives)   # list of str | BuildPassive
    print(build.skills)     # list of str | BuildSkill
    print(build.items)      # list of BuildItem
```

## What gets validated

| Rule | Details |
|---|---|
| `name` required | Must be a non-empty string |
| Field types | Every field is type-checked against the spec |
| `level_interval` | Exactly 2 non-negative integers, `min <= max` |
| `weapon_set` | Unsigned integer (>= 0) |
| `additional_text` markup | Only `<bold>`, `<italics>`, `<red>`, `<rgb(r,g,b)>` tags allowed; RGB components must be 0–255 |
| Mixed arrays | `passives` and `skills` accept bare ID strings or full objects |
| Unknown fields | Flagged at every level of nesting |
| File errors | Missing file and invalid JSON are reported as validation errors |

## .build file format

`.build` files are JSON documents placed in:

```
Documents\My Games\Path of Exile 2\BuildPlanner\
```

Minimal valid example:

```json
{
  "name": "My Build"
}
```

Full example:

```json
{
  "name": "Storm Weaver",
  "description": "Arc with spell echo",
  "ascendancy": "Stormweaver",
  "passives": [
    "PassiveNode_001",
    {
      "id": "PassiveNode_Keystone",
      "level_interval": [1, 50],
      "weapon_set": 0,
      "additional_text": "<bold>{ Allocate early }"
    }
  ],
  "skills": [
    {
      "id": "GemId_Arc",
      "level_interval": [12, 100],
      "support_skills": [
        "GemId_AddedLightning",
        { "id": "GemId_SpellEcho", "level_interval": [18, 100] }
      ]
    }
  ],
  "items": [
    {
      "inventory_id": "Weapon",
      "slot_x": 0,
      "slot_y": 0,
      "unique_name": "Doomfletch"
    }
  ]
}
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## Licence

MIT
