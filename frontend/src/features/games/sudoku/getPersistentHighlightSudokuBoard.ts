import { defineComponent, h } from 'vue';
import type { PropType } from 'vue';
import PuzzleSudoku from '@/features/games/sudoku/sudoku.puzzle.vue'; // Assuming this is the main board component
import {
  type PersistentHighlightOptions,
  withSudokuPersistentHighlighter
} from "./useSudokuPersistentHighlight";
import { createPuzzleInteractionBridge } from '@/features/games.composables/setupPuzzleInteractionBridge';
import { createStaticPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
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
      const session = await createStaticPuzzleSession(props.state, "sudoku")
      const bridge = createPuzzleInteractionBridge(session);
      withSudokuPersistentHighlighter(session, bridge, highlightOptions);

      return () => h(PuzzleSudoku, {
        state: session.state,
        interact: bridge,
        scale: props.scale,
        ...attrs
      }, slots);
    }
  });
}
