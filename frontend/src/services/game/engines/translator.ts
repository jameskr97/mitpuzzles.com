///////////////////////////////////////////////////////////////////////////////
// Enums for Developer-Friendly Cell Types
// region Enums for Cell Types
import type { PUZZLE_TYPES } from "@/constants.ts";

export const enum TentsCell {
  EMPTY = 0,
  TREE = 1,
  TENT = 2,
  GREEN = 3,
}

export const enum KakurasuCell {
  EMPTY = 0,
  BLACK = 1,
  CROSS = 2,
}

export const enum SudokuCell {
  EMPTY = 0,
  ONE = 1,
  TWO = 2,
  THREE = 3,
  FOUR = 4,
  FIVE = 5,
  SIX = 6,
  SEVEN = 7,
  EIGHT = 8,
  NINE = 9,
}

export const enum LightupCell {
  WALL_0 = 0,
  WALL_1 = 1,
  WALL_2 = 2,
  WALL_3 = 3,
  WALL_4 = 4,
  WALL_NO_CONSTRAINT = 5,
  EMPTY = 6,
  BULB = 7,
  CROSS = 8,
}

export const enum MinesweeperCell {
  UNMARKED = 0,
  ONE = 1,
  TWO = 2,
  THREE = 3,
  FOUR = 4,
  FIVE = 5,
  SIX = 6,
  SEVEN = 7,
  EIGHT = 8,
  FLAG = 9,
  SAFE = 10,
}

// endregion

///////////////////////////////////////////////////////////////////////////////
// Translation Maps (Research Number to Enum)
// region Translation Maps
const TENTS_TO_ENUM: Record<number, TentsCell> = {
  [-1]: TentsCell.EMPTY,
  [1]: TentsCell.TREE,
  [-3]: TentsCell.TENT,
  [-4]: TentsCell.GREEN,
};

const KAKURASU_TO_ENUM: Record<number, KakurasuCell> = {
  [-1]: KakurasuCell.EMPTY,
  [0]: KakurasuCell.CROSS,
  [1]: KakurasuCell.BLACK,
};

const SUDOKU_TO_ENUM: Record<number, SudokuCell> = {
  [-1]: SudokuCell.EMPTY,
  [1]: SudokuCell.ONE,
  [2]: SudokuCell.TWO,
  [3]: SudokuCell.THREE,
  [4]: SudokuCell.FOUR,
  [5]: SudokuCell.FIVE,
  [6]: SudokuCell.SIX,
  [7]: SudokuCell.SEVEN,
  [8]: SudokuCell.EIGHT,
  [9]: SudokuCell.NINE,
};

const LIGHTUP_TO_ENUM: Record<number, LightupCell> = {
  [0]: LightupCell.WALL_0,
  [1]: LightupCell.WALL_1,
  [2]: LightupCell.WALL_2,
  [3]: LightupCell.WALL_3,
  [4]: LightupCell.WALL_4,
  [-2]: LightupCell.WALL_NO_CONSTRAINT,
  [-1]: LightupCell.EMPTY,
  [-3]: LightupCell.BULB,
  [-4]: LightupCell.EMPTY,
};

const MINESWEEPER_TO_ENUM: Record<number, MinesweeperCell> = {
  [0]: MinesweeperCell.UNMARKED,
  [1]: MinesweeperCell.ONE,
  [2]: MinesweeperCell.TWO,
  [3]: MinesweeperCell.THREE,
  [4]: MinesweeperCell.FOUR,
  [5]: MinesweeperCell.FIVE,
  [6]: MinesweeperCell.SIX,
  [7]: MinesweeperCell.SEVEN,
  [8]: MinesweeperCell.EIGHT,
  [-1]: MinesweeperCell.UNMARKED,
  [-3]: MinesweeperCell.FLAG,
  [-4]: MinesweeperCell.SAFE,
};
// endregion

///////////////////////////////////////////////////////////////////////////////
// Translation Maps (Research Number to Enum)
// region Reverse Maps
const ENUM_TO_TENTS = buildReverseMap(TENTS_TO_ENUM);
const ENUM_TO_KAKURASU = buildReverseMap(KAKURASU_TO_ENUM);
const ENUM_TO_SUDOKU = buildReverseMap(SUDOKU_TO_ENUM);
const ENUM_TO_LIGHTUP = buildReverseMap(LIGHTUP_TO_ENUM);
const ENUM_TO_MINESWEEPER = buildReverseMap(MINESWEEPER_TO_ENUM);

