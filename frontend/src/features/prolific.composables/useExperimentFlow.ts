import { computed, markRaw, ref } from "vue";


const currentStepIndex = ref(0);

export function useExperimentFlow(flow: ReturnType<typeof defineExperimentFlow>) {
  const consented = ref(false); // local to experiment flow
  const steps = ref(
    flow.map((step) => ({
      ...step,
      component: markRaw(step.component),
      completed: false,
      props: step.props,
    })),
  );

  function markConsentGiven() {
    consented.value = true;
    gameService.consent();
    goNextStep();
  }

  const goNextStep = () => {
    const current = steps.value[currentStepIndex.value];
    current.completed = true;
    if (currentStepIndex.value < steps.value.length - 1) {
      currentStepIndex.value++;
    }
  };

  return {
    steps,
    currentStep: computed(() => steps.value[currentStepIndex.value]),
    currentStepIndex,
    goNextStep,
    percentageCompleted: computed(() => {
      return (steps.value.filter((s) => s.completed).length / steps.value.length) * 100;
    }),
  };
}

// export function useExperimentFlow() {
//   const steps = ref<ExperimentStep[]>([]);
//   const exp = useCurrentExperiment();
//   const currentStepIndex = ref(0);
//
//   async function goNextStep() {
//     if (currentStepIndex.value < steps.value.length - 1) {
//       steps.value[currentStepIndex.value].completed = true; // Mark current step as completed
//       currentStepIndex.value++;
//       steps.value[currentStepIndex.value].enteredAt = new Date(); // Record entry time for the next step
//       await exp.markNextStep(steps.value[currentStepIndex.value].label.toLowerCase())
//     } else {
//       console.warn("No more steps to go to.");
//     }
//   }
//
//   function goToStep(name: string) {
//     const stepIndex = steps.value.findIndex(step => step.label.toLowerCase() === name);
//     if (stepIndex !== -1) {
//       currentStepIndex.value = stepIndex;
//       steps.value[currentStepIndex.value].completed = false; // Mark current step as incomplete
//
//       // set all previous steps as completed
//       for (let i = 0; i < currentStepIndex.value; i++) {
//         steps.value[i].completed = true;
//       }
//     } else {
//       console.warn(`Step with label "${name}" not found.`);
//     }
//   }
//
//   function goPreviousStep() {
//     if (currentStepIndex.value > 0) {
//       steps.value[currentStepIndex.value].completed = false;
//       currentStepIndex.value -= 1;
//     } else {
//       console.warn("Already at the first step, cannot go back.");
//     }
//   }
//
//   on("prolific:trials_complete", () => {
//     // This event is triggered when all trials are completed
//     // You can handle any cleanup or finalization here if needed
//     goNextStep()
//   });
//
//
//   const percentageCompleted = computed(() => {
//     if (steps.value.length === 0) return 0;
//     const completedSteps = steps.value.filter(step => step.completed).length;
//     return (completedSteps / steps.value.length) * 100;
//   })
//
//   const context: ExperimentContext = {
//     participantId: null,
//     answers: {},
//     steps,
//     currentStepIndex,
//     goNextStep,
//     goPreviousStep,
//     percentageCompleted,
//   };
//
//   const addStep = (label: string, component: Component, props: any = {}) => {
//     steps.value.push({
//       id: `step-${steps.value.length}`,
//       label,
//       component: markRaw(component),
//       props: { ...props, context }, // Inject context
//       completed: false,
//     });
//   };
//
//   return {
//     ...context,
//     currentStep: computed(() => steps.value[currentStepIndex.value]),
//     addStep,
//     goToStep
//   };
// }
