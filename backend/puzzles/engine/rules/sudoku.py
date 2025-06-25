from typing import Optional

from puzzles.engine.games import PuzzleEngineBase
from puzzles.engine.rules.base import ValidationResult, RuleDefinition


def no_duplicate_numbers_in_rows() -> RuleDefinition:
    """
    Generate a rule to validate that no number appears more than once in any row.

    :return: A rule function that validates row uniqueness constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        violating_cells = []

        for r in range(rows):
            seen = {}
            for c in range(cols):
                value = state[r * cols + c]

                # Skip empty cells (assuming 0 or similar represents empty)
                if value == 0 or value is None:
                    continue

                if value in seen:
                    # Mark both the original and duplicate cells as violations
                    violating_cells.append({"row": r, "col": seen[value]})
                    violating_cells.append({"row": r, "col": c})
                else:
                    seen[value] = c

        if not violating_cells:
            return None

        return ValidationResult(locations=violating_cells, rule_type="row_duplicate_violation")

    return RuleDefinition(rule)


def no_duplicate_numbers_in_cols() -> RuleDefinition:
    """
    Generate a rule to validate that no number appears more than once in any column.

    :return: A rule function that validates column uniqueness constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        violating_cells = []

        for c in range(cols):
            seen = {}
            for r in range(rows):
                value = state[r * cols + c]

                # Skip empty cells (assuming 0 or similar represents empty)
                if value == 0 or value is None:
                    continue

                if value in seen:
                    # Mark both the original and duplicate cells as violations
                    violating_cells.append({"row": seen[value], "col": c})
                    violating_cells.append({"row": r, "col": c})
                else:
                    seen[value] = r

        if not violating_cells:
            return None

        return ValidationResult(locations=violating_cells, rule_type="col_duplicate_violation")

    return RuleDefinition(rule)


def no_duplicate_numbers_in_boxes() -> RuleDefinition:
    """
    Generate a rule to validate that no number appears more than once in any box.
    Automatically determines box size as square root of board side length.
    Works with 4x4 (2x2 boxes) and 9x9 (3x3 boxes) Sudoku boards.

    :return: A rule function that validates box uniqueness constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        # Calculate box size as square root of board side length
        import math

        box_size = int(math.sqrt(rows))

        violating_cells = []

        # Iterate through each box
        for box_row in range(0, rows, box_size):
            for box_col in range(0, cols, box_size):
                seen = {}

                # Check all cells in this box
                for r in range(box_row, min(box_row + box_size, rows)):
                    for c in range(box_col, min(box_col + box_size, cols)):
                        value = state[r * cols + c]

                        # Skip empty cells (assuming 0 or similar represents empty)
                        if value == 0 or value is None:
                            continue

                        if value in seen:
                            # Mark both the original and duplicate cells as violations
                            violating_cells.append(seen[value])
                            violating_cells.append({"row": r, "col": c})
                        else:
                            seen[value] = {"row": r, "col": c}

        if not violating_cells:
            return None

        return ValidationResult(locations=violating_cells, rule_type="box_duplicate_violation")

    return RuleDefinition(rule)
