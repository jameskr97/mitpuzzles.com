import { useRoute } from "vue-router";
import { usePuzzleStore, type PuzzleAdapter } from "@/store/game";
import * as adapter from "@/store/adapters";
import { useGameLayoutStore } from "./store/useGameLayout";

const ADAPTERS: Record<string, PuzzleAdapter<any, any>> = {
  minesweeper: adapter.minesweeperAdapter,
  sudoku: adapter.sudokuAdapter,
  tents: adapter.tentsAdapter,
};

/**
 * Returns the reactive puzzle module for *whatever* game the current
 * route points to. Call it once in a view component or another composable.
 */
export async function useCurrentPuzzle() {
  const route = useRoute();
  const store = usePuzzleStore();

  const type = route.meta.game_type as string;
  const variant = "default"; // "default" for now, since each game only has one type
  const adapter = ADAPTERS[type];

  if (!adapter) throw new Error(`No puzzle adapter registered for "${type}"`);
  return await store.usePuzzle(type, variant, adapter);
}

export function useGameLayout() {
  const store = useGameLayoutStore();

  const instructions_visible = store.booleanFor("instructions");
  const leaderboard_visible = store.booleanFor("leaderboard");
  console.log(instructions_visible.value, leaderboard_visible.value);

  return {
    instructions_visible,
    leaderboard_visible,
    toggle_instructions: () => (instructions_visible.value = !instructions_visible.value),
    toggle_leaderboard: () => (leaderboard_visible.value = !leaderboard_visible.value),
  };
}
