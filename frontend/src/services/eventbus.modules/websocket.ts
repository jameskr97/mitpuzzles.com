import { useWebSocket } from "@vueuse/core";
import { emit, on } from "@/services/eventbus";
import logger from "@/services/logger.ts";

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
    const url = `${protocol}://${window.location.host}/ws/puzzle/`;

    logger.info("Setting up WebSocket module", { url });
    const unsubscribe = on("socket:send", (data) => send(JSON.stringify(data)));
    const { send, status, close } = useWebSocket(url, {
      autoReconnect: { retries: 3, delay: 2000 },
      onConnected: () => emit("socket:connected"),
      onDisconnected: (_ws: WebSocket, event) =>
        emit("socket:disconnected", { code: event.code, reason: event.reason }),
      onError: (_ws: WebSocket, event) => emit("socket:error", { error: event.toString() }),
      onMessage: (_ws: WebSocket, event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          emit(message.type, message);
        } catch (e) {
          emit("socket:error", { error: event.data });
        }
      },
    });

    // Listen for commands to send to server

    return {
      getConnectionStatus: () => status.value,
      forceDisconnect: () => close(),
      cleanup: unsubscribe,
    };
  },
};
