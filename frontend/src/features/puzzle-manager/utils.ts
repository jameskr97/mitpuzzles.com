import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";

export const format_date = (date_string: string) => {
  return new Date(date_string).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
};

export const get_status_variant = (status: string) => {
  switch (status) {
    case "completed":
      return "green";
    case "running":
      return "blue";
    case "failed":
      return "red";
    default:
      return "secondary";
  }
};

export const get_result_variant = (result: string | null) => {
  switch (result) {
    case "unique":
      return "green";
    case "multi_solution":
      return "secondary";
    case "invalid":
      return "red";
    case "error":
      return "red";
    case "duplicate":
      return "secondary";
    default:
      return "secondary";
  }
};

export const convert_to_definition = (puzzle_data: Record<string, any>): PuzzleDefinition => {
  return {
    id: puzzle_data.complete_id || puzzle_data.definition_id || "unknown",
    puzzle_type: puzzle_data.puzzle_type,
    rows: puzzle_data.rows,
    cols: puzzle_data.cols,
    initial_state: puzzle_data.initial_state,
    solution: puzzle_data.solution,
    meta: puzzle_data,
  };
};
