import { computed, ref } from 'vue';
import type { CanvasTheme } from './canvas-types';

/** Light theme color palette */
const LIGHT_THEME: CanvasTheme = {
  background: '#ffffff',
  grid: '#cccccc',
  majorGrid: '#808080',
  text: '#374151',      // gray-700
  prefilled: '#000000',
  error: '#ef4444',     // red-500
  cursor: '#e0e0e0',
  // Game-specific
  wall: '#000000',
  lit: '#fef08a',       // yellow-200
  green: '#86efac',     // green-300
  gray: '#d1d5db',      // gray-300
  blue: '#3b82f6',      // blue-500
  hint: '#9ca3af'       // gray-400
};

/** Dark theme color palette */
const DARK_THEME: CanvasTheme = {
  background: '#1a1a1a',
  grid: '#404040',
  majorGrid: '#606060',
  text: '#e5e7eb',      // gray-200
  prefilled: '#9ca3af', // gray-400
  error: '#f87171',     // red-400
  cursor: '#404040',
  // Game-specific
  wall: '#000000',
  lit: '#ca8a04',       // yellow-600
  green: '#16a34a',     // green-600
  gray: '#4b5563',      // gray-600
  blue: '#60a5fa',      // blue-400
  hint: '#6b7280'       // gray-500
};

/**
 * Composable for managing canvas theme
 *
 * @returns theme - Reactive theme object
 * @returns isDark - Reactive dark mode flag
 * @returns toggleTheme - Function to toggle between light and dark
 */
export function useCanvasTheme() {
  // TODO: Connect to global theme system when available
  const isDark = ref(false);

  const theme = computed<CanvasTheme>(() =>
    isDark.value ? DARK_THEME : LIGHT_THEME
  );

  const toggleTheme = () => {
    isDark.value = !isDark.value;
  };

  return {
    theme,
    isDark,
    toggleTheme
  };
}
