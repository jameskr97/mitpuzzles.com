/**
 * centralized experiment data collection system
 * captures trial data, node navigation, and user interactions
 */
import { GraphExecutor, node_type } from "@/features/experiment-core";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("experiment:data-collection");
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";

export interface trial_data {
  trial_id: string;
  node_id: string;
  trial_index: number;
  stimulus: any; // the actual stimulus presented

  // timing
  start_time: number;
  end_time?: number;
  duration?: number;

  // outcomes
  response?: any; // user's response
  correct?: boolean;
  points_earned?: number;

  // additional metadata
  metadata?: Record<string, any>;
}

export interface node_data {
  node_id: string;
  node_type: string;
  start_time: number;
  end_time?: number;
  duration?: number;
  data?: any; // node-specific data
  completed: boolean;
}

export interface interaction_event {
  timestamp: number;
  event_type: string;
  node_id: string;
  trial_id?: string;
  sequence: number; // sequence number within the trial/session
  data: any;
}

export interface experiment_data {
  trials: trial_data[];
  nodes: node_data[];
  interactions: interaction_event[];
  experiment_id: string;
  start_time: number;
  end_time?: number;
  duration?: number;
}
export interface point_record {
  node_id: string;
  trial_index?: number;
  points: number;
  timestamp: number;
  source: string; // what generated the points
}

export interface dev_event_log {
  id: string;
  timestamp: number;
  event_type: string;
  details: string;
  data?: any;
}

/**
 * centralized data collection for experiment-core architecture
 */
export class ExperimentDataCollection {
  private trials: trial_data[] = [];
  private nodes: node_data[] = [];
  private interactions: interaction_event[] = [];

  private experiment_start_time: number;
  private experiment_end_time?: number; // if undefined, experiment is ongoing, else completed

  private point_records: point_record[] = []; // points tracking
  private trial_sequence_counters = new Map<string, number>(); // per-trial sequence tracking
  private participant_data: Record<string, any> = {}; // participant data
  private survey_responses = new Map<string, Record<string, any>>(); // survey responses stored separately to avoid duplication
  private dev_event_logs: dev_event_log[] = []; // dev event logging

  constructor(private executor: GraphExecutor) {
    this.experiment_start_time = Date.now();

    // capture participant data from URL parameters
    const url_params = new URLSearchParams(window.location.search);
    // get prolific parameters, if exist.
    const prolific_pid = url_params.get("PROLIFIC_PID");
    const study_id = url_params.get("STUDY_ID");
    const session_id = url_params.get("SESSION_ID");

    if (prolific_pid) {
      this.participant_data.prolific_pid = prolific_pid;
      this.participant_data.study_id = study_id;
      this.participant_data.session_id = session_id;
      this.participant_data.recruitment_platform = "prolific";
    } else {
      // not from prolific. currently, only ther trackable option is direct website visitor
      this.participant_data.recruitment_platform = "direct";
    }

    // capture additional URL params that might be useful
    this.participant_data.referrer = document.referrer;
    this.participant_data.user_agent = navigator.userAgent;

    this.participant_data.url_params = Object.fromEntries(url_params);
  }

  ///////////////////////////////////////////////////////////////
  // dev event logging for development overlay
  private log_dev_event(event_type: string, details: string, data?: any): void {
    const event: dev_event_log = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      event_type,
      details,
      data,
    };
    this.dev_event_logs.push(event);

