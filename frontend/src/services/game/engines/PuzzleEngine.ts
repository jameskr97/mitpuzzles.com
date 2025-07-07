import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { PuzzleConverter, type ResearchGrid } from "@/services/game/engines/translator.ts";
import { SolutionValidator } from "@/services/game/engines/solutions.ts";

export interface InputHandler {
  on_cell_click: (engine: PuzzleEngine, cell: Cell, button: number, override?: number) => boolean;
  on_row_click: (engine: PuzzleEngine, cell: Cell, button: number, override?: number) => boolean;
  on_col_click: (engine: PuzzleEngine, cell: Cell, button: number, override?: number) => boolean;
  on_cell_key_down: (engine: PuzzleEngine, cell: Cell, key: string) => boolean;
}

export interface RuleViolationCell {
  row: number;
  col: number;
}

export interface RuleViolation {
  locations: Array<RuleViolationCell>;
  rule_name: string;
}

export interface RuleDefinition {
  rule_func: (engine: PuzzleEngine) => RuleViolation | null;
}

export class PuzzleEngine<TMeta = any> {
  protected tutorial_mode: boolean = false;
  protected input_handlers: Partial<InputHandler>[] | null = null;
  protected gamerule_constraint_checkers: RuleDefinition[] | null = null;
  protected solution_checker: SolutionValidator;

  public board_state: number[][];
  protected readonly initial_state: number[][];
  public readonly immutable_cells: number[][];

  constructor(
    public definition: PuzzleDefinition<TMeta>,
    board_state?: number[][],
    input_handlers: Partial<InputHandler> | Partial<InputHandler>[] | null = null,
    gamerule_constraint_checkers: RuleDefinition | RuleDefinition[] | null = null,
  ) {
    // convert research initial state into developer-friendly format
    const initial_state = definition.initial_state;
    const x = PuzzleConverter.fromResearch(initial_state as ResearchGrid, this.definition.puzzle_type);
    this.initial_state = JSON.parse(JSON.stringify(x));
    this.board_state = board_state ? JSON.parse(JSON.stringify(board_state)) : JSON.parse(JSON.stringify(x));
    this.immutable_cells = this.get_immutable_cells();
    this.solution_checker = new SolutionValidator(definition.puzzle_type, definition.solution_hash);

    // Initialize the input handler
    if (input_handlers !== null) {
      if (Array.isArray(input_handlers)) {
        this.input_handlers = input_handlers;
      } else if (typeof input_handlers === "object") {
        this.input_handlers = [input_handlers];
      }
    }

    // Initialize game constraints
    if (gamerule_constraint_checkers !== null) {
      if (Array.isArray(gamerule_constraint_checkers)) {
        this.gamerule_constraint_checkers = gamerule_constraint_checkers;
      } else if (typeof gamerule_constraint_checkers === "object") {
        this.gamerule_constraint_checkers = [gamerule_constraint_checkers];
      }
    }
  }

  //////////////////////////////////////////////////////
  /// Universal Methods
  get_immutable_cells(): number[][] {
    const result: number[][] = [];
    for (let r = 0; r < this.definition.rows; r++) {
      const rowData: number[] = [];
      for (let c = 0; c < this.definition.cols; c++) {
        const can_edit = this.can_modify_cell({ row: r, col: c, zone: "game", type: "cell" });
        rowData.push(can_edit ? 0 : 1);
      }
      result.push(rowData);
    }
    return result;
  }

  //////////////////////////////////////////////////////
  /// Abstract Methods
  can_modify_cell(cell: Cell): boolean {
    return false;
  }

  //////////////////////////////////////////////////////
  /// Input Events
  private dispatch_to_handlers(method_name: keyof InputHandler, ...args: any[]): boolean {
    if (!this.input_handlers) return false;
    for (const handler of this.input_handlers) {
      const method = handler[method_name] as ((...args: any[]) => boolean) | undefined;
      if (method && method.apply(handler, args)) {
        return true;
      }
    }
    return false;
  }

  handle_input_event(
    target: string,
    action: string,
    cell: Cell,
    event: MouseEvent | KeyboardEvent,
    override?: number,
  ): boolean {
    if (cell.col === undefined || cell.row === undefined) {
      // console.warn("Cell must have row and col defined for input handling.");
      return false;
    }

    // Check if cell can be modified
    if (!this.can_modify_cell(cell) && cell.zone === "game") {
      // console.warn("Cell cannot be modified:", cell);
      return false;
    }

    const button = event instanceof MouseEvent ? event.button : undefined;
    const key = event instanceof KeyboardEvent ? event.key : undefined;

    // console.log(`Handling input event: ${target}-${action}`);
    switch (`${target}-${action}`) {
      case "cell-click":
        return this.dispatch_to_handlers("on_cell_click", this, cell, button, override);
        break;
      case "cell-keydown":
        return this.dispatch_to_handlers("on_cell_key_down", this, cell, key);
    }
    return false;
  }

  //////////////////////////////////////////////////////
  /// Actions
  board_clear(): void {
    Object.assign(this.board_state, JSON.parse(JSON.stringify(this.initial_state)));
  }

  async check_solution(): Promise<boolean> {
    if (!this.solution_checker) {
      console.warn("No solution checker defined for this puzzle type.");
      return false;
    }
    try {
      return await this.solution_checker.validateSolution(this.board_state);
    } catch (error) {
      console.error("Error checking solution:", error);
      return false;
    }
  }

  get_violations(): RuleViolation[] {
    if (!this.gamerule_constraint_checkers) return [];

    const results: RuleViolation[] = [];
    for (const rule of this.gamerule_constraint_checkers) {
      try {
        const result = rule.rule_func(this);
        if (result !== null) {
          results.push(result);
        }
      } catch (error) {
        console.error("Rule validation failed:", error);
      }
    }
    return results;
  }
}
