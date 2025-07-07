import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { StateCyclingInputHandler } from "@/services/game/engines/handlers.ts";
import { LightupCell } from "@/services/game/engines/translator.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import {
  no_bulbs_lighting_each_other,
  validate_numbered_wall_constraints,
} from "@/services/game/engines/rules/lightup.ts";

export class EngineLightup<T> extends PuzzleEngine<T> {
  constructor(definition: PuzzleDefinition<T>, board_state?: number[][]) {
    super(
      definition,
      board_state,
      [
        new StateCyclingInputHandler([
          LightupCell.EMPTY.valueOf(),
          LightupCell.BULB.valueOf(),
          LightupCell.CROSS.valueOf(),
        ]),
      ],
      [no_bulbs_lighting_each_other(), validate_numbered_wall_constraints()],
    );
  }

  can_modify_cell = (cell: Cell): boolean => this.initial_state[cell.row][cell.col] === LightupCell.EMPTY.valueOf();
}
