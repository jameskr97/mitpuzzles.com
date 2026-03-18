import debug from "debug";

/**
 * create a namespaced debug logger.
 *
 * usage:
 *   const log = createLogger("router");
 *   log("Navigating to %s", path);
 *
 * enable in browser console:
 *   localStorage.setItem("debug", "app:router,app:session");
 *   localStorage.setItem("debug", "app:*");  // enable all
 */
export function createLogger(module: string) {
  return debug(`app:${module}`);
}
