interface ViolationMetadata {
  title: string;
  description: string;
}

export const VIOLATION_MAP: Record<string, ViolationMetadata> = {
  // Generic
  line_sum_row_exceeded: {
    title: "Line Sum Exceeded",
    description: "The sum of the numbers in this row exceeds the allowed limit.",
  },
  line_sum_col_exceeded: {
    title: "Line Sum Exceeded",
    description: "The sum of the numbers in this column exceeds the allowed limit.",
  },
  line_all_row_negative: {
    title: "Line Sum Impossible",
    description: "The sum of the numbers in this row cannot be achieved with the current board.",
  },
  line_all_col_negative: {
    title: "Line Sum Impossible",
    description: "The sum of the numbers in this column cannot be achieved with the current board.",
  },

  // Minesweeper
  minesweeper_surrounding_flag_violation: {
    title: "Too Many Flags",
    description: "These cells have too many flags around them.",
  },

  // Lightup
  bulb_intersection_violation: {
    title: "Bulb Intersect Violation",
    description: "These bulbs are in the same row or column as another bulb, which is not allowed.",
  },
  numbered_wll_constraint_violated: {
    title: "Wal count constraint violated",
    description: "There are too many bulbs around these numbered walls.",
  },

  // Sudoku
  col_duplicate_violation: {
    title: "Column Duplicate",
    description: "There are duplicate numbers in the same column.",
  },
  row_duplicate_violation: {
    title: "Row Duplicate",
    description: "There are duplicate numbers in the same row.",
  },
  box_duplicate_violation: {
    title: "Box Duplicate",
    description: "There are duplicate numbers in the same 3x3 box.",
  },

  // Tents
  tents_intersecting: {
    title: "Tents Intersecting",
    description: "Tents cannot touch each other, even diagonally.",
  },
  tent_count_col_mismatch: {
    title: "Tent Count Mismatch",
    description: "The number of tents in this column does not match the expected count.",
  },
  tent_count_row_mismatch: {
    title: "Tent Count Mismatch",
    description: "The number of tents in this row does not match the expected count.",
  },
  tree_inaccessible: {
    title: "Tree Inaccessible",
    description: "This tree cannot be reached by any tent.",
  },
};
