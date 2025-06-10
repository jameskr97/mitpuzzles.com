from .bus import event_bus


def on_event(event_type: str, priority: int = 0):
    """Decorator to register an event listener"""
    def decorator(func):
        func.priority = priority
        event_bus.subscribe(event_type, func)
        return func
    return decorator
