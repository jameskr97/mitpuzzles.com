import { type EventModule, on } from "@/services/eventbus";
import type { Ref } from "vue";
import { ref } from "vue";
import logger from "@/services/logger.ts";

// 3. Composable-style module (returns reactive state object)
export const reactiveModule: EventModule<{
  count: Ref<number>;
  events: Ref<string[]>;
}> = {
  name: "reactive",
  setup() {
    logger.info("setting up reactive module");
    const count = ref(0);
    const events = ref<string[]>([]);

    const unsubscriber = on("*", (event) => {
      count.value++;
      events.value.push(event);
    });

    const clear = () => {
      count.value = 0;
      events.value = [];
    };

    // Return object with reactive state (T)
    return {
      count, // Ref<number>
      events, // Ref<string[]>
      clear, // () => void (but this is a method, not cleanup)
      _cleanup: unsubscriber, // () => void (this IS cleanup)
    };
  },
};
