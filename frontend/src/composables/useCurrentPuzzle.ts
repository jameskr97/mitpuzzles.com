import { useRoute } from "vue-router";
import { PuzzleData } from "@/models/PuzzleData.ts";
import { ACTIVE_GAMES } from "@/main.ts";

const puzzle_sessions = new Map<string, PuzzleData<any, any>>();

/**
 * Returns the reactive puzzle module for *whatever* game the current
 * route points to. Call it once in a view component or another composable.
 */
export async function useCurrentPuzzle(): Promise<PuzzleData<any, any>> {
  // Determine the current game type from the route metadata
  const route = useRoute();
  const type = route.meta.game_type as string;
  const variant = "default";

  // Data elements to make accessible to the user
  const key = `${type}:${variant}`;
  if (!puzzle_sessions.has(key)) {
    // If the game type is not supported, throw an error
    if (!(type in ACTIVE_GAMES)) {
      throw new Error(`Game type ${type} is not supported.`);
    }

    // If the session for this game type does not exist, create it
    const adapter = ACTIVE_GAMES[type].adapter;
    const data = new PuzzleData(type, variant, adapter);
    await data.init();
    puzzle_sessions.set(key, data);
  }

  const session = puzzle_sessions.get(key);
  if (!session) throw new Error(`Failed to the the puzzle session we just created.`);
  return session;
}

export async function getPuzzle(type: string, variant: string = "default"): Promise<PuzzleData<any, any>> {
  const key = `${type}:${variant}`;
  if (!puzzle_sessions.has(key)) {
    throw new Error("Puzzle session not found.");
  }

  const session = puzzle_sessions.get(key);
  if (!session) throw new Error(`Failed to the the puzzle session we just created.`);
  return session;
}
