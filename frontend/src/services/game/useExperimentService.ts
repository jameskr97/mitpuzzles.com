import { useGameService } from "@/services/game/useGameService";

export function useExperimentService() {
  const ws = useGameService();
  return {

    consent()               { ws.send({ kind: "experiment_consent" }); },
    setStep(step_name: string) {
      ws.send({ kind: "experiment_step", step_name })
    },

    nextTrial(current_points: number) { ws.send({ kind: "experiment_next_trial", points: current_points }); },
    finishCurrentTrial(current_points: number) { ws.send({ kind: "experiment_finish_trial", points: current_points }); },
    setTutorialEnabled: ws.setTutorialEnabled,
    send: ws.send,
    bus: ws.bus,
    resume: ws.resume,
    connected: ws.connected,
  };
}
