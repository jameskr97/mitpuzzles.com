
import { ref, type Ref } from 'vue';

export enum KakurasuCellStates {
    Empty = 0,
    Filled,
    Crossed,
    NUM_STATES
}

export class ModelKakurasuPuzzle {
    readonly ROWS: number;
    readonly COLS: number;

    readonly hintRow: number[];
    readonly hintCol: number[];
    gamestate: Ref<number[]>; // 0: empty, 1: filled, 2: crossed

    constructor() {
        this.ROWS = 4;
        this.COLS = 4;
        this.hintRow = [4, 6, 4, 9]
        this.hintCol = [5, 6, 9, 5]
        this.gamestate = ref(Array(this.ROWS * this.COLS).fill(0));
    }

    getCellState(row: number, col: number): number {
        return this.gamestate.value[row * this.COLS + col];
    }

    getRowSum(row: number): number {
        let sum = 0;
        for (let i = 0; i < this.COLS; i++) {
            if (this.getCellState(row, i) === KakurasuCellStates.Filled) {
                sum += i + 1;
            }
        }
        return sum;
    }

    getColSum(col: number): number {
        let sum = 0;
        for (let i = 0; i < this.ROWS; i++) {
            if (this.getCellState(i, col) === KakurasuCellStates.Filled) {
                sum += i + 1;
            }
        }
        return sum;
    }


    onCellClick(row: number, col: number, event: MouseEvent): void {
        const index = row * this.COLS + col;
        const state = this.gamestate.value[index];

        // go backwards if right click
        if (event.button === 2) {
            this.gamestate.value[index] = (state + KakurasuCellStates.NUM_STATES - 1) % KakurasuCellStates.NUM_STATES;
        } else {
            this.gamestate.value[index] = (state + 1) % KakurasuCellStates.NUM_STATES;
        }
    }
}