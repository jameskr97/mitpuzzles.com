/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
import { create_dev_tool, create_game_entry } from "@/utils.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { useSudokuViolationHighlighter } from "@/features/games/sudoku/useSudokuViolationHighlighter.ts";

export const ACTIVE_GAMES: Record<string, ReturnType<typeof create_game_entry>> = {
  minesweeper: create_game_entry("💣", "Minesweeper", "minesweeper"),
  sudoku: create_game_entry("🔢", "Sudoku", "sudoku", [withSudokuBehaviors, useSudokuViolationHighlighter]),
  tents: create_game_entry("⛺", "Tents", "tents"),
  kakurasu: create_game_entry("⬛", "Kakurasu", "kakurasu"),
  lightup: create_game_entry("💡", "Light Up", "lightup"),
  nonograms: create_game_entry("🏁", "Nonograms", "nonograms"),
  battleships: create_game_entry("🚢", "Battleships", "battleships"),
};
export type PUZZLE_TYPES = keyof typeof ACTIVE_GAMES;

export const DEV_TOOLS: Record<string, ReturnType<typeof create_dev_tool>> = {
  "test-board": create_dev_tool("test-board", "🎯", "Test Board"),
  "puzzle-definition": create_dev_tool("puzzle-definition", "📐", "Puzzle Definition"),
};

export const ACTIVE_EXPERIMENTS: Record<string, any> = {
  "forced-choice": { key: "forced-choice", title: "Preview & Play", icon: "👀", description: "Compete to solve this expeirment in the fastest time!" },
  "metacognition": { key: "metacognition", title: "Confidence Check", icon: "🤔", description: "A game that tests your awareness of your own knowledge." },
  "blind-sudoku": { key: "blind-sudoku", title: "Spotlight Sudoku", icon: "🔍", description: "A variant of Sudoku where some numbers are hidden."},
}

