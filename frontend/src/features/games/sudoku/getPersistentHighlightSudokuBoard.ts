import { defineComponent, h } from 'vue';
import type { PropType } from 'vue';
import PuzzleSudoku from '@/features/games/sudoku/sudoku.puzzle.vue'; // Assuming this is the main board component
import {
  type PersistentHighlightOptions,
  withSudokuPersistentHighlighter
} from "./useSudokuPersistentHighlight";
import { createPuzzleInteractionBridge } from '@/features/games.composables/setupPuzzleInteractionBridge';
import type { PuzzleStateSudoku } from "@/services/states.ts";

/**
 * Creates a Sudoku board component with persistent highlighting
 */
export function getPersistentHighlightSudokuBoard(highlightOptions?: PersistentHighlightOptions) {
  return defineComponent({
    name: 'PersistentHighlightSudokuBoard',
    props: {
      state: {
        type: Object as PropType<PuzzleStateSudoku>,
        required: true
      },
      scale: {
        type: Number,
        default: 1
      },
    },
    async setup(props, { attrs, slots }) {
      const bridge = createPuzzleInteractionBridge("sudoku", {
        mode: "local",
        state: props.state
      });
      withSudokuPersistentHighlighter(props.state, bridge, highlightOptions);

      return () => h(PuzzleSudoku, {
        state: props.state,
        interact: bridge,
        scale: props.scale,
        ...attrs
      }, slots);
    }
  });
}
