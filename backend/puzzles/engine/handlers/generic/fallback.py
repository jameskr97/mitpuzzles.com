import typing

from puzzles.engine.handlers.interface import InputHandler

if typing.TYPE_CHECKING:
    from puzzles.engine.games import PuzzleEngineBase

class FallbackInputHandler(InputHandler):
    def on_cell_click(self, engine: "PuzzleEngineBase", row: int, col: int, button: int, desired_state=None) -> bool:
        print(f"[Fallback] Unhandled cell click: ({row}, {col}) button={button}")
        return False

    def on_row_click(self, engine: "PuzzleEngineBase", row: int, button: int) -> bool:
        print(f"[Fallback] Unhandled row click: {row}, button={button}")
        return False

    def on_col_click(self, engine: "PuzzleEngineBase", col: int, button: int) -> bool:
        print(f"[Fallback] Unhandled col click: {col}, button={button}")
        return False
