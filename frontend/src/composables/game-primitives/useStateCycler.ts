/**
 * useStateCycler - Click-to-cycle state pattern
 *
 * Used by most cell-state games (Minesweeper, Lightup, Kakurasu, etc.)
 * Left click cycles forward, right click cycles backward.
 */

export interface StateCyclerReturn {
  /**
   * Get the next state value based on current value and mouse button
   * @param current - Current cell value
   * @param button - Mouse button (0 = left, 2 = right)
   * @returns Next state value in the cycle
   */
  cycle_state: (current: number, button: number) => number;

  /**
   * Check if a value is a valid state in this cycler
   */
  is_valid_state: (value: number) => boolean;

  /**
   * Get all states in the cycle
   */
  states: readonly number[];
}

/**
 * Create a state cycler for click-to-toggle behavior
 *
 * @param states - Array of states to cycle through (in order)
 *                 Can be an array of numbers or an enum object
 *
 * @example
 * // With explicit array
 * const { cycle_state } = useStateCycler([0, 1, 2]); // EMPTY -> FLAG -> SAFE -> EMPTY
 *
 * // With enum
 * enum MinesweeperCell { UNMARKED = 0, FLAG = 1, SAFE = 2 }
 * const { cycle_state } = useStateCycler(MinesweeperCell);
 */
export function useStateCycler(
  states: number[] | Record<string, number>
): StateCyclerReturn {
  // Normalize input: if it's an enum object, extract numeric values
  const state_array: readonly number[] = Array.isArray(states)
    ? Object.freeze([...states])
    : Object.freeze(
        Object.values(states).filter((v): v is number => typeof v === "number")
      );

  if (state_array.length === 0) {
    throw new Error("useStateCycler: states array cannot be empty");
  }

  /**
   * Get the next state value based on current value and mouse button
   */
  function cycle_state(current: number, button: number): number {
    const current_index = state_array.indexOf(current);

    // If current value isn't in states, start from beginning
    if (current_index === -1) {
      return state_array[0];
    }

    let next_index: number;
    if (button === 2) {
      // Right click: cycle backward
      next_index = (current_index - 1 + state_array.length) % state_array.length;
    } else {
      // Left click (or any other): cycle forward
      next_index = (current_index + 1) % state_array.length;
    }

    return state_array[next_index];
  }

  /**
   * Check if a value is a valid state
   */
  function is_valid_state(value: number): boolean {
    return state_array.includes(value);
  }

  return {
    cycle_state,
    is_valid_state,
    states: state_array,
  };
}
