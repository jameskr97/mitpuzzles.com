import { ref, type ShallowRef } from "vue";
import type { GridGameReturn } from "@/core/games/types/game-return.ts";
import type { DataRecorderReturn } from "./useDataRecorder.ts";

export function useCellDragHandlers(
  game: ShallowRef<GridGameReturn>,
  recorder: DataRecorderReturn,
) {
  const drag_target_value = ref<number | null>(null);

  function on_cell_click(row: number, col: number, button: number) {
    const result = game.value.handle_cell_click?.(row, col, button);
    if (result) {
      drag_target_value.value = result.new_value;
      recorder.record_click({ row, col }, result.old_value, result.new_value);
      recorder.save_board_state(game.value.board.value);
    }
  }

  function on_cell_drag(row: number, col: number) {
    if (drag_target_value.value === null) return;
    const result = game.value.set_cell_value(row, col, drag_target_value.value);
    if (result) {
      recorder.record_click({ row, col }, result.old_value, result.new_value);
      recorder.save_board_state(game.value.board.value);
    }
  }

  return { drag_target_value, on_cell_click, on_cell_drag };
}
