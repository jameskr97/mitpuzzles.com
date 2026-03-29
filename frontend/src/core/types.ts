// shared types derived from the backend OpenAPI schema
import type { components } from "@/core/services/api";

// puzzle
export type PuzzleDefinitionBase = components["schemas"]["PuzzleDefinitionResponse"];
export type PuzzleVariant = components["schemas"]["PuzzleVariant"];
export type LeaderboardEntry = components["schemas"]["LeaderboardEntryResponse"];
export type LeaderboardResponse = components["schemas"]["LeaderboardResponse"];
export type DailyTodayResponse = components["schemas"]["DailyTodayResponse"]
// auth
export type User = components["schemas"]["UserRead"];
export type RegisterPayload = components["schemas"]["UserCreate"];

// tracking
export type HeartbeatPayload = components["schemas"]["HeartbeatRequest"];
