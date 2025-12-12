"""
Minesweeper puzzle solver using SAT.

Rules:
- Each numbered cell indicates exactly how many adjacent cells contain mines
- Adjacent includes all 8 surrounding cells (including diagonals)
- Hidden cells either contain a mine (1) or are safe (0)

Cell values in initial_state (unsolved puzzle):
- 0-8: Revealed cell showing count of adjacent mines
- -1: Hidden/unknown cell

Cell values in solution:
- 0-8: Revealed cell (same as initial)
- -3: Mine (flag)
- -4: Safe (no mine)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class MinesweeperGrid:
    """Represents a minesweeper grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    hidden_cells: List[Tuple[int, int]] = field(default_factory=list)
    numbered_cells: Dict[Tuple[int, int], int] = field(default_factory=dict)

    def __post_init__(self):
        """Parse grid into cell types."""
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid[r][c]
                if val == -1:
                    self.hidden_cells.append((r, c))
                elif 0 <= val <= 8:
                    self.numbered_cells[(r, c)] = val

    def mine_var(self, r: int, c: int) -> int:
        """Get SAT variable for whether cell (r,c) has a mine. Variables start at 1."""
        return r * self.cols + c + 1

    def adjacent_cells(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get all 8-directionally adjacent cells."""
        adjacent = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    adjacent.append((nr, nc))
        return adjacent


def encode(g: MinesweeperGrid, n_mines: int = None) -> CNF:
    """Encode Minesweeper puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for cell mines
    # Auxiliary variables for cardinality constraints start after that
    next_aux_var = g.rows * g.cols + 1

    # Constraint 1: Revealed cells (0-8) cannot have mines
    for (r, c) in g.numbered_cells.keys():
        formula.append([-g.mine_var(r, c)])

    # Constraint 2: Each numbered cell has exactly N adjacent mines
    for (r, c), count in g.numbered_cells.items():
        adjacent = g.adjacent_cells(r, c)
        # Only count hidden cells - revealed cells can't have mines
        hidden_adjacent = [(nr, nc) for (nr, nc) in adjacent if (nr, nc) in g.hidden_cells]
        adjacent_vars = [g.mine_var(nr, nc) for (nr, nc) in hidden_adjacent]

        if adjacent_vars:
            cnf = CardEnc.equals(lits=adjacent_vars, bound=count, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)
            if cnf.nv and cnf.nv >= next_aux_var:
                next_aux_var = cnf.nv + 1
        elif count > 0:
            # No hidden adjacent cells but count > 0 means invalid puzzle
            formula.append([])  # Empty clause = UNSAT

    # Constraint 3: Total mine count (if provided)
    if n_mines is not None:
        mine_vars = [g.mine_var(r, c) for (r, c) in g.hidden_cells]
        if mine_vars:
            cnf = CardEnc.equals(lits=mine_vars, bound=n_mines, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)

    return formula


def decode(model: List[int], g: MinesweeperGrid) -> List[List[int]]:
    """Convert SAT model to solution grid.

    Output uses the same encoding as the puzzle generator:
    - -3: Mine (flag)
    - -4: Safe (no mine)
    - 0-8: Revealed cells (unchanged)
    """
    model_set = set(model)
    solution = [row[:] for row in g.grid]

    for r, c in g.hidden_cells:
        var = g.mine_var(r, c)
        solution[r][c] = -3 if var in model_set else -4

    return solution


@register_solver("minesweeper")
def solve_minesweeper(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a minesweeper puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state', and optionally 'n_mines'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = MinesweeperGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
        )

        n_mines = puzzle_data.get('n_mines')
        formula = encode(g, n_mines)

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
                for r, c in g.hidden_cells:
                    var = g.mine_var(r, c)
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
