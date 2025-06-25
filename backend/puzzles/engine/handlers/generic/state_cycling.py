from typing import Union, Type, List
from enum import IntEnum

from puzzles.engine.games.base import InputHandler, PuzzleEngineBase
from puzzles.engine.games.ops import PuzzleOps


class StateCyclingInputHandler(InputHandler):
    class CycleDirection:
        FORWARD = 0
        BACKWARD = 1

    def __init__(self, allowed_states: Union[Type[IntEnum], List[int]] = None):
        """
        :param allowed_states: A list of numerical values to pass through (typically a list of specific enums value)
                               or an enum itself, when all possible values are allowed.
        """
        if isinstance(allowed_states, type) and issubclass(allowed_states, IntEnum):
            self.allowed_states: List[int] = [e.value for e in allowed_states]
        elif isinstance(allowed_states, list):
            self.allowed_states: List[int] = [e.value if isinstance(e, IntEnum) else e for e in allowed_states]
        else:
            self.allowed_states: List[int] = allowed_states or []

    def on_cell_click(self, engine: PuzzleEngineBase, row: int, col: int, button: str = "left", desired_state=None) -> bool:
        board = engine.board_state

        # If a specific state is requested, don't cycle
        if desired_state is not None:
            if desired_state in self.allowed_states:
                PuzzleOps.set_cell_state(board, row, col, engine.cols, desired_state)
                return True
            return False

        cycle = StateCyclingInputHandler.CycleDirection.FORWARD
        if button == 2:
            cycle = StateCyclingInputHandler.CycleDirection.BACKWARD
        PuzzleOps.cycle_cell(board, row, col, engine.cols, self.allowed_states, cycle)
        return True
