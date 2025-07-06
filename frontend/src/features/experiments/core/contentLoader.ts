// frontend/src/features/experiments/core/contentLoader.ts

import { ref } from "vue";

// Vite's import.meta.glob for loading content files
const contentFiles = import.meta.glob("../definitions/**/*.{md,json,txt}", {
  as: "raw",
  eager: false,
});

const jsonFiles = import.meta.glob("../definitions/**/*.json", {
  eager: false,
});

interface ContentCache {
  [path: string]: string;
}

// Simple cache to avoid re-loading the same files
const contentCache: ContentCache = {};

/**
 * Load markdown or text content from experiment definitions
 * @param experimentId - Directory name (e.g., 'simple-sudoku-study')
 * @param fileName - File name (e.g., 'consent.md', 'instructions.md')
 */
export async function loadExperimentContent(experimentId: string, fileName: string): Promise<string> {
  const fullPath = `../definitions/${experimentId}/${fileName}`;
  const cacheKey = fullPath;

  // Return cached content if available
  if (contentCache[cacheKey]) {
    return contentCache[cacheKey];
  }

  try {
    // Try to find the file in our glob patterns
    const moduleLoader = contentFiles[fullPath];

    if (!moduleLoader) {
      throw new Error(`Content file not found: ${fullPath}`);
    }

    // Load the content
    const content = (await moduleLoader()) as string;

    // Cache it
    contentCache[cacheKey] = content;

    return content;
  } catch (error) {
    console.error(`Failed to load content file: ${fullPath}`, error);
    throw error;
  }
}

/**
 * Load and parse JSON content from experiment definitions
 * @param experimentId - Directory name
 * @param fileName - JSON file name (e.g., 'survey.json')
 */
export async function loadExperimentJSON<T = any>(experimentId: string, fileName: string): Promise<T> {
  const fullPath = `../definitions/${experimentId}/${fileName}`;

  try {
    const moduleLoader = jsonFiles[fullPath];

    if (!moduleLoader) {
      throw new Error(`JSON file not found: ${fullPath}`);
    }

    const module = (await moduleLoader()) as { default: T };
    return module.default;
  } catch (error) {
    console.error(`Failed to load JSON file: ${fullPath}`, error);
    throw error;
  }
}

/**
 * Reactive content loader for Vue components
 * @param experimentId - Directory name
 * @param fileName - File name
 */
export function useExperimentContent(experimentId: string, fileName: string) {
  const content = ref<string>("");
  const loading = ref(true);
  const error = ref<string | null>(null);

  const load = async () => {
    loading.value = true;
    error.value = null;

    try {
      content.value = await loadExperimentContent(experimentId, fileName);
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to load content";
      console.error(`Failed to load ${fileName}:`, err);

      // Provide fallback content based on file type
      content.value = getFallbackContent(fileName);
    } finally {
      loading.value = false;
    }
  };

  // Load immediately
  load();

  return {
    content,
    loading,
    error,
    reload: load,
  };
}

/**
 * Reactive JSON loader for Vue components
 */
export function useExperimentJSON<T = any>(experimentId: string, fileName: string) {
  const data = ref<T | null>(null);
  const loading = ref(true);
  const error = ref<string | null>(null);

  const load = async () => {
    loading.value = true;
    error.value = null;

    try {
      data.value = await loadExperimentJSON<T>(experimentId, fileName);
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to load JSON";
      console.error(`Failed to load ${fileName}:`, err);
      data.value = null;
    } finally {
      loading.value = false;
    }
  };

  // Load immediately
  load();

  return {
    data,
    loading,
    error,
    reload: load,
  };
}

/**
 * Get fallback content when file loading fails
 */
function getFallbackContent(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "md":
      if (fileName.includes("consent")) {
        return getDefaultConsentText();
      } else if (fileName.includes("instruction")) {
        return getDefaultInstructionsText();
      } else {
        return `# ${fileName}\n\nContent could not be loaded. Please check that the file exists.`;
      }

    case "txt":
      return `Content could not be loaded from ${fileName}. Please check that the file exists.`;

    default:
      return `Content could not be loaded from ${fileName}.`;
  }
}

function getDefaultConsentText(): string {
  return `
# Informed Consent for Research Participation

## Study Purpose
You are being invited to participate in a research study investigating human problem-solving strategies.

## What You Will Do
- Complete puzzle-solving tasks
- Answer brief questions about your problem-solving strategies
- Provide demographic information

## Time Commitment
This study will take approximately 30-45 minutes to complete.

## Risks and Benefits
There are no known risks associated with this study beyond those of everyday life. This research may help us better understand human problem-solving processes.

## Confidentiality
Your responses will be kept completely confidential. Data will be stored securely and only aggregate results will be reported.

## Voluntary Participation
Your participation is entirely voluntary. You may withdraw at any time without penalty.

## Contact Information
If you have questions about this research, please contact the research team.

## Consent
By clicking "I Agree" below, you indicate that:
- You have read and understood this consent form
- You are 18 years of age or older
- You voluntarily agree to participate in this research
`;
}

function getDefaultInstructionsText(): string {
  return `
# Instructions

## Welcome
Thank you for participating in this study. You will be completing puzzle-solving tasks.

## What to Expect
- You will solve several puzzles
- Take your time and do your best
- There are no trick questions

## Getting Started
Click "Continue" when you're ready to begin.
`;
}

/**
 * Get the experiment ID from the current context
 * This helper extracts the experiment ID for use in content loading
 */
export function getExperimentIdFromContext(context: any): string {
  // Try to get experiment ID from context or URL
  if (context?.experimentId) {
    return context.experimentId;
  }

  // Extract from current URL as fallback
  const path = window.location.pathname;
  const match = path.match(/\/experiment\/([^\/]+)/);
  return match ? match[1] : "";
}

/**
 * Preload content files for better performance
 * Call this when entering an experiment
 */
export async function preloadExperimentContent(experimentId: string, fileNames: string[]): Promise<void> {
  const loadPromises = fileNames.map((fileName) =>
    loadExperimentContent(experimentId, fileName).catch((err) => {
      console.warn(`Failed to preload ${fileName}:`, err);
    }),
  );

  await Promise.allSettled(loadPromises);
}
