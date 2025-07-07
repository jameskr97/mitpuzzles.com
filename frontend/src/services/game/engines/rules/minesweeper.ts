import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";
import { MinesweeperCell } from "@/services/game/engines/translator.ts";

// Use RuleDefinition from PuzzleEngine (implicitly) by matching its structure
export function validate_flags_around_number(): RuleDefinition {
  /**
   * Generate a rule to validate that numbered cells don't have more surrounding flags
   * than their number indicates.
   */
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const state = engine.board_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    // All 8 directions (including diagonals) for minesweeper
    const directions = [
      [-1, -1],
      [-1, 0],
      [-1, 1],
      [0, -1],
      [0, 1],
      [1, -1],
      [1, 0],
      [1, 1],
    ];

    const violatingNumberLocations: Array<RuleViolationCell> = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cellValue = state[r][c];

        // Skip if not a numbered cell (assuming numbers are 1-8)
        if (typeof cellValue !== "number" || cellValue < 1 || cellValue > 8) {
          continue;
        }

        // Count surrounding flags
        let flagCount = 0;
        for (const [dr, dc] of directions) {
          const nr = r + dr;
          const nc = c + dc;

          if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
            if (state[nr][nc] === MinesweeperCell.FLAG) {
              flagCount++;
            }
          }
        }

        // Check if too many flags
        if (flagCount > cellValue) {
          violatingNumberLocations.push({ row: r, col: c });
        }
      }
    }

    if (violatingNumberLocations.length === 0) {
      return null;
    }

    return {
      locations: violatingNumberLocations,
      rule_name: "minesweeper_surrounding_flag_violation",
    };
  }

  return { rule_func: rule };
}
