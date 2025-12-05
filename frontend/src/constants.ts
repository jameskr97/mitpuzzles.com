/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
import { create_admin_tool, create_dev_tool, create_game_entry } from "@/utils.ts";

export const ACTIVE_GAMES: Record<string, ReturnType<typeof create_game_entry>> = {
  aquarium: create_game_entry("🐠", "aquarium"),
  kakurasu: create_game_entry("⬛", "kakurasu"),
  lightup: create_game_entry("💡", "lightup"),
  minesweeper: create_game_entry("💣", "minesweeper"),
  mosaic: create_game_entry("🧩", "mosaic"),
  nonograms: create_game_entry("🏁", "nonograms"),
  sudoku: create_game_entry("🔢", "sudoku"),
  tents: create_game_entry("⛺", "tents"),
  // hashi: create_game_entry("🌉", "hashi"),
  // norinori: create_game_entry("🀄", "norinori"),
};
export type PUZZLE_TYPES = keyof typeof ACTIVE_GAMES;

export const DEV_TOOLS: Record<string, ReturnType<typeof create_dev_tool>> = {};

export const ACTIVE_EXPERIMENTS: Record<string, any> = {
  "forced-choice": { key: "forced-choice", title: "Preview & Play", icon: "👀" },
  "metacognition": { key: "metacognition", title: "Confidence Check", icon: "🤔", },
  "blind-sudoku": { key: "blind-sudoku", title: "Spotlight Sudoku", icon: "🔍" },
}

export const ADMIN_TOOLS: Record<string, ReturnType<typeof create_admin_tool>> = {
  "analysis": create_admin_tool("analysis", "🔬", "Analysis"),
  "feedback-viewer": create_admin_tool("feedback-viewer", "💬", "Feedback"),
  "priority-puzzles": create_admin_tool("priority-puzzles", "⭐", "Priority Puzzles"),
};

