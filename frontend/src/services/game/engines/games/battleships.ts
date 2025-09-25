import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { BattleshipsMeta, PuzzleDefinition } from "@/services/game/engines/types.ts";
import { StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";
import { BattleshipsCell, TentsCell } from "@/services/game/engines/translator.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";

export class EngineBattleships<T = BattleshipsMeta> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [new StateCyclingInputHandler([BattleshipsCell.EMPTY.valueOf(), BattleshipsCell.SHIP.valueOf(), BattleshipsCell.WATER.valueOf()])],
      [
        // no_adjacent_tents(),
        // validate_trees_have_tent_access(),
        // validate_line_sums_exceeded("row", TentsCell.TENT, "row_tent_counts"),
        // validate_line_sums_exceeded("col", TentsCell.TENT, "col_tent_counts"),
        // validate_line_all_negative("row", TentsCell.GREEN, "row_tent_counts", [TentsCell.TREE]),
        // validate_line_all_negative("col", TentsCell.GREEN, "col_tent_counts", [TentsCell.TREE]),
      ],
    );
  }

  can_modify_cell = (cell: Cell): boolean => this.initial_state[cell.row][cell.col] !== TentsCell.TREE.valueOf();
}
