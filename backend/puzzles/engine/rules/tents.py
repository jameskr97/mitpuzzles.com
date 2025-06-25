from typing import Optional

from puzzles.engine.games import PuzzleEngineBase
from puzzles.engine.rules.base import RuleDefinition, ValidationResult


def no_adjacent_tents() -> RuleDefinition:
    """
    Generate a rule to validate that no tent is adjacent to another tent.

    In Tents puzzle, tents cannot be placed in adjacent cells (including diagonally).

    :return: A rule function that validates tent adjacency constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        from puzzles.engine.games.tents import TentCellStates

        state = engine.board_state
        rows, cols = engine.rows, engine.cols
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        violating_cells = []

        for r in range(rows):
            for c in range(cols):
                if state[r * cols + c] != TentCellStates.Tent:
                    continue

                # Check all adjacent cells for other tents
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if state[nr * cols + nc] == TentCellStates.Tent:
                            violating_cells.append({"row": r, "col": c})
                            break  # Only add this tent once, even if multiple adjacent tents

        if not violating_cells:
            return None

        return ValidationResult(locations=violating_cells, rule_type="tents_intersecting")

    return RuleDefinition(rule)


def validate_tent_counts(axis: str) -> RuleDefinition:
    """
    Generate a rule to validate that the number of tents in each row/column
    doesn't exceed the target count for that row/column.

    :param axis: Either "row" or "col" to specify which axis to validate
    :return: A rule function that validates tent count constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        from puzzles.engine.games.tents import TentCellStates

        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        violating_lines = []

        if axis == "row":
            targets = engine.puzzle_definition.meta["row_tent_counts"]
            for r in range(rows):
                tent_count = sum(1 for c in range(cols) if state[r * cols + c] == TentCellStates.Tent)
                if tent_count > targets[r]:
                    violating_lines.append({"row": r, "col": -1})

        elif axis == "col":
            targets = engine.puzzle_definition.meta["col_tent_counts"]
            for c in range(cols):
                tent_count = sum(1 for r in range(rows) if state[r * cols + c] == TentCellStates.Tent)
                if tent_count > targets[c]:
                    violating_lines.append({"row": -1, "col": c})

        if not violating_lines:
            return None

        return ValidationResult(locations=violating_lines, rule_type=f"tent_count_{axis}_mismatch")

    return RuleDefinition(rule)


def validate_trees_have_tent_access() -> RuleDefinition:
    """
    Generate a rule to validate that trees can still have at least one adjacent tent.

    Checks if any tree has no adjacent tent AND cannot get one because all adjacent
    cells are either Green (marked as no-tent) or Trees (immutable).

    :return: A rule function that validates tree accessibility constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        from puzzles.engine.games.tents import TentCellStates

        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        # Only 4 cardinal directions for tent-tree adjacency
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        violating_trees = []

        for r in range(rows):
            for c in range(cols):
                if state[r * cols + c] != TentCellStates.Tree:
                    continue

                # Check if this tree already has an adjacent tent
                has_adjacent_tent = False
                can_place_tent = False

                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        adjacent_cell = state[nr * cols + nc]
                        if adjacent_cell == TentCellStates.Tent:
                            has_adjacent_tent = True
                            break
                        elif adjacent_cell == TentCellStates.Empty:
                            # Only Empty cells can become tents
                            can_place_tent = True

                # Flag as violation if tree has no adjacent tent AND all non-tent adjacent cells
                # are either Green or Tree (i.e., cannot place a tent)
                if not has_adjacent_tent and not can_place_tent:
                    violating_trees.append({"row": r, "col": c})

        if not violating_trees:
            return None

        return ValidationResult(locations=violating_trees, rule_type="tree_inaccessible")

    return RuleDefinition(rule)
