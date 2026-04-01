"""compute structural metrics for puzzle definitions."""

from typing import Dict, Any, List, Optional
from app.service.encoder import PrecisePuzzleEncoder


def compute_puzzle_metrics(puzzle_type: str, puzzle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    compute structural metrics for a puzzle definition from its puzzle_data.

    returns a dict of PuzzleMetrics schema, or None if the unsupported/missing data.
    """
    config = PrecisePuzzleEncoder.PUZZLE_CONFIGS.get(puzzle_type)
    if not config:
        return None

    initial_state = puzzle_data.get("initial_state") or puzzle_data.get("game_state")
    solution = puzzle_data.get("solution") or puzzle_data.get("game_board")

    if not initial_state or not solution:
        return None

    is_bridge_based = config.get("bridge_based", False)

    # common metrics for cell-based puzzles
    if not is_bridge_based:
        rows = len(initial_state)
        cols = len(initial_state[0]) if rows > 0 else 0
        board_size = rows * cols

        positive_values = set(config["positive_values"])
        negative_values = set(config.get("negative_values", []))
        immutable_values = set(config.get("immutable_values", []))
        empty_values = set(config.get("empty_values", []))

        empty_cells = 0
        clue_cells = 0
        min_actions = 0
        positive_in_solution = 0

        for r in range(rows):
            for c in range(cols):
                init_val = initial_state[r][c]
                sol_val = solution[r][c]

                if init_val in empty_values:
                    empty_cells += 1
                elif init_val in immutable_values:
                    clue_cells += 1

                if sol_val in positive_values:
                    positive_in_solution += 1

                if init_val in empty_values and sol_val in positive_values:
                    min_actions += 1

        solution_density = round(positive_in_solution / board_size, 4) if board_size > 0 else 0.0

        metrics: Dict[str, Any] = {
            "min_actions": min_actions,
            "board_size": board_size,
            "empty_cells": empty_cells,
            "clue_cells": clue_cells,
            "solution_density": solution_density,
        }

        # type-specific metrics
        if puzzle_type == "minesweeper":
            metrics["mine_count"] = positive_in_solution
        elif puzzle_type == "sudoku":
            metrics["given_count"] = clue_cells or (board_size - empty_cells)
        elif puzzle_type == "lightup":
            metrics["bulb_count"] = positive_in_solution
        elif puzzle_type == "tents":
            metrics["tent_count"] = positive_in_solution
        elif puzzle_type == "aquarium":
            metrics["water_cells"] = positive_in_solution
        elif puzzle_type in ("kakurasu", "nonograms"):
            metrics["black_cells"] = positive_in_solution
        elif puzzle_type in ("mosaic", "norinori"):
            metrics["shaded_cells"] = positive_in_solution

        return metrics

    # hashi: bridge-based
    else:
        rows = len(initial_state)
        cols = len(initial_state[0]) if rows > 0 else 0
        board_size = rows * cols

        # count island cells (non-zero in initial state)
        clue_cells = sum(1 for r in initial_state for val in r if val > 0)
        empty_cells = board_size - clue_cells

        # solution is a list of bridges
        if isinstance(solution, list) and len(solution) > 0 and isinstance(solution[0], dict):
            bridge_count = len(solution)
            min_actions = sum(bridge.get("count", 1) for bridge in solution)
        else:
            bridge_count = 0
            min_actions = 0

        return {
            "min_actions": min_actions,
            "board_size": board_size,
            "empty_cells": empty_cells,
            "clue_cells": clue_cells,
            "solution_density": 0.0,
            "bridge_count": bridge_count,
        }
