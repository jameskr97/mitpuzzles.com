"""puzzle formatting functions."""
from typing import Dict, Any

from app.service.encoder import PrecisePuzzleEncoder


def calculate_solution_hash(puzzle_type: str, solution_state) -> str:
    """calculate the run-length-encoding based solution hash for a puzzle."""
    encoder = PrecisePuzzleEncoder(puzzle_type)
    return encoder.create_run_length_encoding(solution_state)


def format_puzzle_for_frontend(puzzle) -> Dict[str, Any]:
    """
    transform a database Puzzle object to the frontend format.

    returns id, puzzle_type, rows, cols, initial_state, solution_hash,
    and meta (everything in puzzle_data that isn't a top-level field).
    """
    puzzle_data = puzzle.puzzle_data

    # everything that doesn't go into a top-level field becomes meta
    top_level_keys = {
        "puzzle_type", "puzzle_size", "puzzle_difficulty",
        "definition_id", "solution_id", "complete_id",
        "rows", "cols", "initial_state", "solution", "difficulty_label",
    }
    meta = {k: v for k, v in puzzle_data.items() if k not in top_level_keys}

    return {
        "id": puzzle.id,
        "puzzle_type": puzzle.puzzle_type,
        "rows": puzzle_data["rows"],
        "cols": puzzle_data["cols"],
        "initial_state": puzzle_data["initial_state"],
        "solution_hash": calculate_solution_hash(puzzle.puzzle_type, puzzle_data["solution"]),
        "meta": meta,
    }


def format_puzzle_with_solution(puzzle) -> Dict[str, Any]:
    """transform a database Puzzle object to admin format (includes actual solution)."""
    result = format_puzzle_for_frontend(puzzle)
    result["solution"] = puzzle.puzzle_data["solution"]
    return result
