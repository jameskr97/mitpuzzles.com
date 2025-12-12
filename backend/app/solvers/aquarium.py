"""
Aquarium puzzle solver using SAT.

Rules:
- Fill cells with water (1) or leave empty (0)
- Row/column clues indicate exact number of water cells in each row/column
- Within each region (aquarium), cells in the same row must have the same state
- Water fills from bottom: if a cell has water, all cells below it in the same
  region column must also have water

Cell values in initial_state:
- -1: Unknown cell
- -3: Water (pre-filled)
- -4: Empty (pre-marked)

Cell values in solution:
- -3: Water
- -4: Empty
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any
from collections import defaultdict
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class AquariumGrid:
    """Represents an aquarium grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    regions: List[List[int]]
    row_clues: List[int]
    col_clues: List[int]

    def water_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) has water. Variables start at 1."""
        return r * self.cols + c + 1


def encode(g: AquariumGrid) -> CNF:
    """Encode Aquarium puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for water placement
    next_aux_var = g.rows * g.cols + 1

    # Pre-assigned cells
    for r in range(g.rows):
        for c in range(g.cols):
            if g.grid[r][c] == -3:  # Water
                formula.append([g.water_var(r, c)])
            elif g.grid[r][c] == -4:  # Empty
                formula.append([-g.water_var(r, c)])

    # Constraint 1: Row sums
    for r, row_sum in enumerate(g.row_clues):
        row_vars = [g.water_var(r, c) for c in range(g.cols)]
        cnf = CardEnc.equals(lits=row_vars, bound=row_sum, top_id=next_aux_var, encoding=EncType.seqcounter)
        formula.extend(cnf.clauses)
        if cnf.nv and cnf.nv >= next_aux_var:
            next_aux_var = cnf.nv + 1

    # Constraint 2: Column sums
    for c, col_sum in enumerate(g.col_clues):
        col_vars = [g.water_var(r, c) for r in range(g.rows)]
        cnf = CardEnc.equals(lits=col_vars, bound=col_sum, top_id=next_aux_var, encoding=EncType.seqcounter)
        formula.extend(cnf.clauses)
        if cnf.nv and cnf.nv >= next_aux_var:
            next_aux_var = cnf.nv + 1

    # Group cells by region
    region_cells: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for r in range(g.rows):
        for c in range(g.cols):
            region_id = g.regions[r][c]
            region_cells[region_id].append((r, c))

    # Constraint 3: Within each region, cells in the same row must have same state
    for region_id, cells in region_cells.items():
        # Group by row
        row_groups: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for (r, c) in cells:
            row_groups[r].append((r, c))

        for row_cells in row_groups.values():
            if len(row_cells) > 1:
                # All cells in this row slice must be identical
                # For each pair: (a -> b) and (b -> a) means a <-> b
                for i in range(len(row_cells) - 1):
                    r1, c1 = row_cells[i]
                    r2, c2 = row_cells[i + 1]
                    v1, v2 = g.water_var(r1, c1), g.water_var(r2, c2)
                    # v1 <-> v2: (not v1 or v2) and (v1 or not v2)
                    formula.append([-v1, v2])
                    formula.append([v1, -v2])

    # Constraint 4: Water fills from bottom within each region column
    for region_id, cells in region_cells.items():
        # Group by column within this region
        col_groups: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        for (r, c) in cells:
            col_groups[c].append((r, c))

        for col_cells in col_groups.values():
            # Sort by row (top to bottom)
            col_cells.sort(key=lambda x: x[0])
            # If cell at row r has water, all cells below must have water
            for i in range(len(col_cells) - 1):
                r_upper, c_upper = col_cells[i]
                r_lower, c_lower = col_cells[i + 1]
                v_upper = g.water_var(r_upper, c_upper)
                v_lower = g.water_var(r_lower, c_lower)
                # If upper has water, lower must have water: upper -> lower
                # Equivalent to: (not upper) or lower
                formula.append([-v_upper, v_lower])

    return formula


def decode(model: List[int], g: AquariumGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output:
    - -3: Water
    - -4: Empty
    """
    model_set = set(model)
    solution = []

    for r in range(g.rows):
        row = []
        for c in range(g.cols):
            var = g.water_var(r, c)
            row.append(-3 if var in model_set else -4)
        solution.append(row)

    return solution


@register_solver("aquarium")
def solve_aquarium(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve an aquarium puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state',
                    'regions', 'row_hints', 'col_hints'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = AquariumGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
            regions=puzzle_data['regions'],
            row_clues=puzzle_data['row_hints'],
            col_clues=puzzle_data['col_hints'],
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
                        var = g.water_var(r, c)
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
