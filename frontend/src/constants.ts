/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
import { create_admin_tool, create_dev_tool, create_game_entry } from "@/utils.ts";

export const ACTIVE_GAMES: Record<string, ReturnType<typeof create_game_entry>> = {
  kakurasu: create_game_entry("⬛", "kakurasu"),
  lightup: create_game_entry("💡", "lightup"),
  minesweeper: create_game_entry("💣", "minesweeper"),
  mosaic: create_game_entry("🧩", "mosaic"),
  nonograms: create_game_entry("🏁", "nonograms"),
  sudoku: create_game_entry("🔢", "sudoku"),
  tents: create_game_entry("⛺", "tents"),
  // hashi: create_game_entry("🌉", "hashi"),
  // norinori: create_game_entry("🀄", "norinori"),
  // aquarium: create_game_entry("🐠", "aquarium"),
};
export type PUZZLE_TYPES = keyof typeof ACTIVE_GAMES;

export const DEV_TOOLS: Record<string, ReturnType<typeof create_dev_tool>> = {
  "test-board": create_dev_tool("test-board", "🎯", "Test Board"),
};

export const ACTIVE_EXPERIMENTS: Record<string, any> = {
  "forced-choice": { key: "forced-choice", title: "Preview & Play", icon: "👀" },
  "metacognition": { key: "metacognition", title: "Confidence Check", icon: "🤔", },
  "blind-sudoku": { key: "blind-sudoku", title: "Spotlight Sudoku", icon: "🔍" },
}

export const ADMIN_TOOLS: Record<string, ReturnType<typeof create_admin_tool>> = {
  // "data-download": create_admin_tool("data-download", "🧮", "Data Download"),
  "analysis": create_admin_tool("analysis", "🔬", "Analysis"),
  // "puzzle-browser": create_admin_tool("puzzle-browser", "🔍", "Puzzle Browser"),
  "feedback-viewer": create_admin_tool("feedback-viewer", "💬", "Feedback"),
  // "analytics-dashboard": create_admin_tool("analytics-dashboard", "📊", "Analytics Dashboard"),
};

