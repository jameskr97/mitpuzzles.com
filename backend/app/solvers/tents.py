"""
Tents puzzle solver using SAT.

Rules:
- Place tents on empty cells adjacent to trees (4-directional)
- Each tree must have exactly one adjacent tent
- No two tents can be adjacent (including diagonally)
- Row/column clues indicate exact number of tents in each row/column

Cell values in initial_state:
- 0: Empty cell
- 1: Tree
- -1: Unknown cell

Cell values in solution:
- 0: Empty cell (no tent)
- 1: Tree
- -3: Tent placed
- -4: Marked as no-tent
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class TentsGrid:
    """Represents a tents grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    row_clues: List[int]
    col_clues: List[int]
    trees: List[Tuple[int, int]] = field(default_factory=list)
    empty_cells: List[Tuple[int, int]] = field(default_factory=list)

    def __post_init__(self):
        """Parse grid to find trees and empty cells."""
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid[r][c]
                if val == 1:
                    self.trees.append((r, c))
                elif val != 1:  # Empty or unknown
                    self.empty_cells.append((r, c))

    def tent_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) has a tent. Variables start at 1."""
        return r * self.cols + c + 1

    def adjacent_4(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get 4-directionally adjacent cells."""
        adjacent = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                adjacent.append((nr, nc))
        return adjacent

    def adjacent_8(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get 8-directionally adjacent cells (including diagonals)."""
        adjacent = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    adjacent.append((nr, nc))
        return adjacent


def encode(g: TentsGrid) -> CNF:
    """Encode Tents puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for tent placement
    next_aux_var = g.rows * g.cols + 1

    # Constraint 1: Trees cannot have tents
    for (r, c) in g.trees:
        formula.append([-g.tent_var(r, c)])

    # Constraint 2: Cells not adjacent to any tree cannot have tents
    tree_set = set(g.trees)
    for (r, c) in g.empty_cells:
        adjacent = g.adjacent_4(r, c)
        if not any((nr, nc) in tree_set for (nr, nc) in adjacent):
            formula.append([-g.tent_var(r, c)])

    # Constraint 3: Each tree must have at least one adjacent tent
    for (r, c) in g.trees:
        adjacent = g.adjacent_4(r, c)
        tent_candidates = [g.tent_var(nr, nc) for (nr, nc) in adjacent if (nr, nc) not in tree_set]
        if tent_candidates:
            # At least one adjacent tent
            formula.append(tent_candidates)

    # Constraint 4: No two tents can be adjacent (8-directional)
    seen_pairs = set()
    for (r, c) in g.empty_cells:
        for (nr, nc) in g.adjacent_8(r, c):
            if (nr, nc) in g.empty_cells or (nr, nc) not in tree_set:
                # Avoid duplicate constraints
                pair = (min((r, c), (nr, nc)), max((r, c), (nr, nc)))
                if pair not in seen_pairs and (nr, nc) not in tree_set:
                    seen_pairs.add(pair)
                    # At most one of these two can be a tent
                    formula.append([-g.tent_var(r, c), -g.tent_var(nr, nc)])

    # Constraint 5: Row sums
    for r, row_sum in enumerate(g.row_clues):
        row_vars = [g.tent_var(r, c) for c in range(g.cols) if (r, c) not in tree_set]
        if row_vars:
            cnf = CardEnc.equals(lits=row_vars, bound=row_sum, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)
            if cnf.nv and cnf.nv >= next_aux_var:
                next_aux_var = cnf.nv + 1

    # Constraint 6: Column sums
    for c, col_sum in enumerate(g.col_clues):
        col_vars = [g.tent_var(r, c) for r in range(g.rows) if (r, c) not in tree_set]
        if col_vars:
            cnf = CardEnc.equals(lits=col_vars, bound=col_sum, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)
            if cnf.nv and cnf.nv >= next_aux_var:
                next_aux_var = cnf.nv + 1

    return formula


def decode(model: List[int], g: TentsGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output uses the same encoding as the puzzle generator:
    - 1: Tree (unchanged)
    - -3: Tent placed
    - -4: No tent (empty)
    """
    model_set = set(model)
    solution = [row[:] for row in g.grid]

    tree_set = set(g.trees)
    for r in range(g.rows):
        for c in range(g.cols):
            if (r, c) not in tree_set:
                var = g.tent_var(r, c)
                solution[r][c] = -3 if var in model_set else -4

    return solution


@register_solver("tents")
def solve_tents(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a tents puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state',
                    'row_tent_counts', 'col_tent_counts'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = TentsGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
            row_clues=puzzle_data['row_tent_counts'],
            col_clues=puzzle_data['col_tent_counts'],
        )

        formula = encode(g)

        solutions = []
        tree_set = set(g.trees)

        with Solver(name='glucose4', bootstrap_with=formula) as solver:
            while len(solutions) < max_solutions:
                if not solver.solve():
                    break

                model = solver.get_model()
                solution = decode(model, g)
                solutions.append(solution)

                # Block this solution - only consider non-tree cells
                blocking_clause = []
                for r in range(g.rows):
                    for c in range(g.cols):
                        if (r, c) not in tree_set:
                            var = g.tent_var(r, c)
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
