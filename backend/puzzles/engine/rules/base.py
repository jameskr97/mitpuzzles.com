import typing
from dataclasses import dataclass, field
from typing import NamedTuple, Optional, Any, Dict, Callable

if typing.TYPE_CHECKING:
    from puzzles.engine.games import PuzzleEngineBase


@dataclass
class ValidationResult:
    locations: Any
    rule_type: str

    def to_dict(self):
        return {
            "locations": list(self.locations),  # Convert set to list
            "rule_type": self.rule_type,
        }

class RuleDefinition(NamedTuple):
    rule_func: Callable[["PuzzleEngineBase"], Optional[ValidationResult]]
