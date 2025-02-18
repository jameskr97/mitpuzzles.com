import { api } from "@/lib/axios";

////////////////////////////////////////////////////////////////////////////////
// Types
//// Interfaces for per-game settings
interface PuzzleMinesweeper {
    rows: number;
    cols: number;
    board: string;
}

interface SudokuDifficulty { pre_filled: number; }
export type GameOptions = MinesweeperDifficulty | SudokuDifficulty;


//// Interfaces for the layout of the game settings
interface GameDetail {
    displayname: string;
    options: GameOptions;
}

interface GameInfo {
    displayname: string;
    key: string
    modes: GameDetail[];
}

export interface GameSettings {
    minesweeper: GameInfo;
    sudoku: GameInfo;
}

////////////////////////////////////////////////////////////////////////////////
// Endpoints
async function request(method: string, url: string, data?: any) {
    let options = {
        url,
        method: method,
        data: undefined,
    }
    if (data !== undefined) options.data = data;
    return api.request(options)
        .then((response) => response.data)
        .catch((error) => error.response.data);
}

export async function getAppSettings(): Promise<GameSettings> {
    return await request('get', '/api/config/game-settings');
}

export async function getRandomPuzzle(): Promise<PuzzleMinesweeper> {
    return await request('get', '/api/puzzle/random');
}
