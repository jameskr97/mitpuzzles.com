import { api } from "@/services/axios";

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

export async function getAppSettings(): Promise<any> {
  return await request("get", "/api/config/game-settings");
}
export async function getRandomPuzzle(puzzle_type: string): Promise<any> {
  return await request("get", "/api/puzzle/random", { puzzle_type, variant: "default" });
}
export async function submitGameRecording(puzzle_id: number, timestamp: string, data: any): Promise<any> {
  return await request("post", "/api/puzzle/submit", { puzzle_id, timestamp, data });
}
export async function getUnsolvedPuzzleCount(params?: { puzzle_type?: string }): Promise<any> {
  return await request("get", "/api/puzzle/unsolved_count", params);
}
export async function getUnsolvedPuzzle(params?: { puzzle_type?: string; variant?: string }): Promise<any> {
  return await request("get", "/api/puzzle/unsolved", params);
}
export async function submitFeedback(message: string, metadata: any): Promise<any> {
  return await request("post", "/api/feedback", { message, metadata });
}
export async function ensureVisitor(): Promise<any> {
  return await request("post", "/api/visitor");
}
