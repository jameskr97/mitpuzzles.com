
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