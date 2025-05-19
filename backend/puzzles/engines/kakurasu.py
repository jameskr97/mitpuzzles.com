from enum import IntEnum
from typing import TYPE_CHECKING

from puzzles.engines.base import PuzzleEngineBase, State

if TYPE_CHECKING:
    from puzzles.models import ActivePuzzleSession


class KakurasuCellStates(IntEnum):
    Empty = 0
    Filled = 1
    Crossed = 2


class KakurasuEngine(PuzzleEngineBase):
    def __init__(self, puzzle_session: "ActivePuzzleSession") -> None:
        super().__init__(
            puzzle_session,
            allowed_states=KakurasuCellStates,
        )

    def create_game_state(self, initial_state: str) -> list:
        """Create a new game state based on the puzzle data."""
        return [int(cell) for cell in list(initial_state)]

    def serialize_gamedata(self) -> dict:
        """
        Serialize the game data to a dictionary.
        This is used to send the game data to the client.
        """
        return {
            "rows": self.rows,
            "cols": self.cols,
            "row_sum": self.puzzle_data["row_sum"],
            "col_sum": self.puzzle_data["col_sum"],
            "board": self.puzzle_session.board_state,
        }

    def can_modify_cell(self, _state: State, row: int, col: int) -> bool:
        return True


    def is_solved(self, strict=False):
        """
        Checks if user input is valid against a solution.

        non-strict mode: all 1 in solution must match all 1 in input. no extra 1
            strict mode: non-strict + all 0 in solution must be marked as 2
        Args:
            strict (bool): Whether to use strict mode validation (default: False)
        Returns:
            bool: True if the input is valid, False otherwise
        """
        user_input = "".join(str(cell) for cell in self.puzzle_session.board_state)
        solution = self.puzzle_data["board_solution"]

        # ensure both strings have the same length
        if len(user_input) != len(solution):
            return False

        for i in range(len(solution)):
            # for both modes:
            # - All '1's in the solution must match with '1's in user input
            # - No extra '1's in user input where solution has '0'
            if solution[i] == "1" and user_input[i] != "1":
                return False

            if solution[i] == "0" and user_input[i] == "1":
                return False

            # for strict mode only:
            # - All '0's in the solution must be marked as '2' (Red Cross) in user input
            if strict and solution[i] == "0" and user_input[i] != "2":
                return False

        # If we passed all checks, the input is valid
        return True
