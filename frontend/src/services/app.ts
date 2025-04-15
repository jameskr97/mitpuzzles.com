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

  return api
    .request(options)
    .then((response) => response.data)
    .catch((error) => error.response.data);
}

export async function getAppSettings(): Promise<any> {
  return await request("get", "/api/config/game-settings");
}
export async function getRandomPuzzle(puzzle_type: string): Promise<any> {
  return await request("get", "/api/puzzle/random", { puzzle_type, variant: "default" });
}
export async function submitGameRecording(puzzle_id: number, data: any): Promise<any> {
  return await request("post", "/api/puzzle/submit", { puzzle_id, data });
}
export async function getUnsolvedPuzzleCount(params?: { puzzle_type?: string }): Promise<any> {
  return await request("get", "/api/puzzle/unsolved_count", params);
}
export async function getUnsolvedPuzzle(params?: { puzzle_type?: string; variant?: string }): Promise<any> {
  return await request("get", "/api/puzzle/unsolved", params);
}