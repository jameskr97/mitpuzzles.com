import { useRoute } from "vue-router";
import { usePuzzleStore, type PuzzleAdapter } from "@/store/game";
import * as adapter from "@/store/adapters";
import { useGameLayoutStore } from "./store/useGameLayout";
import { ACTIVE_GAMES } from "@/main";
import { computed, reactive, ref, type Ref, type useSlots } from "vue";
import { useElementSize } from "@vueuse/core";

/**
 * Returns the reactive puzzle module for *whatever* game the current
 * route points to. Call it once in a view component or another composable.
 */
export async function useCurrentPuzzle() {
  const route = useRoute();
  const store = usePuzzleStore();

  const type = route.meta.game_type as string;
  const variant = "default"; // "default" for now, since each game only has one type
  return await ACTIVE_GAMES[type].store(variant);
}

export function useGameLayout() {
  const store = useGameLayoutStore();

  const instructions_visible = store.booleanFor("instructions");
  const leaderboard_visible = store.booleanFor("leaderboard");

  return {
    instructions_visible,
    leaderboard_visible,
    toggle_instructions: () => (instructions_visible.value = !instructions_visible.value),
    toggle_leaderboard: () => (leaderboard_visible.value = !leaderboard_visible.value),
  };
}

export function useGridLayout(
  rows: number,
  cols: number,
  slots: ReturnType<typeof useSlots>,
  cellSize: number,
  gap: number,
) {
  const dims = reactive({
    NUM_ROWS: rows + +!!slots.top + +!!slots.bottom,
    NUM_COLS: cols + +!!slots.left + +!!slots.right,
  });

  const rootGridStyle = computed(() => {
    return {
      gridTemplateRows: `repeat(${dims.NUM_ROWS}, 1fr)`,
      gridTemplateColumns: `repeat(${dims.NUM_COLS}, 1fr)`,
    };
  });

  const gameGridStyle = computed(() => {
    return {
      gridTemplateRows: `repeat(${rows}, 1fr)`,
      gridTemplateColumns: `repeat(${cols}, 1fr)`,
    };
  });

  // Define where the start and end rows and columns will be of the game grid
  // These helps adjust the gameGrid inside the root grid
  const gameGridColStart = computed(() => (slots.left ? 2 : 1));
  const gameGridColEnd = computed(() => gameGridColStart.value + cols);
  const gameGridRowStart = computed(() => (slots.top ? 2 : 1));
  const gameGridRowEnd = computed(() => gameGridRowStart.value + rows);

  // These help ensure that the gutter grids are placed correctly
  // reguardless of where they are place within the DOM.
  // T=top, L=left, R=right, B=bottom
  const gutterStartTop = computed(() => ({ gridRowStart: 1 })); // This gutter MUST appear first vertically   (top to bottom)
  const gutterStartLeft = computed(() => ({ gridColumnStart: 1 })); // This gutter MUST appear first horizontally (left to right)
  const gutterStartRight = computed(() => ({ gridColumnStart: gameGridColEnd.value })); // This gutter MUST appear last horizontally  (left to right)
  const gutterStartBottom = computed(() => ({ gridRowStart: gameGridRowEnd.value })); // This gutter MUST appear last vertically    (top to bottom)

  // These help keep the RIGHT+LEFT gutters in the right position vertically (verticalGutterBounds),
  //   and also keep the TOP+BOTTOM gutters in the right position horizontally (horizontalGutterBounds)
  const verticalGutterBounds = computed(() => ({
    gridColumnStart: gameGridColStart.value,
    gridColumnEnd: gameGridColStart.value + cols,
  }));
  const horizontalGutterBounds = computed(() => ({
    gridRowStart: gameGridRowStart.value,
    gridRowEnd: gameGridRowStart.value + rows,
  }));

  const globalGutterStyle = computed(() => ({ gap: `${gap}px` }));
  const styleGutterLeft = computed(() => ({
    ...globalGutterStyle.value,
    ...horizontalGutterBounds.value,
    ...gutterStartLeft.value,
  }));

  const styleGutterRight = computed(() => ({
    ...globalGutterStyle.value,
    ...horizontalGutterBounds.value,
    ...gutterStartRight.value,
  }));

  const styleGutterTop = computed(() => ({
    ...globalGutterStyle.value,
    ...verticalGutterBounds.value,
    ...gutterStartTop.value,
  }));

  const styleGutterBottom = computed(() => ({
    ...globalGutterStyle.value,
    ...verticalGutterBounds.value,
    ...gutterStartBottom.value,
  }));

  const styleGameGrid = computed(() => ({
    ...verticalGutterBounds.value,
    ...horizontalGutterBounds.value,
    gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
    gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
    gap: `${gap}px`,
  }));

  return {
    dims,
    rootGridStyle,
    gameGridStyle,
    styleGutterLeft,
    styleGutterRight,
    styleGutterTop,
    styleGutterBottom,
    styleGameGrid,
  };
}

// all numbers in pixels
export class CellProperties {
  cellSize: number = 15;
  gap: number = 1;
  border: number = 15;
}

export function useLayoutCalculation(rows: number, cols: number, props: CellProperties) {
  const step = computed(() => props.cellSize + props.gap);
  const pxGridStart = computed(() => ({ top: `${props.gap}`, left: `${props.gap}` }));

  const cellStyle = computed(() => (r: number, c: number) => ({
    width: `${props.cellSize}px`,
    height: `${props.cellSize}px`,
    // top: `${props.gap + r * step.value}px`,
    // left: `${props.gap + c * step.value}px`,
  }));

  return {
    step,
    dimensions: {},
    pxGridStart,
    cellStyle,
    border: props.border,
  };
}
