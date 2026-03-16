import type { GridGameReturn } from "@/core/games/types/game-return.ts";
import { computed, type ComputedRef, ref, shallowRef, type ShallowRef, watch } from "vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { useDailyServices, type DailyServicesReturn } from "../useDailyServices.ts";
import { type DataRecorderReturn, useDataRecorder } from "@/core/games/composables";
import type { GameController, GameUIState } from "@/core/games/types/game-controller.ts";

export interface DailyGameReturn<TReturn extends GridGameReturn> {
  game: ShallowRef<TReturn>;
  recorder: DataRecorderReturn;
  controller: GameController;
  puzzle_state: ComputedRef<Record<string, any>>;
  canvas_key: ComputedRef<string>;
  on_cell_enter: (row: number, col: number, zone: string) => void;
  on_cell_leave: (row: number, col: number, zone: string) => void;
  date: string;
  error: string | null;
}

export interface DailyGameConfig<TReturn extends GridGameReturn<TMeta>, TMeta = any> {
  puzzle_type: string;
  create_game: (definition: PuzzleDefinition<TMeta>, saved_board: number[][] | null) => TReturn;
  extra_puzzle_state?: (game: TReturn) => Record<string, any>;
}

export async function useDailyGame<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: DailyGameConfig<TReturn, TMeta>,
): Promise<DailyGameReturn<TReturn>> {
  const { puzzle_type, create_game, extra_puzzle_state } = config;

  const services = await useDailyServices<TMeta>(puzzle_type);
  const game = shallowRef<TReturn>(create_game(services.definition.value!, services.saved_board.value));

  const progress_key = `daily:${puzzle_type}`;
  const recorder = useDataRecorder({
    mode: "freeplay",
    puzzle_type: progress_key,
    persist: true,
    broadcast: false,
  });

  const ui = ref<GameUIState>({
    show_solved_state: services.is_solved.value,
    tutorial_mode: false,
    animate_success: false,
    animate_failure: false,
  });

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
    check_solution,
    clear_puzzle,
    request_new_puzzle: async () => {},
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
    date: services.date,
    error: services.error.value,
  } as DailyGameReturn<TReturn>;
}
