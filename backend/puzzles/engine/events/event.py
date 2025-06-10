import typing
from typing import Any, Dict, Optional
from dataclasses import dataclass
import time

if typing.TYPE_CHECKING:
    from puzzles.engine.consumer import PuzzleConsumer


@dataclass
class Event:
    """event container for pub/sub system"""

    type: str
    data: Dict[str, Any]
    session_id: Optional[str] = None
    consumer: "PuzzleConsumer" = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def get_command(self, prefix: str = "cmd:") -> str:
        """Extract command from event type"""
        if self.type.startswith(prefix):
            return self.type[len(prefix) :]
        return ""
