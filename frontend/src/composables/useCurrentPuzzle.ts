import { useRoute } from "vue-router";
import { usePuzzleState } from "@/composables/usePuzzleState.ts";

const puzzle_sessions = new Map<string, ReturnType<typeof usePuzzleState>>();
/**
 * Returns the reactive puzzle module for *whatever* game the current
 * route points to. Call it once in a view component or another composable.
 */
export async function useCurrentPuzzle(): Promise<ReturnType<typeof usePuzzleState>> {
  const type = useRoute().meta.game_type as string;
  if (!puzzle_sessions.has(type)) puzzle_sessions.set(type, usePuzzleState(type));
  return puzzle_sessions.get(type)!;
}
