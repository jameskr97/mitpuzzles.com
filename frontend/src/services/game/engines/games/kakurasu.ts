import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { KakurasuMeta, PuzzleDefinition } from "@/services/game/engines/types.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { KakurasuCell } from "@/services/game/engines/translator.ts";
import { LineStateToggler, StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";
import { validate_line_all_negative, validate_line_sums } from "@/services/game/engines/rules/generic.ts";

export class EngineKakurasu<T = KakurasuMeta> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [
        new StateCyclingInputHandler(KakurasuCell),
        new LineStateToggler(KakurasuCell.EMPTY.valueOf(), KakurasuCell.CROSS.valueOf()),
      ],
      [
        validate_line_sums("row", KakurasuCell.BLACK, "row_sums", true),
        validate_line_sums("col", KakurasuCell.BLACK, "col_sums", true),
        validate_line_all_negative("row", KakurasuCell.CROSS, "row_sums"),
        validate_line_all_negative("col", KakurasuCell.CROSS, "col_sums"),
      ],
    );
  }

  can_modify_cell = (cell: Cell): boolean => true;
}
