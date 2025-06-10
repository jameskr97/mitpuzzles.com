import typing
from abc import ABC

if typing.TYPE_CHECKING:
    from puzzles.engine.games import PuzzleEngineBase


# noinspection PyMethodMayBeStatic
class InputHandler(ABC):
    def on_cell_click(self, engine: "PuzzleEngineBase", row: int, col: int, button: int, desired_state=None) -> bool: return False
    def on_row_click(self, engine: "PuzzleEngineBase", row: int, button: int) -> bool: return False
    def on_col_click(self, engine: "PuzzleEngineBase", col: int, button: int) -> bool: return False

