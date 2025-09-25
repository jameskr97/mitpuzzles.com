import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

/**
 * dwell behavior - delegates hover tracking to puzzle controller methods
 * the controller's hover methods handle the actual recording logic
 */
export function useDwellBehaviour(controller: PuzzleController) {
  function onCellEnter(cell: Cell, event: MouseEvent): boolean {
    // delegate to controller's hover start method
    if (controller.handle_hover_start) {
      controller.handle_hover_start(cell, event);
    }

    // return false to allow other behaviors to process this event
    return false;
  }

  function onCellLeave(cell: Cell, event: MouseEvent): boolean {
    // delegate to controller's hover end method
    if (controller.handle_hover_end) {
      controller.handle_hover_end(cell, event);
    }

    // return false to allow other behaviors to process this event
    return false;
  }

  return {
    onCellEnter,
    onCellLeave,
  };
}