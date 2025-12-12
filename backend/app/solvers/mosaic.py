"""
Mosaic puzzle solver using SAT.

Rules:
- Fill the grid with black (1) and white (0) cells
- A number in a cell specifies how many black cells are in the 3x3 block
  centered at that cell (including the cell itself)

Cell values in initial_state:
- -1: Unknown/unmarked cell
- 0-9: Clue cell (count of black cells in 3x3 neighborhood)

Cell values in solution:
- -3: Black cell (filled)
- -4: White cell (empty)
- 0-9: Clue cells remain unchanged
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class MosaicGrid:
    """Represents a mosaic grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    clue_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self):
        """Parse grid to find clue cells."""
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid[r][c]
                if 0 <= val <= 9:
                    self.clue_cells[(r, c)] = val

    def cell_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) is black. Variables start at 1."""
        return r * self.cols + c + 1

    def neighborhood(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get 3x3 neighborhood centered at (r,c), including the center cell."""
        cells = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    cells.append((nr, nc))
        return cells


def encode(g: MosaicGrid) -> CNF:
    """Encode Mosaic puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for cell colors
    next_aux_var = g.rows * g.cols + 1

    # Constraint: Each clue cell specifies exactly N black cells in its 3x3 neighborhood
    for (r, c), count in g.clue_cells.items():
        neighborhood = g.neighborhood(r, c)
        neighbor_vars = [g.cell_var(nr, nc) for (nr, nc) in neighborhood]

        if neighbor_vars:
            cnf = CardEnc.equals(lits=neighbor_vars, bound=count, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)
            if cnf.nv and cnf.nv >= next_aux_var:
                next_aux_var = cnf.nv + 1

    return formula


def decode(model: List[int], g: MosaicGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output uses the same encoding as the puzzle generator:
    - -3: Black cell
    - -4: White cell
    - 0-9: Clue cells remain unchanged
    """
    model_set = set(model)
    solution = [row[:] for row in g.grid]

    for r in range(g.rows):
        for c in range(g.cols):
            # Only change non-clue cells
            if g.grid[r][c] < 0 or g.grid[r][c] > 9:
                var = g.cell_var(r, c)
                solution[r][c] = -3 if var in model_set else -4

    return solution


@register_solver("mosaic")
def solve_mosaic(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a mosaic puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = MosaicGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
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

                # Block this solution - negate all cell assignments
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
