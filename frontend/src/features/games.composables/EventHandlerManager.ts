import type { usePuzzleController } from "@/composables/usePuzzleController.ts";

/**
 * EventHandlerListKey<TEvents> - Type alias for event names
 *
 * This is simply the names of all the events we can handle.
 * For example, if TEvents is { onClick: (x: number) => boolean, onHover: () => void }
 * then EventHandlerListKey would be "onClick" | "onHover"
 *
 * Think of it as: "What are all the event names I can listen for?"
 */
type EventHandlerListKey<TEvents> = keyof TEvents;

/**
 * EventHandlerList - Type for a list of event handler functions
 *
 * This is an array of functions. Each function:
 * - Can take any number of arguments (...args: any[])
 * - Can return anything (=> any)
 *
 * Think of it as: "A list of functions that all handle the same type of event"
 * Example: [function1, function2, function3] where all handle "onClick" events
 */
type EventHandlerList = ((...args: any[]) => any)[];

/**
 * EventHandlerManager<TEvents> - Generic class to manage event handlers
 *
 * TEvents is a "contract" that defines what events this manager can handle.
 * It must be an object where:
 * - Keys are event names (strings like "onClick", "onHover")
 * - Values are function signatures (like "(x: number) => boolean")
 *
 * Example TEvents:
 * {
 *   onClick: (x: number, y: number) => boolean,
 *   onHover: (cellId: string) => void,
 *   onDoubleClick: () => boolean
 * }
 *
 * This class lets you:
 * 1. Register multiple handlers for each event type
 * 2. Compile them together with different strategies
 * 3. Emit events to all registered handlers
 */
export class EventHandlerManager<TEvents extends { [TEventKey in keyof TEvents]: (...args: any[]) => any }> {
  /**
   * handlerMap - Internal storage for all registered event handlers
   *
   * This is like a filing cabinet where:
   * - Each drawer is labeled with an event name (like "onClick")
   * - Inside each drawer is a list of functions that handle that event
   *
   * Example structure:
   * {
   *   "onClick": [function1, function2, function3],
   *   "onHover": [function4, function5],
   *   "onDoubleClick": [function6]
   * }
   *
   * Partial<Record<...>> means:
   * - It's an object (Record)
   * - Keys are event names (EventHandlerListKey<TEvents>)
   * - Values are arrays of functions (EventHandlerList)
   * - Some events might not have handlers yet (Partial)
   */
  private handlerMap: Partial<Record<EventHandlerListKey<TEvents>, EventHandlerList>> = {};

  /**
   * Add a behavior that implements part of the event interface
   *
   * A "behavior" is a function that returns an object containing event handlers.
   * For example, a behavior might return { onClick: handleClick, onHover: handleHover }
   *
   * The generic <T extends Partial<TEvents>> means:
   * - T can be any subset of the TEvents type
   * - You don't have to implement ALL events, just some of them
   * - The return type T ensures type safety for what you actually implement
   *
   * @param behaviour - Function that takes a session and returns event handlers
   * @param session - The puzzle session data passed to the behavior function
   * @returns The same object that the behavior function returned
   */
  addBehaviour<T extends Partial<TEvents>, State = ReturnType<typeof usePuzzleController>>(
    behaviour: (session: State) => T,
    session: State,
  ): T {
    const additions = behaviour(session);

    for (const key in additions) {
      const typedKey = key as unknown as keyof TEvents;
      const fn = additions[typedKey];

      if (typeof fn === "function") {
        if (!this.handlerMap[typedKey]) this.handlerMap[typedKey] = [];
        this.handlerMap[typedKey]!.push(fn);
      }
    }

    return additions;
  }

  /**
   * Get compiled handlers based on the combining strategy
   *
   * This takes all the registered handlers and combines them into a single object
   * that can be used by components. Different strategies determine how multiple
   * handlers for the same event are combined:
   *
   * - 'first-true': Stop at the first handler that returns true (good for input events)
   * - 'emit-all': Call all handlers, ignore return values (good for notifications)
   * - 'merge-results': Combine all return values together (good for styling/rendering)
   *
   * @param strategy - How to combine multiple handlers for the same event
   * @returns An object containing the compiled event handlers
   */
  getCompiledHandlers(strategy: "first-true" | "emit-all" | "merge-results"): Partial<TEvents> {
    const combined: Partial<TEvents> = {};

    for (const key in this.handlerMap) {
      const typedKey = key as keyof TEvents;
      const fns = this.handlerMap[typedKey]!;

      if (strategy === "first-true") {
        // For BoardEvents - return true if any handler returns true
        combined[typedKey] = ((...args: any[]): boolean => {
          for (const fn of fns) {
            const res = fn(...args);
            if (res) return true;
          }
          return false;
        }) as TEvents[typeof typedKey];
      } else if (strategy === "emit-all") {
        // For GameEvents - call all handlers, return void
        combined[typedKey] = ((...args: any[]): void => {
          for (const fn of fns) {
            fn(...args);
          }
        }) as TEvents[typeof typedKey];
      } else if (strategy === "merge-results") {
        // For RenderingEvents - merge results based on return type
        combined[typedKey] = ((...args: any[]) => {
          if (key.includes("Classes")) {
            // Merge string arrays
            const allClasses: string[] = [];
            for (const fn of fns) {
              const classes = fn(...args);
              if (Array.isArray(classes)) allClasses.push(...classes);
            }
            return allClasses;
          } else if (key.includes("Styles")) {
            // Merge objects
            const allStyles: Record<string, string> = {};
            for (const fn of fns) {
              const styles = fn(...args);
              if (styles && typeof styles === "object") Object.assign(allStyles, styles);
            }
            return allStyles;
          } else if (key.includes("Visible") || key.includes("isVisible")) {
            // AND logic for visibility functions - cell is visible only if ALL handlers return true
            for (const fn of fns) {
              const res = fn(...args);
              // If any handler returns an explicit falsy value, hide the cell
              if (res !== null && res !== undefined && !res) {
                return false;
              }
            }
            // If no handler explicitly returned false, the cell is visible
            return true;
          } else {
            // For other types, return last non-null result
            let result = null;
            for (const fn of fns) {
              const res = fn(...args);
              if (res !== null && res !== undefined) result = res;
            }
            return result;
          }
        }) as TEvents[typeof typedKey];
      }
    }

    return combined;
  }

  /**
   * Emit a specific event to all registered handlers
   *
   * This is a convenience method that directly calls all handlers
   * for a specific event, useful for manual event triggering.
   *
   * @param event - The name of the event to emit
   * @param args - The arguments to pass to each handler
   */
  emit<K extends keyof TEvents>(event: K, ...args: Parameters<TEvents[K]>) {
    for (const fn of this.handlerMap[event] || []) {
      fn(...args);
    }
  }
}
