/**
 * useGameSession — shared game orchestration logic for freeplay and daily modes.
 *
 * handles game creation, recorder setup, ui state, solution checking,
 * clearing, new-puzzle requests, and controller construction.
 * mode-specific behavior (definition source, solve handler, new-puzzle logic)
 * is injected via the services config.
 */

import type { GridGameReturn } from "@/core/games/types/game-return.ts";
import { computed, type ComputedRef, ref, shallowRef, type ShallowRef, watch } from "vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { type DataRecorderReturn, useDataRecorder } from "@/core/games/composables/useDataRecorder.ts";
import type { GameController, GameUIState } from "@/core/games/types/game-controller.ts";
import type { PuzzleVariant } from "@/core/types";
import type { Ref } from "vue";

export interface GameSessionServices<TMeta = any> {
  definition: Ref<PuzzleDefinition<TMeta> | null> | ComputedRef<PuzzleDefinition<TMeta> | null>;
  saved_board: Ref<number[][] | null> | ComputedRef<number[][] | null>;
  is_solved: ComputedRef<boolean>;
  formatted_time: ComputedRef<string>;
  current_variant: Ref<PuzzleVariant>;
  tutorial_used: Ref<boolean> | ComputedRef<boolean>;
  mark_solved: () => Promise<void>;
  mark_tutorial_used: () => void;
  request_new_puzzle: () => Promise<PuzzleDefinition<TMeta> | null>;
  start_game?: () => Promise<void>;
}

export interface GameSessionConfig<TReturn extends GridGameReturn<TMeta>, TMeta = any> {
  puzzle_type: string;
  services: GameSessionServices<TMeta>;
  create_game: (definition: PuzzleDefinition<TMeta>, saved_board: number[][] | null) => TReturn;
  extra_puzzle_state?: (game: TReturn) => Record<string, any>;
}

export interface GameSessionReturn<TReturn extends GridGameReturn> {
  game: ShallowRef<TReturn>;
  recorder: DataRecorderReturn;
  controller: GameController;
  puzzle_state: ComputedRef<Record<string, any>>;
  canvas_key: ComputedRef<string>;
  on_cell_enter: (row: number, col: number, zone: string) => void;
  on_cell_leave: (row: number, col: number, zone: string) => void;
}

export function useGameSession<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: GameSessionConfig<TReturn, TMeta>
): GameSessionReturn<TReturn> {
  const { puzzle_type, services, create_game, extra_puzzle_state } = config;

  const game = shallowRef<TReturn>(create_game(services.definition.value!, services.saved_board.value));

  const recorder = useDataRecorder({
    mode: "freeplay",
    puzzle_type,
    persist: true,
    broadcast: true,
  });

  const ui = ref<GameUIState>({
    show_solved_state: services.is_solved.value,
    tutorial_mode: false,
    animate_success: false,
    animate_failure: false,
  });

  // watch violations, and change activation state depending on tutorial mode
  const violations = computed(() => (ui.value.tutorial_mode ? game.value.get_violations() : []));
  watch(
    () => ui.value.tutorial_mode,
    (is_on) => {
      if (is_on && violations.value.length > 0) services.mark_tutorial_used();
    },
  );

  function on_cell_enter(row: number, col: number, zone: string) {
    recorder.record_hover_start({ row, col }, zone);
  }

  function on_cell_leave(row: number, col: number, zone: string) {
    recorder.record_hover_end({ row, col }, zone);
  }

  async function check_solution(): Promise<boolean> {
    const is_correct = await game.value.check_solution();

    ui.value.show_solved_state = true;
    ui.value.animate_success = is_correct;
    ui.value.animate_failure = !is_correct;

    if (is_correct) {
      await services.mark_solved();
    } else {
      setTimeout(() => {
        ui.value.show_solved_state = false;
      }, 3000);
    }

    setTimeout(() => {
      ui.value.animate_success = false;
      ui.value.animate_failure = false;
    }, 100);

    recorder.record_attempt_solve(is_correct);
    return is_correct;
  }

  function clear_puzzle() {
    const old_board = JSON.parse(JSON.stringify(game.value.board.value));
    game.value.clear();
    const new_board = JSON.parse(JSON.stringify(game.value.board.value));
    recorder.record_clear(old_board, new_board);
    recorder.save_board_state(new_board);
    ui.value.show_solved_state = false;
  }

  async function request_new_puzzle() {
    const new_def = await services.request_new_puzzle();
    if (new_def) {
      game.value = create_game(new_def, services.saved_board.value);
      ui.value.show_solved_state = services.is_solved.value;
      ui.value.tutorial_mode = false;
    }
  }

  const controller: GameController = {
    puzzle_type,
    state: computed(() => ({
      solved: services.is_solved.value,
      definition: {
        id: game.value.definition.id,
        puzzle_type: game.value.definition.puzzle_type,
        rows: game.value.definition.rows,
        cols: game.value.definition.cols,
      },
    })),
    ui,
    current_variant: services.current_variant,
    tutorial_used: services.tutorial_used,
    formatted_time: services.formatted_time,
    check_solution,
    clear_puzzle,
    request_new_puzzle,
    start_game: services.start_game,
  };

  const puzzle_state = computed(() => {
    const base: Record<string, any> = {
      definition: game.value.definition,
      board: game.value.board.value,
      solved: services.is_solved.value,
      violations: violations.value,
    };

    if (game.value.immutable_cells) {
      base.immutable_cells = game.value.immutable_cells.value;
    }

    if (extra_puzzle_state) {
      Object.assign(base, extra_puzzle_state(game.value));
    }

    return base;
  });

  const canvas_key = computed(
    () => `${game.value.definition.id}-${game.value.definition.rows}-${game.value.definition.cols}`,
  );

  return {
    game,
    recorder,
    controller,
    puzzle_state,
    canvas_key,
    on_cell_enter,
    on_cell_leave,
  } as GameSessionReturn<TReturn>;
}
