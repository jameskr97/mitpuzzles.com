import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { useGutterMarking } from "@/features/games.composables/useGutterMarking.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

/**
 * nonogram gutter marking behavior
 * handles clicking on gutter cells to toggle between normal and faded states
 * for marking completed sections
 */
export function useNonogramGutterMarking(controller: PuzzleController) {
  // calculate total gutter cells for each direction
  const meta = controller.state_puzzle.value.definition.meta!;
  const longest_row_hints = meta.row_hints.reduce((longest: any, current: any) => current.length > longest.length ? current : longest, []);
  const longest_col_hints = meta.col_hints.reduce((longest: any, current: any) => current.length > longest.length ? current : longest, []);

  // initialize gutter marking functionality - each hint cell can be marked individually
  const gutter_marking = useGutterMarking(
    "nonograms",
    {
      top: longest_col_hints.length * controller.state_puzzle.value.definition.cols, // total hint cells in top gutter
      left: longest_row_hints.length * controller.state_puzzle.value.definition.rows, // total hint cells in left gutter
    }
  );

  // Helper functions to convert between 2D coordinates and flat indices
  const get_top_gutter_index = (row: number, col: number): number =>  row * controller.state_puzzle.value.definition.cols + col;
  const get_left_gutter_index = (row: number, col: number): number => col * controller.state_puzzle.value.definition.rows + row;

  // Input behavior - handles clicks on gutter cells
  const input_behavior: Partial<BoardEvents> = {
    onCellClick(cell: Cell, _event: MouseEvent): boolean {
      // Only handle gutter cells
      if (cell.zone === "topGutter") {
        const index = get_top_gutter_index(cell.row, cell.col);
        gutter_marking.toggle_gutter_marking("top", index);
        return true; // Consume the event
      } else if (cell.zone === "leftGutter") {
        const index = get_left_gutter_index(cell.row, cell.col);
        gutter_marking.toggle_gutter_marking("left", index);
        return true; // Consume the event
      }
      return false; // Let other behaviors handle non-gutter cells
    },
  };

  // Render behavior - provides visual styling for gutters
  const render_behavior: Partial<RenderEvents> = {
    getTopGutterClasses(row: number, col: number): string[] {
      const index = get_top_gutter_index(row, col);
      return gutter_marking.get_gutter_classes("top", index).split(" ").filter(c => c.length > 0);
    },
    getLeftGutterClasses(row: number, col: number): string[] {
      const index = get_left_gutter_index(row, col);
      return gutter_marking.get_gutter_classes("left", index).split(" ").filter(c => c.length > 0);
    },
  };

  return {
    input_behavior,
    render_behavior,
    gutter_marking,
  };
}

/** Convenience function to register nonogram gutter marking behavior */
export function withNonogramGutterMarking(controller: PuzzleController, bridge: any) {
  const gutter_behavior = useNonogramGutterMarking(controller);
  bridge.addInputBehaviour(() => gutter_behavior.input_behavior);
  bridge.addRenderBehaviour(() => gutter_behavior.render_behavior);
  return gutter_behavior;
}
