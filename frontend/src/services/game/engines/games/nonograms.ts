import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { NonogramMeta, PuzzleDefinition } from "@/services/game/engines/types.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { NonogramsCell } from "@/services/game/engines/translator.ts";
import { StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";

export class EngineNonograms<T = NonogramMeta> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [
        new StateCyclingInputHandler(NonogramsCell),
      ],
      [
        // validate_line_sums("row", NonogramsCell.BLACK, "row_sums", true),
        // validate_line_sums("col", NonogramsCell.BLACK, "col_sums", true),
        // validate_line_all_negative("row", NonogramsCell.CROSS, "row_sums"),
        // validate_line_all_negative("col", NonogramsCell.CROSS, "col_sums"),
      ],
    );
  }

  can_modify_cell = (cell: Cell): boolean => true;
}
