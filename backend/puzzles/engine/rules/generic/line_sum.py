from typing import Optional

from puzzles.engine.games import PuzzleEngineBase
from puzzles.engine.rules.base import RuleDefinition, ValidationResult


def validate_line_sums(axis: str, target_value: int, targets_key: str, weighted: bool = False) -> RuleDefinition:
    """
    Generate a rule to validate that the sum/count of specific values in each row/column
    doesn't exceed the target for that row/column.

    :param axis: Either "row" or "col" to specify which axis to validate
    :param target_value: The cell value to count/sum (e.g., TentCellStates.Tent)
    :param targets_key: Key in puzzle_definition.meta containing the target values (e.g., "row_tent_counts")
    :param weighted: If True, multiply each target_value by its 1-based position in the line
    :return: A rule function that validates line sum/count constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        violating_lines = []

        if axis == "row":
            targets = engine.puzzle_definition.meta[targets_key]
            for r in range(rows):
                if weighted:
                    total = sum((c + 1) for c in range(cols) if state[r * cols + c] == target_value)
                else:
                    total = sum(1 for c in range(cols) if state[r * cols + c] == target_value)

                if total > targets[r]:
                    violating_lines.append({"row": r, "col": -1})

        elif axis == "col":
            targets = engine.puzzle_definition.meta[targets_key]
            for c in range(cols):
                if weighted:
                    total = sum((r + 1) for r in range(rows) if state[r * cols + c] == target_value)
                else:
                    total = sum(1 for r in range(rows) if state[r * cols + c] == target_value)

                if total > targets[c]:
                    violating_lines.append({"row": -1, "col": c})

        if not violating_lines:
            return None

        return ValidationResult(locations=violating_lines, rule_type=f"line_sum_{axis}_exceeded")

    return RuleDefinition(rule)


def validate_line_sums_exceeded(
    axis: str, positive_value: int, targets_key: str, weighted: bool = False
) -> RuleDefinition:
    """
    Generate a rule to validate that positive values don't exceed the target in each line.

    :param axis: Either "row" or "col" to specify which axis to validate
    :param positive_value: The cell value that contributes to the sum (e.g., TentCellStates.Tent)
    :param targets_key: Key in puzzle_definition.meta containing the target values
    :param weighted: If True, multiply each positive_value by its 1-based position in the line
    :return: A rule function that validates line sum exceeded constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        # Helper function to calculate sum for a line
        def calculate_line_sum(line_cells, condition_func):
            return sum((idx + 1) if weighted else 1 for idx, cell in enumerate(line_cells) if condition_func(cell))

        violating_lines = []

        if axis == "row":
            targets = engine.puzzle_definition.meta[targets_key]
            for r in range(rows):
                row_cells = [state[r * cols + c] for c in range(cols)]
                positive_total = calculate_line_sum(row_cells, lambda cell: cell == positive_value)

                if positive_total > targets[r]:
                    violating_lines.append({"row": r, "col": -1})

        elif axis == "col":
            targets = engine.puzzle_definition.meta[targets_key]
            for c in range(cols):
                col_cells = [state[r * cols + c] for r in range(rows)]
                positive_total = calculate_line_sum(col_cells, lambda cell: cell == positive_value)

                if positive_total > targets[c]:
                    violating_lines.append({"row": -1, "col": c})

        if not violating_lines:
            return None

        return ValidationResult(locations=violating_lines, rule_type=f"line_sum_{axis}_exceeded")

    return RuleDefinition(rule)


def validate_line_all_negative(
    axis: str, negative_value: int, targets_key: str, ignored_values: list = None
) -> RuleDefinition:
    """
    Generate a rule to validate that lines aren't completely filled with negative values
    when the target is not zero.

    :param axis: Either "row" or "col" to specify which axis to validate
    :param negative_value: The cell value that marks "not positive" (e.g., TentCellStates.Green)
    :param targets_key: Key in puzzle_definition.meta containing the target values
    :param ignored_values: Optional list of cell values to ignore in the calculation (e.g., [TentCellStates.Tree])
    :return: A rule function that validates all-negative line constraints
    """
    if ignored_values is None:
        ignored_values = []

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        state = engine.board_state
        rows, cols = engine.rows, engine.cols
        violating_lines = []

        if axis == "row":
            targets = engine.puzzle_definition.meta[targets_key]
            for r in range(rows):
                row_cells = [state[r * cols + c] for c in range(cols)]

                # Filter out ignored values
                relevant_cells = [cell for cell in row_cells if cell not in ignored_values]

                # Check if all relevant cells are negative and target is not zero
                if relevant_cells:  # Only check if there are relevant cells
                    all_negative = all(cell == negative_value for cell in relevant_cells)
                    if all_negative and targets[r] > 0:
                        violating_lines.append({"row": r, "col": -1})

        elif axis == "col":
            targets = engine.puzzle_definition.meta[targets_key]
            for c in range(cols):
                col_cells = [state[r * cols + c] for r in range(rows)]

                # Filter out ignored values
                relevant_cells = [cell for cell in col_cells if cell not in ignored_values]

                # Check if all relevant cells are negative and target is not zero
                if relevant_cells:  # Only check if there are relevant cells
                    all_negative = all(cell == negative_value for cell in relevant_cells)
                    if all_negative and targets[c] > 0:
                        violating_lines.append({"row": -1, "col": c})

        if not violating_lines:
            return None

        return ValidationResult(locations=violating_lines, rule_type=f"line_all_{axis}_negative")

    return RuleDefinition(rule)
