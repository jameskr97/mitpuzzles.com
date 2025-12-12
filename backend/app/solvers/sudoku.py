"""
Sudoku puzzle solver using SAT.

Rules:
- Fill each cell with a digit 1-9 (for 9x9)
- Each row must contain each digit exactly once
- Each column must contain each digit exactly once
- Each 3x3 box must contain each digit exactly once

Cell values in initial_state:
- 0 or -1: Empty cell
- 1-9: Given digit

Cell values in solution:
- 1-9: The digit in that cell
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import math
from pysat.solvers import Solver
from pysat.formula import CNF

from .base import SolverResult
from .registry import register_solver


@dataclass
class SudokuGrid:
    """Represents a sudoku grid for SAT encoding."""
    size: int
    grid: List[List[int]]
    box_size: int = field(init=False)

    def __post_init__(self):
        self.box_size = int(math.sqrt(self.size))
        if self.box_size * self.box_size != self.size:
            raise ValueError(f"Sudoku size {self.size} is not a perfect square")

    def cell_digit_var(self, r: int, c: int, d: int) -> int:
        """Get SAT variable for 'cell (r,c) contains digit d'.
        Variables are 1-indexed, d is 1-indexed (1 to size).
        """
        # Variable numbering: (r * size * size) + (c * size) + (d - 1) + 1
        return r * self.size * self.size + c * self.size + d


def encode(g: SudokuGrid) -> CNF:
    """Encode Sudoku puzzle as CNF formula."""
    formula = CNF()
    size = g.size
    box_size = g.box_size

    # Constraint 1: Each cell has exactly one digit
    for r in range(size):
        for c in range(size):
            # At least one digit
            formula.append([g.cell_digit_var(r, c, d) for d in range(1, size + 1)])

            # At most one digit (pairwise exclusion)
            for d1 in range(1, size + 1):
                for d2 in range(d1 + 1, size + 1):
                    formula.append([-g.cell_digit_var(r, c, d1), -g.cell_digit_var(r, c, d2)])

    # Constraint 2: Each digit appears exactly once in each row
    for r in range(size):
        for d in range(1, size + 1):
            # At least once
            formula.append([g.cell_digit_var(r, c, d) for c in range(size)])

            # At most once
            for c1 in range(size):
                for c2 in range(c1 + 1, size):
                    formula.append([-g.cell_digit_var(r, c1, d), -g.cell_digit_var(r, c2, d)])

    # Constraint 3: Each digit appears exactly once in each column
    for c in range(size):
        for d in range(1, size + 1):
            # At least once
            formula.append([g.cell_digit_var(r, c, d) for r in range(size)])

            # At most once
            for r1 in range(size):
                for r2 in range(r1 + 1, size):
                    formula.append([-g.cell_digit_var(r1, c, d), -g.cell_digit_var(r2, c, d)])

    # Constraint 4: Each digit appears exactly once in each box
    for box_r in range(0, size, box_size):
        for box_c in range(0, size, box_size):
            box_cells = [(r, c) for r in range(box_r, box_r + box_size)
                                for c in range(box_c, box_c + box_size)]

            for d in range(1, size + 1):
                # At least once
                formula.append([g.cell_digit_var(r, c, d) for (r, c) in box_cells])

                # At most once
                for i in range(len(box_cells)):
                    for j in range(i + 1, len(box_cells)):
                        r1, c1 = box_cells[i]
                        r2, c2 = box_cells[j]
                        formula.append([-g.cell_digit_var(r1, c1, d), -g.cell_digit_var(r2, c2, d)])

    # Constraint 5: Given cells (pre-filled)
    for r in range(size):
        for c in range(size):
            val = g.grid[r][c]
            if val > 0:  # Given digit
                formula.append([g.cell_digit_var(r, c, val)])

    return formula


def decode(model: List[int], g: SudokuGrid) -> List[List[int]]:
    """Convert SAT model to solution grid."""
    model_set = set(model)
    solution = [[0] * g.size for _ in range(g.size)]

    for r in range(g.size):
        for c in range(g.size):
            for d in range(1, g.size + 1):
                if g.cell_digit_var(r, c, d) in model_set:
                    solution[r][c] = d
                    break

    return solution


@register_solver("sudoku")
def solve_sudoku(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a sudoku puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        size = puzzle_data['rows']
        g = SudokuGrid(
            size=size,
            grid=puzzle_data['initial_state'],
        )

        formula = encode(g)

        solutions = []
        with Solver(name='glucose4', bootstrap_with=formula) as solver:
            while len(solutions) < max_solutions:
                if not solver.solve():
                    break

                model = solver.get_model()
                solution = decode(model, g)
                solutions.append(solution)

                # Block this solution - block the cell-digit assignments
                blocking_clause = []
                for r in range(g.size):
                    for c in range(g.size):
                        for d in range(1, g.size + 1):
                            var = g.cell_digit_var(r, c, d)
                            if var in model:
                                blocking_clause.append(-var)
                solver.add_clause(blocking_clause)

        return SolverResult(
            is_valid=len(solutions) > 0,
            is_unique=len(solutions) == 1,
            solution_count=len(solutions),
            solutions=solutions,
        )

    except Exception as e:
        return SolverResult(
            is_valid=False,
            is_unique=False,
            solution_count=0,
            error=str(e),
        )
