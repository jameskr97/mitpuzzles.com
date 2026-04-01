"""per-game efficiency metrics computed from action_history + solution."""

from typing import Dict, Any, List
from app.service.encoder import PrecisePuzzleEncoder


# action types that represent a user changing a cell value
CELL_ACTIONS = {"cell_click", "click", "cell_keypress", "keypress"}


def compute_min_actions(
    puzzle_type: str,
    initial_state: List[List[int]],
    solution: Any,
) -> int:
    """
    compute the minimum number of clicks needed to solve a puzzle.

    this is the count of required placements only — assists (flags, crosses,
    safe marks, greens) are not counted.
    """
    config = PrecisePuzzleEncoder.PUZZLE_CONFIGS.get(puzzle_type)
    if not config:
        return 0

    # hashi: sum of bridge counts in solution
    if config.get("bridge_based"):
        if isinstance(solution, list) and len(solution) > 0 and isinstance(solution[0], dict):
            return sum(bridge.get("count", 1) for bridge in solution)
        return 0

    positive_values = set(config["positive_values"])
    empty_values = set(config.get("empty_values", []))

    # count cells in solution that have a positive value AND are empty in initial_state
    count = 0
    for r, row in enumerate(initial_state):
        for c, init_val in enumerate(row):
            sol_val = solution[r][c]
            if init_val in empty_values and sol_val in positive_values:
                count += 1

    # ying_yang: second-cycle-value cells need 2 clicks
    # TODO: add when ying_yang click cycle is defined

    return count


def compute_game_metrics(
    puzzle_type: str,
    initial_state: List[List[int]],
    solution: Any,
    action_history: List[Dict[str, Any]],
    is_solved: bool,
) -> Dict[str, Any]:
    """
    Compute per-game efficiency metrics from a single attempt.

    Returns:
        min_actions: minimum clicks needed to solve (required placements only)
        actual_actions: total cell-change actions the user made (including assists)
        efficiency: min_actions / actual_actions (1.0 = perfect, capped at 1.0)
        mistakes: actions where user placed a wrong positive value
        corrections: actions where user fixed a previously wrong cell to the correct value
        cells_changed_multiple_times: cells the user changed more than once
        wasted_actions: actual_actions - min_actions
        action_breakdown: {action_type: count}
    """
    min_acts = compute_min_actions(puzzle_type, initial_state, solution)

    config = PrecisePuzzleEncoder.PUZZLE_CONFIGS.get(puzzle_type)
    is_bridge_based = config and config.get("bridge_based")

    rows = len(initial_state)
    cols = len(initial_state[0]) if rows > 0 else 0
    empty_values = set(config.get("empty_values", [])) if config else set()

    # build solution lookup for cell-based puzzles
    sol_lookup: Dict[str, Any] = {}
    if not is_bridge_based:
        for r in range(rows):
            for c in range(cols):
                sol_lookup[f"{r},{c}"] = solution[r][c]

    positive_values = set(config.get("positive_values", [])) if config else set()
    negative_values = set(config.get("negative_values", [])) if config else set()

    # analyze action_history
    cell_changes: Dict[str, List[Dict[str, Any]]] = {}
    actual_actions = 0
    positive_actions = 0  # placed a required value (correct or not)
    assist_actions = 0    # placed a cross/flag/green/safe mark
    mistakes = 0
    corrections = 0
    action_breakdown: Dict[str, int] = {}

    for action in action_history:
        action_type = action.get("action", "")
        action_breakdown[action_type] = action_breakdown.get(action_type, 0) + 1

        if action_type not in CELL_ACTIONS:
            continue

        cell = action.get("cell")
        if not cell:
            continue

        r, c = cell.get("row"), cell.get("col")
        if r is None or c is None:
            continue

        new_value = action.get("new_value")
        old_value = action.get("old_value")
        if new_value is None:
            continue

        actual_actions += 1
        cell_key = f"{r},{c}"

        if cell_key not in cell_changes:
            cell_changes[cell_key] = []
        cell_changes[cell_key].append(action)

        # classify action: positive placement vs assist vs clearing
        if new_value in positive_values:
            positive_actions += 1
        elif new_value in negative_values:
            assist_actions += 1

        # mistake/correction detection (cell-based puzzles only)
        if not is_bridge_based and cell_key in sol_lookup:
            sol_val = sol_lookup[cell_key]

            # mistake: placed a non-empty value that doesn't match solution
            if new_value not in empty_values and new_value != sol_val:
                mistakes += 1
            # correction: old value was wrong, new value is correct
            elif new_value == sol_val and old_value is not None and old_value not in empty_values and old_value != sol_val:
                corrections += 1

    cells_changed_multiple_times = sum(1 for changes in cell_changes.values() if len(changes) > 1)
    wasted_actions = max(0, actual_actions - min_acts)

    # total efficiency: min_actions / all actions (penalizes assists)
    efficiency = min_acts / actual_actions if actual_actions > 0 else 0.0
    efficiency = min(efficiency, 1.0)

    # solve efficiency: min_actions / positive actions only (ignores assists)
    non_assist_actions = actual_actions - assist_actions
    solve_efficiency = min_acts / non_assist_actions if non_assist_actions > 0 else 0.0
    solve_efficiency = min(solve_efficiency, 1.0)

    return {
        "min_actions": min_acts,
        "actual_actions": actual_actions,
        "positive_actions": positive_actions,
        "assist_actions": assist_actions,
        "efficiency": round(efficiency, 4),
        "solve_efficiency": round(solve_efficiency, 4),
        "mistakes": mistakes,
        "corrections": corrections,
        "cells_changed_multiple_times": cells_changed_multiple_times,
        "wasted_actions": wasted_actions,
        "is_solved": is_solved,
        "action_breakdown": action_breakdown,
    }
