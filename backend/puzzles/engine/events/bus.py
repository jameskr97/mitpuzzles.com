import logging
from typing import List, Dict, Callable
from collections import defaultdict
from .event import Event


class EventBus:
    """Simple pub/sub event bus"""

    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, listener: Callable) -> None:
        """Subscribe a listener to an event type"""
        self.listeners[event_type].append(listener)
        listener_name = getattr(listener, "__name__", str(listener))
        self.logger.debug(f"Subscribed {listener_name} to '{event_type}'")

    def publish(self, event: Event) -> None:
        """Publish an event to all listeners"""
        listeners = self.listeners.get(event.type, [])

        if not listeners:
            self.logger.debug(f"No listeners for event type: {event.type}")
            return

        self.logger.debug(f"Publishing event {event.type} to {len(listeners)} listeners")

        # Sort by priority (higher first)
        sorted_listeners = sorted(listeners, key=lambda l: getattr(l, "priority", 0), reverse=True)

        # Call all listeners with error isolation
        for listener in sorted_listeners:
            try:
                listener(event)
            except Exception as e:
                listener_name = getattr(listener, "__name__", str(listener))
                self.logger.error(f"Error in listener {listener_name}: {e}", exc_info=True)


# global event bus instance
event_bus = EventBus()
