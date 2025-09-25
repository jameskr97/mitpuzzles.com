import { type InputHandler, PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { CellType } from "@/services/game/engines/translator.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { PuzzleOps } from "@/services/game/engines/PuzzleOps.ts";

export class StateCyclingInputHandler implements Partial<InputHandler> {
  private states: number[];

  constructor(states: CellType | CellType[]) {
    if (Array.isArray(states)) {
      // If it's an array, use the values directly
      this.states = states;
    } else {
      // If it's an enum object, extract just the numeric values
      this.states = Object.values(states).filter((v) => typeof v === "number") as number[];
    }
  }

  on_cell_click(engine: PuzzleEngine, cell: Cell, button: number, override?: number): boolean {
    if (cell.zone !== "game") return false;
    const current = engine.board_state[cell.row][cell.col];

    if (override !== undefined) {
      if (this.states.includes(override)) {
        engine.board_state[cell.row][cell.col] = override;
        return true;
      }
      return false;
    }
    const currentIndex = this.states.indexOf(current);
    let nextIndex;
    if (button === 2) {
      nextIndex = (currentIndex - 1 + this.states.length) % this.states.length;
    } else {
      nextIndex = (currentIndex + 1) % this.states.length;
    }

    engine.board_state[cell.row][cell.col] = this.states[nextIndex];
    return true;
  }
}

export class LineStateToggler implements Partial<InputHandler> {
  constructor(
    private from_state: number,
    private to_state: number,
  ) {}

  on_cell_click(engine: PuzzleEngine, cell: Cell, button: number, override?: number): boolean {
    if (!["topGutter", "leftGutter"].includes(cell.zone)) return false;
    const is_row = cell.zone === "leftGutter";
    const index = is_row ? cell.row : cell.col;
    PuzzleOps.change_line_state(
      is_row,
      index,
      engine.board_state,
      engine.definition.rows,
      engine.definition.cols,
      this.from_state,
      this.to_state,
    );
    return true;
  }
}
