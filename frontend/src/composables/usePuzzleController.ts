import { computed, ref, shallowRef, watch } from "vue";
import type * as gtypes from "@/codegen/websocket/game.schema";
import type { EventState, PayloadPuzzleType } from "@/codegen/websocket/game.schema";
import { useGameService } from "@/services/game/useGameService.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { PuzzleTimer } from "@/utils.ts";
import { useLocalStorage } from "@vueuse/core";
import { usePuzzleMetadataStore } from "@/store/puzzle.ts";

const cache = new Map<PayloadPuzzleType, ReturnType<typeof makeController>>();

export function usePuzzleController(puzzle: PayloadPuzzleType): ReturnType<typeof makeController> {
  if (!cache.has(puzzle)) {
    cache.set(puzzle, makeController(puzzle));
  }
  return cache.get(puzzle)!;
}

function makeController(puzzle_type: gtypes.PayloadPuzzleType) {
  const game = useGameService();
  const puzzle_metadata = usePuzzleMetadataStore();
  const state = shallowRef<EventState | null>(null);
  const currentAttemptID = useLocalStorage<string | null>(`mitlogic:puzzle:${puzzle_type}:current_attempt`, null);
  const is_solved = ref(false);
  const show_solved_state = ref(false);

  // NOTE(james): this will get called on every "state" event, but since we
  // cache this controller, we don't want to remove it when the page is changed.
  // instead, just ignore events that are not for this puzzle type.
  const on_connect = () => {
    if (currentAttemptID.value) {
      game.resume(currentAttemptID.value);
    } else {
      game.load(puzzle_type);
    }
  }
  game.bus.on("connected", on_connect);
  if (game.connected.value) on_connect();

  game.bus.on("state", (s: gtypes.EventState) => {
    if (currentAttemptID.value) {
      if (s.session_id !== currentAttemptID.value) return; // wrong session, ignore
    } else {
      if (s.puzzle_type !== puzzle_type) return;
      currentAttemptID.value = s.session_id;
    }
    tutorial_mode_server.value = s.tutorial_mode as boolean;
    if(s.solved) {
      is_solved.value = true;
      show_solved_state.value = true;
    }
    state.value = s;
  });
  game.bus.on("submit_result", (result: boolean) => {
    if (!state.value || state.value.session_id !== currentAttemptID.value) return;
    is_solved.value = result;
    show_solved_state.value = true;
    if (result) {
      timer.stop();
    }
  });

  // derived helpers ----------------------------------
  const rows = computed(() => state.value?.rows ?? 0);
  const cols = computed(() => state.value?.cols ?? 0);
  const isReady = computed(() => !!state.value);

  // imperative helpers -------------------------------
  function handleCellClick(cell: Cell, button = 0, override?: number) {
    if (!state.value) {
      console.warn("Cannot handle cell click, state is not initialized.");
      return;
    }
    if (!state.value.session_id) {
      console.warn("Cannot handle cell click, session_id is not set.");
      return;
    }

    const index = cell.row * (state.value.cols ?? 0) + cell.col;
    if (state.value.immutable[index] === 1) return;

    game.action({
      kind: "action",
      session_id: state.value.session_id,
      payload: {
        target: "cell",
        action: "click",
        position: {
          zone: cell.zone,
          row: cell.row,
          col: cell.col,
          state: override ?? undefined,
          button,
        },
      },
    });
  }

  function request_new_puzzle() {
    if (!state.value) {
      console.warn("Cannot request new puzzle, state is not initialized.");
      return;
    }
    show_solved_state.value = false;
    is_solved.value = false;
    const [size, difficulty] = puzzle_metadata.getSelectedVariant(puzzle_type);
    game.refresh(state.value.session_id, size, difficulty);
    timer.reset();
    timer.start();
  }

  function request_puzzle_clear() {
    if (!state.value || !state.value.session_id) return;
    game.clear(state.value.session_id);
  }

  function request_puzzle_solved() {
    if (!state.value || !state.value.session_id) return;
    game.submit(state.value.session_id);
  }

  const timer = new PuzzleTimer(puzzle_type);
  const tutorial_mode_ui = ref(false);
  const tutorial_mode_server = ref(false);
  watch(tutorial_mode_server, (enabled) => {
    if (!state.value || !state.value.session_id) return;
    game.setTutorialEnabled(state.value.session_id, enabled);
  });

  return {
    puzzleType: puzzle_type,
    state,
    rows,
    cols,
    isReady,
    is_solved,
    show_solved_state,
    handleCellClick,
    request_new_puzzle,
    request_puzzle_clear,
    request_puzzle_solved,
    selected_variant: computed(() => puzzle_metadata.selected_variant[puzzle_type]),
    timer,
    tutorial_mode: tutorial_mode_server
  };
}
