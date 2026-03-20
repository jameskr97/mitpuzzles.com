// shared types derived from the backend OpenAPI schema
import type { components } from "@/core/services/api";

// puzzle
export type PuzzleVariant = components["schemas"]["PuzzleVariant"];
export type LeaderboardEntry = components["schemas"]["LeaderboardEntryResponse"];
export type LeaderboardResponse = components["schemas"]["LeaderboardResponse"];
// auth
export type User = components["schemas"]["UserRead"];
export type RegisterPayload = components["schemas"]["UserCreate"];

// tracking
export type HeartbeatPayload = components["schemas"]["HeartbeatRequest"];
