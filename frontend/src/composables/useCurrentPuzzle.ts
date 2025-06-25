import { useRoute } from "vue-router";
import { ModuleManager, on } from "@/services/eventbus.ts";
import { computed, inject, ref, watch, type Ref } from "vue";
import type { GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { PuzzleTimer } from "@/utils.ts";
import { getPuzzleVariants } from "@/services/app.ts";
import { useLocalStorage } from "@vueuse/core";
import type { MutablePuzzleState } from "@/services/states.ts";
import type { WebSocketMessage } from "@/services/eventbus.modules/websocket.ts";

const puzzle_sessions = new Map<string, ReturnType<typeof createPuzzleSession>>();
const variantCache = new Map<string, string[][]>();

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    puzzle_sessions.clear();
    variantCache.clear();
  });
}

/**
 * Returns the reactive puzzle module for *whatever* game the current
 * route points to. Call it once in a view component or another composable.
 */
export async function useCurrentPuzzle(): Promise<ReturnType<typeof createPuzzleSession>> {
  const type = useRoute().meta.game_type as string;
  if (!puzzle_sessions.has(type)) {
    const event_modules = inject<ModuleManager>("event_modules");
    const game_module = event_modules?.getComposable?.<GameModuleInterface>("game");
    if (!game_module) throw new Error("Game module not found");
    const session = await createPuzzleSession(game_module, type);
    puzzle_sessions.set(type, session);
  }
  return puzzle_sessions.get(type)!;
}

export function getPuzzleSession(puzzleType: string): Awaited<ReturnType<typeof createPuzzleSession>> | undefined {
  return puzzle_sessions.get(puzzleType);
}

export async function createPuzzleSession(gameModule: GameModuleInterface, puzzleType: string) {
  // Try to resume existing session on creation
  gameModule.resumePuzzle(puzzleType);

  // Get puzzle variants
  let variants: string[][];
  if (variantCache.has(puzzleType)) {
    variants = variantCache.get(puzzleType)!;
  } else {
    const res = await getPuzzleVariants(puzzleType);
    variants = res.data || [];
    variantCache.set(puzzleType, variants);
  }

  // Puzzle variants management
  const available_variants = ref<string[][]>(variants);
  const selectedVariantRef = ref<string[]>([]);
  const selected_variant = computed({
    get() {
      // If user has explicitly selected a variant, use that
      if (selectedVariantRef.value.length) return selectedVariantRef.value;

      // Try using session state values if available and defined
      const sessionId = gameModule.getSessionID(puzzleType);
      const state = sessionId ? gameModule.getPuzzleState(sessionId) : null;
      const size = state?.puzzle_size;
      const difficulty = state?.puzzle_difficulty;
      if (size && difficulty) return [size, difficulty];

      // Fall back to first available variant, if any
      if (available_variants.value.length > 0) return available_variants.value[0];
      return ["", ""];
    },
    set(value: string[]) {
      selectedVariantRef.value = value;
      // Note: We can't directly modify state here since we don't have direct access
      // This would need to be handled through game module events if needed
    },
  });

  const timer = new PuzzleTimer(puzzleType);
  const tutorial_mode = useLocalStorage<boolean>(`mitlogic.puzzles:tutorial_mode:${puzzleType}`, false);

  // Watch tutorial mode changes and emit events to game module
  watch(tutorial_mode, (newValue) => {
    gameModule.toggle_tutorial(newValue);
  });

  on("game:submit_result", (result: WebSocketMessage<boolean>) => {
    if (result.data) timer.complete();
  })

  return {
    interact: gameModule,
    puzzle_type: puzzleType,

    // Reactive state
    state: computed(() => {
      const sessionId = gameModule.getSessionID(puzzleType);
      return sessionId ? gameModule.getPuzzleState(sessionId) : null;
    }),

    // Session info
    session_id: computed(() => gameModule.getSessionID(puzzleType)),

    // Ready state
    is_ready: computed(() => {
      const sessionId = gameModule.getSessionID(puzzleType);
      const state = sessionId ? gameModule.getPuzzleState(sessionId) : null;
      return !!(sessionId && state);
    }),

    // Board properties (for compatibility)
    rows: computed(() => {
      const sessionId = gameModule.getSessionID(puzzleType);
      const state = sessionId ? gameModule.getPuzzleState(sessionId) : null;
      return state?.rows ?? 0;
    }),
    cols: computed(() => {
      const sessionId = gameModule.getSessionID(puzzleType);
      const state = sessionId ? gameModule.getPuzzleState(sessionId) : null;
      return state?.cols ?? 0;
    }),

    // Puzzle variants
    available_variants,
    selected_variant,

    // Tutorial and solved state
    tutorial_mode,
    is_solved: computed(() => {
      return gameModule.get_solved_state();
    }),

    // Timer
    timer,

    // Commands
    cmd_puzzle_reset: () => {
      gameModule.clear_puzzle_state();
    },

    cmd_puzzle_submit: () => {
      gameModule.request_submit();
    },

    request_new_puzzle: () => {
      timer.reset();
      const [puzzle_size, puzzle_difficulty] = selected_variant.value;
      gameModule.request_new_puzzle(puzzle_size, puzzle_difficulty);
      timer.start();
    },

    cmd_toggle_tutorial: (enabled: boolean) => {
      tutorial_mode.value = enabled;
    },

    // Cell interaction (delegated to game module)
    handle_cell_click: (cell: any, button: number = 0, stateOverride?: number) => {
      gameModule.handle_cell_click(cell, button, stateOverride);
    },
  };
}

export async function createStaticPuzzleSession(state: Ref<MutablePuzzleState>, puzzleType: string) {
  // Create a dummy session for testing purpose

  return {
    interact: {
      handle_cell_click: (cell: any, _button: number = 0, stateOverride?: number) => {
        if(stateOverride) {
          state.value.board[cell.row * state.value.cols + cell.col] = stateOverride;
        }
      },
    },

    puzzle_type: puzzleType,

    // Reactive state
    state,

    // Session info
    session_id: computed(() => "fake-session-id"),

    // Ready state
    is_ready: computed(() => true),

    // Board properties (for compatibility)
    rows: computed(() => state.value.rows),
    cols: computed(() => state.value.cols),
    available_variants: [],
    selected_variant: [],

    // Tutorial and solved state
    tutorial_mode: ref(false),
    is_solved: computed(() => false),

    // Timer
    timer: null,

    // Commands
    cmd_puzzle_reset: () => {},
    cmd_puzzle_submit: () => {},
    request_new_puzzle: () => {},
    cmd_toggle_tutorial: (_enabled: boolean) => {},
    handle_cell_click: (_cell: any, _button: number = 0, _stateOverride?: number) => {},
  };
}
