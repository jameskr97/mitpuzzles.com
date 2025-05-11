import { ref, type Ref } from "vue";
import type { MutablePuzzleState } from "@/services/states.ts";
import type { GameZone } from "@/features/games/components/board.interaction.ts";

/**
 * Composable handles mouse drag events to change the state of the puzzle board.
 *
 * @param stateRef - Reactive reference to the mutable puzzle state.
 * @param canModifyCell - Optional function to determine if a cell can be modified.
 */
export function useDragStateChanger<T extends MutablePuzzleState>(
  stateRef: Ref<T>,
  canModifyCell?: (row: number, col: number, state: T) => boolean,
) {
  const getIndex = (row: number, col: number) => row * stateRef.value.cols + col;
  const isMouseDown = ref(false);
  let appliedState: number | null = null;
  let activeZone: GameZone | null = null;

  function onMouseDown(zone: GameZone, row: number, col: number) {
    const i = getIndex(row, col);
    appliedState = stateRef.value.board[i]; // capture current state after cycler has updated it
    isMouseDown.value = true;
    activeZone = zone;
  }

  function onMouseUp() {
    isMouseDown.value = false;
    appliedState = null;
    activeZone = null;
  }

  function onMouseEnter(zone: GameZone, row: number, col: number) {
    if (!isMouseDown.value || appliedState === null || zone !== activeZone) return;

    const i = getIndex(row, col);
    if (canModifyCell?.(row, col, stateRef.value) !== false && stateRef.value.board[i] !== appliedState) {
      stateRef.value.board[i] = appliedState;
    }
  }

  return {
    onMouseDown,
    onMouseUp,
    onMouseEnter,
  };
}
