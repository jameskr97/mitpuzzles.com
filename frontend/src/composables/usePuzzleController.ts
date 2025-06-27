import { computed, ref, shallowRef, watch } from "vue";
import type * as gtypes from "@/codegen/websocket/game.schema";
import type { EventState, SupportedPuzzleTypes } from "@/codegen/websocket/game.schema";
import { useGameService } from "@/services/game/useGameService.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { PuzzleTimer } from "@/utils.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle.ts";
import type { MutablePuzzleState } from "@/services/states.ts";

const cache = new Map<string, ReturnType<typeof makeRemoteController>>();

type ControllerOpts = {
  mode?: "remote" | "local";
  /** optional starting snapshot for local sessions */
  initialState?: EventState;
  autoResume?: boolean;
};

export function usePuzzleController(puzzle: SupportedPuzzleTypes, opts: ControllerOpts = {}) {
  const mode = opts.mode ?? "remote";
  const key = `${puzzle}::${mode}`;
  // if (!cache.has(key)) {
  //   cache.set(key, makeRemoteController(puzzle, false));
  // }

  if (!cache.has(key)) {
    if (mode === "local") {
      cache.set(key, makeLocalController(puzzle, opts.initialState));
    } else {
      cache.set(key, makeRemoteController(puzzle, opts.autoResume ?? true));
    }
  }
  return cache.get(key)!;
}

function makeRemoteController(puzzle_type: gtypes.SupportedPuzzleTypes, autoResume: boolean = true) {
  const game = useGameService();
  const puzzle_metadata = usePuzzleMetadataStore();
  const state = shallowRef<EventState | null>(null);
  const is_solved = ref(false);
  const show_solved_state = ref(false);

  // NOTE(james): this will get called on every "state" event, but since we
  // cache this controller, we don't want to remove it when the page is changed.
  // instead, just ignore events that are not for this puzzle type.
  const on_connect = () => {
    game.load(puzzle_type);
  };
  if (autoResume) {
    game.bus.on("connected", on_connect);
    if (game.connected.value) on_connect();
  }

  game.bus.on("state", (s: gtypes.EventState) => {
    // Ignore updates for *other* puzzle types entirely
    if (s.puzzle_type !== puzzle_type) return;

    // sync tutorial flag
    tutorial_mode_server.value = s.tutorial_mode as boolean;

    // solved flag coming from server
    if (s.solved) {
      is_solved.value = true;
      show_solved_state.value = true;
      timer.stop();
    }

    // finally update reactive snapshot
    state.value = s;
  });
  game.bus.on("submit_result", (result: boolean) => {
    if (!state.value) return;

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
    if (!state.value.attempt_id) {
      console.warn("Cannot handle cell click, attempt_id is not set.");
      return;
    }

    const index = cell.row * (state.value.cols ?? 0) + cell.col;
    if (state.value.immutable[index] === 1) return;

    game.action({
      kind: "action",
      attempt_id: state.value.attempt_id,
      puzzle_type,
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
    game.refresh(state.value.attempt_id, puzzle_type as string, size, difficulty);
    timer.reset();
    timer.start();
  }

  function request_puzzle_clear() {
    if (!state.value || !state.value.attempt_id) return;
    game.clear(state.value.attempt_id, puzzle_type as string);
  }

  function request_puzzle_solved() {
    if (!state.value || !state.value.attempt_id) return;
    game.submit(state.value.attempt_id, puzzle_type as string, timer.elapsed_ms.value);
  }

  const timer = new PuzzleTimer(puzzle_type);
  const tutorial_mode_ui = ref(false);
  const tutorial_mode_server = ref(false);
  watch(tutorial_mode_server, (enabled) => {
    if (!state.value || !state.value.attempt_id) return;
    game.setTutorialEnabled(state.value.attempt_id, puzzle_type, enabled);
  });

  return {
    puzzleType: puzzle_type,
    bus: game.bus,
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
    tutorial_mode: tutorial_mode_server,
  };
}

function makeLocalController(puzzle_type: SupportedPuzzleTypes, initial: MutablePuzzleState | undefined) {
  /* We keep state in-memory only */
  const state = ref<MutablePuzzleState>(
    <MutablePuzzleState>initial ?? {
      puzzle_type,
      rows: 0,
      cols: 0,
      board: [],
      immutable: [],
      tutorial_mode: false,
      solved: false,
      attempt_id: "LOCAL-" + Math.random().toString(36).slice(2),
    },
  );

  if (puzzle_type === "sudoku") {
    state.value.immutable = state.value.board.map((cell) => (cell !== 0 ? 1 : 0));
  }

  const is_solved = ref(state.value?.solved ?? false);
  const show_solved_state = ref(false);

  /* derived */
  const rows = computed(() => state.value?.rows ?? 0);
  const cols = computed(() => state.value?.cols ?? 0);
  const isReady = computed(() => !!state.value);

  /* mutate board locally */
  function handleCellClick(cell: Cell, button = 0, override?: number) {
    if (!state.value) return;
    const idx = cell.row * (state.value.cols ?? 0) + cell.col;
    if (state.value.immutable[idx] === 1) return;
    state.value.board[idx] = override ?? (state.value.board[idx] + 1) % 10; // demo logic
  }

  function request_puzzle_clear() {
    if (!state.value) return;
    state.value.board = state.value.board.map(() => 0);
  }

  function request_new_puzzle() {
    console.warn("Local controller: request_new_puzzle() is a no-op.");
  }

  function request_puzzle_solved() {
    console.warn("Local controller: submit() is a no-op.");
  }

  const timer = new PuzzleTimer(puzzle_type);

  return {
    mode: "local",
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
    selected_variant: ref(null),
    timer,
    tutorial_mode: ref(false),
  };
}
