"""
Light Up (Akari) puzzle solver using SAT.

Rules:
- Place light bulbs in white cells
- Every white cell must be illuminated
- Lights shine horizontally/vertically until blocked by black cell
- Lights cannot shine on each other
- Numbered black cells indicate exactly N adjacent lights

Cell values in initial_state (unsolved puzzle):
- -1: Empty white cell
- -2: Black wall (unnumbered)
- 0-4: Numbered black cell (indicates adjacent light count)

Cell values in solution (game_board):
- -3: Light bulb placed
- -4: No light (but cell is illuminated by another light)
- -2: Black wall (unnumbered)
- 0-4: Numbered black cell
"""

from dataclasses import dataclass, field
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class LightUpGrid:
    """Parsed Light Up puzzle grid."""
    rows: int
    cols: int
    grid: list
    white_cells: list = field(default_factory=list)
    black_cells: set = field(default_factory=set)
    numbered_cells: dict = field(default_factory=dict)

    def __post_init__(self):
        for r in range(self.rows):
            for c in range(self.cols):
                val = self.grid[r][c]
                if val == -1:
                    self.white_cells.append((r, c))
                elif val == -2:
                    self.black_cells.add((r, c))
                elif 0 <= val <= 4:
                    self.black_cells.add((r, c))
                    self.numbered_cells[(r, c)] = val

    def light_var(self, r, c):
        """SAT variable for light at (r, c). 1-indexed."""
        return r * self.cols + c + 1

    def visible_from(self, r, c):
        """Get all cells visible from (r, c) - same row/col until black cell."""
        visible = []

        # Left
        for nc in range(c - 1, -1, -1):
            if (r, nc) in self.black_cells:
                break
            visible.append((r, nc))

        # Right
        for nc in range(c + 1, self.cols):
            if (r, nc) in self.black_cells:
                break
            visible.append((r, nc))

        # Up
        for nr in range(r - 1, -1, -1):
            if (nr, c) in self.black_cells:
                break
            visible.append((nr, c))

        # Down
        for nr in range(r + 1, self.rows):
            if (nr, c) in self.black_cells:
                break
            visible.append((nr, c))

        return visible


def encode(g: LightUpGrid) -> CNF:
    """Encode Light Up puzzle as CNF formula."""
    formula = CNF()

    # Reserve variables 1 to rows*cols for cell lights
    # Auxiliary variables for cardinality constraints start after that
    next_aux_var = g.rows * g.cols + 1

    # Constraint 1: No lights on black cells
    for (r, c) in g.black_cells:
        formula.append([-g.light_var(r, c)])

    # Constraint 2: Numbered cells have exactly N adjacent lights
    for (r, c), count in g.numbered_cells.items():
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < g.rows and 0 <= nc < g.cols and (nr, nc) not in g.black_cells:
                neighbors.append(g.light_var(nr, nc))

        if neighbors:
            # Use top_id to avoid variable conflicts with cell variables
            cnf = CardEnc.equals(lits=neighbors, bound=count, top_id=next_aux_var, encoding=EncType.seqcounter)
            formula.extend(cnf.clauses)
            # Update next_aux_var based on what CardEnc used
            # Important: only increase, never decrease (cnf.nv may return max input var if no aux vars created)
            if cnf.nv and cnf.nv >= next_aux_var:
                next_aux_var = cnf.nv + 1
        elif count > 0:
            formula.append([])  # Empty clause = UNSAT

    # Constraint 3: Every white cell must be lit
    for (r, c) in g.white_cells:
        visible = g.visible_from(r, c)
        lit_by = [g.light_var(r, c)] + [g.light_var(vr, vc) for (vr, vc) in visible]
        formula.append(lit_by)

    # Constraint 4: No two lights can see each other
    for (r, c) in g.white_cells:
        for (vr, vc) in g.visible_from(r, c):
            formula.append([-g.light_var(r, c), -g.light_var(vr, vc)])

    return formula


def decode(model, g: LightUpGrid):
    """Convert SAT model to solution grid.

    Output uses the same encoding as the puzzle generator:
    - -3: Light bulb placed
    - -4: No light (illuminated by another light)
    """
    model_set = set(model)
    solution = [row[:] for row in g.grid]

    for r in range(g.rows):
        for c in range(g.cols):
            if g.grid[r][c] == -1:
                var = g.light_var(r, c)
                solution[r][c] = -3 if var in model_set else -4

    return solution


@register_solver("lightup")
def solve_lightup(puzzle_data, max_solutions=10) -> SolverResult:
    """Solve a Light Up puzzle."""
    try:
        g = LightUpGrid(
            rows=puzzle_data["rows"],
            cols=puzzle_data["cols"],
            grid=puzzle_data["initial_state"],
        )

        formula = encode(g)
        solutions = []

        with Solver(name="glucose4", bootstrap_with=formula) as solver:
            while len(solutions) < max_solutions:
                if not solver.solve():
                    break

                model = solver.get_model()
                solutions.append(decode(model, g))

                # Block this solution
                blocking = [-lit for lit in model if 1 <= abs(lit) <= g.rows * g.cols]
                solver.add_clause(blocking)

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
            solutions=[],
            error=str(e),
        )
