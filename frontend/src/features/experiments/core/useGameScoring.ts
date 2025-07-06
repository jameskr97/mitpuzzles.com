export function useGameScoring() {
  
  /**
   * Calculate score for a puzzle
   * @param currentBoard - The current state of the board
   * @param definition - The puzzle definition with solution
   * @returns Points earned (+3 per correct mutable cell, -3 per wrong mutable cell)
   */
  function calculateScore(currentBoard: number[][], definition: PuzzleDefinition & { solution: number[][] }): number {
    if (!currentBoard || !definition.initial_state || !definition.solution) return 0;
    
    let points = 0;
    
    for (let row = 0; row < definition.rows; row++) {
      for (let col = 0; col < definition.cols; col++) {
        const initialValue = definition.initial_state[row][col];
        const currentValue = currentBoard[row][col];
        const solutionValue = definition.solution[row][col];
        
        // Only score cells that were initially empty (mutable cells)
        if (initialValue === 0 || initialValue === -1) {
          // If cell is filled
          if (currentValue !== 0 && currentValue !== -1) {
            if (currentValue === solutionValue) {
              points += 3; // Correct cell
            } else {
              points -= 3; // Wrong cell
            }
          }
          // Empty cells don't affect score
        }
      }
    }
    
    return Math.max(0, points); // Don't go below 0
  }

  return {
    calculateScore
  };
}
