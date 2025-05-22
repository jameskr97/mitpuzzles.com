import { inject, ref, computed } from "vue";
import type { usePuzzleSocket } from "@/features/games.composables/usePuzzleSocket.ts";
import { PuzzleTimer } from "@/utils.ts";
import { getPuzzleVariants } from "@/services/app.ts";

const variantCache = new Map<string, string[][]>();

export async function usePuzzleState(puzzle_type: string) {
  const socket = inject<ReturnType<typeof usePuzzleSocket>>("puzzle_socket");
  if (!socket) throw new Error("Puzzle socket not found");
  const session = socket.getPuzzleSession(puzzle_type);

  // Puzzle Variants
  let variants: string[][];
  if (variantCache.has(puzzle_type)) {
    variants = variantCache.get(puzzle_type)!;
  } else {
    const res = await getPuzzleVariants(puzzle_type);
    variants = res.data || [];
    variantCache.set(puzzle_type, variants);
  }

  // check if we have a variant in the puzzle session
  const available_variants = ref<string[][]>(variants);
  // const selected_variant = ref<string[]>([session.state.value.puzzle_size, session.state.value.puzzle_difficulty]);
  const selectedVariantRef = ref<string[]>([]);

  const selected_variant = computed({
    get() {
      if (!session.state.value) return ["undefined", "undefined"];
      const size = session.state.value.puzzle_size || "undefined";
      const difficulty = session.state.value.puzzle_difficulty || "undefined";
      return selectedVariantRef.value.length ? selectedVariantRef.value : [size, difficulty];
    },
    set(value: string[]) {
      selectedVariantRef.value = value;
      session.state.value.puzzle_size = value[0];
      session.state.value.puzzle_difficulty = value[1];
    },
  });

  const timer = new PuzzleTimer(puzzle_type);

  return {
    puzzle_type,
    selected_variant,
    available_variants,
    timer,
    is_ready: session.is_ready,
    is_solved: session.is_solved,
    state: session.state,
    session_id: session.session_id,

    request_new_puzzle: () => {
      timer.reset();
      const [puzzle_size, puzzle_difficulty] = selected_variant.value;
      session.cmd_puzzle_create(puzzle_size, puzzle_difficulty);
      timer.start();
    },
    session,
  };
}
