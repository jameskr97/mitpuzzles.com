"""
Kakurasu puzzle solver using SAT.

Rules:
- Fill cells black (1) or leave white (0)
- Each row sum = sum of (column_index * cell_value) for black cells (1-indexed columns)
- Each column sum = sum of (row_index * cell_value) for black cells (1-indexed rows)

Cell values in initial_state:
- -1: Unknown cell
- 0: Marked as white (X)
- 1: Marked as black

Cell values in solution:
- -3: Black cell
- -4: White cell
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.pb import PBEnc, EncType as PBEncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class KakurasuGrid:
    """Represents a kakurasu grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    row_sums: List[int]
    col_sums: List[int]

    def cell_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) is black. Variables start at 1."""
        return r * self.cols + c + 1


def encode(g: KakurasuGrid) -> CNF:
    """Encode Kakurasu puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for cell colors
    next_aux_var = g.rows * g.cols + 1

    # Pre-assigned cells
    for r in range(g.rows):
        for c in range(g.cols):
            if g.grid[r][c] == 0:  # Marked white
                formula.append([-g.cell_var(r, c)])
            elif g.grid[r][c] == 1:  # Marked black
                formula.append([g.cell_var(r, c)])

    # Constraint: Row weighted sums
    # Row r: sum of (c+1) * x_{r,c} = row_sums[r]
    for r, target in enumerate(g.row_sums):
        lits = [g.cell_var(r, c) for c in range(g.cols)]
        weights = [c + 1 for c in range(g.cols)]  # 1-indexed column weights

        # Weighted sum equals target
        cnf = PBEnc.equals(lits=lits, weights=weights, bound=target, top_id=next_aux_var, encoding=PBEncType.sortnetwrk)
        formula.extend(cnf.clauses)
        if cnf.nv and cnf.nv >= next_aux_var:
            next_aux_var = cnf.nv + 1

    # Constraint: Column weighted sums
    # Column c: sum of (r+1) * x_{r,c} = col_sums[c]
    for c, target in enumerate(g.col_sums):
        lits = [g.cell_var(r, c) for r in range(g.rows)]
        weights = [r + 1 for r in range(g.rows)]  # 1-indexed row weights

        cnf = PBEnc.equals(lits=lits, weights=weights, bound=target, top_id=next_aux_var, encoding=PBEncType.sortnetwrk)
        formula.extend(cnf.clauses)
        if cnf.nv and cnf.nv >= next_aux_var:
            next_aux_var = cnf.nv + 1

    return formula


def decode(model: List[int], g: KakurasuGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output:
    - 1: Black cell (selected)
    - 0: White cell (not selected)
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


@register_solver("kakurasu")
def solve_kakurasu(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a kakurasu puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state',
                    'row_sums', 'col_sums'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = KakurasuGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
            row_sums=puzzle_data['row_sums'],
            col_sums=puzzle_data['col_sums'],
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

                # Block this solution
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
