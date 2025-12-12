"""
Base types for puzzle solvers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable


@dataclass
class SolverResult:
    """Result of solving a puzzle."""

    is_valid: bool  # Has at least one solution
    is_unique: bool  # Has exactly one solution
    solution_count: int  # Number of solutions found (up to max_solutions)
    solutions: List[List[List[int]]] = field(default_factory=list)
    error: Optional[str] = None


# Type alias for solver functions
# A solver takes puzzle_data and max_solutions, returns SolverResult
SolverFn = Callable[[Dict[str, Any], int], SolverResult]
