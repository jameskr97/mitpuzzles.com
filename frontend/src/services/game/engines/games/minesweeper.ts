import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { MinesweeperCell } from "@/services/game/engines/translator.ts";
import { StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";
import { validate_flags_around_number } from "@/services/game/engines/rules/minesweeper.ts";

export class EngineMinesweeper<T> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [
        new StateCyclingInputHandler([
          MinesweeperCell.UNMARKED.valueOf(),
          MinesweeperCell.FLAG.valueOf(),
          MinesweeperCell.SAFE.valueOf(),
        ]),
      ],
      [validate_flags_around_number()],
    );
  }

  can_modify_cell = (cell: Cell): boolean =>
    this.initial_state[cell.row][cell.col] === MinesweeperCell.UNMARKED.valueOf();
}
