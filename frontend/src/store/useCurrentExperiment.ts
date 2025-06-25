import { defineStore } from "pinia";
import { ref } from "vue";
import { markExperimentConsented, markAtStep } from "@/services/app.ts";


export const useCurrentExperiment = defineStore("mitlogic.currentExperiment", () => {
  const prolific_session_id = ref<string | null>(null);
  const experiment_id = ref<string | null>(null);
  const current_step = ref<string | null>(null);

  function setExperimentSession(prolific_session: string, step: string) {
    prolific_session_id.value = prolific_session;
    current_step.value = step;
  }

  async function markConsented(): Promise<boolean> {
    if (!prolific_session_id.value) {
      console.warn("No Prolific session ID provided");
      return false;
    }

    try {
      const res = await markExperimentConsented(prolific_session_id.value)
      console.log("markExperimentConsented response:", res);
      return true;
    } catch (error) {
      console.error("Error marking experiment consented:", error);
      return false;
    }
  }

  async function markNextStep(step: string): Promise<boolean> {
    try {
      const res = await markAtStep(prolific_session_id.value!, step)
      console.log("markAtNextStep response:", res);
      return true
    } catch (error) {
      console.log("Error marking at next step:", error)
      return false
    }
  }

  return {
    prolific_session_id,
    experiment_id,
    current_step,
    setExperimentSession,
    markConsented,
    markNextStep
  }

})
