/**
 * useHashiGame - Core game logic for Hashi (Bridges)
 *
 * Unlike cell-based games, Hashi stores state as a list of bridges between islands.
 * Islands are numbered cells in the initial_state grid.
 */
import { ref, computed, type ComputedRef, type Ref } from "vue";
import type { PuzzleDefinition, HashiMeta, HashiBridge } from "@/core/games/types/puzzle-types.ts";

export interface HashiGameReturn {
  /** Current bridges */
  bridges: Ref<HashiBridge[]>;

  /** Island positions and their required counts */
  islands: ComputedRef<Map<string, number>>;

  /** Current bridge count per island */
  island_bridge_counts: ComputedRef<Map<string, number>>;

  /** Grid dimensions */
  rows: number;
  cols: number;

  /** Toggle a bridge between two islands */
  toggle_bridge: (
    island1: [number, number],
    island2: [number, number],
    button: number
  ) => { old_count: number; new_count: number } | null;

  /** Check if adding a bridge would cross an existing one */
  would_cross_bridge: (
    island1: [number, number],
    island2: [number, number]
  ) => boolean;

  /** Find the nearest island in a direction from a given position */
  find_island_in_direction: (
    row: number,
    col: number,
    dr: number,
    dc: number
  ) => [number, number] | null;

  /** Check if position is an island */
  is_island: (row: number, col: number) => boolean;

  /** Check solution */
  check_solution: () => Promise<boolean>;

  /** Clear all bridges */
  clear: () => void;

  /** Get bridge between two islands (if any) */
  get_bridge: (
    island1: [number, number],
    island2: [number, number]
  ) => HashiBridge | null;

  /** Puzzle definition */
  definition: PuzzleDefinition<HashiMeta>;
}

/**
 * Check if two positions are the same
 */
function same_position(a: [number, number], b: [number, number]): boolean {
  return a[0] === b[0] && a[1] === b[1];
}

/**
 * Create Hashi game logic
 */
