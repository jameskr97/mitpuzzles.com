/**
 * useDemoGame — lightweight game controller for demo/test puzzles
 *
 * no api calls, no progress store, no history tracking.
 * "new puzzle" simply resets to the same definition.
 */

import { computed, ref, shallowRef } from "vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import type { GridGameReturn } from "@/core/games/types/game-return.ts";
import type { GameController, GameUIState } from "@/core/games/types/game-controller.ts";
import type { GameSessionReturn } from "@/core/games/composables/useGameSession.ts";
import type { DataRecorderReturn } from "@/core/games/composables/useDataRecorder.ts";

interface DemoGameConfig<TReturn extends GridGameReturn<TMeta>, TMeta = any> {
  puzzle_type: string;
  definition: PuzzleDefinition<TMeta>;
  create_game: (definition: PuzzleDefinition<TMeta>, saved_board: number[][] | null) => TReturn;
  extra_puzzle_state?: (game: TReturn) => Record<string, any>;
}

const noop = () => {};
const noop_async = async () => {};

function create_noop_recorder(): DataRecorderReturn {
  return {
    record_click: noop,
    record_keypress: noop,
    record_focus: noop,
    record_hover_start: noop,
    record_hover_end: noop,
    record_clear: noop,
    record_attempt_solve: noop,
    save_board_state: noop_async,
  };
}

export function useDemoGame<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: DemoGameConfig<TReturn, TMeta>
): GameSessionReturn<TReturn> {
  const { puzzle_type, definition, create_game, extra_puzzle_state } = config;

  const game = shallowRef<TReturn>(create_game(definition, null));
  const recorder = create_noop_recorder();
  const solved = ref(false);

  const ui = ref<GameUIState>({
    show_solved_state: false,
    tutorial_mode: false,
    animate_success: false,
    animate_failure: false,
  });

  async function check_solution(): Promise<boolean> {
    const is_correct = await game.value.check_solution();

    ui.value.show_solved_state = true;
    ui.value.animate_success = is_correct;
    ui.value.animate_failure = !is_correct;
    if (is_correct) solved.value = true;

    if (!is_correct) {
      setTimeout(() => { ui.value.show_solved_state = false; }, 3000);
    }
    setTimeout(() => {
      ui.value.animate_success = false;
      ui.value.animate_failure = false;
    }, 100);

    return is_correct;
  }

  function clear_puzzle() {
    game.value.clear();
    ui.value.show_solved_state = false;
  }

  async function request_new_puzzle() {
    game.value = create_game(definition, null);
    solved.value = false;
    ui.value.show_solved_state = false;
    ui.value.tutorial_mode = false;
  }

  const controller: GameController = {
    puzzle_type,
    is_demo: true,
    state: computed(() => ({
      solved: solved.value,
      definition: {
        id: definition.id,
        puzzle_type: definition.puzzle_type,
        rows: definition.rows,
        cols: definition.cols,
      },
    })),
    ui,
    current_variant: ref({ size: definition.puzzle_size, difficulty: definition.puzzle_difficulty ?? null }),
    tutorial_used: ref(false),
    formatted_time: computed(() => ""),
    check_solution,
    clear_puzzle,
    request_new_puzzle,
  };

  const violations = computed(() =>
    ui.value.tutorial_mode ? game.value.get_violations() : []
  );

  const puzzle_state = computed(() => {
    const base: Record<string, any> = {
      definition,
      board: game.value.board.value,
      solved: solved.value,
      violations: violations.value,
    };
    if (game.value.immutable_cells) base.immutable_cells = game.value.immutable_cells.value;
    if (extra_puzzle_state) Object.assign(base, extra_puzzle_state(game.value));
    return base;
  });

  const canvas_key = computed(() => `${definition.id}-${definition.rows}-${definition.cols}`);

  return {
    game,
    recorder,
    controller,
    puzzle_state,
    canvas_key,
    on_cell_enter: noop,
    on_cell_leave: noop,
  } as GameSessionReturn<TReturn>;
}
