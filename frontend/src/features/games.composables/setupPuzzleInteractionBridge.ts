import { type BoardEvents } from "@/features/games.components/board.interaction.ts";
import { useDragStateChanger } from "@/features/games.composables/useDragStateChanger.ts";
import { useClearStateBehaviour } from "@/features/games.composables/useClearStateBehaviour.ts";
import { useStateCycleBehaviour } from "@/features/games.composables/useStateCycleBehaviour.ts";
import { EventHandlerManager } from "@/features/games.composables/EventHandlerManager.ts";
import { emit } from "@/services/eventbus.ts";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import type { PayloadPuzzleType } from "@/codegen/websocket/game.schema";

/**
 * GameEvents - Interface for game-level events
 *
 * These are events that happen at the game level, not individual board interactions.
 * They're typically used for notifications or side effects when game state changes.
 *
 * For example: tracking moves, updating scores, auto-saving progress
 */
export interface GameEvents {
  onBoardModified: (board: number[]) => void;
  onBoardCleared: () => void;
  onBoardChanged: (board: number[]) => void;
}

/**
 * RenderEvents - Interface for render-related events
 *
 * These events are used to customize how cells and borders are rendered.
 * They return styling information that can be applied to elements.
 */
export interface RenderEvents {
  // Cell rendering
  isCellVisible?: (row: number, col: number) => boolean;
  getCellStyles?: (row: number, col: number) => Record<string, string>;
  getCellClasses?: (row: number, col: number) => string[];
  getCellContent?: (row: number, col: number) => string | number | null;
  isCellActive?: (row: number, col: number) => boolean;

  // Gutter content rendering (for labels, sums, etc.)
  getTopGutterClasses?: (row: number, col: number) => string[];
  getTopGutterStyles?: (row: number, col: number) => Record<string, string>;
  getBottomGutterClasses?: (row: number, col: number) => string[];
  getBottomGutterStyles?: (row: number, col: number) => Record<string, string>;
  getLeftGutterClasses?: (row: number, col: number) => string[];
  getLeftGutterStyles?: (row: number, col: number) => Record<string, string>;
  getRightGutterClasses?: (row: number, col: number) => string[];
  getRightGutterStyles?: (row: number, col: number) => Record<string, string>;
}

/**
 * Create a bridge between the puzzle interaction and the puzzle state.
 * - This allows users to add custom behaviours to the puzzle interaction.
 * - Default global behaviours are added by default.
 * - Note, the order of the behaviours is important, as they are called in the order they are added.
 * @param session The puzzle state session
 */
export function createPuzzleInteractionBridge(puzzle_type: PayloadPuzzleType) {
  const ctrl = usePuzzleController(puzzle_type)

  // Create event handler managers for each type of event
  const boardEventManager = new EventHandlerManager<BoardEvents>();
  const gameEventManager = new EventHandlerManager<GameEvents>();
  const renderEventManager = new EventHandlerManager<RenderEvents>();
  emit("game:set_active_puzzle", puzzle_type);

  /**
   * Add a behavior for board interaction events
   *
   * @param behaviour A function that takes the session and returns board event handlers
   * @returns The compiled behavior object that was added
   */
  function addInputBehaviour<T extends Partial<BoardEvents>>(
    behaviour: (ctrl: ReturnType<typeof usePuzzleController>) => T,
  ): T {
    return boardEventManager.addBehaviour(behaviour, ctrl);
  }

  /**
   * Add a behavior for game-level events
   *
   * @param behaviour A function that takes the session and returns game event handlers
   * @returns The compiled behavior object that was added
   */
  function addGameBehaviour<T extends Partial<GameEvents>>(behaviour: (puzzle: typeof ctrl) => T): T {
    return gameEventManager.addBehaviour(behaviour, ctrl);
  }

  /**
   * Add a behavior for rendering customization
   *
   * @param behaviour A function that takes the session and returns render event handlers
   * @returns The compiled behavior object that was added
   */
  function addRenderBehaviour<T extends Partial<RenderEvents>>(behaviour: (puzzle: typeof ctrl) => T): T {
    return renderEventManager.addBehaviour(behaviour, ctrl);
  }

  /**
   * Compile all the input behaviors into a single object
   *
   * @param includeDefaultBehaviours Whether to include default input behaviors
   * @returns Compiled board event handlers
   */
  function getBridge(includeDefaultBehaviours: boolean = true): Partial<BoardEvents> {
    // Add default behaviors if specified
    if (includeDefaultBehaviours) {
      addInputBehaviour(useClearStateBehaviour);
      addInputBehaviour(useStateCycleBehaviour);
      addInputBehaviour(useDragStateChanger);
    }

    return boardEventManager.getCompiledHandlers("first-true");
  }

  /**
   * Get the compiled rendering behaviors
   *
   * @returns Compiled render event handlers
   */
  function getRenderBehaviors(): Partial<RenderEvents> {
    return renderEventManager.getCompiledHandlers("merge-results");
  }

  /**
   * Set up a watcher that emits the onBoardModified event when the board changes
   */
  // if (ctrl.state && Array.isArray(ctrl.state)) {
  //   // Initial board state tracking
  //   const initialBoard = [...ctrl.state];
  //
  //   // Watch for changes to the board
  //   setInterval(() => {
  //     if (session.state.value && Array.isArray(session.state.value.board)) {
  //       const currentBoard = session.state.value.board;
  //       // Only emit if the board actually changed
  //       if (JSON.stringify(initialBoard) !== JSON.stringify(currentBoard)) {
  //         gameEventManager.emit("onBoardModified", currentBoard);
  //         // Update tracked board
  //         initialBoard.splice(0, initialBoard.length, ...currentBoard);
  //       }
  //     }
  //   }, 100); // Check every 100ms
  // }
  //
  /**
   * Return the public API of the interaction bridge
   */
  return {
    addInputBehaviour, // Add behaviors for board interaction events (clicks, hovers)
    addGameBehaviour, // Add behaviors for game-level events (notifications)
    addRenderBehaviour, // Add behaviors for rendering customization
    getBridge, // Get compiled board event handlers
    getRenderBehaviors, // Get compiled rendering handlers
    boardEvents: boardEventManager,
    gameEvents: gameEventManager,
    renderEvents: renderEventManager,
  };
}