function buildReverseMap<T extends number>(forwardMap: Record<number, T>): Record<T, number> {
  const reverseMap: Record<string, number> = {};

  for (const [numberStr, enumValue] of Object.entries(forwardMap)) {
    const number = parseInt(numberStr);

    // Handle duplicates by preferring certain values
    if (reverseMap[enumValue] === undefined) {
      reverseMap[enumValue] = number;
    } else {
      // For minesweeper, prefer -1 over 0 for UNMARKED
      if (enumValue === MinesweeperCell.UNMARKED && number === -1) {
        reverseMap[enumValue] = number;
      }
      // Add other preference rules here if needed
    }
  }

  return reverseMap as Record<T, number>;
}

// endregion

///////////////////////////////////////////////////////////////////////////////
// Type Definitions
export type CellType = TentsCell | KakurasuCell | SudokuCell | LightupCell | MinesweeperCell;
export type ResearchGrid = number[][];
export type DeveloperGrid<T extends CellType> = T[][];

///////////////////////////////////////////////////////////////////////////////
// Conversion Functions
/**
 * Convert from research format (numbers) to developer format (enums)
 */
export function fromResearchFormat<T extends CellType>(
  grid: ResearchGrid,
  puzzle_type: PUZZLE_TYPES,
): DeveloperGrid<T> {
  const translationMap = getToEnumMap(puzzle_type);
  return grid.map((row) =>
    row.map((cell) => {
      const enumValue = translationMap[cell];
      if (enumValue === undefined) {
        throw new Error(`Unknown cell value ${cell} for puzzle type ${puzzle_type}`);
      }
      return enumValue as T;
    }),
  );
}

/**
 * Convert from developer format (enums) to research format (numbers)
 */
export function toResearchFormat<T extends CellType>(grid: DeveloperGrid<T>, puzzle_type: PUZZLE_TYPES): ResearchGrid {
  const translationMap = getFromEnumMap(puzzle_type);

  return grid.map((row) =>
    row.map((cell) => {
      const numberValue = translationMap[cell as string];
      if (numberValue === undefined) {
        throw new Error(`Unknown cell enum ${cell} for puzzle type ${puzzle_type}`);
      }
      return numberValue;
    }),
  );
}

///////////////////////////////////////////////////////////////////////////////
// Conversion Functions

function getToEnumMap(puzzle_type: PUZZLE_TYPES): Record<number, CellType> {
  const map_of_maps = {
    tents: TENTS_TO_ENUM,
    kakurasu: KAKURASU_TO_ENUM,
    sudoku: SUDOKU_TO_ENUM,
    lightup: LIGHTUP_TO_ENUM,
    minesweeper: MINESWEEPER_TO_ENUM,
  };
  if (!(puzzle_type in map_of_maps)) throw new Error(`Unknown puzzle type: ${puzzle_type}`);
  return map_of_maps[puzzle_type];
}

function getFromEnumMap(puzzle_type: PUZZLE_TYPES): Record<string, number> {
  // prettier-ignore
  const map_of_maps = {
    "tents": ENUM_TO_TENTS,
    "kakurasu": ENUM_TO_KAKURASU,
    "sudoku": ENUM_TO_SUDOKU,
    "lightup": ENUM_TO_LIGHTUP,
    "minesweeper": ENUM_TO_MINESWEEPER
  };
  if (!(puzzle_type in map_of_maps)) throw new Error(`Unknown puzzle type: ${puzzle_type}`);
  return map_of_maps[puzzle_type] as Record<string, number>;
}

///////////////////////////////////////////////////////////////////////////////
// Conversion Functions
export type PuzzleCellTypeMap = {
  minesweeper: MinesweeperCell;
  sudoku: SudokuCell;
  tents: TentsCell;
  kakurasu: KakurasuCell;
  lightup: LightupCell;
};

export class PuzzleConverter {
  static fromResearch<K extends keyof PuzzleCellTypeMap>(
    grid: ResearchGrid,
    puzzleType: string,
  ): DeveloperGrid<PuzzleCellTypeMap[K]> {
    return fromResearchFormat<PuzzleCellTypeMap[K]>(grid, puzzleType as K);
  }

  static toResearch<K extends keyof PuzzleCellTypeMap>(
    grid: DeveloperGrid<PuzzleCellTypeMap[K]>,
    puzzleType: K,
  ): ResearchGrid {
    return toResearchFormat(grid, puzzleType);
  }
}
