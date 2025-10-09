import { type InputHandler, PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { SudokuCell } from "@/services/game/engines/translator.ts";
import {
  no_duplicate_numbers_in_boxes,
  no_duplicate_numbers_in_cols,
  no_duplicate_numbers_in_rows,
} from "@/services/game/engines/rules/sudoku.ts";

export class SudokuInputHandler implements Partial<InputHandler> {
  on_cell_key_down(engine: PuzzleEngine, cell: Cell, key: string): boolean {
    if (cell.zone !== "game") return false;

    // Handle backspace/delete to clear cell
    if (key === "Backspace" || key === "Delete") {
      engine.board_state[cell.row][cell.col] = 0;
      return true;
    }

    // Handle numeric input
    const num = parseInt(key);
    if (isNaN(num) || num < 1 || num > engine.definition.rows) return false;
    engine.board_state[cell.row][cell.col] = num;
    return true;
  }
}

export class EngineSudoku<T> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [new SudokuInputHandler()],
      [no_duplicate_numbers_in_rows(), no_duplicate_numbers_in_cols(), no_duplicate_numbers_in_boxes()],
    );
  }

  can_modify_cell = (cell: Cell): boolean => this.initial_state[cell.row][cell.col] === SudokuCell.EMPTY;
}
