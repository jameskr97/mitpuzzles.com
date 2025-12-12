"""
Nonograms (Picross) puzzle solver using SAT.

Rules:
- Fill cells black (1) or leave white (0)
- Row hints indicate lengths of consecutive black cell runs in that row
- Column hints indicate lengths of consecutive black cell runs in that column
- Runs must appear in the order given, with at least one white cell between runs

Cell values in initial_state:
- -1: Unknown cell
- 0: Marked white (X)
- 1: Marked black

Cell values in solution:
- -3: Black cell
- -4: White cell
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from itertools import combinations
from pysat.solvers import Solver
from pysat.formula import CNF

from .base import SolverResult
from .registry import register_solver


@dataclass
class NonogramGrid:
    """Represents a nonogram grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    row_hints: List[List[int]]
    col_hints: List[List[int]]

    def cell_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) is black. Variables start at 1."""
        return r * self.cols + c + 1


def generate_valid_patterns(length: int, hints: List[int]) -> List[List[int]]:
    """Generate all valid patterns for a line with given hints.

    Args:
        length: Length of the line (number of cells)
        hints: List of run lengths

    Returns:
        List of valid patterns, where each pattern is a list of 0s and 1s
    """
    if not hints or hints == [0]:
        # No runs - all white
        return [[0] * length]

    # Total black cells needed
    total_black = sum(hints)
    # Minimum gaps needed (one between each run)
    min_gaps = len(hints) - 1
    # Minimum length needed
    min_length = total_black + min_gaps

    if min_length > length:
        return []  # No valid patterns

    patterns = []

    def generate(hint_idx: int, pos: int, pattern: List[int]):
        """Recursively generate patterns."""
        if hint_idx == len(hints):
            # Fill rest with white
            while len(pattern) < length:
                pattern.append(0)
            patterns.append(pattern[:])
            # Remove the added whites for backtracking
            del pattern[pos:]
            return

        run_len = hints[hint_idx]

        # Calculate minimum space needed for remaining hints (including this one)
        remaining_hints = hints[hint_idx:]
        min_remaining = sum(remaining_hints) + len(remaining_hints) - 1

        # Maximum position where this run can start
        max_start = length - min_remaining

        # Try each possible starting position for this run
        for start in range(pos, max_start + 1):
            # Add white cells before this run
            while len(pattern) < start:
                pattern.append(0)

            # Add the run (black cells)
            for _ in range(run_len):
                pattern.append(1)

            # Add mandatory gap (white) if not last run
            if hint_idx < len(hints) - 1:
                pattern.append(0)
                next_pos = start + run_len + 1
            else:
                next_pos = start + run_len

            generate(hint_idx + 1, next_pos, pattern)

            # Backtrack
            del pattern[pos:]

    generate(0, 0, [])
    return patterns


def encode(g: NonogramGrid) -> CNF:
    """Encode Nonogram puzzle as CNF formula."""
    formula = CNF()

    # Pre-assigned cells
    for r in range(g.rows):
        for c in range(g.cols):
            if g.grid[r][c] == 0:  # Marked white
                formula.append([-g.cell_var(r, c)])
            elif g.grid[r][c] == 1:  # Marked black
                formula.append([g.cell_var(r, c)])

    # Row constraints: each row must match one of its valid patterns
    for r in range(g.rows):
        hints = g.row_hints[r]
        patterns = generate_valid_patterns(g.cols, hints)

        if not patterns:
            # No valid patterns - UNSAT
            formula.append([])
            continue

        # For each cell position, collect which patterns have it black
        for c in range(g.cols):
            var = g.cell_var(r, c)
            black_patterns = [i for i, p in enumerate(patterns) if p[c] == 1]
            white_patterns = [i for i, p in enumerate(patterns) if p[c] == 0]

            # If all patterns have this cell black, it must be black
            if not white_patterns:
                formula.append([var])
            # If all patterns have this cell white, it must be white
            elif not black_patterns:
                formula.append([-var])

    # Column constraints: each column must match one of its valid patterns
    for c in range(g.cols):
        hints = g.col_hints[c]
        patterns = generate_valid_patterns(g.rows, hints)

        if not patterns:
            formula.append([])
            continue

        for r in range(g.rows):
            var = g.cell_var(r, c)
            black_patterns = [i for i, p in enumerate(patterns) if p[r] == 1]
            white_patterns = [i for i, p in enumerate(patterns) if p[r] == 0]

            if not white_patterns:
                formula.append([var])
            elif not black_patterns:
                formula.append([-var])

    # We need a more sophisticated encoding to capture the full constraint
    # Use auxiliary variables to select which pattern each row/column uses

    # Reserve variables after cell variables
    next_aux_var = g.rows * g.cols + 1

    # Row pattern selection
    for r in range(g.rows):
        hints = g.row_hints[r]
        patterns = generate_valid_patterns(g.cols, hints)

        if len(patterns) <= 1:
            continue  # Already handled above or UNSAT

        # Create pattern selector variables
        pattern_vars = list(range(next_aux_var, next_aux_var + len(patterns)))
        next_aux_var += len(patterns)

        # Exactly one pattern must be selected
        # At least one
        formula.append(pattern_vars)
        # At most one (pairwise)
        for i in range(len(pattern_vars)):
            for j in range(i + 1, len(pattern_vars)):
                formula.append([-pattern_vars[i], -pattern_vars[j]])

        # Link pattern selection to cell values
        for c in range(g.cols):
            cell_var = g.cell_var(r, c)
            for pi, pattern in enumerate(patterns):
                pvar = pattern_vars[pi]
                if pattern[c] == 1:
                    # pattern selected -> cell is black
                    formula.append([-pvar, cell_var])
                else:
                    # pattern selected -> cell is white
                    formula.append([-pvar, -cell_var])

    # Column pattern selection
    for c in range(g.cols):
        hints = g.col_hints[c]
        patterns = generate_valid_patterns(g.rows, hints)

        if len(patterns) <= 1:
            continue

        pattern_vars = list(range(next_aux_var, next_aux_var + len(patterns)))
        next_aux_var += len(patterns)

        formula.append(pattern_vars)
        for i in range(len(pattern_vars)):
            for j in range(i + 1, len(pattern_vars)):
                formula.append([-pattern_vars[i], -pattern_vars[j]])

        for r in range(g.rows):
            cell_var = g.cell_var(r, c)
            for pi, pattern in enumerate(patterns):
                pvar = pattern_vars[pi]
                if pattern[r] == 1:
                    formula.append([-pvar, cell_var])
                else:
                    formula.append([-pvar, -cell_var])

    return formula


def decode(model: List[int], g: NonogramGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output:
    - 1: Black cell
    - 0: White cell
    """
    model_set = set(model)
    solution = []

    for r in range(g.rows):
        row = []
        for c in range(g.cols):
            var = g.cell_var(r, c)
            row.append(1 if var in model_set else 0)
        solution.append(row)

    return solution


@register_solver("nonograms")
def solve_nonograms(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a nonograms puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state',
                    'row_hints', 'col_hints'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = NonogramGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
            row_hints=puzzle_data['row_hints'],
            col_hints=puzzle_data['col_hints'],
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

                # Block this solution - only block cell variables
                blocking_clause = []
                for r in range(g.rows):
                    for c in range(g.cols):
                        var = g.cell_var(r, c)
                        if var in model:
                            blocking_clause.append(-var)
                        else:
                            blocking_clause.append(var)
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
