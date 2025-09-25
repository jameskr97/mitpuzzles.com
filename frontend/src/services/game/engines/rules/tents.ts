/* tentsRules.ts */
import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";
import { TentsCell } from "@/services/game/engines/translator.ts"; // enum { Empty, Tent, Tree, Green, … }

/* helper */
const isInBounds = (r: number, c: number, rows: number, cols: number) => r >= 0 && r < rows && c >= 0 && c < cols;

/* ────────────────────────────── 1. no adjacent tents ────────────────────────────── */

export function no_adjacent_tents(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const dirs = [
      [-1, -1],
      [-1, 0],
      [-1, 1],
      [0, -1],
      [0, 1],
      [1, -1],
      [1, 0],
      [1, 1],
    ];

    const violating: RuleViolationCell[] = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (state[r][c] !== TentsCell.TENT) continue;

        // Any neighbouring tent? (break after first hit)
        for (const [dr, dc] of dirs) {
          const nr = r + dr,
            nc = c + dc;
          if (isInBounds(nr, nc, rows, cols) && state[nr][nc] === TentsCell.TENT) {
            violating.push({ row: r, col: c });
            break;
          }
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: "tents_intersecting" } : null;
  }

  return { rule_func: rule };
}

/* ───────────────────── 2. row / column tent-count validation ───────────────────── */

export function validate_tent_counts(axis: "row" | "col"): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;
    const meta = engine.definition.meta as {
      row_tent_counts: number[];
      col_tent_counts: number[];
    };

    const violating: RuleViolationCell[] = [];

    if (axis === "row") {
      const targets = meta.row_tent_counts;
      for (let r = 0; r < rows; r++) {
        const tents = state[r].filter((v) => v === TentsCell.TENT).length;
        if (tents > targets[r]) violating.push({ row: r, col: -1 });
      }
    } else {
      // "col"
      const targets = meta.col_tent_counts;
      for (let c = 0; c < cols; c++) {
        let tents = 0;
        for (let r = 0; r < rows; r++) {
          if (state[r][c] === TentsCell.TENT) tents++;
        }
        if (tents > targets[c]) violating.push({ row: -1, col: c });
      }
    }

    return violating.length ? { locations: violating, rule_name: `tent_count_${axis}_mismatch` } : null;
  }

  return { rule_func: rule };
}

/* ─────────────────── 3. every tree must still be able to get a tent ─────────────────── */

export function validate_trees_have_tent_access(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const dirs = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1], // cardinal only
    ];

    const violating: RuleViolationCell[] = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (state[r][c] !== TentsCell.TENT) continue;

        let hasAdjacentTent = false;
        let canPlaceTent = false;

        for (const [dr, dc] of dirs) {
          const nr = r + dr,
            nc = c + dc;
          if (!isInBounds(nr, nc, rows, cols)) continue;

          const cell = state[nr][nc];
          if (cell === TentsCell.TENT) {
            hasAdjacentTent = true;
            break;
          } else if (cell === TentsCell.EMPTY) {
            canPlaceTent = true;
          }
        }

        if (!hasAdjacentTent && !canPlaceTent) {
          violating.push({ row: r, col: c });
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: "tree_inaccessible" } : null;
  }

  return { rule_func: rule };
}
