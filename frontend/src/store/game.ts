import { defineStore } from "pinia";
import { useLocalStorage, StorageSerializers } from "@vueuse/core";
import { b64decode_array as b64d, b64encode_array as b64e, remap } from "@/lib/util";
import { getRandomPuzzle } from "@/api/app";

// TODO(james): Abstract this out
import { MinesweeperCellStates } from "@/components/games/minesweeper/minesweeper.model";
import type { PuzzleMinesweeper } from "@/api/types";

type GameConfig<T> = {
    get_solution: (puzzle: number[]) => string;
    get_puzzle_state: (new_puzzle: T) => any;
    default_state: () => any[];
};

function createGameStore<T>(game: string, game_class: string, config: GameConfig<T>): any {
    const storage_prefix = `mitlogic.${game}.${game_class}`
    return defineStore(storage_prefix, {
        state: () => ({
            scale: useLocalStorage(`${storage_prefix}.scale`, 30, { serializer: StorageSerializers.number }),
            puzzle: useLocalStorage(`${storage_prefix}.puzzle`, null, {
                // A custom serializer is used to encode the gameboard + game state into base64.
                serializer: {
                    read: (raw) => {
                        if (!raw) return null;
                        const parsed = JSON.parse(raw);
                        return {
                            received_at: parsed.received_at,
                            completed_at: parsed.completed_at,
                            rows: parsed.rows,
                            cols: parsed.cols,
                            board: b64d(parsed.board),
                            gamestate: b64d(parsed.gamestate),
                            solution_hash: parsed.solution_hash,
                        }
                    },
                    write: (value) => {
                        if (!value) return "null";
                        return JSON.stringify({
                            received_at: value.received_at,
                            completed_at: value.completed_at,
                            rows: value.rows,
                            cols: value.cols,
                            board: b64e(value.board),
                            gamestate: b64e(value.gamestate),
                            solution_hash: value.solution_hash,
                        })
                    }
                }
            }),
            history: useLocalStorage(`${storage_prefix}.history`, null, { serializer: StorageSerializers.object }),
        }),
        getters: {
            /**
             * This remapped scale is tied to the scale setting, and remaps to a range.
             * Review the `remap` function documentation for more information.
             *
             * Note: The [0, 100] paremeter should be inline with the range of the getScale   .
             *
             * @param max
             * @returns
             */
            scale_remapped: (state) => {
                return (max: number = 5) => remap([0, 100], [2, max], state.scale)
            },

            /**
             * @returns True if we have a saved puzzle, false otherwise.
             */
            has_puzzle_saved: (state) => !!state.puzzle,

            is_puzzle_solved: (state) => {
                if (!state.puzzle) return false;
                return state.puzzle.solution_hash === b64e(state.puzzle.gamestate);
            },

            validation: (state) => {
                if (!state.puzzle) return null;
                return config.get_solution(state.puzzle.gamestate)
            },
        },
        actions: {
            async fetchPuzzle(shouldForce:boolean = false) {
                if (this.has_puzzle_saved && !shouldForce) return;
                const puzzle = await getRandomPuzzle(); // TODO(james): Update this to use the game 
                const timestamp = Date.now(); // Save the time we fetched the puzzle
                const pstate = config.get_puzzle_state(puzzle as T);

                // Prepare the puzzle history with initial fetch event
                this.history = { events: [{ timestamp, event_type: 'fetch_puzzle' }] };

                // TODO(james): we should probably validate puzzle.board for correct format (regex?)
                this.puzzle = {
                    ...pstate,
                    received_at: timestamp,
                    completed_at: null,
                    gamestate: config.default_state(),
                }
            },

            /**
             * Clear the game state.
             */
            clear_state() {
                if (!this.puzzle) return;
                if (b64e(this.puzzle.gamestate) === b64e(config.default_state())) return; // No need to clear if we're already clear
                this.puzzle.gamestate = config.default_state()
                this.record_event('clear_state');
            },

            /** Add an a event to the history list */
            record_event(event_type: string, payload: any = null) {
                if (!this.history) this.history = { events: [] };
                this.history.events.push({ timestamp: Date.now(), event_type, payload });
            },

            submit_game() {
                this.record_event('submit_game');
            },

            mark_solved() {
                if (!this.puzzle) return;
                this.puzzle.completed_at = Date.now();
            },
        }
    });
}

export function useMinesweeperStore(rows: number, cols: number) {
    return createGameStore<PuzzleMinesweeper>('minesweeper', '5x5', {
        default_state: () => new Array(rows * cols).fill(MinesweeperCellStates.Unmarked),
        get_puzzle_state: (puzzle: PuzzleMinesweeper) => {
            const MINESWEEPER_MAP: Record<string, number> = {
                "U": 10,
                "F": 11,
                "S": 12,
            }
            return {
                rows: puzzle.rows,
                cols: puzzle.cols,
                solution_hash: puzzle.solution_hash,
                board: puzzle.board.split('').map(c => {
                    const num = parseInt(c)
                    return isNaN(num) ? MINESWEEPER_MAP[c] : num
                }),
            }
        },
        get_solution: (puzzle: number[]) => puzzle.map(c => {
            if (c === MinesweeperCellStates.Unmarked) return 0;
            if (c === MinesweeperCellStates.Flagged) return 1;
            if (c === MinesweeperCellStates.Safe) return 2;
            return c;
        }).join(''),
    })();
}

export function useSudokuStore() {
    return createGameStore<PuzzleMinesweeper>('minesweeper', '5x5', {
        default_state: () => new Array(9 * 9).fill(0),
        get_puzzle_state: (puzzle: PuzzleMinesweeper) => {
            const MINESWEEPER_MAP: Record<string, number> = {
                "U": 10,
                "F": 11,
                "S": 12,
            }
            console.log(puzzle)
            return {
                rows: puzzle.rows,
                cols: puzzle.cols,
                solution_hash: puzzle.solution_hash,
                board: puzzle.board.split('').map(c => {
                    const num = parseInt(c)
                    return isNaN(num) ? MINESWEEPER_MAP[c] : num
                }),
            }
        },
        get_solution: (puzzle: number[]) => puzzle.map(c => {
            if (c === MinesweeperCellStates.Unmarked) return 0;
            if (c === MinesweeperCellStates.Flagged) return 1;
            if (c === MinesweeperCellStates.Safe) return 2;
            return c;
        }).join(''),
    })();
}

// export const useMinesweeperStore = createGameStore('minesweeper', '5x5');
// export const useSudokuStore = createGameStore('sudoku', '3x3easy')