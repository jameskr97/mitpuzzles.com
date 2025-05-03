export function useCellStateCycler(NUM_STATES: number, allowedStates?: number[]) {
  if (NUM_STATES < 2) throw new Error("NUM_STATES must be at least 2");

  return {
    /**
     * Cycles the state of a cell based on the mouse button clicked.
     * @param state - The current state of the cell.
     * @param button - The mouse button clicked (0 for left, 1 for middle, 2 for right).
     */
    cycle(state: number, button: number): number {
      const mod = (n: number, m: number): number => ((n % m) + m) % m;
      const states = allowedStates ?? Array.from({ length: NUM_STATES }, (_, i) => i);
      const stateIndex = states.indexOf(state);

      // left click is forward cycle, right click is backward cycle
      if (button === 0) return states[mod(stateIndex + 1, states.length)];
      if (button === 2) return states[mod(stateIndex - 1, states.length)];
      return states[stateIndex]; // No change for other buttons
    },
  };
}
