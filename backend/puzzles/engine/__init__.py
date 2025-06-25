from puzzles.engine.games import PuzzleEngineBase, MinesweeperEngine, TentsEngine, SudokuEngine, LightupEngine
from puzzles.engine.games.kakurasu import KakurasuEngine

PUZZLE_TYPE_TO_ENGINE_MAP: dict[str, type[PuzzleEngineBase]] = {
    "kakurasu": KakurasuEngine,
    "minesweeper": MinesweeperEngine,
    "tents": TentsEngine,
    "sudoku": SudokuEngine,
    "lightup": LightupEngine,
}
