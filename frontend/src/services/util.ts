/**
 * Converts a number from one range to another.
 *
 * @param oldRange - A tuple representing the original range as [oldMin, oldMax].
 * @param newRange - A tuple representing the new desired range as [newMin, newMax].
 * @param value - The number to convert from the original range to the new range.
 * @returns The converted value mapped to the new range.
 */
export function remap(oldRange: [number, number], newRange: [number, number], value: number): number {
  const [oldMin, oldMax] = oldRange;
  const [newMin, newMax] = newRange;

  return newMin + ((value - oldMin) * (newMax - newMin)) / (oldMax - oldMin);
}

/**
 * Convert unix time in milliseconds to HH:MM:SS format
 *
 * @param {number} milliseconds - Unix time in miliseconds
 * @returns {string} Formatted string in milliseconds
 */
export function format_game_stopwatch(milliseconds: number) {
  // constants
  const SECONDS_IN_HOUR = 3600;
  const SECONDS_IN_MINUTE = 60;

  // convert to seconds
  let as_seconds = Math.floor(milliseconds / 1000);

  // get each value of interest
  const hours = Math.floor(as_seconds / SECONDS_IN_HOUR);
  const minutes = Math.floor((as_seconds % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE);
  const seconds = as_seconds % SECONDS_IN_MINUTE;

  // convert to padded strings
  const formatted_minutes = String(minutes).padStart(2, "0");
  const formatted_seconds = String(seconds).padStart(2, "0");
  const mm_ss = `${formatted_minutes}:${formatted_seconds}`;

  // only show hours if hours have passed
  if (hours > 0) {
    const formatted_hours = String(hours).padStart(2, "0");
    return `${formatted_hours}:${mm_ss}`;
  }

  return mm_ss;
}

export async function sha256(message: string) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  return hashHex;
}
