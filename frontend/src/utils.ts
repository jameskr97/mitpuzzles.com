import { format_game_stopwatch } from "@/services/util.ts";
import { computed, type ComputedRef, defineAsyncComponent, ref, type Ref } from "vue";
import logger from "@/services/logger.ts";
import { useLocalStorage } from "@vueuse/core";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
import type { RuleViolation } from "@/services/game/engines/PuzzleEngine.ts";

export function create_game_entry(
  icon: string,
  sidebar_title: string,
  key: string,
  defaultBehaviors: Array<any> = [],
): any {
  return {
    key,
    icon,
    name: sidebar_title,
    component: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/${key}.puzzle.vue`) }),
    instructions: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/instructions.vue`) }),
    default: defaultPuzzles[key],
    defaultBehaviors,
  };
}

export function create_dev_tool(
  key: string,
  icon: string,
  display_name: string,
  meta: object = {},
  requires_admin: boolean = false,
) {
  return {
    key,
    icon,
    name: display_name,
    component: import(`@/views/dev/${key}.vue`),
    requires_admin,
    meta,
  };
}

export function create_experiment(key: string, flow: any) {
  return {
    key,
    component: defineAsyncComponent({
      loader: () => import(`@/features/prolific.experiments/${key}/ExperimentMain.vue`),
    }),
    flow,
  };
}

/** Simplifies resetting all of localStorage through a version variable. */
export class StorageVersionManager {
  // Change this to current date when updating the storage version
  private static readonly VERSION = "2025-06-30";

  static clearOldStorage() {
    const saved = localStorage.getItem("mitlogic.storageVersion");
    if (saved !== StorageVersionManager.VERSION) {
      Object.keys(localStorage).forEach((key) => {
        if (key === "mitlogic.storageVersion") return;
        if (key.startsWith("mitlogic")) {
          localStorage.removeItem(key);
        }
      });
      localStorage.setItem("mitlogic.storageVersion", StorageVersionManager.VERSION);
    }
  }
}

export class PuzzleTimer {
  private timer_id: number | null = null;
  private start_time: number | null = null;

  public elapsed_ms: Ref<number> = ref(0);
  public time_completed: Ref<boolean> = ref(false);
  public display_time: ComputedRef<string> = computed(() => format_game_stopwatch(this.elapsed_ms.value));

  constructor(private puzzle_name: string) {
    this.elapsed_ms = useLocalStorage<number>(`mitlogic.puzzles:${puzzle_name}:time_elapsed`, 0);
    this.time_completed = useLocalStorage<boolean>(`mitlogic.puzzles:${puzzle_name}:time_completed`, false);
  }

  public reset() {
    this.stop();
    this.elapsed_ms.value = 0;
    this.time_completed.value = false;
  }

  public start() {
    if (this.timer_id != null || this.time_completed.value) return;
    logger.debug(`${this.puzzle_name} timer started`);

    this.start_time = performance.now() - this.elapsed_ms.value;
    const tick = () => {
      this.elapsed_ms.value = performance.now() - this.start_time!;
      this.timer_id = requestAnimationFrame(tick);
    };
    this.timer_id = requestAnimationFrame(tick);
  }

  public stop() {
    if (this.timer_id == null) return;
    logger.debug(`${this.puzzle_name} timer stopped`);
    cancelAnimationFrame(this.timer_id);
    this.timer_id = null;
  }

  public get_duration_ms() {
    return this.elapsed_ms.value;
  }

  public complete() {
    logger.debug("Timer marked complete");
    this.stop();
    this.time_completed.value = true;
  }
}

/**
 * Checks if a specific violation rule applies to a given cell in the puzzle.
 * @param violations
 * @param row
 * @param col
 * @param rule
 */
export function check_violation_rule(violations: RuleViolation[], row: number, col: number, rule: string | string[]) {
  if (!violations || !Array.isArray(violations)) return false;
  if (violations.length === 0) return false;
  if (typeof rule === "string") rule = [rule];

  return violations.some(
    (violation) =>
      rule.includes(violation.rule_name) && violation.locations.some((loc) => loc.row === row && loc.col === col),
  );
}

export function shuffle(array: any[]) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

export function detectModeFromPath(): "freeplay" | "prolific" {
  const IS_TEST_EXPERIMENT = /^\/devtool\/test-experiment/.test(location.pathname);
  const IS_REAL_EXPERIMENT = /^\/experiment\//.test(location.pathname);
  return IS_TEST_EXPERIMENT || IS_REAL_EXPERIMENT ? "prolific" : "freeplay";
}

export function getPuzzleDisplayName(parts?: string[]): string {
  if (!parts) return "undefined";
  if (parts.length < 2) return parts[0];
  const name = parts
    .slice(1)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
  return `${parts[0]} ${name}`;
}

export type MaybeOptions<T> = boolean | Partial<T>;

export function normalizeOptions<T extends object>(value: boolean | Partial<T> | undefined, defaults: T): T | null {
  if (value === true) return defaults;
  if (typeof value === "object") return { ...defaults, ...value };
  return null;
}
