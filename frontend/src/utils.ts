import { defineAsyncComponent } from "vue";
import { defaultPuzzles } from "@/core/games/puzzle.defaults.ts";
import CryptoJS from "crypto-js";
import { createLogger } from "@/core/services/logger.ts";
import type { PuzzleVariant } from "@/core/types";
const log = createLogger("storage");
import { i18next } from "@/i18n.ts";
import _ from "lodash";

export function create_game_entry(icon: string, key: string): any {
  // Capitalize first letter for component name (e.g., "hashi" -> "Hashi")
  const component_name = key.charAt(0).toUpperCase() + key.slice(1);
  return {
    key,
    icon,
    name: i18next.t(`puzzle:${key}:title`),
    // Canvas component for home page preview
    component: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/${_.capitalize(key)}Canvas.vue`) }),
    // Freeplay component for routing
    freeplay: () => import(`@/features/games/${key}/${component_name}Freeplay.vue`),
    // Default puzzle state for home page preview
    default: defaultPuzzles[key],
    // Instructions components
    instructions: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/instructions.vue`) }),
    compact_instructions: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/InstructionsCompact.vue`) }),
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

/** Simplifies resetting all of localStorage and IndexedDB through a version variable. */
export class StorageVersionManager {
  // Change this to current date when updating the storage version
  private static readonly VERSION = "2026-03-28";
  private static readonly INDEXEDDB_NAME = "mitpuzzles";

  static async clearOldStorage() {
    const saved = localStorage.getItem("mitlogic.storageVersion");
    if (saved !== StorageVersionManager.VERSION) {
      // Clear localStorage items
      Object.keys(localStorage).forEach((key) => {
        if (key === "mitlogic.storageVersion") return;
        if (key.startsWith("mitlogic")) {
          localStorage.removeItem(key);
        }
      });

      // Clear IndexedDB
      await StorageVersionManager.clearIndexedDB();

      localStorage.setItem("mitlogic.storageVersion", StorageVersionManager.VERSION);
    }
  }

  private static clearIndexedDB(): Promise<void> {
    return new Promise((resolve) => {
      const request = indexedDB.deleteDatabase(StorageVersionManager.INDEXEDDB_NAME);
      request.onsuccess = () => {
        log("IndexedDB cleared successfully");
        resolve();
      };
      request.onerror = () => {
        console.warn("[StorageVersionManager] Failed to clear IndexedDB");
        resolve(); // Resolve anyway to not block the app
      };
      request.onblocked = () => {
        console.warn("[StorageVersionManager] IndexedDB deletion blocked");
        resolve(); // Resolve anyway to not block the app
      };
    });
  }
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

export function getPuzzleDisplayName(variant?: PuzzleVariant): string {
  if (!variant) return "undefined";
  if (!variant.difficulty) return variant.size;
  const difficulty = variant.difficulty.charAt(0).toUpperCase() + variant.difficulty.slice(1);
  return `${variant.size} ${difficulty}`;
}

export async function download_blob(url: string, filename: string) {
  try {
    const response = await fetch(url, { credentials: "include" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const content_type = response.headers.get("content-type") || "application/octet-stream";
    const blob = new Blob([await response.blob()], { type: content_type });
    const blob_url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blob_url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blob_url);
  } catch (err) {
    console.error(`error downloading file from ${url}:`, err);
  }
}


