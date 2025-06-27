/**
 * Centralised state + helpers for running an experiment end‑to‑end.
 *
 * The controller keeps track of:
 *  • the current *high‑level* step (consent → quiz → experiment → survey …)
 *  • the list of puzzle boards for the “experiment” phase
 *  • which trial the participant is currently on
 *
 * It listens for `event_experiment_state` coming over the websocket and
 * updates reactive state accordingly, so Vue components can react in real‑time.
 */
import { computed, ref, watch } from "vue";
import { ACTIVE_EXPERIMENTS } from "@/constants.ts";
import type { EventExperimentState } from "@/codegen/websocket/envelope.schema";
import type { MutablePuzzleState } from "@/services/states.ts";
import { useExperimentService } from "@/services/game/useExperimentService.ts";

/* ───────────────────────────────────────────────────────────────────── */
/*  Exported factory with simple caching                                */
/* ───────────────────────────────────────────────────────────────────── */
const cache = new Map<string, ReturnType<typeof makeExperimentController2>>();

export function useExperimentController(experimentKey: string) {
  if (!cache.has(experimentKey)) {
    cache.set(experimentKey, makeExperimentController2(experimentKey));
  }
  return cache.get(experimentKey)!;
}

/* ───────────────────────────────────────────────────────────────────── */
/*  Concrete implementation                                             */

/* ───────────────────────────────────────────────────────────────────── */
export function makeExperimentController2(key: string) {
  /* static + transport  */
  const def = ACTIVE_EXPERIMENTS[key];
  const ws = useExperimentService();

  /* high-level flow (consent → …) */
  const steps = def.flow;
  const currentStepIndex = ref(0);
  const currentStep = computed(() => steps[currentStepIndex.value]);
  const points = ref(0);

  /* trial bookkeeping */
  const experiment_state = ref<EventExperimentState | null>(null);
  const trialIdx = ref(0);
  const boardState = ref<MutablePuzzleState | null>(null);
  const is_experiment_complete = computed(() => experiment_state?.value?.completed);

  /* ------------------------------------------------------------------ */
  /* UI flags – these used to live in ExperimentGame.vue                */
  /* ------------------------------------------------------------------ */
  const trialRunning = ref(true); // “Finish Trial” vs “Next Trial”
  const boardInteractable = ref(true); // pointer-events
  const showErrorsScreen = ref(false); // transition overlay
  const canFinishTrial = ref(false); // gate Finish btn

  /* helper getters */
  const curBoard = computed(() => experiment_state.value?.boards.find((b) => b.order === trialIdx.value));
  const curId = computed(() => curBoard.value?.session_id);
  const isCurrentFinished = computed(() => curBoard.value?.is_finished ?? false);

  /* ------------------------------------------------------------------ */
  /* websocket listener                                                 */
  /* ------------------------------------------------------------------ */
  ws.bus.on("experiment_state", async (s: EventExperimentState) => {
    experiment_state.value = s;
    points.value = s.total_points;
    /* sync step if backend jumped forward (quiz→experiment etc.) */
    currentStepIndex.value = steps.findIndex((p) => p.id === s.current_step);
    trialIdx.value = s.current_trial
  });

  /**
   * When the current board is already finished (e.g. user solved it in a
   * previous session), flip the UI into “review” mode exactly once.
   * We watch ONLY the boolean `is_finished` so that server‑side cosmetic
   * updates to the board (which create a new object reference) don’t trigger a
   * loop. A local flag prevents running twice.
   */
  let reviewShown = false;
  watch(
    () => curBoard.value?.is_finished, // boolean | undefined
    (finished) => {
      if (!finished || reviewShown) return; // ignore until first true
      reviewShown = true; // lock

      trialRunning.value = false;
      boardInteractable.value = false;
      showErrorsScreen.value = true;
      canFinishTrial.value = false;

      ws.setTutorialEnabled(curId.value!, "sudoku", true); // highlight mistakes once
    },
    { immediate: true },
  );

  /* ------------------------------------------------------------------ */
  /* public actions                                                     */

  /* ------------------------------------------------------------------ */
  function loadTrial(order: number) {
    const board = experiment_state.value?.boards.find((b) => b.order === order);
    if (!board) {
      console.warn("Board with order", order, "not found");
      return;
    }
    trialIdx.value = order;
    trialRunning.value = true;
    boardInteractable.value = true;
    showErrorsScreen.value = false;
    canFinishTrial.value = false;
    // ws.resume("sudoku", board.session_id);
  }

  function updateCanFinish(state: MutablePuzzleState) {
    canFinishTrial.value = state.board.every((c) => c !== 0);
  }

  function finishTrial(earned: number) {
    console.log("Finishing trial of board", curId.value, "earned", earned);
    points.value += earned;
    trialRunning.value = false;
    boardInteractable.value = false;
    showErrorsScreen.value = true;
    ws.finishCurrentTrial(points.value);
    ws.setTutorialEnabled(curId.value!, "sudoku", true); // highlight mistakes
  }

  function nextTrial() {
    if (!experiment_state.value || trialIdx.value + 1 >= experiment_state.value.boards.length) {
      // out of boards → advance experiment step
      ws.setStep("survey");
      currentStepIndex.value = steps.findIndex((p) => p.id === "survey");
      return;
    }
    loadTrial(trialIdx.value + 1);
    ws.nextTrial(points.value);
    // loadTrial(trialIdx.value + 1);
  }

  function nextStep() {
    // advance to the next high‑level step (consent → quiz → experiment → survey …)
    if (currentStepIndex.value + 1 >= steps.length) return; // already at the last step
    currentStepIndex.value += 1;
    ws.setStep(steps[currentStepIndex.value].id);
  }

  return {
    /* read-only exposables */
    steps,
    currentStepIndex,
    points,
    boardState,
    curBoard,
    curId,
    is_experiment_complete,
    currentStep,
    experiment_state,

    /* UI flags */
    trialRunning,
    boardInteractable,
    showErrorsScreen,
    canFinishTrial,

    /* API for view / puzzle-layer */
    loadTrial,
    finishTrial,
    nextTrial,
    nextStep,
    updateCanFinish,
    consent: ws.consent,
  };
}

