import mitt from "mitt";
import type { Payload, WebsocketEnvelope } from "@/codegen/websocket/envelope.schema";
import { decode, encode } from "@msgpack/msgpack";
import type { CommandPing, EventPong } from "@/codegen/websocket/ping.schema";
import logger from "@/services/logger.ts";
import { useAppConfig } from "@/store/app.ts";
import { type MaybeOptions, normalizeOptions } from "@/utils.ts";

interface AutoReconnectOptions {
  retries: number;
  delay: number;
}

interface NetDriverOpts {
  url: string | (() => string);
  heartbeatMs?: number;
  autoReconnect?: MaybeOptions<AutoReconnectOptions>;
}

type Events = {
  open: WebSocket;
  close: CloseEvent;
  error: Event;
  message: WebsocketEnvelope; // parsed + typed
};

export class NetDriver {
  state = "CLOSED" as "OPEN" | "CONNECTING" | "CLOSED";
  readonly bus = mitt<Events>();
  private ws?: WebSocket;
  private seq = 0;
  private retry = 0;
  private heartbeatTimer?: ReturnType<typeof setInterval>;
  private autoReconnect: AutoReconnectOptions | null;

  constructor(private opts: NetDriverOpts) {
    this.autoReconnect = normalizeOptions(this.opts.autoReconnect, { retries: 5, delay: 1000 });
  }

  /* ---------- 3. public API ---------- */
  open() {
    if (this.state !== "CLOSED") return;
    const url = typeof this.opts.url === "function" ? this.opts.url() : this.opts.url;
    this.ws = new WebSocket(url);
    this.ws.binaryType = "arraybuffer"; // use ArrayBuffer for binary messages
    this.state = "CONNECTING";

    this.ws.onopen = () => this.#handleOpen();
    this.ws.onclose = (ev) => this.#handleClose(ev);
    this.ws.onerror = (ev) => this.bus.emit("error", ev);
    this.ws.onmessage = (ev) => this.#handleRawMessage(ev.data);
  }

  close(code = 1000, reason = "client-close") {
    this.ws?.close(code, reason);
  }

  send<T extends Payload>(kind: string, payload: T) {
    if (this.state !== "OPEN") throw new Error("socket not open");
    const env: WebsocketEnvelope = {
      ts: Date.now(),
      payload,
    };
    logger.debug({ "netdriver.send": env.payload.kind, ts: env.ts, payload: env.payload });
    // this.ws!.send(JSON.stringify(env))
    this.ws!.send(encode(env) as ArrayBuffer); // use msgpack for binary messages
  }

  /* ---------- 4. Internals ---------- */
  #handleOpen() {
    this.state = "OPEN";
    this.retry = 0;
    this.bus.emit("open", this.ws!);
    console.log(`[NetDriver] WebSocket connected to ${this.ws!.url}`);
    // start heartbeat if server hasn’t dictated one yet
    // this.#startHeartbeat(1000); // default heartbeat interval
  }

  #handleClose(ev: CloseEvent) {
    this.state = "CLOSED";
    clearInterval(this.heartbeatTimer);
    this.bus.emit("close", ev);

    if (this.autoReconnect && (this.retry < this.autoReconnect.retries || this.autoReconnect.retries === Infinity)) {
      this.retry++;
      setTimeout(() => this.open(), this.autoReconnect.delay);
    }
  }

  #handleRawMessage(raw: ArrayBuffer) {
    const env: WebsocketEnvelope = decode(raw) as WebsocketEnvelope;
    logger.debug({ "netdriver.receive": env.payload.kind, ts: env.ts, payload: env.payload });

    if (env.payload.kind === "pong") {
      const pong = env.payload as EventPong;
      const rtt = Date.now() - pong.payload.client_ts;
      useAppConfig().setRTT(rtt);
    }

    this.bus.emit("message", env);
  }

  #startHeartbeat(ms: number) {
    clearInterval(this.heartbeatTimer);
    if (ms > 0) {
      this.heartbeatTimer = setInterval(
        () =>
          this.send<CommandPing>("ping", {
            kind: "ping",
            payload: {
              client_ts: Date.now(),
            },
          }),
        ms,
      );
    }
  }
}
