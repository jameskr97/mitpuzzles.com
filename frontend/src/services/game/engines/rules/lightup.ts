import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";
import { LightupCell } from "@/services/game/engines/translator.ts";

/* ───────────────────────── helper ───────────────────────── */
const inBounds = (r: number, c: number, rows: number, cols: number) => r >= 0 && r < rows && c >= 0 && c < cols;

export function no_bulbs_lighting_each_other(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const wallValues = new Set<number>([
      LightupCell.WALL_0,
      LightupCell.WALL_1,
      LightupCell.WALL_2,
      LightupCell.WALL_3,
      LightupCell.WALL_4,
      LightupCell.WALL_NO_CONSTRAINT,
    ]);

    const bulbs: [number, number][] = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (state[r][c] === LightupCell.BULB) bulbs.push([r, c]);
      }
    }

    /* cast rays from each bulb */
    const hit = new Set<string>();
    const dirs = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1],
    ];

    for (const [r, c] of bulbs) {
      for (const [dr, dc] of dirs) {
        let nr = r + dr,
          nc = c + dc;
        while (inBounds(nr, nc, rows, cols) && !wallValues.has(state[nr][nc] as number)) {
          if (state[nr][nc] === LightupCell.BULB) {
            hit.add(`${r},${c}`);
            hit.add(`${nr},${nc}`);
            break; // stop in this direction
          }
          nr += dr;
          nc += dc;
        }
      }
    }

    if (hit.size === 0) return null;

    const locations: RuleViolationCell[] = Array.from(hit).map((key) => {
      const [row, col] = key.split(",").map(Number);
      return { row, col };
    });

    return {
      locations,
      rule_name: "bulb_intersection_violation",
    };
  }

  return { rule_func: rule };
}

/* ======================================================================
 * 2. Numbered walls must not have *more* adjacent bulbs than the number.
 * ==================================================================== */
export function validate_numbered_wall_constraints(): RuleDefinition {
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const dirs = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1],
    ];

    const numberedWalls = [
      LightupCell.WALL_0,
      LightupCell.WALL_1,
      LightupCell.WALL_2,
      LightupCell.WALL_3,
      LightupCell.WALL_4,
    ];

    const violating: RuleViolationCell[] = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = state[r][c];
        if (!numberedWalls.includes(cell as number)) continue;

        const required = cell as number; // Wall0 ⇒ 0, Wall1 ⇒ 1, …

        let bulbs = 0;
        for (const [dr, dc] of dirs) {
          const nr = r + dr,
            nc = c + dc;
          if (inBounds(nr, nc, rows, cols) && state[nr][nc] === LightupCell.BULB) {
            bulbs++;
          }
        }

        if (bulbs > required) violating.push({ row: r, col: c });
      }
    }

    return violating.length ? { locations: violating, rule_name: "numbered_wall_constraint_violated" } : null;
  }

  return { rule_func: rule };
}
