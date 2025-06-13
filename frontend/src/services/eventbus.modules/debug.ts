import { on } from "@/services/eventbus.ts";
import logger from "@/services/logger.ts";

export const debugModule = {
  name: "debug",
  setup() {
    return {
      _cleanup: on("*", (event, data) => {
        logger.info({ event, data });
      }),
    };
  },
};
