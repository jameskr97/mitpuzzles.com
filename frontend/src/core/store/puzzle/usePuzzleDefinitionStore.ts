export function getCurrentPuzzleID(puzzle_type: string): string | null {
  return localStorage.getItem(`mitlogic.${puzzle_type}.current_id`);
}

export function setCurrentPuzzleID(puzzle_type: string, puzzle_id: string): void {
  localStorage.setItem(`mitlogic.${puzzle_type}.current_id`, puzzle_id);
}
