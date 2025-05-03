export function useHoverTracking(MIN_TIME_HOVER: number = 2000) {
  let enterTime: number | undefined = undefined;

  return {
    onMouseEnter() {
      enterTime = Date.now();
    },
    onMouseLeave(callback: (time: number) => void) {
      if (!enterTime) return;
      const diff = Date.now() - enterTime;
      if (diff >= MIN_TIME_HOVER) callback(diff);
      enterTime = undefined;
    },
  };
}
