import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { MosaicCell } from "@/services/game/engines/translator.ts";
import { StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";
import { validate_shaded_count_in_3x3_region } from "@/services/game/engines/rules/mosaic.ts";

export class EngineMosaic<T> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [
        new StateCyclingInputHandler([
          MosaicCell.UNMARKED.valueOf(),
          MosaicCell.SHADED.valueOf(),
          MosaicCell.CROSS.valueOf(),
        ]),
      ],
      [validate_shaded_count_in_3x3_region()],
    );

    // convert all numbered cells (0-9) in board_state to UNMARKED
    // the numbers are preserved in initial_state for display
    for (let row = 0; row < this.board_state.length; row++) {
      for (let col = 0; col < this.board_state[row].length; col++) {
        const cell_value = this.board_state[row][col];
        if (cell_value >= MosaicCell.ZERO && cell_value <= MosaicCell.NINE) {
          this.board_state[row][col] = MosaicCell.UNMARKED;
        }
      }
    }
  }

  can_modify_cell = (cell: Cell): boolean => {
    // All cells can be modified in mosaic (numbers can be shaded too)
    return true;
  }
}
