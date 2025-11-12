import type { BoardEvents, Cell } from '@/features/games.components/board.interaction.ts';
import _ from 'lodash';

/**
 * Handles user interactions for canvas-based game boards.
 * Similar to BoardInteraction but designed for canvas coordinate systems.
 */
export class CanvasBoardInteraction {
  // Input state tracking
  private lastMouseDown: Cell | null = null;
  private isKeyPressed: boolean = false;
  private lastHover: Cell | null = null;
  private focused: Cell | null = null;
  private isMouseOnBoard: boolean = false;
  private mobileFocusCallback?: () => void;

  constructor(
    private getCellFromEvent: (event: MouseEvent) => Cell | null,
    private model: Partial<BoardEvents>,
    private emit?: (event: string, ...payload: any) => void,
  ) {
    // Global Event Listeners
    window.addEventListener('mouseup', (e: MouseEvent) => this.model?.onMouseUp?.(e));
    window.addEventListener('keydown', (e: KeyboardEvent) => {
      if (this.lastHover?.type !== 'cell') return; // Only handle keydown if hovering over a cell
      if (!this.isKeyPressed) {
        this.isKeyPressed = true;
        this.dispatchModelEvent('onCellHoveredKeyDown', this.lastHover, e);
      }
    });
    window.addEventListener('keyup', () => {
      this.isKeyPressed = false;
    });
  }

  dispatchModelEvent<K extends keyof BoardEvents>(
    key: K,
    hit?: Cell,
    event?: MouseEvent | KeyboardEvent
  ) {
    this.emit?.(key as string, { hit, event });

    const event_only_funcs = ['onMouseDown', 'onMouseUp', 'onMouseMove', 'onKeyDown'] as const;
    const fn = this.model?.[key];
    if (!fn) return;

    if (event_only_funcs.includes(key as any)) {
      // @ts-expect-error functions correctly, though throws type error
      fn(event);
    } else {
      // @ts-expect-error functions correctly, though throws type error
      fn(hit, event);

      // Fire onCellInteracted event
      if (
        hit &&
        hit.type === 'cell' &&
        typeof this.model?.onCellInteracted === 'function' &&
        key.startsWith('onCell')
      ) {
        this.model?.onCellInteracted(hit as Cell, event as MouseEvent);
      }
    }
  }

  /**
   * Mouse Down Event Handler
   */
  onMouseDown(event: MouseEvent) {
    const hit = this.getCellFromEvent(event);
    if (!hit) return;

    this.lastMouseDown = hit;
    this.dispatchModelEvent('onMouseDown', undefined, event);
    this.dispatchModelEvent('onCellMouseDown', hit, event);
  }

  /**
   * Mouse Up Event Handler
   */
  onMouseUp(event: MouseEvent) {
    const hit = this.getCellFromEvent(event);
    if (!hit) return;

    this.dispatchModelEvent('onMouseUp', undefined, event);
    this.dispatchModelEvent('onCellMouseUp', hit, event);

    // Check if this is a click (mousedown and mouseup on same cell)
    if (
      this.lastMouseDown &&
      this.lastMouseDown.type === 'cell' &&
      this.lastMouseDown.row === hit.row &&
      this.lastMouseDown.col === hit.col &&
      this.lastMouseDown.zone === hit.zone
    ) {
      this.dispatchModelEvent('onCellClick', this.lastMouseDown, event);

      if (!_.isEqual(this.focused, hit)) {
        this.dispatchModelEvent('onCellFocus', this.lastMouseDown, event);
      }

      this.focused = hit;
      this.mobileFocusCallback?.();
    }

    if (hit.type !== 'cell') {
      this.focused = null;
    }
  }

  /**
   * Mouse Move Event Handler
   */
  onMouseMove(event: MouseEvent) {
    const hit = this.getCellFromEvent(event);
    if (!hit) return;

    this.dispatchModelEvent('onMouseMove', undefined, event);

    // Update hover tracking
    if (hit.type === 'cell') {
      if (!this.lastHover || this.lastHover.row !== hit.row || this.lastHover.col !== hit.col) {
        if (this.lastHover) {
          this.dispatchModelEvent('onCellLeave', this.lastHover, event);
        }
        this.dispatchModelEvent('onCellEnter', hit, event);
        this.lastHover = hit;
      }
    } else if (this.lastHover) {
      this.dispatchModelEvent('onCellLeave', this.lastHover, event);
      this.lastHover = null;
    }
  }

  /**
   * Key Down Event Handler
   */
  onKeyDown(event: KeyboardEvent) {
    const hit = this.focused;
    if (!hit || hit.type !== 'cell') return;

    this.dispatchModelEvent('onKeyDown', hit, event);
    this.dispatchModelEvent('onCellKeyDown', hit, event);
  }

  /**
   * Board Enter Event Handler
   */
  onBoardEnter(event: MouseEvent) {
    if (this.isMouseOnBoard) return;

    this.isMouseOnBoard = true;
    this.dispatchModelEvent('onBoardEnter', undefined, event);
  }

  /**
   * Board Leave Event Handler
   */
  onBoardLeave(event: MouseEvent) {
    if (!this.isMouseOnBoard) return;

    this.isMouseOnBoard = false;

    // Clear last hover cell state when mouse leaves the board
    if (this.lastHover) {
      this.dispatchModelEvent('onCellLeave', this.lastHover, event);
      this.lastHover = null;
    }

    this.dispatchModelEvent('onBoardLeave', undefined, event);
  }

  /**
   * Set callback function to be called when mobile input should be focused
   */
  setMobileFocusCallback(callback: () => void) {
    this.mobileFocusCallback = callback;
  }
}
