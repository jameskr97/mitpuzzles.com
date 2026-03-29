/**
 * typed in-tab event bus using mitt.
 * used to decouple stores — emit lifecycle events instead of direct cross-store calls.
 */

import mitt from "mitt";
import type { PuzzleVariant } from "@/core/types";
import { createLogger } from "@/core/services/logger.ts";

export type EventMap = {
  // puzzle lifecycle
  "puzzle:solved:freeplay": { puzzle_type: string; variant: PuzzleVariant };
  "puzzle:solved:daily": { date: string };

  // daily
  "daily:clear-progress": { key: string };

  // visibility
  "puzzle:visibility-changed": { puzzle_type: string; mode: "freeplay" | "experiment"; visible: boolean };
};

export const emitter = mitt<EventMap>();

const log = createLogger("event-bus")
emitter.on('*', (event) => {
  log("event: ", event)
})
