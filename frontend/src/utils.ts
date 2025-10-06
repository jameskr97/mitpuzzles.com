import { defineAsyncComponent } from "vue";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
import { PuzzleEngine, type RuleViolation } from "@/services/game/engines/PuzzleEngine.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { EngineSudoku } from "@/services/game/engines/games/sudoku.ts";
import { EngineKakurasu } from "@/services/game/engines/games/kakurasu.ts";
import { EngineTents } from "@/services/game/engines/games/tents.ts";
import { EngineLightup } from "@/services/game/engines/games/lightup.ts";
import { EngineMinesweeper } from "@/services/game/engines/games/minesweeper.ts";
import CryptoJS from "crypto-js";
import { EngineNonograms } from "@/services/game/engines/games/nonograms.ts";
import { EngineBattleships } from "@/services/game/engines/games/battleships.ts";
import axios from "axios";

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

export function create_admin_tool(
  key: string,
  icon: string,
  display_name: string,
) {
  return {
    key,
    icon,
    name: display_name,
    route_path: `/admin/${key}`,
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

export function getGravatarUrl(email: string, size = 80) {
  const hash = CryptoJS.MD5(email.toLowerCase().trim());
  return `https://www.gravatar.com/avatar/${hash}?s=${size}&d=identicon`;
}

export function getPuzzleDisplayName(parts?: string[]): string {
  if (!parts) return "undefined";
  if (parts.length < 2) return parts[0];
  if (parts[1] == null) return parts[0];
  const name = parts
    .slice(1)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
  return `${parts[0]} ${name}`;
}

export async function download_blob(url: string, filename: string) {
  try {
    const response = await axios.get(url, {
      responseType: 'blob'
    })

    // create download
    const blob = new Blob([response.data], { type: 'application/json' })
    const blob_url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blob_url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(blob_url)
  } catch (err) {
    console.error(`error downloading file from ${url}:`, err)
  }
}


export function createPuzzleEngine<T>(definition: PuzzleDefinition<T>, board?: number[][]): PuzzleEngine {
  switch (definition.puzzle_type) {
    case "sudoku":
      return new EngineSudoku(definition, board);
    case "kakurasu":
      return new EngineKakurasu(definition, board);
    case "nonograms":
      return new EngineNonograms(definition, board);
    case "battleships":
      return new EngineBattleships(definition, board);
    case "tents":
      return new EngineTents(definition, board);
    case "lightup":
      return new EngineLightup(definition, board);
    case "minesweeper":
      return new EngineMinesweeper(definition, board);
    default:
      return new PuzzleEngine(definition, board);
  }
}