export function useHashiGame(
  definition: PuzzleDefinition<HashiMeta>,
  saved_bridges?: HashiBridge[] | null
): HashiGameReturn {
  const rows = definition.rows;
  const cols = definition.cols;
  const initial_state = definition.initial_state;

  // Bridge state
  const bridges = ref<HashiBridge[]>(saved_bridges ? [...saved_bridges] : []);

  // Pre-compute island positions from initial_state
  // Islands are cells with values > 0 (the value is the required bridge count)
  const islands = computed(() => {
    const map = new Map<string, number>();
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const value = initial_state[row]?.[col];
        if (value && value > 0) {
          map.set(`${row},${col}`, value);
        }
      }
    }
    return map;
  });

  // Compute current bridge count per island
  const island_bridge_counts = computed(() => {
    const counts = new Map<string, number>();
    for (const bridge of bridges.value) {
      const key1 = `${bridge.island1[0]},${bridge.island1[1]}`;
      const key2 = `${bridge.island2[0]},${bridge.island2[1]}`;
      counts.set(key1, (counts.get(key1) || 0) + bridge.count);
      counts.set(key2, (counts.get(key2) || 0) + bridge.count);
    }
    return counts;
  });

  /**
   * Check if a position is an island
   */
  function is_island(row: number, col: number): boolean {
    return islands.value.has(`${row},${col}`);
  }

  /**
   * Find the nearest island in a direction
   */
  function find_island_in_direction(
    row: number,
    col: number,
    dr: number,
    dc: number
  ): [number, number] | null {
    let r = row + dr;
    let c = col + dc;
    while (r >= 0 && r < rows && c >= 0 && c < cols) {
      if (is_island(r, c)) {
        return [r, c];
      }
      r += dr;
      c += dc;
    }
    return null;
  }

  /**
   * Get existing bridge between two islands
   */
  function get_bridge(
    island1: [number, number],
    island2: [number, number]
  ): HashiBridge | null {
    return bridges.value.find(
      (b) =>
        (same_position(b.island1, island1) && same_position(b.island2, island2)) ||
        (same_position(b.island1, island2) && same_position(b.island2, island1))
    ) || null;
  }

  /**
   * Check if a new bridge would cross an existing one
   */
  function would_cross_bridge(
    island1: [number, number],
    island2: [number, number]
  ): boolean {
    const [r1, c1] = island1;
    const [r2, c2] = island2;
    const is_horizontal = r1 === r2;

    for (const bridge of bridges.value) {
      const [br1, bc1] = bridge.island1;
      const [br2, bc2] = bridge.island2;
      const bridge_horizontal = br1 === br2;

      // Only check perpendicular bridges
      if (is_horizontal === bridge_horizontal) continue;

      if (is_horizontal) {
        // Our bridge is horizontal, check if vertical bridge crosses it
        const our_row = r1;
        const our_col_min = Math.min(c1, c2);
        const our_col_max = Math.max(c1, c2);
        const their_col = bc1; // Vertical bridge has same col
        const their_row_min = Math.min(br1, br2);
        const their_row_max = Math.max(br1, br2);

        // Check if they cross (strictly inside, not at endpoints)
        if (
          their_col > our_col_min &&
          their_col < our_col_max &&
          our_row > their_row_min &&
          our_row < their_row_max
        ) {
          return true;
        }
      } else {
        // Our bridge is vertical, check if horizontal bridge crosses it
        const our_col = c1;
        const our_row_min = Math.min(r1, r2);
        const our_row_max = Math.max(r1, r2);
        const their_row = br1; // Horizontal bridge has same row
        const their_col_min = Math.min(bc1, bc2);
        const their_col_max = Math.max(bc1, bc2);

        if (
          our_col > their_col_min &&
          our_col < their_col_max &&
          their_row > our_row_min &&
          their_row < our_row_max
        ) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Toggle a bridge between two islands
   * Left click (button 0): cycle 0 → 1 → 2 → 0
   * Right click (button 2): cycle 0 → 2 → 1 → 0 (or just decrement)
   */
  function toggle_bridge(
    island1: [number, number],
    island2: [number, number],
    button: number
  ): { old_count: number; new_count: number } | null {
    // Validate both positions are islands
    if (!is_island(island1[0], island1[1]) || !is_island(island2[0], island2[1])) {
      return null;
    }

    // Must be orthogonally aligned
    if (island1[0] !== island2[0] && island1[1] !== island2[1]) {
      return null;
    }

    const existing = get_bridge(island1, island2);
    const old_count = existing?.count || 0;

    // Calculate new count based on button
    let new_count: number;
    if (button === 2) {
      // Right click: decrement (2 → 1 → 0, or 0 → 2 if we want reverse cycle)
      new_count = old_count === 0 ? 2 : old_count - 1;
    } else {
      // Left click: increment and wrap
      new_count = (old_count + 1) % 3;
    }

    // Check if adding a new bridge would cross existing ones
    if (new_count > 0 && old_count === 0 && would_cross_bridge(island1, island2)) {
      return null;
    }

    // Update bridges array
    if (new_count === 0 && existing) {
      // Remove bridge
      const index = bridges.value.indexOf(existing);
      if (index >= 0) {
        bridges.value.splice(index, 1);
      }
    } else if (new_count > 0) {
      if (existing) {
        existing.count = new_count;
      } else {
        bridges.value.push({ island1, island2, count: new_count });
      }
    }

    // Trigger reactivity
    bridges.value = [...bridges.value];

    return { old_count, new_count };
  }

  /**
   * Clear all bridges
   */
  function clear(): void {
    bridges.value = [];
  }

  /**
   * Check if puzzle is solved
   * All islands must have exactly their required bridge count
   * All islands must be connected (form a single connected component)
   */
  async function check_solution(): Promise<boolean> {
    // Check all islands are satisfied
    for (const [key, required] of islands.value) {
      const actual = island_bridge_counts.value.get(key) || 0;
      if (actual !== required) {
        return false;
      }
    }

    // Check connectivity using BFS
    const island_keys = Array.from(islands.value.keys());
    if (island_keys.length === 0) return true;

    const visited = new Set<string>();
    const queue = [island_keys[0]];
    visited.add(island_keys[0]);

    while (queue.length > 0) {
      const current = queue.shift()!;
      const [row, col] = current.split(",").map(Number);

      // Find all connected islands via bridges
      for (const bridge of bridges.value) {
        let neighbor_key: string | null = null;

        if (bridge.island1[0] === row && bridge.island1[1] === col) {
          neighbor_key = `${bridge.island2[0]},${bridge.island2[1]}`;
        } else if (bridge.island2[0] === row && bridge.island2[1] === col) {
          neighbor_key = `${bridge.island1[0]},${bridge.island1[1]}`;
        }

        if (neighbor_key && !visited.has(neighbor_key)) {
          visited.add(neighbor_key);
          queue.push(neighbor_key);
        }
      }
    }

    // All islands should be visited
    return visited.size === island_keys.length;
  }

  return {
    bridges,
    islands,
    island_bridge_counts,
    rows,
    cols,
    toggle_bridge,
    would_cross_bridge,
    find_island_in_direction,
    is_island,
    check_solution,
    clear,
    get_bridge,
    definition,
  };
}
