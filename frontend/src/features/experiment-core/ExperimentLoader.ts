import type { experiment_definition } from "@/features/experiment-core/graph/types";

// preload all experiments
import blind_sudoku_experiment from "@/features/experiment-definitions/blind-sudoku/experiment";
import forced_choice_experiment from "@/features/experiment-definitions/forced-choice/experiment";
import metacognition_experiment from "@/features/experiment-definitions/metacognition/experiment";

/** experiment loader for the new graph-based experiment system*/
export class ExperimentLoader {
  private static experiment_cache = new Map<string, experiment_definition>();

  // preloaded experiments registry
  private static experiments = new Map<string, experiment_definition>([
    ["blind-sudoku", blind_sudoku_experiment],
    ["forced-choice", forced_choice_experiment],
    ["metacognition", metacognition_experiment],
  ]);

  /** load experiment graph by name from experiment-definitions */
  static async load_experiment(experiment_name: string): Promise<experiment_definition> {
    if (this.experiment_cache.has(experiment_name)) return this.experiment_cache.get(experiment_name)!;

    const experiment = this.experiments.get(experiment_name);
    if (!experiment) {
      throw new Error(`Experiment "${experiment_name}" does not exist.`);
    }

    this.validate_experiment(experiment);
    this.experiment_cache.set(experiment_name, experiment);
    return experiment;
  }

  /** basic experiment validation */
  private static validate_experiment(experiment: experiment_definition): void {
    // ensure eseentials are true
    if (!experiment.id || !experiment.entry_node) throw new Error("experiment missing required fields: id, entry_node");
    if (!experiment.nodes || experiment.nodes.length === 0) throw new Error("experiment must have at least one node");

    // check entry node exists
    const entry_exists = experiment.nodes.some((n) => n.id === experiment.entry_node);
    if (!entry_exists) throw new Error(`entry_node '${experiment.entry_node}' not found in nodes`);
  }
}
