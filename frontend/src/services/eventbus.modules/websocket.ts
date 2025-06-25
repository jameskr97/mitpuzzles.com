import { useWebSocket } from "@vueuse/core";
import { emit, on } from "@/services/eventbus";
import logger from "@/services/logger.ts";
import type { WebsocketFrame } from "@/codegen/websocket.ts";

export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  session_id?: string;
  actor_id?: string;
}

export const websocketModule = {
  name: "websocket",
  setup() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${protocol}://${window.location.host}/ws/puzzlen/`;

    logger.info("Setting up WebSocket module", { url });
    const unsubscribe = on("socket:send", (data) => send(JSON.stringify(data)));
    const { send, status, close } = useWebSocket(url, {
      autoReconnect: { retries: 0, delay: 2000 },
      onConnected: () => {
        emit("socket:connected");
        const urlParams = new URLSearchParams(window.location.search);
        const path = window.location.pathname;
        const valid_path = path.startsWith("/experiment/") || path.startsWith("/devtool/test-experiment");
        const valid_params = urlParams.has("PROLIFIC_PID");
        if (valid_path && valid_params) {
          // console.log("Sending auth message with Prolific ID");
          send(
            JSON.stringify({
              type: "auth:prolific",
              prolific_id: urlParams.get("PROLIFIC_PID"),
              session_id: urlParams.get("SESSION_ID"),
              study_id: urlParams.get("STUDY_ID"),
              experiment_id: "5f42a9e4-0018-4653-9068-e24ed19ac5e8",
            }),
          );
        } else {
          // console.log("Sending auth message for freeplay");
          send(JSON.stringify({ type: "auth:freeplay" }));
        }
      },
      onDisconnected: (_ws: WebSocket, event) =>
        emit("socket:disconnected", {
          code: event.code,
          reason: event.reason,
        }),
      onError: (_ws: WebSocket, event) => emit("socket:error", { error: event.toString() }),
      onMessage: (_ws: WebSocket, event: MessageEvent) => {
        // console.log("new message", event.data);
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          emit(message.type, message);
        } catch (e) {
          emit("socket:error", { error: event.data });
        }
      },
    });

    on("socket:connected", () => console.log("WebSocket connected"));
    on("socket:error", (error) => {
      console.log("WebSocket error:", error);
    });

    return {
      getConnectionStatus: () => status.value,
      forceDisconnect: () => close(),
      cleanup: unsubscribe,
    };
  },
};
