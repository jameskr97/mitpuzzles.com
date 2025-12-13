export interface BackgroundJob {
  id: string;
  created_at: string;
  job_type: "file_upload" | "database_audit";
  status: string;
  puzzle_type: string;
  source_filename: string | null;
  total_puzzles: number;
  processed_count: number;
  unique_count: number;
  multi_solution_count: number;
  invalid_count: number;
  duplicate_count: number;
  error_count: number;
  disabled_count: number;
  completed_at: string | null;
}

export interface AnalysisJobPuzzle {
  id: string;
  puzzle_index: number;
  puzzle_data: Record<string, any>;
  definition_id: string;
  solution_id: string;
  complete_id: string;
  status: string;
  result: string | null;
  solutions: any[] | null;
  solution_count: number | null;
  error_message: string | null;
  imported: boolean;
}

export interface PaginatedPuzzles {
  items: AnalysisJobPuzzle[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
