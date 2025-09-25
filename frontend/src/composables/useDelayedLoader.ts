import { ref } from "vue";

export function useDelayedLoader(delayMs = 200) {
  const isLoading = ref(false);
  const showSpinner = ref(false);

  async function run<T>(fn: () => Promise<T>): Promise<T> {
    isLoading.value = true;
    showSpinner.value = false;

    const timer = setTimeout(() => {
      showSpinner.value = true;
    }, delayMs);

    try {
      return await fn();
    } finally {
      clearTimeout(timer);
      isLoading.value = false;
      showSpinner.value = false;
    }
  }

  return {
    isLoading,
    showSpinner,
    run,
  };
}