function makeExperimentController(experimentKey: string) {
  /** static definition ⇢ pulled from your constants table                     */
  const def = ACTIVE_EXPERIMENTS[experimentKey];
  if (!def) throw new Error(`Unknown experiment key: ${experimentKey}`);

  /** transport layer                                                          */
  const ws = useExperimentService();

  /** high‑level step flow (consent/quiz/experiment/survey …)                  */
  const steps = def.flow;
  const points = ref(0);
  const currentStepIndex = ref(0);

  /** backend experiment state payload */
  const experiment_state = ref<EventExperimentState | null>(null);

  /** trial‑level bookkeeping */
  const current_trial_index = ref(0);
  const current_trial_id = computed(() => experiment_state.value?.boards[current_trial_index.value]?.session_id);
  const current_board_state = ref<MutablePuzzleState | null>(null);
  const current_board = computed(() => experiment_state.value?.boards[current_trial_index.value]);

  /* ─────────────────────────────────────────────────────────────────── */
  /*  websocket listeners                                               */
  /* ─────────────────────────────────────────────────────────────────── */
  ws.bus.on("experiment_state", (state: EventExperimentState) => {
    const lastTrial = experiment_state.value?.current_trial;
    experiment_state.value = state;
    points.value = experiment_state.value.total_points;

    if (steps[currentStepIndex.value].id !== experiment_state.value.current_step)
      goToStepName(experiment_state.value.current_step);

    if(lastTrial !== state.current_trial)
      loadTrial(current_trial_index.value);
  });

  function loadTrial(index: number) {
    // go through experiment_state to get the board where order === index
    console.log("GETTING BOARD WHERE ORDER === ", index);
    const board = experiment_state.value?.boards.find((b) => b.order === index);
    console.log("THAR BOARD IS", board);
    ws.resume("sudoku", board.session_id);
    // ws.setTutorialEnabled(current_trial_id.value, "sudoku", false);
  }

  function finishTrial() {
    ws.setTutorialEnabled(current_trial_id.value, "sudoku", true);
  }

  function nextTrial() {
    if (current_trial_index.value + 1 >= experiment_state.value?.boards.length) return; // all done
    loadTrial(current_trial_index.value + 1);
  }

  // function nextTrial() {
  //   if (current_trial.value + 1 >= trial_boards.value.length) {
  //     goNextStep();
  //     return;
  //   }
  //   loadTrial(current_trial.value + 1);
  // }

  /* ─────────────────────────────────────────────────────────────────── */
  /*  navigation helpers                                                */

  /* ─────────────────────────────────────────────────────────────────── */
  function goToStepName(name: string) {
    const idx = steps.findIndex((s) => s.id === name);
    if (idx === -1) {
      console.warn(`Step "${name}" not found in experiment flow`);
      return;
    }
    currentStepIndex.value = idx;
    // ws.setStep(name);
  }

  function goNextStep() {
    if (currentStepIndex.value + 1 >= steps.length) {
      console.warn("Already at last step; cannot advance further");
      return;
    }
    currentStepIndex.value += 1;
    ws.setStep(steps[currentStepIndex.value].id);
  }

  /* ─────────────────────────────────────────────────────────────────── */
  /*  public API                                                         */
  /* ─────────────────────────────────────────────────────────────────── */
  return {
    /** id **/
    key: experimentKey,

    /** high‑level step control **/
    steps,
    num_steps: steps.length,
    currentStepIndex,
    currentStep: computed(() => steps[currentStepIndex.value]),
    goToStepName,
    goNextStep,

    /** experiment‑state & trials **/
    experiment_state,
    current_trial: current_trial_index,
    current_trial_id,
    current_board,
    loadTrial,
    points,
    nextTrial: () => ws.nextTrial(points.value),
    finishTrial: () => ws.finishCurrentTrial(points.value),
    isCurrentCompleted: computed(() => current_board.value?.is_finished ?? false),
    current_board_state,
    /** misc **/
    consent: ws.consent,
    setTutorialEnabled: (ptype: string, enabled: boolean) =>
      ws.setTutorialEnabled(current_trial_id.value, ptype, enabled),
  };
}
