from typing import Optional

from puzzles.engine.games import PuzzleEngineBase
from puzzles.engine.rules.base import RuleDefinition, ValidationResult


def no_bulbs_lighting_each_other() -> RuleDefinition:
    """
    Generate a rule to validate that no two bulbs can see each other in Light Up.

    In Light Up, bulbs shine light in all four cardinal directions until they hit
    a wall (black cell). No two bulbs should be able to see each other.

    :return: A rule function that validates bulb visibility constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        from puzzles.engine.games.lightup import LightupCellStates

        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        # Wall values from LightupCellStates enum
        wall_values = {
            LightupCellStates.Wall0,
            LightupCellStates.Wall1,
            LightupCellStates.Wall2,
            LightupCellStates.Wall3,
            LightupCellStates.Wall4,
            LightupCellStates.WallBlack,
        }

        # Find all bulbs
        bulbs = []
        for r in range(rows):
            for c in range(cols):
                if state[r * cols + c] == LightupCellStates.Bulb:
                    bulbs.append((r, c))

        violating_bulbs_set = set()

        # Check each bulb against all others
        for i, (r1, c1) in enumerate(bulbs):
            for j, (r2, c2) in enumerate(bulbs):
                if i >= j:  # Avoid checking same pair twice
                    continue

                # Check if bulbs can see each other (same row or column, no walls between)
                if r1 == r2:  # Same row
                    min_c, max_c = min(c1, c2), max(c1, c2)
                    can_see = True
                    for c in range(min_c + 1, max_c):
                        if state[r1 * cols + c] in wall_values:
                            can_see = False
                            break
                    if can_see:
                        violating_bulbs_set.add((r1, c1))
                        violating_bulbs_set.add((r2, c2))

                elif c1 == c2:  # Same column
                    min_r, max_r = min(r1, r2), max(r1, r2)
                    can_see = True
                    for r in range(min_r + 1, max_r):
                        if state[r * cols + c1] in wall_values:
                            can_see = False
                            break
                    if can_see:
                        violating_bulbs_set.add((r1, c1))
                        violating_bulbs_set.add((r2, c2))

        if not violating_bulbs_set:
            return None

        violating_bulbs_list = [{"row": r, "col": c} for r, c in violating_bulbs_set]

        return ValidationResult(
            locations=violating_bulbs_list,
            rule_type="bulb_intersection_violation",
        )

    return RuleDefinition(rule)


def validate_numbered_wall_constraints() -> RuleDefinition:
    """
    Generate a rule to validate that numbered walls in Light Up have the correct
    number of adjacent bulbs.

    In Light Up, walls with numbers (0-4) must have exactly that many bulbs
    in the 4 adjacent cells (not diagonals).

    :return: A rule function that validates numbered wall constraints
    """

    def rule(engine: PuzzleEngineBase) -> Optional[ValidationResult]:
        from puzzles.engine.games.lightup import LightupCellStates

        state = engine.board_state
        rows, cols = engine.rows, engine.cols

        # Only 4 cardinal directions for Light Up wall constraints
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        violating_walls = []

        for r in range(rows):
            for c in range(cols):
                cell_value = state[r * cols + c]

                # Check if this is a numbered wall (0-4)
                if cell_value not in [
                    LightupCellStates.Wall0,
                    LightupCellStates.Wall1,
                    LightupCellStates.Wall2,
                    LightupCellStates.Wall3,
                    LightupCellStates.Wall4,
                ]:
                    continue

                # Get the required number of bulbs
                required_bulbs = cell_value  # Wall0 = 0, Wall1 = 1, etc.

                # Count adjacent bulbs
                adjacent_bulbs = 0
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if state[nr * cols + nc] == LightupCellStates.Bulb:
                            adjacent_bulbs += 1

                # Check if constraint is violated (too many bulbs)
                if adjacent_bulbs > required_bulbs:
                    violating_walls.append({"row": r, "col": c})

        if not violating_walls:
            return None

        return ValidationResult(locations=violating_walls, rule_type="numbered_wall_constraint_violated")

    return RuleDefinition(rule)
