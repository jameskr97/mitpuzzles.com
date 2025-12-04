import type { experiment_definition, graph_node } from "./types";
import { ExperimentGraph } from "@/features/experiment-core";
import { StimuliLoader } from "@/features/experiment-core/stimuli/StimuliLoader";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore";
import { ExperimentDataCollection } from "@/features/experiment-core/data/ExperimentDataCollection.ts";

/** simple execution state* */
export interface execution_state {
  current_node_id: string;
  completed_nodes: string[];
  is_running: boolean;
  start_time: number;
}

/** global trial progress tracking */
export interface trial_progress {
  current: number;
  total: number;
  percentage: number;
}

/** simple graph executor for linear experiments */
export class GraphExecutor {
  // experiment state
  readonly graph: ExperimentGraph;
  public data_collection: ExperimentDataCollection;
  private _state: execution_state;

  // trial tracking
  private node_trial_counts = new Map<string, number>();
  private node_trial_progress = new Map<string, number>();
  private global_trial_position = 0;
  private _total_trial_count = 0;
  private initialized = false;

  // trial state management
  private current_trial_indices = new Map<string, number>();
  private trial_results = new Map<string, any[]>();

  constructor(def: experiment_definition) {
    this.data_collection = new ExperimentDataCollection(this);
    this.graph = new ExperimentGraph(def);

    this._state = {
      current_node_id: this.graph.graph_data.entry_node,
      completed_nodes: [],
      is_running: false,
      start_time: 0,
    };
    this.global_trial_position = 0; // start at 0, increment when trial starts
  }

  /** initialize trial tracking by pre-calculating trial counts */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    for (const node of this.graph.get_nodes()) {
      if (node.type === "trial") {
        try {
          // this call is for tracking + caching, this should be called again when the stimuli is needed.
          const stimuli = await StimuliLoader.load_stimuli(node.config.meta.stimuli);
          this.node_trial_counts.set(node.id, stimuli.total_count);
          this.node_trial_progress.set(node.id, 0);
          this._total_trial_count += stimuli.total_count;
        } catch (error) {
          console.warn(`failed to load stimuli for node ${node.id}:`, error);
          this.node_trial_counts.set(node.id, 0);
          this.node_trial_progress.set(node.id, 0);
        }
      }
    }

    this.initialized = true;
  }

  ////////////////////////////////////////////////////////////////////
  // execution control
  async start(): Promise<void> {
    await this.initialize();
    this._state.is_running = true;
    this._state.start_time = performance.now();
    this._state.current_node_id = this.graph.graph_data.entry_node;
    this._state.completed_nodes = [];

    // clear puzzle history for this experiment
    const history_store = usePuzzleHistoryStore();
    await history_store.clear_events(this.graph.graph_data.id, "experiment");

    // record initial node visit
    const entry_node = this.current_node;
    if (!entry_node) throw new Error("Entry node not found in graph");
    this.data_collection.record_node_visit(entry_node.id, entry_node.type);
  }

  stop(): void {
    this._state.is_running = false;
  }

  reset() {
    this._state.current_node_id = this.graph.graph_data.entry_node;
    this._state.completed_nodes = [];
    this._state.is_running = false;
    this._state.start_time = 0;

    // reset trial tracking
    this.global_trial_position = 0; // start at 0, increment when trial starts
    this.node_trial_progress.clear();
    for (const node_id of this.node_trial_counts.keys()) {
      this.node_trial_progress.set(node_id, 0);
    }

    // reset trial state management
    this.current_trial_indices.clear();
    this.trial_results.clear();
  }

  ////////////////////////////////////////////////////////////////////
  // step control
  can_step(): boolean {
    return this._state.is_running && this.current_node !== null;
  }

  step(): boolean {
    if (!this.can_step()) return false;
    const current_node = this.current_node;
    if (!current_node) return false;

    // NOTE(james): kindof identical. first data completion, second for tranversal log.
    this.data_collection.record_node_completion(current_node.id); // record node completion in data collection
    this._state.completed_nodes.push(current_node.id); // mark current node as completed

    // get outgoing connections
    const next_nodes = this.graph.get_connected_nodes(current_node.id);
    if (next_nodes.length === 0) {
      // (no additional nodes? we're at the end)
      this._state.is_running = false;
      this.data_collection.mark_experiment_complete();
      return false;
    }

    // TODO(james): if we enter a world of complex experiments with non-linear graphs, we'll need
    //              to handle more complex logic here for choosing the next node.
    //              for now, we just go to the first connected node.
    this._state.current_node_id = next_nodes[0];

    const next_node = this.current_node;
    if (next_node) this.data_collection.record_node_visit(next_node.id, next_node.type);
    return true;
  }

  step_back(): boolean {
    if (!this.can_step()) return false;
    if (this._state.completed_nodes.length === 0) return false; // no previous node to go back to
    this._state.current_node_id = this._state.completed_nodes.pop()!; // force upwrap safe due to length check
    return true;
  }

  ////////////////////////////////////////////////////////////////////
  // getters
  get current_node(): graph_node | null {
    const node = this.graph.get_nodes().find((n: graph_node) => n.id === this._state.current_node_id);
    return node || null;
  }

  get total_trial_count(): number {
    return this._total_trial_count;
  }

  get state(): execution_state {
    return { ...this._state };
  }

  ////////////////////////////////////////////////////////////////////
  // trial management methods
  /** get current trial index for current trial node */
  get current_trial_index(): number {
    const current_node = this.current_node;
    if (!current_node || current_node.type !== "trial") return 0;
    return this.current_trial_indices.get(current_node.id) || 0;
  }

  /** get unique id for current trial */
  get current_trial_id(): string | null {
    const current_node = this.current_node;
    if (!current_node || current_node.type !== "trial") return null;
    return `${this.graph.graph_data.id}-${current_node.id}-trial-${this.current_trial_index}`;
  }

  /** get total trials for current node */
  get current_node_trial_count(): number {
    const current_node = this.current_node;
    if (!current_node || current_node.type !== "trial") return 0;
    return this.node_trial_counts.get(current_node.id) || 0;
  }

  /** advance to next trial or complete node if at end */
  next_trial(): boolean {
    const current_node = this.current_node;
    if (!current_node || current_node.type !== "trial") return false;

    const current_index = this.current_trial_index;
    const total_trials = this.current_node_trial_count;

    if (current_index >= total_trials - 1) {
      // all trials complete, move to next node
      this.step();
      return false;
    }

    // increment trial index
    this.current_trial_indices.set(current_node.id, current_index + 1);
    this.global_trial_position++;
    return true;
  }

  /** record trial result */
  record_trial_result(result: any): void {
    const current_node = this.current_node;
    if (!current_node || current_node.type !== "trial") return;

    const results = this.trial_results.get(current_node.id) || [];
    results.push({
      trial_index: this.current_trial_index,
      result,
      timestamp: Date.now(),
    });
    this.trial_results.set(current_node.id, results);
  }

  /** reset trial progress when entering a trial node */
  reset_trial_progress(node_id: string): void {
    this.current_trial_indices.set(node_id, 0);
    this.trial_results.set(node_id, []);
  }

  /** get global trial progress across all nodes */
  // NOTE(james): your IDE is wrong if it says this is unused. it is used.
  get global_progress(): trial_progress {
    if (this.total_trial_count === 0) return { current: 0, total: 0, percentage: 0 };

    return {
      current: this.global_trial_position,
      total: this.total_trial_count,
      percentage: (this.global_trial_position / this.total_trial_count) * 100,
    };
  }
}
