

/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
import { create_dev_tool, create_experiment, create_game_entry } from "@/utils.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import {
  define_2020_06_SudokuExperimentFlow
} from "@/features/prolific.experiments/2025.05.29.sudoku/experiment.flow.ts";


export const ACTIVE_GAMES: Record<string, ReturnType<typeof create_game_entry>> = {
  minesweeper: create_game_entry("💣", "Minesweeper", "minesweeper"),
  sudoku: create_game_entry("🧩", "Sudoku", "sudoku", 4, [withSudokuBehaviors]),
  tents: create_game_entry("⛺", "Tents", "tents"),
  kakurasu: create_game_entry("⬛", "Kakurasu", "kakurasu"),
  lightup: create_game_entry("💡", "Light Up", "lightup")
};
export type GameKey = keyof typeof ACTIVE_GAMES;


export const DEV_TOOLS: Record<string, ReturnType<typeof create_dev_tool>> = {
  "test-board": create_dev_tool("test-board", "🎯", "Test Board"),
  // "test-websocket": create_dev_tool("test-websocket", "🧦", "Test Websockets"),
  // "test-monitor": create_dev_tool("test-monitor", "🖥️", "Test Monitor", true),
  "test-experiment": create_dev_tool("test-experiment", "📝", "Text Experiment", {experiment_key: "2025.05.29.sudoku"}),
};

export const ACTIVE_EXPERIMENTS: Record<string, ReturnType<typeof create_experiment>> = {
  "2025.05.29.sudoku": create_experiment("2025.05.29.sudoku", define_2020_06_SudokuExperimentFlow())
}
