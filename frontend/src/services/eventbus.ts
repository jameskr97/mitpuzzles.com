import mitt from "mitt";
import type { AnyPuzzleState } from "@/services/states.ts";
import type { WebSocketMessage } from "@/services/eventbus.modules/websocket.ts";

export interface ActionPosition {
  row: number;
  col: number;
  zone: "game" | "topGutter" | "leftGutter" | "rightGutter" | "bottomGutter";
  button?: "left" | "right" | "middle" | "unknown";
  state?: number;
  direction?: "top" | "right" | "bottom" | "left";
  key?: string;
}

export const eventBus = mitt<AppEvents>();
export type AppEvents = {
  // === SOCKET EVENTS ===
  "socket:connecting": void;
  "socket:connected": void;
  "socket:disconnected": { code?: number; reason?: string };
  "socket:reconnecting": { attempt: number };
  "socket:reconnected": void;
  "socket:error": { error: string };
  "socket:message": any;
  "socket:latency": { latency: number };
  "socket:send": any;

  // === GAME EVENTS ===
  "game:set_active_puzzle": string;
  "game:state": WebSocketMessage<AnyPuzzleState>;
  "game:solved": { sessionId: string; solved: boolean };
  "game:created": { sessionId: string; puzzleType: string };
  "game:reset": { sessionId: string };
  "game:submit_result": boolean;

  // === COMMANDS ===
  "cmd:create": { puzzle_type: string; puzzle_size?: string; puzzle_difficulty?: string };
  "cmd:resume": { session_id: string };
  "cmd:action": { target: string; action: string; position: ActionPosition };
  "cmd:reset": { sessionId: string };
  "cmd:submit": { sessionId: string };
  "cmd:toggle_tutorial": { enabled: boolean };

  // === UI EVENTS ===
  "ui:notification": { message: string; type: "success" | "error" | "info" };

  // === ESCAPE HATCH ===
  [key: string]: any; // Allow arbitrary events
};

export function emit<K extends keyof AppEvents>(
  event: K,
  ...args: AppEvents[K] extends void ? [] : [AppEvents[K]]
): void {
  eventBus.emit(event, args[0]);
}

export function on(event: "*", handler: (event: string, data: any) => void): () => void;

export function on<K extends keyof AppEvents>(
  event: K,
  handler: AppEvents[K] extends void ? () => void : (data: AppEvents[K]) => void,
): () => void;

export function on(event: string, handler: any): () => void {
  if (event === "*") {
    eventBus.on("*" as any, handler);
    return () => eventBus.off("*" as any, handler);
  } else {
    eventBus.on(event, handler);
    return () => eventBus.off(event, handler);
  }
}

export interface EventModule<T = Record<string, any>> {
  name: string;
  setup(): T & { cleanup?: () => void };
}

export class ModuleManager {
  private composables: Map<string, any> = new Map();

  register<T>(module: EventModule<T>): this {
    const composable = module.setup();
    this.composables.set(module.name, composable);
    return this;
  }

  getComposable<T>(name: string): T | undefined {
    return this.composables.get(name) as T;
  }

  cleanup(name?: string) {
    if (name) {
      const composable = this.composables.get(name);
      composable?.cleanup?.();
      this.composables.delete(name);
    } else {
      this.composables.forEach((composable) => composable?.cleanup?.());
      this.composables.clear();
    }
  }
}
