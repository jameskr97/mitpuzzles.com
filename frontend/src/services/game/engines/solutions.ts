import {
  type CellType,
  type DeveloperGrid,
  KakurasuCell,
  LightupCell,
  MinesweeperCell,
  SudokuCell,
  TentsCell,
} from "@/services/game/engines/translator.ts";

interface PuzzleConfig {
  positiveValues: number[];
  negativeValues: number[];
  immutableValues: number[];
  emptyValues: number[];
}

class RunLengthEncoder {
  private static readonly PUZZLE_CONFIGS: Record<string, PuzzleConfig> = {
    tents: {
      positiveValues: [TentsCell.TENT], // Only tents matter for solution
      negativeValues: [TentsCell.GREEN], // Green marks (pertinent negative)
      immutableValues: [TentsCell.TREE], // Trees are given
      emptyValues: [TentsCell.EMPTY], // Empty cells
    },

    kakurasu: {
      positiveValues: [KakurasuCell.BLACK], // Black cells (marked)
      negativeValues: [KakurasuCell.CROSS], // Cross marks (pertinent negative)
      immutableValues: [], // No immutable cells
      emptyValues: [KakurasuCell.EMPTY], // Empty cells
    },

    sudoku: {
      positiveValues: [
        SudokuCell.ONE,
        SudokuCell.TWO,
        SudokuCell.THREE,
        SudokuCell.FOUR,
        SudokuCell.FIVE,
        SudokuCell.SIX,
        SudokuCell.SEVEN,
        SudokuCell.EIGHT,
        SudokuCell.NINE,
      ],
      negativeValues: [], // No pertinent negatives
      immutableValues: [], // Given numbers treated same as solution
      emptyValues: [SudokuCell.EMPTY], // Empty cells
    },

    lightup: {
      positiveValues: [LightupCell.BULB], // Only bulbs matter for solution
      negativeValues: [LightupCell.CROSS], // Lit cells (pertinent negative)
      immutableValues: [
        LightupCell.WALL_0,
        LightupCell.WALL_1,
        LightupCell.WALL_2,
        LightupCell.WALL_3,
        LightupCell.WALL_4,
        LightupCell.WALL_NO_CONSTRAINT,
      ],
      emptyValues: [LightupCell.EMPTY], // Empty cells
    },

    minesweeper: {
      positiveValues: [MinesweeperCell.FLAG], // Flags (marking mines)
      negativeValues: [MinesweeperCell.SAFE], // Safe marks (pertinent negative)
      immutableValues: [
        MinesweeperCell.ONE,
        MinesweeperCell.TWO,
        MinesweeperCell.THREE,
        MinesweeperCell.FOUR,
        MinesweeperCell.FIVE,
        MinesweeperCell.SIX,
        MinesweeperCell.SEVEN,
        MinesweeperCell.EIGHT,
      ],
      emptyValues: [MinesweeperCell.UNMARKED], // Unmarked cells
    },
  };

  private config: PuzzleConfig;
  private puzzleType: string;

  constructor(puzzleType: string) {
    this.puzzleType = puzzleType;
    const config = RunLengthEncoder.PUZZLE_CONFIGS[puzzleType];
    if (!config) {
      throw new Error(`Unknown puzzle type: ${puzzleType}`);
    }
    this.config = config;
  }

  private isPositiveState(cellValue: CellType): boolean {
    return this.config.positiveValues.includes(cellValue);
  }

  private getPositiveStateValue(cellValue: CellType): string {
    const positiveValues = this.config.positiveValues;

    if (positiveValues.length === 1) {
      // Simple binary puzzles (Tents, Kakurasu, Lightup, Minesweeper)
      return "1";
    } else {
      // Sudoku - use the actual number
      return cellValue.toString();
    }
  }

  private calculateGap(row1: number, col1: number, row2: number, col2: number, board: DeveloperGrid<CellType>): number {
    const cols = board[0]?.length || 0;
    const pos1 = row1 * cols + col1;
    const pos2 = row2 * cols + col2;

    // Count ALL cells between positions to maintain spatial integrity
    return pos2 - pos1 - 1;
  }

  async createRunLengthEncoding(board: DeveloperGrid<CellType>): Promise<string> {
    const encodingParts: string[] = [];
    const positivePositions: Array<[number, number, string]> = [];

    // Find all positive state positions
    for (let rowIdx = 0; rowIdx < board.length; rowIdx++) {
      for (let colIdx = 0; colIdx < board[rowIdx].length; colIdx++) {
        const cellValue = board[rowIdx][colIdx];
        if (this.isPositiveState(cellValue)) {
          const stateChar = this.getPositiveStateValue(cellValue);
          positivePositions.push([rowIdx, colIdx, stateChar]);
        }
      }
    }

    if (positivePositions.length === 0) {
      return "0"; // No positive states, return empty encoding
      return await this.hashEncoding("0");
    }

    // Encode leading empty cells before first positive state
    const [firstRow, firstCol] = positivePositions[0];
    const cols = board[0]?.length || 0;
    const leadingGap = firstRow * cols + firstCol;

    if (leadingGap > 0) {
      if (leadingGap <= 26) {
        encodingParts.push(String.fromCharCode("a".charCodeAt(0) + leadingGap - 1));
      } else {
        encodingParts.push(`#${leadingGap}`);
      }
    }

    // Build run-length encoding
    for (let i = 0; i < positivePositions.length; i++) {
      const [row, col, stateChar] = positivePositions[i];
      encodingParts.push(stateChar);

      if (i < positivePositions.length - 1) {
        const [nextRow, nextCol] = positivePositions[i + 1];
        const gapCount = this.calculateGap(row, col, nextRow, nextCol, board);

        if (gapCount > 0) {
          if (gapCount <= 26) {
            // Convert to letter (a=1, b=2, ..., z=26)
            encodingParts.push(String.fromCharCode("a".charCodeAt(0) + gapCount - 1));
          } else {
            // For larger gaps
            encodingParts.push(`#${gapCount}`);
          }
        }
      }
    }

    const encoding = encodingParts.join("");
    return encoding;
    // return await this.hashEncoding(encoding);
  }

  private async hashEncoding(encoding: string): Promise<string> {
    const hashInput = encoding;
    const encoder = new TextEncoder();
    const data = encoder.encode(hashInput);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }
}

// Solution validator for frontend validation
export class SolutionValidator {
  private encoder: RunLengthEncoder;

  constructor(
    puzzle_type: string,
    private solution_hash: string,
  ) {
    this.encoder = new RunLengthEncoder(puzzle_type);
  }

  async validateSolution(currentBoard: DeveloperGrid<CellType>): Promise<boolean> {
    const currentHash = await this.encoder.createRunLengthEncoding(currentBoard);
    return currentHash === this.solution_hash;
  }
}
