import type {
  PuzzleEngine,
  RuleDefinition,
  RuleViolation,
  RuleViolationCell,
} from "@/services/game/engines/PuzzleEngine.ts";
import { MosaicCell } from "@/services/game/engines/translator.ts";

export function validate_shaded_count_in_3x3_region(): RuleDefinition {
  /**
   * Generate a rule to validate that numbered cells have the correct number
   * of shaded cells in their 3x3 region (including the numbered cell itself).
   */
  function rule(engine: PuzzleEngine): RuleViolation | null {
    const board_state = engine.board_state;
    const initial_state = engine.initial_state;
    const rows = engine.definition.rows;
    const cols = engine.definition.cols;

    const violating_number_locations: Array<RuleViolationCell> = [];

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        // Check initial_state for the number clue
        const initial_value = initial_state[r][c];

        // Skip if not a numbered cell (0-9)
        if (typeof initial_value !== "number" || initial_value < 0 || initial_value > 9) {
          continue;
        }

        const expected_count = initial_value;

        // Count shaded cells in 3x3 region centered on this cell
        let shaded_count = 0;

        // Check all 9 cells in the 3x3 region (including the center cell)
        for (let dr = -1; dr <= 1; dr++) {
          for (let dc = -1; dc <= 1; dc++) {
            const nr = r + dr;
            const nc = c + dc;

            // Skip if out of bounds
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) {
              continue;
            }

            // Count if the cell is shaded (check board_state for user markings)
            if (board_state[nr][nc] === MosaicCell.SHADED) {
              shaded_count++;
            }
          }
        }

        // Check if shaded count exceeds the expected count
        if (shaded_count > expected_count) {
          violating_number_locations.push({ row: r, col: c });
        }
      }
    }

    if (violating_number_locations.length === 0) {
      return null;
    }

    return {
      locations: violating_number_locations,
      rule_name: "mosaic_shaded_count_violation",
    };
  }

  return { rule_func: rule };
}
