import type { stimuli_config } from "@/features/experiment-core/stimuli/types.ts";

/** graph types used to construct the graph */
export interface experiment_definition {
  id: string;
  title: string;
  description: string;
  nodes: graph_node[];
  edges: graph_edge[];
  entry_node: string; // id of starting node
}

export interface graph_node {
  id: string;
  type: node_type;
  config: node_config;
}

export interface graph_edge {
  id: string;
  from_node: string;
  to_node: string;
}

export interface node_config<T = any> {
  // common config properties
  content?: string;
  component?: string;
  component_path?: string;

  // typed config specific to this node type
  meta: T;

  [key: string]: any;
}

// basic node types for experiments
export enum node_type {
  CONSENT = "consent",
  INSTRUCTIONS = "instructions",
  TRIAL = "trial",
  SURVEY = "survey",
  PROLIFIC_REDIRECT = "prolific_redirect",
  DATA_UPLOAD = "data_upload",
}

// typed meta interfaces for specific node types
export interface trial_meta {
  stimuli: stimuli_config;
  show_points?: boolean; // whether to show points earned during trial
  time_limit?: number;
  trial_type: string;
  trial_component?: string; // optional trial component to render inside TrialNode
}

export interface prolific_redirect_meta {
  completion_code: string;
}

// helper types for traversal
export type node_visitor = (node: graph_node) => void;
export type edge_visitor = (edge: graph_edge) => void;
