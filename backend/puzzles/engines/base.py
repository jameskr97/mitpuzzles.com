# puzzles/engines/base.py
import typing
from enum import Enum
from typing import Any, Dict, List, Type

from puzzles.converters import get_translation_dict, game_state_to_string
from puzzles.engines.ops import PuzzleOps

if typing.TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession

Move = Dict[str, Any]  # {"row": 3, "col": 4, "button": 0}
RawState = str  # "0 1 2 3 4 5 6 7 8"
State = List[int]  # flat row-major board
PuzzleData = Dict[str, Any]  # generator output


class PuzzleEngineBase:
    class StateCycleDirection:
        FORWARD = 0
        BACKWARD = 1

    def __init__(self, puzzle_session, allowed_states: Type[Enum] | List | None = None) -> None:
        self.puzzle_data = puzzle_session.puzzle.puzzle_data
        self.rows: int = self.puzzle_data.get("rows", self.puzzle_data.get("length", self.puzzle_data.get("n_rows", 0)))
        self.cols: int = self.puzzle_data.get("cols", self.puzzle_data.get("width", self.puzzle_data.get("n_cols", 0)))
        self.puzzle_session: "ActivePuzzleSession" = puzzle_session
        self.allowed_states: List[int] = [t.value for t in allowed_states] if allowed_states else []
        self.translation_dict = get_translation_dict(puzzle_session.puzzle.puzzle_type)

    def get_initial_board_string(self):
        """Convert game_state to string format"""
        return game_state_to_string(self.puzzle_data["game_state"], self.translation_dict)

    def get_solution_board_string(self):
        """Convert game_board (solution) to string format"""
        return game_state_to_string(self.puzzle_data["game_board"], self.translation_dict)

    def create_game_state(self) -> State:
        # Convert game_state to string format and then to our internal format
        initial_state_string = self.get_initial_board_string()

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

    def save_active_puzzle(self):
        """
        Save the current board state to the database.
        @param session: The ActivePuzzleSession instance.
        """
        self.puzzle_session.save()

    def _cycle(self, index: int, direction: StateCycleDirection = StateCycleDirection.FORWARD) -> int:
        """
        Cycles the current state to the next one in the allowed states.
        If the current state is not in the allowed states, it returns the first one.
        """
        current_state = self.puzzle_session.board_state[index]
        try:
            pos = self.allowed_states.index(current_state)
        except ValueError:
            return self.allowed_states.index(0)

        step = 1 if direction == PuzzleEngineBase.StateCycleDirection.FORWARD else -1
        return self.allowed_states[(pos + step) % len(self.allowed_states)]

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return True

    # Board Actions
    def board_clear(self):
        """
        Clears the board by setting all cells to the default state.
        """
        self.puzzle_session.board_state = self.create_game_state()
        self.save_active_puzzle()

    # User Event Handlers
    def on_cell_click(self, row: int, col: int, button: str = "left", desired_state=None) -> bool:
        if not self.can_modify_cell(self.puzzle_session.board_state, row, col):
            return False

        if desired_state is not None:
            if desired_state not in self.allowed_states:
                return False
            PuzzleOps.set_cell_state(self.puzzle_session.board_state, row, col, self.cols, desired_state)
            return True

        cycle = PuzzleEngineBase.StateCycleDirection.FORWARD
        if button == "right":
            cycle = PuzzleEngineBase.StateCycleDirection.BACKWARD

        PuzzleOps.cycle_cell(
            self.puzzle_session.board_state,
            row,
            col,
            self.cols,
            self.allowed_states,
            cycle,
        )
        return True

    def on_row_click(self, row: int) -> bool:
        return False

    def on_col_click(self, col: int) -> bool:
        return False

    def on_border_click(self, row: int, col: int, direction: str) -> bool:
        return False

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

    def handle_input_event(self, event_data: dict) -> bool:
        target = event_data.get("target")
        action = event_data.get("action")
        row = event_data["position"].get("row")
        col = event_data["position"].get("col")
        button = event_data["position"].get("button", "left")
        state = event_data["position"].get("state", None)
        zone = event_data["position"].get("zone", None)

        match (target, action, zone):
            case ("cell", "click", "game"):
                return self.on_cell_click(row, col, button, state)
            case ("cell", "click", "leftGutter"):
                return self.on_row_click(row)
            case ("cell", "click", "topGutter"):
                return self.on_col_click(col)

        return False

    def get_board_state(self) -> State:
        return self.puzzle_session.board_state

    def serialize_gamedata(self) -> dict:
        raise NotImplementedError("serialize_gamedata() must be implemented in subclasses")

    def format_game_update(self) -> dict:
        return {
            "type": "game.update",
            "puzzle_session_id": str(self.puzzle_session.id),
            "game_data": self.serialize_gamedata(),
        }
