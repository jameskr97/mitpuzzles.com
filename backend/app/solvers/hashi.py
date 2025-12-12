"""
Hashi (Bridges) puzzle solver using SAT.

Rules:
- Islands have numbers indicating total bridges needed
- Connect islands with 0, 1, or 2 bridges horizontally or vertically
- Bridges cannot cross other bridges
- All islands must be connected (form a single connected component)

Cell values in initial_state:
- 0: Empty cell
- 1-8: Island with that many bridges required

Solution format:
- bridges: List of {island1: [r,c], island2: [r,c], count: 1|2}
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Any, Optional
from itertools import combinations
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

from .base import SolverResult
from .registry import register_solver


@dataclass
class HashiGrid:
    """Represents a hashi grid for SAT encoding."""
    rows: int
    cols: int
    grid: List[List[int]]
    islands: List[Tuple[int, int, int]] = field(default_factory=list)  # (row, col, count)
    bridges: List[Tuple[Tuple[int, int], Tuple[int, int]]] = field(default_factory=list)
    bridge_to_idx: Dict[Tuple[Tuple[int, int], Tuple[int, int]], int] = field(default_factory=dict)

    def __post_init__(self):
        # Find all islands
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] > 0:
                    self.islands.append((r, c, self.grid[r][c]))

        # Find all possible bridges between adjacent islands
        island_coords = {(r, c) for r, c, _ in self.islands}
        for r, c, _ in self.islands:
            # Check right
            for c2 in range(c + 1, self.cols):
                if (r, c2) in island_coords:
                    self._add_bridge((r, c), (r, c2))
                    break
            # Check down
            for r2 in range(r + 1, self.rows):
                if (r2, c) in island_coords:
                    self._add_bridge((r, c), (r2, c))
                    break

    def _add_bridge(self, island1: Tuple[int, int], island2: Tuple[int, int]):
        """Add a potential bridge, normalized so island1 < island2."""
        if island1 > island2:
            island1, island2 = island2, island1
        if (island1, island2) not in self.bridge_to_idx:
            self.bridge_to_idx[(island1, island2)] = len(self.bridges)
            self.bridges.append((island1, island2))

    def bridge_var(self, bridge_idx: int, count: int) -> int:
        """Get SAT variable for 'bridge bridge_idx has exactly count bridges'.
        count is 1 or 2. Variables are 1-indexed.
        bridge_idx * 2 + (count - 1) + 1
        """
        return bridge_idx * 2 + count

    def get_bridges_for_island(self, r: int, c: int) -> List[int]:
        """Get indices of all bridges connected to island at (r, c)."""
        island = (r, c)
        result = []
        for (i1, i2), idx in self.bridge_to_idx.items():
            if i1 == island or i2 == island:
                result.append(idx)
        return result


def do_bridges_intersect(bridge1: Tuple[Tuple[int, int], Tuple[int, int]],
                          bridge2: Tuple[Tuple[int, int], Tuple[int, int]]) -> bool:
    """Check if two bridges intersect (one horizontal, one vertical crossing)."""
    (r1, c1), (r2, c2) = bridge1
    (r3, c3), (r4, c4) = bridge2

    bridge1_horizontal = r1 == r2
    bridge2_horizontal = r3 == r4

    # If both same orientation, they can't cross
    if bridge1_horizontal == bridge2_horizontal:
        return False

    if bridge1_horizontal:
        # Bridge 1 is horizontal, Bridge 2 is vertical
        h_row = r1
        h_col_min, h_col_max = min(c1, c2), max(c1, c2)
        v_col = c3
        v_row_min, v_row_max = min(r3, r4), max(r3, r4)

        # Check if they cross (strictly interior, not at endpoints)
        return (h_col_min < v_col < h_col_max and
                v_row_min < h_row < v_row_max)
    else:
        # Bridge 1 is vertical, Bridge 2 is horizontal
        v_col = c1
        v_row_min, v_row_max = min(r1, r2), max(r1, r2)
        h_row = r3
        h_col_min, h_col_max = min(c3, c4), max(c3, c4)

        return (h_col_min < v_col < h_col_max and
                v_row_min < h_row < v_row_max)


def encode(g: HashiGrid) -> Tuple[CNF, int]:
    """Encode Hashi puzzle as CNF formula.

    Returns:
        Tuple of (CNF formula, next_aux_var for additional encoding)
    """
    formula = CNF()

    # Variables: for each bridge, we have 2 variables:
    # bridge_var(idx, 1) = "bridge idx has at least 1 bridge"
    # bridge_var(idx, 2) = "bridge idx has exactly 2 bridges"
    # So count = 0 means neither true, count = 1 means var1 true & var2 false,
    # count = 2 means both true

    # Reserve variables: 2 per bridge
    next_aux_var = len(g.bridges) * 2 + 1

    # Constraint: if bridge has 2, it must have 1 (var2 -> var1)
    for idx in range(len(g.bridges)):
        var1 = g.bridge_var(idx, 1)
        var2 = g.bridge_var(idx, 2)
        # var2 -> var1: (-var2 or var1)
        formula.append([-var2, var1])

    # Constraint: Each island must have exactly the required number of bridges
    for r, c, required in g.islands:
        bridge_indices = g.get_bridges_for_island(r, c)

        if not bridge_indices and required > 0:
            # Island needs bridges but has none possible - UNSAT
            formula.append([])
            continue

        # Sum of bridges = required
        # Each bridge contributes: 0 if neither var, 1 if var1 only, 2 if var1 and var2
        # We encode: sum of all var1 + sum of all var2 = required
        # (since var2 -> var1, if var2 is true, var1 is also true, so total is 2)

        all_vars = []
        for idx in bridge_indices:
            all_vars.append(g.bridge_var(idx, 1))
            all_vars.append(g.bridge_var(idx, 2))

        # Sum of all these vars = required
        cnf = CardEnc.equals(lits=all_vars, bound=required, top_id=next_aux_var, encoding=EncType.seqcounter)
        formula.extend(cnf.clauses)
        if cnf.nv and cnf.nv >= next_aux_var:
            next_aux_var = cnf.nv + 1

    # Constraint: Bridges cannot cross
    for i in range(len(g.bridges)):
        for j in range(i + 1, len(g.bridges)):
            if do_bridges_intersect(g.bridges[i], g.bridges[j]):
                # At most one can have bridges (if either has count >= 1, other must have 0)
                # NOT (bridge_i has >= 1 AND bridge_j has >= 1)
                # = NOT var_i_1 OR NOT var_j_1
                var_i = g.bridge_var(i, 1)
                var_j = g.bridge_var(j, 1)
                formula.append([-var_i, -var_j])

    return formula, next_aux_var


def check_connectivity(g: HashiGrid, model_set: Set[int]) -> bool:
    """Check if all islands are connected via bridges in the solution."""
    if len(g.islands) <= 1:
        return True

    # Build adjacency from model
    adjacency: Dict[Tuple[int, int], List[Tuple[int, int]]] = {(r, c): [] for r, c, _ in g.islands}

    for idx, (island1, island2) in enumerate(g.bridges):
        var1 = g.bridge_var(idx, 1)
        if var1 in model_set:  # Has at least one bridge
            adjacency[island1].append(island2)
            adjacency[island2].append(island1)

    # BFS from first island
    start = (g.islands[0][0], g.islands[0][1])
    visited = {start}
    queue = [start]

    while queue:
        current = queue.pop(0)
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return len(visited) == len(g.islands)


def decode(model: List[int], g: HashiGrid) -> List[Dict[str, Any]]:
    """Convert SAT model to solution bridges.

    Output: List of bridge dicts with island1, island2, count
    """
    model_set = set(model)
    solution = []

    for idx, (island1, island2) in enumerate(g.bridges):
        var1 = g.bridge_var(idx, 1)
        var2 = g.bridge_var(idx, 2)

        if var2 in model_set:
            count = 2
        elif var1 in model_set:
            count = 1
        else:
            count = 0

        if count > 0:
            solution.append({
                "island1": list(island1),
                "island2": list(island2),
                "count": count
            })

    return solution


@register_solver("hashi")
def solve_hashi(puzzle_data: Dict[str, Any], max_solutions: int = 10) -> SolverResult:
    """
    Solve a hashi puzzle and check for unique solution.

    Args:
        puzzle_data: Normalized puzzle with 'rows', 'cols', 'initial_state'
        max_solutions: Maximum solutions to enumerate

    Returns:
        SolverResult with validity and uniqueness info
    """
    try:
        g = HashiGrid(
            rows=puzzle_data['rows'],
            cols=puzzle_data['cols'],
            grid=puzzle_data['initial_state'],
        )

        if len(g.islands) == 0:
            return SolverResult(
                is_valid=True,
                is_unique=True,
                solution_count=1,
                solutions=[[]],
            )

        formula, _ = encode(g)

        solutions = []
        with Solver(name='glucose4', bootstrap_with=formula) as solver:
            while len(solutions) < max_solutions:
                if not solver.solve():
                    break

                model = solver.get_model()
                model_set = set(model)

                # Check connectivity (this is hard to encode in SAT efficiently)
                if not check_connectivity(g, model_set):
                    # Block this solution and continue
                    blocking_clause = []
                    for idx in range(len(g.bridges)):
                        var1 = g.bridge_var(idx, 1)
                        var2 = g.bridge_var(idx, 2)
                        if var1 in model_set:
                            blocking_clause.append(-var1)
                        else:
                            blocking_clause.append(var1)
                        if var2 in model_set:
                            blocking_clause.append(-var2)
                        else:
                            blocking_clause.append(var2)
                    solver.add_clause(blocking_clause)
                    continue

                solution = decode(model, g)
                solutions.append(solution)

                # Block this solution
                blocking_clause = []
                for idx in range(len(g.bridges)):
                    var1 = g.bridge_var(idx, 1)
                    var2 = g.bridge_var(idx, 2)
                    if var1 in model_set:
                        blocking_clause.append(-var1)
                    else:
                        blocking_clause.append(var1)
                    if var2 in model_set:
                        blocking_clause.append(-var2)
                    else:
                        blocking_clause.append(var2)
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
