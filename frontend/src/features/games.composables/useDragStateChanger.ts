import { inject, ref } from "vue";
import type { GameZone, Cell, BoardEvents } from "@/features/games.components/board.interaction.ts";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { type GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { ModuleManager } from "@/services/eventbus.ts";

/**
 * Composable handles mouse drag events to change the state of the puzzle board.
 */
export function useDragStateChanger(session: Awaited<ReturnType<typeof createPuzzleSession>>): Partial<BoardEvents> {
  const event_modules = inject<ModuleManager>("event_modules");
  const game_module = event_modules?.getComposable?.<GameModuleInterface>("game");

  const isMouseDown = ref(false);
  let activeZone: GameZone | null = null;
  let firstClickedCell: Cell | null = null;

  function onCellMouseDown(cell: Cell, _event: MouseEvent): boolean {
    isMouseDown.value = true;
    activeZone = cell.zone;
    firstClickedCell = cell;
    return false;
  }

  function onMouseUp(_: MouseEvent): boolean {
    isMouseDown.value = false;
    activeZone = null;
    return false;
  }

  function onCellEnter(cell: Cell, event: MouseEvent): boolean {
    if (isMouseDown.value == false || cell.zone !== activeZone || firstClickedCell == null) return false;
    const desiredState =
      session.state.value?.board[firstClickedCell.row * session.state.value.cols + firstClickedCell.col];
    const currentState = session.state.value?.board[cell.row * session.state.value.cols + cell.col];

    // do nothing if the state is the same
    if (currentState === desiredState) return false;
    game_module?.handle_cell_click(cell, event.button, desiredState);
    return true; // return true to indicate that the event was handled
  }

  return {
    onCellMouseDown,
    onMouseUp,
    onCellEnter,
  };
}
