import { api } from "@/services/axios";
import type { PuzzleActionPayload } from "@/store/database";

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
