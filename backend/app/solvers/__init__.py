"""
Puzzle solvers package.
Contains SAT-based solvers for various puzzle types.
"""

from .base import SolverResult
from .registry import get_solver, supports_solver, solve

# Import solvers to register them
from . import lightup
from . import minesweeper
from . import mosaic
from . import tents
from . import aquarium
from . import kakurasu
from . import nonograms
from . import sudoku
from . import hashi

__all__ = ["SolverResult", "get_solver", "supports_solver", "solve"]
