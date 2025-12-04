import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import type { processed_stimuli, raw_stimuli, stimuli_config, stimuli_format } from "./types";
import { shuffle } from "@/utils";

/** loader for different stimuli formats - loads all stimuli files at build time */
export class StimuliLoader {
  // load all stimuli files from experiment definitions at build time
  private static stimuli_files: Record<string, any> = import.meta.glob(["../../experiment-definitions/*/*.json"], {
    eager: true,
  });

  private static stimuli_cache = new Map<string, processed_stimuli>();

  /** load and process stimuli based on config */
  static async load_stimuli(config: stimuli_config): Promise<processed_stimuli> {
    const cache_key =
      typeof config.source === "string"
        ? `${config.source}:${config.presentation_mode}:${config.trial_count}:${config.selection_strategy}`
        : `callback:${config.presentation_mode}:${config.trial_count}:${config.selection_strategy}`;

    if (this.stimuli_cache.has(cache_key)) {
      return this.stimuli_cache.get(cache_key)!;
    }

    try {
      let raw_data: raw_stimuli;

      if (typeof config.source === "function") {
        // handle callback source
        raw_data = await config.source();
      } else {
        // handle file path source
        const stimuli_module = this.stimuli_files[config.source];
        if (!stimuli_module?.default) throw new Error(`stimuli file '${config.source}' not found`);
        raw_data = stimuli_module.default;
      }

      const processed = this.process_stimuli(raw_data, config);

      // cache and return
      this.stimuli_cache.set(cache_key, processed);
      return processed;
    } catch (error) {
      console.error(`failed to load stimuli from source`, error);
      throw new Error(`stimuli source not found or invalid: ${error}`);
    }
  }

  /** detect format and process raw stimuli */
  private static process_stimuli(raw_data: raw_stimuli, config: stimuli_config): processed_stimuli {
    const format = this.detect_format(raw_data);

    // normalize to pairs format
    let pairs: PuzzleDefinition[][];
    if (format === "sequential_list") {
      pairs = (raw_data as PuzzleDefinition[]).map((item) => [item]); // convert single items to pairs of [item]
    } else {
      pairs = raw_data as PuzzleDefinition[][]; // already in pairs format
    }

    const selected_pairs = this.apply_selection(pairs, config);  // apply selection strategy (choose subset)
    const final_pairs = this.apply_presentation_mode(selected_pairs, config); // apply presentation mode (reorder the selected pairs)

    return {
      format,
      items: final_pairs,
      total_count: final_pairs.length,
    };
  }

  /** detect stimuli format based on structure */
  private static detect_format(raw_data: raw_stimuli): stimuli_format {
    if (!Array.isArray(raw_data) || raw_data.length === 0) throw new Error("stimuli data must be a non-empty array");

    const first_item = raw_data[0];
    if (Array.isArray(first_item)) return "paired_list"; // array? assume paired
    if (this.is_puzzle_definition(first_item)) return "sequential_list"; // object? assume puzzle definition

    throw new Error("unable to detect stimuli format - expected PuzzleDefinition or PuzzleDefinition[]");
  }

  /** check if object looks like a PuzzleDefinition */
  private static is_puzzle_definition(obj: any): obj is PuzzleDefinition {
    return (
      obj &&
      typeof obj.id !== "undefined" &&
      typeof obj.puzzle_type === "string" &&
      typeof obj.rows === "number" &&
      typeof obj.cols === "number" &&
      Array.isArray(obj.initial_state) &&
      Array.isArray(obj.solution)
    );
  }

  /** apply selection strategy to choose subset of stimuli */
  private static apply_selection(pairs: PuzzleDefinition[][], config: stimuli_config): PuzzleDefinition[][] {
    const trial_count = config.trial_count || pairs.length;
    if (trial_count >= pairs.length) return pairs; // use all available

    switch (config.selection_strategy) {
      case "random":
        return shuffle([...pairs]).slice(0, trial_count);
      case "first_n":
        return pairs.slice(0, trial_count);
      case "balanced":
        // implement balanced selection if needed
        return shuffle([...pairs]).slice(0, trial_count);
      default:
        throw new Error(`unknown selection strategy: ${config.selection_strategy}`);
    }
  }

  /** apply presentation mode to reorder selected stimuli */
  private static apply_presentation_mode(pairs: PuzzleDefinition[][], config: stimuli_config): PuzzleDefinition[][] {
    switch (config.presentation_mode) {
      case "random":
        return shuffle([...pairs]); // shuffle the order of pairs
      case "sequential":
        return pairs; // keep original order
      case "paired":
        return pairs; // keep original order (pairs are already pairs)
      default:
        throw new Error(`unknown presentation mode: ${config.presentation_mode}`);
    }
  }
}
