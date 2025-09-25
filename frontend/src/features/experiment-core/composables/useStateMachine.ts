import { computed, readonly, ref, type Ref } from "vue";

export interface StateTransition<TState extends string> {
  /** the state this transition is from, or null if it's the initial state */
  from: TState | null;
  /** the state this transition is to */
  to: TState;
  /** the timestamp when this transition occurred */
  timestamp: number;
}

export interface StateMachineConfig<TState extends string> {
  state_initial: TState;
  states: Record<
    TState,
    {
      /** callback for when entering this state */
      onEnter?: (data?: Record<string, any>) => void;
      /** callback for when exiting this state */
      onExit?: () => void | boolean; // can return false to prevent transition
      /** list of states we can get to from this state */
      canTransitionTo?: TState[];
      /** guard function to check if we can transition FROM this state to another */
      canTransition?: (to: TState) => boolean;
    }
  >;
  debug?: boolean;
}

interface StateMachineState<TState extends string> {
  current: TState;
  previous: TState | null;
  transitions: Array<StateTransition<TState>>;
  listeners: Array<(transition: StateTransition<TState>) => void>;
}

export function useStateMachine<TState extends string>(config: StateMachineConfig<TState>) {
  const m_state: Ref<StateMachineState<TState>> = ref({
    current: config.state_initial,
    previous: null,
    transitions: [],
    listeners: []
  }) as Ref<StateMachineState<TState>>;

  /** check if were allowed to transition to a state from the current state */
  function canTransition(from: TState, to: TState): boolean {
    const fromConfig = config.states[from];
    if (fromConfig?.canTransitionTo && !fromConfig.canTransitionTo.includes(to)) return false;
    if (fromConfig?.canTransition && !fromConfig.canTransition(to)) return false;
    return true;
  }

  function transitionTo(state_new: TState): boolean {
    const from = m_state.value.current as TState;

    // check if transition is allowed
    if (!canTransition(from, state_new)) {
      if (config.debug) console.warn(`Cannot transition from ${from} to ${state_new}`);
      return false;
    }

    // call onExit for the current state
    const config_current = config.states[from];
    if (config_current?.onExit) {
      try {
        const result = config_current.onExit();
        if (result === false) {
          if (config.debug) console.log(`Transition ${from} → ${state_new} aborted by onExit`);
          return false;
        }
      } catch (error) {
        console.error(`Error in onExit for state ${from}:`, error);
      }
    }

    // update the state
    m_state.value.previous = from;
    m_state.value.current = state_new;

    // create transition record
    const transition: StateTransition<TState> = {
      from,
      to: state_new,
      timestamp: Date.now(),
    };
    m_state.value.transitions.push(transition);

    // call onEnter for the new state
    const config_new = config.states[state_new];
    if (config_new?.onEnter) config_new.onEnter();

    // notify listeners of the transition
    m_state.value.listeners.forEach((listener) => {
      try {
        listener(transition);
      } catch (error) {
        console.error("State transition listener error:", error);
      }
    });

    if (config.debug) console.log(`State Machine Transition ${from} → ${state_new}`);
    return true;
  }

  /** Add transition listener */
  function onTransition(listener: (transition: StateTransition<TState>) => void) {
    m_state.value.listeners.push(listener);
    return () => (m_state.value.listeners = m_state.value.listeners.filter((l) => l !== listener));
  }

  /** reset the state machine to initial state */
  function reset() {
    m_state.value.current = config.state_initial;
    m_state.value.previous = null;
    m_state.value.transitions = [];

    // Call onEnter for initial state
    const config_initial = config.states[config.state_initial];
    if (config_initial?.onEnter) {
      try {
        config_initial.onEnter();
      } catch (error) {
        console.error(`Error in onEnter during reset for state ${config.state_initial}:`, error);
      }
    }

    if (config.debug) console.log(`State Machine Reset to ${config.state_initial}`);
  }

  return {
    current_state: computed(() => m_state.value.current),
    previous_state: computed(() => m_state.value.previous),
    transition_history: computed(() => readonly(m_state.value.transitions)),

    transitionTo,
    onTransition,
    reset,
  };
}
