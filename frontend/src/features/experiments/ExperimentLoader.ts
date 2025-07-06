import type { ExperimentConfig } from "./core/types";
const experiment_modules = import.meta.glob("./definitions/*/experiment.config.ts", { eager: true });

interface ExperimentModule {
  default?: ExperimentConfig;
  [key: string]: any; // For named exports
}

const experimentRegistry: Record<string, ExperimentConfig> = {};

for (const path in experiment_modules) {
  const module = experiment_modules[path] as ExperimentModule;

  // match the path => ./definitions/<the thing we want to match>/experiment.config.ts
  // './definitions/sudoku-reasoning/experiment.config.ts' -> 'sudoku-reasoning'
  const match = path.match(/\.\/definitions\/([^\/]+)\/experiment\.config\.ts$/);
  if (!match) continue;

  const experimentId = match[1];
  let config: ExperimentConfig | null = null;

  if (module.default) {
    config = module.default;
  } else {
    // Look for any exported ExperimentConfig
    for (const exportName in module) {
      const exportValue = module[exportName];
      if (exportValue && typeof exportValue === "object" && exportValue.id && exportValue.steps) {
        config = exportValue as ExperimentConfig;
        break;
      }
    }
  }

  if (config) {
    // Ensure the config ID matches the directory name
    if (config.id !== experimentId) {
      console.warn(`Experiment ID mismatch: directory '${experimentId}' vs config ID '${config.id}'`);
    }

    experimentRegistry[experimentId] = config;
    console.log(`Loaded experiment: ${experimentId}`);
  } else {
    console.warn(`No valid experiment config found in ${path}`);
  }
}

/**
 * Get experiment configuration by directory name
 * @param experimentId - Directory name under definitions/
 */
export function getExperimentConfig(experiment_id: string): ExperimentConfig | null {
  return experimentRegistry[experiment_id] || null;
}

/**
 * Get all available experiments
 */
export function getAllExperiments(): Record<string, ExperimentConfig> {
  return { ...experimentRegistry };
}

/**
 * Get list of experiment IDs
 */
export function getExperimentIds(): string[] {
  return Object.keys(experimentRegistry);
}

/**
 * Validate experiment exists
 */
export function experimentExists(experimentId: string): boolean {
  return experimentId in experimentRegistry;
}

// Development helper - log all discovered experiments
if (process.env.NODE_ENV === "development") {
  console.log("Discovered experiments:", Object.keys(experimentRegistry));
}
