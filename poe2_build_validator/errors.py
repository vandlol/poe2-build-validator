from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationError:
    path: str        # JSON-path style location, e.g. "passives[2].id"
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, path: str, message: str) -> None:
        self.errors.append(ValidationError(path, message))

    def __str__(self) -> str:
        if self.valid:
            return "Build is valid."
        lines = [f"Build has {len(self.errors)} error(s):"]
        lines += [f"  - {e}" for e in self.errors]
        return "\n".join(lines)
