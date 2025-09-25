/* lineRules.ts
 * Generic line-validation helpers (rows / columns)
 */
import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";

/* ────────────────────────────── helpers ────────────────────────────── */

const makeLineCoords = (axis: "row" | "col", idx: number): RuleViolationCell =>
  axis === "row" ? { row: idx, col: -1 } : { row: -1, col: idx };

const isPositive = (cell: unknown, value: number) => cell === value;

/* ─────────────────────── 1. validate_line_sums ───────────────────────
 * Counts / weighted-counts of `targetValue` in each line must NOT exceed the
 * corresponding value in meta[targetsKey].
 */
export function validate_line_sums(
  axis: "row" | "col",
  targetValue: number,
  targetsKey: string,
  weighted = false,
): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;
    const targets: number[] = engine.definition.meta[targetsKey];

    const violating: RuleViolationCell[] = [];

    if (axis === "row") {
      for (let r = 0; r < rows; r++) {
        const total = weighted
          ? state[r].map((cell, c) => (cell === targetValue ? c + 1 : 0)).reduce((a, b) => a + b, 0)
          : state[r].filter((cell) => cell === targetValue).length;

        if (total > targets[r]) violating.push(makeLineCoords("row", r));
      }
    } else {
      for (let c = 0; c < cols; c++) {
        let total = 0;
        for (let r = 0; r < rows; r++) {
          if (state[r][c] === targetValue) {
            total += weighted ? r + 1 : 1;
          }
        }
        if (total > targets[c]) violating.push(makeLineCoords("col", c));
      }
    }

    return violating.length ? { locations: violating, rule_name: `line_sum_${axis}_exceeded` } : null;
  }

  return { rule_func: rule };
}

/* ──────────────── 2. validate_line_sums_exceeded (positive) ────────────────
 * Same idea but explicitly names the positive value being summed.
 */
export function validate_line_sums_exceeded(
  axis: "row" | "col",
  positiveValue: number,
  targetsKey: string,
  weighted = false,
): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;
    const targets: number[] = engine.definition.meta[targetsKey];

    const violating: RuleViolationCell[] = [];

    const calcLineSum = (cells: number[]): number =>
      cells.reduce((acc, cell, idx) => {
        return acc + (cell === positiveValue ? (weighted ? idx + 1 : 1) : 0);
      }, 0);

    if (axis === "row") {
      for (let r = 0; r < rows; r++) {
        const total = calcLineSum(state[r]);
        if (total > targets[r]) violating.push(makeLineCoords("row", r));
      }
    } else {
      for (let c = 0; c < cols; c++) {
        const colCells = Array.from({ length: rows }, (_, r) => state[r][c]);
        const total = calcLineSum(colCells);
        if (total > targets[c]) violating.push(makeLineCoords("col", c));
      }
    }

    return violating.length ? { locations: violating, rule_name: `line_sum_${axis}_exceeded` } : null;
  }

  return { rule_func: rule };
}

/* ──────────────── 3. validate_line_all_negative ────────────────
 * Flags a line if **all** relevant cells are `negativeValue`
 * (after ignoring any `ignoredValues`) **and** the target for that line
 * is greater than zero.
 */
export function validate_line_all_negative(
  axis: "row" | "col",
  negativeValue: number,
  targetsKey: string,
  ignoredValues: number[] = [],
): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;
    const targets: number[] = engine.definition.meta[targetsKey];

    const violating: RuleViolationCell[] = [];

    const isRelevant = (cell: unknown) => !ignoredValues.includes(cell as number);

    if (axis === "row") {
      for (let r = 0; r < rows; r++) {
        const relevant = state[r].filter(isRelevant);
        if (relevant.length && relevant.every((cell) => cell === negativeValue) && targets[r] > 0) {
          violating.push(makeLineCoords("row", r));
        }
      }
    } else {
      for (let c = 0; c < cols; c++) {
        const colCells = Array.from({ length: rows }, (_, r) => state[r][c]);
        const relevant = colCells.filter(isRelevant);
        if (relevant.length && relevant.every((cell) => cell === negativeValue) && targets[c] > 0) {
          violating.push(makeLineCoords("col", c));
        }
      }
    }

    return violating.length ? { locations: violating, rule_name: `line_all_${axis}_negative` } : null;
  }

  return { rule_func: rule };
}