    // cap at 100 events
    if (this.dev_event_logs.length > 100) this.dev_event_logs.shift();
  }

  get dev_events(): dev_event_log[] {
    return [...this.dev_event_logs];
  }

  ///////////////////////////////////////////////////////////////
  ///////////////////////////////////////////////////////////////
  // node recording fucntions, for all node types
  record_node_visit(node_id: string, node_type: string): void {
    // skip recording data_upload nodes - they're not part of the experiment
    if (node_type === "data_upload") return;

    // if upload has already completed, don't track additional node visits
    if (this.experiment_end_time) {
      log("skipping node visit tracking for %s - upload already completed", node_id);
      return;
    }

    const node: node_data = {
      node_id,
      node_type,
      start_time: Date.now(),
      completed: false,
    };

    this.nodes.push(node);
    this.log_dev_event("node_visit", `entered ${node_type} node: ${node_id}`, { node_id, node_type });
  }

  ///////////////////////////////
  // trial data recording
  record_trial_start(trial_index: number, stimulus: PuzzleDefinition[]): void {
    const node_id = this.executor.current_node!.id;
    const trial: trial_data = {
      trial_id: this.executor.current_trial_id!,
      node_id,
      trial_index,
      stimulus,
      start_time: Date.now(),
    };

    this.trial_sequence_counters.set(node_id, 0); // init trial sequence counter
    this.trials.push(trial);
    this.log_dev_event("trial_start", `trial ${trial_index} started in node: ${node_id}`, {
      trial_id: trial.trial_id,
      trial_index,
      node_id,
    });
  }

  record_trial_end(response: any, _correct?: boolean, points?: number, metadata?: Record<string, any>): void {
    const trial = this.trials.find((t) => t.trial_id === this.executor.current_trial_id);
    if (!trial) {
      console.warn(`tried to end trial ${this.executor.current_trial_id} but no start record found`);
      return;
    }

    const end_time = Date.now();
    trial.end_time = end_time;
    trial.duration = end_time - trial.start_time;
    trial.response = response;
    trial.points_earned = points;
    trial.metadata = metadata;
  }

  record_interaction(event_type: string, node_id: string, data: any, trial_id?: string): void {
    let sequence = 0;
    if (trial_id) {
      const current_sequence = this.trial_sequence_counters.get(trial_id) || 0;
      sequence = current_sequence;
      this.trial_sequence_counters.set(trial_id, current_sequence + 1);
    }

    const interaction: interaction_event = {
      timestamp: Date.now(),
      event_type,
      node_id,
      trial_id,
      sequence,
      data,
    };

    this.interactions.push(interaction);
    this.log_dev_event("interaction", `${event_type} recorded`, {
      cell: data.cell,
      event_type,
      node_id,
      trial_id,
      sequence,
    });
  }

  ///////////////////////////////
  // survey data recording
  record_survey_responses(node_id: string, responses: Record<string, any>): void {
    const node = this.nodes.find((n) => n.node_id === node_id && !n.completed);
    if (!node) {
      console.warn(`tried to record survey responses for node ${node_id} but no active visit record found`);
      return;
    }

    // store survey responses separately to avoid duplication in export
    this.survey_responses.set(node_id, responses);
  }

  record_node_completion(node_id: string): void {
    // if upload has already completed, don't track additional node completions
    if (this.experiment_end_time) {
      log("skipping node completion tracking for %s - experiment already completed", node_id);
      return;
    }

    const node = this.nodes.find((n) => n.node_id === node_id && !n.completed);
    if (!node) {
      console.warn(`tried to complete node ${node_id} but no active visit record found`);
      return;
    }

    const end_time = Date.now();
    node.end_time = end_time;
    node.duration = end_time - node.start_time;
    node.completed = true;
  }

  // experiment lifecycle
  mark_experiment_complete(): void {
    this.experiment_end_time = Date.now();
  }

  ///////////////////////////////////////////////////////////////
  /// points management
  get total_points(): number {
    return this.point_records.reduce((total, record) => total + record.points, 0);
  }

  add_points(points: number, source: string, trial_index?: number): void {
    this.point_records.push({
      node_id: this.executor.current_node?.id!,
      trial_index,
      points,
      timestamp: Date.now(),
      source,
    });
  }

  ///////////////////////////////////////////////////////////////
  // getters
  get trial_data(): trial_data[] {
    return [...this.trials];
  }

  export_for_analysis(): any {
    const data = {
      trials: [...this.trials],
      nodes: [...this.nodes],
      interactions: [...this.interactions],
      experiment_id: this.executor.graph.graph_data.id,
      start_time: this.experiment_start_time,
      end_time: this.experiment_end_time,
      duration: this.experiment_end_time ? this.experiment_end_time - this.experiment_start_time : undefined,
    };
    log("Exporting experiment data for analysis: %O", data);

    // OK DATA COLLECTION. We want to build a final stat structure that looks like the following:
    // It's not the best for analysis, but it's the best to see and ensure that everything is captured.
    // type exported_structure = {
    //   experiment: {
    //     identifier: "the experiment id";
    //     timestamp_start: number;
    //     timestamp_complete: number;
    //   };
    //   participant: {
    //     recruitment_platform: "prolific" | "direct"; // direct == someone who took it directly from our website,
    //     prolific_participand_id?: string;
    //     prolific_study_id?: string;
    //     prolific_session_id?: string;
    //     // no parans needed for "direct" - server side will be able to identify the user
    //   };
    //   nodes: [
    //     {
    //       node_id: string;
    //       node_type: "consent" | "instructions" | "trial" | "survey" | "prolific_redirect";
    //       timestamp_enter: number;
    //       timestamp_exit: number;
    //       survey_responses?: Record<string, any>; // only for survey nodes
    //       trials: [
    //         // only for trial nodes
    //         {
    //           timestamp_start: number;
    //           timestamp_end: number;
    //           points_earned?: number;
    //           stimuli: Array<{}>; // stimulus (PuzzleDefinition) presented (same list that user received)
    //           actions: Array<{}>; // interactions recorded during this trial
    //           meta: Record<string, string>; // trial metadata
    //         },
    //       ];
    //     },
    //   ];
    // };

    // group interactions by trial_id for nesting
    const interactions_by_trial = new Map<string, interaction_event[]>();
    data.interactions.forEach((interaction) => {
      if (!interaction.trial_id) return; // skip interactions not tied to a trial

      if (!interactions_by_trial.has(interaction.trial_id)) interactions_by_trial.set(interaction.trial_id, []);
      interactions_by_trial.get(interaction.trial_id)!.push(interaction);
    });

    // group trials by node_id for nesting
    const trials_by_node = new Map<string, trial_data[]>();
    data.trials.forEach((trial) => {
      if (!trials_by_node.has(trial.node_id)) trials_by_node.set(trial.node_id, []);
      trials_by_node.get(trial.node_id)!.push(trial);
    });

    const formatted_nodes = data.nodes.map((node) => {
      const node_trials = trials_by_node.get(node.node_id) || [];

      // format trials for this node
      const formatted_trials = node_trials.map((trial) => {
        const trial_interactions = interactions_by_trial.get(trial.trial_id) || [];

        return {
          timestamp_start: trial.start_time,
          timestamp_end: trial.end_time,
          points_earned: trial.points_earned,
          stimuli: trial.stimulus,
          actions: trial_interactions.map((interaction) => ({
            sequence: interaction.sequence,
            timestamp: interaction.timestamp,
            event_type: interaction.event_type,
            data: interaction.data,
          })),
          meta: {
            trial_id: trial.trial_id,
            trial_index: trial.trial_index,
            duration: trial.duration,
            correct: trial.correct,
            ...trial.metadata,
          },
        };
      });

      // build node structure
      const formatted_node: any = {
        node_id: node.node_id,
        node_type: node.node_type,
        timestamp_enter: node.start_time,
        timestamp_exit: node.end_time,
      };

      // add trials if this is a trial node
      if (node.node_type === node_type.TRIAL && formatted_trials.length > 0) formatted_node.trials = formatted_trials;

      // add survey responses if this is a survey node
      if (node.node_type === node_type.SURVEY && this.survey_responses.has(node.node_id))
        formatted_node.survey_responses = this.survey_responses.get(node.node_id);

      return formatted_node;
    });

    return {
      experiment: {
        identifier: data.experiment_id,
        timestamp_start: data.start_time,
        timestamp_end: data.end_time,
      },
      participant: this.participant_data,
      nodes: formatted_nodes,
    };
  }
}
