import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";
import { SudokuCell } from "@/services/game/engines/translator.ts";

export function no_duplicate_numbers_in_rows(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state; // number[][]
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const violating: RuleViolationCell[] = [];

    for (let r = 0; r < rows; r++) {
      const seen = new Map<unknown, number>(); // value → first-col
      for (let c = 0; c < cols; c++) {
        const value = state[r][c];
        if (value === SudokuCell.EMPTY) continue;

        if (seen.has(value)) {
          violating.push({ row: r, col: seen.get(value)! });
          violating.push({ row: r, col: c });
        } else {
          seen.set(value, c);
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: "row_duplicate_violation" } : null;
  }

  return { rule_func: rule };
}

/* ---------- 2. duplicate numbers in columns ---------- */

export function no_duplicate_numbers_in_cols(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const violating: RuleViolationCell[] = [];

    for (let c = 0; c < cols; c++) {
      const seen = new Map<unknown, number>(); // value → first-row
      for (let r = 0; r < rows; r++) {
        const value = state[r][c];
        if (value === SudokuCell.EMPTY) continue;

        if (seen.has(value)) {
          violating.push({ row: seen.get(value)!, col: c });
          violating.push({ row: r, col: c });
        } else {
          seen.set(value, r);
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: "col_duplicate_violation" } : null;
  }

  return { rule_func: rule };
}

/* ---------- 3. duplicate numbers in boxes ---------- */

export function no_duplicate_numbers_in_boxes(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const boxSize = Math.sqrt(rows); // 4×4 → 2, 9×9 → 3 …
    if (!Number.isInteger(boxSize)) return null; // non-square board → skip

    const violating: RuleViolationCell[] = [];

    for (let br = 0; br < rows; br += boxSize) {
      for (let bc = 0; bc < cols; bc += boxSize) {
        const seen = new Map<unknown, RuleViolationCell>(); // value → first cell

        for (let r = br; r < br + boxSize; r++) {
          for (let c = bc; c < bc + boxSize; c++) {
            const value = state[r][c];
            if (value === SudokuCell.EMPTY) continue;

            if (seen.has(value)) {
              violating.push(seen.get(value)!);
              violating.push({ row: r, col: c });
            } else {
              seen.set(value, { row: r, col: c });
            }
          }
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: "box_duplicate_violation" } : null;
  }

  return { rule_func: rule };
}
