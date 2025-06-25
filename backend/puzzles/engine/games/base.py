import typing
from typing import Any, Dict, List, Iterable

from puzzles.abstract import PuzzleDefinition
from puzzles.converters import get_translation_dict, game_state_to_string
from puzzles.engine.handlers.generic.fallback import FallbackInputHandler
from puzzles.engine.handlers.interface import InputHandler
from puzzles.engine.rules.base import RuleDefinition, ValidationResult

if typing.TYPE_CHECKING:
    pass

Move = Dict[str, Any]  # {"row": 3, "col": 4, "button": 0}
RawState = str  # "0 1 2 3 4 5 6 7 8"
State = List[int]  # flat row-major board
PuzzleData = Dict[str, Any]  # generator output

class PuzzleEngineBase:
    """
    Pure-Python game engine.  **No Django imports allowed.**
    """

    def __init__(self,
                 definition: PuzzleDefinition,
                 board_state: State,
                 input_handler: InputHandler | List[InputHandler] = None,
                 extra_gamedata_fields: list[str] | dict[str, str] = None,
                 validation_constraints: RuleDefinition | List[RuleDefinition] = None,
                 debug: bool = False) -> None:
        self.puzzle_definition: PuzzleDefinition = definition
        self.board_state: State = board_state
        self.rows: int = self.puzzle_definition.rows
        self.cols: int = self.puzzle_definition.cols
        self.translation_dict = get_translation_dict(self.puzzle_definition.type)
        self.extra_gamedata_fields = extra_gamedata_fields
        self.validation_constraints = validation_constraints
        self.tutorial_mode: bool = False
        self.__initial_state = self.get_initial_board_string()

        if not self.board_state:
            self.board_state = self.__initial_state.copy()

        if isinstance(input_handler, Iterable) and not isinstance(input_handler, InputHandler):
            self.input_handlers = list(input_handler)
        else:
            self.input_handlers = [input_handler]

        if debug:
            self.input_handlers.append(FallbackInputHandler())
        self.input_handlers = [h for h in self.input_handlers if h]

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

        # TODO: store non-modifiable classes on the frontend to prevent us from even seeing this request
        if not self.can_modify_cell(self.board_state, row, col) and zone == "game":
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
        return game_state_to_string(self.puzzle_definition.initial_state, self.translation_dict)

    def get_solution_board_string(self):
        return game_state_to_string(self.puzzle_definition.solution_state, self.translation_dict)

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return False

    def get_immutable_cells(self) -> list[int]:
        """Return [1 if cell is immutable, 0 if modifiable]"""
        result = []
        for r in range(self.rows):
            for c in range(self.cols):
                can_edit = self.can_modify_cell(self.board_state, r, c)
                result.append(0 if can_edit else 1)
        return result

    # Board Actions
    def board_clear(self):
        if self.board_state == self.__initial_state:
            return False # do nothing, board is in initial state
        self.board_state = self.__initial_state.copy()
        return True

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

    def serialize_gamedata(self) -> dict:
        res = {
            "immutable": self.get_immutable_cells(),
            "tutorial_mode": self.tutorial_mode,
            "board_initial": self.get_initial_board_string(),
        }

        # Add additional fields if specified
        # if we were given a dictionary, we will use the keys as source keys and values as output keys
        # if we were given a list, we will use the list items as input + output keys
        if self.extra_gamedata_fields:
            if isinstance(self.extra_gamedata_fields, dict):
                for source_key, output_key in self.extra_gamedata_fields.items():
                    if source_key in self.puzzle_definition.meta:
                        res[output_key] = self.puzzle_definition.meta[source_key]
                    else:
                        raise ValueError(f"Field '{source_key}' not found in puzzle data.")
            elif isinstance(self.extra_gamedata_fields, list):
                for field in self.extra_gamedata_fields:
                    if field in self.puzzle_definition.meta:
                        res[field] = self.puzzle_definition.meta[field]
                    else:
                        raise ValueError(f"Field '{field}' not found in puzzle data.")
        return res


    def validate(self) -> list[ValidationResult]:
        """
        Run all validation rules and return a list of error messages.
        An empty list means the board is valid.
        """
        if not self.validation_constraints or self.tutorial_mode == False:
            return []
        results = []
        for rule_def in self.validation_constraints:
            result = rule_def.rule_func(self)
            if result:
                results.append(result)
        return results
