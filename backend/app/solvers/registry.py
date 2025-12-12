"""
Solver registry - maps puzzle types to solver functions.
"""

from typing import Dict, Any, Optional
from .base import SolverResult, SolverFn


# Registry of solver functions by puzzle type
_SOLVERS: Dict[str, SolverFn] = {}


def register_solver(puzzle_type: str):
    """Decorator to register a solver function."""
    def decorator(fn: SolverFn) -> SolverFn:
        _SOLVERS[puzzle_type] = fn
        return fn
    return decorator


def get_solver(puzzle_type: str) -> Optional[SolverFn]:
    """Get solver function for a puzzle type, or None if not supported."""
    return _SOLVERS.get(puzzle_type)


def supports_solver(puzzle_type: str) -> bool:
    """Check if a solver exists for the puzzle type."""
    return puzzle_type in _SOLVERS


def solve(puzzle_type: str, puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a puzzle using the appropriate solver.

    Args:
        puzzle_type: Type of puzzle (e.g., "lightup")
        puzzle_data: Normalized puzzle data
        max_solutions: Max solutions to find (2 for uniqueness check)

    Returns:
        SolverResult

    Raises:
        ValueError if no solver exists for the puzzle type
    """
    solver = get_solver(puzzle_type)
    if solver is None:
        raise ValueError(f"No solver for puzzle type: {puzzle_type}")
    return solver(puzzle_data, max_solutions)
