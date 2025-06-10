import typing
from typing import Optional

from puzzles.engine.games import PuzzleEngineBase
from puzzles.engine.rules.base import ValidationResult, RuleDefinition


def numbered_cell_flag_validator() -> RuleDefinition:
    """
    Generate a rule to validate that numbered cells don't have more surrounding flags
    than their number indicates.

    For minesweeper: checks that cells with numbers (1-8) don't have more flags
    around them than the number specifies.

    :return: A rule function that validates flag counts around numbered cells
    """
    from puzzles.engine.games.minesweeper import CellStatesMinesweeper

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.get_board_state()
        rows, cols = engine.rows, engine.cols

        # All 8 directions (including diagonals) for minesweeper
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        violating_number_locations = []

        for r in range(rows):
            for c in range(cols):
                cell_value = state[r * cols + c]

                # Skip if not a numbered cell (assuming numbers are 1-8)
                if not isinstance(cell_value, int) or cell_value < 1 or cell_value > 8:
                    continue

                # Count surrounding flags
                flag_count = 0
                for dr, dc in directions:
                    nr = r + dc
                    nc = c + dr
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if state[nr * cols + nc] == CellStatesMinesweeper.FLAG:
                            flag_count += 1

                # Check if too many flags
                if flag_count > cell_value:
                    violating_number_locations.append({"row": r, "col": c})

        if not violating_number_locations:
            return None

        return ValidationResult(
            locations=violating_number_locations,
            rule_type="minesweeper_surrounding_flag_violation",
        )

    return RuleDefinition(rule)
