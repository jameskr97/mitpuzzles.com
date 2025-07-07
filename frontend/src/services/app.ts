import { api } from "@/services/axios";
import type { PuzzleActionHistory, PuzzleActionPayload } from "@/store/game.ts";

////////////////////////////////////////////////////////////////////////////////
// Endpoints
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
  action_history: PuzzleActionPayload[]
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

export async function getPuzzle(puzzle_type: string, size: string, difficulty: string): Promise<any> {
  return await request("get", "/api/puzzle/definition/random/", { puzzle_type, size, difficulty });
}

export async function getPuzzleTypes(): Promise<any> {
  return await request("get", "/api/puzzle/definition/types/");
}

export async function submitFeedback(message: string, metadata: any): Promise<any> {
  return await request("post", "/api/feedback", { message, metadata });
}

export async function ensureVisitor(): Promise<any> {
  return await request("get", "/api/visitor");
}

export async function getPuzzleVariants(puzzle_type: string): Promise<any> {
  return await request("get", "/api/puzzle/definition/variants", { puzzle_type });
}

export async function markExperimentConsented(prolific_session_id: string): Promise<any> {
  return await request("post", "/api/experiment/consent", { prolific_session_id });
}

export async function markAtStep(prolific_session_id: string, step: string): Promise<any> {
  return await request("post", "/api/experiment/step", { prolific_session_id, step });
}

export async function submitExperimentSurvey(prolific_session_id: string, survey: any): Promise<any> {
  return await request("post", "/api/experiment/survey", { prolific_session_id, survey });
}

export async function getLeaderboard(ptype: string, psize: string, pdiff: string, limit: number = 10): Promise<any> {
  return await request("get", "/api/puzzle/freeplay/leaderboard/", {
    puzzle_type: ptype,
    puzzle_size: psize,
    puzzle_difficulty: pdiff,
    limit,
  });
}

export async function changeVisitorUsername(new_username: string): Promise<any> {
  return await request("post", "/api/visitor/username", { new_username });
}

export async function submitPuzzleAttempt(payload: PuzzleFreeplayAttemptPayload): Promise<any> {
  return await request("post", "/api/puzzle/freeplay/", { ...payload });
}
export async function submitProlificExperiment(payload: ProlificExperimentPayload): Promise<any> {
  return await request("post", "/api/experiment/prolific/", payload);
}
