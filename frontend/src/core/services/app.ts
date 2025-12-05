import { api } from "@/core/services/axios.ts";
import type { PuzzleActionPayload } from "@/core/store/database";

async function request(method: string, url: string, data?: any) {
  let options: any = {
    url,
    method,
  };

  if (method.toUpperCase() === "GET" && data !== undefined) {
    options.params = data;
  } else if (data !== undefined) {
    options.data = data;
  }

  try {
    const response = await api.request(options);
    return {
      data: response.data,
      status: response.status,
    };
  } catch (error: any) {
    throw error;
  }
}

export interface PuzzleFreeplayAttemptPayload {
  puzzle_id: number;
  completed_at: string;
  completion_time_client_ms: number;
  action_history: PuzzleActionPayload[];
  is_solved: boolean;
  used_tutorial: boolean;
}

export interface ProlificExperimentPayload {
  prolific_participant_id: string;
  prolific_study_id: string;
  prolific_session_id: string;
  experiment_data: any;
  survey: {
    age: number;
    gender: string;
    education: string;
    experience: string;
    feedback: string;
  };
}


export async function getRandomPuzzleID(puzzle_type: string, size: string, difficulty: string): Promise<any> {
  return await request("get", "/api/puzzle/definition/random", { puzzle_type, puzzle_size: size, puzzle_difficulty: difficulty });
}

export async function getNextPuzzleID(puzzle_type: string, size: string, difficulty: string, session_id?: string): Promise<any> {
  const params: any = { puzzle_type, puzzle_size: size, puzzle_difficulty: difficulty };
  if (session_id) {
    params.session_id = session_id;
  }
  return await request("get", "/api/puzzle/next", params);
}

export async function submitFeedback(message: string, metadata: any): Promise<any> {
  return await request("post", "/api/feedback", { message, metadata });
}

export async function submitPuzzleAttempt(payload: PuzzleFreeplayAttemptPayload): Promise<any> {
  return await request("post", "/api/puzzle/freeplay/submit", { ...payload });
}

export async function submitProlificExperiment(payload: ProlificExperimentPayload): Promise<any> {
  return await request("post", "/api/experiment/prolific", payload);
}

export async function submitExperimentData(experiment_data: any): Promise<any> {
  return await request("post", "/api/experiment", {
    experiment: experiment_data.experiment,
    participant: experiment_data.participant,
    nodes: experiment_data.nodes
  });
}

// Analytics API functions
export interface StatsData {
  total_users: number;
  active_users_today: number;
  total_games_played: number;
  avg_session_duration_minutes: number;
  timestamp: string;
}

export interface GameStatisticsParams {
  include_superusers?: boolean;
  user_filter?: 'logged_in' | 'anonymous' | 'all';
  game_type?: string[];
  game_size?: string[];
  difficulty?: string[];
  start_date?: string;
  end_date?: string;
}

export interface UserEngagementParams {
  include_superusers?: boolean;
  start_date?: string;
  end_date?: string;
}

export interface GameTypesBreakdownParams {
  include_superusers?: boolean;
  user_filter?: 'logged_in' | 'anonymous' | 'all';
  start_date?: string;
  end_date?: string;
}

export async function get_analytics_stats_summary(include_superusers?: boolean): Promise<any> {
  return await request("get", "/api/analytics/stats-summary", { include_superusers });
}

export async function get_analytics_game_statistics(params?: GameStatisticsParams): Promise<any> {
  return await request("get", "/api/analytics/game-statistics", params);
}

export async function get_analytics_user_engagement(params?: UserEngagementParams): Promise<any> {
  return await request("get", "/api/analytics/user-engagement", params);
}

export async function get_analytics_game_types_breakdown(params?: GameTypesBreakdownParams): Promise<any> {
  return await request("get", "/api/analytics/game-types-breakdown", params);
}

export async function get_analytics_active_users(): Promise<any> {
  return await request("get", "/api/analytics/active-users");
}

export async function get_analytics_registrations_over_time(params?: { start_date?: string; end_date?: string; groupby?: string }): Promise<any> {
  return await request("get", "/api/analytics/registrations-over-time", params);
}

export async function get_analytics_average_session_time(params?: { start_date?: string; end_date?: string }): Promise<any> {
  return await request("get", "/api/analytics/average-session-time", params);
}

// Priority Puzzle API functions
export interface PriorityPuzzle {
  id: string;
  puzzle_id: string;
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string | null;
  added_at: string;
  is_active: boolean;
  times_shown: number;
  times_solved: number;
}

export interface PriorityPuzzleSummary {
  id: string;
  puzzle_id: string;
  added_at: string;
  is_active: boolean;
  times_shown: number;
  times_solved: number;
}

export interface PriorityGroup {
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string | null;
  total_puzzles: number;
  total_shown: number;
  total_solved: number;
  puzzles: PriorityPuzzleSummary[];
}

export interface PriorityGroupedResponse {
  groups: PriorityGroup[];
  total_groups: number;
  total_puzzles: number;
}

export interface PriorityPuzzlesResponse {
  priorities: PriorityPuzzle[];
  total_count: number;
}

export interface GetPriorityPuzzlesParams {
  include_inactive?: boolean;
  puzzle_type?: string;
  limit?: number;
  offset?: number;
}

export async function get_priority_puzzles(params?: GetPriorityPuzzlesParams): Promise<any> {
  return await request("get", "/api/puzzle/admin/priority", params);
}

export async function get_priority_puzzles_grouped(include_inactive: boolean = false): Promise<any> {
  return await request("get", "/api/puzzle/admin/priority/grouped", { include_inactive });
}

export async function add_priority_puzzle(puzzle_id: string): Promise<any> {
  return await request("post", "/api/puzzle/admin/priority", { puzzle_id });
}

export async function remove_priority_puzzle(priority_id: string): Promise<any> {
  return await request("delete", `/api/puzzle/admin/priority/${priority_id}`);
}

export function get_priority_puzzle_export_url(priority_id: string, solved_only: boolean = true): string {
  return `/api/puzzle/admin/priority/${priority_id}/export?solved_only=${solved_only}`;
}

export function get_priority_group_export_url(
  puzzle_type: string,
  puzzle_size: string,
  puzzle_difficulty: string | null,
  solved_only: boolean = true
): string {
  let url = `/api/puzzle/admin/priority/group/export?puzzle_type=${encodeURIComponent(puzzle_type)}&puzzle_size=${encodeURIComponent(puzzle_size)}&solved_only=${solved_only}`;
  if (puzzle_difficulty) {
    url += `&puzzle_difficulty=${encodeURIComponent(puzzle_difficulty)}`;
  }
  return url;
}
