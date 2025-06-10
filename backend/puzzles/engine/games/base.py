import typing
from typing import Any, Dict, List, Type, Iterable, Callable

from django.conf import settings

from puzzles.converters import get_translation_dict, game_state_to_string
from puzzles.engine.handlers.interface import InputHandler
from puzzles.engine.handlers.generic.fallback import FallbackInputHandler
from puzzles.engine.rules.base import RuleDefinition, ValidationResult

if typing.TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

Move = Dict[str, Any]  # {"row": 3, "col": 4, "button": 0}
RawState = str  # "0 1 2 3 4 5 6 7 8"
State = List[int]  # flat row-major board
PuzzleData = Dict[str, Any]  # generator output

def save_after_exec(func):
    """Decorator to save the puzzle session after executing a method."""
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.puzzle_session.save()
        return result
    return wrapper

class PuzzleEngineBase:

    def __init__(self,
                 puzzle_session,
                 input_handler: InputHandler | List[InputHandler] = None,
                 extra_gamedata_fields: list[str] | dict[str, str] = None,
                 validation_constraints: RuleDefinition | List[RuleDefinition] = None) -> None:
        self.puzzle_data = puzzle_session.puzzle.puzzle_data
        self.rows: int = self.puzzle_data.get("rows", self.puzzle_data.get("length", self.puzzle_data.get("n_rows", 0)))
        self.cols: int = self.puzzle_data.get("cols", self.puzzle_data.get("width", self.puzzle_data.get("n_cols", 0)))
        self.puzzle_session: "ActivePuzzleSession" = puzzle_session
        self.translation_dict = get_translation_dict(puzzle_session.puzzle.puzzle_type)
        self.extra_gamedata_fields = extra_gamedata_fields
        self.validation_constraints = validation_constraints

        if isinstance(input_handler, Iterable) and not isinstance(input_handler, InputHandler):
            self.input_handlers = list(input_handler)
        else:
            self.input_handlers = [input_handler]

        if settings.DEBUG:
            self.input_handlers.append(FallbackInputHandler())

    #############################################################################
    ### Input Handling
    def _dispatch_to_handlers(self, method_name: str, *args, **kwargs) -> bool:
        for handler in self.input_handlers:
            method = getattr(handler, method_name, None)
            if method and method(*args, **kwargs):
                return True
        return False

    def handle_input_event(self, event_data: dict) -> bool:
        target = event_data.get("target")
        action = event_data.get("action")
        row = event_data["position"].get("row")
        col = event_data["position"].get("col")
        button = event_data["position"].get("button", "left")
        state = event_data["position"].get("state", None)
        zone = event_data["position"].get("zone", None)

        # don't pass through if the cell is not meant to be modified
        # TODO: store non-modifiable classes on the frontend to prevent us from even seeing this request
        if not self.can_modify_cell(self.puzzle_session.board_state, row, col) and zone == "game":
            return False

        match (target, action, zone):
            case ("cell", "click", "game"):
                return self._dispatch_to_handlers("on_cell_click", self, row, col, button, state)
            case ("cell", "click", "leftGutter"):
                return self._dispatch_to_handlers("on_row_click", self,row, button)
            case ("cell", "click", "topGutter"):
                return self._dispatch_to_handlers("on_col_click",self, col, button)
        return False

    #############################################################################
    ### Board Translation and State Management
    def get_initial_board_string(self):
        """Convert game_state to string format"""
        return game_state_to_string(self.puzzle_data["game_state"], self.translation_dict)

    def get_solution_board_string(self):
        """Convert game_board (solution) to string format"""
        return game_state_to_string(self.puzzle_data["game_board"], self.translation_dict)

    def create_game_state(self) -> State:
        # Convert game_state to string format and then to our internal format
        initial_state_string = self.get_initial_board_string()
        return initial_state_string
        # Convert each character in the string to the appropriate type
        # For most puzzles, this will be integers, but some might use other characters
        result = []
        for char in initial_state_string:
            if char.isdigit():
                result.append(int(char))
            else:
                # For non-numeric states (like "." or "L" in some puzzles)
                result.append(char)
        return result

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return False

    # Board Actions
    @save_after_exec
    def board_clear(self):
        self.puzzle_session.board_state = self.create_game_state()
        self.puzzle_session.save()

    def is_solved(self, strict=False) -> bool:
        """
        Check if the puzzle is solved.
        :param strict: If strict is True, check if the board state matches the solution exactly.
                       If not strict, only the positive state cells must be checked.
                       - (in kakurasu, the black cells)
                       - (in minesweeper, the flagged cells)
                       - (in lightup, the bulbs)
        :return:
        """
        return False

    def get_board_state(self) -> State:
        return self.puzzle_session.board_state

    def serialize_gamedata(self) -> dict:
        res = {
            "rows": self.rows,
            "cols": self.cols,
            "board": self.get_board_state(),
            "board_initial": self.get_initial_board_string(),
        }

        # Add additional fields if specified
        # if we were given a dictionary, we will use the keys as source keys and values as output keys
        # if we were given a list, we will use the list items as input + output keys
        if self.extra_gamedata_fields:
            if isinstance(self.extra_gamedata_fields, dict):
                for source_key, output_key in self.extra_gamedata_fields.items():
                    if source_key in self.puzzle_data:
                        res[output_key] = self.puzzle_data[source_key]
                    else:
                        raise ValueError(f"Field '{source_key}' not found in puzzle data.")
            elif isinstance(self.extra_gamedata_fields, list):
                for field in self.extra_gamedata_fields:
                    if field in self.puzzle_data:
                        res[field] = self.puzzle_data[field]
                    else:
                        raise ValueError(f"Field '{field}' not found in puzzle data.")
        return res

    def format_game_update(self) -> dict:
        return {
            "type": "game.update",
            "puzzle_session_id": str(self.puzzle_session.id),
            "game_data": self.serialize_gamedata(),
        }

    def validate(self) -> list[ValidationResult]:
        """
        Run all validation rules and return a list of error messages.
        An empty list means the board is valid.
        """
        if not self.validation_constraints:
            return []
        results = []
        for rule_def in self.validation_constraints:
            result = rule_def.rule_func(self)
            if result:
                results.append(result)
        return results
