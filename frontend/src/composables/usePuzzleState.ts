import { inject, ref } from "vue";
import type { usePuzzleSocket } from "@/features/games.composables/usePuzzleSocket.ts";
import { PuzzleTimer } from "@/utils.ts";
import { getPuzzleVariants } from "@/services/app.ts";

const variantCache = new Map<string, string[]>();

export async function usePuzzleState(puzzle_type: string) {
  const socket = inject<ReturnType<typeof usePuzzleSocket>>("puzzle_socket");
  if (!socket) throw new Error("Puzzle socket not found");
  const session = socket.getPuzzleSession(puzzle_type);

  // Puzzle Variants
  let variants: string[];
  if (variantCache.has(puzzle_type)) {
    variants = variantCache.get(puzzle_type)!;
  } else {
    const res = await getPuzzleVariants(puzzle_type);
    variants = res.data || [];
    variantCache.set(puzzle_type, variants);
  }

  // Puzzle Variants
  const available_variants = ref<string[]>(variants);
  const selected_variant = ref<string>(available_variants.value[0]);
  const timer = new PuzzleTimer(puzzle_type);

  return {
    puzzle_type,
    selected_variant,
    available_variants,
    timer,
    is_ready: session.is_ready,
    state: session.state,
    session_id: session.session_id,

    request_new_puzzle: () => {
      timer.reset();
      session.cmd_puzzle_create(selected_variant.value);
      timer.start();
    },
    session,
  };
}
