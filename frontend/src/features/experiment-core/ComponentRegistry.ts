import type { Component } from "vue";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("experiment:component-registry");

/** registry for experiment components loaded at build time */
export class ComponentRegistry {
  // load all vue components from both shared trials and experiment-definitions
  private static components: Record<string, any> = import.meta.glob(
    [
      "../experiment-definitions/*/*.vue", // experiment-specific components
    ],
    { eager: true },
  );

  /** get component by experiment name and component name with priority-based resolution */
  static get_component(experiment_name: string, component_name: string): Component | null {
    log("trying to get component %s/%s", experiment_name, component_name);

    // Priority order: shared components first, then experiment-specific
    const paths = [
      `./components/trials/${component_name}.vue`, // shared (highest priority)
      `../experiment-definitions/${experiment_name}/${component_name}.vue`, // experiment-specific
    ];

    for (const path of paths) {
      const component_module = this.components[path];
      if (component_module?.default) {
        log("found component at: %s", path);
        return component_module.default as Component;
      }
    }

    // debug: log available paths if not found
    console.warn(`component not found: tried ${paths.join(", ")}`);
    console.warn("available components:", Object.keys(this.components));

    return null;
  }
}
