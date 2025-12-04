import pino from "pino";

export default pino({
  browser: { asObject: true },
  level: import.meta.env.PINO_LOG_LEVEL || "trace",
});
